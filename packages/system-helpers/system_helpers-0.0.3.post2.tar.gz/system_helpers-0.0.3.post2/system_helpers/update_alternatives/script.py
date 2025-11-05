import argparse
import logging
import pathlib

import typeguard

from system_helpers.update_alternatives.alternatives     import update_alternatives
from system_helpers.update_alternatives.argparse_helpers import ParseKwargs

@typeguard.typechecked
def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--prefix',
        help = "Directory where alternatives are created.",
        required = False, type = pathlib.Path, default = pathlib.Path("/usr/bin"),
    )

    parser.add_argument(
        '--for-each-of',
        help = "List of link-command pairs.",
        nargs ='*',
        required = True,
        action = ParseKwargs,
    )

    parser.add_argument(
        '--level',
        help = "Priority level.",
        required = False, type = int, default = 10,
    )

    parser.add_argument(
        '--display',
        help = "Whether to display information.",
        required = False, action = 'store_true', default = True,
    )

    return parser.parse_args()

@typeguard.typechecked
def main() -> None:

    logging.basicConfig(level=logging.INFO)

    args = parse_args()

    update_alternatives(**vars(args))

if __name__ == "__main__":

    main()
