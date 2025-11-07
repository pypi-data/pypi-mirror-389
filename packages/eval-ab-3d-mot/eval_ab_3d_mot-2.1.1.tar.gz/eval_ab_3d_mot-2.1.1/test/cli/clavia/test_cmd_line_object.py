"""."""

import pytest

from eval_ab_3d_mot.cli.clavia.cmd_line import AUTO, CmdLineBatchRunWithClavIA
from eval_ab_3d_mot.kitti_category import KittiCategory


@pytest.fixture()
def cli() -> CmdLineBatchRunWithClavIA:
    cli = CmdLineBatchRunWithClavIA()
    cli.annotations = ['002.txt', '001.txt']
    return cli


def test_init(cli: CmdLineBatchRunWithClavIA) -> None:
    assert cli.category_prm == AUTO
    assert cli.category_obj == 'car'


def test_get_annotations(cli: CmdLineBatchRunWithClavIA) -> None:
    assert cli.get_annotations() == ['001.txt', '002.txt']


def test_repr(cli: CmdLineBatchRunWithClavIA) -> None:
    assert repr(cli) == 'CmdLineBatchRunWithClavIA(category-obj car category-prm auto)'


def test_get_object_category(cli: CmdLineBatchRunWithClavIA) -> None:
    assert cli.get_object_category() == KittiCategory.CAR


def test_get_parameter_category(cli: CmdLineBatchRunWithClavIA) -> None:
    assert cli.get_parameter_category() == KittiCategory.CAR


def test_different_get_parameter_category(cli: CmdLineBatchRunWithClavIA) -> None:
    cli.category_prm = 'pedestrian'
    assert cli.get_parameter_category() == KittiCategory.PEDESTRIAN
