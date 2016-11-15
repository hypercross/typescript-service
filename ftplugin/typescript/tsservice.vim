if exists("g:tsservice_loaded")
    if !exists("b:opened")
        let b:opened = 1
        let b:endLine = line('$')
        let b:endPos = col([b:endLine, '$'])
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
let b:opened = 1
let b:endLine = line('$')
let b:endPos = col([b:endLine, '$'])
python tssOpen()

func tsservice#updateBuffer()
    let endLine = line('$')
    let endPos = col([endLine, '$'])
    python tssUpdateBuffer()
    let b:endLine = endLine
    let b:endPos = endPos
endfunc

let g:tsservice_loaded = 1

"callbacks

func tsservice#defJump()
    python tssDefinition()
    python tssHandleRecent()
endfunc
nnoremap <c-]> :call tsservice#defJump()<CR>
"
func tsservice#listUsages()
    python tssUsages()
    python tssHandleRecent()
endfunc
nnoremap <F12> :call tsservice#listUsages()<CR>

func tsservice#complete(findstart, base)
    if a:findstart == 1
        call tsservice#updateBuffer()
        return pyeval('tssFindCompletionStart()')
    else
        python tssCompletions()
        return pyeval('tssHandleRecent()')
    endif
endfunc
set omnifunc=tsservice#complete

autocmd BufWritePost *.ts call tsservice#updateBuffer()
