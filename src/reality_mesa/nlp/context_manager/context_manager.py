from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reality_mesa.tabletop_engine.tabletop import PointerCtx
from ..llm import start_llm_task, ask_llm_and_wait
from ..semantic_graph import SemanticGraph,SemanticNode,SemanticSubgraph, SemanticGraphExpandConfig,GenerateTriples,SemanticTriple
from ..sentence_embedding import SentenceEmbedder,EmbeddingGenerate
import spacy
from spacy.tokens import Span
from spacy.tokens import Token
import time
from collections import deque
from .description_triple_generator import GenerateTriplesDescription
from .prompts import *
import ast
class ContextManager:
    def __init__(self,max_sentences=6, max_sent_age = 90,max_triples_subgraph:int = 35):
        self.graph = SemanticGraph(allow_orphan_nodes=True,min_similarity=0.55)
        self.expander = SemanticGraphExpandConfig(k_depth=0.11,k_prompt=0.35)
        self.last_subgraph = SemanticSubgraph(self.graph,{})
        
        self.llm_queue,self.llm_manager,self.llm_task = start_llm_task()
        self.nlp = spacy.load("pt_core_news_lg")

        self.embedder = SentenceEmbedder()
        self.max_triples_subgraph = max_triples_subgraph

        self.tabletop_to_context: dict[int,str] = {}
        self.context_to_tabletop: dict[str,int] = {}

        self.max_sent_age = max_sent_age
        self.not_processed = 0
        self.max_sent = max_sentences
        self.sent_list:deque[tuple[str,float]] = deque(maxlen=max_sentences)
        self.pointer :PointerCtx | None = None

    def __extract_verb(self,doc:Span):
        root = next(t for t in doc if t.dep_ == "ROOT")
        if root is None:
            root(next(t for t in doc if t.pos_ == "VERB"))
        if root is None:
            return { "sujeito":None, "acao":None,"objetos":[],"finalidades":[],"modos":[],"tipo":None}
        
        kind = "DR"
        nsubj = next((t for t in root.children if t.dep_ == "nsubj"), None)
        if root.lemma_ in ("querer","queror","querar"):
            kind = "QR"
            last_root = root
            root = next((t for t in root.children if t.dep_ in ("xcomp") and t.pos_ == "VERB"), None)
            if root is None:
                root = next((t for t in last_root.children if t.dep_ in ("ccomp")), None)
                if root is None:
                    return { "sujeito":None, "acao":None,"objetos":[],"finalidades":[],"modos":[],"tipo":None}
                if root.pos_ not in ("VERB"):
                    root = next((t for t in root.children if t.dep_ in ("aux","aux:pass","aux:atv","acl:relcl") and t.pos_ == "VERB"), None)
                if root is None:
                    return { "sujeito":None, "acao":None,"objetos":[],"finalidades":[],"modos":[],"tipo":None}
        obj = [t for t in root.children if  t.dep_ in ("dobj", "obj")]
        obl = [t for t in root.children if  t.dep_ in ("dobl", "obl")]
        advmod = [t for t in root.children if t.dep_ == "advmod"]
        return { "sujeito":nsubj, "acao":root,"objetos":obj,"finalidades":obl,"modos":advmod,"tipo":kind}
    
    def GetSentences(self,text:str):
        doc = self.nlp(text)
        sentences = doc.sents
        return sentences

    def AddSentence(self,sent:Span):
        now = time.monotonic()
        #TODO ADD SENTENCE TO SENT LIST
        self.sent_list.appendleft((sent.text,now))
        self.not_processed += 1
        # REMOVE AUGMENTATION NODES
        # ADD AUGMENTATION NODES
        info = self.__extract_verb(sent)
        objs:list[Span|Token] = [info["sujeito"]]+info["objetos"]+info["finalidades"] + [sent]
        descriptions = [" ".join(tok.text for tok in t.subtree) for t in objs if t is not None]
        embeddings = EmbeddingGenerate(self.embedder,descriptions)
        subgraph = SemanticSubgraph(self.graph,{})
        for s,e in embeddings:
            sub = SemanticSubgraph.Create(self.graph,e)
            sub.Expand(2,self.expander)
            subgraph.Join(sub)
        subgraph.SetAge(now)
        subgraph.Join(self.last_subgraph,k_modifier=0.8)
        subgraph.OldAgeKill(90,now)
        subgraph.Prune(self.max_triples_subgraph)
        self.last_subgraph = subgraph
        return subgraph, info
    
    def ClearSubgraph(self):
        self.last_subgraph = SemanticSubgraph(self.graph,{})
    

    def GetContextToken(self,tabletop_id:int):
        if tabletop_id in self.tabletop_to_context:
            return self.tabletop_to_context[tabletop_id]
        return None
    
    def GetTabletopToken(self,token:str):
        if token in self.context_to_tabletop:
            return self.context_to_tabletop[token]
        return None
    
    def AddCtxTabletop(self,ctx:str,id_tt:int):
        self.context_to_tabletop[ctx] = id_tt
        self.tabletop_to_context[id_tt] = ctx

    
    def GetSubgraphStr(self,add_subtitles:bool = True, add_age:bool = True, add_trip_id:bool = False):
        subtitles = """legenda: significado de templates e espaços\n<id> palavra ou código simples sem aspas  que identifica uma entidade. ex: tok1
<relacao> verbo e auxiliares sem aspas que representam a relação entre entidades. ex: ser amigo de
<string> texto simples ou complexo em miúsculo e com aspas que representa uma descrição ou característica complexa, reduzido o máximo possível. ex: \"uma criatura das trevas\"\n"""
       
        if add_age:
            subtitles += "<idade> tempo em segundos e minutos desde que esta tripla foi criada, utilizada como informação extra. ex: 5m03\n"
        if add_trip_id:
            subtitles += "<id_tripla> id numérico da tripla em que aparece, utilizado para identificar uma tripla sem repetí-la. ex: 3\n"

        subtitles+= "formato de entradas:\n"
        base = ""
        if add_trip_id:
            base+="<id_tripla>|"
        if add_age:
            base+="\'<idade>\'"

        subtitles+= f"{base}(<id>,<relacao>,<string>)\n{base}(<id>,<relacao>,<id>)\n{base}(<string>,<relacao>,<string>)\n{base}(<string>,<relacao>,<id>)\n"

        text = "--- INICIO TRIPLAS RELACIONADAS AO CONTEXTO ---\n" + self.last_subgraph.ToString(add_age,time.monotonic(),show_id=add_trip_id) +"--- FIM TRIPLAS RELACIONADAS AO CONTEXTO ---\n"

        return subtitles + text if add_subtitles else text
    
    def GetSentencesStr(self,add_subtitle:bool = True, divide:bool = False,add_time:bool = True):
        now = time.monotonic()
        
        while len(self.sent_list)>0:
            if time.monotonic() -  self.sent_list[-1][1] > self.max_sent_age:
                self.sent_list.pop()
            else:
                break

        self.not_processed = min(self.not_processed, len(self.sent_list))
        subtitle = """legenda: últimas frases faladas em sequência, formatadas como:
tempo em minutos desde que a frase foi falada | frase
ex. 5m03 | Eu vou até ali.
4m50 | Não, desisto, vou até aqui mesmo.\n"""
        if add_time:
            phrases =[f"{int((now-t)/60)}m{int(now-t)%60:02} | {phrase}" for phrase,t in self.sent_list]
        else:
            phrases =[phrase for phrase,t in self.sent_list]
        phrases.reverse()
        p_done = '\n'.join(phrases[:len(self.sent_list)-self.not_processed])
        p_not_done = '\n'.join(phrases[len(self.sent_list)-self.not_processed:])

        if not add_subtitle:
            return p_done+"\n"+p_not_done
        
        if divide and len(p_done)>0:
            subtitle+="\n----- FRASES JÁ PROCESSADAS, USE APENAS COMO CONTEXTO, NÃO CRIE OU REMOVA A PARTIR DELAS ----\n"
            subtitle+=p_done
        if divide and len(p_not_done)>0:
            subtitle+="\n----- FRASES NÃO PROCESSADAS, CRIE E REMOVA APENAS A PARTIR DELAS ----\n"
            subtitle+=p_not_done

        if divide and len(phrases)>0:
            subtitle+="\n------- FIM DE FRASES CONTEXTUAIS ---------\n"
        
        if divide:
            return subtitle
        return subtitle+ "------- INICIO DE FRASES CONTEXTUAIS ---------\n"+p_done+"\n"+p_not_done+"\n------- FIM DE FRASES CONTEXTUAIS ---------\n"

    def AddToGraph(self,triple_txt):
        triples = GenerateTriples(self.graph,self.embedder,triple_txt)
        new_triples = SemanticSubgraph(self.graph,{})
        for t in triples:
            new_triples.AddTriple(t,0.75)

        self.last_subgraph.Join(new_triples)
        self.last_subgraph.Prune(self.max_triples_subgraph)
        

    def AddElement(self,id_tt:int, id_str:str, description:str):
        self.AddCtxTabletop(id_str,id_tt)
        self.graph.AddNode(SemanticNode(id_str))
        print(f"id:{id_str}\n{description}\n\n")
        out = GenerateTriplesDescription(self.llm_queue,description,id_str)
        print(out)
        if out:
            GenerateTriples(self.graph,self.embedder,out)
    

    def AddElementTriples(self,id_tt:int, id_str:str, triples:str):
        self.AddCtxTabletop(id_str,id_tt)
        self.graph.AddNode(SemanticNode(id_str))
        GenerateTriples(self.graph,self.embedder,triples)

    def RemoveElement(self,id_tt:int):
        if id_tt in self.tabletop_to_context:
            name = self.tabletop_to_context.pop(id_tt)
            self.context_to_tabletop.pop(name,None)
            node = self.graph.NodeInGraph((name,False))
            if node is not None:
                self.graph.RemoveNode(node.id)

    def UpdatePointers(self,ptrs:"PointerCtx | None"):
        self.pointer = ptrs

    def GetLNContextStr(self,ctx:list[tuple[SemanticTriple,float]],add_subtitles:bool = True):
        if len(ctx) == 0:
            return str("")
        subtitles = "INFORMAÇÕES QUE PODEM SER UTILIZADAS PARA O PROCESSAMENTO DE RELAÇÕES\n"
        ctx.sort(key=lambda k: k[1],reverse=True)
        phrases = '\n'.join([t.ToNaturalLanguage() for t,_ in ctx])
        if add_subtitles:
            return subtitles+phrases+"\n"
        return phrases+"\n"
    
    def GetIdRelationsStr(self,ctx:list[tuple[SemanticTriple,float]],add_subtitles:bool = True):
        if len(ctx) == 0:
            return str("")
        subtitles = "RELAÇÕES ENTRE ENTIDADES QUE PODEM SER UTILIZADAS NO FORMATO DE TRIPLAS RELACIONAIS\n"
        ctx.sort(key=lambda k: k[1],reverse=True)
        phrases = '\n'.join([t.ToString() for t,_ in ctx])
        if add_subtitles:
            return subtitles+phrases+"\n"
        return phrases+"\n"
    
    def AddPtrToIdDict(self,id_dict:dict):
        if self.pointer is None:
            return
        
        id_dict["p_apontado"] = {
                "id":"p_apontado",
                "caracteristicas": [],
                "caracteristicas especiais":["Posição que está sendo apontada pelo usuário, o fim de uma reta de medição de destino."\
                    " Frases que possuem textos como daqui até ali, até esse lugar, aquele lugar, até aqule ponto, até aqui, ou mova/crie por essa reta/linha, representam esse objeto."\
                        " Outras entidades que falem sobre ponto de interesse de fim de caminho se referem a esta entidade."]
            }
        
        for tt_node in self.pointer.end_right_on:
            key = self.GetContextToken(tt_node)
            if key is None:
                continue
                
            
            if self.pointer.start is None:
                txt = "Esta entidade tem muito alta possibilidade de representar a entidade movida, origem, ou o ponto de chegada quando representado como esse, isso, este, ele, ela, essa, desse, daqui, dali, e sujeitos ocultos, visto que o usuário apontou para sua posição como um ponto de interesse do comando, estando exatamente na posição de p_apontado"
                if key in id_dict:
                    id_dict[key]["caracteristicas especiais"].append(txt)
                else:
                    id_dict[key] = {
                        "id": key, 
                        "caracteristicas": [],
                        "caracteristicas especiais": [txt]
                    }
            else:
                txt = "Esta entidade tem muito alta possibilidade de representar o ponto de chegada, ou destino do comando, quando representado como esse, isso, este, ele, ela, essa, desse, daqui, dali, e sujeitos ocultos, visto que o usuário apontou para sua posição como um ponto de interesse do comando, estando exatamente na posição de p_apontado"
                if key in id_dict:
                    id_dict[key]["caracteristicas especiais"].append(txt)
                else:
                    id_dict[key] = {
                        "id": key, 
                        "caracteristicas": [],
                        "caracteristicas especiais": [txt]
                    }
        
        for tt_node in self.pointer.end_near:
            key = self.GetContextToken(tt_node)
            if key is None:
                continue
            if self.pointer.start is None:
                txt = "Esta entidade tem alta possibilidade de representar a entidade movida, origem, ou o ponto de chegada quando representado como esse, isso, este, ele, ela, essa, desse, daqui, dali, e sujeitos ocultos, visto que o usuário apontou para sua posição como um ponto de interesse do comando, estando próximo, mas não exatamente na posição de p_apontado"
                if key in id_dict:
                    id_dict[key]["caracteristicas especiais"].append(txt)
                else:
                    id_dict[key] = {
                        "id": key, 
                        "caracteristicas": [],
                        "caracteristicas especiais": [txt]
                    }
            else:
                txt = "Esta entidade tem alta possibilidade de representar o ponto de chegada, ou destino do comando, quando representado como esse, isso, este, ele, ela, essa, desse, daqui, dali, e sujeitos ocultos, visto que o usuário apontou para sua posição como um ponto de interesse do comando, estando próximo, mas não exatamente na posição de p_apontado"
                if key in id_dict:
                    id_dict[key]["caracteristicas especiais"].append(txt)
                else:
                    id_dict[key] = {
                        "id": key, 
                        "caracteristicas": [],
                        "caracteristicas especiais": [txt]
                    }

        if self.pointer.start_near is not None and self.pointer.start_right_on is not None:
            for tt_node in self.pointer.start_right_on:
                key = self.GetContextToken(tt_node)
                if key is None:
                    continue
                txt = "Esta entidade tem muito alta possibilidade de representar a entidade movida ou origem do comando, quando representado como esse, isso, este, ele, ela, essa, desse, daqui, dali, e sujeitos ocultos, visto que o usuário apontou para sua posição como um ponto de interesse no inicio do movimento/comando, estando exatamente no ponto de inicio do comando."
                if key in id_dict:
                    id_dict[key]["caracteristicas especiais"].append(txt)
                else:
                    id_dict[key] = {
                        "id": key, 
                        "caracteristicas": [],
                        "caracteristicas especiais": [txt]
                    }
                  
            for tt_node in self.pointer.start_near:
                key = self.GetContextToken(tt_node)
                if key is None:
                    continue
                txt ="Esta entidade tem alta possibilidade de representar a entidade movida ou origem do comando, quando representado como esse, isso, este, ele, ela, essa, desse, daqui, dali, e sujeitos ocultos, visto que o usuário apontou para sua posição como um ponto de interesse no inicio do movimento/comando, estando próximo, mas não exatamente no ponto de inicio do comando."
                if key in id_dict:
                    id_dict[key]["caracteristicas especiais"].append(txt)
                else:
                    id_dict[key] = {
                        "id": key, 
                        "caracteristicas": [],
                        "caracteristicas especiais": [txt]
                    }

        
    def GetIdDict(self,ctx:list[tuple[SemanticTriple,float]],ids:dict[int,SemanticNode]):
        if len(ids) == 0:
            return {}
        
        out= {}
        for id in ids.values():
            out[id.ToString()] = {
                "id": id.ToString(), 
                "caracteristicas": [],
                "caracteristicas especiais": []
            }
        
        ctx.sort(key= lambda k: k[1],reverse=True)
        for triple, _ in ctx:
            key = triple.start.ToString()
            if key in out:
                out[key]["caracteristicas"].append(triple.ToNaturalLanguage())
        return out

    def IdDictToString(self,id_dict:dict,add_subtitles:bool = True):
        if len(id_dict) == 0:
            return str("")
        subtitles = "ENTIDADES VÁLIDAS E SUAS CARACTERÍSTICAS EM LINGUAGEM NATURAL\n"
        phrases = ""
        for val in id_dict.values():
            phrases += str(object=val) + "\n" 
        if add_subtitles:
            return subtitles+phrases+"\n"
        return phrases+"\n"
    
    def GetCtxStr(self, subtitles:bool= True,add_positional:bool = True):
        ln, idrel, iddesc,ids = self.last_subgraph.DivideContext()
        desc_dict = self.GetIdDict(iddesc,ids)
        if add_positional:
            self.AddPtrToIdDict(desc_dict)
        return self.GetLNContextStr(ln,subtitles)+self.GetIdRelationsStr(idrel,subtitles)+self.IdDictToString(desc_dict,subtitles)

    def RemoveContext(self, entities:str):
        user_prompt = f"Entidades:\n{entities}"\
            f"\nTriplas:\n{self.GetSubgraphStr(False,False,True)}"\
            f"\n{self.GetSentencesStr(True,True,False)}"
        out = ask_llm_and_wait(self.llm_queue,REMOVAL_PROPMT,user_prompt)
        if out is None:
            return

        try: 
            remove = ast.literal_eval(out)
            if not isinstance(remove,list):
                return
        except:
            return;

        for i in remove:
            print("REMOVED:\n")
            if isinstance(i,int):
                tt = self.graph.GetTriple(i)
                if tt is not None:
                    print(tt.ToString()+"\n")
                self.graph.RemoveTriple(i)

    def AddTripleContext(self, entities:str):
        user_prompt = f"Entidades:\n{entities}"\
            f"\nTriplas:\n{self.GetSubgraphStr(False,False,True)}"\
            f"\n{self.GetSentencesStr(True,True,False)}"

        out = ask_llm_and_wait(self.llm_queue,ADDITION_PROMPT,user_prompt)
        if out is None:
            return
        print("\nADDED\n")
        print(out)
        self.AddToGraph(out)

    def AddDictContext(self,ctx:list[tuple[SemanticTriple,float]]):
        ctx.sort(key=lambda k: k[1])
        triples = '\n'.join([t.ToString() for t,s in ctx])
        user_prompt = f"Triplas do Dicionário Anteriores:\n{triples}"\
            f"\n{self.GetSentencesStr(True,True,False)}"

        out = ask_llm_and_wait(self.llm_queue,DICTIONARY_PROMPT,user_prompt)
        if out is None:
            return
        print("\nDICTONARY\n")
        print(out)
        self.AddToGraph(out)

        

        
        
        

