#!/usr/bin/env bash

# get current user's home directory
home_directory=$(eval echo ~${SUDO_USER})

# use vim-plug to manage all vim plugins
curl -fLo $home_directory/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim


# delete old plugged and create new one
if [ -d "$home_directory/.vim/plugged" ]
then
    rm -fr $home_directory/.vim/plugged
fi
mkdir -p $home_directory/.vim/plugged

# use self-configuration for vim and tmux
cp .vimrc .tmux.conf $home_directory

# install necessary vim plugins automatic
vim -c "silent PlugInstall" -c "qa"

hexmode_plugin_directory="$home_directory/.vim/plugged/hexmode/plugin/hexmode.vim"
# replace the first xxd command to xxd -g1, print one byte instead of two per group
sed -i '0,/silent %!xxd/ s/silent %!xxd/silent %!xxd -g1/' $hexmode_plugin_directory

# use ustc mirror to speed up python-pip
mkdir -p $home_directory/.config/pip
cp pip.conf $home_directory/.config/pip/

usr_local_bin_path="/usr/local/bin"
# get system info of kernal and os in lowercase
kernel_name=$(echo "$(uname -s)" | tr '[:upper:]' '[:lower:]')
os_name=$(echo "$(uname -o)" | tr '[:upper:]' '[:lower:]')
if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
then
    # sed -i 's/'"\/usr\/bin\/ctags"'/'"\/mingw64\/bin\/ctags"'/g' ~/.vimrc
    # use local mirror to speedup download
    cp ./demo/mirrorlist* /etc/pacman.d/
    cp ./cn_update_package $usr_local_bin_path
    # DO NOT RUN UPDATE PACKAGE COMMAND HERE
    #cn_update_package
else
    old_string="trans_bin = \"$usr_local_bin_path\""
    usr_local_bin_path="$home_directory/.local/bin"
    new_string="trans_bin = \"$usr_local_bin_path\""
    echo $old_string $new_string $home_directory/.vimrc
    sed -i "s#$old_string#$new_string#g" "$home_directory/.vimrc"
    mkdir -p $usr_local_bin_path
    # DO NOT OVERWRITE PREVIOUS BAK FILE
    if [ -f $home_directory/.bash_profile.bak ]
    then
        cp $home_directory/.bash_profile.bak $home_directory/.bash_profile
    else
        cp $home_directory/.bash_profile $home_directory/.bash_profile.bak
    fi
    echo "PATH=$PATH:$usr_local_bin_path" >> $home_directory/.bash_profile
fi

# nc: if file exist, do not download
# nv: do not print that much log
# P: re-direct to given directory
wget -nc -nv -P $usr_local_bin_path/ git.io/trans

cp ./code_backup.sh \
   ./ctags_cscope_update.sh \
   ./string_replace.sh \
   ./code_format_clang.sh \
   $usr_local_bin_path

chmod 755 $usr_local_bin_path/code_backup.sh \
          $usr_local_bin_path/ctags_cscope_update.sh \
          $usr_local_bin_path/string_replace.sh \
          $usr_local_bin_path/code_format_clang.sh \
          $usr_local_bin_path/trans

if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
then
    cn_update_package
fi
