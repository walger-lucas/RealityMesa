from .coord_transform import CoordTransformManager
import cv2
from cv2.typing import MatLike
import numpy as np
class CharucoCoordTransformManager(CoordTransformManager):
    def __init__(self,aruco_dict_id: int = cv2.aruco.DICT_5X5_50):
        super().__init__()
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
        self.charuco_board = None
        self.size = np.array([0,0])
        self.coord = np.array([0,0])

    
    def GetCalibrationImage(self,size_squares=(8,5), sqr_length_px = 100) -> tuple[int,int,MatLike]:
        """
        Generates charuco image of size size_squares*sqr_length_px with dict set on init
        
        :param self: Description
        :param size_squares: How many squares in X and Y directions there are.
        :param sqr_length_px: length of square in pixels

        :returns width height and image matrix of charuco board
        """
        self.charuco_board = cv2.aruco.CharucoBoard(
            size=size_squares,
            squareLength= sqr_length_px,
            markerLength= sqr_length_px/2,
            dictionary= self.aruco_dict)
        self.w = int( size_squares[0]*sqr_length_px)
        self.h = int(size_squares[1]*sqr_length_px)
        return self.w, self.h, self.charuco_board.generateImage((self.w,self.h), marginSize=0, borderBits=1)
    
    def DoCallibrationCorners(self, img:MatLike, top_left_coord=None, bottom_right_coord = None)->bool:
        if top_left_coord == None or bottom_right_coord == None:
            return self.DoCallibration(img)
        size = [bottom_right_coord[0]-top_left_coord[0],bottom_right_coord[1]-top_left_coord[1]]
        return self.DoCallibration(img,top_left_coord,size)

    def DoCallibration(self, img:MatLike, coord=None, size = None)->bool:

        if self.charuco_board == None:
            return False
        
        if coord == None:
            coord = [0.0,0.0]
        if(size == None):
            size = [self.w,self.h]

        self.coord = np.array(coord)
        self.size = np.array(size)
        
        in_pts = np.array([[coord[0] ,coord[1]],
                           [coord[0] + size[0],coord[1]],
                           [coord[0] ,coord[1]+ size[1]],
                           [coord[0] + size[0] ,coord[1]+ size[1]]],np.float32)
        
        out_pts = np.array([[0 ,0],
                           [self.w,0],
                           [0 ,self.h],
                           [self.w ,self.h]],np.float32)
        
        screen_space_to_board_px = CoordTransformManager(in_pts,out_pts)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        charuco_detector = cv2.aruco.CharucoDetector(self.charuco_board)
        charucoCorners, charucoIds, markerCorners, markerIds = charuco_detector.detectBoard(gray)

        if charucoIds is not None and len(charucoIds) >= 4 :
            ids: np.ndarray = charucoIds.reshape(-1)
            charuco_pts = np.array([[p[0], p[1]] for p in self.charuco_board.getChessboardCorners()], dtype=np.float32)
            charuco_pts = charuco_pts[ids]
            img_pts = charucoCorners.reshape(-1, 2).astype(np.float32)
        elif markerIds is not None and len(markerIds) > 4:
            markerIds_flat = markerIds.flatten()
            obj_pts = self.charuco_board.getObjPoints()
            charuco_pts = np.vstack([self.charuco_board.getObjPoints()[id][:,:2] for id in markerIds_flat if id < len(obj_pts)]).astype(np.float32)
            img_pts = np.vstack([c.reshape(-1, 2) for c in markerCorners]).astype(np.float32)
        else:
            return False
        if(len(charuco_pts)<5):
            return False
        board_px_to_image = CoordTransformManager(charuco_pts,img_pts)
        out = CoordTransformManager.JoinTransform(screen_space_to_board_px,board_px_to_image)
        self.CopyCalibration(out)
        return True
    
    def DebugImage(self,debug_img:MatLike):
            pt = self.TransformTo(+np.array([0.0+self.coord[0],0.0+self.coord[1]]))
            pt1 = (int(pt[0]),int(pt[1]))
            pt = self.TransformTo(np.array([self.size[0]+self.coord[0],0.0+self.coord[1]]))
            pt2 = (int(pt[0]),int(pt[1]))
            pt = self.TransformTo(np.array([self.size[0]+self.coord[0],self.size[1]+self.coord[1]]))
            pt3 = (int(pt[0]),int(pt[1]))
            pt = self.TransformTo(np.array([0+self.coord[0],self.size[1]+self.coord[1]]))
            pt4 = (int(pt[0]),int(pt[1]))
            cv2.line(debug_img,pt1,pt2,(0,0,255),2)
            cv2.line(debug_img,pt2,pt3,(0,0,255),2)
            cv2.line(debug_img,pt4,pt3,(0,0,255),2)
            cv2.line(debug_img,pt4,pt1,(0,0,255),2)



        