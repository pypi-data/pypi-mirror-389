import logging
import pathlib
import shutil
import subprocess
import typing

import typeguard

@typeguard.typechecked
def get_list_of_packages_from_requirements_file(*, file : pathlib.Path) -> typing.List[str]:
    """
    Get list of packages from a requirements file.

    Note that this function only supports skipping empty lines and comment lines, *i.e.*,
    not all features from https://pip.pypa.io/en/stable/reference/requirements-file-format/
    are supported.
    """
    packages = []
    with file.open(mode = "r") as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                packages.extend(line.strip().split())
    return packages

@typeguard.typechecked
def install_command(*, yes : bool = True, no_install_recommends : bool = True) -> typing.List[str]:
    """
    Get the `apt` command to install packages.
    """
    cmd = ['apt']

    if yes:
        cmd.append('--yes')

    if no_install_recommends:
        cmd.append('--no-install-recommends')

    cmd.append('install')
    return cmd

class Cleaner:
    @typeguard.typechecked
    @staticmethod
    def run() -> None:
        logging.info("Cleaning 'apt' cache and lists.")
        subprocess.check_call(['apt', 'clean'])
        shutil.rmtree(pathlib.Path("/var/lib/apt/lists"))

@typeguard.typechecked
def install_packages(*,
    packages : typing.Optional[typing.List[str]] = None,
    requirements : typing.Optional[typing.List[pathlib.Path]] = None,
    update : bool = False,
    upgrade : bool = False,
    clean: bool = False,
    args : typing.Optional[typing.List[str]] = None,
) -> None:
    """
    Install list of packages by using `apt`.

    Optionally:
        * update
        * upgrade
        * clean
    """
    to_be_installed = []

    if packages:
        to_be_installed += packages

    if requirements:
        for file in requirements:
            to_be_installed += get_list_of_packages_from_requirements_file(file = file)

    if len(to_be_installed) == 0:
        raise RuntimeError('There is no package to be installed.')

    logging.info(f"Installing 'apt' packages {to_be_installed} (update={update}, upgrade={upgrade}, clean={clean}, args={args})")

    if update:
        subprocess.check_call(['apt', 'update'])

    if upgrade:
        subprocess.check_call(['apt', '--yes', 'upgrade'])

    cmd = install_command(yes = True, no_install_recommends = True)
    if args:
        cmd += args
    cmd += to_be_installed

    subprocess.check_call(cmd)

    if clean: Cleaner.run()
