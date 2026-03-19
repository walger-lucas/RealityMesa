import pygame
import sys
from reality_mesa.rendering import Camera
from reality_mesa.vision.vision_manager import StopVisionManager
from reality_mesa.infra import send_command
import time
from reality_mesa.tabletop_engine.tabletop_reader import tabletop_read,PointOfInterest
pygame.init()

tt, cam, screen = tabletop_read("C:/Users/Administrador/Documents/Projetos/TTRPGMESA/tabletops/tabletop.json")
# Create window

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
time.sleep(0.5)
pygame.quit()
sys.exit()