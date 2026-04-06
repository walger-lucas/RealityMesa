from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from reality_mesa.tabletop_engine.tabletop import PointerCtx
from ..llm import start_llm_task
from ..semantic_graph import SemanticGraph,SemanticNode,SemanticSubgraph, SemanticGraphExpandConfig,GenerateTriples,SemanticTriple
from ..sentence_embedding import SentenceEmbedder,EmbeddingGenerate
import spacy
from spacy.tokens import Span
from spacy.tokens import Token
import time
from collections import deque
from .description_triple_generator import GenerateTriplesDescription
#TODO THIS CLASS MUST HAVE ACCESS TO TABLETOP? IT IS THE NLP MANAGER, MUST ALLOW AND DEAMBIGUIATE TOKENS AND POIs but should not generate them


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
        self.ctx_triples :list[SemanticTriple] = []

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
        for t in self.ctx_triples:
            subgraph.AddTriple(t,0.5)
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
    
    def GetSentencesStr(self,add_subtitle:bool = True, divide:bool = False):
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
        phrases =[f"{int((now-t)/60)}m{int(now-t)%60:02} | {phrase}" for phrase,t in self.sent_list]
        phrases.reverse()
        p_done = '\n'.join(phrases[:len(self.sent_list)-self.not_processed])
        p_not_done = '\n'.join(phrases[len(self.sent_list)-self.not_processed:])

        if not add_subtitle:
            return p_done+"\n"+p_not_done
        
        if divide and len(p_done)>0:
            subtitle+="----- FRASES JÁ PROCESSADAS, USE COMO CONTEXTO, NÃO CRIE A PARTIR DELAS ----\n"
            subtitle+=p_done
        if divide and len(p_not_done)>0:
            subtitle+="----- FRASES NÃO PROCESSADAS, USE COMO CONTEXTO E CRIE NOVAS TRIPLAS A PARTIR DELAS ----\n"
            subtitle+=p_not_done

        if divide and len(phrases)>0:
            subtitle+="------- FIM DE FRASES CONTEXTUAIS ---------\n"
        
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
        out = GenerateTriplesDescription(self.llm_queue,description,id_str)
        if out:
            GenerateTriples(self.graph,self.embedder,out)
    
    def RemoveElement(self,id_tt:int):
        if id_tt in self.tabletop_to_context:
            name = self.tabletop_to_context.pop(id_tt)
            self.context_to_tabletop.pop(name,None)
            node = self.graph.NodeInGraph((name,False))
            if node is not None:
                self.graph.RemoveNode(node.id)

    def UpdatePointers(self,ptrs:"PointerCtx | None"):
        p_origin = "p_origem"
        p_pointing = "p_apontado"

        node_org = self.graph.NodeInGraph((p_origin,False))
        node_dest = self.graph.NodeInGraph((p_pointing,False))
        if node_org is not None:
            self.graph.RemoveNode(node_org.id)
        if node_dest is not None: 
            self.graph.RemoveNode(node_dest.id)
        self.ctx_triples = []
        if ptrs is None:
            return
        
        base_triples = f"({p_pointing}; ser apontado por; \"usuario final\")\n({p_pointing}; ser; \"ponto ou local no espaço\")\n"
        self.graph.AddNode(SemanticNode(p_pointing))
        if ptrs.start_right_on is None:
            base_triples += f"({p_pointing};ser provável; \"local destino em comandos\")\n"\
                f"({p_pointing}; ser provável; \"local origem em comandos\")\n"\
                f"({p_pointing}; provavelmente representar; \"pronome ele ou ela, este, isto, isso\")\n"\
                f"({p_pointing}; provavelmente representar; \"palavras aquele, aquilo, esta, aquela, aqui, ate ali, etc\")\n"
        else:
            self.graph.AddNode(SemanticNode(p_origin))
            base_triples += f"({p_pointing};ser provável; \"local destino em comandos\")\n"\
                f"({p_origin}; ser provável; \"local origem em comandos\")\n"\
                f"({p_pointing}; provavelmente representar; \"pronome ele ou ela, este, isto, isso\")\n"\
                f"({p_pointing}; provavelmente representar; \"palavras aquele, aquilo, esta, aquela, daqui, etc\")\n"\
                f"({p_origin}; provavelmente representar; \"pronome ele ou ela, este, isto, isso\")\n"\
                f"({p_origin}; provavelmente representar; \"palavras aquele, aquilo, esta, aquela, daqui, até ali, etc\")\n"\
                f"({p_origin}; ter sido apontado por; \"usuario final\")\n({p_origin}; ser; \"ponto ou local no espaço\")\n"\
                f"({p_origin}; fazer uma reta até; {p_pointing})|um caminho ou reta entre uma origem e um destino|\n"
        
        for n in ptrs.end_right_on:
            tok = self.GetContextToken(n)
            if tok is not None:
                base_triples += f"({tok};exatamente em;{p_pointing})|estar muito próximo ao ponto ou local apontado|\n"
        
        for n in ptrs.end_near:
            tok = self.GetContextToken(n)
            if tok is not None:
                base_triples += f"({tok};próximo a;{p_pointing})|estar próximo ou local apontado|\n"

        if(ptrs.start_right_on is not None):
            for n in ptrs.start_right_on:
                tok = self.GetContextToken(n)
                if tok is not None:
                    base_triples += f"({tok};exatamente em;{p_origin})|estar muito próximo ao ponto ou local apontado|\n"
        if(ptrs.start_near is not None):
            for n in ptrs.start_near:
                tok = self.GetContextToken(n)
                if tok is not None:
                    base_triples += f"({tok};próximo a;{p_origin})|estar próximo ou local apontado|\n"
        self.ctx_triples = GenerateTriples(self.graph,self.embedder,base_triples)
        for t in self.ctx_triples:
            self.last_subgraph.AddTriple(t,0.9)
        self.last_subgraph.Prune(self.max_triples_subgraph)
        

