from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.vision.hand_tracking import HandsManager,debug_hand_tracking
from reality_mesa.vision.homography import CharucoCoordTransformManager
from reality_mesa.infra import CommandQueue
from threading import Thread
from reality_mesa.vision.hand_gesture_manager import HandGestureGenerator
import cv2
import time
import numpy as np
if TYPE_CHECKING:
    from reality_mesa.tabletop_engine import Tabletop


class VisionManager:
    def __init__(self,tabletop_queue:CommandQueue[Tabletop]):
        self.command_queue:CommandQueue[VisionManager] = CommandQueue()
        self.__running = True
        self.homography_transform = CharucoCoordTransformManager()
        self.hand_manager = HandsManager(45,1920,1920)
        self.cap: None | cv2.VideoCapture = None
        self.hand_gesture_generator = HandGestureGenerator(tabletop_queue)
    
    def process_commands(self):
        self.command_queue.process_commands(self)

    def Stop(self):
        self.__running = False

    def StartCamera(self,cam_id:int = 0, fps:int=45,size:tuple[int,int]=(1920,1080),max_time:float=5.0):
        self.cap = None
        self.hand_manager = HandsManager(fps,size[0],size[1])
        self.cap = cv2.VideoCapture(cam_id, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, size[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, size[1])
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc(*'MJPG'))
        start_time = time.monotonic()
        self.fps = fps
        while time.monotonic()-start_time < max_time:
            ret, _ = self.cap.read()
            if ret:
                return True
        return False
    
    def StopCamera(self):
        self.cap = None

    def Run(self):
        while self.__running:
            self.process_commands()
            if not self.cap:
                continue
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            rgb = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            hands, removed = self.hand_manager.RunVision(rgb)
            self.homography_transform.DebugImage(frame)
            debug_hand_tracking.debug_draw_hand_manager(frame,self.hand_manager)
            self.hand_gesture_generator.Update(hands,removed,self.homography_transform,1/self.fps)

            


            cv2.imshow("Tracked Hands", frame)
            cv2.waitKey(int(1000/self.fps))
            #time.sleep(1/self.fps)

def start_vision_task(tabletop_queue:CommandQueue[Tabletop])->CommandQueue[VisionManager]:
    manager = VisionManager(tabletop_queue)
    queue = manager.command_queue
    task = Thread(target=vision_task,args=(manager,))
    task.start()
    return queue

def vision_task(manager:VisionManager):
    manager.Run()
