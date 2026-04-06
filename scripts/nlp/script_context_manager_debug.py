from reality_mesa.nlp.context_manager.context_manager import ContextManager
from reality_mesa.tabletop_engine.tabletop import PointerCtx
import time
from reality_mesa.nlp.llm import ask_llm_and_wait
import pygame
ctx = ContextManager()

id = 1
print(f"- a - adicionar tripla:\n- p - pesquisar em grafo\n- d - deletar histórico de pesquisa\n- l - perguntar\n- u - update pointers")
text = input()
while(text!=""):
    if text == "a":
        print(f"descricao tok{id}:")
        text = input()
        while(text!=""):
            start = time.monotonic()
            ctx.AddElement(id,f"tok{id}",text)
            print(f" {time.monotonic()-start}s to process---------------------")
            print(ctx.graph.ToString())
            print("---------------------")
            id+=1
            print(f"descricao tok{id}:")
            text = input()
    elif(text=="p"):
        while(text!=""):
            print(f"pesquisar: ")
            text = input()
            if text == "":
                break
            start = time.monotonic()
            sents = ctx.GetSentences(text)
            for s in sents:
                ctx.AddSentence(s)
            print(ctx.GetSentencesStr()+"\n"+ctx.GetSubgraphStr())
            print("---------------------")
    elif(text=="d"):
        ctx.ClearSubgraph()
    elif(text =="l"):
         while(text!=""):
            print(f"perguntar: ")
            text = input()
            if text == "":
                break
            start = time.monotonic()
            sents = ctx.GetSentences(text)
            sem = None
            for s in sents:
                sem ,_ =ctx.AddSentence(s)
            txt ="responda as perguntas dadas sobre tokens ids e relacoes a partir das triplas abaixo:\n"+ ctx.GetSentencesStr(True) + "\n"+ ctx.GetSubgraphStr(True,True)
            print(ask_llm_and_wait(ctx.llm_queue,txt,"pergunta: \n"+text,2048,15))
            if sem is not None:
                print(sem.ToString(show_score=True))
            print(f" {time.monotonic()-start}s to process---------------------")
    elif(text=="u"):
        print("add ponto destino? y/n")
        text = input()
        if text != "y":
            ptr = None
        else:
            
            print("quais toks estao bem no ponto de destino? tok1;tok2;tok3")
            text = input()
            end_exact = text.split(sep= ";")
            end_exact = [ctx.GetTabletopToken(t.strip()) for t in end_exact]
            end_exact = [t for t in end_exact if t is not None]
            print("quais toks estao proximos do ponto de destino? tok1;tok2;tok3")
            text = input()
            end_near = text.split(sep= ";")
            end_near = [ctx.GetTabletopToken(t.strip()) for t in end_near]
            end_near = [t for t in end_near if t is not None]
            print("add ponto inicio? y/n")
            text = input()
            if text != "y":
                ptr = PointerCtx(pygame.Vector2(0,0),end_exact,end_near)
            else:
                print("quais toks estao bem no ponto de inicio? tok1;tok2;tok3")
                text = input()
                start_exact = text.split(sep= ";")
                start_exact = [ctx.GetTabletopToken(t.strip()) for t in start_exact]
                start_exact = [t for t in start_exact if t is not None]
                print("quais toks estao proximos do ponto de destino? tok1;tok2;tok3")
                text = input()
                start_near = text.split(sep= ";")
                start_near = [ctx.GetTabletopToken(t.strip()) for t in start_near]
                start_near = [t for t in start_near if t is not None]
                ptr = PointerCtx(pygame.Vector2(0,0),end_exact,end_near,pygame.Vector2(0,0),start_exact,start_near)
        if ptr is not None:
            print(ptr.end_right_on)
            print(ptr.end_near)
        start = time.monotonic()
        ctx.UpdatePointers(ptr)
        print(f" {time.monotonic()-start}s to process---------------------")
        print(ctx.graph.ToString())
        print("---------------------")
    print(f"- a - adicionar tripla:\n- p - pesquisar em grafo\n- d - deletar histórico de pesquisa\n- l - perguntar\n- u - update pointers")
    text = input()


print("closing")
ctx.llm_manager.run = False
ctx.llm_task.join()