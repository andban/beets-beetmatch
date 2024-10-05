import confuse

_DEFAULT_CONFIG = {
    "auto": True
}


class BaseConfig:
    _config: confuse.Subview

    def __init__(self, config: confuse.Subview):
        self._config = config

    @property
    def auto_import(self):
        return self._config.get("auto")
