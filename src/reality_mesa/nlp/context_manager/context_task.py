from __future__ import annotations
from typing import TYPE_CHECKING
from queue import Empty

if TYPE_CHECKING:
    from reality_mesa.tabletop_engine.tabletop import PointerCtx, Tabletop
    

from reality_mesa.infra import CommandQueue, send_future_command
from .context_manager import ContextManager
from reality_mesa.tabletop_engine.tt_commands import GetPointerCtx

class ContextTask:
    def __init__(self,tt_queue: CommandQueue["Tabletop"],ctx_queue: CommandQueue["ContextTask"]) -> None:
        self.tabletop_queue = tt_queue
        self.ctx_queue = ctx_queue
        self.ctx = ContextManager(8,120,40)
        self.run = True


    def UpdateCtx(self):
        try:
            ptr = send_future_command(self.tabletop_queue,GetPointerCtx(7,1.5,8),timeout=1.0)
            self.ctx.UpdatePointers(ptr.result(1.0))
        except:
            ...

    def Run(self):
        while self.run:
            try:
                command = self.ctx_queue.get(timeout=2)
                command.execute(self)
            except Empty:
                ...
            except Exception as e:
                raise 
        self.ctx.llm_manager.run = False
        self.ctx.llm_task.join()

    def Stop(self):
         self.run = False

from threading import Thread

def start_ctx_task(tt_queue: CommandQueue["Tabletop"],ctx_queue: CommandQueue["ContextTask"])->tuple[ContextTask,Thread]:
    manager = ContextTask(tt_queue,ctx_queue)
    task = Thread(target=ctx_task,args=(manager,),daemon=False)
    task.start()
    return manager, task

def ctx_task(manager:"ContextTask"):
    manager.Run()    
