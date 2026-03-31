from .semantic_node import SemanticNode,NaturalLanguageNode
from .semantic_triple import SemanticTriple
from ..sentence_embedding import EmbeddingCompare
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

    
        







