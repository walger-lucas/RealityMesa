

# Installation
To install the following, download python  >=3.12 <3.13, then create a venv via the command

python -m venv venv

the activate it by using the command

./venv/Scripts/activate

you may need to tweak permission on windows

after that, do a

pip install .e . --force-reinstall

or

pip install .e .[dev] --force-reinstall

to install pytest and other dev libs with it

after all, you will need to install the llama-server and download the Qwen3-4B-Instruct-2507-Q5_K_M.gguf model from hugging face, accessible from [hugging face](https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF), if you decide to use other model, it must not use thinking tags, and you need to change the path to it at src\reality_mesa\nlp\llm\llm.py. 

*If your computer manages llama-server for cuda 12*, 
you may run the following script

python ./setup.py

this will automatically download the model and correct llama-server, it will also download the spacy portuguese pipeline, to download this 
    python -m spacy download pt_core_news_lg,

It will also install torch for cuda 12.x, to use the gpu and cuda for audio.

pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121

---
This project utilizes the llama-server executable for Windows 64x CUDA 12.4, you may need to exchange the specific dlls and executables of llama-server on the corresponding directory for one that is compatible with your operating system and graphics card. Releases for these binary files, and github to build it by source code is [available on github](https://github.com/ggml-org/llama.cpp/releases).
---


# ARTWORKS

a map.png is missing as its art is currently created using assets from [forgotten-adventures](https://www.forgotten-adventures.net/), its copyrights prohibit it from being embedded on vtt software. This art will be remade in a simpler way for the repository.
The presentation will keep using the older map, it just wont be available through the repo.

The token art is made out of public domain art from Lehmann's illustrations, based on Hey's fables ( Paul Horst-Schulze and Otto Richard Bossert 1911) accessed via [artvee](https://artvee.com/wall-charts/lehmanns-illustrations-based-on-heys-fables/).