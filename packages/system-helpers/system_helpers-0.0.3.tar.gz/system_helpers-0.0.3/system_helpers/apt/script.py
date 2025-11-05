import argparse
import logging
import pathlib

import typeguard

from system_helpers.apt         import extract
from system_helpers.apt.install import install_packages, Cleaner

@typeguard.typechecked
def parse_args() -> argparse.Namespace:
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(required = True)

    parser_ip = subparsers.add_parser('install-packages')

    parser_ip.add_argument('--clean',   action = 'store_true')
    parser_ip.add_argument('--update',  action = 'store_true')
    parser_ip.add_argument('--upgrade', action = 'store_true')

    parser_ip.add_argument(
        '--packages',
        help = "List of packages to install.",
        nargs = '*',
        required = False,
    )

    parser_ip.add_argument(
        '--requirement',
        help = 'Requirement file à la pip.',
        dest = 'requirements',
        action = 'append',
        type = pathlib.Path,
        required = False,
    )

    parser_ip.add_argument(
        '--args',
        help = 'Additional arguments to \'apt install\'.',
        nargs = argparse.REMAINDER,
        required = False,
    )

    parser_ip.set_defaults(func = install_packages)

    parser_ex = subparsers.add_parser('extract-from-package')

    parser_ex.add_argument('--package', required = True, type = str)
    parser_ex.add_argument('--files',   required = True, nargs = argparse.REMAINDER)

    parser_ex.set_defaults(func = extract.extract)

    parser_clean = subparsers.add_parser('clean')

    parser_clean.set_defaults(func = Cleaner.run)

    return parser.parse_args()

@typeguard.typechecked
def main() -> None:

    logging.basicConfig(level = logging.INFO)

    args = parse_args()

    kwargs = vars(args)

    func = kwargs.pop('func')

    func(**kwargs)

if __name__ == "__main__":

    main()
