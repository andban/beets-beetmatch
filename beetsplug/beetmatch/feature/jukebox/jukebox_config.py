import warnings
from functools import cached_property
from typing import Union

import confuse

from beetsplug.beetmatch.common import BaseConfig
from ...common.musly import (
    load_musly_jukebox,
    get_musly_methods,
    get_musly_decoders,
    is_musly_present,
    create_musly_jukebox, MuslyJukeboxConfig,
)
from ...feature.jukebox import Jukebox

_DEFAULT_CONFIG = {
    "musly": {
        "enabled": is_musly_present(),
        "threads": 1,
        "method": "timbre",
        "data_dir": "beetmatch",
    },
    "jukeboxes": [],
}


class JukeboxConfig(BaseConfig):
    _config: confuse.Subview

    def __init__(self, config: confuse.Subview):
        super(JukeboxConfig, self).__init__(config)
        self._config.add(_DEFAULT_CONFIG)

    @cached_property
    def jukeboxes(self):
        jukeboxes = self._config["jukeboxes"].get(list)
        if not any(j["name"] == "all" for j in jukeboxes):
            jukeboxes.append({"name": "all", "query": []})
        return jukeboxes

    @cached_property
    def jukebox_names(self):
        return [jukebox["name"] for jukebox in self.jukeboxes]

    def get_jukebox(self, name: Union[str, None] = None):
        jukebox_config = next((jc for jc in self.jukeboxes if jc["name"] == name), None)

        if jukebox_config is None:
            warnings.warn(
                f"no jukebox config named '{name}' found", category=UserWarning
            )
            return None

        jukebox_query = jukebox_config.get("query", [])
        if isinstance(jukebox_query, str):
            jukebox_query = [jukebox_query]

        return Jukebox(
            name=name,
            query=jukebox_query,
            musly_jukebox=self.get_musly_jukebox(name),
            filename=self._get_musly_jukebox_filename(name),
        )

    @cached_property
    def musly_enabled(self):
        return self._config["musly"]["enabled"].get() and True  # make this optional

    @cached_property
    def musly_threads(self):
        return self._config["musly"]["threads"].get(confuse.Integer())

    @cached_property
    def musly_data_dir(self):
        return (
            self._config["musly"]["data_dir"]
            .get(confuse.Path(in_app_dir=True))
            .resolve()
        )

    def get_musly_jukebox(self, name=None):
        if not is_musly_present():
            return None

        musly_jukebox_config = self._get_musly_config()
        if name is None:
            return create_musly_jukebox(musly_jukebox_config)

        filename = self._get_musly_jukebox_filename(name)
        return load_musly_jukebox(filename, musly_jukebox_config, True)

    def _get_musly_config(self) -> MuslyJukeboxConfig:
        supported_methods = get_musly_methods()
        supported_decoders = get_musly_decoders()

        method = self._config["musly"]["method"].get(
            confuse.Optional(confuse.Choice(supported_methods))
        )
        decoder = self._config["musly"]["decoder"].get(
            confuse.Optional(confuse.Choice(supported_decoders))
        )

        return {"method": method, "decoder": decoder}

    def _get_musly_jukebox_filename(self, name):
        return self.musly_data_dir.joinpath(name + ".jukebox")
