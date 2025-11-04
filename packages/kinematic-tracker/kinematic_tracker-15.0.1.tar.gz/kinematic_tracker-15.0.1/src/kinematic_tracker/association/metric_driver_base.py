"""
This module defines the `MetricDriverBase` class. The class provides a common functionality
for managing the computation of association metric (similarity scores) between
detection reports and tracked targets.
"""

import numpy as np


class MetricDriverBase:
    """
    A base class for handling metrics between reports and targets. It provides methods
    to initialize and retrieve rectangular contiguous chunks of similarity scores.

    Attributes:
        num_reports_max: Maximum number of reports allowed.
        num_targets_max: Maximum number of targets allowed.
        num_reports: Current number of reports.
        num_targets: Current number of targets.
        num_elements: Total number of elements in the metric matrix.
        metric_rt: A 2D buffer for the similarity scores.
        vec_z: A vertical vector used as buffer in GIoU and Mahalanobis.
    """

    def __init__(self, num_reports_max: int, num_targets_max: int, num_z: int) -> None:
        """
        Initializes the MetricDriverBase instance with the given maximum limits
        for reports, targets, and additional data.

        Args:
            num_reports_max: Maximum number of reports.
            num_targets_max: Maximum number of targets.
            num_z: Number of variables in the measurement vectors.
        """
        self.num_reports_max = num_reports_max
        self.num_targets_max = num_targets_max
        self.num_reports = 0
        self.num_targets = 0
        self.num_elements = 0
        self.metric_rt = np.zeros((num_reports_max, num_targets_max))
        self.vec_z = np.zeros((num_z, 1))

    def get_rect_chunk(self, num_reports: int, num_targets: int) -> np.ndarray:
        """
        Retrieves a rectangular contiguous chunk of the metric matrix located in
        the buffer are carved precisely to store the similarity score between
        a given number of reports and targets.

        Args:
            num_reports: Number of reports to include in the chunk.
            num_targets: Number of targets to include in the chunk.

        Returns:
            np.ndarray: A 2D array representing the requested rectangular chunk.

        Raises:
            ValueError: If the number of reports exceeds `num_reports_max`.
            ValueError: If the number of targets exceeds `num_targets_max`.
        """
        self.num_reports = num_reports
        self.num_targets = num_targets
        self.num_elements = num_reports * num_targets
        if num_reports > self.num_reports_max:
            raise ValueError(f'Too much detections? {num_reports} {self.num_reports_max}')

        if num_targets > self.num_targets_max:
            raise ValueError(f'Too much tracks? {num_targets} {self.num_targets_max}')
        flat_chunk = self.metric_rt.reshape(-1)[: self.num_elements]
        rect_chunk = flat_chunk.reshape(num_reports, num_targets)
        return rect_chunk
