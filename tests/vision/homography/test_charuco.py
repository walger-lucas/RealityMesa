import numpy as np
import cv2
import pytest

from reality_mesa.vision.homography import CharucoCoordTransformManager

def create_random_homography(w, h, max_perturb_ratio=0.15):
    """
    Generates a random but controlled perspective transform.

    max_perturb_ratio controls how strong the distortion is.
    0.15 = corners can move up to 15% of width/height.
    """

    src = np.array([
        [0, 0],
        [w, 0],
        [0, h],
        [w, h]
    ], dtype=np.float32)

    max_dx = w * max_perturb_ratio
    max_dy = h * max_perturb_ratio

    dst = src.copy()

    for i in range(4):
        dx = np.random.uniform(-max_dx, max_dx)
        dy = np.random.uniform(-max_dy, max_dy)
        dst[i] += [dx, dy]

    H = cv2.getPerspectiveTransform(src, dst)
    return H


def create_known_homography(w, h):
    """
    Create a synthetic projective transform that warps
    the board in a realistic perspective way.
    """

    src = np.array([
        [0, 0],
        [w, 0],
        [0, h],
        [w, h]
    ], dtype=np.float32)

    dst = np.array([
        [50, 30],
        [w - 80, 10],
        [40, h - 50],
        [w - 30, h - 20]
    ], dtype=np.float32)

    H = cv2.getPerspectiveTransform(src, dst)
    return H


def apply_homography(img, H, out_size):
    return cv2.warpPerspective(img, H, out_size)


def test_charuco_calibration_recovers_homography1():

    manager = CharucoCoordTransformManager()

    # Step 1 — generate ideal projector image
    w, h, board_img = manager.GetCalibrationImage(
        size_squares=(5, 3),
        sqr_length_px=200
    )

    board_img_bgr = cv2.cvtColor(board_img, cv2.COLOR_GRAY2BGR)

    # Step 2 — create synthetic known homography
    H_known = create_known_homography(w, h)

    warped = apply_homography(
        board_img_bgr,
        H_known,
        (w, h)
    )

    # Step 3 — run calibration on warped image
    ok = manager.DoCallibration(warped)
    assert ok, "Calibration failed to detect enough Charuco points"

    # Step 4 — validate recovered transform
    # Sample random board points and compare projection

    test_pts = np.array([
        [10, 10],
        [w - 10, 10],
        [10, h - 10],
        [w - 10, h - 10],
        [w // 2, h // 2]
    ], dtype=np.float32)

    expected = cv2.perspectiveTransform(
        test_pts.reshape(-1, 1, 2),
        H_known
    ).reshape(-1, 2)

    recovered = manager.TransformTo(test_pts) 

    error = np.linalg.norm(expected - recovered, axis=1)

    assert np.mean(error) < 2.0, \
        f"Homography recovery error too large: {np.mean(error)}"
    print(f"Homography recovery error: {np.mean(error)}")


def test_charuco_calibration_recovers_homography2():
    errors = []
    for i in range(0,1000):
        manager = CharucoCoordTransformManager(cv2.aruco.DICT_5X5_100)

        # Step 1 — generate ideal projector image
        w, h, board_img = manager.GetCalibrationImage(
            size_squares=(10, 6),
            sqr_length_px=100
        )

        board_img_bgr = cv2.cvtColor(board_img, cv2.COLOR_GRAY2BGR)

        # Step 2 — create synthetic known homography
        H_known = create_random_homography(w, h,0.25)

        warped = apply_homography(
            board_img_bgr,
            H_known,
            (w, h)
        )

        # Step 3 — run calibration on warped image
        ok = manager.DoCallibration(warped)
       # if ok == False:
         #   cv2.imshow("txt",warped)
         #   cv2.waitKey()

        assert ok, "Calibration failed to detect enough Charuco points"

        # Step 4 — validate recovered transform
        # Sample random board points and compare projection

        test_pts = np.array([
            [10, 10],
            [w - 10, 10],
            [10, h - 10],
            [w - 10, h - 10],
            [w // 2, h // 2]
        ], dtype=np.float32)

        expected = cv2.perspectiveTransform(
            test_pts.reshape(-1, 1, 2),
            H_known
        ).reshape(-1, 2)

        recovered = manager.TransformTo(test_pts) 

        error = np.linalg.norm(expected - recovered, axis=1)
        errors.append(np.mean(error))
    print(f"Total runs: {len(errors)}")
    print(f"Homography recovery mean error: {np.mean(errors)}")
    print(f"Homography recovery max error: {np.max(errors)}")
    assert np.mean(errors) < 2.0, \
        f"Homography recovery error too large: {np.mean(errors)}"
    

def test_camera_world_roundtrip():

    manager = CharucoCoordTransformManager()
    w, h, board_img = manager.GetCalibrationImage((8, 5), 80)
    board_img_bgr = cv2.cvtColor(board_img, cv2.COLOR_GRAY2BGR)

    # Create synthetic warp
    H_known = create_random_homography(w, h, 0.1)
    warped = cv2.warpPerspective(board_img_bgr, H_known, (w, h))

    ok = manager.DoCallibration(warped)
    assert ok

    # Random camera-space points
    camera_pts = np.array([
        [100, 100],
        [w - 100, 80],
        [200, h - 50],
        [w // 2, h // 2]
    ], dtype=np.float32)

    for p in camera_pts:
        world = manager.TransformFrom(p)
        back = manager.TransformTo(world)

        error = np.linalg.norm(back - p)

        assert error < 2.0, f"Roundtrip error too large: {error}"

def test_docalibration_with_custom_world_space():

    manager = CharucoCoordTransformManager()
    w, h, board_img = manager.GetCalibrationImage((8, 5), 80)
    board_img_bgr = cv2.cvtColor(board_img, cv2.COLOR_GRAY2BGR)

    # ---- simulate projector → camera ----
    H_board_to_camera = create_random_homography(w, h, 0.1)
    warped = cv2.warpPerspective(board_img_bgr, H_board_to_camera, (w, h))

    # ---- define custom world screen space ----
    coord = [100.0, 200.0]
    size  = [500.0, 300.0]

    # Run calibration with custom world space
    ok = manager.DoCallibration(warped, coord=coord, size=size)
    assert ok

    # ---- manually build world → board homography ----
    world_pts = np.array([
        [coord[0], coord[1]],
        [coord[0] + size[0], coord[1]],
        [coord[0], coord[1] + size[1]],
        [coord[0] + size[0], coord[1] + size[1]],
    ], dtype=np.float32)

    board_pts = np.array([
        [0, 0],
        [w, 0],
        [0, h],
        [w, h]
    ], dtype=np.float32)

    H_world_to_board = cv2.getPerspectiveTransform(world_pts, board_pts)

    # ---- expected full transform ----
    H_expected = H_board_to_camera @ H_world_to_board

    # ---- test random world points ----
    test_world_pts = np.array([
        [coord[0] + 50, coord[1] + 50],
        [coord[0] + size[0] - 50, coord[1] + 40],
        [coord[0] + 30, coord[1] + size[1] - 30],
        [coord[0] + size[0] / 2, coord[1] + size[1] / 2]
    ], dtype=np.float32)

    expected = cv2.perspectiveTransform(
        test_world_pts.reshape(-1, 1, 2),
        H_expected
    ).reshape(-1, 2)

    recovered = np.vstack([
        manager.TransformTo(p)
        for p in test_world_pts
    ])

    error = np.linalg.norm(expected - recovered, axis=1)
    mean_error = np.mean(error)

    assert mean_error < 2.0, \
        f"Custom world-space transform error too large: {mean_error}"
