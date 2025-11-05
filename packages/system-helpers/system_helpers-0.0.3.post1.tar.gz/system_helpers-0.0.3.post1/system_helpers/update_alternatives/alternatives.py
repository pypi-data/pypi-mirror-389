import pathlib
import subprocess
import typing

import typeguard

@typeguard.typechecked
def update_alternatives(*,
    for_each_of : typing.Dict[str, str],
    prefix : pathlib.Path,
    level : int,
    display : bool,
) -> None:
    """
    Update alternatives for a list of 'apps'.
    """
    for link, command in for_each_of.items():
        subprocess.check_call([
            'update-alternatives',
            '--install', prefix / link, link, prefix / command,
            str(level),
        ])

        if display:
            subprocess.check_call(['update-alternatives', '--display', link])
