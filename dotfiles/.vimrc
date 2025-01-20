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
set nobackup " do not keep a backup file, use versions instead

set history=50      " keep 50 lines of command line history
set ruler           " show the cursor position all the time
set showcmd         " display incomplete commands
set incsearch       " do incremental searching
set autoread
" Turn on the Wild menu
set wildmenu
set completeopt=menu
set viminfo='50,/1,:0,<50,@0,s10,h,n~/.vim/viminfo  " :help 'viminfo'

set ttimeout        " time out for key codes
set ttimeoutlen=100 " wait up to 100ms after Esc for special key

" Show @@@ in the last line if it is truncated.
set display=truncate

" Show a few lines of context around the cursor.  Note that this makes the
" text scroll if you mouse-click near the start or end of the window.
set scrolloff=5

" Do not recognize octal numbers for Ctrl-A and Ctrl-X,
" most users find it confusing.
set nrformats-=octal

" Ignore compiled files
set wildignore=*.o,*~,*.pyc,*/.git/*,*/.hg/*,*/.svn/*,*/.DS_Store

" Height of the command bar
set cmdheight=1

" A buffer becomes hidden when it is abandoned
set hid

" Don't redraw while executing macros (good performance config)
set lazyredraw

" For Win32 GUI: remove 't' flag from 'guioptions': no tearoff menu entries
" let &guioptions = substitute(&guioptions, "t", "", "g")
if has('win32')
    set guioptions-=t
endif

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

    " I like highlighting strings inside C comments.
    " Revert with ":unlet c_comment_strings".
    let c_comment_strings=1
endif

" Only do this part when compiled with support for autocommands.
if has("autocmd")
    " Enable file type detection.
    " Use the default filetype settings, so that mail gets 'tw' set to 72,
    " 'cindent' is on in C files, etc.
    " Also load indent files, to automatically do language-dependent indenting.
    filetype plugin indent on

    " Put these in an autocmd group, so that we can delete them easily.
    augroup vimStartup
        au!

        " For all text files set 'textwidth' to 78 characters.
        autocmd FileType text setlocal textwidth=78

        " When editing a file, always jump to the last known cursor position.
        " Don't do it when the position is invalid, when inside an event handler
        " (happens when dropping a file on gvim) and for a commit message (it's
        " likely a different one than last time).
        autocmd BufReadPost *
            \ if line("'\"") >= 1 && line("'\"") <= line("$") && &ft !~# 'commit'
            \ |   exe "normal! g`\""
            \ | endif
    augroup END

    augroup qf
        au!

        " auto open quickfix window, default height is 10
        autocmd QuickFixCmdPost * copen 20

    augroup END
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
        if getfsize("./cscope.out") > 1
            cs add ./cscope.out
        endif
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
    " nmap <Leader><Leader>e :cs find e <C-R>=expand("<cword>")<CR><CR>
    " nmap <Leader><Leader>f :cs find f <C-R>=expand("<cfile>")<CR><CR>
    " nmap <Leader><Leader>i :cs find i ^<C-R>=expand("<cfile>")<CR>$<CR>

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
" search selected string in visual mode
vnoremap // y/\V<C-R>=escape(@",'/\')<CR><CR>

if exists('$TMUX')
    " https://n8henrie.com/2021/05/copy-and-paste-between-vim-selection-and-tmux/
    vnoremap <leader>y y<CR>:call system("tmux load-buffer -", @0)<CR>gv<ESC>
    nnoremap <leader>p :let @0 = system("tmux save-buffer -")<CR>"0p<CR>g;
else
    set clipboard=unnamed
    vnoremap <leader>y "*y
    nnoremap <leader>p <ESC>"*p
endif

func! CurrentFileDir(cmd)
    return a:cmd . " " . expand("%:p:h") . "/"
endfunc

cno $c e <C-\>eCurrentFileDir("e")<cr>

" https://dustri.org/b/lightweight-and-sexy-status-bar-in-vim.html
" https://www.tdaly.co.uk/post/vanilla-vim-statusline
"" statusline
function! StatuslineCurMode()
    let l:statusline_currentmode={
           \ 'n'      : 'NORMAL ',
           \ 'v'      : 'VISUAL ',
           \ 'V'      : 'V·Line ',
           \ "\<C-V>" : 'V·Block ',
           \ 'i'      : 'INSERT ',
           \ 'R'      : 'Replace ',
           \ 'Rv'     : 'V·Replace ',
           \ 'c'      : 'Command ',
           \}
    return get(l:statusline_currentmode, mode(), 'Thinking')
endfunction

set laststatus=2
set statusline=%1*\ %{StatuslineCurMode()}
" git branch information from vim-fugitive plugin
set statusline+=%2*\%{exists('g:loaded_fugitive')?FugitiveStatusline():''}
" set statusline+=%3*\ %f\                     " short filename
set statusline+=%3*\ %{expand('%:~:.')}\     " short filename
set statusline+=%4*\%h%m%r                   " file flags (help, RO, modified)
set statusline+=%4*\%y                       " file type
" vim gutentags running status
set statusline+=%4*%{exists('g:loaded_gutentags')?gutentags#statusline():''}
set statusline+=%=                           " right align
set statusline+=%4*\ %{&fenc?&fenc:&enc}     " fileencodings
set statusline+=%4*\[%{&ff}\]\               " fileformat
set statusline+=%2*\Ln\ %l/%L\\|Col\ %v      " line count
set statusline+=%4*\ ::                      " seperator
set statusline+=%4*\ %p%%                    " precentage

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Folding
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Enable folding, I find it very useful
"set nofen
"set fdl=0

command -nargs=1 C :',. w! $HOME/.vimbuf
command -nargs=0 P :r $HOME/.vimbuf


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
" set listchars=tab:>-
set listchars=tab:\┆\ 

set tag=tags

" Support Plug NerdTree
" let NERDTreeIgnore=['\.vim$', '\~$', '\.pyc$', 'tags', '\.txt$', '\.out$']
" let g:NERDTreeDirArrowExpandable = "▸"
" let g:NERDTreeDirArrowCollapsible = "▾"
" let g:NERDTreeQuitOnOpen = 1
" map <Leader><Leader>n :NERDTreeTabsToggle<CR>
" let g:nerdtree_tabs_open_on_console_startup = 1
" let g:nerdtree_tabs_smart_startup_focus = 2
let g:fern#disable_default_mappings = 1
let g:fern#default_hidden = 1
let g:fern#drawer_width = 40
" let g:fern_auto_preview = 1
map <Leader><Leader>n :Fern . -drawer -toggle<CR>
let g:fern#renderer#default#root_symbol = '~ '

" function! FernPreviewGetMargins() abort
"     return g:fern#drawer_width
" endfunction

function! FernInit() abort
  nmap <buffer><expr>
        \ <Plug>(fern-my-open-expand-collapse)
        \ fern#smart#leaf(
        \   "\<Plug>(fern-action-open:select)",
        \   "\<Plug>(fern-action-expand)",
        \   "\<Plug>(fern-action-collapse)",
        \ )
  nmap <buffer> <CR> <Plug>(fern-my-open-expand-collapse)
  nmap <buffer> h <Plug>(fern-action-collapse)
  nmap <buffer> l <Plug>(fern-action-expand)
  nmap <buffer> <nowait> < <Plug>(fern-action-leave)
  nmap <buffer> <nowait> > <Plug>(fern-action-enter)
  nmap <buffer> p <Plug>(fern-action-preview:auto:toggle)
  nmap <buffer> <C-f> <Plug>(fern-action-preview:scroll:down:half)
  nmap <buffer> <C-d> <Plug>(fern-action-preview:scroll:up:half)
  " let g:fern_preview_window_calculator.left = function('FernPreviewGetMargins')
endfunction

augroup FernEvents
  autocmd!
  autocmd FileType fern call FernInit()
augroup END

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
" let g:airline#extensions#tabline#enabled = 1
" let g:airline#extensions#tabline#left_sep = ' '
" let g:airline#extensions#tabline#left_alt_sep = '|'
" let g:airline_theme='wombat'
" let g:airline_section_c = '%-0.64{getcwd()}/%t'
" let g:airline#extensions#ale#enabled = 1

" Support syntastic plugin
" set statusline+=%#warningmsg#
" set statusline+=%{SyntasticStatuslineFlag()}
" set statusline+=%*

" let g:syntastic_always_populate_loc_list = 1
" let g:syntastic_auto_loc_list = 2
" let g:syntastic_check_on_open = 1
" let g:syntastic_check_on_wq = 0

" support minibufexpl plugin
" let g:miniBufExplMapWindowNavVim = 1
" let g:miniBufExplMapWindowNavArrows = 1
" let g:miniBufExplMapCTabSwitchBufs = 1
" let g:miniBufExplModSelTarget = 1
let g:miniBufExplMaxSize = 3

" Support tagbar plugin
nmap <Leader>t :TagbarToggle<CR>
let g:tagbar_ctags_bin = '/usr/bin/ctags'
let g:tagbar_width = 35 " default is 40
let g:tagbar_iconchars = ['▸', '▾']
" if has("autocmd")
"     autocmd VimEnter * nested :TagbarOpen
" endif " if has("autocmd")

" nmap <Leader>t :Vista!!<CR>
" let g:vista_default_executive = 'ctags'
" let g:vista_executive_for = {
"   \ 'cpp': 'vim_lsp',
"   \ 'php': 'vim_lsp',
"   \ }

" for better performance in AutoComplPop
" set omnifunc=syntaxcomplete#Complete
" let g:acp_behaviorKeywordCommand = "\<C-x>\<C-o>"
" let g:OmniCpp_SelectFirstItem = 2
" SuperTab has occupied <C-p> and <C-n> key in insert mode
" release <tab> key binding from SuperTab and use it for code_complete
" let g:SuperTabMappingForward = '<nul>'
" let g:SuperTabMappingBackward = '<nul>'
" let g:SuperTabMappingTabLiteral = '<nul>'

" let g:ycm_global_ycm_extra_conf='~/.vim/plugged/YouCompleteMe/.ycm_extra_conf.py'
" let g:ycm_confirm_extra_conf=0

let g:gutentags_modules = ['ctags', 'cscope']
" config project root markers.
let g:gutentags_project_root = ['.root', '.project', 'tags']
" uncomment this line to debug gutentags
" let g:gutentags_define_advanced_commands = 1
" https://www.zachpfeffer.com/single-post/2018/02/20/generate-ctags-files-for-cc-source-files
let g:gutentags_ctags_extra_args_dict = {
            \ 'c': [
                \ '--recurse',
                \ '--fields=+ailmnS',
                \ '--languages=C,C++',
                \ '--c++-kinds=+p',
                \ '--extras=+q'
                \ ],
            \ 'cpp': [
                \ '--recurse',
                \ '--fields=+ailmnS',
                \ '--languages=C,C++',
                \ '--c++-kinds=+p',
                \ '--extras=+q'
                \ ],
            \ 'python': [
                \ '--recurse',
                \ '--fields=+ln',
                \ '--languages=python',
                \ '--python-kinds=-iv',
                \ ],
            \ }
" let g:gutentags_cscope_executable = 'cscope -Rbkq'
let g:gutentags_cscope_build_inverted_index = 1
" generate datebases in my cache directory, prevent gtags files polluting my project
" let g:gutentags_cache_dir = expand('~/.cache/tags')
" change focus to quickfix window after search (optional).
" let g:gutentags_plus_switch = 1
" let g:gutentags_plus_nomap = 1
" command! -nargs=1 Gfsymbol GscopeFind s <args>
" command! -nargs=1 Gfdef    GscopeFind g <args>
" command! -nargs=1 Gfcall   GscopeFind c <args>
" command! -nargs=1 Gfinc    GscopeFind i <args>
" command! -nargs=1 Gfvalue  GscopeFind a <args>

" Support Auto-Format plugin
nnoremap <Leader>f :Autoformat<CR>
vnoremap <Leader>f :Autoformat<CR>
" let g:formatdef_my_custom_cs = '"clang-format -style=file"'
let g:formatdef_my_custom_cs = '"astyle --options=~/.astylerc"'
let g:formatters_cs = ['my_custom_cs']
let g:formatdef_autopep8 = "'autopep8 - --range '.a:firstline.' '.a:lastline"
let g:formatters_python = ['autopep8']
let g:autoformat_autoindent = 0
let g:autoformat_retab = 0
" let g:autoformat_remove_trailing_spaces = 0
autocmd BufWrite *.rs :Autoformat

" Support Ctrl-P plugin
" let g:ctrlp_map = '<c-p>'
" let g:ctrlp_cmd = 'CtrlP'

" let g:ctrlp_working_path_mode = 'ra'
" let g:ctrlp_root_markers = ['pom.xml', '.p4ignore', 'README.md', 'tags', 'cscope.out']
" let g:ctrlp_custom_ignore = {
"   \ 'dir':  '\v[\/]\.(git|hg|svn)$',
"   \ 'file': '\v\.(exe|so|dll|swp|tmp|out|log|bin|hex)$',
"   \ 'link': 'some_bad_symbolic_links',
"   \ }
" let g:ctrlp_user_command = 'ag %s -l --nocolor --hidden -g ""'
" let g:ctrlp_match_window = 'bottom,order:ttb,min:1,max:10,results:10'
let g:Lf_ShortcutF = '<C-p>'
let g:Lf_HideHelp = 1
let g:Lf_RootMarkers = [
        \ 'tags', 'cscope.out',
        \ '.git', '.svn', '.hg'
        \]
" https://github.com/ggreer/the_silver_searcher/blob/850e2b3887f0daa873fe2098f3f215b2c36000e1/tests/list_file_types.t
" let g:Lf_ExternalCommand = 'ag %s -l --cc --cpp --silent --nocolor -g ""'
" let g:Lf_ExternalCommand = 'ag %s -l --silent --ignore={
"             \"*.sw?","~$*",
"             \"*.o","*.d","*.su","*.so","*.dll","*.a","*.obj",
"             \"*.tmp","tags","*.out*","*.bak","*.log",
"             \"*.bin","*.hex","*.exe","*.py[co]","*.cache"
"         \} -g ""'
let g:Lf_ExternalCommand = 'ag %s -l --silent --hidden
        \ --ignore ".git" --ignore ".svn" --ignore ".hg"
        \ --ignore ".cache" --ignore ".npm"
        \ --ignore "*.sw?" --ignore "~$*"
        \ --ignore "*.o" --ignore "*.d" --ignore "*.su" --ignore "*.obj"
        \ --ignore "*.so" --ignore "*.dll" --ignore "*.a"
        \ --ignore "*.tmp" --ignore "tags" --ignore "*.out*"
        \ --ignore "*.bak" --ignore "*.log"
        \ --ignore "*.bin" --ignore "*.hex" --ignore "*.exe"
        \ --ignore "*.py[co]" --ignore "*.cache"
        \ -g ""'
let g:Lf_CommandMap = {'<C-K>': ['<Up>'], '<C-J>': ['<Down>']}
let g:Lf_ShowDevIcons = 0
let g:Lf_PreviewInPopup = 0

" Support ctrlsp plugin
let g:ctrlsf_default_view_mode = 'compact'
let g:ctrlsf_compact_winsize = '20%'
let g:ctrlsf_context = '-C 0'
let g:ctrlsf_case_sensitive = 'yes'
let g:ctrlsf_default_root = 'cwd'
let g:ctrlsf_auto_preview = 1
let g:ctrlsf_indent = 2
let g:ctrlsf_auto_focus = {
    \ "at": "start"
    \ }
let g:ctrlsf_backend = 'ag'
" \ 'ag': '--silent --word-regexp'
" \ 'ag': '--silent --literal'
" let g:ctrlsf_extra_backend_args = {
"     \ 'ag': '--silent --word-regexp'
"     \ }
let g:ctrlsf_mapping = {
    \ "open"    : ["<CR>", "o", "<2-LeftMouse>"],
    \ "openb"   : "",
    \ "split"   : "",
    \ "vsplit"  : "",
    \ "tab"     : "",
    \ "tabb"    : "",
    \ "popen"   : "",
    \ "popenf"  : "",
    \ "quit"    : "q",
    \ "stop"    : "",
    \ "next"    : ["<C-N>", "j"],
    \ "prev"    : ["<C-P>", "k"],
    \ "nfile"   : "",
    \ "pfile"   : "",
    \ "chgmode" : "",
    \ "pquit"   : "q",
    \ "loclist" : "",
    \ "fzf"     : "",
    \ }
nmap <Leader><Leader>e <Plug>CtrlSFCwordExec
vmap <Leader><Leader>e <Plug>CtrlSFVwordExec

" Support for easy motion
let g:EasyMotion_do_mapping = 0 " Disable default mappings
let g:EasyMotion_smartcase = 1 " Turn on case insensitive feature
nmap s <Plug>(easymotion-sn)

" Support Hexmode plugin
let g:hexmode_patterns = '*.bin,*.exe,*.dat,*.o'
let g:hexmode_xxd_options = '-g 1'

" Support for Vim-Dict plugin
" let g:trans_bin = "/usr/bin"
nnoremap <silent> <Leader><Leader>t :Trans<CR>

" exclude some filetype when do diff
let g:DirDiffExcludes = "CVS,*.class,*.exe,*.bin,*.hex,.*,.*.swp,*.o,tags,*.log,*.out,*.git,*.svn"
let g:DirDiffIgnore = "Id:,Revision:,Date:"
let g:DirDiffWindowSize = 5
nnoremap <Leader><Leader>g :diffget<CR>
nnoremap <Leader><Leader>p :diffput<CR>

" vim-lion squeeze extra whitespace
let g:lion_squeeze_spaces = 1

" disable markdown on polyglot
let g:polyglot_disabled = ['markdown']

" change indent display color
let g:vim_json_conceal = 0
let g:markdown_syntax_conceal = 0
let g:indentLine_color_term = 239
let g:indentLine_char_list = ['|', '¦', '┆', '┊']

" enable rainbow plugin default
let g:rainbow_active = 1

" bug fix for code color plugin
" let c_no_curly_error = 1
" Enable highlighting of C++11 attributes
let g:cpp_attributes_highlight = 1
" Highlight struct/class member variables (affects both C and C++ files)
let g:cpp_member_highlight = 1
" Put all standard C and C++ keywords under Vim's highlight group 'Statement', (affects both C and C++ files)
let g:cpp_simple_highlight = 1

" vim-matchup corrupts with statusline
let g:matchup_matchparen_enabled = 0

" configuration for vim-table-mode
autocmd BufEnter *.md let g:table_mode_corner='|'

" configuration for rust.vim
" let g:rustfmt_autosave = 1

" configuration for coc.nvim
" let g:lsp_cxx_hl_use_text_props = 1
nnoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
nnoremap <silent><nowait><expr> <C-d> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-b>"
inoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? "\<c-r>=coc#float#scroll(1)\<cr>" : "\<Right>"
inoremap <silent><nowait><expr> <C-d> coc#float#has_scroll() ? "\<c-r>=coc#float#scroll(0)\<cr>" : "\<Left>"
vnoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
vnoremap <silent><nowait><expr> <C-d> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-b>"

nnoremap <Leader><Leader>k :CocCommand document.toggleInlayHint<CR>
" vmap <leader>a <Plug>(coc-codeaction-selected)
" nmap <leader>a <Plug>(coc-codeaction-selected)
let g:coc_global_extensions = [
        \ "coc-rome", "coc-markdownlint", "coc-rust-analyzer", "coc-xml",
        \ "coc-yaml", "coc-sh", "coc-spell-checker", "coc-highlight",
        \ "coc-pyright", "coc-clangd", "coc-pairs", "coc-json", "coc-go"
        \]
" Remove plugins not explicitly defined in g:coc_global_extensions
" Ignore special case: friendly-snippets, coc-vim-source-requirements
function! CocClean() abort
  let g:extensions_to_clean = CocAction("loadedExtensions")
      \ ->filter({idx, extension -> extension !~ 'friendly-snippets'})
      \ ->filter({idx, extension -> extension !~ 'coc-vim-source-requirements'})
      \ ->filter({idx, extension -> index(g:coc_global_extensions, extension) == -1})
  if len(g:extensions_to_clean)
    exe 'CocUninstall' join(map(g:extensions_to_clean, {_, line -> split(line)[0]}))
  endif
endfunction
command! -nargs=0 CocClean :call CocClean()









" Specify a directory for plugins (for Neovim: ~/.local/share/nvim/plugged)
call plug#begin('~/.vim/plugged')

" Make sure you use single quotes

" Manage your project looks like a tree-list
" Plug 'scrooloose/nerdtree'
" Plug 'jistr/vim-nerdtree-tabs'
Plug 'lambdalisue/fern.vim'
Plug 'yuki-yano/fern-preview.vim'

" comment your code easily
" Plug 'scrooloose/nerdcommenter'
Plug 'tpope/vim-commentary'

" check your code syntastic
" Plug 'vim-syntastic/syntastic'
" Plug 'dense-analysis/ale'

" display vim status
" Plug 'vim-airline/vim-airline'
" Plug 'vim-airline/vim-airline-themes'

" display whitespace
Plug 'bronson/vim-trailing-whitespace'

" use mini-buffer window to display select function
" this plugin broke command `20 split README.md`
Plug 'fholgado/minibufexpl.vim'

" use tagbar to display current status
Plug 'majutsushi/tagbar'
" Plug 'liuchengxu/vista.vim'

" auto complete code usging SuperTab
" Plug 'ervandew/supertab'
" Plug 'vim-scripts/AutoComplPop'
" Plug 'vim-scripts/OmniCppComplete'
" Plug 'mbbill/code_complete'
" Plug 'ycm-core/YouCompleteMe'
Plug 'neoclide/coc.nvim', {'branch': 'release'}
" Plug 'jackguo380/vim-lsp-cxx-highlight'
" Plug 'ackyshake/VimCompletesMe'
Plug 'ludovicchabant/vim-gutentags'
" Plug 'skywind3000/gutentags_plus'

" auto add delimite
" Plug 'Raimondi/delimitMate'

" auto format code using clang style
Plug 'vim-autoformat/vim-autoformat'

" fuzzy search using Ctrl-P
" Plug 'ctrlpvim/ctrlp.vim'
Plug 'Yggdroot/LeaderF'
Plug 'dyng/ctrlsf.vim'

" Support open and edit hex file
Plug 'fidian/hexmode'

" use network dictionary for words
Plug 'echuraev/translate-shell.vim'

" use easy motion for fast jump
Plug 'easymotion/vim-easymotion'

" use reversion manage tool
" Plug 'vim-scripts/vcscommand.vim'
Plug 'tpope/vim-fugitive'

" use dirdiff tool to do diff and merge
Plug 'will133/vim-dirdiff'

" use mark to display color
Plug 'vim-scripts/Mark'

" display indent
Plug 'Yggdroot/indentLine'

" display quote, blanket in different color
Plug 'luochen1990/rainbow'

" easy align code
" Plug 'junegunn/vim-easy-align'
" gl for right-align and gL for ledt-align operator
Plug 'tommcdo/vim-lion'

" color for c/c++ code
" Plug 'octol/vim-cpp-enhanced-highlight'
Plug 'bfrg/vim-cpp-modern'
Plug 'sheerun/vim-polyglot'

" use % to match keywords
Plug 'andymass/vim-matchup'

" use onedark colorscheme
Plug 'rafi/awesome-vim-colorschemes'

" display git info
Plug 'airblade/vim-gitgutter'

" auto generate table in vim
Plug 'dhruvasagar/vim-table-mode'

" vim-8 rust plugin to support hilighting, formating, Syntastic
" Plug 'rust-lang/rust.vim'

" split long line to multiple line by gS or gJ for the opposite
Plug 'AndrewRadev/splitjoin.vim'












" Initialize plugin system
call plug#end()



silent! colorscheme one-dark
" autocmd BufEnter *.txt colorscheme github
" autocmd BufEnter *.log colorscheme github
" autocmd BufEnter *.md  colorscheme github

" autocmd BufEnter *.txt set spell spelllang=en_gb
" autocmd BufEnter *.log set spell spelllang=en_gb
" autocmd BufEnter *.md  set spell spelllang=en_gb

highlight Comment ctermfg=lightgreen guifg=green
highlight Visual cterm=underline,standout ctermfg=red ctermbg=lightred
highlight Search cterm=bold ctermfg=yellow ctermbg=lightblue
" refer to <http://vim.wikia.com/wiki/Xterm256_color_names_for_console_Vim?file=Finder.gif>
highlight DiffChange cterm=none ctermfg=blue ctermbg=lightcyan gui=none guifg=bg guibg=Red
highlight DiffAdd    cterm=none ctermfg=blue ctermbg=lightcyan gui=none guifg=bg guibg=Red
highlight DiffDelete cterm=none ctermfg=blue ctermbg=lightcyan gui=none guifg=bg guibg=Red
highlight DiffChange cterm=none ctermfg=blue ctermbg=lightcyan gui=none guifg=bg guibg=Red
highlight DiffText   cterm=none ctermfg=blue ctermbg=lightcyan gui=none guifg=bg guibg=Red

" add crosshair style cursor
highlight CursorLine   cterm=reverse ctermbg=NONE ctermfg=NONE guibg=darkgray guifg=NONE
" highlight CursorColumn cterm=NONE ctermbg=lightgray ctermfg=NONE guibg=brown guifg=NONE
highlight CursorColumn cterm=reverse ctermbg=NONE ctermfg=NONE guibg=brown guifg=NONE
set cursorline    " enable the horizontal line
set cursorcolumn  " enable the vertical line
" refer to https://vim.fandom.com/wiki/Xterm256_color_names_for_console_Vim?file=Xterm-color-table.png
highlight ColorColumn cterm=reverse ctermbg=NONE ctermfg=NONE guibg=brown guifg=NONE
set colorcolumn=80

" highlight line number
highlight LineNr term=bold cterm=NONE ctermfg=Grey ctermbg=NONE gui=NONE guifg=DarkGrey guibg=NONE

" change coc underline highlight
" highlight MyErrorHi cterm=None ctermbg=lightgray ctermfg=NONE
" highlight link CocErrorHighlight MyErrorHi
" highlight link CocWarningHighlight MyErrorHi
" highlight link CocHintHighlight MyErrorHi
" highlight link CocInfoHighlight MyErrorHi

" https://www.ditig.com/256-colors-cheat-sheet
highlight User1 ctermbg=2   ctermfg=0   guibg=green guifg=black
highlight User2 ctermbg=12  ctermfg=120 guibg=black guifg=lightgreen
highlight User3 ctermbg=240 ctermfg=168 guibg=black guifg=grey
highlight User4 ctermbg=8   ctermfg=156 guibg=black guifg=lightgreen

highlight SpecialKey ctermfg=239 guibg=black
highlight CocInlayHint ctermfg=10 ctermbg=242 guifg=#15aabf guibg=Grey

highlight MarkWord1  ctermbg=DarkCyan     ctermfg=Black  guibg=#8CCBEA    guifg=Black
highlight MarkWord2  ctermbg=Green        ctermfg=Black  guibg=#A4E57E    guifg=Black
highlight MarkWord3  ctermbg=DarkYellow   ctermfg=Black  guibg=#FFDB72    guifg=Black
highlight MarkWord4  ctermbg=LightRed     ctermfg=Black  guibg=#FF7272    guifg=Black
highlight MarkWord5  ctermbg=DarkRed      ctermfg=Black  guibg=#FFB3FF    guifg=Black
highlight MarkWord6  ctermbg=Blue         ctermfg=Black  guibg=#9999FF    guifg=Black
