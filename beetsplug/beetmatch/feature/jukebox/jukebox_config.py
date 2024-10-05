import warnings

import confuse

from beetsplug.beetmatch import musly
from beetsplug.beetmatch.common import BaseConfig
from beetsplug.beetmatch.feature.jukebox import Jukebox
from beetsplug.beetmatch.musly import MuslyJukebox, MuslyError

_DEFAULT_CONFIG = {
    "musly": {
        "enabled": musly.libmusly.library_present(),
        "threads": 1,
        "method": "timbre",
        "data_dir": "beetmatch",
    },
    "jukeboxes": []
}


class JukeboxConfig(BaseConfig):
    _config: confuse.Subview

    def __init__(self, config: confuse.Subview):
        super(JukeboxConfig, self).__init__(config)
        self._config.add(_DEFAULT_CONFIG)

    @property
    def jukeboxes(self):
        return self._config['jukeboxes'].get(list)

    @property
    def jukebox_names(self):
        return [jukebox["name"] for jukebox in self.jukeboxes]

    def get_jukebox(self, name: str):
        jukebox_config = next((jc for jc in self.jukeboxes if jc["name"] == name), None)

        if jukebox_config is None:
            warnings.warn(f"no jukebox config named '{name}' found", category=UserWarning)
            return None

        jukebox_query = jukebox_config.get("query", [])
        if isinstance(jukebox_query, str):
            jukebox_query = [jukebox_query]

        return Jukebox(
            name=name,
            query=jukebox_query,
            musly_jukebox=self.get_musly_jukebox(name),
            filename=self._get_musly_jukebox_filename(name)
        )

    @property
    def musly_enabled(self):
        return self._config['musly']['enabled'].get() and musly.libmusly.library_present()

    @property
    def musly_threads(self):
        return self._config['musly']['threads'].get(confuse.Integer())

    @property
    def musly_data_dir(self):
        return self._config['musly']['data_dir'].get(
            confuse.Path(in_app_dir=True)).resolve()

    def get_musly_jukebox(self, name=None):
        if not self.musly_enabled:
            return None

        try:
            if not name:
                return MuslyJukebox(**self._get_musly_config())

            with open(self._get_musly_jukebox_filename(name), "rb") as fh:
                return MuslyJukebox.load_from(fh)
        except FileNotFoundError:
            return MuslyJukebox(**self._get_musly_config())
        except MuslyError as e:
            raise RuntimeError(f"could not load musly jukebox '{name}': file seems to be corrupted ({e})")
        except Exception as e:
            raise RuntimeError(f"could not load musly jukebox '{name}': unexpected error ({e})")

    def _get_musly_config(self):
        supported_methods = musly.libmusly.list_methods() if musly.libmusly.library_present() else []

        method = self._config['musly']['method'].get(
            confuse.Optional(confuse.Choice(supported_methods))
        )

        return {"method": method}

    def _get_musly_jukebox_filename(self, name):
        return self.musly_data_dir.joinpath(name + ".jukebox")
