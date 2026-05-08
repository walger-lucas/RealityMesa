from spacy.tokens import Span

from reality_mesa.infra.command_queue import CommandQueue,Command,send_command
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.tabletop_engine.tt_commands import MoveCommand
from reality_mesa.nlp.llm import ask_llm_and_wait
from .verbal_commands import verbal_command, VerbalCommands
import json

PROMPT_MOVE ="""Você é um sistema de Extração de Movimento com Ancoragem em Entidades.

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

a partir das entidades válidas entregues.
NÃO UTILIZE ENTIDADES FORA DA LISTA DE ENTIDADES VÁLIDAS NA RESPOSTA FINAL.

REGRAS ESSENCIAIS
Use as frases contextuais somente para resolver pronomes ou referências.
O movimento existe apenas na frase atual.
ENTIDADES
Apenas os ids são entidades
Ex: tok0, tok1, p_apontado, ...
NÃO UTILIZE entidades invalidas.

MAPEAMENTO SEMÂNTICO

Para ligar a frase às entidades:

Compare a descrição da frase com os atributos e caracteristicas das entidades .
Use também informacoes de contexto como:
albino é branco

Escolha a entidade com maior compatibilidade semântica.
MOVIMENTO
quem_se_moveu deve ser uma entidade válida.
ate_onde deve ser uma entidade válida.
Nunca use descrições ("...") como resposta.
Não use a mesma entidade nos dois campos.
PONTOS ESPECIAIS
Os IDs p_apontado e p_origem também podem ser usados, representano o local que o falante da frase está atualmente apontando, e onde ele estava apontando.
Eles não são obrigatórios, apenas opções válidas.
caso alguém esteja sendo apontado per eles, utilize a entidade apontada ao invés deste.
utilize-os caso necessários para desambiguar pronomes.

PRIORIDADE
Correspondência semântica direta
Correspondência via significado
Contexto (pronomes, como "esse cara")
RESTRIÇÕES
Não invente entidades
Não explique
Retorne apenas JSON válido
SAÍDA
{{
"quem_se_moveu": "<id>",
"ate_onde": "<id>"
}}
CASOS VAZIOS

Se não identificar:

{{
"quem_se_moveu": "",
"ate_onde": ""
}}

ULTIMAS FRASES PARA SEREM UTILIZADAS COMO CONTEXTO
{ultimas_frases}

{contexto}
frase atual:
"""

class MoveVerbalCommand(VerbalCommands):
    LEMMA = ("morrer","mover","movor","movar","movir","andar","andor","ander","correr","corrar","corror","voar","ir","fugir","planar","caminhar","galopar")
    def __init__(self) -> None:
        super().__init__()
    @staticmethod
    def activate(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]) -> bool:
        if info["acao"] is not None and info["acao"].lemma_.lower() in MoveVerbalCommand.LEMMA:
            return True
        if(len(sent)>1 and sent[0].text.lower() in  ("mova","movo","mover")):
            return True
        return False
    @staticmethod
    def execute(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]):
        send_command(ctx_queue,
                     MoveCommandCtx(tt_queue,
                                    str(sent.text),
                                    str(PROMPT_MOVE)))

verbal_command(MoveVerbalCommand,10)

class MoveCommandCtx(Command[ContextTask]):
    def __init__(self, tt_queue:CommandQueue[Tabletop],text:str,prompt:str) -> None:
        self.tt_queue = tt_queue
        self.text = text
        self.prompt = prompt
    
    def execute(self, input: ContextTask):
        prompt = self.prompt.format(contexto=input.ctx.GetCtxStr(),
            ultimas_frases=input.ctx.GetSentencesStr(False,False,False))
        print(prompt+"\n"+self.text)
        out =ask_llm_and_wait(input.ctx.llm_queue,prompt,self.text,256,5.0)
        if out is not None:
            try:
                data = json.loads(out)
                if("quem_se_moveu" in data and "ate_onde" in data):
                    org = data["quem_se_moveu"]
                    dest = data["ate_onde"]
                    end= None if input.ctx.pointer is None else input.ctx.pointer.end
                    org_tok = None if org == "p_apontado" else input.ctx.GetTabletopToken(org)
                    dest_org = end if dest == "p_apontado" else input.ctx.GetTabletopToken(dest)
                    if org_tok is not None and dest_org is not None:
                        send_command(self.tt_queue,MoveCommand(org_tok,dest_org))
            except:
                ...

