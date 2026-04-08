from spacy.tokens import Span

from reality_mesa.infra.command_queue import CommandQueue,Command,send_command
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.tabletop_engine.tt_commands import LineCommand
from reality_mesa.nlp.llm import ask_llm_and_wait
from .vocal_commands import vocal_command, VocalCommands
import json

PROMPT_LINE ="""Você é um sistema de Extração de Conexão Linear com Ancoragem em Entidades.

ENTRADA

Você receberá:

UMA FRASE ATUAL (pode conter erros de fala)
INFORMAÇÕES CONTEXTUAIS (para resolver palavras desconhecidas)
FRASES CONTEXTUAIS (para resolver referências)
ENTIDADES VÁLIDAS e CARACTERISTICAS (ÚNICAS ENTIDADES QUE PODEM SER RESPOSTA)

OBJETIVO

A partir APENAS da FRASE ATUAL, identifique:

ponto_inicial
ponto_final

a partir das entidades válidas entregues.

NÃO UTILIZE ENTIDADES FORA DA LISTA DE ENTIDADES VÁLIDAS NA RESPOSTA FINAL.

REGRAS ESSENCIAIS

Use as frases contextuais somente para resolver pronomes ou referências.
A conexão existe apenas na frase atual.

ENTIDADES

Apenas os ids são entidades  
Ex: tok0, tok1, p_apontado, ...

NÃO UTILIZE entidades inválidas.

MAPEAMENTO SEMÂNTICO

Para ligar a frase às entidades:

Compare a descrição da frase com os atributos e características das entidades.
Use também informações de contexto como:
albino é branco

Escolha a entidade com maior compatibilidade semântica.

CONEXÃO LINEAR

A conexão deve representar uma relação linear entre dois pontos.

Inclui conceitos como:
reta, linha, caminho, ligação, trajeto direto, medição linear

Exemplos possíveis:
- "faça uma reta daqui até ali"
- "liga isso até aquilo"
- "meça do ponto A ao ponto B"

DIRECIONALIDADE

A ordem textual define:

origem → destino

Exemplos:
- "de X até Y" → X = ponto_inicial, Y = ponto_final
- "daqui até ali" → daqui = inicial, ali = final

ponto_inicial deve ser uma entidade válida.
ponto_final deve ser uma entidade válida.

Nunca use descrições ("...") como resposta.
Não use a mesma entidade nos dois campos.

PONTOS ESPECIAIS

Os IDs p_apontado e p_origem também podem ser usados, representando:
- p_apontado → para onde o falante aponta agora
- p_origem → de onde ele apontava antes

Eles não são obrigatórios, apenas opções válidas.

Se houver uma entidade sendo apontada, utilize a entidade apontada ao invés deles.

Utilize-os apenas se necessário para desambiguar.

PRIORIDADE

Correspondência semântica direta  
Correspondência via significado  
Contexto (pronomes, como "isso", "aquilo", "ali")

RESTRIÇÕES

Não invente entidades  
Não explique  
Retorne apenas JSON válido  

SAÍDA

{{
"ponto_inicial": "<id>",
"ponto_final": "<id>"
}}

CASOS VAZIOS

Se não identificar:

{{
"ponto_inicial": "",
"ponto_final": ""
}}

ULTIMAS FRASES PARA SEREM UTILIZADAS COMO CONTEXTO
{ultimas_frases}

{contexto}

frase atual:
"""

class LineVocalCommand(VocalCommands):
    __ACTION_VERB_LEMMA = ("medir","meçar","meçer","ligar","conectar")
    __CREATE_VERB_LEMMA = ("criar","fazer","façar")
    
    def __init__(self) -> None:
        super().__init__()
    @staticmethod
    def activate(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]) -> bool:
        if info["acao"] is not None and ( info["acao"].lemma_.lower() in LineVocalCommand.__ACTION_VERB_LEMMA
                or (info["acao"].lemma_.lower() in LineVocalCommand.__CREATE_VERB_LEMMA and len(info["objetos"]))>0 
                and info["objetos"][0].lemma_.lower() in ("linha","reta","caminho")):
            return True
        return False
    
    @staticmethod
    def execute(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]):
        send_command(ctx_queue,
                     LineCommandCtx(tt_queue,
                                    str(sent.text),
                                    str(PROMPT_LINE)))

vocal_command(LineVocalCommand,9)

class LineCommandCtx(Command[ContextTask]):
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
                if("ponto_inicial" in data and "ponto_final" in data):
                    org = data["ponto_inicial"]
                    dest = data["ponto_final"]
                    end= None if input.ctx.pointer is None else input.ctx.pointer.end
                    org_tok = end if org == "p_apontado" else input.ctx.GetTabletopToken(org)
                    dest_org = end if dest == "p_apontado" else input.ctx.GetTabletopToken(dest)
                    if org_tok is not None and dest_org is not None:
                        send_command(self.tt_queue,LineCommand(org_tok,dest_org))
            except:
                ...

