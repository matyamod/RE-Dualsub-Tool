"""Font slot assets (*.fslt.2 or *.fslt.4).

Notes:
    Some RE engine games have font slot files.
    A font slot file has 16 slots.
    A slot has some file paths for fonts (*.otf.*).
    And each text widget (in *.gui.* files) specifies one of the slots.

    # Sample codes
    from REFontSlot import FontSlot
    fslt = FontSlot()
    fslt.import_fslt("*.fslt.*")
    fslt.export_json("*.json")
    fslt2 = FontSlot()
    fslt2.import_json("*.json")
    fslt2.export_fslt("*.fslt.*")
"""
import io
import os
from typing import Final
from io_util import (
    read_uint32, read_uint32_array, read_uint64, read_uint64_array,
    read_float32_array, read_wstr,
    write_uint32, write_uint32_array, write_uint64, write_uint64_array,
    write_float32_array, write_wstr,
    save_json, load_json, check_type, check_length, get_index
)


class FileInfo:
    HEAD_SIZE: Final[int] = 24

    def __init__(self):
        self.unk: list[float] = [0, 0, 0, 0]  # ???
        self.name: str = ""  # path for .oft files

        # private
        self.__name_offs: int = 0  # offset for name map
        self.__name_index: int = 0  # index for name map

    def read_head(self, f: io.BufferedReader):
        # struct.unpack("<ffffQ", f.read(24))
        self.unk = read_float32_array(f, 4)
        self.__name_offs = read_uint64(f)

    def read_name(self, f: io.BufferedReader):
        f.seek(self.__name_offs)
        self.name = read_wstr(f)

    def update_name_map(self, name_map: list[str]):
        index = get_index(name_map, self.name)
        if index < 0:
            index = len(name_map)
            name_map.append(self.name)
        # save index for writing name offsets
        self.__name_index = index

    def update_name_offsets(self, name_offsets: list[int]):
        self.__name_offs = name_offsets[self.__name_index]

    def write_head(self, f: io.BufferedReader):
        # "<ffffQ"
        write_float32_array(f, self.unk)
        write_uint64(f, self.__name_offs)

    def get_json(self):
        return {
            "name": self.name,
            "unk": self.unk
        }

    def set_json(self, j: dict):
        self.name = j["name"]
        check_type(self.name, "name", str)
        self.unk = j["unk"]
        check_type(self.unk, "unk", list, float)
        check_length(self.unk, "unk", 4)


class UnkInfo:
    HEAD_SIZE: Final[int] = 48

    def __init__(self):
        self.unk: list[float] = [0.0, 0.0]  # ???
        self.unk2: list[int] = [0, 0, 0, 0]  # ???
        self.names: list[str] = ["", "", ""]  # ???

        # private
        self.__name_offsets: list[int] = [0, 0, 0]  # offsets for name map
        self.__name_indices: list[int] = [0, 0, 0]  # indices for name map

    def read_head(self, f: io.BufferedReader):
        # struct.unpack("<QQQffIIII", f.read(48))
        self.__name_offsets = read_uint64_array(f, 3)
        self.unk = read_float32_array(f, 2)
        self.unk2 = read_uint32_array(f, 4)

    def read_name(self, f: io.BufferedReader):
        self.names = []
        for offs in self.__name_offsets:
            f.seek(offs)
            self.names.append(read_wstr(f))

    def update_name_map(self, name_map: list[str]):
        self.__name_indices = []
        for name in self.names:
            index = get_index(name_map, name)
            if index < 0:
                index = len(name_map)
                name_map.append(name)
            # save index for writing name offsets
            self.__name_indices.append(index)

    def update_name_offsets(self, name_offsets: list[int]):
        self.__name_offsets = [name_offsets[index] for index in self.__name_indices]

    def write_head(self, f: io.BufferedReader):
        # "<QQQffIIII"
        write_uint64_array(f, self.__name_offsets)
        write_float32_array(f, self.unk)
        write_uint32_array(f, self.unk2)

    def get_json(self) -> dict:
        return {
            "names": self.names,
            "unk": self.unk,
            "unk2": self.unk2
        }

    def set_json(self, j: dict):
        self.names = j["names"]
        check_type(self.names, "name", list, str)
        check_length(self.names, "names", 3)
        self.unk = j["unk"]
        check_type(self.unk, "unk", list, float)
        check_length(self.unk, "unk", 2)
        self.unk2 = j["unk2"]
        check_type(self.unk2, "unk2", list, int)
        check_length(self.unk2, "unk2", 4)


class Slot:
    V4_HEAD_SIZE: Final[int] = 40
    def __init__(self, version: int):
        self.version: int = version
        self.info_lists: list[list] = []  # list of FileInfo lists.

        # private
        self.__info_counts: list[int] = []  # counts for FileInfo
        self.__offset_offsets: list[int] = []  # offset for info_offsets
        self.__info_offsets_list: list[list[int]] = []  # lists of offsets
        match self.version:
            case 2:
                self.__classes = [FileInfo]
            case 4:
                self.__classes = [FileInfo, UnkInfo, UnkInfo]
            case _:
                pass

    def read_fileinfo(self, f: io.BufferedReader):
        match self.version:
            case 2:
                count = read_uint64(f)
                self.__info_counts = [count]
                info_list = [FileInfo() for i in range(count)]
                _ = [info.read_head(f) for info in info_list]
                self.info_lists = [info_list]
            case 4:
                self.__info_counts = read_uint32_array(f, 3)
                nul = read_uint32(f)
                assert nul == 0
                self.__offset_offsets = read_uint64_array(f, 3)  # offsets to info_offsets
                current = f.tell()
                # self.__info_offsets_list = []
                self.info_lists = []
                for offs_offs, count, clas in zip(self.__offset_offsets, self.__info_counts, self.__classes):
                    f.seek(offs_offs)
                    info_offsets = read_uint64_array(f, count)
                    # self.__info_offsets_list.append(info_offsets)
                    info_list = [clas() for i in range(count)]
                    for info, offs in zip(info_list, info_offsets):
                        f.seek(offs)
                        info.read_head(f)
                    self.info_lists.append(info_list)
                f.seek(current)
            case _:
                pass

    def read_name(self, f: io.BufferedReader):
        for info_list in self.info_lists:
            _ = [info.read_name(f) for info in info_list]

    def update_head(self, current: int):
        """Update head data."""
        self.__info_counts = [len(info_list) for info_list in self.info_lists]
        match self.version:
            case 2:
                current += 8 + FileInfo.HEAD_SIZE * self.__info_counts[0]
            case 4:
                self.__offset_offsets = []
                for count in self.__info_counts:
                    self.__offset_offsets.append(current)
                    # There is 1 uint64 even if count is 0.
                    current += 8 * (count + (count == 0))
            case _:
                pass

        return current

    def update_offsets(self, current: int):
        """Update info_offsets for writing."""
        self.__info_offsets_list = []
        for info_list, clas in zip(self.info_lists, self.__classes):
            info_offsets = [current + clas.HEAD_SIZE * i for i in range(len(info_list))]
            current += clas.HEAD_SIZE * len(info_list)
            self.__info_offsets_list.append(info_offsets)
        return current

    def update_name_map(self, name_map: list[str]):
        for info_list in self.info_lists:
            _ = [info.update_name_map(name_map) for info in info_list]

    def update_name_offsets(self, name_offsets: list[int]):
        for info_list in self.info_lists:
            _ = [info.update_name_offsets(name_offsets) for info in info_list]

    def write_fileinfo(self, f: io.BufferedWriter):
        match self.version:
            case 2:
                write_uint64(f, self.__info_counts[0])
                _ = [info.write_head(f) for info in self.info_lists[0]]
            case 4:
                write_uint32_array(f, self.__info_counts)
                write_uint32(f, 0)
                write_uint64_array(f, self.__offset_offsets)
                current = f.tell()
                iters = zip(self.__offset_offsets, self.__info_offsets_list, self.__info_counts, self.info_lists)
                for offs_offs, info_offsets, count, info_list in iters:
                    f.seek(offs_offs)
                    write_uint64_array(f, info_offsets)
                    if count == 0:
                        write_uint64(f, 0)
                    for offs, info in zip(info_offsets, info_list):
                        f.seek(offs)
                        info.write_head(f)
                    self.info_lists.append(info_list)
                f.seek(current)
            case _:
                pass

    def get_json(self) -> dict:
        j = {}
        for info_list, i in zip(self.info_lists, range(3)):
            if len(info_list) > 0:
                if i == 0:
                    key = "files"
                else:
                    key = "unk" + str(i - 1)
                j[key] = [info.get_json() for info in info_list]
        return j

    def set_json(self, j: dict):
        match self.version:
            case 2:
                self.info_lists = [[]]
            case 4:
                self.info_lists = [[], [], []]
            case _:
                pass
        i = 0
        for info_list, clas in zip(self.info_lists, self.__classes):
            if i == 0:
                key = "files"
            else:
                key = "unk" + str(i - 1)
            i += 1
            if key not in j:
                continue
            info_list_json: list[dict] = j[key]
            check_type(info_list_json, key, list, dict)
            for info_json in info_list_json:
                new_info = clas()
                new_info.set_json(info_json)
                info_list.append(new_info)


class FontSlot:
    MAGIC: Final[int] = b"FSLT"
    SUPPORTED_VERSIONS: Final[list[int]] = [2, 4]
    SLOT_COUNT: Final[int] = 16  # Maybe all files have 16 slots

    def __init__(self):
        self.version: int = 0
        self.slots: list[Slot] = []

    def read(self, f: io.BufferedReader):
        self.version = read_uint32(f)
        if self.version not in FontSlot.SUPPORTED_VERSIONS:
            raise RuntimeError(f"Unsupported file version. ({self.version})")

        magic = f.read(4)
        if magic != FontSlot.MAGIC:
            raise RuntimeError("Not .fslt file.")

        slot_offsets = read_uint64_array(f, FontSlot.SLOT_COUNT)

        self.slots = [Slot(self.version) for i in range(FontSlot.SLOT_COUNT)]
        for slot, offs in zip(self.slots, slot_offsets):
            assert offs == f.tell()
            slot.read_fileinfo(f)

        _ = [slot.read_name(f) for slot in self.slots]

    def write(self, f: io.BufferedWriter):
        write_uint32(f, self.version)
        f.write(FontSlot.MAGIC)

        # Update private attributes before writing
        current = 8 + 8 * FontSlot.SLOT_COUNT
        match self.version:
            case 2:
                slot_offsets = []
                for slot in self.slots:
                    slot_offsets.append(current)
                    current = slot.update_head(current)
            case 4:
                slot_offsets = [current + Slot.V4_HEAD_SIZE * i for i in range(len(self.slots))]
                current += Slot.V4_HEAD_SIZE * len(self.slots)
                for slot in self.slots:
                    current = slot.update_head(current)
                for slot in self.slots:
                    current = slot.update_offsets(current)
            case _:
                pass

        # Collect names from attributes.
        name_map = []
        _ = [slot.update_name_map(name_map) for slot in self.slots]

        f.write(b"\x00" * (current - 8))

        # Update name offsets and write name map
        name_offsets = []
        for name in name_map:
            name_offsets.append(f.tell())
            write_wstr(f, name)
        _ = [slot.update_name_offsets(name_offsets) for slot in self.slots]

        # Write slots
        f.seek(8)
        write_uint64_array(f, slot_offsets)
        _ = [slot.write_fileinfo(f) for slot in self.slots]

    def get_json(self) -> dict:
        return {
            "type": "FontSlot",
            "version": self.version,
            "slots": [slot.get_json() for slot in self.slots]
        }

    def set_json(self, j: dict):
        self.version = j["version"]
        if self.version not in FontSlot.SUPPORTED_VERSIONS:
            raise RuntimeError(f"Unsupported file version. ({self.version})")

        slots_json: list[dict] = j["slots"]
        check_type(slots_json, "slots", list, dict)
        check_length(slots_json, "slots", 16)
        if len(slots_json) != FontSlot.SLOT_COUNT:
            raise RuntimeError(f"Requires {FontSlot.SLOT_COUNT} slots but there are {len(slots_json)} slots.")

        self.slots = [Slot(self.version) for slot in slots_json]
        for slot, j in zip(self.slots, slots_json):
            slot.set_json(j)

    def import_fslt(self, file: str):
        with io.open(file, "rb") as f:
            self.read(f)

    def export_fslt(self, file: str):
        with io.open(file, "wb") as f:
            self.write(f)

    def export_json(self, file: str):
        save_json(self.get_json(), file)

    def import_json(self, file: str):
        j = load_json(file)
        self.set_json(j)

    def get_ext(self):
        return f"fslt.{self.version}"
