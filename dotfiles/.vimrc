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
set nobackup nowritebackup " do not keep a backup file, use versions instead

set history=50      " keep 50 lines of command line history
set ruler           " show the cursor position all the time
set showcmd         " display incomplete commands
set incsearch       " do incremental searching
set autoread
" Turn on the Wild menu
set wildmenu
set wildcharm=<Tab>
set completeopt=menuone,noinsert,noselect,popup
set viminfo='50,/1,:0,<50,@0,s10,h,n~/.vim/viminfo  " :help 'viminfo'

" from vim version 9.1.1243, it starts to support diff by char
" https://github.com/vim/vim/commit/9943d4790e42721a6777da9e12637aa595ba4965
" if has("patch-9.1.1243")
"     set diffopt=internal,filler,closeoff,inline:char
" endif
set fillchars+=diff:\ " display nothing for diff add/delete

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
        autocmd!

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
        autocmd!

        " auto open quickfix window, default height is 10
        autocmd QuickFixCmdPost * copen 20

    augroup END

    augroup ToggleCursorLineCol
        autocmd!
        autocmd WinLeave,BufLeave * set nonumber colorcolumn= nocursorline nocursorcolumn
        autocmd WinEnter,BufEnter * setlocal number colorcolumn=80 cursorline cursorcolumn
    augroup END

    augroup FernEvents
        autocmd!
        autocmd FileType fern call FernInit()
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

    set nocscopeverbose
    " add any cscope database in current directory
    if executable('cscope') && getfsize("./cscope.out") > 1
        cs add ./cscope.out
    elseif executable('gtags-cscope') && getfsize("./GTAGS") > 1
        set csprg=gtags-cscope
        cs add ./GTAGS
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

    nnoremap <Leader><Leader>c :cs find c <C-R>=expand("<cword>")<CR><CR>
    " nnoremap <Leader><Leader>e :cs find e <C-R>=expand("<cword>")<CR><CR>
    " nnoremap <Leader><Leader>f :cs find f <C-R>=expand("<cfile>")<CR><CR>
    " nnoremap <Leader><Leader>i :cs find i ^<C-R>=expand("<cfile>")<CR>$<CR>

endif

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Moving around and tabs
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

" Smart way to move windows btw. refer to `:help window-moving-cursor`
map <C-j> <C-W>j
" map <C-k> <C-W>k<C-W>h
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

" auto set paste/nopaste when use 'shift+insert'
" https://coderwall.com/p/if9mda/automatically-set-paste-mode-in-vim-when-pasting-in-insert-mode
" Auto-toggle paste mode for xterm
let &t_SI .= "\<Esc>[?2004h"
let &t_EI .= "\<Esc>[?2004l"
inoremap <special> <expr> <Esc>[200~ XTermPasteBegin()
function! XTermPasteBegin()
  set pastetoggle=<Esc>[201~
  set paste
  return ""
endfunction

func! CurrentFileDir(cmd)
    return a:cmd . " " . expand("%:p:h") . "/"
endfunc

cno $c e <C-\>eCurrentFileDir("e")<cr>

" https://dustri.org/b/lightweight-and-sexy-status-bar-in-vim.html
" https://www.tdaly.co.uk/post/vanilla-vim-statusline
"" statusline
function! StatuslineCurMode() abort
    let l:mode_map = {
           \ 'n'      : 'Normal',
           \ 'v'      : 'Visual',
           \ 'V'      : 'V·Line',
           \ "\<C-V>" : 'V·Block',
           \ 'i'      : 'Insert',
           \ 'R'      : 'Replace',
           \ 'Rv'     : 'V·Replace',
           \ 'c'      : 'Command',
           \}
    return "%#User1# " . get(l:mode_map, mode(), 'Thinking') . " "
endfunction

function! StatuslineGitBranch() abort
    let l:git_head_file = finddir('.git', expand('%:p:h') . ';') .. "/HEAD"
    if filereadable(l:git_head_file)
        let l:git_branch = substitute(get(readfile(l:git_head_file), 0, ""), "^ref: refs/heads/", "", "")
        return "%#User2# [Git](" . l:git_branch . ") "
    else
        return ""
    endif
endfunction

function! StatuslineFilename(active_win, nofile_flag) abort
    if a:nofile_flag
        if exists('g:ctrlsf_loaded') && bufname('%') == '__CtrlSFPreview__'
            let l:filename = ctrlsf#utils#PreviewSectionC()
        else
            return "%#SignColumn#"
        endif
    else
        let l:filename = empty(bufname()) ? "new file" : expand('%:~:.')
    endif

    if a:active_win
        return "%#User3# " . l:filename
    else
        return "%#User4# filename: " . l:filename . " %#SignColumn#"
    endif
endfunction

function! StatuslineRight(longfmt) abort
    let l:lines_cnt = -(strlen(line('$')) * 2 + 1)
    let l:right = "%#User2# Ln %" . l:lines_cnt . "(%l/%L%)%9(| Col %v%) "
    if a:longfmt
        let l:select_lines = abs(line(".") - line("v")) + 1
        if l:select_lines > 1
            let l:se_show = "selected " . l:select_lines . " lines, "
        else
            let l:se = searchcount(#{maxcount:0})
            if l:se.exact_match
                let l:se_show = "matches " . l:se.current . "/" . l:se.total . ", "
            endif
        endif
        let l:right = "%#User4#[" . get(l:, "se_show", "")
                \ . "%{&fenc?&fenc:&enc},%{&ff}%(,%Y%)%(,%M%)%(,%R%)] "
                \ . l:right . "%#User4# ::%4(%p%%%)"
    endif
    return "%=" . l:right
endfunction

function! StatusLineCustom(winid) abort
    let l:nofile_idx = index(['nofile', 'quickfix', 'prompt', 'popup'],
                \ getbufvar(winbufnr(a:winid), "&buftype"))
    if win_getid() == a:winid && l:nofile_idx == -1
        let l:mode = "%{%StatuslineCurMode()%}"
        let l:filename = "%{%StatuslineFilename(1, 0)%}"
        if &columns > 100 && winwidth(0) == &columns
            let l:git_branch = "%{%StatuslineGitBranch()%}"
            let l:right = "%{%StatuslineRight(1)%}"
        else
            let l:right = "%{%StatuslineRight(0)%}"
        endif
        return l:mode . "%<" . get(l:, "git_branch", "") . l:filename
                \ . " %#User4#" . l:right
    else
        if l:nofile_idx == -1
            return "%{%StatuslineFilename(0, 0)%}"
        else
            return "%{%StatuslineFilename(0, 1)%}"
        endif
    endif
endfunction

set laststatus=2
set statusline=%!StatusLineCustom(g:statusline_winid)

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Folding
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Enable folding, I find it very useful
"set nofen
"set fdl=0

" command -nargs=1 C :',. w! $HOME/.vimbuf
" command -nargs=0 P :r $HOME/.vimbuf


" modified by TinyFish on 2016.3.18 to enable show line number
"
set encoding=utf-8
scriptencoding utf-8
set fileencodings=ucs-bom,utf-8,gb2312,gb18030
set termencoding=utf-8
set fileformats=unix
" set spell after encoding to avoid loading twice, refer to ':help spell'
set spell spelllang=en_gb,cjk
let g:netrw_liststyle = 3

set shiftwidth=4
set tabstop=4
set softtabstop=4
set expandtab

set nowrap
set guioptions=mlrb

set list
" set listchars=tab:>-
set listchars=tab:\┆\ " do not remove end whitespace

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
map <Leader><Leader>n :Fern . -drawer -toggle -reveal=%<CR>
let g:fern#renderer#default#root_symbol = '~ '
let g:fern#renderer#default#leading = '   '
let g:fern#renderer#default#leaf_symbol = ' '
let g:fern#renderer#default#collapsed_symbol = ' + '
let g:fern#renderer#default#expanded_symbol = ' - '
let g:fern#disable_drawer_hover_popup = 1

" function! FernPreviewGetMargins() abort
"     return g:fern#drawer_width
" endfunction

function! FernInit() abort
  nnoremap <buffer><expr>
        \ <Plug>(fern-my-open-expand-collapse)
        \ fern#smart#leaf(
        \   "\<Plug>(fern-action-preview:close) \| \<Plug>(fern-action-open:select)",
        \   "\<Plug>(fern-action-expand)",
        \   "\<Plug>(fern-action-collapse)",
        \ )
  nnoremap <buffer> <CR> <Plug>(fern-my-open-expand-collapse)
  nnoremap <buffer> <nowait> < <Plug>(fern-action-collapse)
  nnoremap <buffer> <nowait> > <Plug>(fern-action-open-or-expand)
  nnoremap <buffer> p <Plug>(fern-action-preview:auto:toggle)
  nnoremap <buffer> q <Plug>(fern-action-preview:auto:disable) \| <Plug>(fern-action-preview:close)
  nnoremap <buffer> <C-f> <Plug>(fern-action-preview:scroll:down:half)
  nnoremap <buffer> <C-d> <Plug>(fern-action-preview:scroll:up:half)
  " let g:fern_preview_window_calculator.left = function('FernPreviewGetMargins')
endfunction

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
" let g:miniBufExplMaxSize = 1
" let g:miniBufExplBuffersNeeded = 1
let g:buftabline_numbers = 2
let g:buftabline_indicators = 1
let g:buftabline_separators = 1

" Support tagbar plugin
nnoremap <Leader>t :TagbarToggle<CR>
let g:tagbar_ctags_bin = 'ctags'
let g:tagbar_width = 35 " default is 40
let g:tagbar_iconchars = ['▸', '▾']

" Support Auto-Format plugin
nnoremap <Leader>f :Autoformat<CR>
vnoremap <Leader>f :Autoformat<CR>
" let g:formatdef_my_custom_cs = '"clang-format -style=file"'
let g:formatdef_terraform_format = '"tofu fmt -"'
let g:formatdef_jsonnet_format = '"jsonnetfmt -"'
let g:formatters_jsonnet = ['jsonnet_format']
let g:formatdef_my_custom_cs = '"astyle --options=~/.astylerc"'
let g:formatters_cs = ['my_custom_cs']
let g:formatdef_ruff_format = '"ruff --config line-length=80 format - --no-cache --range " . a:firstline . ":" . a:lastline'
let g:formatdef_ruff_check = '"ruff check - --no-cache --silent --select I --fix"'
let g:formatters_python = ['ruff_check', 'ruff_format']
let g:run_all_formatters_python = 1
let g:autoformat_autoindent = 0
let g:autoformat_retab = 0
" let g:autoformat_remove_trailing_spaces = 0
" autocmd BufWrite *.rs :Autoformat

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

function! UserIgnorePattern(regex_cmd) abort
    let l:ignore_arg = get({
        \ 'ag': ' --ignore ',
        \ 'rg': ' --glob !',
        \ }, a:regex_cmd, "")
    let l:ignore_patterns = [
        \ ".git", ".svn", ".hg",
        \ ".npm", "*.sw?", "~$*", "*.py[co]", "*.cache",
        \ "*.o", "*.d", "*.su", "*.obj", "*.so", "*.dll", "*.a", "*.bin", "*.hex", "*.exe",
        \ "*.tmp", "tags", "*.out*", "*.bak", "*.log", "GPATH", "GRTAGS", "GTAGS"
        \ ]
    return empty(l:ignore_arg) ? '' : l:ignore_arg .. join(l:ignore_patterns, l:ignore_arg)
endfunction

function! LeaderfSearchMode(cur_mode, cur_word) abort
    let l:option = '--bottom --stayOpen --auto-preview --preview-position=right rg'
    if a:cur_mode < 2 && len(a:cur_word) < 5
        return ('Leaderf --regexMode ' .. l:option)
    else
        return ('Leaderf! ' .. l:option .. (a:cur_mode < 2 ? ' -w' : '')
                \ .. ' -F -M=80 -e ' .. a:cur_word)
    endif
endfunction

let g:Lf_HideHelp = 1
let g:Lf_RootMarkers = ['tags', 'cscope.out', 'GTAGS', '.git', '.svn', '.hg']
let g:Lf_ExternalCommand = 'rg %s --files-with-matches --hidden --no-messages
    \ --no-ignore --no-require-git --sort=path' .. UserIgnorePattern("rg")
let g:Lf_CommandMap = {'<C-Down>': ['<C-f>'], '<C-Up>': ['<C-d>']}
let g:Lf_NormalCommandMap = {"*": {"<C-Down>": "<C-f>", "<C-Up>":   "<C-d>"}}
" let g:Lf_PreviewInPopup = 0
let g:Lf_PreviewScrollStepSize = 5
let g:Lf_Rg = 'rg --trim --sort=path --hidden --no-ignore --column
    \ --max-columns-preview' .. UserIgnorePattern("rg")
let g:Lf_Ctags=""
let g:Lf_MruEnable = 0
let g:Lf_PopupPalette = {'dark': {'Lf_hl_popupBorder': {'ctermfg': 'NONE'}}}
let g:Lf_ShowDevIcons = 0
let g:Lf_GitFolderIcons = { 'open': '+', 'closed': '-' }
let g:Lf_GitAddIcon = 'A'
let g:Lf_GitDelIcon = 'D'
let g:Lf_GitModifyIcon = 'M'
let g:Lf_GitRenameIcon = 'R'
let g:Lf_GitCopyIcon = 'Y'
let g:Lf_GitUntrackIcon = 'U'
let g:Lf_GtagsSource = 2
let g:Lf_GtagsStoreInProject = 1
let g:Lf_GtagsfilesCmd = {
        \ '.git': 'git ls-files --recurse-submodules',
        \ '.hg': 'hg files',
        \ 'default': 'rg --no-messages --hidden --no-ignore --files' .. UserIgnorePattern("rg")
        \}
" adjust these two configuration accordingly based on your linux distribution
" find more information in `man gtags` or 'gtags.conf', here is for Debian
let g:Lf_Gtagsconf = '/etc/gtags/gtags.conf' " can be /usr/share/gtags/gtags.conf in Archlinux
let g:Lf_Gtagslabel = 'universal-ctags'

nnoremap <silent> <C-p> :<C-u>Leaderf --bottom
    \ --auto-preview --preview-position=right file<CR>
nnoremap <silent> <Leader><Leader>e :<C-u><C-r>=LeaderfSearchMode(0, leaderf#Rg#getPattern(0))<CR><CR>
vnoremap <silent> <Leader><Leader>e :<C-u><C-r>=LeaderfSearchMode(2, leaderf#Rg#getPattern(2))<CR><CR>

" Support for easy motion
" let g:EasyMotion_do_mapping = 0 " Disable default mappings
" let g:EasyMotion_smartcase = 1 " Turn on case insensitive feature
" nnoremap s <Plug>(easymotion-sn)
let g:sneak#label = 1
" let g:sneak#s_next = 1
let g:sneak#prompt = 'SneakMotion: '
" set searchlength to 99 is big enough to wait for Enter key pressing
nnoremap <silent> s :<c-u>call sneak#wrap('', 99, 0, 2, 1)<CR>
nnoremap <silent> S :<c-u>call sneak#wrap('', 99, 1, 2, 1)<CR>

" Support Hexmode plugin
let g:hexmode_patterns = '*.bin,*.exe,*.dat,*.o'
let g:hexmode_xxd_options = '-g 1'

" Support for Vim-Dict plugin
" let g:trans_bin = "/usr/bin"
nnoremap <silent> <Leader><Leader>t :Trans --from-vim<CR>
vnoremap <silent> <Leader><Leader>t :Trans --from-vim<CR>

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
" let g:matchup_matchparen_enabled = 0
let g:matchup_matchparen_offscreen = {'method': 'popup', 'highlight': 'User1'}

" configuration for vim-table-mode
" autocmd BufEnter *.md let g:table_mode_corner='|'
let g:table_mode_corner='|'
function! UserInsertTable(...) abort
    let l:args = filter(copy(a:000), 'v:val =~ ''\d\+''')
    let l:table_line = max([3, str2nr(get(l:args, 0))])
    let l:table_col  = max([3, str2nr(get(l:args, 1))])
    let l:out_string_list = repeat(
        \ [repeat(g:table_mode_corner .. "   ", l:table_col) .. g:table_mode_corner],
        \ l:table_line)
    silent! call insert(
        \ l:out_string_list,
        \ repeat(g:table_mode_corner .. "---", l:table_col) .. g:table_mode_corner,
        \ 1)
    silent! call appendbufline(bufnr(), line("."), l:out_string_list)
    silent! execute "TableModeEnable"
endfunction
command! -nargs=* TableAddNew call UserInsertTable(<f-args>)

" configuration for rust.vim
" let g:rustfmt_autosave = 1

" configuration for coc.nvim
" let g:lsp_cxx_hl_use_text_props = 1
nnoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
nnoremap <silent><nowait><expr> <C-d> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-d>"
inoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? "\<C-R>=coc#float#scroll(1)\<CR>" : "\<Right>"
inoremap <silent><nowait><expr> <C-d> coc#float#has_scroll() ? "\<C-R>=coc#float#scroll(0)\<CR>" : "\<Left>"
vnoremap <silent><nowait><expr> <C-f> coc#float#has_scroll() ? coc#float#scroll(1) : "\<C-f>"
vnoremap <silent><nowait><expr> <C-d> coc#float#has_scroll() ? coc#float#scroll(0) : "\<C-d>"
nnoremap <silent><nowait><expr> <C-]> cscope_connection() ? "\<C-]>" : "\<Plug>(coc-definition)"
" nnoremap <silent><nowait><expr> <C-t> cscope_connection() ? "\<C-t>" : "\<Plug>(coc-references)"
nnoremap <silent><nowait><expr> <C-t> cscope_connection() ? "\<C-t>" : "\<C-o>"

nnoremap <Leader><Leader>k :CocCommand document.toggleInlayHint<CR>
inoremap <silent><expr> <Tab> get(b:, 'table_mode_active', 0) > 0 ?
            \ '<C-O>:execute "normal \<Plug>(table-mode-motion-right)"<CR>'
            \ : pumvisible() ? "\<C-n>" : len(pum_getpos()) ? "\<C-n>" : "\<C-x><C-k>"
function! CocJumpErrorOrHover() abort
    if get(b:, 'table_mode_active', 0) > 0
        execute "normal \<Plug>(table-mode-motion-right)"
    elseif get(g:, 'did_coc_loaded', 0) > 0
        if !(CocAction('hasProvider', 'hover') && call("CocAction", ['definitionHover', ['float']]))
            execute "normal \<Plug>(coc-codeaction-cursor)"
        endif
    endif
endfunction
nnoremap <silent> <Tab> :call CocJumpErrorOrHover()<CR>

" vnoremap <leader>a <Plug>(coc-codeaction-selected)
" nnoremap <leader>a <Plug>(coc-codeaction-selected)
let g:coc_global_extensions = [
        \ "coc-biome", "coc-markdownlint", "coc-rust-analyzer", "coc-xml",
        \ "coc-yaml", "coc-sh", "coc-spell-checker", "coc-highlight",
        \ "coc-pyright", "coc-clangd", "coc-pairs", "coc-json", "coc-go",
        \ "coc-vimlsp"
        \]
" Remove plugins not explicitly defined in g:coc_global_extensions
" Ignore special case: friendly-snippets, coc-vim-source-requirements
function! CocClean() abort
    if get(g:, 'did_coc_loaded', 0) == 0
        return
    endif

    let g:extensions_to_clean = CocAction("loadedExtensions")
        \ ->filter({idx, extension -> extension !~ 'friendly-snippets'})
        \ ->filter({idx, extension -> extension !~ 'coc-vim-source-requirements'})
        \ ->filter({idx, extension -> index(g:coc_global_extensions, extension) == -1})
    if len(g:extensions_to_clean)
        exe 'CocUninstall' join(map(g:extensions_to_clean, {_, line -> split(line)[0]}))
    endif
endfunction
command! -nargs=0 CocClean :call CocClean()

" display 8 lines in prefix window to display command output
let g:asyncrun_open = 8









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

" display vim status
" Plug 'vim-airline/vim-airline'
" Plug 'vim-airline/vim-airline-themes'

" display whitespace
" Plug 'bronson/vim-trailing-whitespace'
Plug 'ntpeters/vim-better-whitespace'

" use mini-buffer window to display select function
" this plugin broke command `20 split README.md`
" Plug 'fholgado/minibufexpl.vim'
Plug 'ap/vim-buftabline'

" use tagbar to display current status
" Plug 'majutsushi/tagbar'
Plug 'preservim/tagbar'
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
" Plug 'ludovicchabant/vim-gutentags'
" Plug 'skywind3000/gutentags_plus'
" Plug 'vim-syntastic/syntastic'
" Plug 'dense-analysis/ale'
Plug 'vim-autoformat/vim-autoformat'

" auto add delimite
" Plug 'Raimondi/delimitMate'
" Plug 'cohama/lexima.vim'

" fuzzy search using Ctrl-P
" Plug 'ctrlpvim/ctrlp.vim'
Plug 'Yggdroot/LeaderF'

" Support open and edit hex file
Plug 'fidian/hexmode'

" use network dictionary for words
Plug 'echuraev/translate-shell.vim'

" use easy motion for fast jump
" Plug 'easymotion/vim-easymotion'
Plug 'justinmk/vim-sneak'

" use reversion manage tool
" Plug 'vim-scripts/vcscommand.vim'
" Plug 'tpope/vim-fugitive'

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
" gl for right-align and gL for left-align operator
Plug 'tommcdo/vim-lion'

" color for c/c++ code
" Plug 'octol/vim-cpp-enhanced-highlight'
" Plug 'bfrg/vim-cpp-modern'
Plug 'sheerun/vim-polyglot'

" use % to match keywords
Plug 'andymass/vim-matchup'

" use onedark colorscheme
Plug 'rafi/awesome-vim-colorschemes'

" display git info
" Plug 'airblade/vim-gitgutter'

" auto generate table in vim
Plug 'dhruvasagar/vim-table-mode'

" vim-8 rust plugin to support hilighting, formating, Syntastic
" Plug 'rust-lang/rust.vim'

" split long line to multiple line by gS or gJ for the opposite
" Plug 'AndrewRadev/splitjoin.vim'

" run command aysnc in backgroup
Plug 'skywind3000/asyncrun.vim'













" Initialize plugin system
call plug#end()



silent! colorscheme one-dark
" autocmd BufEnter *.txt colorscheme github
" autocmd BufEnter *.log colorscheme github
" autocmd BufEnter *.md  colorscheme github

" autocmd BufEnter *.txt set spell spelllang=en_gb
" autocmd BufEnter *.log set spell spelllang=en_gb
" autocmd BufEnter *.md  set spell spelllang=en_gb

" https://www.ditig.com/256-colors-cheat-sheet
highlight Comment ctermfg=lightgreen guifg=green
highlight Visual cterm=underline,standout ctermfg=red ctermbg=lightred
highlight Search cterm=bold ctermfg=yellow ctermbg=gray

highlight DiffAdd    cterm=none ctermfg=143 ctermbg=232
highlight DiffDelete cterm=none ctermfg=143 ctermbg=232
highlight DiffChange cterm=none ctermfg=NONE ctermbg=60
highlight DiffText   cterm=none ctermfg=194  ctermbg=29

" add crosshair style cursor
highlight CursorLine cterm=reverse ctermbg=NONE ctermfg=NONE
highlight CursorColumn cterm=reverse ctermbg=NONE ctermfg=NONE
highlight LineNr cterm=NONE ctermfg=240 ctermbg=NONE
highlight CursorLineNr cterm=bold,underline ctermfg=153 ctermbg=NONE
highlight ColorColumn cterm=reverse ctermbg=NONE ctermfg=NONE
highlight SignColumn cterm=NONE ctermbg=NONE ctermfg=NONE
highlight VertSplit cterm=bold ctermfg=232 ctermbg=238

" change coc underline highlight
highlight SpecialKey ctermfg=239
highlight CocMenuSel ctermbg=65
highlight CocInlayHint ctermfg=10 ctermbg=242
highlight CocInfoSign cterm=None ctermbg=NONE ctermfg=120
highlight! link CocHintSign CocInfoSign

" https://www.ditig.com/256-colors-cheat-sheet
highlight User1 ctermbg=2   ctermfg=0
highlight User2 ctermbg=12  ctermfg=120
highlight User3 ctermbg=195 ctermfg=168
highlight User4 ctermbg=8   ctermfg=156

highlight MarkWord1  ctermbg=DarkCyan     ctermfg=Black
highlight MarkWord2  ctermbg=Green        ctermfg=Black
highlight MarkWord3  ctermbg=DarkYellow   ctermfg=Black
highlight MarkWord4  ctermbg=LightRed     ctermfg=Black
highlight MarkWord5  ctermbg=DarkRed      ctermfg=Black
highlight MarkWord6  ctermbg=LightBlue    ctermfg=Black

highlight SpellUserDefinedError ctermbg=170 ctermfg=236
highlight! link SpellCheckError None
highlight! link SpellBad SpellCheckError
highlight! link SpellCap SpellCheckError
highlight! link SpellLocal SpellCheckError
