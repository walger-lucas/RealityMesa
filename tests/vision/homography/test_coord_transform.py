import numpy as np
import pytest

from reality_mesa.vision.homography import CoordTransformManager


def random_points(n=10):
    return np.random.rand(n, 2).astype(np.float32) * 100


def test_identity_transform():
    manager = CoordTransformManager()

    pts = random_points()
    out = manager.TransformTo(pts)

    assert np.allclose(pts, out)


def test_translation_transform():
    pts_src = np.array([
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1]
    ], dtype=np.float32)

    translation = np.array([10, 20], dtype=np.float32)
    pts_dst = pts_src + translation

    manager = CoordTransformManager(pts_src, pts_dst)

    test_pts = random_points()
    transformed = manager.TransformTo(test_pts)

    assert np.allclose(transformed, test_pts + translation, atol=1e-4)


def test_inverse_transform():
    pts_src = np.array([
        [0, 0],
        [2, 0],
        [2, 2],
        [0, 2]
    ], dtype=np.float32)

    pts_dst = np.array([
        [10, 5],
        [14, 5],
        [14, 9],
        [10, 9]
    ], dtype=np.float32)

    manager = CoordTransformManager(pts_src, pts_dst)

    pts = random_points()
    forward = manager.TransformTo(pts)
    back = manager.TransformFrom(forward)

    assert np.allclose(pts, back, atol=1e-4)


def test_join_transform():
    pts_a = np.array([
        [0, 0],
        [1, 0],
        [1, 1],
        [0, 1]
    ], dtype=np.float32)

    pts_b = pts_a + np.array([10, 0], dtype=np.float32)
    pts_c = pts_b + np.array([0, 20], dtype=np.float32)

    A = CoordTransformManager(pts_a, pts_b)
    B = CoordTransformManager(pts_b, pts_c)

    joined = CoordTransformManager.JoinTransform(A, B)

    test_pts = random_points()

    step = B.TransformTo(A.TransformTo(test_pts))
    direct = joined.TransformTo(test_pts)

    assert np.allclose(step, direct, atol=1e-4)


def test_single_point_input():
    manager = CoordTransformManager()

    pt = np.array([5, 6], dtype=np.float32)

    out = manager.TransformTo(pt)

    assert out.shape == (1, 2)
    assert np.allclose(out, np.array([[5, 6]], dtype=np.float32))
