from .llama_talks import LlamaServer
from reality_mesa.infra import CommandQueue, FutureCommand, send_future_command
from threading import Thread
import signal
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model/Qwen_Qwen3-4B-Instruct-2507-Q5_K_M.gguf")
LLAMA_SERVER_PATH = os.path.join(BASE_DIR, "llama/llama-server.exe")

class LlmManager:
    def __init__(self, model_path = None, executable_path = None,ctx_size = 4096) -> None:
        if model_path is None:
            model_path = MODEL_PATH
        if executable_path is None:
            executable_path = LLAMA_SERVER_PATH
        self.command_queue: CommandQueue[LlmManager] = CommandQueue()
        self.server = LlamaServer(model_path=model_path,
                                  executable=executable_path,
                                    port=7666,
                                    ctx_size=ctx_size,        # or 16k if model supports it well
                                    n_gpu_layers=999,
                                    batch_size=512,
                                    ubatch_size=128,
                                    kv_offload=True
                                    )
        self.run = True
        self.client = None

    def Run(self):
        
        try:
            with self.server:
                self.client = self.server.client

                while self.run:
                    self.command_queue.process_commands(self)

        except Exception as e:
            print("[LlmManager] Error:", e)

        finally:
            print("[LlmManager] Cleanup complete")

    def _handle_signal(self, signum, frame):
        print(f"\n[LlmManager] Received signal {signum}")
        self.run = False

    def register_signals(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)


        

def start_llm_task()->tuple[CommandQueue[LlmManager],LlmManager,Thread]:
    manager = LlmManager()
    manager.register_signals()
    queue = manager.command_queue
    task = Thread(target=llm_task,args=(manager,),daemon=False)
    task.start()
    return queue, manager, task

def llm_task(manager:LlmManager):
    manager.Run()

class LlmProcessCommand(FutureCommand[LlmManager,str|None]):
    def __init__(self,system_prompt:str,user_prompt:str,max_token:int = 512):
        super().__init__()
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
        self.max_tok = max_token

    def _run(self, input: LlmManager) -> str | None:
        if input.client is None:
            return None
        
        response = input.client.chat.completions.create(
                model="local-model",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": self.user_prompt},
                ],
                max_tokens=self.max_tok,
                temperature=0.0,
                top_p=1.0,
                seed=42,
                frequency_penalty=0.0,
                presence_penalty= 0.0,
            )
        if(len(response.choices)<1):
            return None
        
        answer = response.choices[0].message.content

        return answer
    
def ask_llm_and_wait(queue:CommandQueue[LlmManager],system_prompt:str,user_prompt:str,max_token:int = 512,timeout = 5.0):
    try:
        return send_future_command(queue,
                               LlmProcessCommand(
                                    system_prompt=system_prompt,
                                    user_prompt=user_prompt,
                                    max_token=max_token)).result(timeout=timeout)
    except:
        return None