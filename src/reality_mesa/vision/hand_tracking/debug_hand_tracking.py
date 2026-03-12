from . import FingerEnum, HandsManager, GetFingerNode
from .hands_manager import HandTracker
from ..homography import CoordTransformManager
import cv2
from cv2.typing import MatLike

def debug_draw_hand_tracker(img:MatLike,hand:HandTracker,perspective_transform:CoordTransformManager | None = None):
    add_values = True
    if perspective_transform == None:
        perspective_transform = CoordTransformManager()
    
    color = (255,0,255)
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    thickness = 1

    org = list(map(int,hand.position))
    org[0] += 20
    text =  f"{hand.id}L" if hand.left_hand else f"{hand.id}R"
    if not hand.visible:
        cv2.circle(img,list(map(int, hand.position)),3,color,4)
        cv2.putText(img,text,org,font,font_scale,color,thickness)
        return
    
    cv2.putText(img,text,[int(hand.top_left_bounding_box[0])-20,int(hand.top_left_bounding_box[1])-25],font,font_scale,color,thickness)
    cv2.rectangle(img,[int(hand.top_left_bounding_box[0])-20,int(hand.top_left_bounding_box[1])-20],[int(hand.bottom_right_bounding_box[0])+20,int(hand.bottom_right_bounding_box[1])+20],color,1)
    

    for finger in FingerEnum:
        stat = hand.GetFingerStatus(finger)
        color = (255,0,0) if stat == 0 else (0,0,255) if stat == 1 else (0,255,0) if stat == 2 else (0,255,255)
        cv2.line(img,list(map(int, hand.landmarks[GetFingerNode(finger,0)][:2])),list(map(int, hand.landmarks[GetFingerNode(finger,1)][:2])),color,thickness=4)
        cv2.line(img,list(map(int, hand.landmarks[GetFingerNode(finger,1)][:2])),list(map(int, hand.landmarks[GetFingerNode(finger,2)][:2])),color,thickness=3)
        cv2.line(img,list(map(int, hand.landmarks[GetFingerNode(finger,2)][:2])),list(map(int, hand.landmarks[GetFingerNode(finger,3)][:2])),color,thickness=2)
        if add_values:
            org = list(map(int,hand.landmarks[GetFingerNode(finger,3)][:2]))
            org[0] += 20
            text = format(hand.finger_activation[finger],".3f")
            cv2.putText(img,text,org,font,font_scale,color,thickness)

    color = (255,0,0)
    cv2.line(img,list(map(int, hand.landmarks[0][:2])),list(map(int, hand.landmarks[1][:2])),color,thickness=4)
    cv2.line(img,list(map(int, hand.landmarks[1][:2])),list(map(int, hand.landmarks[2][:2])),color,thickness=3)
    cv2.line(img,list(map(int, hand.landmarks[2][:2])),list(map(int, hand.landmarks[3][:2])),color,thickness=2)
    cv2.line(img,list(map(int, hand.landmarks[3][:2])),list(map(int, hand.landmarks[4][:2])),color,thickness=2)
        

    color = (0,255,0) if hand.GetNormalStatus() == 2 else (0,0,255) if hand.GetNormalStatus() == 0 else (255,0,0)
    cv2.circle(img,list(map(int, hand.position[:2])),5,(255,255,0),4)
    vec =  hand.position + hand.normal_vec[:2]*50
    cv2.line(img,list(map(int, hand.position)),list(map(int, vec[:2])),color,thickness=2)
    cv2.circle(img,list(map(int, vec[:2])),5,color)
    if add_values:
        org = list(map(int,vec[:2]))
        org[0] += 20
        text = format(hand.normal_value,".3f")
        cv2.putText(img,text,org,font,font_scale,color,thickness)

    stat = hand.GetPinchStatus()
    color = (0,255,255) if stat == 0 else (0,255,0) if stat == 1 else (0,0,255)
    cv2.line(img,list(map(int, hand.landmarks[4][:2])),list(map(int, hand.landmarks[8][:2])),color,thickness=2)
    if add_values:
        org = list(map(int,hand.landmarks[4][:2]))
        org[0] += 20
        text = format(hand.pinch_distance,".3f")
        cv2.putText(img,text,org,font,font_scale,color,thickness)
        

def debug_draw_hand_manager(img:MatLike,hand_manager:HandsManager,perspective_transform:CoordTransformManager | None = None):
    if perspective_transform == None:
        perspective_transform = CoordTransformManager()

    for hand in hand_manager.hands_dict.values():
        debug_draw_hand_tracker(img,hand,perspective_transform)