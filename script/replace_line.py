#!/usr/bin/env python3

import sys, fileinput

def replace_text(filename, text_to_search, replacement_text):
    """
    replace a line in file
    """
    fd = fileinput.FileInput(filename, inplace=True, backup='.bak')
    for line in fd:
        print(line.replace(text_to_search, replacement_text), end='')

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 replace_line filename search_text replace_text")
    else:
        replace_text(sys.argv[1], sys.argv[2], sys.argv[3])
