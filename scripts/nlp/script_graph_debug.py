from reality_mesa.nlp.sentence_embedding.sentence_embedding import SentenceEmbedder,EmbeddingGenerate,EmbeddingCompare
import time
import numpy as np
from reality_mesa.nlp.semantic_graph import SemanticGraph,SemanticNode,NaturalLanguageNode,SemanticTriple, SemanticSubgraph, SemanticGraphExpandConfig


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
    
# --- Frases base ---
frases = [
    "ser",                 #0
    "ser humano",          #1
    "humano",              #2
    "ser médico",          #3
    "médico",              #4
    "trabalhar como",      #5
    "hospital",            #6
    "trabalhar em hospital",#7
    "doente",              #8
    "estar doente",        #9
    "curar",               #10
    "paciente",            #11
    "ser paciente",        #12
    "amigo",               #13
    "ser amigo de",        #14
    "conhecer",            #15
    "cidade",              #16
    "morar em cidade",     #17
    "Curitiba",            #18
    "ser Curitiba",        #19
    "trabalhar em",        #20
    "o amigo do humano que pratica medicina"
]

emb = SentenceEmbedder()
embed = EmbeddingGenerate(emb, frases, lambda s,e: phrase(s,e))

# --- Tokens abstratos ---
tok1 = SemanticNode("tok1")
tok2 = SemanticNode("tok2")
tok3 = SemanticNode("tok3")
tok4 = SemanticNode("tok4")
tok5 = SemanticNode("tok5")
tok6 = SemanticNode("tok6")

# --- Nós de linguagem natural ---
ln_humano   = NaturalLanguageNode(embed[2].txt, embed[2].embedding)
ln_medico   = NaturalLanguageNode(embed[4].txt, embed[4].embedding)
ln_hospital = NaturalLanguageNode(embed[6].txt, embed[6].embedding)
ln_doente   = NaturalLanguageNode(embed[8].txt, embed[8].embedding)
ln_paciente = NaturalLanguageNode(embed[11].txt, embed[11].embedding)
ln_cidade   = NaturalLanguageNode(embed[16].txt, embed[16].embedding)
ln_curitiba = NaturalLanguageNode(embed[18].txt, embed[18].embedding)

# --- Grafo ---
graph = SemanticGraph()

triples = [

    # --- Identidade / classe ---
    SemanticTriple(embed[0].txt, embed[1].embedding, tok1, ln_humano),
    SemanticTriple(embed[0].txt, embed[3].embedding, tok1, ln_medico),

    # --- Profissão / atividade ---
    SemanticTriple(embed[20].txt, embed[7].embedding, tok1, ln_hospital),
    SemanticTriple(embed[20].txt, embed[7].embedding, tok2, ln_hospital),
    SemanticTriple(embed[20].txt, embed[7].embedding, ln_medico, ln_hospital),

    # --- Estado ---
    SemanticTriple(embed[0].txt, embed[9].embedding, tok2, ln_doente),
    SemanticTriple(embed[0].txt, embed[12].embedding, tok2, ln_paciente),

    # --- Ação ---
    SemanticTriple(embed[10].txt, embed[10].embedding, tok1, tok2),

    # --- Relação social ---
    SemanticTriple(embed[14].txt, embed[14].embedding, tok1, tok3, bidirectional=True),
    SemanticTriple(embed[15].txt, embed[15].embedding, tok3, tok4),

    # --- Localização ---
    SemanticTriple(embed[17].txt, embed[17].embedding, tok3, ln_cidade),
    SemanticTriple(embed[17].txt, embed[17].embedding, tok4, ln_curitiba),

    # --- Ontologia (conceitos ligados) ---
    SemanticTriple(embed[0].txt, embed[1].embedding, ln_curitiba, ln_cidade),
    SemanticTriple(embed[0].txt, embed[3].embedding, ln_medico, ln_humano),

    # --- Equivalência semântica parcial ---
    SemanticTriple(embed[4].txt, embed[3].embedding, ln_medico, tok1),
    
    # --- Relação indireta interessante ---
    SemanticTriple(embed[10].txt, embed[10].embedding, tok1, ln_doente),

]

for t in triples:
    graph.AddTriple(t)

print(graph.ToString(add_time=True))

print("-------- gen sg -----------------")

sg = SemanticSubgraph.Create(graph,embed[21].embedding,k_min_similarity=0.35,quantity=4)
sg.SetAge(time.monotonic())
print(sg.ToString())
print("-------- gen sg 2-----------------")
sg.Expand(2,SemanticGraphExpandConfig(k_depth=0.15,k_prompt=0.35,k_repetition=0.03,min_similarity=0.25))
print(sg.ToString())


