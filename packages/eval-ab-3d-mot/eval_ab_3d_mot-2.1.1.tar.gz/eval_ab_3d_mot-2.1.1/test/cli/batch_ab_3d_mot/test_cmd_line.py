"""."""

import pytest

from eval_ab_3d_mot.cli.batch_ab_3d_mot.cmd_line import CmdLineBatchRunAb3dMot, get_cmd_line


@pytest.fixture()
def cli() -> CmdLineBatchRunAb3dMot:
    cli = CmdLineBatchRunAb3dMot()
    cli.detections = ['car/002.txt', 'car/001.txt']
    return cli


def test_get_detections(cli: CmdLineBatchRunAb3dMot) -> None:
    assert cli.get_detections() == ['car/001.txt', 'car/002.txt']
    cli.detections = ['car/002.txt', 'pedestrian/001.txt']
    with pytest.raises(ValueError):
        cli.get_detections()


def test_category_and_tracking_dir() -> None:
    args = ['car/0001.txt', 'car/0002.txt', '-v', '-c', 'cyclist', '-o', 'my-dir']
    cli = get_cmd_line(args)
    assert isinstance(cli, CmdLineBatchRunAb3dMot)
    assert cli.verbosity == 1
    assert cli.category == 'cyclist'
    assert cli.trk_dir == 'my-dir'
    assert cli.detections == ['car/0001.txt', 'car/0002.txt']


def test_at_least_one_detection_file_expected() -> None:
    with pytest.raises(SystemExit):
        get_cmd_line([])
