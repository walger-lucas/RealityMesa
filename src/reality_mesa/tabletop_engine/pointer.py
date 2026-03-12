from reality_mesa.rendering import Camera
from .tabletop_object import TabletopObject
import pygame
import math


class Pointer(TabletopObject):
    def __init__(self,point_end: pygame.Vector2, point_start: pygame.Vector2|None = None, color = (250,250,250),width=5,subtitle = True):
        super().__init__()
        self.point_start = point_start
        self.point_end = point_end
        self.start_end_timer = False
        self.end_timer = 5.0
        self.color = color
        self.common_color = color
        self.width = width
        self.subtitle = subtitle
        self.focused  = False

    def Start(self):
        tt = self.tabletop
        if tt is None:
            return
        pm = tt.GetPointerManager()
        pm.AddPointer(self)

    def Remove(self):
        tt = self.tabletop
        if tt is None:
            return
        pm = tt.GetPointerManager()
        pm.RemovePointer(self.id)

    def MoveEnd(self, point_end:pygame.Vector2):
        if not self.tabletop:
            return
        self.point_end = self.tabletop.FixToGrid(pygame.Vector2(1,1),point_end)

    def StartEndPointer(self,time_to_end = 5.0):
        self.end_timer = time_to_end
        self.start_end_timer = True

    def Update(self):
        if not self.tabletop:
            return
        if self.start_end_timer:
            self.end_timer -= self.tabletop.GetDeltaTime()
            if self.end_timer < 0.0:
                self.tabletop.RemoveObject(self.id)
    def DrawOverlay(self, surface: pygame.Surface, camera: Camera):
        if self.point_start and self.tabletop:
            v = self.point_end-self.point_start
            center = (self.point_end+self.point_start)/2
            if v.length() < 0.1:
                camera.DrawWorldElipse(surface,self.point_end,pygame.Vector2(0.2,0.2),self.width,self.color)
                return
            v_ort = v.rotate(90)/v.length()
            text = self.tabletop.GetDistanceStr(v.length())
            camera.DrawWorldArrow(surface,self.color,self.point_start,self.point_end,self.width,0.15,0.2)
            ang = pygame.Vector2(1, 0).angle_to(v)
            camera.DrawWorldText(surface,text,center,+v_ort*(18),self.color,True,-ang)
            camera.DrawWorldText(surface,text,center,-v_ort*(18),self.color,True,-ang+180)
        else:
            camera.DrawWorldElipse(surface,self.point_end,pygame.Vector2(0.2,0.2),self.width,self.color)
    
    def Focus(self,focus_color = (255,255,0)):
        self.color = focus_color
        self.focused  = True
    
    def Unfocus(self):
        self.color = self.common_color
        self.focused  = False

    def IsFocused(self):
        return self.focused