" An example for a vimrc file.
"
" Maintainer: Bram Moolenaar <Bram@vim.org>
" Last change: 2002 Sep 19
"
" To use it, copy it to
"     for Unix and OS/2:  ~/.vimrc
"     for Amiga:  s:.vimrc
"     for MS-DOS and Win32:  $VIM\_vimrc
"     for OpenVMS:  sys$login:.vimrc

" When started as "evim", evim.vim will already have done these settings.
if v:progname =~? "evim"
    finish
endif

" Use Vim settings, rather then Vi settings (much better!).
" This must be first, because it changes other options as a side effect.
set nocompatible

" allow backspacing over everything in insert mode
set backspace=indent,eol,start

if has("vms")
    set nobackup " do not keep a backup file, use versions instead
else
    set nobackup " keep a backup file
endif

set history=50      " keep 50 lines of command line history
set ruler           " show the cursor position all the time
set showcmd         " display incomplete commands
set incsearch       " do incremental searching

" For Win32 GUI: remove 't' flag from 'guioptions': no tearoff menu entries
" let &guioptions = substitute(&guioptions, "t", "", "g")

" Don't use Ex mode, use Q for formatting
map Q gq

" This is an alternative that also works in block mode, but the deleted
" text is lost and it only works for putting the current register.
"vnoremap p "_dp

" Switch syntax highlighting on, when the terminal has colors
" Also switch on highlighting the last used search pattern.
if &t_Co > 2 || has("gui_running")
    syntax on
    set hlsearch
endif

" Only do this part when compiled with support for autocommands.
if has("autocmd")

    " Enable file type detection.
    " Use the default filetype settings, so that mail gets 'tw' set to 72,
    " 'cindent' is on in C files, etc.
    " Also load indent files, to automatically do language-dependent indenting.
    filetype plugin indent on

    " Put these in an autocmd group, so that we can delete them easily.
    augroup vimrcEx
        au!

        " For all text files set 'textwidth' to 78 characters.
        autocmd FileType text setlocal textwidth=78

        " When editing a file, always jump to the last known cursor position.
        " Don't do it when the position is invalid or when inside an event handler
        " (happens when dropping a file on gvim).
        autocmd BufReadPost *
                    \ if line("'\"") > 0 && line("'\"") <= line("$") |
                    \   exe "normal g`\"" |
                    \ endif

    augroup END

    augroup qf
        au!

        " auto open quickfix window, default height is 10
        autocmd QuickFixCmdPost * copen 20

    augroup END

else

    set autoindent " always set autoindenting on

endif " has("autocmd")

" CSCOPE settings for vim
" This file contains some boilerplate settings for vim's cscope interface,
" plus some keyboard mappings that I've found useful.
"
" USAGE:
" -- vim 6:     Stick this file in your ~/.vim/plugin directory (or in a
"               'plugin' directory in some other directory that is in your
"               'runtimepath'.
"
" -- vim 5:     Stick this file somewhere and 'source cscope.vim' it from
"               your ~/.vimrc file (or cut and paste it into your .vimrc).
"
" NOTE:
" These key maps use multiple keystrokes (2 or 3 keys).  If you find that vim
" keeps timing you out before you can complete them, try changing your timeout
" settings, as explained below.
"
" Happy cscoping,
"
" Jason Duell       jduell@alumni.princeton.edu     2002/3/7


" This tests to see if vim was configured with the '--enable-cscope' option
" when it was compiled.  If it wasn't, time to recompile vim...
if has("cscope")

    """"""""""""" Standard cscope/vim boilerplate

    " use both cscope and ctag for 'ctrl-]', ':ta', and 'vim -t'
    set cscopetag

    " check cscope for definition of a symbol before checking ctags: set to 1
    " if you want the reverse search order.
    set csto=0

    " add any cscope database in current directory
    if filereadable("./cscope.out")
        cs add ./cscope.out
        " else add the database pointed to by environment variable
    elseif $CSCOPE_DB != ""
        cs add $CSCOPE_DB
    endif

    " show msg when any other cscope db added
    set cscopeverbose

    if has('quickfix')
        set cscopequickfix=s-,c-,d-,i-,t-,e-
    endif


    """"""""""""" My cscope/vim key mappings
    " The following maps all invoke one of the following cscope search types:
    " a: Find assignments to this symbol
    " c: Find functions calling this function
    " d: Find functions called by this function
    " e: Find this egrep pattern
    " f: Find this file
    " g: Find this definition
    " i: Find files #including this file
    " s: Find this C symbol
    " t: Find this text string

    nmap <Leader><Leader>c :cs find c <C-R>=expand("<cword>")<CR><CR>
    nmap <Leader><Leader>e :cs find e <C-R>=expand("<cword>")<CR><CR>
    " nmap <Leader><Leader>f :cs find f <C-R>=expand("<cfile>")<CR><CR>
    " nmap <Leader><Leader>i :cs find i ^<C-R>=expand("<cfile>")<CR>$<CR>


    """"""""""""" key map timeouts
    " By default Vim will only wait 1 second for each keystroke in a mapping.
    " You may find that too short with the above typemaps.  If so, you should
    " either turn off mapping timeouts via 'notimeout'.
    "set notimeout
    " Or, you can keep timeouts, by uncommenting the timeoutlen line below,
    " with your own personal favorite value (in milliseconds):
    "set timeoutlen=4000
    " Either way, since mapping timeout settings by default also set the
    " timeouts for multicharacter 'keys codes' (like <F1>), you should also
    " set ttimeout and ttimeoutlen: otherwise, you will experience strange
    " delays as vim waits for a keystroke after you hit ESC (it will be
    " waiting to see if the ESC is actually part of a key code like <F1>).
    "set ttimeout
    " personally, I find a tenth of a second to work well for key code
    " timeouts. If you experience problems and have a slow terminal or network
    " connection, set it higher.  If you don't set ttimeoutlen, the value for
    " timeoutlent (default: 1000 = 1 second, which is sluggish) is used.
    "set ttimeoutlen=100

endif

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Moving around and tabs
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" Smart way to move btw. windows
map <C-j> <C-W>j
map <C-k> <C-W>k
map <C-h> <C-W>h
map <C-l> <C-W>l
map <S-*> <C-W>y

func! CurrentFileDir(cmd)
    return a:cmd . " " . expand("%:p:h") . "/"
endfunc

cno $c e <C-\>eCurrentFileDir("e")<cr>

"echo CurrentFileDir("pwd")<cr>
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Folding
" """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Enable folding, I find it very useful
"set nofen
"set fdl=0

function! CurDir()
    let curdir = substitute(getcwd(), '/Users/amir/', "~/", "g")
    return curdir
endfunction

" modified by TinyFish on 2016.3.18 to enable show line number
"
set encoding=utf-8
scriptencoding utf-8
set fileencodings=ucs-bom,utf-8,gb2312,gb18030
set termencoding=utf-8
set fileformats=unix

set shiftwidth=4
set tabstop=4
set softtabstop=4
set expandtab

set number
set nowrap
set guioptions=mlrb

set list
set listchars=tab:>-

set tag=tags
map <Leader>u :!ctags -Rn<CR>:!cscope -Rbk<CR>:cs reset<CR><CR>

"
" endif
highlight Comment ctermfg=green guifg=green
highlight Visual cterm=reverse ctermbg=none
" refer to <http://vim.wikia.com/wiki/Xterm256_color_names_for_console_Vim?file=Finder.gif>
highlight DiffChange cterm=bold ctermfg=none ctermbg=119 gui=none guifg=bg guibg=Red
highlight DiffAdd    cterm=bold ctermfg=none ctermbg=119 gui=none guifg=bg guibg=Red
highlight DiffDelete cterm=bold ctermfg=none ctermbg=119 gui=none guifg=bg guibg=Red
highlight DiffChange cterm=bold ctermfg=none ctermbg=119 gui=none guifg=bg guibg=Red
highlight DiffText   cterm=bold ctermfg=none ctermbg=119 gui=none guifg=bg guibg=Red
set statusline=\ %F%m%r%h\ %w\ \ CWD:\ %r%{CurDir()}%h\ \ \ Line:\ %l/%L:%c

command -nargs=1 C :',. w! $HOME/.vimbuf
command -nargs=0 P :r $HOME/.vimbuf


" Support Plug NerdTree
let NERDTreeIgnore=['\.vim$', '\~$', '\.pyc$', 'tags', '\.txt$', '\.out$']
let g:NERDTreeDirArrowExpandable = "▸"
let g:NERDTreeDirArrowCollapsible = "▾"
map <Leader>n :NERDTreeTabsToggle<CR>
" let g:nerdtree_tabs_open_on_console_startup = 1
" let g:nerdtree_tabs_smart_startup_focus = 2

" Support NerdCommenter, powerful comment tool
" Add spaces after comment delimiters by default
"let g:NERDSpaceDelims = 1
" Use compact syntax for prettified multi-line comments
"let g:NERDCompactSexyComs = 1
" Align line-wise comment delimiters flush left instead of following code indentation
"let g:NERDDefaultAlign = 'left'
" Set a language to use its alternate delimiters by default
"let g:NERDAltDelims_java = 1
" Add your own custom formats or override the defaults
" let g:NERDCustomDelimiters = { 'h': { 'left': '/**','right': '**/' } }
"let g:NERDCustomDelimiters = { 'cpp': { 'left': '/**','right': '**/' } }
" Allow commenting and inverting empty lines (useful when commenting a region)
"let g:NERDCommentEmptyLines = 1
" Enable trimming of trailing whitespace when uncommenting
"let g:NERDTrimTrailingWhitespace = 1

" Support airline plugin
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#left_sep = ' '
let g:airline#extensions#tabline#left_alt_sep = '|'

" Support syntastic plugin
set statusline+=%#warningmsg#
set statusline+=%{SyntasticStatuslineFlag()}
set statusline+=%*

let g:syntastic_always_populate_loc_list = 1
let g:syntastic_auto_loc_list = 2
let g:syntastic_check_on_open = 1
let g:syntastic_check_on_wq = 0

" support minibufexpl plugin
let g:miniBufExplMapWindowNavVim = 1
let g:miniBufExplMapWindowNavArrows = 1
let g:miniBufExplMapCTabSwitchBufs = 1
let g:miniBufExplModSelTarget = 1

" Support tagbar plugin
nmap <Leader>t :TagbarToggle<CR>
let g:tagbar_ctags_bin='/usr/bin/ctags'
" let g:tagbar_width=35 " default is 40
let g:tagbar_iconchars = ['▸', '▾']
" if has("autocmd")
"     autocmd VimEnter * nested :TagbarOpen
" endif " if has("autocmd")

" Support Auto-Format plugin
nnoremap <Leader>f :Autoformat<CR>
vnoremap <Leader>f :Autoformat<CR>
let g:formatdef_my_custom_cs = '"clang-format -style=file"'
let g:formatters_cs = ['my_custom_cs']
let g:autoformat_autoindent = 0
let g:autoformat_retab = 0
let g:autoformat_remove_trailing_spaces = 0

" Support Ctrl-P plugin
" let g:ctrlp_map = '<c-p>'
" let g:ctrlp_cmd = 'CtrlP'

" let g:ctrlp_working_path_mode = 'ra'
" let g:ctrlp_root_markers = ['pom.xml', '.p4ignore', 'README.md', 'tags', 'cscope.out']

" let g:ctrlp_custom_ignore = {
"   \ 'dir':  '\v[\/]\.(git|hg|svn)$',
"   \ 'file': '\v\.(exe|so|dll|swp|tmp)$',
"   \ 'link': 'some_bad_symbolic_links',
"   \ }
let g:Lf_ShortcutF = '<C-P>'
let g:Lf_HideHelp = 1
let g:Lf_RootMarkers = [
        \ 'tags', 'cscope.out',
        \ '.project*', 'README*',
        \'.git', '.svn', '.hg'
        \]
let g:Lf_WildIgnore = {
        \ 'dir': ['.svn','.git','.hg'],
        \ 'file': [
            \ '*.sw?','~$*','*.bak','*.exe',
            \ '*.o','*.so','*.py[co]','*.dll',
            \ '*.tmp','tags','*.out'
            \]
        \}
let g:Lf_DefaultExternalTool = "ag"

" Support Hexmode plugin
let g:hexmode_patterns = '*.bin,*.exe,*.dat,*.o'

" Support for Vim-Dict plugin
let g:trans_bin = "/usr/local/bin"
nnoremap <silent> <leader><leader>t :Trans<CR>

" Support for easy motion
let g:EasyMotion_do_mapping = 0 " Disable default mappings

" Jump to anywhere you want with minimal keystrokes, with just one key binding.
" `s{char}{label}`
nmap s <Plug>(easymotion-overwin-f)

" Turn on case insensitive feature
let g:EasyMotion_smartcase = 1

" JK motions: Line motions
map <Leader>j <Plug>(easymotion-j)
map <Leader>k <Plug>(easymotion-k)

" exclude some filetype when do diff
let g:DirDiffExcludes = "CVS,*.class,*.exe,.*.swp,*.o,tags,*.out"
let g:DirDiffIgnore = "Id:,Revision:,Date:"
let g:DirDiffWindowSize = 5
nnoremap <Leader><Leader>g :diffget<CR>
nnoremap <Leader><Leader>p :diffput<CR>




" Specify a directory for plugins (for Neovim: ~/.local/share/nvim/plugged)
call plug#begin('~/.vim/plugged')
"
" " Make sure you use single quotes

" Manage your project looks like a tree-list
Plug 'scrooloose/nerdtree'
Plug 'jistr/vim-nerdtree-tabs'

" comment your code easily
" Plug 'scrooloose/nerdcommenter'
Plug 'tpope/vim-commentary'

" check your code syntastic
Plug 'vim-syntastic/syntastic'

" display vim status
Plug 'vim-airline/vim-airline'
Plug 'vim-airline/vim-airline-themes'

" display whitespace
Plug 'bronson/vim-trailing-whitespace'

" use mini-buffer window to display select function
Plug 'fholgado/minibufexpl.vim'

" ust tagbar to display current status
Plug 'majutsushi/tagbar'

" auto complete code usging SuperTab
" Plug 'ervandew/supertab'
" Plug 'vim-scripts/AutoComplPop'
" Plug 'Valloric/YouCompleteMe'
Plug 'ervandew/supertab'

" auto add delimite
Plug 'Raimondi/delimitMate'

" auto format code using clang style
Plug 'Chiel92/vim-autoformat'

" fuzzy search using Ctrl-P
" Plug 'ctrlpvim/ctrlp.vim'
Plug 'Yggdroot/LeaderF'

" Support open and edit hex file
Plug 'fidian/hexmode'

" use network dictionary for words
Plug 'echuraev/translate-shell.vim'

" use easy motion for fast jump
Plug 'easymotion/vim-easymotion'

" use reversion manage tool
Plug 'vim-scripts/vcscommand.vim'

" use dirdiff tool to do diff and merge
Plug 'will133/vim-dirdiff'



"
" Initialize plugin system
call plug#end()

