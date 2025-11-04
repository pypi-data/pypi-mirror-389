"""."""

import numpy as np
import pytest

from kinematic_tracker.association.association import Association, AssociationMethod
from kinematic_tracker.association.association_metric import AssociationMetric


@pytest.fixture
def det_rz() -> list[np.ndarray]:
    """."""
    return [np.linspace(1.0, 6.0, num=6), np.linspace(2.0, 7.0, num=6)]


@pytest.fixture
def association() -> Association:
    """."""
    a = Association(12, 6)
    a.threshold = 0.56
    a.mah_pre_factor = 3.996
    a.method = AssociationMethod.GREEDY
    a.metric = AssociationMetric.MAHALANOBIS
    return a


@pytest.fixture
def metric_23() -> np.ndarray[tuple[2, 3], np.dtype[float]]:
    metric_rc = np.zeros((2, 3))
    # fmt: off
    metric_rc[:] = np.array(((1.0, 2.0, 4.0),
                             (4.0, 5.0, 6.0)))
    # fmt: on
    return metric_rc
