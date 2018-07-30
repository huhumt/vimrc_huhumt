# vimrc_huhumt
my own vimrc and tux_conf file
![alt text](https://raw.githubusercontent.com/huhumt/vimrc_huhumt/master/demo/demo.png)

DEPENDENCY

this script and configuration file rely on program below
1. vim, better newer than 7.4, you can check it by vim --version
2. python, both python2.7 and/or python3 is okay
3. curl and git for download plugins
4. ctags and cscope for jump in code
5. clang, cmake to support YouCompleteMe, Clang Complete
6. some other dependencies, sorry for it. I only test on my own computer, maybe
have some problems on your computer, you may solve it by yourself or contact me
by <nepood@gmail.com> or pull your request to this repo.

DESCRIPTION

this is my own vimrc file to write program. it combines functions as below:
1. show directory and project as tree using nerdtree and minibufexpl on the left
2. dispaly varialbes, structures, functions on the right using tagbar
3. auto complete code by tab using supertab, maybe you want to use youcompleteme
4. dispaly current status on the bottom using vim-airline
5. easy comment/uncomment codes using nerdcommenter
6. auto check syntastic error
7. auto update tags using ctags and vim-easytags
8. good configuration file comes from Bram Moolenaar


INSTALLATION

1. run script by "./auto_install.sh", maybe you need run "chmod 755 auto_install.sh"
first to make the script executable. Or you can run "sh auto_install.sh" directly
2. enter into vim and install plugins by ":PlugInstall"
3. all okay, enjoy your new vim

GOOD NEW:
    Now you can do all the procedure simply by running:  
    sh -c "$(curl -fsSL https://github.com/huhumt/vimrc_huhumt/blob/master/auto_install.sh)"

UPDATE

20170606: You must try YouCompleteMe plugin, or you will lose great
pleasure to write code. Although it's a bit more complex to install,
trust me, it's worth your time and effort. Treasure your life by typing
less codes using auto-complete tools.

20170607: All the script has been well tested on my MSYS2 terminal run on
Microsoft Windows7 Professional cracked edition work computer. What a shame!
After testing on my debian personal computer, I found it should run
"chmod 775 atuo_install.sh" first to make the script executable.

20170608: I find some problems when running vim on tmux, the colors of vim will change.
I have searched for some solutions but haven't totally solved them. I am using Mintty
terminal emulator on MSYS2(a Cygwin similar) environment. If you have some good
ideas for it, please let me know, I will appriciate for your kindness. Another big
problem is I can not run both YouCompleteMe(lack of python-dev support) and
Clang Complete(lack of libclang support), what a pity. But SuperTab is not enough
for auto completation, it can not identify class, structure. So I change to use
AutoComplPop, hope you like it too. Sometimes I feel it's exhausted to deal with all
kinds of these problems, but it's worth my effort to try those good things rather than
using pirated software. At the same time, you can try eclipse-cdt as alternatives.

20170613: I have tested on my debian 8 personal computer with xterm terminal and find
there is no problem in dispaly color when running vim with tmux. Maybe it's a small
problem of the MSYS2 Mintty terminal. So wish you good luck.

20180525: You can now do all the procedure by only one command "sh auto_install.sh".
I have added some small scripts for my own use.

20180730: Inspired by oh-my-zsh, now you can install it by:  
    sh -c "$(curl -fsSL https://github.com/huhumt/vimrc_huhumt/blob/master/auto_install.sh)"
