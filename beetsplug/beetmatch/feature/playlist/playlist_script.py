import os.path
import subprocess
from logging import Logger
from os import PathLike
from sys import stdout, stderr
from typing import Union, List

from beets.library import Item

from beetsplug.beetmatch.common import default_logger


class PlaylistScript:
    _script_path: Union[str, PathLike[str]]
    _log: Logger

    def __init__(self, script_path, log=default_logger):
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"the playlist script {script_path} does not exist")

        self._script_path = script_path
        self._log = log

    def execute(self, jukebox_name: str, items: List[Item]):
        self._log.debug("executing playlist script '%s'...", self._script_path)

        try:
            cmd = [self._script_path, jukebox_name]
            cmd.extend([item.path for item in items])
            subprocess.run(cmd, stderr=stderr, stdout=stdout, check=True)
        except subprocess.CalledProcessError as e:
            self._log.error(
                "playlist script '%s' failed: %s", self._script_path, exc_info=e
            )
