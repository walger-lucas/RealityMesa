
import os
from sentence_transformers import SentenceTransformer
from typing import TypeVar, Generic, Callable, Protocol
import numpy as np

class HasGetSemanticEmbedding(Protocol):
    def GetSemanticEmbedding(self)-> np.ndarray:
        ...

TEmbedded = TypeVar("TEmbedded",bound=HasGetSemanticEmbedding)
TEmbeddedGenerate = TypeVar("TEmbeddedGenerate")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models/portuguese-bge-m3")

class SentenceEmbedder:

    THRESHOLD_CONSTANT = 0.4
    POWER_CONSTANT = 0.6
    def __init__(self,model = None):
        if model==None:
            model=MODEL_PATH
        self.model = SentenceTransformer(model,device="cpu")

    def embed(self,sentences, normalize = True)->np.ndarray:
        emb = self.model.encode(sentences=sentences)
        if normalize:
            return self.normalize(emb)
        else:
            return emb

    @staticmethod
    def normalize(emb):        
        norm = np.linalg.norm(emb, axis=-1, keepdims=True)
        norm[norm == 0] = 1  # prevent division by zero
        return emb/norm
    
    @staticmethod
    def similarity(sentence_a:np.ndarray,sentence_b:np.ndarray) -> np.ndarray | float:
        return np.dot(sentence_a, sentence_b)
    @staticmethod
    def semantic_similarity(a: np.ndarray, b: np.ndarray):
        a = np.atleast_2d(a)
        b = np.atleast_2d(b)

        sim = a @ b.T  # (n, m)
        sim = np.clip(sim, -1.0, 1.0)

        # threshold + power
        p = SentenceEmbedder.POWER_CONSTANT
        t = SentenceEmbedder.THRESHOLD_CONSTANT

        score = np.zeros_like(sim)
        mask = sim >= t
        score[mask] = ((sim[mask] - t) / (1 - t)) ** p
        return score.squeeze()  # squeeze for 1D if input was 1D

class EmbeddingCompareMatrix(Generic[TEmbedded]):
    def __init__(self,size:int):
        self.nodes:list[TEmbedded] = []
        self.size = size
        self.count = 0
        self._embedding_matrix = None

    def AppendNode(self, node:TEmbedded):
        if self._embedding_matrix is None:
            self._embedding_matrix = np.empty((self.size, len(node.GetSemanticEmbedding())))

        if self._embedding_matrix.shape[1] != len(node.GetSemanticEmbedding()):
            raise ValueError(
                f"Embedding dimension mismatch: "
                f"expected {self._embedding_matrix.shape[1]}, got {len(node.GetSemanticEmbedding())}"
            )
        if self.count < self.size:
            self._embedding_matrix[self.count] = node.GetSemanticEmbedding()
        else:
            self._embedding_matrix = np.vstack([self._embedding_matrix, node.GetSemanticEmbedding().reshape(1, -1)])

        self.nodes.append(node)
        self.count += 1

    def Similarity(self,embedding) -> list[tuple[TEmbedded,float]]:
        if(self._embedding_matrix is not None):
            sim = SentenceEmbedder.semantic_similarity(embedding,self._embedding_matrix)
            return [(node,similarity) for node, similarity in zip(self.nodes,sim)]
        else:
            return []
        
def EmbeddingCompare(embedding,nodes:list[TEmbedded]) -> list[tuple[TEmbedded,float]]:
    embeddings = [node.GetSemanticEmbedding().reshape(1, -1) for node in nodes]
    if len(nodes)<1:
        return []
    
    embedding_matrix = np.vstack(embeddings) if len(nodes)>1 else embeddings[0]
    sim = SentenceEmbedder.semantic_similarity(embedding,embedding_matrix)
    
    sim = np.atleast_1d(sim)
    return [(node,similarity) for node, similarity in zip(nodes,sim)]

def EmbeddingGenerate(embedder:SentenceEmbedder, 
                      str_list:list[str],
                      generator:Callable[[str,np.ndarray],TEmbeddedGenerate] = lambda s,e : (s,e)) -> list[TEmbeddedGenerate]:
    embedded:np.ndarray = embedder.embed(str_list)
    return [generator(s,e) for s,e in zip(str_list,embedded)]

