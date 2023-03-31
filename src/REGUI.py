"""GUI assets (*.gui.540034)

Notes:
    - Still messy codes.
    - No functions for *.gui export and *.json import yet.
    - Used alphaZomega's .bt to get hints for file structure.

    # Sample codes
    from REGUI import GUIResource
    gui = GUIResource()
    gui.import_gui("*.gui.540034")
    gui.export_json("*.json")
"""

import io
from enum import IntEnum
import os
from io_util import (
    mkdir, read_int16, read_uint16, read_int32, read_uint32, read_uint64, read_uint64_array,
    read_float32, read_float32_array, read_str, read_wstr,
    write_uint32, write_uint64, write_float32_array, write_str,
    save_json
)

class PropType(IntEnum):
    Unknown = 0x0
    Bool = 0x1
    S8 = 0x2
    U8 = 0x3
    S16 = 0x4
    U16 = 0x5
    S32 = 0x6
    U32 = 0x7
    S64 = 0x8
    U64 = 0x9
    F32 = 0xA
    F64 = 0xB
    Str8 = 0xC
    Str16 = 0xD
    Enum = 0xE
    Quaternion = 0xF
    Array = 0x10
    NativeArray = 0x11
    Class = 0x12
    NativeClass = 0x13
    _struct = 0x14
    Vec2 = 0x15
    Vec3 = 0x16
    Vec4 = 0x17
    Color = 0x18
    Range = 0x19
    Float2 = 0x1A
    Float3 = 0x1B
    Float4 = 0x1C
    RangeI = 0x1D
    Point = 0x1E
    Size = 0x1F
    Asset = 0x20
    Action = 0x21
    Guid = 0x22
    Uint2 = 0x23
    Uint3 = 0x24
    Uint4 = 0x25
    Int2 = 0x26
    Int3 = 0x27
    Int4 = 0x28
    OBB = 0x29
    Mat4 = 0x2A
    Rect = 0x2B
    PathPoint3D = 0x2C
    Plane = 0x2D
    Sphere = 0x2E
    Capsule = 0x2F
    AABB = 0x30
    Nullable = 0x31
    Sfix = 0x32
    Sfix2 = 0x33
    Sfix3 = 0x34
    Sfix4 = 0x35
    AnimationCurve = 0x36
    KeyFrame = 0x37
    GameObjectRef = 0x38


def read_prop(f: io.BufferedReader, prop_type: PropType, base_offs=0):
    current = f.tell()
    offset = current
    match prop_type:
        case PropType.Bool:
            value = read_uint64(f) > 0
        case PropType.U8 | PropType.U16 | PropType.U32 | PropType.U64:
            value = read_uint64(f)
        case PropType.F32:
            value = read_float32(f)
        case _:
            value = None
            offset = read_uint64(f)
    if offset != current:
        f.seek(base_offs + offset)
        match prop_type:
            case PropType.Str16 | PropType.Asset:
                value = read_wstr(f)
            case PropType.Enum | PropType.Str8:
                value = read_str(f)
            case PropType.Size | PropType.Float2:
                value = read_float32_array(f, 2)
            case PropType.Vec3 | PropType.Float3:
                value = read_float32_array(f, 3)
            case PropType.Float4 | PropType.Rect:
                value = read_float32_array(f, 4)
            case PropType.Guid:
                value = str(f.read(16))
            case PropType.Color:
                value = [i / 255.0 for i in f.read(4)]
    f.seek(current + 8)
    return value, offset


class Attribute:
    def read_head(self, f: io.BufferedReader):
        self.type = PropType(read_uint32(f))
        self.unk = read_int32(f)
        self.name_offs = read_uint64(f)
        self.read_value(f)
        self.hash = f.read(4) # hash?
        padding = f.read(4)
        assert padding == b"\x00" * 4

    def read_value(self, f: io.BufferedReader):
        self.offset_to_offset = f.tell()
        self.value, self.value_offs = read_prop(f, self.type)

    def read_name(self, f: io.BufferedReader):
        f.seek(self.name_offs)
        self.name = read_str(f)      


    def seek_to_value(self, f: io.BufferedReader):
        f.seek(self.value_offs)


    def get_json(self):
        j = {
            "type": self.type.name,
            "name": self.name,
            "val_offs": self.value_offs
        }
        if self.value is not None:
            j["val"] = self.value
        if self.unk != -1:
            j["unk"] = self.unk
        return j


class SubElement:
    def read(self, f: io.BufferedReader):
        self.guids = f.read(48)
        self.name_offs = read_uint64(f)
        self.class_name_offs = read_uint64(f)
        self.sub_struct_offs = read_uint64(f)
        self.sub_structEnd_offs = read_uint64(f)
        self.extra_attr_offs = read_uint64(f)
        f.seek(self.sub_struct_offs)
        attr_count = read_uint64(f)
        self.attributes = [Attribute() for i in range(attr_count)]
        for attr in self.attributes:
            attr.read_head(f)
        for attr in self.attributes:
            attr.read_name(f)
        f.seek(self.extra_attr_offs)
        extra_attr_count = read_uint64(f)
        self.extra_attributes = [Attribute() for i in range(extra_attr_count)]
        for attr in self.extra_attributes:
            attr.read_head(f)
        for attr in self.extra_attributes:
            attr.read_name(f)

        f.seek(self.name_offs)
        self.name = read_wstr(f)
        f.seek(self.class_name_offs)
        self.class_name = read_str(f)

    def get_json(self, no_attr=False):
        j = {
            "name": self.name,
            "class": self.class_name
        }
        if no_attr:
            return j
        j["attributes"] =  [attr.get_json() for attr in self.attributes]
        if len(self.extra_attributes) > 0:
            j["extra_attributes"] = [attr.get_json() for attr in self.extra_attributes]
        return j

    def __getitem__(self, key):
        attrs = [attr for attr in self.attributes if attr.name == key]
        if len(attrs) != 1:
            raise KeyError(key)
        return attrs[0]


class ClipTrack:
    def read(self, f: io.BufferedReader, name_map_offs: int):
        self.child_track_count = read_uint16(f)
        self.prop_count = read_uint16(f)
        nul = read_uint32(f)
        assert nul == 0
        self.hash = f.read(8)
        name_offs = read_uint64(f)
        self.first_child_id = read_uint64(f)
        self.first_prop_id = read_uint64(f)
        end_offs = f.tell()
        f.seek(name_map_offs + name_offs * 2)
        self.name = read_wstr(f)
        f.seek(end_offs)

    def get_json(self):
        j = {
            "name": self.name,
            "child_track_count": self.child_track_count,
            "prop_count": self.prop_count
        }
        if self.child_track_count > 0:
            j["first_child_id"] = self.first_child_id
        if self.prop_count > 0:
            j["first_prop_id"] =  self.first_prop_id
        return j


class ClipProp:
    ARRAY_TYPES = [
        PropType.Color,
        PropType.Size,
        PropType.Vec2,
        PropType.Vec3,
        PropType.Vec4,
        PropType.Float2,
        PropType.Float3,
        PropType.Float4
    ]
    def read(self, f: io.BufferedReader, name_map_offs: int):
        self.start_frame = read_uint32(f)
        self.end_frame = read_float32(f)
        self.hash = f.read(8)
        name_offs = read_uint64(f)
        nul = read_uint64(f)
        assert nul == 0
        self.first_key_id = read_uint64(f)
        num = read_int16(f)
        self.unk = read_int16(f)
        nul = f.read(1)
        assert nul == b'\x00'
        self.type = PropType(f.read(1)[0])
        self.unk2 = read_uint16(f)
        nul = f.read(8)
        assert nul == b'\x00' * 8


        has_child = self.type in ClipProp.ARRAY_TYPES
        if has_child:
            self.key_count = 0
            self.child_count = num
        else:
            self.key_count = num
            self.child_count = 0

        end_offs = f.tell()
        f.seek(name_map_offs + name_offs)
        self.name = read_str(f)
        f.seek(end_offs)

    def get_json(self):
        j = {
            "name": self.name,
            "type": self.type.name,
            "start": self.start_frame,
            "end": self.end_frame,
            "first_key_id": self.first_key_id,
            "unk": self.unk,
            "unk2": self.unk2
        }
        if self.key_count > 0:
            j["key_count"] = self.key_count
        if self.child_count > 0:
            j["child_count"] = self.child_count
        return j


class ClipKey:
    def read(self, f: io.BufferedReader, prop: ClipProp, clip_start_offs: int):
        self.frame = read_float32(f)
        self.rate = read_float32(f)
        self.interpolation_type = read_uint32(f)
        self.unk = read_uint32(f)
        self.unk2 = read_uint32(f)
        self.value, self.value_offs = read_prop(f, prop.type, base_offs=clip_start_offs)
        nul = read_uint32(f)
        assert nul == 0

    def get_json(self):
        return {
            "frame": self.frame,
            "rate": self.rate,
            "interpolation": self.interpolation_type,
            "unk": self.unk,
            "unk2": self.unk2,
            "value": self.value,
            "value_offs": self.value_offs
        }


class Clip:
    MAGIC = b"CLIP"
    SUPPORTED_VERSIONS = [54]

    def read(self, f: io.BufferedReader):
        self.guid = f.read(16)
        f.seek(8, 1)
        self.name_offs = read_uint64(f)
        f.seek(8, 1)
        start = f.tell()
        magic = f.read(4)
        if magic != Clip.MAGIC:
            raise RuntimeError("Parse error. (Not a clip object.)")
        self.version = read_uint32(f)
        if self.version not in Clip.SUPPORTED_VERSIONS:
            raise RuntimeError(f"Unsupported clip version. ({self.version})")
        self.frame_count = read_float32(f)
        self.track_count = read_uint32(f)
        self.prop_count = read_uint32(f)
        self.key_count = read_uint32(f)
        self.clip_data_offs = read_uint64(f)
        self.props_offs = read_uint64(f)
        self.keys_offs = read_uint64(f)
        self.unk_offsets = read_uint64(f)
        self.unk_offsets2 = read_uint64(f)
        self.name_map_offs = read_uint64(f)
        self.unk_offsets3 = read_uint64(f)
        self.wide_name_map_offs = read_uint64(f)
        self.clip_end_offs = read_uint64(f)
        nul = read_uint64(f)
        assert nul == 0

        assert f.tell() == start + self.clip_data_offs
        self.tracks = [ClipTrack() for i in range(self.track_count)]
        for t in self.tracks:
            t.read(f, start + self.wide_name_map_offs)
        assert f.tell() == start + self.props_offs
        self.props = [ClipProp() for i in range(self.prop_count)]
        for p in self.props:
            p.read(f, start + self.name_map_offs)

        assert f.tell() == start + self.keys_offs
        self.keys = [ClipKey() for i in range(self.key_count)]
        props = sorted(self.props, key=lambda p: p.first_key_id)
        props = sum([[p] * p.key_count for p in props], [])


        if len(self.keys) != len(props):
            for t in self.tracks:
                print(t.get_json())
            for p in self.props:
                print(p.get_json())
            print(len(props))
            print(len(self.keys))
            print(f.tell())
        #for k, p in zip(self.keys, sorted(self.props, key=lambda x: x.key_id)):
        for k, p in zip(self.keys, props):
            k.read(f, p, start)
        f.seek(self.name_offs)
        self.name = read_wstr(f)

    def get_json(self):
        return {
            "name": self.name,
            "frame_count": self.frame_count,
            "tracks": [t.get_json() for t in self.tracks],
            "props": [p.get_json() for p in self.props],
            "keys": [k.get_json() for k in self.keys]
        }


class Element:
    def read(self, f: io.BufferedReader):
        self.guid = f.read(16)
        self.name_offs, self.class_name_offs, self.sub_offs, self.clip_offs = read_uint64_array(f, 4)

        f.seek(self.sub_offs)
        sub_element_count = read_uint64(f)
        self.sub_elements = [SubElement() for i in range(sub_element_count)]
        sub_element_offsets = read_uint64_array(f, sub_element_count)

        for sub_elm, offs in zip(self.sub_elements, sub_element_offsets):
            f.seek(offs)
            sub_elm.read(f)

        f.seek(self.clip_offs)
        f.seek(4, 1)
        clip_count = read_uint32(f)
        self.clips = [Clip() for i in range(clip_count)]
        clip_offsets = read_uint64_array(f, clip_count)
        for clip, offs in zip(self.clips, clip_offsets):
            f.seek(offs)
            clip.read(f)

        f.seek(self.name_offs)
        self.name = read_wstr(f)
        f.seek(self.class_name_offs)
        self.class_name = read_str(f)

    def get_json(self, no_attr=False, no_clip=False):
        j = {
            "name": self.name,
            "class": self.class_name,
            "sub_elements": [sub_elm.get_json(no_attr=no_attr) for sub_elm in self.sub_elements]
        }
        if not no_clip:
            j["clips"] = [clip.get_json() for clip in self.clips]
        return j

    def __getitem__(self, key):
        sub_elms = [sub_elm for sub_elm in self.sub_elements if sub_elm.name == key]
        if len(sub_elms) != 1:
            raise KeyError(key)
        return sub_elms[0]


class GUIResource:
    MAGIC = b"GUIR"
    SUPPORTED_VERSIONS = [540034]

    def read(self, f: io.BufferedReader):
        self.version = read_uint32(f)
        if self.version not in GUIResource.SUPPORTED_VERSIONS:
            raise RuntimeError(f"Unsupported file version. ({self.version})")

        magic = f.read(4)
        if magic != GUIResource.MAGIC:
            raise RuntimeError("Not GUI file.")

        # read offsets
        offsetsStart_offset = read_uint64(f)
        end_offs = read_uint64_array(f, 5)
        offsetsStart = read_uint64(f)
        view_offset = read_uint64(f)
        element_count = read_uint64(f)
        offsets = read_uint64_array(f, element_count)

        # read elements
        self.elements = [Element() for i in range(element_count)]
        for elm, ofs in zip(self.elements, offsets):
            f.seek(ofs)
            elm.read(f)

        # read sub elements
        f.seek(view_offset)
        self.view = SubElement()
        self.view.read(f)

    def get_json(self, no_attr=False, no_clip=False):
        j = {
            "type": "GUI",
            "version": self.version
        }
        j["elements"] = [elm.get_json(no_attr=no_attr, no_clip=no_clip) for elm in self.elements]
        j["view"] = self.view.get_json(no_attr=no_attr)
        return j

    def __getitem__(self, key):
        elms = [elm for elm in self.elements if elm.name == key]
        if len(elms) != 1:
            raise KeyError(key)
        return elms[0]

    def import_gui(self, file: str):
        with io.open(file, "rb") as f:
            self.read(f)

    """
    def export_gui(self, file: str):
        with io.open(file, "wb") as f:
            self.write(f)
    """

    def export_json(self, file: str, no_attr=False, no_clip=False):
        save_json(self.get_json(no_attr=no_attr, no_clip=no_clip), file)

    """
    def import_json(self, file: str):
        j = load_json(file)
        self.set_json(j)
    """

    def get_ext(self):
        return f"gui.{self.version}"
