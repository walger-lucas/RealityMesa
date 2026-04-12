from reality_mesa.rendering.camera import Camera

from .tabletop_object import TabletopObject
import pygame

from reality_mesa.infra import send_command
from reality_mesa.nlp.context_manager.context_commands import AddToken, RemoveToken


class PointOfInterest(TabletopObject):
    __SHOW_TEXT:bool = False
    def __init__(self,pos:pygame.Vector2, description:str):
        super().__init__()
        self.pos = pos
        self.description = description

    def Start(self):
         if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.AddPOI(self)
            send_command(self.tabletop.ctx_queue,
                         AddToken(self.id,
                                  f"tok{self.id}",
                                  self.description))
    def Remove(self):
        if self.tabletop:
            tok_manager = self.tabletop.GetTokenManager()
            tok_manager.RemovePOI(self.id)
            send_command(self.tabletop.ctx_queue,
                         RemoveToken(self.id))

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