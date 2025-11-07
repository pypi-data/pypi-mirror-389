"""."""

from enum import Enum
from typing import Tuple, Union


class KittiCategory(Enum):
    CAR = 'car'
    CYCLIST = 'cyclist'
    PEDESTRIAN = 'pedestrian'

    def get_kitti_labels(self) -> Union[Tuple[str], Tuple[str, str]]:
        if self == KittiCategory.CAR:
            return 'Car', 'Van'
        else:
            return (self.value.capitalize(),)
