

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

---
This project utilizes the llama-server executable for Windows 64x CUDA 12.4, you may need to exchange the specific dlls and executables of llama-server on the corresponding directory for one that is compatible with your operating system and graphics card. Releases for these binary files, and github to build it by source code is [available on github](https://github.com/ggml-org/llama.cpp/releases).