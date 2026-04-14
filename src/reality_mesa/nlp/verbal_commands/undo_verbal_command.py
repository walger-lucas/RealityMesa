from spacy.tokens import Span

from reality_mesa.infra.command_queue import CommandQueue,Command,send_command
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.tabletop_engine.tt_commands import UndoTabletopCommand
from reality_mesa.nlp.llm import ask_llm_and_wait
from .verbal_commands import verbal_command, VerbalCommands
import json

class UndoVerbalCommand(VerbalCommands):
    __ACTION_VERB_LEMMA = ("desfazer","voltar","volta")
    def __init__(self) -> None:
        super().__init__()
    @staticmethod
    def activate(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]) -> bool:
        if info["acao"] is not None and info["acao"].lemma_.lower() in UndoVerbalCommand.__ACTION_VERB_LEMMA:
            return True
        return False
    @staticmethod
    def execute(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]):
        send_command(tt_queue,UndoTabletopCommand())

verbal_command(UndoVerbalCommand,0)