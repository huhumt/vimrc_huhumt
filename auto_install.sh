#/bin/bash

curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
mkdir ~/.vim/plugged
cp .vimrc .tmux.conf ~/
vim -c "silent PlugInstall" -c "qa"

cp ./demo/mirrorlist* /etc/pacman.d/
cp ./cn_update_package /usr/local/bin/
cn_update_package
