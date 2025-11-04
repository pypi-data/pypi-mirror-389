"""."""

import pytest

from kinematic_tracker.association.association import Association


def test_set_ind_pos_size(association: Association) -> None:
    """."""
    assert association.ind_pos_size == (0, 1, 2, -3, -2, -1)
    association.metric = association.metric.GIOU
    association.set_ind_pos_size((0, 1, 2, 3, 4, 5))
    assert association.ind_pos_size == (0, 1, 2, 3, 4, 5)

    with pytest.raises(ValueError):
        association.set_ind_pos_size((0, 1, 2))
