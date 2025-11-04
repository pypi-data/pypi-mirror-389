"""The module for computing Generalized Intersection over Union (GIoU) association metric.

This module provides functionality for computing the similarity score between detection reports
and Kalman filter states (targets) using the Generalized Intersection over Union (GIoU) metric.
The metric is computed between the 3D bounding boxes which are aligned with Cartesian axes.

The resulting rectangular matrix will have a shape of (num_reports, num_targets), and located
at the beginning of the pre-allocated buffer `metric_rt` of the base class `MetricDriverBase`.
The resulting matrix is contiguous in memory.

Classes:
    MetricGIoUAligned: Computes GIoU-based association metrics between detections
        and Kalman filter states in aligned coordinate space.
"""

from typing import Any, Sequence

import cv2
import numpy as np

from .g_iou_scores_aligned import GIoUAux
from .metric_driver_base import MetricDriverBase


class MetricGIoUAligned(MetricDriverBase):
    """Computes GIoU-based association metrics between detections and Kalman filter states.

    This class inherits from MetricDriverBase and implements GIoU-based metric computation
    for data association between detection reports and Kalman filter states. The computation
    is performed between cuboids (3D bounding boxes) aligned with Cartesian axes.

    Attributes:
        report_aux (GIoUAux): Helper object for processing detection measurements.
        target_aux (GIoUAux): Helper object for processing Kalman filter states.

    Args:
        num_reports_max: Maximum number of detection reports to handle.
        num_targets_max: Maximum number of targets (Kalman filters) to handle.
        num_z: Dimension of the measurement vector.
    """

    def __init__(
        self, num_reports_max: int, num_targets_max: int, num_z: int, ind_pos_size: Sequence[int]
    ) -> None:
        """Initialize the MetricGIoUAligned instance.

        Args:
            num_reports_max: Maximum number of detection reports to handle.
            num_targets_max: Maximum number of targets (Kalman filters) to handle.
            num_z: Dimension of the measurement vector.
            ind_pos_size: Location of variables in the measurement vector.
                          By default, the indices will be 0,1,2,-3,-2,-1, i.e.
                          the center of the cuboid is taken as first three variables
                          of the measurement vector and sizes (dimensions) of the
                          cuboids are taken from the last three variables.
        """
        super().__init__(num_reports_max, num_targets_max, num_z)
        self.ind_pos_size = np.array(ind_pos_size, dtype=int)
        self.vec_pos_size_filter = np.zeros((6, 1))
        self.vec_pos_size_det = np.zeros((6, 1))
        self.report_aux = GIoUAux()
        self.target_aux = GIoUAux()

    def compute_metric(
        self,
        det_rz: Sequence[np.ndarray[Any, float]] | np.ndarray[Any, float],
        filters: Sequence[cv2.KalmanFilter],
    ) -> np.ndarray:
        """Compute GIoU-based metrics between detections and Kalman filter states.

        Args:
            det_rz: Detection measurements, either as a sequence of numpy arrays
                or a single numpy array containing measurement vectors.
            filters: Sequence of OpenCV KalmanFilter objects representing tracked targets.

        Returns:
            np.ndarray: A matrix of GIoU scores between each detection-target pair,
                with shape (num_detections, num_targets).
        """
        rect_chunk = self.get_rect_chunk(len(det_rz), len(filters))
        for t, kf in enumerate(filters):
            np.dot(kf.measurementMatrix, kf.statePre, out=self.vec_z)
            self.vec_pos_size_filter[:, 0] = self.vec_z[self.ind_pos_size, 0]
            self.target_aux.set_vec_z(self.vec_pos_size_filter)
            for r, det_z in enumerate(det_rz):
                self.vec_pos_size_det[:, 0] = det_z[self.ind_pos_size]
                self.report_aux.set_vec_z(self.vec_pos_size_det)
                rect_chunk[r, t] = self.target_aux.get_g_iou(self.report_aux)
        return rect_chunk
