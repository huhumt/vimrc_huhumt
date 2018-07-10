#!/usr/bin/env bash

# get current user's home directory
home_director=$(eval echo ~${SUDO_USER})

# use vim-plug to manage all vim plugins
curl -fLo $home_director/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
mkdir -p $home_director/.vim/plugged
# use self-configuration for vim and tmux
cp .vimrc .tmux.conf $home_director
# install necessary vim plugins automatic
vim -c "silent PlugClean" -c "silent PlugInstall" -c "qa"
hexmode_plugin_directory="$home_director/.vim/plugged/hexmode/plugin/hexmode.vim"
# replace the first xxd command to xxd -g1, print one byte instead of two per group
sed -i '0,/silent %!xxd/ s/silent %!xxd/silent %!xxd -g1/' $hexmode_plugin_directory

# use ustc mirror to speed up python-pip
mkdir -p $home_director/.config/pip
cp pip.conf $home_director/.config/pip/

usr_local_bin_path="/usr/local/bin"
# get system info of kernal and os in lowercase
kernel_name=$(echo "$(uname -s)" | tr '[:upper:]' '[:lower:]')
os_name=$(echo "$(uname -o)" | tr '[:upper:]' '[:lower:]')
if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
then
    # sed -i 's/'"\/usr\/bin\/ctags"'/'"\/mingw64\/bin\/ctags"'/g' ~/.vimrc
    # use local mirror to speedup download
    cp ./demo/mirrorlist* /etc/pacman.d/
    cp ./cn_update_package /usr/local/bin/
    cn_update_package
else
    usr_local_bin_path="$home_director/.local/bin"
    mkdir -p $usr_local_bin_path
    cp $home_director/.bash_profile $home_director/.bash_profile.bak
    echo "PATH=$PATH:$usr_local_bin_path" >> $home_director/.bash_profile
fi

cp ./code_backup.sh \
   ./ctags_cscope_update.sh \
   ./replace_line.py \
   ./code_format_clang.sh \
   $usr_local_bin_path
