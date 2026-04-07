from reality_mesa.infra import Command, CommandQueue,send_command,send_future_command
from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.nlp.context_manager.context_commands import UpdatePointers,UpdateCtx,SegmentText,AddSent
from .vocal_commands import vocal_commands_registry

class VocalCommandManager():
    def __init__(self,tt_queue:CommandQueue[Tabletop],ctx_queue:CommandQueue[ContextTask]) -> None:
        self.tt_queue = tt_queue
        self.ctx_queue = ctx_queue
        self.run = True

    def ProcessText(self,txt:str):
        send_command(self.ctx_queue,UpdatePointers())
        try:
            sents = send_future_command(self.ctx_queue,SegmentText(txt)).result(15.0)
            
            for sent in sents:
                info = send_future_command(self.ctx_queue,AddSent(sent)).result(15.0)
                for cmd,_ in vocal_commands_registry:
                    if cmd.activate(sent,info,self.tt_queue,self.ctx_queue):
                        cmd.execute(sent,info,self.tt_queue,self.ctx_queue)
                        break
        except:
            ...
        finally:
            send_command(self.ctx_queue,UpdateCtx())

    def Run(self):
        while(self.run):
            txt = input("Falas:")
            self.ProcessText(txt)
    def Stop(self):
        self.run = False

        
from threading import Thread

def start_voice_task(tt_queue: CommandQueue["Tabletop"],ctx_queue: CommandQueue["ContextTask"])->tuple[VocalCommandManager,Thread]:
    manager = VocalCommandManager(tt_queue,ctx_queue)
    task = Thread(target=voice_task,args=(manager,),daemon=False)
    task.start()
    return manager, task

def voice_task(manager:VocalCommandManager):
    manager.Run() 
