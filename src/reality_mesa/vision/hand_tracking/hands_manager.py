import norfair
from norfair.filter import OptimizedKalmanFilterFactory
from .hand_data import HandTracker

import numpy as np

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import cv2
from cv2.typing import MatLike
import os
import time
from norfair.tracker import Tracker, Detection


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models/hand_landmarker.task")

def hand_reid_distance(track_a:norfair.tracker.TrackedObject, track_b:norfair.tracker.TrackedObject):
        
        centroid_a = np.mean(track_a.estimate, axis=0)
        centroid_b = np.mean(track_b.estimate, axis=0)
        return float(np.linalg.norm(centroid_a - centroid_b))

class HandsManager:
    
    def __init__(self, fps=30,width=640,height=640):
        self.__tracker_left = Tracker(
            initialization_delay=fps//10,
            distance_function='mean_euclidean',
            hit_counter_max= int(fps/2),
            filter_factory=OptimizedKalmanFilterFactory(Q=0.4),
            distance_threshold=max(width,height)/4,
            past_detections_length=15,
            reid_distance_function=hand_reid_distance,
            reid_distance_threshold=max(width,height)/4,
            reid_hit_counter_max=fps,
        )
        self.__tracker_right = Tracker(
            initialization_delay=fps//10,
            distance_function='mean_euclidean',
            hit_counter_max= int(fps/2),
            filter_factory=OptimizedKalmanFilterFactory(Q=0.4),
            distance_threshold=max(width,height)/4,
            past_detections_length=15,
            reid_distance_function=hand_reid_distance,
            reid_distance_threshold=max(width,height)/4,
            reid_hit_counter_max=fps,
        )
        base_options = python.BaseOptions(
            model_asset_path=MODEL_PATH
        )
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=8,
            running_mode=vision.RunningMode.VIDEO,
            min_hand_detection_confidence=0.2,
            min_hand_presence_confidence=0.2,
            min_tracking_confidence=0.6,
        )
        self.hand_detector = vision.HandLandmarker.create_from_options(options)
        self.timestamp = 0
        self.hands_dict:dict[int,HandTracker] = {}
        self.cur_time = time.monotonic()
        self.fps = fps

    def RunVision(self,rgb_img:MatLike):
        """
        Runs hand_vision model and hand tracking, updates current hand tracking and hand state
        
        Args:
            rgb_img (MatLike): Image to run model and extract hands

        Returns:
            tuple[dict[int,HandData],int]: Returns tuple with dict of current active hand_data and removed hand id list
        """
        w = rgb_img.shape[1]
        h = rgb_img.shape[0]
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_img
        )

        results = self.hand_detector.detect_for_video(mp_image, self.timestamp)
        self.timestamp += 1
        tracked_objects_left, tracked_objects_right = self.__ProcessHandlandmarkExtraction(results,w,h)

        new_time = time.monotonic()
        delta_time = new_time - self.cur_time
        self.cur_time = new_time

        # Create new ids
        self.__UpdateTrackedObjects(tracked_objects_left,tracked_objects_right,delta_time)

        #remove invalid
        removed_list: list[int] = []
        for id_ in list(self.hands_dict):
            if self.timestamp - self.hands_dict[id_].frame > 0:
                self.hands_dict.pop(id_)
                removed_list.append(id_)

        hand_data = {id_:hand.hand_data for id_,hand in self.hands_dict.items()}

        return hand_data, removed_list
    
    def __ProcessHandlandmarkExtraction(self,results, w:int, h:int):
        """Adds landmarks to trackers"""
        
        detections_L = []
        detections_R = []
         
        if (results.hand_landmarks and results.handedness and results.hand_world_landmarks 
            and len(results.hand_landmarks) == len(results.handedness) == len(results.hand_world_landmarks)):
            for hand_landmarks, handedness_list, world_landmarks in zip(
                results.hand_landmarks,
                results.handedness,
                results.hand_world_landmarks
            ):
                # Extract only landmarks 0 and 5
                points = np.array([
                    [hand_landmarks[i].x * w, hand_landmarks[i].y * h]
                    for i in [0, 5]
                ])
                
                corrected_landmarks = np.array([[land.x*w,land.y*h,land.z*w] for land in hand_landmarks],np.float32) 
                corrected_world_landmarks = np.array([[land.x,land.y,land.z] for land in world_landmarks],np.float32) 
                label = handedness_list[0].category_name  # "Left" or "Right"

                detection = Detection(
                    points,
                    data= (corrected_landmarks,corrected_world_landmarks)  # already a list of landmarks
                )

                if label == "Left":
                    detections_L.append(detection)
                else:
                    detections_R.append(detection)

        tracked_objects_left = self.__tracker_left.update(detections_L)
        tracked_objects_right = self.__tracker_right.update(detections_R)
        return tracked_objects_left, tracked_objects_right
    
    def __UpdateTrackedObjects(self,tracked_objects_left:list[norfair.tracker.TrackedObject], tracked_objects_right:list[norfair.tracker.TrackedObject],delta_time):
        for tobj in tracked_objects_left:
            hid = tobj.id
            if hid is None:
                continue
            lost =  tobj.hit_counter < tobj.hit_counter_max/2
            landmarks,world_landmarks = (None,None) if lost else tobj.last_detection.data
            position = np.mean(tobj.estimate, axis=0)
            id = hid*2-1
            if id not in self.hands_dict:
                self.hands_dict[id] = HandTracker(id,True,position,landmarks,world_landmarks,self.timestamp,delta_time)
            else:
                self.hands_dict[id].Update(position,landmarks,world_landmarks,self.timestamp,delta_time)
        
        for tobj in tracked_objects_right:
            hid = tobj.id
            if hid is None:
                continue
            lost =  tobj.hit_counter < tobj.hit_counter_max/2
            landmarks,world_landmarks = (None,None) if lost else tobj.last_detection.data
            position = np.mean(tobj.estimate, axis=0)
            id = hid*2
            if id not in self.hands_dict:
                self.hands_dict[id] = HandTracker(id,False,position,landmarks,world_landmarks,self.timestamp,delta_time)
            else:
                self.hands_dict[id].Update(position,landmarks,world_landmarks,self.timestamp,delta_time)