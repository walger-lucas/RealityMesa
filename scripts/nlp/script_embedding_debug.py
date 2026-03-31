from reality_mesa.nlp.sentence_embedding.sentence_embedding import SentenceEmbedder,EmbeddingGenerate,EmbeddingCompare
import time
import numpy as np

class phrase:
    def __init__(self,txt:str,embedding:np.ndarray):
        self.txt =txt
        self.embedding = embedding
    
    def GetSemanticEmbedding(self):
        return self.embedding
    
    def __str__(self) -> str:
        return f'{self.txt}'
    
    def __repr__(self):
        return self.__str__()
    
frases = [
    "The cat slept quietly on the warm windowsill.",
    "A futuristic city floats above the clouds at sunset.",
    "João bought fresh bread at the bakery this morning.",
    "The algorithm failed due to unexpected null values.",
    "A wizard whispered secrets to the ancient forest.",
    "She forgot her keys and had to climb through the window.",
    "Quantum computers may revolutionize cryptography.",
    "The dog chased a ball across the empty field.",
    "An old library hides forbidden knowledge in dusty books.",
    "The coffee tasted bitter but smelled amazing.",
    "A spaceship drifted silently through deep space.",
    "Maria is studying medicine and law at the same time.",
    "The server crashed after too many simultaneous requests.",
    "A dragon guards a treasure beneath the mountain.",
    "The rain tapped rhythmically against the glass.",
    "He solved the puzzle faster than anyone expected.",
    "Artificial intelligence is changing how we interact with technology.",
    "The child laughed while chasing butterflies in the garden.",
    "A hidden door appeared behind the bookshelf.",
    "The stock market fluctuated wildly during the crisis.",
    "A lone knight wandered through the foggy valley.",
    "The recipe requires eggs, flour, and a pinch of salt.",
    "She sent a message but never received a reply.",
    "The neural network overfitted the training data.",
    "A mysterious signal was detected from a distant galaxy.",
    "The artist painted a surreal landscape of melting clocks.",
    "He trains every day to improve his endurance.",
    "The database query returned inconsistent results.",
    "A ghostly figure appeared at the end of the hallway.",
    "The sun rose slowly over the quiet village.",
    "branco",
    "branca",
    "pele branca",
]

frase_comp = ["branco"]

emb = SentenceEmbedder()
embed = EmbeddingGenerate(emb,frases,lambda s,e: phrase(s,e))
start = time.monotonic() 
embed1 = emb.embed(frase_comp)
print(f"sec:{time.monotonic()-start}")
sim = EmbeddingCompare(embed1.squeeze(),embed)
print(sim)

