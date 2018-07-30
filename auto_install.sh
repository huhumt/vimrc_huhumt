#!/usr/bin/env bash

# get current user's home directory
home_directory=$(eval echo ~${SUDO_USER})

# use vim-plug to manage all vim plugins
curl -fLo $home_directory/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

# use self-configuration for vim and tmux
# cp .vimrc .tmux.conf .clang-format $home_directory
curl -fLo $home_directory/.vimrc \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/.vimrc
curl -fLo $home_directory/.tmux.conf \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/.tmux.conf
curl -fLo $home_directory/.clang-format \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/.clang-format

# delete old plugged and create new one
if [ -d "$home_directory/.vim/plugged" ]
then
    rm -fr $home_directory/.vim/plugged
fi
mkdir -p $home_directory/.vim/plugged

# install necessary vim plugins automatic
vim -c "silent PlugInstall" -c "qa"

hexmode_plugin_directory="$home_directory/.vim/plugged/hexmode/plugin/hexmode.vim"
# replace the first xxd command to xxd -g1, print one byte instead of two per group
sed -i '0,/silent %!xxd/ s/silent %!xxd/silent %!xxd -g1/' $hexmode_plugin_directory

# use ustc mirror to speed up python-pip
# mkdir -p $home_directory/.config/pip
# cp pip.conf $home_directory/.config/pip/
curl -fLo $home_directory/.config/pip/pip.conf --create-dirs \
        https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/.pip.conf

usr_local_bin_path="/usr/local/bin"
# get system info of kernal and os in lowercase
kernel_name=$(echo "$(uname -s)" | tr '[:upper:]' '[:lower:]')
os_name=$(echo "$(uname -o)" | tr '[:upper:]' '[:lower:]')
if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
then
    # sed -i 's/'"\/usr\/bin\/ctags"'/'"\/mingw64\/bin\/ctags"'/g' ~/.vimrc
    # use local mirror to speedup download
    # cp ./demo/mirrorlist* /etc/pacman.d/
    # cp ./cn_update_package $usr_local_bin_path
    # add a good color configuration for mintty
    # cp ./base16-eighties-mod /usr/share/mintty/themes/
    # DO NOT RUN UPDATE PACKAGE COMMAND HERE
    #cn_update_package
    curl -fLo $usr_local_bin_path/cn_update_package.sh \
            https://github.com/huhumt/vimrc_huhumt/blob/master/cn_update_package.sh
    curl -fLo /usr/share/mintty/themes/base16-eighties-mod \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/base16-eighties-mod
    mintty -c base16-eighties-mod
else
    old_string="trans_bin = \"$usr_local_bin_path\""
    usr_local_bin_path="$home_directory/.local/bin"
    new_string="trans_bin = \"$usr_local_bin_path\""
    echo $old_string $new_string $home_directory/.vimrc
    sed -i "s#$old_string#$new_string#g" "$home_directory/.vimrc"
    mkdir -p $usr_local_bin_path
    if [ -f $home_directory/.bash_profile ]
    then
        # DO NOT OVERWRITE PREVIOUS BAK FILE
        if [ -f $home_directory/.bash_profile.bak ]
        then
            cp $home_directory/.bash_profile.bak $home_directory/.bash_profile
        else
            cp $home_directory/.bash_profile $home_directory/.bash_profile.bak
        fi
    fi
    echo "export PATH=\${PATH}:$usr_local_bin_path" >> $home_directory/.bash_profile
fi

# nc: if file exist, do not download
# nv: do not print that much log
# P: re-direct to given directory
wget -nc -nv -P $usr_local_bin_path/ git.io/trans

# cp ./code_backup.sh \
#    ./ctags_cscope_update.sh \
#    ./string_replace.sh \
#    ./code_format_clang.sh \
#    $usr_local_bin_path
curl -fLo $usr_local_bin_path/code_backup.sh \
        https://github.com/huhumt/vimrc_huhumt/blob/master/code_backup.sh
curl -fLo $usr_local_bin_path/ctags_cscope_update.sh \
        https://github.com/huhumt/vimrc_huhumt/blob/master/ctags_cscope_update.sh
curl -fLo $usr_local_bin_path/string_replace.sh \
        https://github.com/huhumt/vimrc_huhumt/blob/master/string_replace.sh
curl -fLo $usr_local_bin_path/code_format_clang.sh \
        https://github.com/huhumt/vimrc_huhumt/blob/master/code_format_clang.sh

chmod 755 $usr_local_bin_path/code_backup.sh \
          $usr_local_bin_path/ctags_cscope_update.sh \
          $usr_local_bin_path/string_replace.sh \
          $usr_local_bin_path/code_format_clang.sh \
          $usr_local_bin_path/trans

if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
then
    curl -fLo /etc/pacman.d/mirrorlist.mingw32.bak \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/mirrorlist.mingw32.bak
    curl -fLo /etc/pacman.d/mirrorlist.mingw32.cn \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/mirrorlist.mingw32.cn

    curl -fLo /etc/pacman.d/mirrorlist.mingw64.bak \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/mirrorlist.mingw64.bak
    curl -fLo /etc/pacman.d/mirrorlist.mingw64.cn \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/mirrorlist.mingw64.cn

    curl -fLo /etc/pacman.d/mirrorlist.msys.bak \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/mirrorlist.msys.bak
    curl -fLo /etc/pacman.d/mirrorlist.msys.cn \
            https://github.com/huhumt/vimrc_huhumt/blob/master/demo/mirrorlist.msys.cn

    cn_update_package
fi
