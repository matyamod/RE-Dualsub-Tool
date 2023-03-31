"""Make dualsub mod.

Notes:
    It'll search src recursively.
    I recommend using run_retool.py to make a folder that have only UI related assets before using make_dualsub.py.

    # Usage
    python src/make_dualsub.py src --main_lang=l1 --sub_lang=l2 -j=json [options]
    - src: path to .msg files
    - l1: use this as 2nd language when user's language is the same as l2.
    - l2: use this as 2nd language for other languages.
    - json: json file that has entry name patterns. use entry_patterns/re4.json for RE4 files.

    # Language list
    ja: Japanese               en: English
    fr: French                 it: Italian
    de: German                 es: Spanish
    ru: Russian                pl: Polish
    nl: Dutch                  pt: Portuguese
    ptbr: PortugueseBr         ko: Korean
    zhtw: TraditionalChinese   zhcn: SimplifiedChinese
    fi: Finnish                sv: Swedish
    da: Danish                 no: Norwegian
    cs: Czech                  hu: Hungarian
    sk: Slovak                 ar: Arabic
    tr: Turkish                bg: Bulgarian
    el: Greek                  ro: Romanian
    th: Thai                   ua: Ukrainian
    vi: Vietnamese             id: Indonesian
    cc: Fiction                hi: Hindi
    es419: LatinAmericanSpanish
"""

import argparse
from argparse import RawTextHelpFormatter
import json
import os
import re
import textwrap

import REMSGUtil
from REMSG import MSG, LANG_LIST

SHORT_LANG_TO_INT = REMSGUtil.SHORT_LANG_LU
SHORT_LANG_TO_LONG = {key: LANG_LIST[i] for key, i in SHORT_LANG_TO_INT.items()}


def mkdir(dir):
    os.makedirs(dir, exist_ok=True)


def get_args():
    # Make description for the language options.
    lang_list = "language list: \n"
    lf_flag = False
    for key, val in SHORT_LANG_TO_LONG.items():
        lang_list += f"  {key}: {val} "
        lang_list += "\n" if lf_flag else " " * (22 - len(key) - len(val))
        lf_flag = not lf_flag

    # Parse args
    parser = argparse.ArgumentParser(
                prog = 'python make_dualsub.py',
                description = 'Make dual-subtitle mods for RE Engine games.',
                formatter_class=RawTextHelpFormatter,
                epilog = textwrap.dedent(lang_list))
    parser.add_argument('source', type=str, help='.msg file or directory')
    parser.add_argument('-l1', '--main_lang', type=str, default="en",
                        help="use this as 2nd language when user's language is the same as sub_lang.")
    parser.add_argument('-l2', '--sub_lang', type=str, default="ja",
                        help='use this as 2nd language for other languages.')
    parser.add_argument('-o', '--out', type=str, default="out", help='output directory.')
    parser.add_argument('-j', '--patterns_json', type=str, default="",
                        help='json file that has entry name patterns.')
    parser.add_argument('--save_as_json', action='store_true',
                        help='Save editted files as json.')
    parser.add_argument('--ignore_one_line', action='store_true',
                        help='Use "one_line_entries" patters as "ignore_entries".')
    args = parser.parse_args()

    # Check args
    if args.main_lang not in SHORT_LANG_TO_LONG.keys():
        raise RuntimeError(f"{args.main_lang} is not supported.\n{lang_list}")
    if args.sub_lang not in SHORT_LANG_TO_LONG.keys():
        raise RuntimeError(f"{args.sub_lang} is not supported.\n{lang_list}")
    if not os.path.exists(args.source):
        raise RuntimeError(f"Specified path does NOT exist. ({args.source})")

    print(f"Input: {args.source}")
    print(f"Output: {args.out}")
    print(f"Main lang: {SHORT_LANG_TO_LONG[args.main_lang]}")
    print(f"2nd lang: {SHORT_LANG_TO_LONG[args.sub_lang]}")
    print(f"Patterns file: {args.patterns_json}")
    print(f"Save as json: {args.save_as_json}")
    print(f"Ignore one line: {args.ignore_one_line}")

    return args


def read_json(json_path):
    try:
        with open(json_path, encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def has_pattern(entry, patterns: list[str]):
    for pt in patterns:
        if re.match(pt, entry.name):
            return True
    return False


def should_skip(entry, ignore_entries: list[str]):
    # ignore_entries: entry name pattern whose text should be displayed in a language.
    text = entry.langs[0]
    if has_pattern(entry, ignore_entries):
        return True
    if text.startswith("<COLOR"):
        return True
    if text.startswith("<") and text.split(">")[1] == "":
        return True
    return False


def should_be_one_line(entry, one_line_entries: list[str]):
    # one_line_entries: entry name pattern whose text should be displayed in a line.
    text = entry.langs[0]
    if has_pattern(entry, one_line_entries) and "\r\n" not in text:
        return True
    if text.startswith("<ICON") and "\r\n" not in text:
        return True
    return False


def is_almost_same(text1, text2):
    tl1 = text1.lower()
    tl2 = text2.lower()
    if (tl2 in tl1 or tl2 == tl1 + "s"
        or tl2 == tl1 + "."
        or tl2 == tl1 + "es"
        or tl2 == tl1[:-1] + "ies"
        or tl2 == "the " + tl1):
        return True
    if tl1.replace(" ", "") == tl2.replace(" ", ""):
        return True
    return False


def merge_text(main_text, sub_text, sep="\r\n", is_three_lines=False):
    if (len(main_text) <= 100 and len(sub_text) <= 100
        and is_almost_same(main_text, sub_text)):
        return main_text
    if is_three_lines and ("\r\n" in main_text) and ("\r\n" in sub_text):
        main_splitted = main_text.split("\r\n")
        if main_splitted[-1] == "":
            main_splitted = main_splitted[:-1]
        sub_splitted = sub_text.split("\r\n")
        if sub_splitted[-1] == "":
            sub_splitted = sub_splitted[:-1]
        if len(main_text) >= len(sub_text):
            sub_text = " ".join(sub_splitted)
        else:
            main_text = " ".join(main_splitted)
    return main_text + sep + sub_text


def merge_entry(entry, main_lang: int, sub_lang: int,
                ignore_entries, one_line_entries,
                three_lines_entries,
                ignore_one_line=False):
    contents = entry.langs
    sub_text = contents[sub_lang]
    if sub_text in ["", "\n"] or should_skip(entry, ignore_entries):
        return
    separator = "\r\n"
    if should_be_one_line(entry, one_line_entries):
        if ignore_one_line:
            return
        separator = " / "

    is_three_lines = has_pattern(entry, three_lines_entries)

    new_contents = []

    for i, text in zip(range(len(contents)), contents):
        if text in ["", "\n"]:
            new_contents.append(text)
            continue
        if i == sub_lang:
            main_text = contents[main_lang]
            if main_text in ["", "\n"]:
                new_contents.append(text)
                continue
            new_text = merge_text(text, main_text,
                                  sep=separator,
                                  is_three_lines=is_three_lines)
        else:
            new_text = merge_text(text, sub_text,
                                  sep=separator,
                                  is_three_lines=is_three_lines)
        new_contents.append(new_text)
    entry.setContent(new_contents)


def merge_msg(file, out, main_lang: int, sub_lang: int,
              ignore_entries, one_line_entries,
              three_lines_entries,
              save_as_json=False, ignore_one_line=False):
    print(f"Processing {file}...")
    msg: MSG = REMSGUtil.importMSG(os.path.abspath(file))
    mkdir(out)
    new_file = os.path.abspath(os.path.join(out, os.path.basename(file)))

    for entry in msg.entrys:
        merge_entry(entry, main_lang, sub_lang,
                    ignore_entries, one_line_entries,
                    three_lines_entries,
                    ignore_one_line=ignore_one_line)
    if save_as_json:
        REMSGUtil.exportJson(msg, new_file + ".json")
    else:
        REMSGUtil.exportMSG(msg, new_file)


def is_msg(file):
    splitted = file.split(".")
    return len(splitted) >= 3 and splitted[-2] == "msg"


def merge_dir(directory, out, main_lang: int, sub_lang: int,
              ignore_entries, one_line_entries,
              three_lines_entries,
              save_as_json=False, ignore_one_line=False):
    out = os.path.join(out, os.path.basename(directory))
    for base in sorted(os.listdir(directory)):
        file = os.path.join(directory, base)
        if os.path.isfile(file):
            if is_msg(file):
                merge_msg(file, out, main_lang, sub_lang,
                          ignore_entries, one_line_entries,
                          three_lines_entries,
                          save_as_json=save_as_json, ignore_one_line=ignore_one_line)
        else:
            merge_dir(file, out, main_lang, sub_lang,
                      ignore_entries, one_line_entries,
                      three_lines_entries,
                      save_as_json=save_as_json, ignore_one_line=ignore_one_line)


if __name__ == "__main__":
    args = get_args()

    main_lang: int = SHORT_LANG_TO_INT[args.main_lang]
    sub_lang: int = SHORT_LANG_TO_INT[args.sub_lang]

    patterns_json: dict = read_json(args.patterns_json)
    ignore_entries: list[str] = patterns_json.get("ignore_entries", [])
    one_line_entries: list[str] = patterns_json.get("one_line_entries", [])
    three_lines_entries: list[str] = patterns_json.get("three_lines_entries", [])

    save_as_json: bool = args.save_as_json
    ignore_one_line: bool = args.ignore_one_line

    if os.path.isfile(args.source):
        merge_msg(args.source, args.out, main_lang, sub_lang,
                  ignore_entries, one_line_entries,
                  three_lines_entries,
                  save_as_json=save_as_json, ignore_one_line=ignore_one_line)
    elif os.path.isdir(args.source):
        merge_dir(args.source, args.out, main_lang, sub_lang,
                  ignore_entries, one_line_entries,
                  three_lines_entries,
                  save_as_json=save_as_json, ignore_one_line=ignore_one_line)
