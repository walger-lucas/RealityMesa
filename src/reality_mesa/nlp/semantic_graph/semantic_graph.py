from .semantic_node import SemanticNode,NaturalLanguageNode
from .semantic_triple import SemanticTriple
from ..sentence_embedding import EmbeddingCompare, SentenceEmbedder, EmbeddingGenerate
import time

class SemanticGraph:
    def __init__(self,max_nodes:int=0,min_similarity=0.50,allow_orphan_nodes = False):
        self.__max_nodes = max_nodes
        self.__min_similarity = min_similarity
        self.__id_nodes : dict[int,SemanticNode] = {}
        self.__ln_nodes : dict[int,NaturalLanguageNode] = {}
        self.__triples : dict[int,SemanticTriple] = {}
        self.__tag_find: dict[str,int] = {}
        #ln_node -score- ln_node (how closely 2 tuples ressemble each other)
        self.__equality_graph : dict[int,list[tuple[int,float]]] ={}
        #all edges that exist each node, and if it is forward or backwards
        self.__adj_list: dict[int,list[tuple[int,bool]]] = {}
        self.__radj_list: dict[int,list[tuple[int,bool]]] = {}
        self.__node_id: int = 0
        self.__triple_id: int = 0
        self.__allow_orphan_nodes = allow_orphan_nodes
    
    @property
    def triples(self):
        return [n for n in self.__triples.values()]

    def AddNode(self, node:SemanticNode):
        if node.id in self.__id_nodes:
            return
        
        id = self.__node_id
        node.SetId(id) #may raise an error
        self.__node_id+=1
        self.__id_nodes[id] = node
        self.__tag_find[node.ToString()] = id
        #see proximity and andd to equality graph
        if isinstance(node,NaturalLanguageNode):
            eq_in = []
            nodes = [n for n in self.__ln_nodes.values()]
            
            scores = EmbeddingCompare(node.GetSemanticEmbedding(),
                                        nodes) if len(nodes)>0 else []
            for n, score in scores:
                if score < self.__min_similarity:
                    continue
                eq_in.append((n.id,score))
                self.__equality_graph[n.id].append((id,score))
                self.__equality_graph[n.id].sort(key=lambda k: k[1],reverse=True)
            eq_in.sort(key=lambda k: k[1],reverse=True)
            self.__equality_graph[id] = eq_in
            self.__ln_nodes[id] = node

    def IsValidNode(self, node:SemanticNode):
        return (node.id in self.__id_nodes)
    def IsValidTriple(self,triple:SemanticTriple):
        return (triple.id in self.__triples and 
                self.IsValidNode(triple.start) and
                self.IsValidNode(triple.end))
    
    def GetNode(self,id:int):
        if id in self.__id_nodes:
            return self.__id_nodes[id]
        return None
    def GetTriple(self,id:int):
        if id in self.__triples:
            return self.__triples[id]
        return None

    def RemoveNode(self,id:int):
        node = self.GetNode(id)
        if node is None:
            return
        
        tag = node.ToString()
        self.__tag_find.pop(tag,None)
        self.__id_nodes.pop(id,None)
        self.__ln_nodes.pop(id,None)
        triple1 = self.__adj_list.pop(id,None)#remove all adjacent triples that have id
        if triple1 is not None:
            for t,_ in triple1:
                self.RemoveTriple(t)
        triple2 = self.__radj_list.pop(id,None)#remove all adjacent triples that have this id
        if triple2 is not None:
            for t,_ in triple2:
                self.RemoveTriple(t)
        eq = self.__equality_graph.pop(id,None)
        if eq is not None:
            for i,_ in eq:
                self.__equality_graph[i] = [t for t in self.__equality_graph[i] if t[0] != id]
    
    def __RemoveNodeIfOrphan(self,id):
        if (((id in self.__adj_list and len(self.__adj_list[id]) == 0) or
        id not in self.__adj_list) and 
        ((id in self.__radj_list and len(self.__radj_list[id]) == 0) or id not in self.__radj_list)):
            self.RemoveNode(id)

    def RemoveTriple(self,id:int):
        triple = self.GetTriple(id)
        if triple is None:
            return
        
        if(triple.start.id in self.__adj_list):
            adj = self.__adj_list[triple.start.id]
            adj = [(t,b) for t,b in adj if t!=triple.id]
            self.__adj_list[triple.start.id] = adj
        if(triple.start.id in self.__radj_list):
            adj = self.__radj_list[triple.start.id]
            adj = [(t,b) for t,b in adj if t!=triple.id]
            self.__radj_list[triple.start.id] = adj

        if(triple.end.id in self.__adj_list):
            adj = self.__adj_list[triple.end.id]
            adj = [(t,b) for t,b in adj if t!=triple.id]
            self.__adj_list[triple.end.id] = adj
        if(triple.end.id in self.__radj_list):
            adj = self.__radj_list[triple.end.id]
            adj = [(t,b) for t,b in adj if t!=triple.id]
            self.__radj_list[triple.end.id] = adj

        self.__triples.pop(id,None)
        if not self.__allow_orphan_nodes:
            self.__RemoveNodeIfOrphan(triple.start.id)
            self.__RemoveNodeIfOrphan(triple.end.id)

        

    def AddTriple(self,triple:SemanticTriple):
        if triple.id in self.__triples:
            return
        
        self.AddNode(triple.start)
        self.AddNode(triple.end)

        id = self.__triple_id
        triple.SetId(id) #may raise an error
        self.__triple_id+=1
        self.__triples[id] = triple

        
        if(triple.start.id not in self.__adj_list):
            self.__adj_list[triple.start.id] = []

        if(triple.end.id not in self.__adj_list):
            self.__adj_list[triple.end.id] = []
        
        if(triple.end.id not in self.__radj_list):
            self.__radj_list[triple.end.id] = []

        if(triple.start.id not in self.__radj_list):
            self.__radj_list[triple.start.id] = []

        self.__adj_list[triple.start.id].append((triple.id,True))
        self.__radj_list[triple.end.id].append((triple.id,True))
        

        if triple.bidirectional:
            self.__adj_list[triple.end.id].append((triple.id,False))
            self.__radj_list[triple.start.id].append((triple.id,False))
        
    def ToString(self,add_time:bool = False,current_time:float|None = None):
        text = ""
        for _,t in self.__triples.items():
            text+=t.ToString(add_time,current_time)+"\n"
        return text
    
    def GetAdjacencies(self,node_id:int) ->list[tuple[int,bool]]:
        if node_id in self.__adj_list:
            return self.__adj_list[node_id]
        else:
            return []

    def GetRAdjacencies(self,node_id:int) ->list[tuple[int,bool]]:
        if node_id in self.__radj_list:
            return self.__radj_list[node_id]
        else:
            return []

    def GetEqualities(self,node_id:int) ->list[tuple[int,float]]:
        if node_id in self.__equality_graph:
            return self.__equality_graph[node_id]
        else:
            return []
        
    def TripleInGraph(self,triple:tuple[tuple[str,str,str],tuple[bool,bool],bool],relation: None|str = None):
        nodes,is_str,bidirectional = triple
        start = self.NodeInGraph((nodes[0],is_str[0]))
        end = self.NodeInGraph((nodes[2],is_str[1]))
        node_output = (nodes[0] if start is None else start,nodes[2] if end is None else end)
        if (start is None and not is_str[0]) or (end is None and not is_str[1]):
            return None
        rel_triple = ""
        if start is not None and end is not None:
            adj = self.GetAdjacencies(start.id)
            for t,_ in adj:
                trip = self.GetTriple(t)
                if trip is not None and (trip.end.id == end.id or trip.start.id == end.id) and trip.relation == nodes[1]:
                    return trip
            
            radj = self.GetRAdjacencies(start.id)
            for t,_ in radj:
                trip = self.GetTriple(t)
                if trip is not None and (trip.end.id == end.id or trip.start.id == end.id) and trip.relation == nodes[1]:
                    return trip

            if start.id not in self.__ln_nodes and end.id not in self.__ln_nodes:
                if relation is None:
                    return None
                else:
                    rel_triple = relation

        if (start is None or start.id in self.__ln_nodes) and (end is None or end.id in self.__ln_nodes):
            rel_triple = ' '.join([nodes[0],nodes[1],nodes[2]])
        elif(start is not None and (end is None or end.id in self.__ln_nodes)):
            rel_triple = ' '.join([nodes[1],nodes[2]])
        elif(end is not None and (start is None or start.id in self.__ln_nodes)):
            rel_triple = ' '.join([nodes[0],nodes[1]])
        return (node_output,(nodes[1],rel_triple),bidirectional)

        
        
            
        

    
    def NodeInGraph(self,node:tuple[str,bool]):
        text,certainly_str = node
        node_id = None
        if not certainly_str and text in self.__tag_find:
            node_id = self.GetNode(self.__tag_find[text])
            if node_id is not None:
                return node_id
        
            
        str_text = f"\"{text}\""
        node_str = None
        if certainly_str and str_text in self.__tag_find:
            node_str = self.GetNode(self.__tag_find[str_text])
        return node_str
            
    
#is text
def __normalize_text(text):
    is_str:bool = text.startswith('"')
    return (' '.join(
        text.replace('"', '')
         .lower()
         .strip()
         .split()
    ), is_str)

def GenerateTriples(graph:SemanticGraph,embedder:SentenceEmbedder,input:str):
    class embed_id:
        def __init__(self):
            self.to_embed = []
            self.id = 0
        def add_to_embed(self,txt):
            self.to_embed.append(txt)
            id = self.id
            self.id+=1
            return id
    import re

    embed_id_store = embed_id()

    extract_pattern = r'([\(\[])([^()\[\]]+)([\)\]])(?:\|([^|]*)\|)?'
    split_pattern = r';(?=(?:[^"]*"[^"]*")*[^"]*$)'

    results = []

    for open_b, content, close_b, extra in re.findall(extract_pattern, string=input):
        parts = re.split(split_pattern, content)

        parts = [p.strip() for p in parts]

        is_square = open_b == '['

        parts = [__normalize_text(p) for p in parts]
        parts = [(p, s) for p, s in parts if p != '' and len(p) < 80]

        if len(parts) != 3:
            continue

        extra_norm = __normalize_text(extra)[0] if extra else None

        results.append(((
            (parts[0][0], parts[1][0], parts[2][0]),
            (parts[0][1], parts[2][1]),
            is_square,
        ),extra_norm))

    process = [graph.TripleInGraph(r,e) for r,e in results]
    process_new_nodes= [r for r in process if not isinstance(r,SemanticTriple) and r is not None and r[1][1]]
    new_nodes:list[tuple[int|SemanticNode,int|SemanticNode,tuple[str,int],bool]] = []
    for nodes,relations,bidir in process_new_nodes:
        start = embed_id_store.add_to_embed(nodes[0]) if isinstance(nodes[0],str) else nodes[0]
        end = embed_id_store.add_to_embed(nodes[1]) if isinstance(nodes[1],str) else nodes[1]
        relationship = (relations[0],embed_id_store.add_to_embed(relations[1]))
        new_nodes.append((start,end,relationship,bidir))

    embeddings = EmbeddingGenerate(embedder,embed_id_store.to_embed, lambda s,e:(s,e))

    for start, end, relationship, bidir in new_nodes:
        if isinstance(start,int):
            start= NaturalLanguageNode(embeddings[start][0],embeddings[start][1])
        if isinstance(end,int):
            end= NaturalLanguageNode(embeddings[end][0],embeddings[end][1])    
        triple = SemanticTriple(relationship[0],embeddings[relationship[1]][1],start,end,bidir,born_time=time.monotonic())
        graph.AddTriple(triple)

    

    

    









