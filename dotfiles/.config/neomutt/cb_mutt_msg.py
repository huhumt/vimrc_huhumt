#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


class AddressBook:
    def __init__(self, filename):
        self.filename = filename

        try:
            with open(filename, "r", encoding="utf-8", errors="ignore") as f:
                self.address_book_header, self.address_book_list = (
                    self.read_address_book(f.read())
                )
        except FileNotFoundError:
            self.address_book_list = list()
            self.address_book_header = os.linesep.join(
                [
                    "# abook addressbook file",
                    "[format]",
                    "program=abook",
                    "version=0.6.1",
                    ""
                ]
            )

    @property
    def get_address_book_header(self):
        return self.address_book_header

    @property
    def get_address_book_list(self):
        return self.address_book_list

    @staticmethod
    def read_address_book(content):
        """
        read address_book file to python dict
        """

        re_header = re.compile(r"(?P<header>^[\s\S]+?)\[0\]")
        if header := re_header.findall(content):
            address_book_header = header[0]
        else:
            raise ValueError("Not a valid addressbook file")

        re_person = re.compile(
            r"(?:\[\d+\])"
            r"(?P<first>(?:\r?\n\w+=[ \S]+)*\r?\n)"
            r"email=(?P<email>[^,\s]+).*"
            r"(?P<end>(?:\r?\n\w+=[ \S]+)*)"
        )
        address_book_list = list()
        for first, email, end in re_person.findall(content):
            if AddressBook.validate_email(email):
                address_book_list.append((email, f"{first}email={email}{end}"))
        return address_book_header, address_book_list

    def update_address_book(self, email_list, force_write=False):
        """
        update address_book based on email_list
        """

        def _dict_to_abook_str(abook_list, start_cnt=0):
            """
            out abook string from list
            """
            two_newline = os.linesep * 2
            return two_newline.join(
                [
                    f"[{start_cnt + i}]{p[1]}"
                    for i, p in enumerate(
                        sorted(abook_list, key=lambda x: x[0])
                    )
                ]
                + [""]
            )

        new_email_list = []
        for email in email_list:
            email_alphabet = re.sub("[ .]", "", email.lower())
            address_book_key_alphabet = [
                re.sub("[ .]", "", s[0].lower()) for s in self.address_book_list
            ]

            if email_alphabet not in address_book_key_alphabet:
                name = email.split("@")[0].replace(".", " ").title()
                new_email_list.append(
                    (email, f"{os.linesep}name={name}{os.linesep}email={email}")
                )

        if force_write:
            with open(self.filename, "w", encoding="utf-8") as fd:
                fd.write(
                    self.address_book_header
                    + _dict_to_abook_str(
                        self.address_book_list + new_email_list
                    )
                )
        else:
            with open(self.filename, "a", encoding="utf-8") as fd:
                fd.write(
                    _dict_to_abook_str(
                        new_email_list, start_cnt=len(self.address_book_list)
                    )
                )

    @staticmethod
    def read_email(email_text):
        """
        parse email
        """
        re_date = re.compile(r"Date: \w+,[ ]+(?P<date>\d+[ ]+\w+[ ]+\d{4})")
        if email_date_re := re.findall(re_date, email_text):
            try:
                email_date = datetime.strptime(email_date_re[0], "%d %b %Y")
            except ValueError:
                pass
            else:
                one_month_ago_date = datetime.now() - timedelta(days=30)
                if email_date > one_month_ago_date:
                    re_email = r"[\w.+-]+@[\w-]+\.[\w.-]+"
                    return list(
                        f
                        for f in set(re.findall(re_email, email_text))
                        if AddressBook.validate_email(f)
                    )

    @staticmethod
    def validate_email(email_address):
        """
        validate email address
        """
        return all(
            [
                "@test.co.uk" in email_address,
                not bool(re.search(r"mr-\d+", email_address)),
                len(re.findall(r'\d', email_address)) < 5
            ]
        )

    @staticmethod
    def hyperlinks_text(url, hyper_txt):
        hyperlinks = "\033]8;{};{}\033\\{}\033]8;;\033\\"
        return hyperlinks.format("", url, hyper_txt)


if __name__ == "__main__":
    """
    main entry of the program
    """

    read_std_lines = sys.stdin.buffer.read().decode("utf-8", "ignore")

    try:
        result = subprocess.run(
            [
                "shorten_url",
                "--update-message",
                "--url-min-length=100",
                read_std_lines,
            ],
            stdout=subprocess.PIPE,
        )
        sys.stdout.write(result.stdout.decode("utf-8").strip())
    except Exception:
        sys.stdout.write(read_std_lines)

    abook_class = AddressBook(
        Path.home().joinpath(".config/neomutt/test_addressbook")
    )
    if email_list := abook_class.read_email(read_std_lines):
        abook_class.update_address_book(email_list, force_write=True)
