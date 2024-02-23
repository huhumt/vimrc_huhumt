#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re

from urllib.parse import urlencode
from urllib.request import build_opener


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

    address_book_dict = {}
    person_dict = {}

    start_flag = False
    s_line = ""
    email = ""

    with open(filename, 'r', encoding="utf-8") as fd:
        for line in fd:
            s_line = line.strip()
            if start_flag and s_line and "=" in s_line:
                key = s_line.split("=")[0].strip()
                val = " ".join(s_line.split("=")[-1].split())

                if "email" == key.lower():
                    email = _search_valid_email(val.lower())
                else:
                    person_dict[key] = val

            if re.search(r"\[([0-9]+)\]", s_line):  # find [1234]
                start_flag = True
                if (email and person_dict
                        and email not in address_book_dict.keys()):
                    address_book_dict[email] = person_dict
                person_dict = {}
                email = ""
            address_book_header += line if not start_flag else ""

    if email and person_dict and email not in address_book_dict.keys():
        address_book_dict[email] = person_dict
    append_newline_flag = True if s_line else False

    return dict(sorted(address_book_dict.items()))


def shorten_url(message):
    # regex are based on urlbar.py, written by xt
    # Extended to reflect RFC3986/3987 by MacGyver
    url_scheme = r'[a-zA-Z][a-zA-Z0-9+\-.]*'

    url_octet = r'(?:2(?:[0-4]\d|5[0-5])|1\d\d|\d{1,2})'
    url_ipaddr = r'%s(?:\.%s){3}' % (url_octet, url_octet)

    url_hexdig = r'[0-9a-fA-F]'
    url_h16 = r'%s{1,4}' % (url_hexdig)
    url_ls32 = r'(?:%s:%s|%s)' % (url_h16, url_h16, url_ipaddr)
    url_ip6addr = [r'(?:%s:){6}%s' % (url_h16, url_ls32),
                   r'::(?:%s:){5}%s' % (url_h16, url_ls32),
                   r'%s?::(?:%s:){4}%s' % (url_h16, url_h16, url_ls32),
                   r'(?:(?:%s:){0,1}%s)?::(?:%s:){3}%s' % (url_h16, url_h16,
                                                           url_h16, url_ls32),
                   r'(?:(?:%s:){0,2}%s)?::(?:%s:){2}%s' % (url_h16, url_h16,
                                                           url_h16, url_ls32),
                   r'(?:(?:%s:){0,3}%s)?::(?:%s:)%s' % (url_h16, url_h16,
                                                        url_h16, url_ls32),
                   r'(?:(?:%s:){0,4}%s)?::%s' % (url_h16, url_h16, url_ls32),
                   r'(?:(?:%s:){0,5}%s)?::%s' % (url_h16, url_h16, url_h16),
                   r'(?:(?:%s:){0,6}%s)?::' % (url_h16, url_h16)]
    url_ip6addr = "(?:" + ")|(?:".join(url_ip6addr) + ")"
    url_iplit = r'\[(?:%s)\]' % (url_ip6addr)  # We're ignoring the IPvFuture

    url_gendelims = r'[:/?#\[\]@]'
    url_subdelims = r"[!$&'()*+,;=]"
    url_reserved = r'(?:%s|%s)' % (url_gendelims, url_subdelims)
    url_iunreserved = r'[\w\-.~]'

    url_pctencoded = r'%%%s{2}' % (url_hexdig)

    url_iregname = r'(?:%s|%s|%s)*' % (url_iunreserved, url_pctencoded,
                                       url_subdelims)

    url_iuserinfo = r'(?:%s|%s|%s|:)*' % (url_iunreserved, url_pctencoded,
                                          url_subdelims)
    url_ihost = r'(?:%s|%s|%s)' % (url_iplit, url_ipaddr, url_iregname)
    url_iauth = r'(?:%s@)?%s(?::\d*)?' % (url_iuserinfo, url_ihost)

    url_ipchar = r'(?:%s|%s|%s|:|@)' % (url_iunreserved, url_pctencoded,
                                        url_subdelims)
    url_ipath_abempty = r'(?:/%s*)*' % (url_ipchar)

    # Some complex stuff about reserved parts of the UCS namespace
    # we're not doing in iquery, so iquery == ifragment.
    # It seems that [ and ] are not used as delimiters in iquery
    # and ifragment, so allow them in these segments.
    url_iquery = r'(?:%s|/|\?|\[\])*' % (url_ipchar)
    url_ifragment = url_iquery

    # Grab one additional character (if present) so that we can
    # later determine whether the user knew what they were doing.
    url_full = (
        r'(?P<url>(?:%s)://(?:%s)(?:%s)(?:\?%s)?(?:#%s)?)(?P<trailer>.)?' % (
            url_scheme, url_iauth, url_ipath_abempty,
            url_iquery, url_ifragment)
    )
    regex = re.compile(url_full, re.IGNORECASE)
    ISGD = 'https://is.gd/create.php?format=simple&%s'
    short_url_list = []

    for match in regex.finditer(message):
        url = match.group('url')
        trailer = match.group('trailer')

        # Heuristics for dealing with valid URI characters used as URI
        # delimiters.
        if url[-1] == ',':
            # Does the URL contain other commas? If so, don't strip.
            # Is the URL followed by a space? If not, don't strip.
            if trailer == ' ' and url[:-1].count(',') == 0:
                url = url[:-1]
        elif url[-1] == '.' or url[-1] == '?':
            # Strip if the URL is followed by whitespace *or* nothing.
            # Nothing seems to use a . at the end, and it's a natural
            # sentence terminator.
            if trailer is None or trailer == ' ':
                url = url[:-1]
        elif url[-1] == ')' or url[-1] == ']':
            # Tough one. First check whether the URL is followed by
            # a space or end of line.
            if trailer is None or trailer == ' ':
                closer = url[-1]
                closer_to_opener = {")": "(", "]": "["}
                opener = closer_to_opener[closer]
                # Check if the brackets would be balanced inside the URL.
                opening = url.count(opener)
                closing = url.count(closer)
                if opening < closing:
                    match_start, match_end = match.span('url')
                    # Is the URL *immediately* preceded by an opener?
                    prior = message[:match_start]
                    if prior and prior[-1] == opener:
                        url = url[:-1]
                    else:
                        after = message[match_end:]
                        # Are brackets outside of the URL unbalanced?
                        opening = prior.count(opener) + after.count(opener)
                        closing = prior.count(closer) + after.count(closer)
                        url = (url[:-1] if opening > closing else url)
        elif url[-1] == "'":
            # Another doozy. Can't really work with balance because of
            # contractions such as "can't".
            # So let's simply check for enclosing, but only if there's not
            # another delimiter.
            if trailer is None or trailer == ' ':
                match_start = match.start('url')
                if match_start > 0 and message[match_start - 1] == "'":
                    url = url[:-1]
        # End heuristics

        if len(url) > 64:
            url = ISGD % urlencode({'url': url})
            try:
                opener = build_opener()
                opener.addheaders = [('User-Agent', 'weechat')]
                short_url_list.append(opener.open(url).read().decode('utf-8'))
            except:
                pass
    return short_url_list


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
        email_alphabet = re.sub("[ .]", "", email)
        address_book_key_alphabet = [
            re.sub("[ .]", "", s) for s in address_book_dict.keys()]
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
            w_string += f"email={k}\n\n"
        with open(filename, "w", encoding="utf-8") as fd:
            fd.write(f"{w_string}{new_string}")
    else:
        if new_string:
            if append_newline_flag:
                new_string = f"\n{new_string}"
            with open(filename, "a", encoding="utf-8") as fd:
                fd.write(new_string)


if __name__ == "__main__":
    """
    main entry of the program
    """

    home = os.path.expanduser("~")
    filename = os.path.join(home, ".config/neomutt/test_addressbook")
    address_book_dict = read_address_book(filename)

    read_std_lines = ""
    for line in sys.stdin:
        read_std_lines += line

    write_std_lines = ""
    for s in read_std_lines.splitlines():
        write_std_lines += f"{s}\n"
        left_white = len(s) - len(s.lstrip())
        for short_url in shorten_url(s):
            write_std_lines += f"{'  ' * left_white}[ {short_url} ]\n"
    sys.stdout.write(write_std_lines)

    email_list = read_email(read_std_lines)
    update_address_book(filename, address_book_dict, email_list, APPEND_MODE)
