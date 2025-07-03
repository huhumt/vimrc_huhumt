#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from collections import OrderedDict
import subprocess
import sys
import os
import re


MAIL_FLAG = "@test.co.uk"
APPEND_MODE, REWRITE_MODE = range(2)

append_newline_flag = False
address_book_header = ""


def read_address_book(filename):
    """
    read address_book file to python dict
    """

    def _search_valid_email(email_string):
        for s in email_string.split(","):
            email_address = s.strip()
            if email_address.endswith(MAIL_FLAG):
                return email_address
        return None

    global address_book_header
    global append_newline_flag

    address_book_dict = OrderedDict()

    with open(filename, 'r', encoding="utf-8") as fd:
        person_dict = OrderedDict()
        start_flag = False
        s_line = ""
        email = ""

        for line in fd:
            s_line = line.strip()
            if start_flag and s_line and "=" in s_line:
                key, val = [" ".join(s.split()) for s in s_line.split("=", 1)]
                if "email" in key.lower():
                    email = _search_valid_email(val.lower())
                    val = email
                person_dict[key] = val

            if re.search(r"\[([0-9]+)\]", s_line):  # find [1234]
                start_flag = True
                if (email and person_dict
                        and email not in address_book_dict.keys()):
                    address_book_dict[email] = person_dict
                person_dict = {}
                email = ""
            address_book_header += line if not start_flag else ""

        append_newline_flag = True if s_line else False
        if email and person_dict and email not in address_book_dict.keys():
            address_book_dict[email] = person_dict

    return address_book_dict


def read_email(email_text):
    """
    parse email
    """

    email_list = []
    # for line in email_text.splitlines():
    for line in email_text.splitlines():
        line_strip = line.lower().strip()
        if ((line_strip.startswith("from:")
             or line_strip.startswith("to:"))
                and MAIL_FLAG in line_strip):
            for s in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", line):
                if s.endswith(MAIL_FLAG) and s not in email_list:
                    email_list.append(s)
    return email_list


def update_address_book(filename, address_book_dict, email_list, mode):
    """
    update address_book based on email_list
    """

    new_string = ""
    address_book_len = len(address_book_dict.keys())
    for email in email_list:
        email_alphabet = re.sub("[ .]", "", email.lower())
        address_book_key_alphabet = [
            re.sub("[ .]", "", s.lower()) for s in address_book_dict.keys()
        ]

        if email_alphabet not in address_book_key_alphabet:
            new_string += f"[{address_book_len}]\n"
            name = email.split("@")[0].replace(".", " ").title()
            new_string += f"name={name}\n"
            new_string += f"email={email}\n\n"
            address_book_len += 1

    if mode == REWRITE_MODE:
        w_string = address_book_header
        for i, k in enumerate(address_book_dict):
            w_string += f"[{i}]\n"
            for key, val in address_book_dict[k].items():
                w_string += f"{key}={val}\n"
            w_string += "\n"
        with open(filename, "w", encoding="utf-8") as fd:
            fd.write(f"{w_string}{new_string}")
    else:
        if new_string:
            if append_newline_flag:
                new_string = f"\n{new_string}"
            with open(filename, "a", encoding="utf-8") as fd:
                fd.write(new_string)


def hyperlinks_text(url, hyper_txt):
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


if __name__ == "__main__":
    """
    main entry of the program
    """

    home = os.path.expanduser("~")
    filename = os.path.join(home, ".config/neomutt/test_addressbook")
    address_book_dict = read_address_book(filename)
    read_std_lines = sys.stdin.buffer.read().decode("utf-8", 'ignore')

    try:
        result = subprocess.run(
            [
                'shorten_url',
                "--update-message",
                "--url-min-length=100",
                read_std_lines
            ],
            stdout=subprocess.PIPE
        )
        sys.stdout.write(result.stdout.decode('utf-8').strip())
    except:
        sys.stdout.write(read_std_lines)

    email_list = read_email(read_std_lines)
    update_address_book(filename, address_book_dict, email_list, APPEND_MODE)
