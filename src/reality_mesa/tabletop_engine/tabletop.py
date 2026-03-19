from .tabletop_object import TabletopObject
import pygame
from reality_mesa.rendering import Camera
from reality_mesa.tabletop_engine.token_manager import TokenManager
from reality_mesa.tabletop_engine.pointer_manager import PointerManager
import time
from reality_mesa.infra import CommandQueue, send_future_command, send_command
from reality_mesa.vision.vision_manager import VisionManager, start_vision_task, GetCharucoBoard, CalibrateWithCharuco, StartCamera

class Tabletop:
    def __init__(self,image:pygame.Surface,tabletop_size:tuple[int,int], unit:str = "m",unit_size:float=1.5, cam_config = None):
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
        self.tabletop_queue: CommandQueue[Tabletop] = CommandQueue()
        self.vision_queue: CommandQueue[VisionManager] = start_vision_task(self.tabletop_queue)
        self.calibrate = False
        self.calibration_image = None
        self.calibration_done = None
        self.last_camera:None |Camera = None
        self.remove_list = []
        if not cam_config:
            cam_config = {}
        if (send_future_command(self.vision_queue,StartCamera(cam_config.pop("cam_id",0),cam_config.pop("fps",45),cam_config.pop("resolution",(1920,1080)))).result()):
            self.Calibrate()
        



    def __GetId(self):
        id = self.__id_count
        self.__id_count+=1
        return id
    
    def AddObject(self,obj:TabletopObject):
        obj._SetupObject(self,self.__GetId())
        self.__objects[obj.id] = obj
        obj.Start()

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

        if not self.calibration_image:
            img = send_future_command(self.vision_queue,GetCharucoBoard(sqr_length_px=px_size,size_squares=size_sqr)).result()
            self.calibration_image = pygame.surfarray.make_surface(img.swapaxes(0, 1))
            self.calibration_done = send_future_command(self.vision_queue,CalibrateWithCharuco((px_size,px_size),None,max_timeout=15))
        if self.calibration_done is not None and self.calibration_done.done():
            self.calibration_image = None
            self.calibrate = False
        else:
            surface.blit(self.calibration_image,(px_size,px_size))
        
        
