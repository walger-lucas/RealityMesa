from cv2 import perspectiveTransform, findHomography, warpPerspective
import numpy as np
import numpy.typing as npt

class CoordTransformManager:
    def __init__(self, in_pts:npt.NDArray[np.floating]|None = None, out_pts:npt.NDArray[np.floating] | None= None):
        if in_pts is not None and out_pts is not None:
            in_pts = self.__ensure_n2(in_pts)
            out_pts = self.__ensure_n2(out_pts)

            assert len(in_pts) >= 4
            assert len(in_pts) == len(out_pts)

            H, _ = findHomography(in_pts, out_pts)
            Hinv, _ = findHomography(out_pts, in_pts)

            self.__M = H
            self.__N = Hinv
        else:
            self.__M = np.eye(3, dtype=np.float32)
            self.__N = np.eye(3, dtype=np.float32)
    
    def CopyCalibration(self, coordTransform : "CoordTransformManager"):
        self.__M = coordTransform.__M.copy()
        self.__N = coordTransform.__N.copy()
    
    def GetInverse(self):
        out  = CoordTransformManager()
        out.__M = self.__N
        out.__N = self.__M
        return out

    def TransformTo(self, pts:npt.NDArray[np.floating])->npt.NDArray[np.floating]:
        pts = self.__ensure_n2(pts)
        return self.__apply_homography(pts, self.__M)

    def TransformFrom(self, pts:npt.NDArray[np.floating])->npt.NDArray[np.floating]:
        pts = self.__ensure_n2(pts)
        return self.__apply_homography(pts, self.__N)
    
    # Creates coord transform with the same effect of doing A transform then B transform
    @staticmethod
    def JoinTransform(coordTransformA : "CoordTransformManager",coordTransformB: "CoordTransformManager"):
        out  = CoordTransformManager()
        out.__M = coordTransformB.__M @ coordTransformA.__M
        out.__N = coordTransformA.__N @ coordTransformB.__N
        return out

    # Ensures pts are of dimension (N,2)
    def __ensure_n2(self, pts):
        pts = np.asarray(pts, dtype=np.float32)

        if pts.ndim == 1:
            assert pts.shape[0] == 2
            pts = pts.reshape(1, 2)
        assert pts.ndim == 2 and pts.shape[1] == 2
        return pts

    def __apply_homography(self, pts, H):
        pts_cv = pts.reshape(-1, 1, 2)
        transformed = perspectiveTransform(pts_cv, H)
        return transformed.reshape(-1, 2)[0]