"""."""

from pathlib import Path
from typing import Sequence, Union

from pure_ab_3d_mot.tracker import Ab3DMot
from rich.progress import Progress

from eval_ab_3d_mot.cli.common.opt_param import fill_r_cnn_opt_param
from eval_ab_3d_mot.cli.common.r_cnn_adaptor import read_r_cnn_ab_3d_mot
from eval_ab_3d_mot.cli.common.single_sequence import get_tracking_result
from eval_ab_3d_mot.cli.common.tracking_io import write_ab_3d_mot_tracking

from .cmd_line import get_cmd_line


def run(args: Union[Sequence[str], None] = None) -> bool:
    cli = get_cmd_line(args)
    category = cli.get_category()
    print(category)
    result_root = Path(cli.trk_dir) / category.value
    result_root.mkdir(exist_ok=True, parents=True)
    with Progress() as progress:
        detections = cli.get_detections()
        task = progress.add_task('[cyan]Working...', total=len(detections))
        for det_file_name in cli.get_detections():
            adaptor = read_r_cnn_ab_3d_mot(det_file_name, cli.ann_dir, 0)
            tracker = Ab3DMot()
            fill_r_cnn_opt_param(category, tracker)
            result = get_tracking_result(adaptor, tracker, cli.verbosity)
            output_path = result_root / Path(det_file_name).name
            print(f'    Store {output_path}')
            write_ab_3d_mot_tracking(result, str(output_path))
            progress.update(task, advance=1)

    return True


def main() -> None:
    run()  # pragma: no cover
