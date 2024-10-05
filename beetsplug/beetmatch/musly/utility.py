import sys


class MuslyError(Exception):
    """Raised when a call to libmusly fails."""


def check_return_value(ret, message="call to libmusly failed"):
    """
    Check return value of library call and raise if it indicates an error.
    """
    if ret < 0:
        raise MuslyError(message)
    return ret


def read_c_str(src):
    string = bytearray()

    while True:
        c = src.read(1)

        if not c or not c[0]:
            return string.decode("utf-8")

        string.extend(c)


def read_int(src, n_bytes):
    raw = src.read(n_bytes)
    if not raw:
        return None

    return int.from_bytes(raw, sys.byteorder)
