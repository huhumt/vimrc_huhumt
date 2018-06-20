#/bin/bash

curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
mkdir ~/.vim/plugged
cp .vimrc .tmux.conf ~/
vim -c "silent PlugClean" -c "silent PlugInstall" -c "qa"

mkdir ~/.config/pip
cp pip.conf ~/.config/pip/

# get system info of kernal and os in lowercase
kernel_name=$(echo "$(uname -s)" | tr '[:upper:]' '[:lower:]')
os_name=$(echo "$(uname -o)" | tr '[:upper:]' '[:lower:]')
if [[ "$kernel_name" = *"mingw"* ]] || [[ "$os_name" = *"msys"* ]]
then
    sed -i 's/'"\/usr\/bin\/ctags"'/'"\/mingw64\/bin\/ctags"'/g' ~/.vimrc
    # use local mirror to speedup download
    cp ./demo/mirrorlist* /etc/pacman.d/
    cp ./cn_update_package /usr/local/bin/
    cn_update_package
fi
