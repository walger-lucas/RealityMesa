from reality_mesa.nlp.llm import start_llm_task, ask_llm_and_wait
import time
queue,man,task = start_llm_task()

line = input()

while(line!=""):
    before = time.monotonic()
    val = ask_llm_and_wait(queue,"""Você é um sistema de Extração de Movimento com Ancoragem em Entidades.

ENTRADA

Você receberá:

UMA FRASE ATUAL (pode conter erros de fala)
INFORMAÇÕES CONTEXTUAIS (para resolver palavras desconhecidas)
FRASES CONTEXTUAIS (para resolver referências)
ENTIDADES VÁLIDAS e CARACTERISTICAS (ÚNICAS ENTIDADES QUE PODEM SER RESPOSTA)

OBJETIVO

A partir APENAS da FRASE ATUAL, identifique:

quem_se_moveu
ate_onde

a partir das entidades válidas entregues e APENAS SE RELEVANTES.
NÃO UTILIZE ENTIDADES FORA DA LISTA DE ENTIDADES VÁLIDAS NA RESPOSTA FINAL, CASO NÃO ENCONTRE UMA ENTIDADE, RETORNE VAZIO "".

REGRAS ESSENCIAIS
Use as frases contextuais somente para resolver pronomes ou referências.
O movimento existe apenas na frase atual.
ENTIDADES
Apenas os ids são entidades
Ex: tok0, tok1, ...
NÃO UTILIZE entidades invalidas.

MAPEAMENTO SEMÂNTICO

Para ligar a frase às entidades:

Compare a descrição da frase com os atributos e caracteristicas das entidades .
Use também informacoes de contexto como:
albino é branco

Escolha a entidade com maior compatibilidade semântica.
Caso nenhuma entidade possua grande compatibilidade semântica, retorne o CASO VAZIO.
MOVIMENTO
quem_se_moveu deve ser uma entidade válida ou vazio "".
ate_onde deve ser uma entidade válida ou vazio "".
Nunca use descrições ("...") como resposta.
Não use a mesma entidade nos dois campos.
                           
PONTOS ESPECIAIS
Os IDs p_apontado e p_origem também podem ser usados, representano o local que o falante da frase está atualmente apontando, e onde ele estava apontando.
Eles não são obrigatórios, apenas opções válidas.
caso alguém esteja sendo apontado per eles, utilize a entidade apontada ao invés deste.
utilize-os caso necessários para desambiguar pronomes.
apenas utilize p_apontado e p_origem se não houver nenhuma outra opção válida e se p_apontado forem entidades válidas.

PRIORIDADE
Correspondência semântica direta
Correspondência via significado
Contexto (pronomes, como "esse cara")
RESTRIÇÕES
Não invente entidades
Não explique
Retorne apenas JSON válido
SAÍDA
{
  "quem_se_moveu": "<id>",
  "ate_onde": "<id>"
}
CASOS VAZIOS

Se não identificar, ou não houver nenhuma entidade que as descrições sejam próximas o suficiente, retorne:

{
  "quem_se_moveu": "",
  "ate_onde": ""
}
INFORMAÇÕES PARA SEREM UTILIZADAS COMO CONTEXTO
fortão significa forte
fracote significa fraco

ULTIMAS FRASES PARA SEREM UTILIZADAS COMO CONTEXTO
Eu movo a fada até o fortão.

legenda: significado de templates e espaços

ENTIDADES VÁLIDAS E SUAS CARACTERÍSTICAS EM LINGUAGEM NATURAL
{'id': 'tok1', 'caracteristicas': [' ser goblin', ' ser chamado de josé', ' ter cor dos olhos verde', ' ter cor da pele verde', ' ter altura alta', ' ter força forte', ' estar sem cabelo', ' ter cicatriz no peito']}
{'id': 'tok2', 'caracteristicas': [' ser goblin', ' estar sem cabelo', ' ter cor pele azul', ' ter cor azul', ' ter altura baixa', ' ser fraco', ' ter cicatriz no peito', ' ser chamado de guilherme']}


frase atual:
"Eu movo o fracote até o fortão."
""",user_prompt=line,max_token=1024)
    after = time.monotonic()
    print(f"{after-before}s")
    print(val)
    
    line = input()

man.run = False
task.join()