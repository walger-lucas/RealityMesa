from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.infra import Command, CommandQueue,FutureCommand
from spacy.tokens import Span

class VocalCommands:
    @staticmethod
    def activate(sent:Span,info:dict,tt_queue:CommandQueue[Tabletop],ctx_queue:CommandQueue[ContextTask])->bool:
        return False
    
    @staticmethod
    def execute(sent:Span,info:dict,tt_queue:CommandQueue[Tabletop],ctx_queue:CommandQueue[ContextTask]):
        ...


vocal_commands_registry:list[tuple[type[VocalCommands],int]] = []
def vocal_command(cmd: type[VocalCommands],priority:int=0):
    vocal_commands_registry.append((cmd,priority))
    vocal_commands_registry.sort(key=lambda k:k[1],reverse=True)