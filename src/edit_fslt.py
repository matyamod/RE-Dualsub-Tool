"""Coverter for fslt files.

Notes:
    python src/edit_fslt.py file [-o=out]
    - file: path to fslt or json.
    - out: path to output folder.
"""

import argparse
import os
from io_util import mkdir
from REFontSlot import FontSlot, Slot


def is_fslt_file(file: str) -> bool:
    splitted: list[str] = os.path.basename(file).split(".")
    if len(splitted) < 3:
        return False
    return splitted[-2] == "fslt"


def merge_fslt(fslt1: FontSlot, fslt2: FontSlot):
    for slot1, slot2 in zip(fslt1.slots, fslt2.slots):
        merge_slot(slot1, slot2)


def merge_slot(slot1: Slot, slot2: Slot):
    names = [info.name for info in slot1.info_lists[0]]
    for info in slot2.info_lists[0]:
        if info.name not in names:
            slot1.info_lists[0].append(info)

    # Idk if we can merge FileInfo2. so, it'll just swap.
    if len(slot1.info_lists[1]) == 0:
        slot1.info_lists[1] = slot2.info_lists[1]
    if len(slot1.info_lists[2]) == 0:
        slot1.info_lists[2] = slot2.info_lists[2]


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=str, help='.fslt or .json')
    parser.add_argument('--dir', type=str, default=None, help='fslt folder for merge mode.')
    parser.add_argument('-o', '--out', type=str, default=None, help='output directory.')
    parser.add_argument('-m', '--mode', type=str, default="convert",
                        help='convert: covert between .fslt and .json. merge: merge a .fslt file into other files.')
    args = parser.parse_args()
    if not os.path.exists(args.file):
        raise RuntimeError(f"Specified path does NOT exist. ({args.file})")
    if args.mode == "merge":
        if not os.path.isdir(args.dir):
            raise RuntimeError(f"--dir should be a directory. ({args.dir})")
    return args


if __name__ == "__main__":
    args = get_args()
    file = args.file
    out = args.out

    match args.mode:
        case "convert":
            fslt = FontSlot()
            if file.endswith(".json"):
                if out is None:
                    out = "fslt"
                fslt.import_json(file)
                mkdir(out)
                new_file = os.path.join(out, os.path.basename(file)[:-4] + fslt.get_ext())
                fslt.export_fslt(new_file)
            elif is_fslt_file(file):
                if out is None:
                    out = "json"
                fslt.import_fslt(file)
                mkdir(out)
                file_base = ".".join(os.path.basename(file).split(".")[:-2])
                new_file = os.path.join(out, file_base + ".json")
                fslt.export_json(new_file)
            else:
                raise RuntimeError(f"Not .json nor .fslt.* ({file})")
        case "merge":
            directory = args.dir
            src_fslt = FontSlot()
            src_fslt.import_fslt(file)
            mkdir(out)
            for trg in sorted(os.listdir(directory)):
                if not is_fslt_file(trg):
                    continue
                trg_file = os.path.join(directory, trg)
                print(f"processing {trg_file}...")
                trg_fslt = FontSlot()
                trg_fslt.import_fslt(trg_file)
                merge_fslt(trg_fslt, src_fslt)
                new_file = os.path.join(out, trg)
                trg_fslt.export_fslt(new_file)
        case _:
            raise RuntimeError(f"Unsupported mode. ({args.mode})")
