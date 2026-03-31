from typing import TYPE_CHECKING
from dataclasses import dataclass
import time

from . import SemanticGraph
from . import SemanticTriple
from ..sentence_embedding import EmbeddingCompare


@dataclass
class SemanticGraphExpandConfig:
    k_depth:float = 0.08
    k_prompt:float = 0.2
    k_repetition:float = 0.1
    min_similarity:float = 0.25
    max_node_augmentation:int = 6
    k_language_bonus:float = 1.2

class SemanticSubgraph:
    def __init__(self,graph:SemanticGraph, prompt_compare_dict: dict[int,float]):
        self.graph = graph
        self.triples : set[int] = set()
        self.scores: dict[int,float] = {}
        self.orphan_triples: list[SemanticTriple] = []
        self.triples_age: dict[int,float] = {}
        self.frontier: dict[int,set[int]] = {}
        self.origin: set[int] = set()
        self.nodes: set[int] = set()
        self.prompt_compare = {} if prompt_compare_dict is None else prompt_compare_dict

    def AddTriple(self,triple:SemanticTriple,score:float=1.0,age: float | None = None):
        if self.graph.IsValidTriple(triple):
            self.triples.add(triple.id)
            self.scores[triple.id] = score
            self.triples_age[triple.id] = age if age is not None else time.monotonic()
            #self.AddToFrontier(triple.end.id,triple.id)
            #if triple.bidirectional:
            #    self.AddToFrontier(triple.start.id,triple.id)
        else:
            self.orphan_triples.append(triple)

    def PurgeOrphanTriples(self):
        self.orphan_triples = []

    def RemoveTriple(self,id):
        self.triples.discard(id)
        self.scores.pop(id,0)

    def SetAge(self, age: float | None = None):
        if age is None:
            age = time.monotonic()
        for k in self.triples_age:
            self.triples_age[k] = age

    def ToString(self,add_time:bool = False,current_time= None,show_score:bool = True):
        if current_time is None:
            current_time = time.monotonic()
        text = ""
        triples = (self.graph.GetTriple(t) for t in self.triples)
        for triple in triples:
            if triple is None:
                continue
            if show_score:
                text+= f"|{self.scores[triple.id]:.3}|"
            text+= triple.ToString(add_time,current_time) + "\n"
        return text

    #dict of all noded and what triple they came from
    def _GetFrontier(self):
        self.frontier = {}
        triples = (self.graph.GetTriple(t) for t in self.triples)
        for triple in triples:
            if triple is None:
                continue

            self.origin.add(triple.start.id)
            
            self.AddToFrontier(triple.start.id,triple.id)
            self.AddToFrontier(triple.end.id,triple.id)
        return self.frontier
    
    def AddToFrontier(self, id:int,triple:int):
        if id in self.nodes:
            return
        if id in self.frontier:
            self.frontier[id].add(triple)
        else:
            self.frontier[id] = set([triple])

    def PopFromFrontier(self):
        n = self.frontier.popitem()
        self.nodes.add(n[0])
        return n
    
    def Expand(self,n_iterations,config:SemanticGraphExpandConfig|None = None):
        if config is None:
            config = SemanticGraphExpandConfig()
        iterations = n_iterations
        while(iterations>0):
            new_frontier: list[tuple[int,int]] = []
            #empty current frontier
            while(len(self.frontier)>0):
                node, origin_triples = self.PopFromFrontier()
                triples = self._ExpandNode(node,origin_triples,n_iterations-iterations+1,config)
                
                count = 0
                for triple_id, score in triples:
                    triple = self.graph.GetTriple(triple_id)
                    if triple is None:
                        continue

                    if triple.id in self.triples:
                        val = max(self.scores[triple_id],score)
                        self.scores[triple_id] = min(val+ (1-val)*config.k_repetition,1.0)
                    else:
                        if count >= config.max_node_augmentation:
                            break
                        count+=1
                        self.AddTriple(triple,score)
                        new_frontier.append((triple.start.id,triple.id))
                        new_frontier.append((triple.end.id,triple.id))
            #update frontier for next operation
            for n,t in new_frontier:
                self.AddToFrontier(n,t)
            iterations-=1
        
    def _ExpandNode(self,node,origin_triples,iteration,config:SemanticGraphExpandConfig)->list[tuple[int,float]]:
        
        possible_trip = [(trip,1.0) for trip,_ in self.graph.GetAdjacencies(node)]
        possible_trip.extend([(trip,1.0) for trip,_ in self.graph.GetRAdjacencies(node)])
        for n,s in self.graph.GetEqualities(node):
            possible_trip.extend([(trip,s) for trip,_ in self.graph.GetAdjacencies(n)])
            possible_trip.extend([(trip,s) for trip,_ in self.graph.GetRAdjacencies(n)])

        max_score = 0.0
        for t in origin_triples:
            if t in self.scores and self.scores[t]>max_score:
                max_score = self.scores[t]
                
        triples: list[tuple[int,float]] = []
        for t,s in possible_trip:
            if t in origin_triples:
                continue
            score_prompt = self.prompt_compare[t]*config.k_prompt if t in self.prompt_compare else 0.0
            score_origin = min(max_score,s*config.k_language_bonus)*(1-config.k_prompt)
            score = min(score_origin + score_prompt,1.0)
            score *= max(1-config.k_depth*iteration,0)
            if score >= config.min_similarity:
                triples.append((t,score))

        triples.sort(key=lambda t: t[1])
        return triples
    
    def Prune(self,size) -> None:
        triple_score = [(t,self.scores[t]) for t in self.triples]
        triple_score.sort(key=lambda t: t[1])
        leave = max(0, len(self.triples)-size)
        triple_score = triple_score[:leave]
        for t, s in triple_score:
            self.RemoveTriple(t)

    def OldAgeKill(self,max_age:float, current_time:float|None = None):
        current_time = current_time or time.monotonic()
        mark_death = []
        for t in self.triples:
            if current_time-self.triples_age[t] > max_age:
                mark_death.append(t)
        
        for t in mark_death:
            self.RemoveTriple(t)

    def Join(self,subgraph:"SemanticSubgraph",k_repetition:float = 1.1,k_modifier=1.0):
        for triple in subgraph.triples:
            if triple in self.triples:
                val = max(self.scores[triple],subgraph.scores[triple]*k_modifier)
                self.scores[triple] = min(val+ (1-val)*k_repetition,1.0)
            else:
                t = self.graph.GetTriple(triple)
                if t is not None:
                    self.AddTriple(t,subgraph.scores[triple]*k_modifier,subgraph.triples_age[triple])

    
    @staticmethod
    def Create(graph:SemanticGraph,embedding,k_min_similarity = 0.35,quantity = 5):
        triples = graph.triples
        scores = EmbeddingCompare(embedding,
                                        triples) if len(triples)>0 else []
        semantic_compare = {triple.id:sim for triple,sim in scores}
        sg = SemanticSubgraph(graph,semantic_compare)

        scores.sort(key=lambda k: k[1],reverse=True)
        scores = scores[:quantity]
        for t,s in scores:
            if s>k_min_similarity:
                sg.AddTriple(t,s,0)
        sg._GetFrontier()

        return sg