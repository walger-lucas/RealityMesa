from typing import TypeVar, Generic
from abc import abstractmethod, ABC
from concurrent.futures import Future

TInput = TypeVar("TInput")
TResult = TypeVar("TResult")

class Command(ABC,Generic[TInput]):

    @abstractmethod
    def execute(self, input:TInput):
        """Subclasses must implement this."""
        pass


class FutureCommand(Command[TInput], Generic[TInput, TResult]):
    def __init__(self):
        super().__init__()
        self.future: None | Future[TResult]  = None

    def GetFuture(self):
        if self.future is None:
            self.future = Future()
        return self.future
    
    @abstractmethod
    def _run(self,input:TInput) -> TResult:
        """Subclasses must implement this."""
        pass

    def SetFuture(self,obj:TResult):
        if self.future is None:
            return
        self.future.set_result(result=obj)

    def execute(self, input:TInput):
        out = self._run(input=input)
        self.SetFuture(obj=out)


