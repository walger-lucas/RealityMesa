import subprocess
import time
import signal
import requests
from typing import Optional, List
import os
from openai import OpenAI
import threading

class LlamaServer:
    def __init__(
        self,
        model_path: str,
        host: str = "127.0.0.1",
        port: int = 8080,
        ctx_size: int = 4096,
        n_threads: Optional[int] = None,
        n_gpu_layers: Optional[int] = 999,
        ubatch_size = 512,
        batch_size = 4096,
        mmap: bool = True,
        mlock: bool = False,
        kv_offload: bool = True,
        extra_args: Optional[List[str]] = None,
        executable: str = "llama-server",
        startup_wait: float = 3.0,
        verbose:bool = False
    ):
        self.model_path = model_path
        self.host = host
        self.port = port
        self.ctx_size = ctx_size
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.mmap = mmap
        self.mlock = mlock
        self.kv_offload = kv_offload
        self.extra_args = extra_args or []
        self.executable = executable
        self.startup_wait = startup_wait
        self.batch_size = batch_size
        self.ubatch_size = ubatch_size
        self.verbose = False

        self.process: Optional[subprocess.Popen] = None
        self._client: Optional[OpenAI] = None

    # -------------------------
    # Command construction
    # -------------------------
    def _build_command(self) -> List[str]:
        cmd = [
            self.executable,
            "-m", self.model_path,
            "--host", self.host,
            "--port", str(self.port),
            "--ctx-size", str(self.ctx_size),
            "--batch-size", str(self.batch_size),
            "--ubatch-size", str(self.ubatch_size),
        ]

        if self.n_threads is not None:
            cmd += ["--threads", str(self.n_threads)]

        if self.n_gpu_layers is not None:
            cmd += ["--n-gpu-layers", str(self.n_gpu_layers)]

        if self.kv_offload:
            cmd.append("--kv-offload")

        if not self.mmap:
            cmd.append("--no-mmap")

        if self.mlock:
            cmd.append("--mlock")

        cmd.extend(self.extra_args)
        return cmd

    # -------------------------
    # Lifecycle
    # -------------------------
    def start(self, verbose: bool = True, warmup: bool = True):
        if self.process and self.process.poll() is None:
            raise RuntimeError("llama-server already running")
        
        cmd = self._build_command()
        print(cmd)

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=os.environ,
        )

        threading.Thread(
            target=self._reader,
            args=(self.process.stdout,),
            daemon=True,
        ).start()

        threading.Thread(
            target=self._reader,
            args=(self.process.stderr,),
            daemon=True,
        ).start()

        self._wait_ready()

        if warmup:
            self._warmup()

        return self

    def stop(self):
        if not self.process:
            return

        # Try graceful shutdown via API
        try:
            requests.post(f"http://{self.host}:{self.port}/shutdown", timeout=2)
        except Exception:
            pass

        # Fallback: terminate process
        try:
            self.process.terminate()
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()

        self.process = None

    def _reader(self, pipe):
        if(not self.verbose):
            return
        try:
            for line in iter(pipe.readline, ''):
                print(f"[llama] {line}", end="")
        finally:
            pipe.close()


    def _wait_ready(self, timeout=60):
        url = f"http://{self.host}:{self.port}/v1/models"
        start = time.perf_counter()

        while time.perf_counter() - start < timeout:
            # Drain logs
            # Check HTTP
            try:
                if requests.get(url, timeout=1).status_code == 200:
                    self.startup_time = time.perf_counter() - start
                    return
            except Exception:
                pass

            time.sleep(0.1)

        raise RuntimeError("llama-server did not become ready")

    # -------------------------
    # Warmup
    # -------------------------
    def _warmup(self):
        url = f"http://{self.host}:{self.port}/v1/chat/completions"

        payload = {
            "model": "warmup",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 1,
            "temperature": 0.0,
        }

        for _ in range(10):
            try:
                requests.post(url, json=payload, timeout=2)
                return
            except requests.exceptions.RequestException:
                time.sleep(0.5)

    # -------------------------
    # OpenAI-compatible client
    # -------------------------
    @property
    def client(self) -> OpenAI:
        """
        Lazily creates and returns an OpenAI-compatible client
        connected to this llama-server instance.
        """
        if self.process is None or self.process.poll() is not None:
            raise RuntimeError("llama-server is not running")

        if self._client is None:
            self._client = OpenAI(
                base_url=f"http://{self.host}:{self.port}/v1",
                api_key="not-needed",
            )

        return self._client

    # -------------------------
    # Context manager
    # -------------------------
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
