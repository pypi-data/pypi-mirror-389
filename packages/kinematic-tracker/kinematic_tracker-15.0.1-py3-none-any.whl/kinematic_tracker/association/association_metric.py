"""Types of association metrics (matching scores)."""

from enum import Enum


class AssociationMetric(Enum):
    """."""

    GIOU = 'giou'
    MAHALANOBIS = 'mahalanobis'
    UNKNOWN_METRIC = 'unknown-metric'
