"""."""

import numpy as np
import pytest

from eval_ab_3d_mot.cli.common.kitti_adaptor import KittiAdaptor
from eval_ab_3d_mot.kitti_category import KittiCategory


def test_normal_init(adaptor: KittiAdaptor) -> None:
    assert adaptor.last_time_stamp == 9
    assert len(adaptor.time_stamps) == 2


def test_wrongly_shaped_detections() -> None:
    ids_l = np.array([1], int)
    stamps_l = np.array([0], int)
    category_l = np.array(['Car'], str)
    with pytest.raises(AssertionError):
        KittiAdaptor(stamps_l, ids_l, category_l, np.zeros((1, 8)), KittiCategory.CAR)
    with pytest.raises(AssertionError):
        KittiAdaptor(stamps_l, ids_l, category_l, np.zeros(7), KittiCategory.CAR)
    with pytest.raises(AssertionError):
        KittiAdaptor(stamps_l, ids_l, category_l, np.zeros((1, 1, 8)), KittiCategory.CAR)
