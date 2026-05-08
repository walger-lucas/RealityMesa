import pygame
import sys
from reality_mesa.vision.vision_manager import StopVisionManager
from reality_mesa.infra import send_command, CommandQueue
from reality_mesa.tabletop_engine.tabletop_reader import tabletop_read,PointOfInterest,Tabletop
from reality_mesa.nlp.context_manager.context_task import ContextTask, start_ctx_task
from reality_mesa.nlp.verbal_commands import start_voice_task
import time
def main():
    pygame.init()

    tt_queue: CommandQueue[Tabletop] = CommandQueue()
    ctx_queue: CommandQueue[ContextTask] = CommandQueue()
    
    ctx, ctx_task = start_ctx_task(tt_queue,ctx_queue)
    tt, cam, screen,stt = tabletop_read(tt_queue,
                                    ctx_queue,
                                    "C:/Users/Administrador/Documents/Projetos/TTRPGMESA/tabletops/tabletop.json")
    # Create window
    voice_manager,voice_task = start_voice_task(tt_queue,ctx_queue,stt)
    pygame.display.set_caption("Reality Mesa")

    clock = pygame.time.Clock()
    running = True

    while running:
        # --- Event handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c:
                    tt.Calibrate()
                if event.key == pygame.K_1:
                    cam.zoom = min(cam.zoom +0.25 , 10)
                if event.key == pygame.K_2:
                    cam.zoom = max(0.25,cam.zoom-0.25)
                if event.key == pygame.K_UP:
                    cam.pos += pygame.Vector2(0,-1)
                if event.key == pygame.K_DOWN:
                    cam.pos += pygame.Vector2(0,1)
                if event.key == pygame.K_LEFT:
                    cam.pos += pygame.Vector2(-1,0)
                if event.key == pygame.K_RIGHT:
                    cam.pos += pygame.Vector2(1,0)
                if event.key == pygame.K_p:
                    PointOfInterest.ShowPOIs(not PointOfInterest.IsShowingPOIs()) 

        # --- Update logic ---
        # (nothing yet)

        tt.Update()

        # --- Draw ---
        screen.fill((30, 30, 30))  # background color

        tt.Draw(screen,cam)
        if(tt.calibrate):
            tt.DoCalibration(screen)

        pygame.display.flip()
        clock.tick(60)  # limit to 60 FPS

    send_command(tt.vision_queue,StopVisionManager())



    ctx.Stop()
    ctx_task.join()

    voice_manager.Stop()
    voice_task.join()

    time.sleep(0.5)
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()