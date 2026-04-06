from reality_mesa.nlp.sentence_embedding.sentence_embedding import SentenceEmbedder,EmbeddingGenerate,EmbeddingCompare
import time
import numpy as np
from reality_mesa.nlp.semantic_graph import SemanticGraph,SemanticNode,NaturalLanguageNode,SemanticTriple, SemanticSubgraph, SemanticGraphExpandConfig
from reality_mesa.nlp.semantic_graph.semantic_graph import GenerateTriples
from reality_mesa.nlp.llm import start_llm_task

emb = SentenceEmbedder()

# --- Tokens abstratos ---
tok1 = SemanticNode("tok1")
tok2 = SemanticNode("tok2")
tok3 = SemanticNode("tok3")
tok4 = SemanticNode("tok4")
tok5 = SemanticNode("tok5")
tok6 = SemanticNode("tok6")
queue,man,task = start_llm_task()
# --- Grafo ---
graph = SemanticGraph(allow_orphan_nodes=True)
graph.AddNode(tok1)
graph.AddNode(tok2)
text = """
(tok1;ser;"feliz")
(tok2;ser;"triste")
(tok1;amigo de;tok2)|"alguém ser amigo de outro"|
["feliz";significar;"alegre"]
["feliz";oposto de;"triste"]
"""
GenerateTriples(graph,emb,text)
print(graph.ToString(add_time=True))

print("--------------")

embed = emb.embed(["amigo"])
gv = SemanticSubgraph.Create(graph,embed)
print(gv.ToString(show_score=True,show_id=True))

man.run = False
task.join()

