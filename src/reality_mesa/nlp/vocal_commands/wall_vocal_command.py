from spacy.tokens import Span

from reality_mesa.infra.command_queue import CommandQueue,send_command
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.tabletop_engine.wall_token import wallTypeRegistry,CreateWall
from .vocal_commands import vocal_command, VocalCommands

class WallVocalCommand(VocalCommands):
    __ACTION_VERB_LEMMA = ("transformar")
    def __init__(self) -> None:
        super().__init__()
    @staticmethod
    def activate(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]) -> bool:
        if info["acao"] is not None and info["acao"].lemma_.lower() in WallVocalCommand.__ACTION_VERB_LEMMA:
            obj = [o.lemma_.lower() for o in info["objetos"]]
            if(set(obj) & set(["linha","reta","seta"])):
                return True
        return False
    @staticmethod
    def execute(sent: Span, info: dict, tt_queue: CommandQueue[Tabletop], ctx_queue: CommandQueue[ContextTask]):
        for wall_type,wall_data in wallTypeRegistry.items():
            if(any(t.text in wall_data.MATERIALS for t in sent)):
                send_command(tt_queue,CreateWall(wall_type))
                break

vocal_command(WallVocalCommand,0)