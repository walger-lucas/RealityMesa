from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from reality_mesa.nlp.context_manager.context_task import ContextTask

from .tabletop_object import TabletopObject
import pygame
from reality_mesa.rendering import Camera
from reality_mesa.tabletop_engine.token_manager import TokenManager
from reality_mesa.tabletop_engine.pointer_manager import PointerManager
from reality_mesa.tabletop_engine.undo_manager import UndoManager
import time
from reality_mesa.infra import CommandQueue, send_future_command, send_command
from reality_mesa.vision.vision_manager import VisionManager, start_vision_task, GetCharucoBoard, CalibrateWithCharuco, StartCamera

class Tabletop:
    def __init__(self,tt_queue:CommandQueue["Tabletop"],ctx_queue:CommandQueue[ContextTask],image:pygame.Surface,tabletop_size:tuple[int,int], unit:str = "m",unit_size:float=1.5, cam_config = None):
        self.__id_count = 0
        self.__objects: dict[int,TabletopObject] = {}
        self.__deltatime = 1.0
        self.__tok_manager = TokenManager(self)
        self.__ptr_manager = PointerManager(self)
        self.__cur_time = time.monotonic()
        self.__tabletop_image = image
        self.tabletop_size = tabletop_size
        self.unit = unit
        self.unit_size = unit_size
        self.tabletop_queue = tt_queue
        self.vision_queue: CommandQueue[VisionManager] = start_vision_task(self.tabletop_queue)
        self.calibrate = False
        self.future_img = None
        self.calibration_image = None
        self.calibration_done = None
        self.last_camera:None |Camera = None
        self.remove_list = []
        self.ctx_queue = ctx_queue
        self.undo_manager = UndoManager()
        if not cam_config:
            cam_config = {}
        send_command(self.vision_queue,StartCamera(cam_config.pop("cam_id",0),cam_config.pop("fps",45),cam_config.pop("resolution",(1920,1080)),120))
        

    def __GetId(self):
        id = self.__id_count
        self.__id_count+=1
        return id
    
    def AddObject(self,obj:TabletopObject):
        obj._SetupObject(self,self.__GetId())
        self.__objects[obj.id] = obj
        obj.Start()

    def GetObject(self,id:int):
        if id in self.__objects:
            return self.__objects[id]
        return None

    def RemoveObject(self,obj_id:int):
        if obj_id in self.__objects:
            self.remove_list.append(obj_id)

    def Update(self):
        now = time.monotonic()
        self.__deltatime = now-self.__cur_time
        self.__cur_time = now
        for obj in self.__objects.values():
            obj.Update()
        self.tabletop_queue.process_commands(self)
        for id in self.remove_list:
            obj = self.__objects.pop(id,None)
            if obj:
                obj.Remove()
        self.remove_list = []

    
    def Draw(self,surface:pygame.Surface, camera:Camera):
        self.last_camera = camera
        camera.DrawWorldSprite(surface,self.__tabletop_image,pygame.Vector2(-0.5,-0.5),pygame.Vector2(self.tabletop_size))
        offset = pygame.Vector2(-0.5,-0.5)*camera.zoom*camera.pixels_per_unit

        for i in range(0,self.tabletop_size[0]+1,1):
            posi = camera.World2Screen(pygame.Vector2(i,0))
            posf = camera.World2Screen(pygame.Vector2(i,self.tabletop_size[1]))
            pygame.draw.line(surface,(255,255,255,150),posi+offset,posf+offset)
        for i in range(0,self.tabletop_size[1]+1,1):
            posi = camera.World2Screen(pygame.Vector2(0,i))
            posf = camera.World2Screen(pygame.Vector2(self.tabletop_size[0],i))
            pygame.draw.line(surface,(255,255,255,150),posi+offset,posf+offset)

        for obj in self.__objects.values():
            obj.DrawUnderlay(surface,camera)

        for obj in self.__objects.values():
            obj.Draw(surface,camera)

        for obj in self.__objects.values():
            obj.DrawOverlay(surface,camera)
    
    def GetDeltaTime(self):
        return self.__deltatime
    
    def GetTokenManager(self):
        return self.__tok_manager
    
    def GetPointerManager(self):
        return self.__ptr_manager
    
    def FixToGrid(self, size:pygame.Vector2,pos: pygame.Vector2) -> pygame.Vector2:
        square = (round(abs(size.x)) % 2 == 0,round(abs(size.y)) % 2 == 0 )
        posnew = (pos[0]-0.5 if square[0] else pos[0],pos[1] if square[1]-0.5 else pos[1])
        pos_grided = [round(posnew[0]), round(posnew[1])]
        pos_grided[0] = max(0,min(self.tabletop_size[0]-1,pos_grided[0]))
        pos_grided[1] = max(0,min(self.tabletop_size[1]-1,pos_grided[1]))

        return pygame.Vector2(pos_grided[0]+0.5 if square[0] else pos_grided[0],pos_grided[1]+0.5 if square[1] else pos_grided[1])
    
    def GetDistanceStr(self,dist_units:float):
        return f"{dist_units*self.unit_size : .1f} {self.unit}"
    
    def Calibrate(self):
        self.calibrate = True
        
    def DoCalibration(self,surface:pygame.Surface):
        size_sqr = (10,6)
        max_w = (surface.get_width()*0.8)//size_sqr[0]
        max_h = (surface.get_height()*0.8)//size_sqr[1]
        px_size = int(min(max_h,max_w))
        
        if self.future_img is None:
            self.future_img = send_future_command(self.vision_queue,GetCharucoBoard(sqr_length_px=px_size,size_squares=size_sqr))
        
        try:
            if self.calibration_image is None and self.future_img is not None and self.future_img.done():
                if self.future_img.cancelled():
                    self.future_img = None
                    self.calibration_image = None
                    self.calibration_done = None
                    self.calibrate = False
                    return
                img = self.future_img.result()
                self.calibration_image = pygame.surfarray.make_surface(img.swapaxes(0, 1))

            if self.calibration_done is None and self.calibration_image is not None:
                self.calibration_done = send_future_command(self.vision_queue,CalibrateWithCharuco((px_size,px_size),None,max_timeout=15))
        
            if self.calibration_done is not None and self.calibration_done.done():
                if self.calibration_done.cancelled():
                    self.future_img = None
                    self.calibration_image = None
                    self.calibration_done = None
                    self.calibrate = False
                    return
                self.future_img = None
                self.calibration_image = None
                self.calibration_done = None
                self.calibrate = False
        except:
                self.future_img = None
                self.calibration_image = None
                self.calibration_done = None
                self.calibrate = False
        
        if self.calibration_image is not None:
            surface.blit(self.calibration_image,(px_size,px_size))
        


    # Will return None if error or no ptr and (([],[]),([],[])|None) for when there is a ptr, with none at the second if it is a point only. first [] is the right on, and second is the near
    def GetPointerCtx(self,max_val:int = 5, distance_normalized:float = 2.0,max_distance_total:float = 8.0):
        if ((ptr_man:=self.GetPointerManager()) is None or
            self.last_camera is None or 
            (ptr := ptr_man.GetFocus()) is None or
            (tok_man :=self.GetTokenManager()) is None):
            return None

        dist = min(distance_normalized/self.last_camera.zoom,max_distance_total)

        end_pos = ptr.point_end
        end_right_on = tok_man.HitPointAll(end_pos)
        end_right_on.sort(key=lambda k: (k.pos - end_pos).length())
        end_right_on = [t.id for t in end_right_on]
        end_right_on = end_right_on[:max_val]

        end_near = tok_man.AllNear(end_pos,dist,end_right_on)
        end_near.sort(key=lambda k: (k.pos - end_pos).length())
        end_near = [t.id for t in end_near]
        end_near = end_near[:max_val]

        start_pos = ptr.point_start
        if start_pos is None:
            return PointerCtx(end_pos,end_right_on,end_near)
        
        start_right_on = tok_man.HitPointAll(start_pos)
        start_right_on.sort(key=lambda k: (k.pos - start_pos).length())
        start_right_on = [t.id for t in start_right_on]
        start_right_on = start_right_on[:max_val]

        start_near = tok_man.AllNear(start_pos,dist,start_right_on)
        start_near.sort(key=lambda k: (k.pos - start_pos).length())
        start_near = [t.id for t in start_near]
        start_near = start_near[:max_val]
        start = (start_right_on,start_near)
        return PointerCtx(end_pos,end_right_on,end_near,
                          start_pos,start_right_on,start_near)

from dataclasses import dataclass

@dataclass    
class PointerCtx:
    end: pygame.Vector2
    end_right_on: list[int]
    end_near: list[int]
    start: pygame.Vector2 | None = None
    start_right_on: list[int] |None = None
    start_near: list[int] | None = None
        
    
        
        
        
