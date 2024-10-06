import pathlib
from base64 import b64decode
from typing import Union, List

from beets import dbcore
from beets.dbcore import Query
from beets.dbcore.query import TrueQuery, AndQuery
from beets.library import Item, parse_query_string

from beetsplug.beetmatch.musly import MuslyJukebox


class Jukebox:
    _name: str
    _query: Query
    _filename: pathlib.Path
    _musly_jukebox: MuslyJukebox

    def __init__(self, name: str, filename: pathlib.Path, musly_jukebox=None, query=None):
        self._name = name
        self._filename = filename
        self._musly_jukebox = musly_jukebox

        if isinstance(query, str):
            self._query, _ = parse_query_string(query, Item)
        elif isinstance(query, list):
            self._query = AndQuery([parse_query_string(q, Item)[0] for q in query])
        else:
            self._query = TrueQuery()

    @property
    def name(self):
        return self._name

    @property
    def filename(self):
        return self._filename

    @property
    def musly_jukebox(self):
        return self._musly_jukebox

    def get_query(self, additional_query: Union[str, dbcore.Query] = "") -> Query:
        if not additional_query:
            return self._query

        if isinstance(additional_query, str):
            additional_query, _ = parse_query_string(additional_query, Item)

        return dbcore.AndQuery((self._query, additional_query))

    def save_musly_jukebox(self):
        if not self._musly_jukebox:
            return

        self._filename.parent.mkdir(parents=True, exist_ok=True)
        with open(self._filename, "wb") as fh:
            print(f"filename {self._filename}")
            self._musly_jukebox.write_to(fh)

    def init_musly_jukebox(self, items: List[Item]):
        if not self.musly_jukebox:
            return

        for item in items:
            track_data = item.get('musly_track')
            if track_data is None:
                continue

            track = self.musly_jukebox.track_from_bytearray(b64decode(track_data))
            self.musly_jukebox.add_tracks([track], [item.id])
