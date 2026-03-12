from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.rendering import Camera
from .tabletop_object import TabletopObject
import pygame
import math

if TYPE_CHECKING:
    from .token_manager import TokenManager


class Token(TabletopObject):
    def __init__(self, description:str , pos: pygame.Vector2, size: pygame.Vector2, image: pygame.Surface):
        self.image = image
        self.pos = pos
        self.size = size
        self.description = description

        self.moving = False
        self.target_end_position = pos
        self.start_position = pos
        self.move_change_position = pos
        self.auto_end_move = False
        self.movable = True
        self.time_to_move = 1.0
        self.cur_time = 0.0
        self.min_speed = 10
        self.max_time_move = 1.5
        self.linear_speed = 0.0

    def Start(self):
        if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.AddToken(self)

    def Remove(self):
        if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.RemoveToken(self.id)

    def Draw(self, surface: pygame.Surface, camera: Camera):
        camera.DrawWorldSpriteCenter(surface,self.image,self.pos,self.size)

    def DrawUnderlay(self, surface: pygame.Surface, camera: Camera):
        if self.movable and self.moving:
            camera.DrawWorldElipse(surface,self.pos,self.size*1.2,camera.pixels_per_unit//5,(255,255,255,127))
            camera.DrawWorldElipse(surface,self.target_end_position,pygame.Vector2(0.2,0.2),0,(255,255,255,127))
        

    def Move(self,end_pos:pygame.Vector2, auto_end = False, allow_overlap = True):
        if not self.movable:
            return
        
        if not allow_overlap and self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            end_pos = self.tabletop.FixToGrid(self.size,end_pos)
            vec = tok_manager.FindEmpty(self.move_change_position,end_pos,self.size,self.size,[self.id])
            if vec:
                end_pos = vec
            else:
                return
            
        if not self.moving:
            self.start_position = self.pos

        self.move_change_position = self.pos
        self.auto_end_move = auto_end
        self.moving = True
        self.cur_time = 0.0
        self.target_end_position = end_pos



        dist = (self.target_end_position - self.move_change_position).length()
        if(dist != 0.0):
            self.linear_speed = self.min_speed*self.max_time_move/dist
        else:
            self.linear_speed = 0.0

    
    def Update(self):
        deltatime = self.tabletop.GetDeltaTime() if self.tabletop else 0.0
        if(self.movable and self.moving):
            self.cur_time+= deltatime
            time = min(1.0,self.cur_time/self.time_to_move)
            pos = -2*time**3/3 + 3*time**2 + time*self.linear_speed
            pos = min(1.0,pos)
            
            if (self.target_end_position - self.pos).length() >0.05:
                self.pos = self.move_change_position.lerp(self.target_end_position,pos)
            else:
                self.pos = self.target_end_position

            if self.auto_end_move and (self.pos - self.target_end_position).length() < 0.05:
                self.pos = self.target_end_position
                self.moving = False
                
                #register move command

    def GetRect(self):
        tok_rect = pygame.FRect(self.pos-self.size/2,self.size)
        return tok_rect
    
    def HitRect(self, rect:pygame.FRect):
        tok_rect = self.GetRect()
        out = tok_rect.colliderect(rect)
        return out
    
    def HitPoint(self, pt:pygame.Vector2):
        tok_rect = self.GetRect()
        return tok_rect.collidepoint(pt)
    
