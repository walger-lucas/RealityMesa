import os
import sys
import platform
import urllib.request

# ---------------- CONFIG ---------------- #

LLAMA_VERSION = "v0.2.90"  # example version
LLAMA_BASE_URL = f"https://github.com/ggml-org/llama.cpp/releases/download/b8589/llama-b8589-bin-win-cuda-12.4-x64.zip"
LLAMA_CUDA_DRIVERS = "https://github.com/ggml-org/llama.cpp/releases/download/b8589/cudart-llama-bin-win-cuda-12.4-x64.zip"

MODEL_URL = "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q5_K_M.gguf"

BIN_DIR = "./src/reality_mesa/nlp/llm/llama"
MODEL_DIR = "./src/reality_mesa/nlp/llm/model"

# ---------------------------------------- #

def download_file(url, dest_path):
    if os.path.exists(dest_path):
        print(f"[OK] Already exists: {dest_path}")
        return

    print(f"[DOWNLOADING] {url}")
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"[DONE] Saved to {dest_path}")
    except Exception as e:
        print(f"[ERROR] Failed to download {url}")
        raise e


def get_llama_binary_name():
    system = platform.system().lower()

    if system == "windows":
        return "llama-server.exe"
    elif system == "darwin":
        return "llama-server"
    else:  # linux
        return "llama-server"

def extract_zip(zip_path, extract_to):
    import zipfile

    print(f"[EXTRACTING] {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"[DONE] Extracted to {extract_to}")


def setup_llama():
    
    zip_path = os.path.join(BIN_DIR, "llama.zip")

    download_file(LLAMA_BASE_URL, zip_path)
    extract_zip(zip_path, BIN_DIR)

    # Optional: cleanup
    os.remove(zip_path)
    download_file(LLAMA_CUDA_DRIVERS, zip_path)
    extract_zip(zip_path, BIN_DIR)

    # Optional: cleanup
    os.remove(zip_path)


def setup_model():
    filename = MODEL_URL.split("/")[-1]
    model_path = os.path.join(MODEL_DIR, filename)

    download_file(MODEL_URL, model_path)


def main():
    print("=== SETUP START ===")

    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(MODEL_DIR, exist_ok=True)

    setup_llama()
    setup_model()

    print("=== SETUP COMPLETE ===")


if __name__ == "__main__":
    main()