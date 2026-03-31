from reality_mesa.nlp.llm import start_llm_task, ask_llm_and_wait
import time
queue,man,task = start_llm_task()

line = input()

while(line!=""):
    before = time.monotonic()
    val = ask_llm_and_wait(queue,"""Você é um extrator de triplas semânticas.

Converta uma descrição em triplas no formato EXATO:

(id, relação, conteúdo)

Entrada:
id
descrição
Regras:

Formato e id:

Use EXATAMENTE o id fornecido
Cada linha deve ser: (id, relação, conteúdo)
Uma tripla por linha
Não escreva nada além das triplas

Relações permitidas:

ser (identidade, natureza)
ter (atributos, partes, estados)
usar (ações, funções) 
outras como: achar, estar, considerar, etc.
Use relações apenas quando fizer sentido e não sendo ambíguas

Conteúdo:

Máximo de cobertura possível
Uma ideia por tripla
Não inventar informações
Não repetir ou parafrasear o mesmo conteúdo
Linguagem curta e clara, sem pronomes ambíguos

Segurança:

Não gerar conteúdo ofensivo, discriminatório ou julgamentos
Ignorar partes problemáticas da descrição
Se não restar conteúdo válido → resposta vazia (nenhuma linha)
Nunca explicar, avisar ou recusar
Validação (antes de responder):
Todas seguem (id, relação, conteúdo)?
Não tem redundância ou invenção
Conteúdo não é de cunho preconceituoso.
Se não houver conteúdo válido retorne vazio
Exemplo:

Entrada:
id: espada_1
descrição: "Uma espada longa de aço, usada por cavaleiros, com lâmina afiada e cabo ornamentado."

Saída:
(espada_1, ser, uma espada longa)
(espada_1, ter, lâmina de aço)
(espada_1, ter, lâmina afiada)
(espada_1, ter, cabo ornamentado)
(espada_1, usar, ser usada por cavaleiros)

""",user_prompt=line,max_token=1024)
    after = time.monotonic()
    print(f"{after-before}s")
    print(val)
    
    line = input()

man.run = False
task.join()