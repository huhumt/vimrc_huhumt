#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path, PurePath
import argparse
import os


def do_replace(src: str, dst: str, filename: PurePath, whole_line_mode: bool):
    '''
    replace string in file
    '''

    line_number = 0
    found_number = 0
    out_binary_str = b""
    with open(filename, "rb") as f:
        for binary_line in f:
            line_number += 1
            try:
                line = binary_line.decode('utf-8')
                if src in line:
                    out_binary_str += (
                        f"{dst}{os.linesep}" if whole_line_mode
                        else line.replace(src, dst)
                    ).encode()
                    found_number += 1
                    print(f"\tLine {line_number:>5} ---> "
                          f"replace {src.strip()} with {dst.strip()}")
                else:
                    out_binary_str += line.encode('utf-8')
            except UnicodeDecodeError:
                out_binary_str += binary_line
                pass

    if found_number > 0:
        print(f"Replaced {found_number} in {filename.as_posix()}\n")
        with open(filename, "wb") as f:
            f.write(out_binary_str)


def string_replace(src: str, dst: str, filename: str, whole_line_mode: bool = False):
    '''
    repacle src with dst in filename or all files in directory
    '''

    support_filetype_list = [
        '.c', '.cpp', '.h', '.hpp', '.cc',
        '.txt'
    ]
    filepath = Path(filename)
    if filepath.is_file():
        do_replace(src, dst, filepath, whole_line_mode=whole_line_mode)
    elif filepath.is_dir():
        for f in list(filter(
                lambda x: x.is_file() and x.suffix in support_filetype_list,
                filepath.rglob("*"))):
            do_replace(src, dst, f, whole_line_mode=whole_line_mode)


if __name__ == "__main__":

    '''
    main entry for the program
    '''

    parser = argparse.ArgumentParser(
        description="replace string in a file of directory")
    parser.add_argument(
        "src", type=str,
        help="str need to be replaced"
    )
    parser.add_argument(
        "dst", type=str,
        help="string will be replaced to this"
    )
    parser.add_argument(
        "path", type=str,
        help="can be filename or directory"
    )
    parser.add_argument(
        "--whole_line_mode",
        help="""replace whole line with dst""",
        default=False, action="store_true"
    )

    args = parser.parse_args()
    string_replace(args.src, args.dst, args.path, args.whole_line_mode)
