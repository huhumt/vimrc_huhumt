#!/bin/bash

check_dependencies() {
    local deps_app_list=(vim curl patch ag ctags cscope astyle python3)
    for deps_app in "${deps_app_list[@]}"
    do
        if ! type -p "$deps_app" > /dev/null
        then
            printf "Make sure you have successfully installed $deps_app\n"
            exit
        fi
    done
}

config_vim() {
    # install npm to .local
    curl -sL install-node.vercel.app/lts | bash -s -- --prefix=.local

    # use vim-plug to manage all vim plugins
    curl -fLo "$home_directory/.vim/autoload/plug.vim" --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

    # use self-configuration for vim
    curl -fLo "$home_directory/.vimrc" \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/dotfiles/.vimrc

    # configuration for vim-coc
    curl -fLo "$home_directory/.vim/coc-settings.json" \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/dotfiles/.vim/coc-settings.json

    rm -fr "$home_directory/.vim/plugged"
    mkdir -p "$home_directory/.vim/plugged"

    # install necessary vim plugins automatic
    echo "Installing vim plugins..."
    vim -c "silent PlugInstall" -c "qa"

    vim_mark_plugin_dir="$home_directory/.vim/plugged/Mark"
    sed -i 's/hi MarkWord1  ctermbg=Cyan    /hi MarkWord1  ctermbg=LightRed/' \
        "$vim_mark_plugin_dir/plugin/mark.vim"

    minibufexpl_plugin_dir="$home_directory/.vim/plugged/minibufexpl.vim"
    sed -i 's/call <SID>Buf/silent! call <SID>Buf/' \
        "$minibufexpl_plugin_dir/plugin/minibufexpl.vim"

    sed -i "s#let g:trans_bin.*#let g:trans_bin = \"$local_bin_path\"#" \
        "$home_directory/.vimrc"

    ctrlsf_plugin_dir="$home_directory/.vim/plugged/ctrlsf.vim"
    sed -i -E 's#(search hit.+)(continuing at.+)#\1\2\n            return#' \
        "$ctrlsf_plugin_dir/autoload/ctrlsf.vim"
    sed -i 's#let out .= a:line.content#let out .= trim(a:line.content)#' \
        "$ctrlsf_plugin_dir/autoload/ctrlsf/view.vim"

    plug_dir="$home_directory/.vim/plugged/"
    curl -fLo "$plug_dir/gutentags.patch" \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/script/gutentags.patch
    # patch file generated by diff -ruN old new > diff.patch file
    cd "$plug_dir" && patch -s -p0 < gutentags.patch && rm gutentags.patch
}

config_dotfile() {
    curl -fLo "$home_directory/.tmux.conf" \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/dotfiles/.tmux.conf
    curl -fLo "$home_directory/.clang-format" \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/dotfiles/.clang-format
    curl -fLo "$home_directory/.astylerc" \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/dotfiles/.astylerc
}

config_script() {
    # nc: if file exist, do not download
    # nv: do not print that much log
    # P: re-direct to given directory
    # wget -nc -nv -P $local_bin_path/ git.io/trans
    curl -fLo "$local_bin_path/trans" git.io/trans

    curl -fLo "$local_bin_path/code_backup.sh" \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/script/code_backup.sh
    curl -fLo "$local_bin_path/string_replace.sh" \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/script/string_replace.sh
    curl -fLo "$local_bin_path/python_replace.py" \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/script/python_replace.py
    curl -fLo "$local_bin_path/code_format_clang.sh" \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/script/code_format_clang.sh
    curl -fLo "$local_bin_path/tmux_panels.sh" \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/script/tmux_panels.sh

    chmod 755 "$local_bin_path"/*.sh \
              "$local_bin_path/trans"
}

config_mingw() {
    kernel_name=$(uname -s | tr '[:upper:]' '[:lower:]')
    os_name=$(uname -o | tr '[:upper:]' '[:lower:]')

    if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
    then
        curl -fLo /usr/share/mintty/themes/base16-eighties-mod \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/demo/base16-eighties-mod
        curl -fLo "$home_directory/.minttyrc" \
            https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/dotfiles/.minttyrc
        echo "/usr/local/bin"
    else
        echo "$home_directory/.local/bin"
    fi
}

# get current user's home directory
home_directory=$(eval echo "~${SUDO_USER}")
check_dependencies
config_dotfile
local_bin_path=$(config_mingw)
mkdir -p "$local_bin_path"
config_script
config_vim
echo 'Done, remember to add export PATH=${PATH}:$local_bin_path to .bashrc'
