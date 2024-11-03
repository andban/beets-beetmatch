# Copyright: Copyright (c) 2021, Andreas Bannach
#
# Author: Andreas Bannach <andreas at borntohula.de>
# Created: 18/12/2021, 03:54 PM
# License: See LICENSE.txt

"""
Module for algorithmic playlist generation
"""

from beets.importer import ImportTask
from beets.plugins import BeetsPlugin

from .common import BaseConfig
from .common.musly import is_musly_present
from .feature.jukebox import JukeboxCommand, JukeboxConfig
from .feature.playlist import PlaylistCommand


# from .feature.server import ServerCommand


class BeetmatchPlugin(BeetsPlugin):
    """Algorithmic playlist generator."""

    analyze_cmd: JukeboxCommand
    playlist_cmd: PlaylistCommand

    def __init__(self):
        super(BeetmatchPlugin, self).__init__()

        config = BaseConfig(self.config)

        self.analyze_cmd = JukeboxCommand(self.config)
        self.playlist_cmd = PlaylistCommand(self.config)

        if config.auto_import:
            self.import_stages = [self.analyze_track]

    def commands(self):
        cmds = [self.playlist_cmd]
        if is_musly_present():
            cmds.append(self.analyze_cmd)

        return cmds

    def analyze_track(self, _, task: ImportTask):
        config = JukeboxConfig(self.config)
        jukebox = config.get_musly_jukebox()

        for item in task.items:
            self.analyze_cmd.analyze_track(item, jukebox, write=True)
