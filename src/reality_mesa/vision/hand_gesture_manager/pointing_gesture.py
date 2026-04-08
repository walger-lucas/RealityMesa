from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.infra.command_queue import CommandQueue, Command, send_command
from reality_mesa.vision.homography.coord_transform import CoordTransformManager
from .hand_gesture_generator import HandData, HandGesture,HandGestureGenerator,FingerEnum
from reality_mesa.vision.hand_tracking.hand_data import DistanceNorm
if TYPE_CHECKING:
    from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.tabletop_engine.pointer import Pointer
import pygame
import numpy as np
import cv2


class PointCommand(Command["Tabletop"]):
    def __init__(self, id:int, position: pygame.Vector2, event:int,line: bool):
        super().__init__()
        self.id = id
        self.position = position
        self.event = event
        self.line = line
    def execute(self, input: "Tabletop"):
        cam = input.last_camera
        if not cam:
            return
        pos = cam.Screen2World(self.position)
        posfixed = input.FixToGrid(pygame.Vector2(1,1),pos)
        if self.event == 0:
            if self.line:
                point = Pointer(posfixed,posfixed)
            else:
                point = Pointer(posfixed,None)
            input.AddObject(point)
            input.GetPointerManager().PickPointer(self.id,point,self.position)
            
        elif self.event == 1:
            input.GetPointerManager().PickUpdate(self.id,self.position)
        else:
            input.GetPointerManager().PickEnd(self.id,self.position,3)

@HandGestureGenerator.gesture_command
class PointGestureOneFinger(HandGesture):
    PRIORITY = 0
    STARTUP_TIME = 0.1
    MIN_TIME_STOP = 0.4

    def __init__(self):
        super().__init__()
        self.cur_pos = None
        self.min_stop = 0
        self.hand_id = 0
        self.line = False
    def GetPos(self,hand: HandData,coord_transform: CoordTransformManager)->pygame.Vector2:
        pos = hand.img_coords[8]
        p2 = coord_transform.TransformFrom(pos[:2])
        return pygame.Vector2(p2)
        
    @staticmethod
    def GestureTest(hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        return (hand.FingerOpen(FingerEnum.INDEX_FINGER) and 
                (not hand.FingerOpen(FingerEnum.MIDDLE_FINGER)) and
                (not hand.FingerOpen(FingerEnum.RING_FINGER)) and
                (not hand.FingerOpen(FingerEnum.LITTLE_FINGER)))
    
    def Awake(self, hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        self.hand_id = hand.id
        if hand.visible:
            self.cur_pos = self.GetPos(hand,coord_transform)
    def Start(self, hand: HandData, coord_transform: CoordTransformManager, command_queue: CommandQueue[Tabletop], deltatime: float):
        if(self.cur_pos):
            send_command(command_queue,PointCommand(hand.id,self.cur_pos,0,self.line))
    def Update(self, hand: HandData, coord_transform: CoordTransformManager, command_queue: CommandQueue[Tabletop], deltatime: float):
        if hand.visible:
            if not self.GestureTest(hand,coord_transform,deltatime):
                self.min_stop += deltatime
                if self.min_stop > self.MIN_TIME_STOP:
                    self.StopCommand()
            else:
                self.min_stop = 0
                self.cur_pos = self.GetPos(hand,coord_transform)
                send_command(command_queue,PointCommand(hand.id,self.cur_pos,1,self.line))
            return
    def End(self, command_queue: CommandQueue[Tabletop], deltatime: float):
        if self.cur_pos is not None:
            send_command(command_queue,PointCommand(self.hand_id,self.cur_pos,2,self.line))

@HandGestureGenerator.gesture_command
class PointGestureTwoFingers(PointGestureOneFinger):
    PRIORITY = 2
    STARTUP_TIME = 0.1
    MIN_TIME_STOP = 0.4
    def __init__(self):
        super().__init__()
        self.line = True

    @staticmethod
    def GestureTest(hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        if hand.visible:
            two_fingers = (hand.FingerOpen(FingerEnum.INDEX_FINGER) and 
                    (hand.FingerOpen(FingerEnum.MIDDLE_FINGER)) and
                    (not hand.FingerOpen(FingerEnum.RING_FINGER)) and
                    (not hand.FingerOpen(FingerEnum.LITTLE_FINGER)))
            
            dist = hand.FindDistance(8,12,DistanceNorm.NORMALIZE_BY_INDEX)
            return bool((dist < 2) and two_fingers) 
        return False
            
