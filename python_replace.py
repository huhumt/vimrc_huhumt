#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os

def get_file_type(filename):

    '''
    get file type
    '''
    return os.path.splitext(filename)[1]

def check_support_file(filename):

    '''
    check whether filetype is supported
    '''

    support_filetype_list = [ \
            '.c', '.cpp', '.h', '.hpp', '.cc', \
            '.txt'
            ]
    filetype = get_file_type(filename)
    if filetype in support_filetype_list:
        return True
    else:
        return False

def print_string_without_newline(input_string):

    '''
    if a string ends with \r\n, \n, \r, delete the newline characters
    '''

    if input_string[-2:] == "\r\n" or input_string[-2:] == "\n\r":
        return input_string[:-2]
    elif input_string[-1] == "\r" or input_string[-1] == "\n":
        return input_string[:-1]
    else:
        return input_string

def replace_whole_line_mode(ori, newest):

    '''
    add newline characters to newest string
    '''

    if ori[-2:] == "\r\n" or ori[-2:] == "\n\r":
        return newest + ori[-2:]
    elif ori[-1] == "\r" or ori[-1] == "\n":
        return newest + ori[-1]
    else:
        return newest

def do_replace(src, dst, filename, whole_line_mode):

    '''
    replace string in file
    '''

    if check_support_file(filename) is False:
        return 0

    read_fd = open(filename, 'rb')
    write_filename = filename + ".tmp"
    write_fd = open(write_filename, 'wb')
    replace_list = []
    line_number = 0
    try:
        for binary_line in read_fd:
            line_number += 1
            try:
                line = binary_line.decode('utf-8')
                if src in line:
                    if whole_line_mode is True:
                        line_replaced = replace_whole_line_mode(line, dst)
                    else:
                        line_replaced = line.replace(src, dst)
                    write_fd.write(line_replaced.encode('utf-8'))
                    replace_list.append([line_number, line, line_replaced])
                else:
                    write_fd.write(line.encode('utf-8'))
            except UnicodeDecodeError:
                write_fd.write(binary_line)
                pass
    finally:
        read_fd.close()
        write_fd.close()

    if replace_list:
        print("\nIn %s:" % (filename))
        for (i, ori, newest) in replace_list:
            print("\tLine %d ---> replace %s with %s" \
                    % (i, print_string_without_newline(ori.encode('utf-8')), print_string_without_newline(newest.encode('utf-8'))))

    os.remove(filename)
    os.rename(write_filename, filename)

def string_replace(src, dst, filename, whole_line_mode = False):

    '''
    repacle src with dst in filename
    '''

    if os.path.islink(filename):
        return 0
    elif os.path.isfile(filename):
        do_replace(src, dst, filename, whole_line_mode = whole_line_mode)
    elif os.path.isdir(filename):
        directory_list = os.listdir(filename)
        if filename[-1] == "/":
            filename = filename[:-1]
        for directory in directory_list:
            string_replace(src, dst, filename + "/" + directory, whole_line_mode = whole_line_mode)
    else:
        return 0

    return 0

if __name__ == "__main__":

    '''
    main entry for the program
    '''

    parameter_len = len(sys.argv)
    if parameter_len < 3:
        print("Usage: Python3 python_replace.py src dst filename/directory whole_line_mode=True/False")
        print("whole_line_mode is opitional to replace src with dst for the whole line")
        exit(0)
    elif parameter_len > 4:
        string_replace(sys.argv[1], sys.argv[2], sys.argv[3], True)
    else:
        string_replace(sys.argv[1], sys.argv[2], sys.argv[3])
