from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.infra.command_queue import CommandQueue, Command, send_command
from reality_mesa.vision.homography.coord_transform import CoordTransformManager
from .hand_gesture_generator import HandData, HandGesture,HandGestureGenerator,FingerEnum
if TYPE_CHECKING:
    from reality_mesa.tabletop_engine.tabletop import Tabletop
from reality_mesa.tabletop_engine.tt_commands import UndoTabletopCommand
import pygame

@HandGestureGenerator.gesture_command
class UndoGesture(HandGesture):
    PRIORITY = 3
    STARTUP_TIME = 0.1
    MIN_TIME_STOP = 0.2

    def __init__(self):
        super().__init__()
        self.cur_pos = None
        self.undo = False
        self.min_stop = 0
        self.hand_id = 0
        
    @staticmethod
    def GestureTest(hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        return (hand.FingerOpen(FingerEnum.INDEX_FINGER) and 
                (not hand.FingerOpen(FingerEnum.MIDDLE_FINGER)) and
                (not hand.FingerOpen(FingerEnum.RING_FINGER)) and
                (hand.FingerOpen(FingerEnum.LITTLE_FINGER)) and hand.FacingCam())
    
    def Awake(self, hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        self.hand_id = hand.id
    def Start(self, hand: HandData, coord_transform: CoordTransformManager, command_queue: CommandQueue[Tabletop], deltatime: float):
        ...
    def Update(self, hand: HandData, coord_transform: CoordTransformManager, command_queue: CommandQueue[Tabletop], deltatime: float):
        if hand.visible:
            if not (hand.FingerOpen(FingerEnum.INDEX_FINGER) and 
                (not hand.FingerOpen(FingerEnum.MIDDLE_FINGER)) and
                (not hand.FingerOpen(FingerEnum.RING_FINGER)) and
                (hand.FingerOpen(FingerEnum.LITTLE_FINGER))):
                self.min_stop += deltatime
                if self.min_stop > self.MIN_TIME_STOP:
                    self.StopCommand()
            elif hand.FacingAwayCam():
                self.undo = True
                self.StopCommand()
            else:
                self.min_stop = 0
            
            return
    def End(self, command_queue: CommandQueue[Tabletop], deltatime: float):
        if self.undo:
            send_command(command_queue,UndoTabletopCommand())
            