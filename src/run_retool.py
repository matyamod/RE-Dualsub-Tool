"""Extract only UI related files with REtool.exe

Notes:
    It'll use only UI related files from *.list.
    It won't take long time to extract.

    python src/run_retool.py retool pak file_list [-o=out]
    - retool: path to REtool.exe
    - pak: path to .pak
    - file_list: path to *.list.
    - out: output folder
"""

import argparse
import os
import subprocess

def mkdir(dir):
    os.makedirs(dir, exist_ok=True)

def get_args():
    parser = argparse.ArgumentParser(
                prog = 'python run_retool.py',
                description = 'Extract msg files from RE Engine games.')
    parser.add_argument('retool', type=str, help='Path to REtool.exe')
    parser.add_argument('pak', type=str, help='.pak for RE Engine games')
    parser.add_argument('file_list', type=str, help='.list for RETool')
    parser.add_argument('-o', '--out', type=str, default="out", help='output directory.')
    args = parser.parse_args()
    check_file_path(args.retool, "exe")
    check_file_path(args.pak, "pak")
    check_file_path(args.file_list, "list")
    print("Settings")
    print(f"  REtool: {args.retool}")
    print(f"  pak   : {args.pak}")
    print(f"  list  : {args.file_list}")
    print(f"  output: {args.out}")
    return args


def check_file_path(file, ext):
    if not file.endswith("." + ext):
        raise RuntimeError(f"{file} should be .{ext} file")
    if not os.path.exists(file):
        raise RuntimeError(f"{file} does NOT exist.")
    if not os.path.isfile(file):
        raise RuntimeError(f"{file} is NOT a file.")


def run_cmd(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (stdout, stderr) = proc.communicate()
    stdout = stdout.decode()
    print(stdout)
    if proc.returncode != 0:
        err_msg = stderr.decode()
        if len(err_msg) > 0:
            raise RuntimeError(err_msg)
    return stdout


def run_retool(retool, msg_list, pak, out):
    print("Running REtool...")
    batch = os.path.join(os.path.dirname(__file__), "run_retool.bat")
    mkdir(out)
    stdout = run_cmd(('cmd', '/c',
                      batch,
                      os.path.abspath(retool),
                      os.path.abspath(msg_list),
                      os.path.abspath(pak),
                      os.path.abspath(out)))
    if not stdout.split("\n")[-2].startswith("Extracted "):
        raise RuntimeError("REtool raised an unexpected error.")


def make_msg_list(file_list):
    print("Generating src\custom.list...")
    batch = os.path.join(os.path.dirname(__file__), "make_list.bat")
    run_cmd(('cmd', '/c', batch, os.path.abspath(file_list)))


if __name__ == "__main__":
    args = get_args()
    make_msg_list(args.file_list)
    msg_list = os.path.join(os.path.dirname(__file__), "custom.list")
    with open(msg_list, "r") as f:
        f.seek(0, 2)
        if f.tell() == 0:
            raise RuntimeError(f"No msg files in {args.file_list}")
    run_retool(args.retool, msg_list, args.pak, args.out)
    print(f"Done!")