import argparse
import ast
import base64
import html
import re
import socket
import string
import urllib.request
from collections import OrderedDict

SCRIPT_NAME = "urlserver"
SCRIPT_AUTHOR = "Sébastien Helleu <flashcode@flashtux.org>"
SCRIPT_VERSION = "2.6"
SCRIPT_LICENSE = "GPL3"
SCRIPT_DESC = "Shorten URLs with own HTTP server"
SCRIPT_FILENAME = "/tmp/shorten_url.list"

SCRIPT_COMMAND = "urlserver"
SCRIPT_BUFFER = "urlserver"

urlserver = {
    "socket": None,
    "urls": {},
    "number": 0,
}

# script options
urlserver_settings_default = {
    # HTTP server settings
    "http_autostart": ("on", "start the built-in HTTP server automatically)"),
    "http_scheme_display": ("http", "display this scheme in shortened URLs"),
    "http_hostname": (
        "localhost",
        "force hostname/IP in bind of socket "
        "(empty value = auto-detect current hostname)",
    ),
    "http_hostname_display": ("", "display this hostname in shortened URLs"),
    "http_port": (
        "8002",
        "force port for listening (empty value = find a random free port)",
    ),
    "http_port_display": (
        "",
        "display this port in shortened URLs. Useful if you forward "
        "a different external port to the internal port",
    ),
    "http_allowed_ips": (
        "",
        "regex for IPs allowed to use server "
        r'(example: "^(123\.45\.67\.89|192\.160\..*)$")',
    ),
    "http_auth": (
        "",
        'login and password (format: "login:password") required to access to '
        "page with list of URLs (note: content is evaluated, see /help eval)",
    ),
    "http_auth_redirect": (
        "on",
        'require the login/password (if option "http_auth" is set) for URLs '
        "redirections",
    ),
    "http_url_prefix": (
        "",
        "prefix to add in URLs to prevent external people to scan your URLs "
        '(for example: prefix "xx" will give URL: http://host.com:1234/xx/8)',
    ),
    "http_bg_color": ("#f4f4f4", "background color for HTML page"),
    "http_fg_color": ("#000", "foreground color for HTML page"),
    "http_css_url": (
        "",
        "URL of external Cascading Style Sheet to add (BE CAREFUL: the HTTP "
        "referer will be sent to site hosting CSS file!) (empty value = use "
        "default embedded CSS)",
    ),
    "http_embed_image": (
        "off",
        "embed images in HTML page (BE CAREFUL: the HTTP referer will be sent "
        "to site hosting image!)",
    ),
    "http_embed_youtube": (
        "off",
        "embed youtube videos in HTML page (BE CAREFUL: the HTTP referer "
        "will be sent to youtube!)",
    ),
    "http_embed_youtube_size": (
        "480*350",
        'size for embedded youtube video, format is "xxx*yyy"',
    ),
    "http_prefix_suffix": (
        " ",
        "suffix displayed between prefix and message in HTML page",
    ),
    "http_title": (
        "Shorten URLs service on local machine",
        "title of the HTML page",
    ),
    "http_time_format": ("%d/%m/%y %H:%M:%S", "time format in the HTML page"),
    "http_open_in_new_page": ("on", "open links in new pages/tabs"),
    "debug": ("off", "print some debug messages"),
}
urlserver_settings = {k: v[0] for k, v in urlserver_settings_default.items()}


def base62_encode(number):
    """Encode a number in base62 (all digits + a-z + A-Z)."""
    base62chars = string.digits + string.ascii_letters
    l = []
    while number > 0:
        remainder = number % 62
        number = number // 62
        l.insert(0, base62chars[remainder])
    return "".join(l) or "0"


def base62_decode(str_value):
    """Decode a base62 string (all digits + a-z + A-Z) to a number."""
    base62chars = string.digits + string.ascii_letters
    return sum(
        [
            base62chars.index(char) * (62 ** (len(str_value) - index - 1))
            for index, char in enumerate(str_value)
        ]
    )


def base64_decode(s):
    return base64.b64decode(s.encode("utf-8"))


def urlserver_get_base_url():
    """
    Return url with port number if != default port for the protocol,
    including prefix path.
    """
    scheme = urlserver_settings["http_scheme_display"]
    hostname = (
        urlserver_settings["http_hostname_display"]
        or urlserver_settings["http_hostname"]
        or socket.getfqdn()
    )

    # If the built-in HTTP server isn't running, default to port from settings
    port = urlserver_settings["http_port"]
    if len(urlserver_settings["http_port_display"]) > 0:
        port = urlserver_settings["http_port_display"]
    elif urlserver["socket"]:
        port = urlserver["socket"].getsockname()[1]

    # Don't add :port if the port matches the default port for the protocol
    prefixed_port = ":%s" % port

    if scheme == "http" and prefixed_port == ":80":
        prefixed_port = ""
    elif scheme == "https" and prefixed_port == ":443":
        prefixed_port = ""

    prefix = ""
    if urlserver_settings["http_url_prefix"]:
        prefix = "%s/" % urlserver_settings["http_url_prefix"]

    return "%s://%s%s/%s" % (scheme, hostname, prefixed_port, prefix)


def urlserver_server_reply(
    conn, code, extra_header, message, mimetype="text/html"
):
    """Send a HTTP reply to client."""
    if extra_header:
        extra_header += "\r\n"
    s = "HTTP/1.1 %s\r\n%sContent-Type: %s\r\nContent-Length: %d\r\n\r\n" % (
        code,
        extra_header,
        mimetype,
        len(message),
    )
    msg = None
    if type(message) is bytes:
        msg = s.encode("utf-8") + message
    else:
        msg = s.encode("utf-8") + message.encode("utf-8")
    if urlserver_settings["debug"] == "on":
        print("urlserver: sending %d bytes" % len(msg))
    conn.sendall(msg)


def urlserver_server_reply_auth_required(conn):
    """Reply a 401 (authorization required)."""
    urlserver_server_reply(
        conn,
        "401 Authorization required",
        f'WWW-Authenticate: Basic realm="{SCRIPT_NAME}"',
        "",
    )


def urlserver_server_reply_404_not_found(conn):
    """Reply a 404 (not found)."""
    urlserver_server_reply(
        conn,
        "404 Not found",
        "",
        "<html>\n"
        "<head><title>Page not found</title></head>\n"
        "<body><h1>Page not found</h1></body>\n"
        "</html>",
    )


def urlserver_server_favicon():
    """Return favicon for HTML page."""
    s = (
        "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+g"
        "vaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH3QUTDCsWY4ZjDAAAAC5p"
        "VFh0Q29tbWVudAAAAAAAQnkgRmxhc2hDb2RlIC0gaHR0cDovL3dlZWNoYXQub3Jn"
        "L3IAZSEAAAZJSURBVFjD7ZZdbFTHFcf/M/fueteLP8A2/oSExsVASECCIIgctaIG"
        "oURVmzyEipJWSYUsFRGliJS3qEkElVqpapWHSrxEqVopbaVGrRKJtiRYlps6ttMH"
        "YmwIKcaO7cXE3vXdj/s1M+f04e6u1vVWfaxUMVejO/fO3HN+5z/nzgxwv9wv/+Mi"
        "/lPHxq3NyM6tlh9jR14/3BBvqqsPApXwC2FMhdoOfRVTobZVoONambhIWgm2kSBb"
        "JEgiYQQljOCEBie14IQB1Wk2CcWc1NrkeMJ53a7l/Ge513C28RUAwJMXjz7X0rvp"
        "64iL3UZwtwE3GCKhmKDBMEzQTFBM0MZAkUFoTNQuV4ruoSGw0SAi0Gf522Yy/8ua"
        "AGcbX0HnrvYtT7068KdUZ8MeRUboslEiKDKAiSoTIAxDcCSngICEKF2otMrPEgKC"
        "mJEORuHohZoAOwd6O77y/ccvN3Y37Aq1gRSAEACEgJRlBxJSMKQBJDiqzBBEADOE"
        "YUAzQxFBE7M2kUTakPB1wNP59wH4NQEOfXvfWy1bN+5SWlfYpRCwbIniF66Xnly6"
        "ExTDTBgoX4Xa1b52w0AXla9dY8gjIp+YfGPYq7p7ZMjXRD75xqebxSkAvA7g0Il9"
        "Rx7Y23204lwKCI7EzN7OLP7x9Ls/Va76PYAMIKgOD1Hnw49x994D6Orfh9+dfUIL"
        "EeX20xcvx1Tg2ssz16xceibu5u4lQi+fAtHMIj7UALAO4OCze85YlgTBAkkBJgCC"
        "QSCMX5p4W7nq0gu/mQvSkyPnN7R2dwkh6yFkSgiZElI0Pnb8/M8B/AFATNrx0aZN"
        "HX3NXb110rJsacUhpMBvf9D/DIB31gE8de5wnQnNB3/71YTt5nzXzft5z/FzRcdz"
        "jDLu3Nj8+wDcyxe+9cjRc29esOJJAFz53s+tBOnp0U4AOPTd1x5vbN+6U1qxZOWf"
        "lxbmrw3Nupm7d8rv1gD8+Y1JowN1KdXW8NaW3f1o375DdGxvlU1dPfLXg7vvlcft"
        "GDj5op1IgcmsUa+wspBe+GR4BADaHto7IKSVXKsvY+aj9/4OYLImwFdPX/xR+5f3"
        "9QMiLgTqAZGEEPWh61iJDRuf9QvZEQCpzp0HT0ZzU7WiCYH01Og4gNknTv0kUZdq"
        "OiaFBa5SyM3e83JLsx8AULUAmtu27TmfbGyxmbnKsMTSzbFbKiiGAHDwuVdPJBra"
        "EmSoHBQYABNh7O0LfwGwOvePob6eR5/cH3gGoFI/MzKfz99NT304Ug1eAdjzjZdO"
        "1Td32TpQiPwzmAAixYuTYx8bFU4BkG1f6j/u5TRADOaSd2EjPTV0C4xxAGjvGxg0"
        "KgXl6SpAxuL18XEA87UAxJZHnz5dzAQgKiMDzEDoOv78J0NXABR3HTu3Hdz8iJdV"
        "4HL0xJCWxLX3fnEVwA0AaNi8/3tuJgQxlcZECkxfeeOvAArrAHr7Tx2RsY5ud1VV"
        "OWcwS6zMTc866U8/AsB1iS0HQy+2Wfk6UokAFgLFzI1cdn5yCEDw4P7BZ0CtjcVV"
        "VVIJgLCwujBxR3nO2JrfpgQgWx742jd9R9tcFTkzQ4gYbg1fGgIwGw3fdDIoSBAZ"
        "gLmUhwJLn45OM6lhAGjqPPIdd1WBKepnMAQkZj9+cxjAzX9fd+xtB15qJtN82HMM"
        "eE30Atpf0sszw1cB5AF0W7FtA5HxaBwRQMbVy7evjgGwW7YdP2Z06wE3G+URU5QA"
        "oX83WF0YvgIgWAcQuuFuUo19nlOKqgqAqd7e3Du4HyK2ktzw4POhmwKTrkTGBDBZ"
        "dkffj8907oifYQZUkRCyiRQoTWNheeIWg0dq7Tu2tHqOhm4CZHQl88v0zMCmnlMv"
        "M9PLTICbDSqZXz0GLEAUVpKSq/vJcHHl+iiYPq8JQGZjq+soMFFJ2pKBUuYylRKO"
        "q+DK87/GIYNJRFNTbhPDmFzgF24MAdA1AfxC7h0mf5DZirJ6jaPICJUyntgApECs"
        "NEgpIq3A2mcmn8l4zMUsmVyWKbvClFkmk/7CmM8W2Vy/Gh1XeD1A4ARXtH/tBDj1"
        "Q+YNfeBYnCgMwfkiUT7P5GSZcsvMzhJT4R4zrQBmGawyxF6GzbJD5p8OkHcB+KVl"
        "NixFTNX7wH87lMYB9ABoKe8tAFYBFKsM8/1z/P3yf1f+BRr3PuAGLe5KAAAAAElF"
        "TkSuQmCC"
    )
    return base64_decode(s)


def urlserver_server_reply_list(conn, sort="-time"):
    """Send list of URLs as HTML page to client."""
    content = '<div class="urls">\n<table id="urls_table">\n'
    sortkey = {"-": ("", "&uarr;"), "+": ("-", "&darr;")}
    content += "  <tr>"
    for column, defaultsort in (("time", "-"), ("number", "-")):
        if sort[1:] == column:
            content += (
                '<th class="sortable sorted_by %s_header">'
                '<a href="sort=%s%s">%s</a> %s</th>'
                % (
                    column,
                    sortkey[sort[0]][0],
                    column,
                    column.capitalize(),
                    sortkey[sort[0]][1],
                )
            )
        else:
            content += (
                '<th class="sortable %s_header">'
                '<a class="sort_link" href="sort=%s%s">%s</a></th>'
                % (column, defaultsort, column, column.capitalize())
            )

    content += (
        '<th class="unsortable message_header">Short URLs</th>'
        '<th class="unsortable message_header">Convention URLs message</th>'
        "</tr>\n"
    )

    for key, item in urlserver["urls"].items():
        content += "  <tr>"
        short_url = item[1]
        short_url_e = "\x01\x02\x03\x04"
        url = item[2]
        url_e = "\x05\x06\x07\x08"
        message = html.escape(
            f"Shorten url script:\t convert {url_e} to {short_url_e}"
        ).split("\t", 1)
        message[0] = '<span class="prefix">%s</span>' % message[0]
        message[1] = '<span class="message">%s</span>' % message[1]

        strjoin = (
            '<span class="prefix_suffix"> %s </span>'
            % urlserver_settings["http_prefix_suffix"].replace(" ", "&nbsp;")
        )

        if urlserver_settings["http_open_in_new_page"] == "on":
            target = "_blank"
        else:
            target = "_self"

        href = (
            '</span><a class="%s" href="%s" title="%s" target="%s">'
            '%s</a><span class="message">'
        )
        short_url_href = href % (
            "short_url",
            url,
            "Short url for link",
            target,
            short_url,
        )

        if len(url) > len(short_url) * 5:
            display_url = (
                f"{url[: len(short_url) * 3]}...{url[-len(short_url) :]}"
            )
        else:
            display_url = url

        url_href = href % (
            "url",
            short_url,
            "Url for link",
            target,
            display_url,
        )
        message = (
            strjoin.join(message)
            .replace(short_url_e, short_url_href)
            .replace(url_e, url_href)
        )

        obj = ""
        if urlserver_settings[
            "http_embed_image"
        ] == "on" and url.lower().endswith(
            (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg")
        ):
            obj = (
                '<div class="obj"><img src="%s" title="%s" alt="%s">'
                "</div>" % (url, url, url)
            )
        elif (
            urlserver_settings["http_embed_youtube"] == "on"
            and "youtube.com/" in url
        ):
            m = re.search(r"v=([\w\d]+)", url)
            if m:
                yid = m.group(1)
                try:
                    size = urlserver_settings["http_embed_youtube_size"].split(
                        "*"
                    )
                    width = int(size[0])
                    height = int(size[1])
                except:
                    width = 480
                    height = 350
                obj = (
                    '<div class="obj youtube">'
                    '<iframe id="%s" type="text/html" width="%d" '
                    'height="%d" '
                    'src="https://www.youtube.com/embed/%s?enablejsapi=1">'
                    "</iframe></div>" % (yid, width, height, yid)
                )

        content += (
            '<td class="timestamp">%s</td>'
            '<td class="number" style="text-align:center">%s</td>'
            '<td class="short_url">%s</td>'
            '<td class="message">' % (key, item[0], item[1])
        )
        content += "%s%s</td></tr>\n" % (message, obj)
    content += "</table>"

    if len(urlserver_settings["http_css_url"]) > 0:
        css = (
            '<link rel="stylesheet" type="text/css" href="%s" />'
            % urlserver_settings["http_css_url"]
        )
    else:
        css = (
            '<style type="text/css" media="screen">'
            "<!--\n"
            "  html { font-family: Verdana, Arial, Helvetica; "
            "font-size: 12px; background: %s; color: %s }\n"
            "  .urls table { border-collapse: collapse }\n"
            "  .urls table td,th { border: solid 1px #cccccc; "
            "padding: 4px; font-size: 12px }\n"
            "  .timestamp,.number,.short_url{ white-space: nowrap }\n"
            "  .sorted_by { font-style: italic; }\n"
            "  .obj { margin-top: 1em }\n"
            "-->"
            "</style>\n"
            % (
                urlserver_settings["http_bg_color"],
                urlserver_settings["http_fg_color"],
            )
        )

    html_code = (
        "<html>\n"
        "<head>\n"
        "<title>%s</title>\n"
        '<meta http-equiv="content-type" content="text/html; '
        'charset=utf-8" />\n'
        "%s\n"
        '<base href="%s" />\n'
        '<link rel="icon" type="image/png" href="favicon.png" />\n'
        "</head>\n"
        "<body>\n%s\n</body>\n"
        "</html>"
        % (
            urlserver_settings["http_title"],
            css,
            urlserver_get_base_url(),
            content,
        )
    )
    urlserver_server_reply(conn, "200 OK", "", html_code)


def urlserver_check_auth(data):
    """Check user/password to access a page/URL."""
    global urlserver_settings
    if not urlserver_settings["http_auth"]:
        return True
    http_auth = eval(urlserver_settings["http_auth"], {}, {})
    auth = re.search(
        r"^Authorization: Basic (\S+)$", data, re.MULTILINE | re.IGNORECASE
    )
    if auth and (base64_decode(auth.group(1)).decode("utf-8") == http_auth):
        return True
    return False


def urlserver_server_fd_cb():
    """Callback for server socket."""
    if not urlserver["socket"]:
        return False

    conn, addr = urlserver["socket"].accept()
    if urlserver_settings["debug"] == "on":
        print("urlserver: connection from %s" % str(addr))

    if urlserver_settings["http_allowed_ips"] and not re.match(
        urlserver_settings["http_allowed_ips"], addr[0]
    ):
        if urlserver_settings["debug"] == "on":
            print("urlserver: IP not allowed")
        conn.close()
        return False

    try:
        conn.settimeout(0.3)
        data = conn.recv(4096).decode("utf-8", "ignore")
        data = data.replace("\r\n", "\n")
    except:
        return True

    referer = re.search("^Referer:", data, re.MULTILINE | re.IGNORECASE)
    m = re.search("^GET /(.*) HTTP/.*$", data, re.MULTILINE)
    if not m:
        urlserver_server_reply_404_not_found(conn)
        return True

    url = m.group(1)
    if urlserver_settings["debug"] == "on":
        print(f"urlserver: {m.group(0)} {url}")

    if url.lower() in ("stop", "shutdown", "close"):
        return False

    if "favicon." in url:
        urlserver_server_reply(
            conn,
            "200 OK",
            "",
            urlserver_server_favicon(),
            mimetype="image/x-icon",
        )
        return True

    if urlserver_settings["http_url_prefix"]:
        if url.startswith(urlserver_settings["http_url_prefix"]):
            url = url[len(urlserver_settings["http_url_prefix"]) :]
            if url.startswith("/"):
                url = url[1:]
        else:
            if urlserver_settings["debug"] == "on":
                print("urlserver: prefix missing")
            return True

    sort = url[5:] if url.startswith("sort=") else "-time"
    urlserver_read_urls(sort)

    if not url or url.startswith("sort="):
        # page with list of urls
        if urlserver_check_auth(data):
            urlserver_server_reply_list(conn, sort)
        else:
            urlserver_server_reply_auth_required(conn)
        return True

    # short url, read base62 key and redirect to page
    try:
        number = base62_decode(url)
    except:
        urlserver_server_reply_404_not_found(conn)
    else:
        long_url = urlserver_search_url(number)
        authok = urlserver_settings[
            "http_auth_redirect"
        ] != "on" or urlserver_check_auth(data)
        if authok and long_url:
            # if we have a referer in request, use meta for
            # redirection (so that referer is not sent)
            # otherwise, we can make redirection with HTTP 302
            if referer:
                urlserver_server_reply(
                    conn,
                    "200 OK",
                    "",
                    '<meta name="referrer" content="never">\n'
                    '<meta http-equiv="refresh" content="0; '
                    'url=%s">' % long_url,
                )
            else:
                conn.sendall(
                    "HTTP/1.1 302\r\nLocation: {}\r\n\r\n".format(
                        long_url
                    ).encode("utf-8")
                )
        else:
            urlserver_server_reply_auth_required(conn)

    conn.close()
    return True


def urlserver_server_start():
    """Start mini HTTP server."""
    global urlserver
    hostname = urlserver_settings["http_hostname"] or socket.getfqdn()
    port = int(urlserver_settings["http_port"])
    urlserver["socket"] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    urlserver["socket"].setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        if urlserver["socket"].connect_ex((hostname, port)):
            urlserver["socket"].bind((hostname, port))
            urlserver["socket"].listen(5)
            print(f"URL server listening on {hostname}:{port}")
        else:
            print(f"URL server already in listening on {hostname}:{port}")
            exit()
    except Exception as e:
        print(f"Bind error: {e}, server not running")


def urlserver_server_stop(stop_url):
    """Stop mini HTTP server."""
    global urlserver
    if urlserver["socket"]:
        print("Stop server by closing socket")
        urlserver["socket"].close()
        urlserver["socket"] = None
    else:
        print(f"Stop server by {stop_url}")
        try:
            urllib.request.urlopen(stop_url)
        except:
            pass


def urlserver_read_urls(sort="-time"):
    """Read file with URLs."""
    global urlserver
    filename = SCRIPT_FILENAME
    try:
        urls_dict = ast.literal_eval(open(filename, "r").read())
        if "time" not in sort:  # sort by timestamp, default format
            urls_dict = sorted(urls_dict.items(), key=lambda url: url[1][0])
        urlserver["urls"] = OrderedDict(urls_dict)
        if sort.startswith("-"):
            urlserver["urls"] = OrderedDict(
                reversed(list(urlserver["urls"].items()))
            )
        urlserver["number"] = list(urlserver["urls"].values())[-1][0]
    except:
        print(f"urlserver: error reading file {filename}")


def urlserver_search_url(number):
    for val in urlserver["urls"].values():
        if val[0] == number:
            return val[2]
    return None


if __name__ == "__main__":
    target_url = "http://%s:%s" % (
        urlserver_settings["http_hostname"],
        urlserver_settings["http_port"],
    )
    parser = argparse.ArgumentParser(
        description=f"Start urlserver at {target_url}"
    )
    parser.add_argument(
        "--stop",
        dest="stop",
        action="store_true",
        help=f"stop urlserver {target_url}",
    )
    parser.add_argument(
        "--restart",
        dest="restart",
        action="store_true",
        help=f"restart urlserver {target_url}",
    )

    stop_url = f"{target_url}/stop"
    args = parser.parse_args()
    if args.stop or args.restart:
        urlserver_server_stop(stop_url)
    if args.restart or not args.stop:
        # start mini HTTP server
        urlserver_server_start()
        try:
            on_listening = True
            while on_listening:
                on_listening = urlserver_server_fd_cb()
        except KeyboardInterrupt:
            print("Terminated by keyboard interrupt, bye")
        finally:
            urlserver_server_stop(stop_url)
