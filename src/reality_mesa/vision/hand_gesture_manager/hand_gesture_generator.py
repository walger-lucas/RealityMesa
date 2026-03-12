from __future__ import annotations
from typing import TYPE_CHECKING
from reality_mesa.vision.hand_tracking.hand_data import HandData,FingerEnum
from reality_mesa.infra import CommandQueue
from reality_mesa.vision.homography import CoordTransformManager
from abc import abstractmethod, ABC
if TYPE_CHECKING:
    from reality_mesa.tabletop_engine import Tabletop
class HandGesture(ABC):
    STARTUP_TIME : float = 0.0
    PRIORITY:int = 0
    def __init__(self):
        self.__time_start = 0
        self.__started = False
        self.__stop= False
        
    def ValidateTest(self,hand: HandData,coord_transform:CoordTransformManager,command_queue:CommandQueue[Tabletop], deltatime: float):
        if self.__started:
            return True
        self.__time_start += deltatime
        if not self.GestureTest(hand,coord_transform,deltatime):
            return False
        if self.__time_start >= self.STARTUP_TIME:
            self.__started = True
        return True
    
    @property
    def started(self):
        return self.__started
    @property
    def stop(self):
        return self.__stop
    
    def StopCommand(self):
        self.__stop = True

    @staticmethod
    @abstractmethod
    def GestureTest(hand: HandData,coord_transform:CoordTransformManager, deltatime: float)->bool:
        ...

    def Awake(self,hand: HandData,coord_transform:CoordTransformManager, deltatime: float):
        """Run after creation of object, use it to store information that may not be available later"""
        ...
    
    def Start(self,hand: HandData,coord_transform:CoordTransformManager,command_queue:CommandQueue[Tabletop], deltatime: float):
        """Run after object starts to be running"""
    
    def Update(self,hand: HandData,coord_transform:CoordTransformManager,command_queue:CommandQueue[Tabletop], deltatime: float):
        """Updates itself"""
        ...
    
    def End(self,command_queue:CommandQueue[Tabletop], deltatime: float):
        """Run after hand stopped being seen or StopCommand Called"""
        ...

    @classmethod
    def StartupGesture(cls,hand: HandData,coord_transform:CoordTransformManager, deltatime: float) -> "HandGesture | None":
        if cls.GestureTest(hand,coord_transform,deltatime):
            obj = cls()
            obj.Awake(hand,coord_transform,deltatime)
            return obj
        return None

class HandGestureData :
    def __init__(self):
        self.active_hand_gesture:HandGesture| None = None
        self.hand_gestures:dict[type[HandGesture],HandGesture] = {}

class HandGestureGenerator:
    gestureCommands: list[type[HandGesture]] = []
    def __init__(self,command_queue:CommandQueue[Tabletop]):
        self.__hands: dict[int,HandGestureData] = {}
        self.command_queue = command_queue
    @staticmethod
    def gesture_command(gest_type:type[HandGesture]):
        HandGestureGenerator.gestureCommands.append(gest_type)
        HandGestureGenerator.gestureCommands.sort(key=lambda c: c.PRIORITY, reverse=True)
        return gest_type

    def Update(self,hands:dict[int,HandData],removed: list[int],coord_transform:CoordTransformManager,deltatime: float):
        for id in removed:
            if id in self.__hands:
                hand = self.__hands.pop(id)
                if(hand.active_hand_gesture):
                    hand.active_hand_gesture.End(self.command_queue,deltatime)
        for id, hand in hands.items():
            if id not in self.__hands:
                self.__hands[id] = HandGestureData()
            h = self.__hands[id]
            priority = h.active_hand_gesture.PRIORITY if h.active_hand_gesture else float("-inf")
            for commands in HandGestureGenerator.gestureCommands:
                if commands.PRIORITY <= priority or commands in h.hand_gestures:
                    continue
                obj = commands.StartupGesture(hand,coord_transform,deltatime)
                if obj:
                    h.hand_gestures[commands] = obj

            remove:list[type[HandGesture]] = []
            for gest_type, gestures in h.hand_gestures.items(): 
                if gestures.started:
                    continue
                if gestures.PRIORITY <= priority:
                    remove.append(gest_type)
                    continue
                verify = gestures.ValidateTest(hand,coord_transform,self.command_queue,deltatime)
                if not verify:
                    remove.append(gest_type)
                    continue
                if not gestures.started:
                    continue
                if h.active_hand_gesture:
                    h.active_hand_gesture.End(self.command_queue,deltatime)
                    remove.append(type(h.active_hand_gesture))
                h.active_hand_gesture = gestures
                h.active_hand_gesture.Start(hand,coord_transform,self.command_queue,deltatime)
            for t in remove:
                h.hand_gestures.pop(t,None)

            if h.active_hand_gesture:
                h.active_hand_gesture.Update(hand,coord_transform,self.command_queue,deltatime)
                if h.active_hand_gesture.stop:
                    h.active_hand_gesture.End(self.command_queue,0)
                    h.hand_gestures.pop(type(h.active_hand_gesture))
                    h.active_hand_gesture = None
            




            


            
