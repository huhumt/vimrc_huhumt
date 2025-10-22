#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import subprocess
import sys
import os
import re


class AddressBook:
    def __init__(self, filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                self.address_book = f.read()
        except FileExistsError as e:
            print(e)
        except UnicodeDecodeError as e:
            print(e)

        self.filename = filename
        self.address_book_header = ""
        self.address_book_list = list()

    @property
    def get_address_book(self):
        return self.address_book

    @property
    def get_address_book_header(self):
        return self.address_book_header

    @property
    def get_address_book_list(self):
        return self.address_book_list

    def read_address_book(self):
        """
        read address_book file to python dict
        """

        re_header = r'(?P<header>^[\s\S]+?)\[0\]'
        if header := re.findall(re_header, self.address_book):
            self.address_book_header = header[0]
        else:
            raise ValueError("Not a valid addressbook file")

        re_person = r'(?:\[\d+\])(?P<first>(?:\r?\n\w+=[ \S]+)*\r?\n)email=(?P<email>[^,\s]+).*(?P<end>(?:\r?\n\w+=[ \S]+)*)'
        for first, email, end in re.findall(re_person, self.address_book):
            if self.validate_email(email):
                self.address_book_list.append(
                    (email, f"{first}email={email}{end}")
                )

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
                    f"[{start_cnt+i}]{p[1]}"
                    for i, p in enumerate(sorted(abook_list, key=lambda x: x[0]))
                ]
                + [""]
            )

        new_email_list = []
        for email in email_list:
            email_alphabet = re.sub("[ .]", "", email.lower())
            address_book_key_alphabet = [
                re.sub("[ .]", "", s[0].lower())
                for s in self.address_book_list
            ]

            if email_alphabet not in address_book_key_alphabet:
                name = email.split("@")[0].replace(".", " ").title()
                new_email_list.append(
                    (email, f"{os.linesep}name={name}{os.linesep}email={email}")
                )

        if force_write:
            with open(self.filename, "w", encoding="utf-8") as fd:
                fd.write(self.address_book_header + _dict_to_abook_str(
                    self.address_book_list + new_email_list
                ))
        else:
            with open(self.filename, "a", encoding="utf-8") as fd:
                fd.write(_dict_to_abook_str(
                    new_email_list, start_cnt=len(self.address_book_list)
                ))

    @staticmethod
    def read_email(email_text):
        """
        parse email
        """
        try:
            re_date = r'Date: \w+,[ ]+(?P<date>\d+[ ]+\w+[ ]+\d{4})'
            email_date_re = re.findall(re_date, email_text)
            email_date = datetime.strptime(email_date_re[0], '%d %b %Y').date()
            one_month_ago_date = (datetime.now() - timedelta(days=30)).date()
            if email_date > one_month_ago_date:
                re_email = r'[\w.+-]+@[\w-]+\.[\w.-]+'
                return list(
                    f for f in set(re.findall(re_email, email_text))
                    if AddressBook.validate_email(f)
                )
            else:
                return list()
        except:
            return list()

    @staticmethod
    def validate_email(email_address):
        """
        validate email address
        """
        return all([
            "test.co.uk" in email_address,
            not bool(re.search(r'mr-\d+', email_address))
        ])

    @staticmethod
    def hyperlinks_text(url, hyper_txt):
        hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
        return hyperlinks.format("", url, hyper_txt)


if __name__ == "__main__":
    """
    main entry of the program
    """

    with open("./test.txt", "r") as f:
        read_std_lines = f.read()

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

    home = os.path.expanduser("~")
    filename = os.path.join(home, ".config/neomutt/test_addressbook")
    abook_class = AddressBook(filename)
    abook_class.read_address_book()
    if email_list := abook_class.read_email(read_std_lines):
        abook_class.update_address_book(email_list, force_write=True)
