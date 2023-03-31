import io
import json
import os
import struct


def mkdir(dir):
    os.makedirs(dir, exist_ok=True)


def save_json(j, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(j, f, indent=4, ensure_ascii=False)


def load_json(file):
    with open(file, encoding='utf-8') as f:
        return json.load(f)


def read_int16(f: io.BufferedReader):
    return struct.unpack("<h", f.read(2))[0]


def read_int32(f: io.BufferedReader):
    return struct.unpack("<i", f.read(4))[0]


def read_uint16(f: io.BufferedReader):
    return struct.unpack("<H", f.read(2))[0]


def read_uint32(f: io.BufferedReader):
    return struct.unpack("<I", f.read(4))[0]


def read_uint64(f: io.BufferedReader):
    return struct.unpack("<Q", f.read(8))[0]


def read_float32(f: io.BufferedReader):
    return struct.unpack("<f", f.read(4))[0]


def read_uint32_array(f: io.BufferedReader, num: int):
    return struct.unpack("<" + "I" * num, f.read(4 * num))


def read_uint64_array(f: io.BufferedReader, num: int):
    return struct.unpack("<" + "Q" * num, f.read(8 * num))


def read_float32_array(f: io.BufferedReader, num: int):
    return struct.unpack("<" + "f" * num, f.read(4 * num))


def read_str(f):
    start = f.tell()
    while f.read(1) != b"\x00":
        pass
    length = f.tell() - start
    f.seek(-length, 1)
    string = f.read(length - 1).decode()
    f.seek(1, 1)
    return string


def write_str(f, wstr):
    f.write(wstr.encode())
    f.write(b"\x00")


def read_wstr(f):
    start = f.tell()
    while f.read(2) != b"\x00\x00":
        pass
    length = f.tell() - start
    f.seek(-length, 1)
    string = f.read(length - 2).decode(encoding="utf-16-le")
    f.seek(1, 2)
    return string


def write_wstr(f, wstr):
    f.write(wstr.encode(encoding="utf-16-le"))
    f.write(b"\x00\x00")


def write_uint32(f: io.BufferedWriter, num: int):
    f.write(struct.pack("<I", num))


def write_uint64(f: io.BufferedWriter, num: int):
    f.write(struct.pack("<Q", num))


def write_uint32_array(f: io.BufferedWriter, ary: list[int]):
    num = len(ary)
    f.write(struct.pack("<" + "I" * num, *ary))


def write_uint64_array(f: io.BufferedWriter, ary: list[int]):
    num = len(ary)
    f.write(struct.pack("<" + "Q" * num, *ary))


def write_float32_array(f: io.BufferedWriter, ary: list[float]):
    num = len(ary)
    f.write(struct.pack("<" + "f" * num, *ary))


def check_type(x, name: str, obj_type: type, elm_type: type=None):
    is_safe = isinstance(x, obj_type)
    if obj_type in [list, tuple] and elm_type is not None:
        is_safe = is_safe and all(isinstance(elm, elm_type) for elm in x)
    if not is_safe:
        obj_type_str = obj_type.__name__
        x_type_str = type(x).__name__
        if elm_type is not None:
            obj_type_str += " of " + elm_type.__name__
            if type(x) in [list, tuple]:
                x_type_str += " of " + type(x[0]).__name__

        raise TypeError(f"{name} should be {obj_type_str}, not {x_type_str}")


def check_length(x, name: str, length: int):
    if len(x) != length:
        raise TypeError(f"Length of {name} should be {length}")


def get_index(l, val):
    try:
        return l.index(val)
    except ValueError:
        return -1
