"""."""

from argparse import ArgumentParser
from typing import List, Sequence

from rich_argparse import RawTextRichHelpFormatter

from eval_ab_3d_mot.cli.common.get_hlp import get_hlp
from eval_ab_3d_mot.kitti_category import KittiCategory


PROG = 'batch-run-ab-3d-mot-with-clavia'
HLP_OUT = 'Directory to store tracking results.'
HLP_ANN = 'Annotations (ground-truth) directory.'
HLP_CAT_OBJ = 'Category of the objects selected for tracking.'
HLP_CAT_PRM = 'Category of to selected tracker parameters.'
AUTO = 'auto'


class CmdLineBatchRunWithClavIA:
    def __init__(self) -> None:
        self.verbosity = 0
        self.annotations: List[str] = []
        self.category_obj = KittiCategory.CAR.value
        self.category_prm = AUTO

    def __repr__(self) -> str:
        return (
            'CmdLineBatchRunWithClavIA('
            f'category-obj {self.category_obj} '
            f'category-prm {self.category_prm})'
        )

    def get_object_category(self) -> KittiCategory:
        return KittiCategory(self.category_obj)

    def get_parameter_category(self) -> KittiCategory:
        if self.category_prm == AUTO:
            result = KittiCategory(self.category_obj)
        else:
            result = KittiCategory(self.category_prm)
        return result

    def get_annotations(self) -> List[str]:
        return sorted(self.annotations)


def get_cmd_line(args: Sequence[str]) -> CmdLineBatchRunWithClavIA:
    cli = CmdLineBatchRunWithClavIA()
    parser = ArgumentParser(
        PROG, f'{PROG} <annotations> [OPTIONS]', formatter_class=RawTextRichHelpFormatter
    )
    parser.add_argument('annotations', nargs='+', help='Annotation files.')

    categories = tuple(c.value for c in KittiCategory)
    hlp_c_obj = get_hlp(HLP_CAT_OBJ, cli.category_obj)
    parser.add_argument('--category-obj', '-c', choices=categories, help=hlp_c_obj)

    hlp_c_prm = get_hlp(HLP_CAT_PRM, cli.category_prm + ' 🛈 objects category')
    cc_pp = tuple(c.value for c in KittiCategory) + (AUTO,)
    parser.add_argument('--category-prm', '-p', choices=cc_pp, help=hlp_c_prm)

    parser.add_argument('--verbosity', '-v', action='count', help='Script verbosity.')
    parser.parse_args(args, namespace=cli)
    if cli.verbosity > 0:
        print(cli)
    return cli
