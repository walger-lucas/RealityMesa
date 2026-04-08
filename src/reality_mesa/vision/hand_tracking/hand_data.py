import numpy as np
from enum import IntEnum
from dataclasses import dataclass

class DistanceNorm(IntEnum):
    DONT_NORMALIZE = 0
    NORMALIZE_BY_INDEX = 1
    NORMALIZE_BY_KNUCKLE = 2

class FingerEnum(IntEnum):
    INDEX_FINGER = 0
    MIDDLE_FINGER = 1
    RING_FINGER = 2
    LITTLE_FINGER = 3


def GetFingerNode(finger_id: FingerEnum, node:int) ->int:
    FINGER_NODES = {
        FingerEnum.INDEX_FINGER : (5,6,7,8),
        FingerEnum.MIDDLE_FINGER : (9,10,11,12),
        FingerEnum.RING_FINGER : (13,14,15,16),
        FingerEnum.LITTLE_FINGER : (17,18,19,20),
    }
    if node >=0 and node < len(FINGER_NODES[finger_id]):
        return FINGER_NODES[finger_id][node]
    return 0

@dataclass(frozen=True)
class HandData:
    id:int
    visible: bool
    img_coords: np.ndarray
    world_coords: np.ndarray
    left_hand: bool
    finger_open: list[int]
    pinch: bool
    normal_status: int
    normal_vec: np.ndarray

    def FingerOpen(self,finger_id: FingerEnum):
        return self.finger_open[finger_id] >=2
    
    def FingerClosed(self,finger_id: FingerEnum):
        return self.finger_open[finger_id] == 0
    
    def FacingCam(self):
        return self.normal_status == 0
    
    def FacingAwayCam(self):
        return self.normal_status == 2

    def FindNormal(self,a,b,c):
        BA = self.world_coords[a] - self.world_coords[b]
        BC = self.world_coords[c] - self.world_coords[b]

        BA /= np.linalg.norm(BA)
        BC /= np.linalg.norm(BC)
    
        cross = np.cross(BA, BC)
        return cross if not self.left_hand else -cross
    
    def FindAngle(self,a,b,c):
        BA = self.world_coords[a] - self.world_coords[b]
        BC = self.world_coords[c] - self.world_coords[b]

        # normalized
        BA /= np.linalg.norm(BA)
        BC /= np.linalg.norm(BC)
    
        dot = np.dot(BA, BC)
        return np.arccos(dot)
    
    def FindDistance(self,a,b,normalization = DistanceNorm.DONT_NORMALIZE):
        BA = self.world_coords[a] - self.world_coords[b]
        dist = np.linalg.norm(BA)
        if normalization == DistanceNorm.DONT_NORMALIZE:
            return dist
        elif normalization == DistanceNorm.NORMALIZE_BY_INDEX:
            norm = np.linalg.norm(self.world_coords[11]-self.world_coords[12])
        else:
            norm = np.linalg.norm(self.world_coords[0]-self.world_coords[9])
        return dist/norm

class HandTracker:
    __FINGER_ACTIVATION = {
        FingerEnum.INDEX_FINGER : (0.5,0.6,0.60),
        FingerEnum.MIDDLE_FINGER : (0.5,0.6,0.67),
        FingerEnum.RING_FINGER : (0.5,0.6,0.67),
        FingerEnum.LITTLE_FINGER : (0.5,0.6,0.67),
    }
    __PINCH_ACTIVATION = (1.8,2.4)
    __DIRECTION_ACTIVATION = (-0.5,0.5)
    __ACTIVATION_HITCOUNT = 1/64

    def __init__(self,id,is_left_hand,position,landmarks,world_landmarks,cur_frame,delta_time:float=1):
        self.id = id
        self.left_hand = is_left_hand
        self.landmarks: np.ndarray = landmarks
        self.position: np.ndarray = position
        self.world_landmarks: np.ndarray = world_landmarks

        self.finger_activation = {FingerEnum.INDEX_FINGER : 0,
                                 FingerEnum.MIDDLE_FINGER : 0,
                                 FingerEnum.RING_FINGER : 0,
                                 FingerEnum.LITTLE_FINGER : 0}
        self.pinch_distance = 50
        self.pinch_hit_count = 0

        #hitcounts
        self.finger_hit_counts: dict[FingerEnum,float] = {FingerEnum.INDEX_FINGER : 0.0,
                                FingerEnum.MIDDLE_FINGER : 0.0,
                                FingerEnum.RING_FINGER : 0.0,
                                FingerEnum.LITTLE_FINGER : 0.0}
        self.pinch_hit_count = 0
        self.normal_vec = np.array([0,0,1],np.float32)
        self.normal_value = 0
        self.Update(position,landmarks,world_landmarks,cur_frame,delta_time)

    def Update(self,position,landmarks,world_landmarks,cur_frame,delta_time: float=1.0):
        self.deltatime = delta_time
        self.frame = cur_frame
        self.visible:bool = landmarks is not None
        if self.landmarks is None:
            self.landmarks = landmarks
            self.world_landmarks = world_landmarks
        #lastely update positions
        if self.visible:
            self.__UpdateBoundingBox()
            self.__ProcessFingerOpening()
            self.__ProcessPinchPosition()
            self.__HandNormal()
        
            self.landmarks = landmarks
            self.world_landmarks = world_landmarks
        self.position = position

    def __UpdateBoundingBox(self):
        self.top_left_bounding_box = self.landmarks.min(axis=0)
        self.bottom_right_bounding_box = self.landmarks.max(axis=0)


    def __HandNormal(self):
        self.normal_vec = self.FindNormal(0,5,17)
        
        self.normal_value = np.dot(self.normal_vec,np.array([0,0,1]))
        

    def FindNormal(self,a,b,c):
        BA = self.world_landmarks[a] - self.world_landmarks[b]
        BC = self.world_landmarks[c] - self.world_landmarks[b]
        
        BA /= np.linalg.norm(BA)
        BC /= np.linalg.norm(BC)
    
        cross = np.cross(BA, BC)
        return cross if self.left_hand else -cross
    
    def FindAngle(self,a,b,c):
        BA = self.world_landmarks[a] - self.world_landmarks[b]
        BC = self.world_landmarks[c] - self.world_landmarks[b]

        # normalized
        BA /= np.linalg.norm(BA)
        BC /= np.linalg.norm(BC)
    
        dot = np.dot(BA, BC)
        return np.arccos(dot)
    
    def FindDistance(self,a,b,normalization = DistanceNorm.DONT_NORMALIZE):
        BA = self.landmarks[a] - self.landmarks[b]
        dist = np.linalg.norm(BA)
        if normalization == DistanceNorm.DONT_NORMALIZE:
            return dist
        elif normalization == DistanceNorm.NORMALIZE_BY_INDEX:
            norm = np.linalg.norm(self.landmarks[11]-self.landmarks[12])
        else:
            norm = np.linalg.norm(self.landmarks[0]-self.landmarks[9])
        return dist/norm
    
    def __ProcessFingerOpening(self):
        for finger in list(FingerEnum):
            degrees1 = self.FindAngle(GetFingerNode(finger,0),GetFingerNode(finger,1),GetFingerNode(finger,3))
            degrees2 = self.FindAngle(0,GetFingerNode(finger,0),GetFingerNode(finger,3))
            degrees = degrees1-1
            degrees_aux = degrees2-1
            self.finger_activation[finger] = (degrees/(np.pi - 1)) 
            if self.finger_activation[finger]> HandTracker.__FINGER_ACTIVATION[finger][2] and degrees_aux>0.80:
                self.finger_hit_counts[finger] += self.deltatime
            elif self.finger_activation[finger] <= HandTracker.__FINGER_ACTIVATION[finger][1]:
                self.finger_hit_counts[finger] = 0

    def GetFingerStatus(self,finger: FingerEnum):
        state = 0
        for val in HandTracker.__FINGER_ACTIVATION[finger]:
            if self.finger_activation[finger] <= val:
                break
            state += 1
        if state == 2:
            if self.finger_hit_counts[finger] >= HandTracker.__ACTIVATION_HITCOUNT:
                return state
            else:
                return state-1
        if state == 3:
            if self.finger_hit_counts[finger] >= HandTracker.__ACTIVATION_HITCOUNT:
                return state
            else:
                return 1
        return state
    
    def GetNormalStatus(self):
        state = 0
        for val in HandTracker.__DIRECTION_ACTIVATION:
            if self.normal_value <= val:
                break
            state += 1
        return state
    
    def __ProcessPinchPosition(self):
        add_vec = self.landmarks[4] - self.landmarks[3]
        add_vec = add_vec
        distance2 =  np.linalg.norm((add_vec+self.landmarks[4]) - self.landmarks[8])
        distance2 = distance2/np.linalg.norm(self.landmarks[7]- self.landmarks[8])
        self.pinch_distance = distance2

        if self.pinch_distance <= HandTracker.__PINCH_ACTIVATION[0]:
            self.pinch_hit_count += self.deltatime
        elif self.pinch_distance > HandTracker.__PINCH_ACTIVATION[1]:
            self.pinch_hit_count = max(self.pinch_hit_count - self.deltatime,0)

    def GetPinchStatus(self):
        state = 0
        for val in HandTracker.__PINCH_ACTIVATION:
            if self.pinch_distance <= val:
                break
            state += 1
        if state == 0 or state == 1:
            if self.pinch_hit_count < HandTracker.__ACTIVATION_HITCOUNT:
                return 2
            else:
                return state
        return state
    
    @property
    def hand_data(self)->HandData:
        fing_status = [self.GetFingerStatus(fing) for fing in FingerEnum]
        pinch = True if self.GetPinchStatus() in (0,1) else False

        return HandData(id= self.id,
                        visible=self.visible,
                        img_coords=self.landmarks,
                        world_coords=self.world_landmarks,
                        left_hand=self.left_hand,
                        finger_open=fing_status,
                        pinch=pinch,
                        normal_status=self.GetNormalStatus(),
                        normal_vec=self.normal_vec)
    



