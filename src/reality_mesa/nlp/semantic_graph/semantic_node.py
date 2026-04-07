import numpy as np
from ..sentence_embedding import SentenceEmbedder


class SemanticNode:
    def __init__(self,node_identifier:str):
        self.node_identifier = node_identifier
        self.__id:int = -1
    
    @property
    def id(self) ->int:
        return self.__id

    
    def SetId(self,id:int):
        if self.id==-1:
            self.__id = id
        else:
            raise ValueError(f"Error tried to set id already set before on '{self.ToString}' node")
        return self.__id
    
    def MatchScore(self,node:"SemanticNode | str"):
        if isinstance(node,"SemanticNode"):
            return 1.0 if self.id == node.id or self.node_identifier == node.node_identifier else 0.0
        else:
            return 1.0 if self.node_identifier == node else 0.0
    
    def ToString(self):
        return str(self.node_identifier)
    
    def ToNaturalLanguage(self):
        return str("")
    

class NaturalLanguageNode(SemanticNode):
    def __init__(self, str:str, embedding: np.ndarray): 
        super().__init__(str)
        self._embedding = embedding

    def MatchScore(self, node: SemanticNode | str):
        if(isinstance(node,NaturalLanguageNode)):
            return max(super().MatchScore(node),SentenceEmbedder.semantic_similarity(self._embedding,node._embedding)[0])
        else:
            return super().MatchScore(node)
        
    def GetSemanticEmbedding(self):
        return self._embedding
    
    def ToString(self):
        return f"\"{str(self.node_identifier)}\""
    
    def ToNaturalLanguage(self):
        return str(self.node_identifier)
        
        








        

    
