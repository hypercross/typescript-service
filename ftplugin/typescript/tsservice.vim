if exists("g:tsservice_loaded")
    if !exists("b:opened")
        let b:opened = 1
        python tssOpen()
    endif
    finish
endif

if !has('python')
    echo 'python required'
    finish
endif

if !exists("g:tsserver")
    let g:tsserver = ['node', 'node_modules/typescript/bin/tsserver']
endif

exec 'pyfile ' . expand('<sfile>:p:h') . '/tsservice.py'
python tssOpen()
let b:opened = 1

let g:tsservice_loaded = 1

"callbacks

func tsservice#defJump()
    python tssDefinition()
    python tssHandleSeq(tssReqseq)
endfunc
"nnoremap <c-]> :call tsservice#defJump()<CR>

autocmd BufWritePost *.ts python tssReload()
