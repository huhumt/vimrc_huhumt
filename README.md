# vimrc_huhumt
my own vimrc and tux_conf file

DEPENDENCY

this script and configuration file rely on program below
1. vim, better newer than 7.4, you can check it by vim --version
2. python, both python2.7 and/or python3 is okay
3. curl and git for download plugins
4. ctags for jump in code
5. some other dependencies, sorry for it. I only test on my own computer, maybe
have some problems on your computer, you may solve it by yourself or contact me
by <nepood@gmail.com> or pull your request to this repo.

DESCRIPTION

this is my own vimrc file to write program. it combine functions as below:
1. show directory and project as tree using nerdtree and minibufexpl on the left
2. dispaly varialbes, structures, functions on the right using tagbar
3. auto complete code by tab using supertab, maybe you want to use youcompleteme
4. dispaly current status on the bottom using vim-airline
5. easy comment/uncomment codes using nerdcommenter
6. auto check syntastic error
7. auto update tags using ctags and vim-easytags
8. good configuration file comes from Bram Moolenaar


INSTALLATION

1. run script by "./auto_install.sh"
2. enter into vim and install plugins by ":PlugInstall"
3. all okay, enjoy your new vim
