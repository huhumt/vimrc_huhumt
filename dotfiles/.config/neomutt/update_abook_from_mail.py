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

        if re.match(r"\[([0-9]+)\]", line):  # match [1234]
            start_flag = 1
        elif not line.strip():
            start_flag = 0
            if email.strip():
                abook_dict[email] = person_dict
            person_dict = {}
            email = ""
    fd.close()
    return abook_dict


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


def update_abook(abook_filename, abook_dict, email_list):
    """
    update abook based on email_list
    """

    num = len(abook_dict.keys())
    new_string = ""
    for email in email_list:
        email_alphabet = re.sub("[ .]", "", email)
        abook_key_alphabet = [re.sub("[ .]", "", s) for s in abook_dict.keys()]
        if email_alphabet not in abook_key_alphabet:
            new_string = f"[{num}]\n"
            name = email.split("@")[0].replace(".", " ").title()
            new_string += f"name={name}\n"
            new_string += f"email={email}\n\n"
            num += 1

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
    abook_dict = read_abook(filename)
    email_list = read_email(sys.argv[1])
    update_abook(filename, abook_dict, email_list)
