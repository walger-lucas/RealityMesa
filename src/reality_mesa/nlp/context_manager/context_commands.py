from __future__ import annotations
from typing import TYPE_CHECKING
from spacy.tokens import Span

from reality_mesa.nlp.context_manager.context_task import ContextTask

if TYPE_CHECKING:
    from .context_task import ContextTask

from reality_mesa.infra import CommandQueue, Command,FutureCommand

class UpdatePointers(Command[ContextTask]):
    def __init__(self) -> None:
        super().__init__()
    def execute(self, input: ContextTask):
        input.UpdateCtx()

class AddToken(Command[ContextTask]):
    def __init__(self,id:int,name:str,description:str) -> None:
        super().__init__()
        self.id = id
        self.name = name
        self.description = description
    def execute(self, input: ContextTask):
        input.ctx.AddElement(self.id,self.name,self.description)
        print(input.ctx.graph.ToString())


class AddTriples(Command[ContextTask]):
    def __init__(self,id:int,name:str,triples:str) -> None:
        super().__init__()
        self.id = id
        self.name = name
        self.triples = triples
    def execute(self, input: ContextTask):
        input.ctx.AddElementTriples(self.id,self.name,self.triples)
        print(input.ctx.graph.ToString())

class RemoveToken(Command[ContextTask]):
    def __init__(self,id:int) -> None:
        super().__init__()
        self.id = id
    def execute(self, input: ContextTask):
        input.ctx.RemoveElement(self.id)

class SegmentText(FutureCommand[ContextTask,list[Span]]):
    def __init__(self,text:str) -> None:
        super().__init__()
        self.text = text

    def _run(self, input: ContextTask):
        return list(input.ctx.GetSentences(self.text))
    
class AddSent(FutureCommand[ContextTask,dict]):
    def __init__(self,sent:Span) -> None:
        super().__init__()
        self.sent = sent

    def _run(self, input: ContextTask):
        _,info =  input.ctx.AddSentence(self.sent)
        return info

    
class UpdateCtx(Command[ContextTask]):
    def __init__(self,update:bool=False) -> None:
        super().__init__()
        self.update = update
        
    def execute(self, input: ContextTask):
        if self.update:
            ln, idrel, iddesc,ids = input.ctx.last_subgraph.DivideContext()
            desc_dict = input.ctx.GetIdDict(iddesc,ids)
            input.ctx.AddPtrToIdDict(desc_dict)
            entities = input.ctx.IdDictToString(desc_dict)
            input.ctx.RemoveContext(entities)
            input.ctx.AddTripleContext(entities)
            input.ctx.AddDictContext(ln)
        input.ctx.not_processed = 0
        ...