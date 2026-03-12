from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.infra.command_queue import CommandQueue, Command, send_command
from reality_mesa.vision.homography.coord_transform import CoordTransformManager
from .hand_gesture_generator import HandData, HandGesture,HandGestureGenerator
if TYPE_CHECKING:
    from reality_mesa.tabletop_engine import Tabletop
import pygame

class PinchCommand(Command["Tabletop"]):
    def __init__(self, id:int, position: pygame.Vector2, event:int):
        super().__init__()
        self.id = id
        self.position = position
        self.event = event
    def execute(self, input: Tabletop):
        if self.event == 0:
            input.GetTokenManager().PickToken(self.id,self.position)
        elif self.event == 1:
            input.GetTokenManager().PickUpdate(self.id,self.position)
        else:
            input.GetTokenManager().UnpickToken(self.id,self.position)


@HandGestureGenerator.gesture_command
class PinchGesture(HandGesture):
    PRIORITY = 1

    MIN_TIME_STOP = 0.1

    def __init__(self):
        super().__init__()
        self.cur_pos = None
        self.min_stop = 0
        self.hand_id = 0
    def GetPos(self,hand: HandData,coord_transform: CoordTransformManager)->pygame.Vector2:
        pos = (hand.img_coords[8] + hand.img_coords[4]*2)/3
        p2 = coord_transform.TransformFrom(pos[:2])
        return pygame.Vector2(p2)
        
    @staticmethod
    def GestureTest(hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        return hand.pinch
    
    def Awake(self, hand: HandData, coord_transform: CoordTransformManager, deltatime: float):
        self.hand_id = hand.id
        if hand.visible:
            self.cur_pos = self.GetPos(hand,coord_transform)
    def Start(self, hand: HandData, coord_transform: CoordTransformManager, command_queue: CommandQueue[Tabletop], deltatime: float):
        if(self.cur_pos):
            send_command(command_queue,PinchCommand(hand.id,self.cur_pos,0))
    def Update(self, hand: HandData, coord_transform: CoordTransformManager, command_queue: CommandQueue[Tabletop], deltatime: float):
        if hand.visible:
            self.cur_pos = self.GetPos(hand,coord_transform)
            send_command(command_queue,PinchCommand(hand.id,self.cur_pos,1))
            if not hand.pinch:
                self.min_stop += deltatime
                if self.min_stop > self.MIN_TIME_STOP:
                    self.StopCommand()
            else:
                self.min_stop = 0
            return
    def End(self, command_queue: CommandQueue[Tabletop], deltatime: float):
        if self.cur_pos is not None:
            send_command(command_queue,PinchCommand(self.hand_id,self.cur_pos,2))