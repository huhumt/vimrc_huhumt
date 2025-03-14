#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.parse import urlparse
import webbrowser
import sys
import re


def open_url(url):
    """
    open url in default browser
    if it's a real url, from https://stackoverflow.com/a/38020041
    or search by duckduckgo
    """
    url_set = set()
    bracket_dict = {
        ")": "(",
        "]": "[",
        ">": "<",
        "}": "{",
        "'": "'",
        '"': '"',
    }
    duckduckgo_search = f"https://duckduckgo.com/?t=ffab&q={url}&ia=web"

    for l in re.findall(r'(?P<url>[([<{"\']?(?:http|ftp)s?://\S+)', url):
        try:
            cur_url = l[1:-1] if l[0] == bracket_dict.get(l[-1]) else l
            result = urlparse(cur_url)
            if (all([result.scheme, result.netloc])
                    and "..." not in result
                    and cur_url not in url_set):
                url_set.add(cur_url)
                webbrowser.open(cur_url, new=2)
        except AttributeError:
            pass

    if not url_set:
        webbrowser.open(duckduckgo_search, new=2)


def main():
    """
    parse url and open url in system default browser
    """
    if not sys.stdin.isatty():
        open_url(sys.stdin.buffer.read().decode("utf-8", "ignore"))

if __name__ == "__main__":
    main()
