from .vision_manager import VisionManager
from reality_mesa.infra import Command,FutureCommand
from cv2.typing import MatLike
import time
import cv2

class GetCharucoBoard(FutureCommand[VisionManager,MatLike]):
    def __init__(self,size_squares=(8,5), sqr_length_px = 100):
        super().__init__()
        self.size_squares = size_squares
        self.sqr_length_px = sqr_length_px
    
    def _run(self, input: VisionManager) -> MatLike:
        _,_,img = input.homography_transform.GetCalibrationImage(self.size_squares,self.sqr_length_px)
        return img
    
class CalibrateWithCharuco(FutureCommand[VisionManager,bool]):
    def __init__(self,coord:tuple[float,float] | None, size:tuple[float,float] | None, max_timeout: float= 5.0):
        super().__init__()
        self.max_timeout = max_timeout
        self.coord = coord
        self.size = size
    
    def _run(self, input: VisionManager) -> bool:
        start_time = time.monotonic()
        if input.cap == None:
            return False
        while time.monotonic()-start_time < self.max_timeout:
            success,img = input.cap.read()
            if (success and
                input.homography_transform.DoCallibration(img,coord=self.coord,size=self.size)
                ):
                return True
        return False
    
class StopCamera(Command[VisionManager]):
    def __init__(self) -> None:
        super().__init__()
    def execute(self, input: VisionManager):
        input.StopCamera()

class StartCamera(Command[VisionManager]):
    def __init__(self,cam_id:int = 0, fps:int=45,size:tuple[int,int]=(1920,1080),max_time:float=5.0):
        super().__init__()
        self.cam_id = cam_id
        self.fps = fps
        self.size = size
        self.max_time = max_time
    def execute(self, input: VisionManager):
        input.StartCamera(self.cam_id,self.fps,self.size,self.max_time)
    
class StopVisionManager(Command[VisionManager]):
    def __init__(self) -> None:
        super().__init__()
    def execute(self, input: VisionManager):
        input.Stop()