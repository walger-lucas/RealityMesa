from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.tabletop_engine.pointer import Pointer
import pygame
import math
from collections import deque
if TYPE_CHECKING:
    from .tabletop import Tabletop

class PointerManager:
    def __init__(self,tabletop:Tabletop):
        self._pointer: dict[int,Pointer] = {}
        self.tabletop = tabletop
        self._pick_pointer:dict[int,int] = {} #picker_id to token
        self._pick_pointer_inverse: dict[int,int] = {} #token to picker_id
        self.focus:list[int] = []

    def AddPointer(self,ptr:Pointer):
        if ptr.id not in self._pointer:
            self._pointer[ptr.id] = ptr
            self.Focus(ptr.id)

    def RemovePointer(self,ptr_id:int):
        if ptr_id in self._pointer:
            self._pointer.pop(ptr_id)
            self.Unfocus(ptr_id)
    
    def GetPointer(self,ptr_id:int):
        if ptr_id in self._pointer:
            return self._pointer[ptr_id]
        else:
            return None
    
    def Focus(self,ptr_id:int):
        new_focus = self.GetPointer(ptr_id)
        if new_focus is None:
            return
        
        if len(self.focus)>0:
            last_focus = self.focus[-1]
            focus_ptr = self.GetPointer(last_focus)
            if focus_ptr is not None:
                focus_ptr.Unfocus()
            else:
                self.focus.pop()
        
        self.focus.append(ptr_id)
        new_focus.Focus()

    def Unfocus(self,ptr_id):
        if len(self.focus)==0:
            return
        last_focus = self.focus[-1]
        focus_ptr = self.GetPointer(last_focus)
        if last_focus == ptr_id and focus_ptr is not None:
            focus_ptr.Unfocus()
        self.focus.remove(ptr_id)

        if len(self.focus)==0:
            return
        
        new_focus = self.focus[-1]

        if last_focus != new_focus:
            focus_ptr = self.GetPointer(new_focus)
            if focus_ptr is not None:
                focus_ptr.Focus()

    def GetFocus(self):
        if len(self.focus)==0:
            return None
        last_focus = self.focus[-1]
        focus_ptr = self.GetPointer(last_focus)
        return focus_ptr
    
    #create ptr on tt fixed position and connected to a hand id
    def PickPointer(self,picker_id:int,ptr:Pointer,position:pygame.Vector2):
        if not self.tabletop.last_camera:
            return
        self._pick_pointer[picker_id] = ptr.id
        pos = self.tabletop.last_camera.Screen2World(position)
        posfixed = self.tabletop.FixToGrid(pygame.Vector2(1,1),pos)
        ptr.MoveEnd(point_end=posfixed)
    
    def PickUpdate(self,picker_id:int,position:pygame.Vector2):
        if not self.tabletop.last_camera:
            return
        if picker_id not in self._pick_pointer:
            return
        ptr = self.GetPointer(self._pick_pointer[picker_id])
        if not ptr:
            return
        pos = self.tabletop.last_camera.Screen2World(position)
        posfixed = self.tabletop.FixToGrid(pygame.Vector2(1,1),pos)
        ptr.MoveEnd(point_end=posfixed)

    def PickEnd(self,picker_id:int,position:pygame.Vector2,time_to_end:float = 5.0):
        if not self.tabletop.last_camera:
            return
        if picker_id not in self._pick_pointer:
            return
        val = self._pick_pointer.pop(picker_id,None)
        if not val:
            return
        ptr = self.GetPointer(val)
        if not ptr:
            return
        
        pos = self.tabletop.last_camera.Screen2World(position)
        posfixed = self.tabletop.FixToGrid(pygame.Vector2(1,1),pos)
        ptr.MoveEnd(point_end=posfixed)
        ptr.StartEndPointer(time_to_end)



