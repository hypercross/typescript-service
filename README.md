## typescript-service

Another typescript service plugin for vim.
Why another? Because I can't get the other two to work nicely:

- typescript-tools: https://github.com/clausreinke/typescript-tools
    - not up to date, not actively developed
    - has a custom ts server, more work needed to keep up with newer ts versions
    - bug with tsconfig.json
- tsuquyomi: https://github.com/Quramy/tsuquyomi
    - vimproc dependency, no thanks Shougo I have neovim/vim8
    - before each omni-completion, buffer is written to a file for tsserver reload. Seriously?
    - slightly too many Japanese spellings

So this is me trying to whip together something that works for myself.

features(for now):
```
" jump to definition
nnoremap <buffer> <c-]> :call tsservice#defJump()<CR>

" list occurences in quickfix
nnoremap <buffer> <F12> :call tsservice#listUsages()<CR>

" omnicomplete
set omnifunc=tsservice#complete

" list syntax/semantic diagnostics in quickfix
autocmd BufWritePost *.ts call tsservice#fileErr()
```
