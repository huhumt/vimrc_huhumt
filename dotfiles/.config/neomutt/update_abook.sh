#!/bin/sh

MESSAGE=$(cat)
python3 ~/.config/neomutt/update_abook_from_mail.py "${MESSAGE}"
