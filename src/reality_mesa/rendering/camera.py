import pygame
import math


class Camera:
    def __init__(self, viewport_size, pixels_per_unit=100,font_size = 24):
        self.pos = pygame.Vector2(0, 0)
        self.zoom = 1.0
        self.pixels_per_unit = pixels_per_unit
        self.viewport_size = pygame.Vector2(viewport_size)
        self.font = pygame.font.SysFont("arial", font_size)

    def World2Screen(self, world_pos:pygame.Vector2):
        view = world_pos - self.pos
        view *= self.zoom* self.pixels_per_unit                 
        screen = view + self.viewport_size / 2
        return screen
    
    def Screen2World(self,screen_pos:pygame.Vector2):
        view = screen_pos - self.viewport_size / 2
        view /= self.zoom*self.pixels_per_unit
        world_pos = view+self.pos
        return world_pos
    
    def DrawWorldSprite(self, screen:pygame.Surface, sprite:pygame.Surface,world_pos:pygame.Vector2,world_size:pygame.Vector2):
        pixel_size = world_size* self.zoom*self.pixels_per_unit
        screen_pos = self.World2Screen(world_pos)
        scaled = pygame.transform.scale(
            sprite,
            (int(pixel_size.x), int(pixel_size.y))
        )
        screen.blit(scaled, screen_pos)

    def DrawWorldSpriteCenter(self, screen:pygame.Surface, sprite:pygame.Surface,world_pos:pygame.Vector2,world_size:pygame.Vector2):
        self.DrawWorldSprite(screen,sprite,world_pos-world_size/2,world_size)

    def DrawWorldArrow(self, screen:pygame.Surface, color, start:pygame.Vector2, end:pygame.Vector2, width=2, head_length=0.3, head_width=0.4):

        screen_start = self.World2Screen(start)
        screen_end = self.World2Screen(end)

        pygame.draw.line(screen, color, screen_start, screen_end, width)

        if (start-end).length()<head_length:
            return
        # Direction vector
        dx = screen_end[0] - screen_start[0]
        dy = screen_end[1] - screen_start[1]
        angle = math.atan2(dy, dx)

        # Arrow head points
        left = (
            screen_end[0] - head_length*self.pixels_per_unit * math.cos(angle) + head_width*self.pixels_per_unit * math.sin(angle),
            screen_end[1] - head_length*self.pixels_per_unit * math.sin(angle) - head_width*self.pixels_per_unit * math.cos(angle),
        )

        right = (
            screen_end[0] - head_length*self.pixels_per_unit * math.cos(angle) - head_width*self.pixels_per_unit * math.sin(angle),
            screen_end[1] - head_length*self.pixels_per_unit * math.sin(angle) + head_width*self.pixels_per_unit * math.cos(angle),
        )

        pygame.draw.polygon(screen, color, [screen_end, left, right])

    def DrawWorldText(self,surface:pygame.Surface, text:str, position:pygame.Vector2, pixel_offset: pygame.Vector2= pygame.Vector2(0,0), color=(255, 255, 255), center=False,rotate = 0.0):
        text_surface = self.font.render(text, True, color)
        if rotate != 0:
            text_surface = pygame.transform.rotate(text_surface, rotate)
        text_rect = text_surface.get_rect()
        text_pos = self.World2Screen(position)
        text_pos.x += pixel_offset[0]
        text_pos.y += pixel_offset[1]
        if center:
            text_rect.center = text_pos
        else:
            text_rect.topleft = text_pos
        

        surface.blit(text_surface, text_rect)

    def DrawWorldElipse(self,surface:pygame.Surface,world_pos,world_size, width = 10, color = (255,255,255,30)):
        pixel_size = world_size* self.zoom*self.pixels_per_unit
        screen_pos = self.World2Screen(world_pos)
        rect = pygame.Rect(screen_pos-pixel_size/2,pixel_size)
        pygame.draw.ellipse(surface,color,rect,width)