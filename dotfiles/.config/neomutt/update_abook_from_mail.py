#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re


def read_abook(abook_filename):
    """
    read abook file to python dict
    """

    fd = open(abook_filename, 'r', encoding="utf-8")
    start_flag = 0
    abook_dict = {}
    person_dict = {}
    email = ""
    abook_len = 0
    for line in fd:
        if start_flag > 0:
            key = line.split("=")[0].strip()
            val = " ".join(line.split("=")[-1].split())
            person_dict[key] = val

            if "email" == key.lower():
                for person_email in val.split(","):
                    if "@test.co.uk" in person_email:
                        email = person_email.lower().replace(" ", "")
                        break

        num_list = re.findall(r"\[([0-9]+)\]", line)  # find [1234]
        if num_list:
            start_flag = 1
            abook_len = int(num_list[0]) + 1
        elif not line.strip():
            start_flag = 0
            if email.strip():
                abook_dict[email] = person_dict
            person_dict = {}
            email = ""
    fd.close()
    return abook_dict, abook_len


def read_email(email_text):
    """
    parse email
    """

    email_list = []
    mail_flag = "@test.co.uk"
    # for line in email_text.splitlines():
    for line in email_text.splitlines():
        line_strip = line.lower().strip()
        if ((line_strip.startswith("from:")
             or line_strip.startswith("to:"))
                and mail_flag in line_strip):
            for tmp in re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]+", line):
                if tmp.endswith(mail_flag) and tmp not in email_list:
                    email_list.append(tmp)
    return email_list


def update_abook(abook_filename, abook_dict, abook_len, email_list):
    """
    update abook based on email_list
    """

    new_string = ""
    for email in email_list:
        email_alphabet = re.sub("[ .]", "", email)
        abook_key_alphabet = [re.sub("[ .]", "", s) for s in abook_dict.keys()]
        if email_alphabet not in abook_key_alphabet:
            new_string += f"[{abook_len}]\n"
            name = email.split("@")[0].replace(".", " ").title()
            new_string += f"name={name}\n"
            new_string += f"email={email}\n\n"
            abook_len += 1

    if new_string:
        fd = open(abook_filename, "a", encoding="utf-8")
        fd.write(new_string)
        fd.close()


if __name__ == "__main__":
    """
    main entry of the program
    """

    home = os.path.expanduser("~")
    filename = os.path.join(home, ".config/neomutt/test_addressbook")
    abook_dict, abook_len = read_abook(filename)
    email_list = read_email(sys.argv[1])
    update_abook(filename, abook_dict, abook_len, email_list)
