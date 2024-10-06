import ctypes
import ctypes.util
import struct
import sys
from io import BytesIO, BufferedIOBase
from typing import BinaryIO, List

from .utility import MuslyError, check_return_value, read_c_str, read_int

BUFFER_TYPES = (
    memoryview,
    bytearray,
)
BYTES_TYPE = bytes


def _guess_lib_name():
    """
    Return a list of possible library names based on current platform.
    """
    if sys.platform == "darwin":
        return ("libmusly.dylib",)
    elif sys.platform == "win32":
        return (
            "libmusly.dll",
            "musly.dll",
        )
    else:
        # todo: check package managers
        return ("libmusly.so", "libmusly.dylib")


def _load_lib(name):
    """
    Try to load the given dynamic library, or return None if unavailable.
    """
    if sys.platform == "win32":
        name = ctypes.util.find_library(name)

        if not name:
            return None

    try:
        return ctypes.cdll.LoadLibrary(name)
    except OSError as ex:
        print("failed to load lib '%s': %o", name, ex)
        return None


_libmusly = None
for name in _guess_lib_name():
    _libmusly = _load_lib(name)

    if _libmusly is not None:
        break
    else:
        # raise ImportError("could not load libmusly")
        print("no libmusly found")


class JukeboxStruct(ctypes.Structure):
    _fields_ = [
        (
            "method",
            ctypes.c_void_p,
        ),
        (
            "method_name",
            ctypes.c_char_p,
        ),
        (
            "decoder",
            ctypes.c_void_p,
        ),
        ("decoder_name", ctypes.c_char_p),
    ]


class TrackStruct(ctypes.c_void_p):
    pass


def library_present():
    return _libmusly is not None


def version() -> str:
    return _libmusly.musly_version().decode('utf-8')


def set_debug_level(level: int):
    return _libmusly.musly_debug(level)


def list_methods():
    methods = _libmusly.musly_jukebox_listmethods().decode("utf-8")
    if not methods:
        return []

    return methods.split(",")


def list_decoders():
    decoders = _libmusly.musly_jukebox_listdecoders().decode("utf-8")

    if decoders is None:
        return []

    return decoders.split(",")


def jukebox_create(method: str, decoder: str) -> JukeboxStruct:
    cmethod = BYTES_TYPE(str(method), encoding="utf-8") if method is not None else None
    cdecoder = BYTES_TYPE(str(decoder), encoding="utf-8") if decoder is not None else None

    jukebox = _libmusly.musly_jukebox_poweron(cmethod, cdecoder)
    if jukebox is None:
        raise MuslyError(
            "failed to create musly jukebox using method: %s, and decoder: %s"
            % (method, decoder)
        )

    return jukebox


def jukebox_free(jukebox: JukeboxStruct):
    if jukebox is not None:
        _libmusly.musly_jukebox_poweroff(jukebox)


def jukebox_decoder(jukebox: JukeboxStruct) -> str:
    return jukebox.contents.decoder_name.decode("utf-8")


def jukebox_method(jukebox: JukeboxStruct) -> str:
    return jukebox.contents.method_name.decode("utf-8")


def jukebox_method_info(jukebox: JukeboxStruct):
    desc = _libmusly.musly_jukebox_aboutmethod(jukebox)
    return desc.decode('utf-8') if desc is not None else None


def jukebox_get_header_size(jukebox: JukeboxStruct):
    return check_return_value(_libmusly.musly_jukebox_binsize(jukebox, 1, 0))


def jukebox_get_track_size(jukebox: JukeboxStruct):
    return check_return_value(_libmusly.musly_jukebox_binsize(jukebox, 0, 1))


def _jukebox_serialize_header(jukebox: JukeboxStruct, dest: BinaryIO):
    size = jukebox_get_header_size(jukebox)
    size_as_bytes = int.to_bytes(size, sys.int_info.sizeof_digit, sys.byteorder)
    dest.write(size_as_bytes)

    buffer = (ctypes.c_char * size).from_buffer(bytearray(size))
    buffer_used = _libmusly.musly_jukebox_tobin(jukebox, buffer, 1, 0, 0)
    dest.write(buffer[:buffer_used])


def _jukebox_serialize_tracks(jukebox: JukeboxStruct, dest: BytesIO, chunk_size=100):
    track_count = jukebox_track_count(jukebox)
    track_size = jukebox_get_track_size(jukebox)

    buffer_size = track_size * chunk_size
    buffer = (ctypes.c_char * buffer_size).from_buffer(bytearray(buffer_size))

    track_written = 0
    while track_count > 0:
        tracks_to_write = min(chunk_size, track_count)
        buffer_used = check_return_value(
            _libmusly.musly_jukebox_tobin(jukebox, buffer, 0, tracks_to_write, track_written))
        dest.write(buffer[:buffer_used])
        track_written += tracks_to_write
        track_count -= tracks_to_write


def jukebox_serialize(jukebox: JukeboxStruct, dest: BinaryIO):
    # libmusly version
    dest.write(version().encode("utf-8"))
    dest.write(struct.pack("=b", 0))

    # system int size and byteorder info
    dest.write(int.to_bytes(sys.int_info.sizeof_digit, 1, sys.byteorder))
    dest.write(int.to_bytes(0x01020304, sys.int_info.sizeof_digit, sys.byteorder))

    # jukebox method name
    dest.write(jukebox_method(jukebox).encode("utf-8"))
    dest.write(struct.pack("=b", 0))

    # jukebox decoder name
    dest.write(jukebox_decoder(jukebox).encode("utf-8"))
    dest.write(struct.pack("=b", 0))

    _jukebox_serialize_header(jukebox, dest)
    _jukebox_serialize_tracks(jukebox, dest)


def jukebox_deserialize(src: BufferedIOBase, ignore_decoder=True, chunk_size=100) -> JukeboxStruct:
    used_version = read_c_str(src)
    if not used_version or used_version != version():
        print(f"WARNING: deserializing jukebox created with musly version '{used_version}' using musly '{version()}'")

    int_size = read_int(src, 1)
    if not int_size or int_size != sys.int_info.sizeof_digit:
        raise MuslyError("cannot deserialize jukebox because mismatching integer size")

    byteorder = read_int(src, int_size)
    if not byteorder or byteorder != 0x01020304:
        raise MuslyError("cannot deserialize jukebox because mismatching byteorder")

    method = read_c_str(src)
    decoder = read_c_str(src)
    if not method or (not ignore_decoder and not decoder):
        raise MuslyError("cannot deserialize jukebox because missing method/decoder")

    jukebox = jukebox_create(method, decoder)

    track_size = jukebox_get_track_size(jukebox)
    header_size = read_int(src, sys.int_info.sizeof_digit)
    header = src.read(header_size)
    track_count = check_return_value(_libmusly.musly_jukebox_frombin(jukebox, header, 1, 0))

    buffer_size = track_size * chunk_size
    buffer = (ctypes.c_char * buffer_size).from_buffer(bytearray(buffer_size))
    while track_count > 0:
        tracks_read = min(track_count, chunk_size)
        bytes_read = src.readinto(buffer)
        if bytes_read != tracks_read * track_size:
            raise MuslyError('cannot deserialize jukebox because less tracks found than expected')

        check_return_value(_libmusly.musly_jukebox_frombin(jukebox, ctypes.byref(buffer), 0, tracks_read))
        track_count -= tracks_read

    return jukebox


def _jukebox_track_alloc(jukebox: JukeboxStruct) -> TrackStruct:
    track_ptr = _libmusly.musly_track_alloc(jukebox)
    if not track_ptr:
        raise MuslyError("failed to allocate track")
    return track_ptr


def track_free(track: TrackStruct):
    _libmusly.musly_track_free(track)


def jukebox_track_size(jukebox: JukeboxStruct):
    return check_return_value(_libmusly.musly_track_binsize(jukebox))


def jukebox_track_count(jukebox: JukeboxStruct):
    return _libmusly.musly_jukebox_trackcount(jukebox)


def jukebox_max_track_id(jukebox: JukeboxStruct):
    return check_return_value(_libmusly.musly_jukebox_trackcount(jukebox))


def jukebox_get_track_ids(jukebox: JukeboxStruct):
    id_array = (ctypes.c_int * jukebox_track_count(jukebox))()
    check_return_value(_libmusly.musly_jukebox_gettrackids(jukebox, id_array))

    return list(id_array)


def jukebox_add_tracks(jukebox: JukeboxStruct, tracks: List[TrackStruct], track_ids=None):
    track_array = (ctypes.c_void_p * len(tracks))(*tracks)
    track_array_ptr = ctypes.cast(track_array, ctypes.POINTER(ctypes.c_void_p))

    id_array = (ctypes.c_int * len(tracks))()
    if track_ids:
        id_array[:] = [int(t) for t in track_ids]

    check_return_value(_libmusly.musly_jukebox_addtracks(
        jukebox,
        track_array_ptr,
        id_array,
        len(tracks),
        1 if track_ids is None else 0
    ))

    return list(id_array) if track_ids is None else track_ids


def jukebox_remove_tracks(jukebox: JukeboxStruct, track_ids: List[int]):
    id_array = (ctypes.c_int * len(track_ids))(*track_ids)
    check_return_value(_libmusly.musly_jukebox_removetracks(
        jukebox, id_array, len(track_ids)
    ))


def jukebox_track_to_string(jukebox: JukeboxStruct, track: TrackStruct):
    track_string = _libmusly.musly_track_tostr(jukebox, track)
    return track_string.decode('utf-8')


def jukebox_track_to_bytearray(jukebox: JukeboxStruct, track: TrackStruct):
    track_size = jukebox_track_size(jukebox)
    target = bytearray(track_size)
    buffer = (ctypes.c_char * len(target)).from_buffer(target)

    check_return_value(_libmusly.musly_track_tobin(jukebox, track, buffer))

    return target


def jukebox_track_from_bytearray(jukebox: JukeboxStruct, data: bytearray) -> TrackStruct:
    track_size = jukebox_track_size(jukebox)
    if len(data) != track_size:
        raise MuslyError("cannot create track from byte array because mismatching size")

    track_ptr = _jukebox_track_alloc(jukebox)
    check_return_value(_libmusly.musly_track_frombin(
        jukebox, BYTES_TYPE(data), track_ptr
    ))

    return track_ptr


def jukebox_track_from_audio_file(jukebox: JukeboxStruct, filename: str, start, length):
    track_ptr = _jukebox_track_alloc(jukebox)
    if not isinstance(filename, BYTES_TYPE):
        filename = BYTES_TYPE(filename, encoding="utf-8")

    check_return_value(_libmusly.musly_track_analyze_audiofile(
        jukebox, filename, start, length, track_ptr
    ), f"failed to analyze audio file {filename}")

    return track_ptr


def jukebox_set_style(jukebox: JukeboxStruct, tracks: List[TrackStruct]):
    track_array = (ctypes.c_void_p * len(tracks))(*tracks)
    track_array_ptr = ctypes.cast(track_array, ctypes.POINTER(ctypes.c_void_p))

    check_return_value(_libmusly.musly_jukebox_setmusicstyle(
        jukebox, track_array_ptr, len(tracks)
    ))


def jukebox_compute_similarities(jukebox: JukeboxStruct,
                                 track: TrackStruct, track_id: int,
                                 other_tracks: List[TrackStruct],
                                 other_ids: List[int]) -> List[float]:
    if len(other_tracks) != len(other_ids):
        raise MuslyError("cannot compute similarities because mismatching lengths of tracks and ids")

    other_tracks_array = (ctypes.c_void_p * len(other_tracks))(*other_tracks)
    other_tracks_array_ptr = ctypes.cast(other_tracks_array, ctypes.POINTER(ctypes.c_void_p))

    other_ids_array = (ctypes.c_int * len(other_ids))(*other_ids)
    similarity_array = (ctypes.c_float * len(other_tracks))()

    check_return_value(
        _libmusly.musly_jukebox_similarity(
            jukebox,
            track,
            track_id,
            other_tracks_array_ptr,
            other_ids_array,
            len(other_tracks),
            similarity_array
        )
    )

    return list(similarity_array)


if _libmusly:
    _libmusly.musly_version.argtypes = ()
    _libmusly.musly_version.restype = ctypes.c_char_p

    _libmusly.musly_debug.argtypes = (ctypes.c_int,)
    _libmusly.musly_debug.restype = None

    _libmusly.musly_jukebox_listmethods.argtypes = ()
    _libmusly.musly_jukebox_listmethods.restype = ctypes.c_char_p

    _libmusly.musly_jukebox_listdecoders.argtypes = ()
    _libmusly.musly_jukebox_listdecoders.restype = ctypes.c_char_p

    _libmusly.musly_jukebox_poweron.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
    )
    _libmusly.musly_jukebox_poweron.restype = ctypes.POINTER(JukeboxStruct)

    _libmusly.musly_jukebox_poweroff.argtypes = (ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_jukebox_poweroff.restype = None

    _libmusly.musly_jukebox_aboutmethod.argtypes = (
        ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_jukebox_aboutmethod.restype = ctypes.c_char_p

    _libmusly.musly_jukebox_binsize.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_int,
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_binsize.restype = ctypes.c_int

    _libmusly.musly_jukebox_tobin.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_tobin.restype = ctypes.c_int

    _libmusly.musly_jukebox_frombin.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_frombin.restype = ctypes.c_int

    _libmusly.musly_track_size.argtypes = (ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_track_size.restype = ctypes.c_int

    _libmusly.musly_jukebox_trackcount.argtypes = (ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_jukebox_trackcount.restype = ctypes.c_int

    _libmusly.musly_jukebox_maxtrackid.argtypes = (ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_jukebox_maxtrackid.restype = None

    _libmusly.musly_track_alloc.argtypes = (ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_track_alloc.restype = ctypes.c_void_p

    _libmusly.musly_track_free.argtypes = (ctypes.c_void_p,)
    _libmusly.musly_track_free.restype = None

    _libmusly.musly_track_binsize.argtypes = (ctypes.POINTER(JukeboxStruct),)
    _libmusly.musly_track_binsize.restype = ctypes.c_int

    _libmusly.musly_track_tobin.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_void_p,
        ctypes.c_char_p,
    )
    _libmusly.musly_track_tobin.restype = ctypes.c_int

    _libmusly.musly_track_frombin.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_char_p,
        ctypes.c_void_p,
    )
    _libmusly.musly_track_frombin.restype = ctypes.c_int

    _libmusly.musly_track_tostr.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_void_p,
    )
    _libmusly.musly_track_tostr.restype = ctypes.c_char_p

    _libmusly.musly_track_analyze_audiofile.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_char_p,
        ctypes.c_float,
        ctypes.c_float,
        ctypes.c_void_p,
    )
    _libmusly.musly_track_analyze_audiofile.restype = ctypes.c_int

    _libmusly.musly_jukebox_addtracks.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_addtracks.restype = ctypes.c_int

    _libmusly.musly_jukebox_removetracks.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_removetracks.restype = ctypes.c_int

    _libmusly.musly_jukebox_gettrackids.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.POINTER(ctypes.c_int),
    )
    _libmusly.musly_jukebox_gettrackids.restype = ctypes.c_int

    _libmusly.musly_jukebox_setmusicstyle.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_setmusicstyle.restype = ctypes.c_int

    _libmusly.musly_jukebox_similarity.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_float),
    )
    _libmusly.musly_jukebox_similarity.restype = ctypes.c_int

    _libmusly.musly_jukebox_guessneighbors.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_guessneighbors.restype = ctypes.c_int

    _libmusly.musly_jukebox_guessneighbors_filtered.argtypes = (
        ctypes.POINTER(JukeboxStruct),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
        ctypes.POINTER(ctypes.c_int),
        ctypes.c_int,
    )
    _libmusly.musly_jukebox_guessneighbors_filtered.restype = ctypes.c_int
