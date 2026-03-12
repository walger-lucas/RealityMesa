import queue
from .command import Command, FutureCommand

from typing import TypeVar, Generic
TInput = TypeVar("TInput")
TResult = TypeVar("TResult")

class CommandQueue(queue.Queue[Command[TInput]],Generic[TInput]):
    def __init__(self,maxsize: int = 0):
        super().__init__(maxsize)
    def process_commands(self,input:TInput):
        while not self.empty():
                command = self.get()
                command.execute(input)

def send_command(command_queue:CommandQueue[TInput],command:Command[TInput], block = True, timeout: None|float = None):
    command_queue.put(command,block,timeout)

def send_future_command(command_queue:CommandQueue[TInput],command:FutureCommand[TInput,TResult], block = True, timeout: None|float = None):
    future = command.GetFuture()
    send_command(command_queue,command,block,timeout)
    return future