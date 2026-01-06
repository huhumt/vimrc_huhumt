#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from collections import OrderedDict
import subprocess
import argparse
import requests
import json
import sys
import re

ALL_DAY_EVENT_KEY = "All day event"
ALL_DAY_HOLIDAY_KEY = "All day holiday"
# https://stackoverflow.com/a/28938235
COLOUR_OFF = '\033[0m'
COLOUR_BG_BLUE = '\033[44m'
COLOUR_BG_YELLOW = '\033[43m'
COLOUR_GREEN = '\033[0;32m'
COLOUR_PURPLE_BOLD = '\033[1;35m'
COLOUR_LIGHT_GRAY = '\033[0;37m'
COLOUR_DARK_GRAY = '\033[2;37m'
HEADER_COLOUR = COLOUR_BG_BLUE + "{day}" + COLOUR_OFF + "{header}"
ALL_DAY_COLOUR = "    {colour}{name}" + COLOUR_OFF
NORMAL_EVENT_COLOUR = "    {event}"
DONE_EVENT_COLOUR = "    " + COLOUR_DARK_GRAY + "{event}" + COLOUR_OFF
IN_EVENT_COLOUR = (COLOUR_BG_YELLOW + "[*] {event}"
                   + COLOUR_GREEN + "{url}" + COLOUR_OFF)


def to_colour(day: str, header: str, event_dict: dict, colour_en: bool) -> str:
    now_h_m = datetime.now().time()
    colour_out_str = HEADER_COLOUR.format(day=day, header=header)

    for k, v in sorted(event_dict.items(), key=lambda v: int(
            re.sub(fr'{ALL_DAY_EVENT_KEY}|{ALL_DAY_HOLIDAY_KEY}|:',
                   r'0', v[1]["time"]))
    ):
        event_time = v.get("time")
        event_name = k[:40]

        if event_time == ALL_DAY_HOLIDAY_KEY:
            colour_str = ALL_DAY_COLOUR.format(
                colour=COLOUR_PURPLE_BOLD, name=f"{event_name} (All day)")
        elif event_time == ALL_DAY_EVENT_KEY:
            colour_str = ALL_DAY_COLOUR.format(
                colour=COLOUR_LIGHT_GRAY, name=f"{event_name} (Not holiday)")
        else:
            cur_event = f"{event_time}  {event_name}"
            reminder_c = datetime.strptime(event_time, "%H:%M")
            reminder_s = (reminder_c - timedelta(minutes=15)).time()
            reminder_e = (reminder_c + timedelta(minutes=5)).time()
            # colour disabled or event not start yet
            if (not colour_en) or (now_h_m < reminder_s):
                colour_str = NORMAL_EVENT_COLOUR.format(event=cur_event)
            elif now_h_m > reminder_e:  # colour enabled and event finished
                colour_str = DONE_EVENT_COLOUR.format(event=cur_event)
            else:  # colour enabled and now in the event
                if event_urls := (v["urls"][1:] or ""):
                    event_urls = "\n    ".join([""] + event_urls)
                colour_str = IN_EVENT_COLOUR.format(
                    event=cur_event, url=event_urls)
        colour_out_str += f"\n{colour_str}"
    return colour_out_str


def get_weather(loc: str) -> list | None:
    WWO_CODE = {
        "113": "Sunny",
        "116": "PartlyCloudy",
        "119": "Cloudy",
        "122": "VeryCloudy",
        "143": "Fog",
        "176": "LightShowers",
        "179": "LightSleetShowers",
        "182": "LightSleet",
        "185": "LightSleet",
        "200": "ThunderyShowers",
        "227": "LightSnow",
        "230": "HeavySnow",
        "248": "Fog",
        "260": "Fog",
        "263": "LightShowers",
        "266": "LightRain",
        "281": "LightSleet",
        "284": "LightSleet",
        "293": "LightRain",
        "296": "LightRain",
        "299": "HeavyShowers",
        "302": "HeavyRain",
        "305": "HeavyShowers",
        "308": "HeavyRain",
        "311": "LightSleet",
        "314": "LightSleet",
        "317": "LightSleet",
        "320": "LightSnow",
        "323": "LightSnowShowers",
        "326": "LightSnowShowers",
        "329": "HeavySnow",
        "332": "HeavySnow",
        "335": "HeavySnowShowers",
        "338": "HeavySnow",
        "350": "LightSleet",
        "353": "LightShowers",
        "356": "HeavyShowers",
        "359": "HeavyRain",
        "362": "LightSleetShowers",
        "365": "LightSleetShowers",
        "368": "LightSnowShowers",
        "371": "HeavySnowShowers",
        "374": "LightSleetShowers",
        "377": "LightSleet",
        "386": "ThunderyShowers",
        "389": "ThunderyHeavyRain",
        "392": "ThunderySnowShowers",
        "395": "HeavySnowShowers",
    }
    WEATHER_SYMBOL = {
        "Unknown": "✨",
        "Cloudy": "☁️",
        "Fog": "🌫",
        "HeavyRain": "🌧",
        "HeavyShowers": "🌧",
        "HeavySnow": "❄️",
        "HeavySnowShowers": "❄️",
        "LightRain": "🌦",
        "LightShowers": "🌦",
        "LightSleet": "🌧",
        "LightSleetShowers": "🌧",
        "LightSnow": "🌨",
        "LightSnowShowers": "🌨",
        "PartlyCloudy": "⛅️",
        "Sunny": "☀️",
        "ThunderyHeavyRain": "🌩",
        "ThunderyShowers": "⛈",
        "ThunderySnowShowers": "⛈",
        "VeryCloudy": "☁️",
    }
    try:
        json_resp = requests.get(f'http://wttr.in/{loc}?format=j1').json()
    except:
        return None
    return [
        f"{WEATHER_SYMBOL.get(WWO_CODE.get(i.get('weatherCode'), 'Unknown'))}"
        f" 🌡️ {i.get('FeelsLikeC')}°C 🌬️↓ {i.get('WindGustKmph')}km/h"
        for i in json_resp.get("weather")[0].get("hourly")
    ]


def hyperlinks_text(url: str, hyper_txt: str) -> str:
    hyperlinks = '\033]8;{};{}\033\\{}\033]8;;\033\\'
    return hyperlinks.format("", url, hyper_txt)


def search_and_short_url(urls: str, sep=" ") -> str:
    url_list = list()
    for href in re.compile(r'<a href="(?P<url>[^"]+)"').findall(urls):
        if (url := subprocess.run([
            'shorten_url', "--url-min-length=16", re.sub(r'[\s\|]', '', href)
        ], stdout=subprocess.PIPE).stdout.decode('utf-8').strip()) not in url_list:
            url_list.append(url)
    return sep.join(url_list)


def to_date(from_date: datetime, to_format: str = "%Y-%m-%d %a") -> str:
    return from_date.strftime(to_format)


def convert_date_format(date_str: str, from_date: datetime) -> str | None:
    # current only support these two formats
    #  "%a %b %d" is from 'gcalcli agenda'
    #  "%Y-%m-%d" is from 'gcalcli search'
    date_format_list = ["%a %b %d", "%Y-%m-%d"]
    for date_format in date_format_list:
        try:
            event_date = datetime.strptime(date_str.strip(), date_format)
        except ValueError:
            pass
        else:
            event_month = event_date.month
            event_day = event_date.day
            if event_month < from_date.month:
                event_datetime = from_date.replace(
                    year=from_date.year+1, month=event_month, day=event_day)
            else:
                event_datetime = from_date.replace(
                    month=event_month, day=event_day)
            return to_date(event_datetime)
    print(f"{date_str} is not support, can not continue")
    return None


def update_event_dict(date_log: str, today_date: datetime) -> OrderedDict:
    week_a = [(today_date+timedelta(days=i)).strftime("%a") for i in range(7)]
    month_b = [datetime.strptime(str(i).zfill(2), "%m").strftime("%b")
               for i in range(1, 13)]
    re_week_month = f"(?:{'|'.join(week_a)}) (?:{'|'.join(month_b)})"
    re_event = re.compile(
        fr'(?P<date>(?:{re_week_month} |\d+-\d+-)\d+)?'
        r'[ ]+(?P<time>\d{1,2}:\d{2})?[ ]*(?P<event>.+)'
        r'(?:\s+Calendar: (?P<calendar>.+))?'
        r'(?:\s+Link: (?P<link>.+))?'
        r'(?:\s+Hangout Link: (?P<hangout_link>.+))?'
        r'(?:\s+Location: (?P<location>.+))?'
        r'(?:\s+Description:[-+\s]+(?P<description>[^+]+)[-+]+)?'
    )

    cur_date = None
    cur_date_list = []
    event_dict = OrderedDict()

    for (
        date, time, event, calendar, link, hangout_link, location, description
    ) in re_event.findall(date_log):
        england_holiday = all([
            "United Kingdom" in calendar,
            "England" in location or "United Kingdom" in location
        ])
        event = re.sub(r' \(?regional holiday\)?', '',
                       event.strip(), flags=re.IGNORECASE)
        re_meetint_room = r'\(Meeting Room\)-Dale House-(.+?) \('
        if meeting_room := re.findall(re_meetint_room, location):
            event_attr = meeting_room[0].strip()
        elif location and not england_holiday:
            event_attr = location
        else:
            event_attr = None
            re_attr = r'\| (?P<attr>Public holiday|Observance)[ ]+\|'
            if attr := re.findall(re_attr, description):
                event = f"{attr[0]}: {event}"
                if attr[0] == "Public holiday":
                    event_attr = re.sub(
                        "holidays ", "", calendar, flags=re.IGNORECASE)

        event_lower = event.lower()
        # do not record event in "home" or "office"
        # do not record calendar named "Holiday Calendar"
        # do not record duplicated event
        # do not record if event in empty
        if any([
                event_lower in ("home", "office"),
                calendar == "Holiday Calendar",
                event_lower in cur_date_list,
                not event_lower
        ]):
            cur_event = None
        else:
            cur_event = {
                event + (f" ({event_attr})" if event_attr else ""): {
                    "time": time or (ALL_DAY_HOLIDAY_KEY
                                     if england_holiday else ALL_DAY_EVENT_KEY),
                    "urls": [link] + list(filter(None, [
                        hangout_link, search_and_short_url(description)]))
                }
            }
        if date and (date != cur_date):
            cur_date_list = [event_lower]
            cur_date = date
        else:
            cur_date_list.append(event_lower)

        if cur_date and cur_event:
            target_date = convert_date_format(cur_date, today_date)
            if target_date in event_dict:
                event_dict[target_date].update(cur_event)
            else:
                event_dict.update({target_date: cur_event})
    return event_dict


def remove_colour(input_str: str) -> str:
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", input_str).strip()


def update_from_file(event_dict, days_later: int) -> dict | None:
    re_holiday = r'(?P<name>.*holiday.*)\((?P<duration>\d+) day[s]*\)'
    for k, v in event_dict.items():
        for name, duration in re.findall(re_holiday, k, re.IGNORECASE):
            if (left_day := int(duration) - days_later) > 0:
                day_label = 'days' if left_day > 1 else 'day'
                return {f"{name} ({left_day} {day_label})": v}


def set_days_later(days_later: int, today_date: datetime) -> int:
    if days_later < 0:
        week_num = today_date.isoweekday()
        if (week_num > 5) or (week_num == 5 and today_date.hour > 16):
            # display next Monday's event from Friday's afternoon
            days_later = 8 - week_num
        else:
            # display tomorrow event after 17:00
            days_later = 1 if today_date.hour > 16 else 0
    return days_later


def main_out_agenda(event_dict, today_date, days_later, loc) -> None:
    event_date = today_date + timedelta(days=days_later)
    w_m_d = to_date(event_date)
    day_event_dict = event_dict.get(w_m_d) or {
        "Weekend" if event_date.isoweekday() > 5 else "No Event found": {
            "time": ALL_DAY_HOLIDAY_KEY
        }
    }
    header_list = ["", " (tomorrow)", f" ({days_later} days later)"]
    weather_idx = today_date.hour // 3
    if len(weather_list := event_dict.get("today_weather")) > weather_idx:
        header_list[0] = f" ({loc} {weather_list[weather_idx]})"
    header = header_list[days_later if days_later < len(header_list) else -1]
    print(to_colour(w_m_d, header, day_event_dict, days_later == 0))


def parse_arguments(filename: str):
    parser = argparse.ArgumentParser(
        description="Filter gcalcli agenda message")
    parser.add_argument(
        "--out-event-only", dest="out_event_only", action="store_true",
        help="Output today's event only")
    parser.add_argument(
        "--from-file", dest="from_file", action="store_true", default=False,
        help=f"Read agenda message from file {filename}")
    parser.add_argument(
        "--days-later", dest="days_later", type=int, default=-1,
        help="Display n days later agenda, must be within 30 days")
    parser.add_argument(
        "--weather-loc", dest="weather_loc", type=str, default="Manchester",
        help="Get weather information in location")
    return parser.parse_args()


if __name__ == "__main__":
    GCALCLI_FILENAME = "/tmp/gcalcli_agenda.json"
    args = parse_arguments(GCALCLI_FILENAME)
    today_date = datetime.today()
    today_key = to_date(today_date)
    days_later = set_days_later(args.days_later, today_date)

    try:
        with open(GCALCLI_FILENAME,
                  "r", encoding="utf-8", errors="ignore") as f:
            from_file_event_dict = json.load(f)
    except FileNotFoundError:
        from_file_event_dict = {}

    if args.from_file or sys.stdin.isatty():
        if from_file_event_dict:
            event_dict = from_file_event_dict
        else:
            exit()
    else:
        event_dict = update_event_dict(remove_colour(
            sys.stdin.buffer.read().decode('utf-8', 'ignore')), today_date)
        if "today_weather" in from_file_event_dict:
            weather_list = from_file_event_dict.get("today_weather")
        else:
            weather_list = get_weather(args.weather_loc)
        event_dict.update({"today_weather": weather_list})
        if from_file_today := from_file_event_dict.get(today_key):
            if file_holiday := update_from_file(from_file_today, days_later):
                event_dict.update({today_key: file_holiday})

    if args.out_event_only:
        for k, v in event_dict.get(today_key, {}).items():
            event_time = v.get("time")
            if event_time in [ALL_DAY_EVENT_KEY, ALL_DAY_HOLIDAY_KEY]:
                event_time = str()
            print(f"{event_time}    {k}")
    else:
        main_out_agenda(event_dict, today_date, days_later, args.weather_loc)
        if event_dict != from_file_event_dict:  # do not update if no changes
            with open(GCALCLI_FILENAME, "w", encoding="utf-8") as f:
                json.dump(event_dict, f, indent=4)
