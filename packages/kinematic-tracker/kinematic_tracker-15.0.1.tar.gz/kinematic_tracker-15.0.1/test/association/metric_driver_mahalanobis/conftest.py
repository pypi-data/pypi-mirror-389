"""."""

import cv2
import numpy as np
import pytest


@pytest.fixture
def filters() -> list[cv2.KalmanFilter]:
    """."""
    kf = cv2.KalmanFilter(12, 6, 0, cv2.CV_64F)
    kf.measurementMatrix = np.eye(6, 12)
    kf.measurementNoiseCov = np.eye(6) * 4.0
    kf.statePre = np.linspace(1.0, 12.0, num=12).reshape(12, 1)
    kf.errorCovPre = np.eye(12) * 1.0
    filters = [kf]

    kf2 = cv2.KalmanFilter(12, 6, 0, cv2.CV_64F)
    kf2.measurementMatrix = np.eye(6, 12)
    kf2.measurementNoiseCov = np.eye(6) * 4.0
    kf2.statePre = np.linspace(2.0, 13.0, num=12).reshape(12, 1)
    kf2.errorCovPre = np.eye(12) * 2.0
    filters.append(kf2)

    kf3 = cv2.KalmanFilter(12, 6, 0, cv2.CV_64F)
    kf3.measurementMatrix = np.eye(6, 12)
    kf3.measurementNoiseCov = np.eye(6) * 4.0
    kf3.statePre = np.linspace(3.0, 14.0, num=12).reshape(12, 1)
    kf3.errorCovPre = np.eye(12) * 3.0
    filters.append(kf3)

    return filters
