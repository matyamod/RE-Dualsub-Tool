"""Coverter for gui files.

Notes:
    No function for json2gui yet.

    # Usage
    python src/edit_fslt.py file [-o=out]
    - file: path to .gui.
    - out: path to output folder.
"""

import argparse
import io
import os
from io_util import mkdir, write_float32_array
from REGUI import GUIResource

def edit_gui(file, out):
    if (os.path.basename(file) != "cs_ui0600.gui.540034"
        and os.path.basename(file) != "cs_ui3070.gui.540034"
        and os.path.basename(file) != "cs_ui3080.gui.540034"
        and os.path.basename(file) != "cs_ui3090.gui.540034"):
        return

    print(f"processing {file}...")
    gui = GUIResource()
    gui.import_gui(file)
    mkdir(out)

    def mult_attr(f, attr, factor=[1, 2]):
        attr.seek_to_value(f)
        value = attr.value
        write_float32_array(f, [value[0] * factor[0], value[1] * factor[1]])

    def add_attr(f, attr, add):
        attr.seek_to_value(f)
        value = attr.value
        write_float32_array(f, [value[0] + add[0], value[1] + add[1]])

    gui_path = os.path.join(out, os.path.basename(file))
    with io.open(gui_path, "wb") as f:
        readf = io.open(file, "rb")
        f.write(readf.read())
        if os.path.basename(file) == "cs_ui0600.gui.540034":
            elm = gui["c_tips_text"]
            attr = elm["mask"]["Size"]
            mult_attr(f, attr)
            attr = elm["mask"]["Position"]
            mult_attr(f, attr)
            attr = elm["m_tips0"]["RegionSize"]
            mult_attr(f, attr)
            attr = elm["m_tips1"]["RegionSize"]
            mult_attr(f, attr)
            attr = gui["c_tips"]["c_pageguide"]["Position"]
            mult_attr(f, attr, factor=[1, 1.6])
        elif os.path.basename(file) == "cs_ui3070.gui.540034":
            attr = gui["main"]["c_caption"]["Position"]
            add_attr(f, attr, [0, -40])
        elif os.path.basename(file) == "cs_ui3080.gui.540034":
            attr = gui["c_mode"]["c_preview"]["Position"]
            add_attr(f, attr, [0, 50])
        elif os.path.basename(file) == "cs_ui3090.gui.540034":
            attr = gui["main"]["c_value"]["Position"]
            add_attr(f, attr, [0, 50])
        readf.close()


def edit_gui_dir(directory, out):
    if os.path.isfile(directory):
        if is_gui_file(directory):
            edit_gui(directory, out)
        return

    out = os.path.join(out, os.path.basename(directory))
    for file_base in sorted(os.listdir(directory)):
        file = os.path.join(directory, file_base)
        edit_gui_dir(file, out)


def is_gui_file(file):
    splitted = file.split(".")
    if len(splitted) < 3:
        return False
    return splitted[-2] == "gui"


def dump_gui(file, out, no_attr=False, no_clip=False):
    if os.path.isfile(file) and is_gui_file(file):
        print(f"processing {file}...")
        gui = GUIResource()
        gui.import_gui(file)
        mkdir(out)
        json_path = os.path.join(out, os.path.basename(file) + ".json")
        gui.export_json(json_path, no_attr=no_attr, no_clip=no_clip)
        return

    directory = file
    out = os.path.join(out, os.path.basename(directory))
    for file_base in sorted(os.listdir(directory)):
        file = os.path.join(directory, file_base)
        dump_gui(file, out, no_attr=no_attr, no_clip=no_clip)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='path to .gui')
    parser.add_argument('-o', '--out', type=str, default=None, help='output directory.')
    parser.add_argument('-m', '--mode', type=str, default="dump",
                        help='dump: convert .gui to .json. edit: edit some files for RE4.')
    parser.add_argument('--no_attr', action='store_true',
                        help='Discard attribute data when exporting as json.')
    parser.add_argument('--no_clip', action='store_true',
                        help='Discard clip data when exporting as json.')
    args = parser.parse_args()
    if not os.path.exists(args.file):
        raise RuntimeError(f"Specified path does NOT exist. ({args.file})")
    return args


if __name__=="__main__":
    args = get_args()
    directory = args.file
    out = args.out
    match args.mode:
        case "edit":
            edit_gui_dir(directory, out)
        case "dump":
            no_attr = args.no_attr
            no_clip = args.no_clip
            dump_gui(directory, out, no_attr=no_attr, no_clip=no_clip)
        case _:
            print(args.mode == "dump")
            raise RuntimeError(f"Unsupported mode. ({args.mode})")