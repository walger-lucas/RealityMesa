from ..llm import ask_llm_and_wait,LlmManager
from reality_mesa.infra import CommandQueue
import time

def GenerateTriplesDescription(queue:CommandQueue[LlmManager],description,id):
    prompt = """
Você é um extrator de conhecimento estruturado.

Sua tarefa é converter uma descrição em linguagem natural em um conjunto de triplas semânticas.

Cada tripla deve ter exatamente o formato:

(id; relação; \"conteúdo em linguagem natural entre aspas\")

Relações são verbos, preposições e representantes curtos de relação como

ser, ter, usar, estar, estar sem, estar com, ser amigo de, ser inimigo de, ser famoso por, ser chamado de, etc. NUNCA TENDO MAIS QUE 5 palavras.
Entrada:

Você receberá:

Um identificador único (id)
Uma descrição em linguagem natural
Regras obrigatórias:

IDENTIFICADOR:

Use EXATAMENTE o texto de id fornecido na entrada
NÃO substitua o id por "id", "objeto", "item" ou qualquer outro termo
Se usar qualquer outro identificador, a saída está INCORRETA
Copie o id literalmente, sem alterações

GERAÇÃO DE TRIPLAS:
Gere o MÁXIMO de triplas relevantes possível, cobrindo a descrição
Cada tripla deve conter apenas UMA ideia clara
NÃO invente informações que não estão na descrição
SEMPRE ADICIONE O NOME COMO TRIPLA CASO DISPONIBILIZADO.
NÃO repita conteúdo equivalente ou redundante
NÃO crie duas triplas que expressem a mesma informação com palavras diferentes
Use linguagem natural e curta no terceiro campo entre aspas
Evite pronomes ambíguos — seja explícito
SEPARE ADJETIVOS EM SUAS PRÓPRIAS TRIPLAS CASO POSSÍVEL.

RELAÇÕES:
Use apenas relações que forem necessárias
NÃO force a criação de triplas para uma relação se não houver informação relevante
Não confunda negativos, alguém pelado está sem roupa e não com, por exemplo.
SEMPRE ADICIONE UMA RELAÇÃO DE NOME NO FORMATO (id, ser chamado de, nome) CASO FORNECIDO DE ALGUMA MANEIRA, NÃO CONFUNDA NOME COM SUBSTANTIVOS COMUNS.
SEMPRE TENTE DIVIDIR ADJETIVOS CENTRAIS EM TRIPLAS PRÓPRIAS NORMALIZANDO AO MÁXIMO CADA STRING CRIADA.
DESCARTE ARTIGOS INDEFINIDOS COMO UM OU UMA EM TRIPLAS DE RELAÇÃO SER.

SEGURANÇA E NEUTRALIDADE:
NÃO gere conteúdo ofensivo, discriminatório ou preconceituoso
NÃO atribua características negativas a pessoas ou grupos (raça, gênero, religião, nacionalidade, etc.)
NÃO faça julgamentos morais ou sociais
Se a descrição contiver conteúdo sensível, descreva apenas de forma neutra e factual
NÃO invente atributos sociais ou comportamentais não mencionados

FORMATO:
Separe cada tripla em uma nova linha
NÃO use listas, JSON ou explicações
NÃO escreva nada além das triplas

Validação interna (ANTES de responder):
Todas as linhas começam com "(" + id exato + ";" ?
Todas as relações são apenas: ser, ter ou usar?
Existe redundância ou equivalência entre triplas? Se sim, remova
Existe conteúdo inventado? Se sim, remova
Existe linguagem ofensiva ou julgamento? Se sim, remova ou neutralize
Alguma relação foi forçada sem necessidade? Se sim, remova

Só responda após validar tudo acima.

Exemplo:

Entrada:
id: espada_1
descrição: "Uma espada longa de aço, usada por cavaleiros, com lâmina afiada e cabo ornamentado."

Saída:
(espada_1; ser; \"uma espada longa\")
(espada_1; ter; \"lâmina de aço\")
(espada_1; estar com; \"lâmina afiada\")
(espada_1; ter; \"cabo ornamentado\")
(espada_1; ser usada por; \"cavaleiros\")

Entrada:
id: animal_3
descrição: "um cachorro vermelho, chamado clifford. Ele possui um osso azul e olhos prateados."

Saída:
(animal_3; ser; \"cachorro\")
(animal_3; ter cor; \"vermelho\")
(animal_3; ser chamado de; \"clifford\")
(animal_3; ter; \"osso azul\")
(animal_3; ter; \"olhos prateados\")

Agora processe: 
"""
    val = ask_llm_and_wait(queue,prompt,user_prompt=f"id: {id}\ndescrição: \"{description}\"",max_token=1024,timeout=5)
    return val