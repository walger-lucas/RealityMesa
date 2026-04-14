from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.infra import Command, CommandQueue,FutureCommand
from spacy.tokens import Span

class VerbalCommands:
    @staticmethod
    def activate(sent:Span,info:dict,tt_queue:CommandQueue[Tabletop],ctx_queue:CommandQueue[ContextTask])->bool:
        return False
    
    @staticmethod
    def execute(sent:Span,info:dict,tt_queue:CommandQueue[Tabletop],ctx_queue:CommandQueue[ContextTask]):
        ...


verbal_commands_registry:list[tuple[type[VerbalCommands],int]] = []
def verbal_command(cmd: type[VerbalCommands],priority:int=0):
    verbal_commands_registry.append((cmd,priority))
    verbal_commands_registry.sort(key=lambda k:k[1],reverse=True)