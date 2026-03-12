import pygame
import sys
from reality_mesa.tabletop_engine import tabletop, token
from reality_mesa.rendering import Camera
from reality_mesa.vision.vision_manager import StopVisionManager
from reality_mesa.infra import send_command
import time
from reality_mesa.tabletop_engine.pointer import Pointer
pygame.init()

display_id = 1
# Create window
width, height = pygame.display.get_desktop_sizes()[display_id]
screen = pygame.display.set_mode(
    (width, height),
    pygame.NOFRAME,
    display=display_id
)
pygame.display.set_caption("Reality Mesa")

clock = pygame.time.Clock()
running = True
tt_back= pygame.Surface(pygame.Vector2(1000,1000))
tt_back.fill((200,200,200))
token_img = pygame.Surface(pygame.Vector2(50,50))
token_img.fill((255,0,0))
tt = tabletop.Tabletop(tt_back,(10,10))
tok = token.Token("basic",pygame.Vector2(5,5),pygame.Vector2(1,1),token_img)
tt.AddObject(tok)
cam  = Camera((800, 600),50)
cam.pos =  pygame.Vector2(5,5)
tok2 = token.Token("basic",pygame.Vector2(2,2),pygame.Vector2(3,3),token_img)
tt.AddObject(tok2)


while running:
    # --- Event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0:
                tok.Move(pygame.Vector2(2,2),True,False)
            if event.key == pygame.K_1:
                tok.Move(pygame.Vector2(8,8),True,False)
            if event.key == pygame.K_c:
                tt.Calibrate()

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