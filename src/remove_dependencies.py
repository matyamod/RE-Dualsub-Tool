"""Remove mmh3 and chardet from REMSG_Converter."""
import os
import shutil


def mkdir(dir):
    os.makedirs(dir, exist_ok=True)


def comment_out(line):
    indent=0
    for c in line:
        if c != " ":
            break
        indent+=1
    return " " * indent + "# " + line[indent:], indent


def read_function(file):
    empty_count = 0
    lines = []
    while empty_count < 2:
        line = file.readline()
        if not line:
            return lines + ["'''\n"]
        elif line in ["\n"]:
            empty_count += 1
        else:
            empty_count = 0
        lines.append(line)
    return lines[:-2] + ["'''\n", "\n", "\n"]


def copy_file(file, src_dir="REMSG_Converter", new_dir="src"):
    orig_path = os.path.join(src_dir, file)
    mkdir(new_dir)
    shutil.copy(orig_path, new_dir)

def edit_file(file, removable_functions, removable_lines, pass_lines,
                src_dir="REMSG_Converter", new_dir="src"):
    orig_path = os.path.join(src_dir, file)
    mkdir(new_dir)
    new_path = os.path.join(new_dir, file)
    file_orig = open(orig_path, "r")
    file_new = open(new_path, "w")
    while True:
        line = file_orig.readline()
        if not line:
            break

        skip = False
        for rem_f in removable_functions:
            if line.startswith(rem_f):
                file_new.write("'''\n")
                lines = [line] + read_function(file_orig)
                file_new.writelines(lines)
                skip = True
        if skip:
            continue

        for pass_l in pass_lines:
            if line.startswith(pass_l):
                line, indent = comment_out(line)
                file_new.write(" " * indent + "pass\n")
                break

        for rem_l in removable_lines:
            if line.startswith(rem_l):
                line, _ = comment_out(line)
                break

        file_new.write(line)

    file_orig.close()
    file_new.close()


if __name__=="__main__":
    removable_functions = {
        "REMSGUtil.py": [
            "def importCSV",
            "def importTXT",
            "def importJson",
            "def getEncoding"
        ]
    }

    removable_lines = {
        "REMSG.py": [
            "import mmh3",
            "                assert nameHash == entry.hash"
        ],
        "REMSGUtil.py": [
            "import chardet"
        ]
    }

    pass_lines = {
        "REMSG.py": [
            "                nameHash = mmh3"
        ]
    }

    python_files = ["REMSG.py", "REMSGUtil.py", "REWString.py", "HexTool.py"]

    for file in python_files:
        rem_f = removable_functions.get(file, [])
        rem_l = removable_lines.get(file, [])
        pass_l = pass_lines.get(file, [])
        if rem_f == [] and rem_l == [] and pass_l == []:
            copy_file(file)
        else:
            edit_file(file, rem_f, rem_l, pass_l)
