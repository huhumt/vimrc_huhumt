#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from urllib.parse import urlparse
import webbrowser
import sys


def validate_url(url):
    """
    validate if it's a real url, from https://stackoverflow.com/a/38020041
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and "..." not in result
    except AttributeError:
        return False


def open_url(url):
    """
    open url in default browser
    """
    webbrowser.open(url, new=2)


def main():
    """
    parse url and open url in system default browser
    """
    if sys.stdin.isatty():
        return 0

    url_list = []
    for url in sys.stdin.read().split():
        if validate_url(url) and url not in url_list:
            url_list.append(url)
            open_url(url)
    return 0


if __name__ == "__main__":
    main()
