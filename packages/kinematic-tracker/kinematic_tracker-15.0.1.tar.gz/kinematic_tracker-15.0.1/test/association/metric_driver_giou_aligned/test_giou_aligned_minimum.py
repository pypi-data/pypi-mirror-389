"""."""

import cv2
import numpy as np
import pytest

from kinematic_tracker.association.metric_giou_aligned import MetricGIoUAligned


@pytest.fixture
def filters() -> list[cv2.KalmanFilter]:
    """."""
    kf = cv2.KalmanFilter(12, 6, 0, cv2.CV_64F)
    kf.measurementMatrix = np.eye(6, 12)
    kf.statePre = np.linspace(1.0, 12.0, num=12).reshape(12, 1)
    filters = [kf]

    kf2 = cv2.KalmanFilter(12, 6, 0, cv2.CV_64F)
    kf2.measurementMatrix = np.eye(6, 12)
    kf2.statePre = np.linspace(2.0, 13.0, num=12).reshape(12, 1)
    filters.append(kf2)

    kf3 = cv2.KalmanFilter(12, 6, 0, cv2.CV_64F)
    kf3.measurementMatrix = np.eye(6, 12)
    kf3.statePre = np.linspace(3.0, 14.0, num=12).reshape(12, 1)
    filters.append(kf3)

    return filters


def test_giou_aligned(det_rz: list[np.ndarray], filters: list[cv2.KalmanFilter]) -> None:
    """."""
    driver = MetricGIoUAligned(100, 500, 6, (0, 1, 2, 3, 4, 5))
    metric = driver.compute_metric(det_rz, filters)
    ref = [
        [1.0, 0.6318122555410691],
        [0.6318122555410691, 1.0],
        [0.4686147186147186, 0.6735666418466121],
    ]
    assert metric == pytest.approx(np.array(ref).T)
    assert np.shares_memory(metric, driver.metric_rt)
