#!/usr/bin/env bash


WEECHAT_HOME_DIR="$HOME/.config/weechat"
WEECHAT_CMD_ARRAY=(
    "/set script.scripts.download_enabled on"
    "/script install pv_info.pl colorize_nicks.py go.py"
    "/set weechat.color.nicklist_away .gray"
    "/set weechat.look.paste_auto_add_newline off"
    "/set weechat.bar.status.items [time],buffer_number+: +buffer_name,[lag],completion,scroll,[spell_suggest]"
    "/key bind ctrl-J /bar scroll nicklist * +50%"
    "/key bind ctrl-K /bar scroll nicklist * -50%"
    "/set spell.check.default_dict en_GB"
    "/set spell.check.enabled on"
    "/set spell.check.suggestions 3"
    "/set spell.color.suggestion *green"
)

init_weechat()
{
    init_command=$( IFS=';'; echo "${WEECHAT_CMD_ARRAY[*]}" )
    weechat -d "$WEECHAT_HOME_DIR" -r "$init_command"
}

init_weechat
