from reality_mesa.infra import Command, CommandQueue,send_command,send_future_command
from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.nlp.context_manager.context_task import ContextTask
from reality_mesa.nlp.context_manager.context_commands import UpdatePointers,UpdateCtx,SegmentText,AddSent
from .vocal_commands import vocal_commands_registry
from RealtimeSTT import AudioToTextRecorder
from spacy.tokens import Span
class VocalCommandManager():
    def __init__(self,tt_queue:CommandQueue[Tabletop],ctx_queue:CommandQueue[ContextTask],recorder:AudioToTextRecorder) -> None:
        self.tt_queue = tt_queue
        self.ctx_queue = ctx_queue
        self.run = True
        self.recorder = recorder
    def ProcessText(self,txt:str):
        send_command(self.ctx_queue,UpdatePointers())
        update_ctx = False;
        try:
            sents = send_future_command(self.ctx_queue,SegmentText(txt)).result(15.0)
            for sent in sents:
                info = send_future_command(self.ctx_queue,AddSent(sent)).result(15.0)
                for cmd,_ in vocal_commands_registry:
                    if cmd.activate(sent,info,self.tt_queue,self.ctx_queue):
                        cmd.execute(sent,info,self.tt_queue,self.ctx_queue)
                        break
                update_ctx |= self.ShoudUpdate(sent)
        except Exception as e:
            print(f"Ocorreu um erro: {e}")
        finally:
            send_command(self.ctx_queue,UpdateCtx(update_ctx))

    def Run(self):
        
        while(self.run):
            txt = self.recorder.text()
            if(self.run):
                if isinstance(txt,str):
                    print("falante: " + txt)
                    self.ProcessText(txt)
    def Stop(self):
        self.run = False
        self.recorder.shutdown()

    def ShoudUpdate(self,sent:Span) -> bool:
        ACTIVATION_VERBS = ("ser","estar","ter","significar","dizer")
        if(any(t.lemma_ in ACTIVATION_VERBS for t in sent)):
            return True
        return False


        
from threading import Thread

def start_voice_task(tt_queue: CommandQueue["Tabletop"],ctx_queue: CommandQueue["ContextTask"],stt_help:list[str])->tuple[VocalCommandManager,Thread]:

    
    prompt = "Palavras relevantes: \n" + 'mover\nandar\nfazer linha\nmova o\nmovo\ntransformar\nfaça reta\n'+ '\n'.join(stt_help)
    print(prompt)
    recorder = AudioToTextRecorder(language="pt",model='medium',initial_prompt=prompt
                                   ,initial_prompt_realtime=prompt,post_speech_silence_duration=0.2)
    manager = VocalCommandManager(tt_queue,ctx_queue,recorder)
    task = Thread(target=voice_task,args=(manager,),daemon=True)
    task.start()
    return manager, task

def voice_task(manager:VocalCommandManager):
    manager.Run() 
