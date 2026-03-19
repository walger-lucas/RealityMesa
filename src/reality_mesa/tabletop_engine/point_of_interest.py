from reality_mesa.rendering.camera import Camera

from .tabletop_object import TabletopObject
import pygame
class PointOfInterest(TabletopObject):
    __SHOW_TEXT:bool = False
    def __init__(self,pos:pygame.Vector2, description:str):
        super().__init__()
        self.pos = pos
        self.description = description

    def Start(self):
        ...
    def Remove(self):
        ...

    @staticmethod
    def ShowPOIs(show:bool):
        PointOfInterest.__SHOW_TEXT = show

    @staticmethod    
    def IsShowingPOIs():
        return PointOfInterest.__SHOW_TEXT

    def DrawOverlay(self, surface: pygame.Surface, camera: Camera):
        if PointOfInterest.__SHOW_TEXT:
            camera.DrawWorldText(surface,self.description,self.pos+pygame.Vector2(0,-0.5),pygame.Vector2(0,-15))
            camera.DrawWorldElipse(surface,self.pos,pygame.Vector2(0.2,0.2))