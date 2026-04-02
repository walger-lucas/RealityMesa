from .semantic_node import SemanticNode
from ..sentence_embedding import SentenceEmbedder
from enum import IntEnum
import numpy as np
import time

class TRIPLE_TYPE(IntEnum):
    COMMON_TRIPLE = 0
    MAIN_TRIPLE = 1
    REDUCED_TRIPLE = 2

#TODO TRANSFORM TRIPLE TO DATACLASS
class SemanticTriple:
    def __init__(self,relation:str,
                 relation_embedding: np.ndarray,
                 node_start: SemanticNode,
                 node_end:SemanticNode,
                 bidirectional: bool = False,
                 is_permanent: bool = False,
                 born_time: float|None = None,
                 triple_type:TRIPLE_TYPE = TRIPLE_TYPE.COMMON_TRIPLE):
        self.__relation = relation
        self.__relation_embedding = relation_embedding
        self.__start = node_start
        self.__end = node_end
        self.__bidirectional = bidirectional
        self.__permanent = is_permanent
        self.__born_time = born_time if born_time is not None else time.monotonic()
        self.__type = triple_type
        self.__id:int = -1
    
    @property
    def id(self) ->int:
        return self.__id
    
    @property
    def permanent(self):
        return self.__permanent
    
    @property
    def bidirectional(self):
        return self.__bidirectional
    
    @property
    def relation(self):
        return self.__relation

    def SetId(self,id:int):
        if self.id==-1:
            self.__id = id
        else:
            raise ValueError(f"Error tried to set id already set before on triple '{self.ToString()}'")
        return self.__id
    
    @property
    def triple_type(self):
        return self.__type
    
    @property
    def start(self):
        return self.__start
    
    @property
    def end(self):
        return self.__end
    
    def TimeLived(self,now:float=time.monotonic()):
        return now-self.__born_time
    
    def ToString(self, add_time = False,current_time: float |None = None):
        if current_time is None:
            current_time = time.monotonic()
        string = f"{self.start.ToString()}; {self.__relation}; {self.end.ToString()}"
        base = f"[{string}]" if self.bidirectional else f"({string})"
        sec = int(self.TimeLived(current_time))
        minutes = sec//60
        sec = sec%60
        return base if not add_time else f"'{minutes}m{sec:02}' {base}"
    
    def ToNaturalLanguage(self, add_time = False,current_time: float |None = None):
        if current_time is None:
            current_time = time.monotonic()
        sec = int(self.TimeLived(current_time))
        minutes = sec//60
        sec = sec%60
        base = f"{self.start.ToNaturalLanguage()} {self.__relation} {self.end.ToNaturalLanguage()}"
        time_str = f"{minutes}m{sec:02} ago, {base}"
        return time_str if add_time else base
    
    def MatchScore(self,embedding:np.ndarray):
        return SentenceEmbedder.semantic_similarity(embedding,self.__relation_embedding)

    def GetSemanticEmbedding(self):
        return self.__relation_embedding