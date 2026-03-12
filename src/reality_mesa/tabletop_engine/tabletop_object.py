from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.rendering import Camera
import pygame
if TYPE_CHECKING:
    from .tabletop import Tabletop

class TabletopObject:
    def __init__(self):
        self.__tabletop:Tabletop | None = None
        self.__id = -1

    def _SetupObject(self,tabletop:Tabletop,id:int):
        self.__tabletop:Tabletop | None= tabletop
        self.__id = id
        
    @property
    def id(self):
        return self.__id

    @property
    def tabletop(self):
        return self.__tabletop

    def Start(self):
        pass

    def Update(self):
        pass

    def Remove(self):
        pass

    def Draw(self,surface:pygame.Surface, camera:Camera):
        pass

    def DrawOverlay(self,surface:pygame.Surface, camera:Camera):
        pass

    def DrawUnderlay(self,surface:pygame.Surface, camera:Camera):
        pass
        
        
