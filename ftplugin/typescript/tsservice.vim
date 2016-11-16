if exists("g:tsservice_disabled")
    finish
endif

if !has('python')
    echo 'python required! typescript-service is disabled'
    let g:tsservice_disabled = 1
    finish
endif

if exists("g:tsservice_loaded")
    if !exists("b:opened")
        call tsservice#initBuffer()
    endif
    finish
endif

let g:tsservice_loaded = 1

if !exists("g:tsserver")
    let g:tsserver = ['node', 'node_modules/typescript/bin/tsserver']
endif

exec 'pyfile ' . expand('<sfile>:p:h') . '/tsservice.py'

func tsservice#updateBuffer()
    let endLine = line('$')
    let endPos = col([endLine, '$'])
    python tssUpdateBuffer()
    let b:endLine = endLine
    let b:endPos = endPos
endfunc

"callbacks

func tsservice#defJump()
    python tssDefinition()
    python tssHandleRecent()
endfunc
"
func tsservice#listUsages()
    python tssUsages()
    python tssHandleRecent()
endfunc

func tsservice#fileErr()
    python tssFileErr()
    let qf = pyeval('tssWaitForFileDiag()')
    call setqflist(qf)
    if len(qf)
        copen
    else
        cclose
    endif
endfunc

func tsservice#complete(findstart, base)
    if a:findstart == 1
        call tsservice#updateBuffer()
        return pyeval('tssFindCompletionStart()')
    else
        python tssCompletions()
        return pyeval('tssHandleRecent()')
    endif
endfunc

func tsservice#setDefaultKeymap()
    nnoremap <buffer> <c-]> :call tsservice#defJump()<CR>
    nnoremap <buffer> <F12> :call tsservice#listUsages()<CR>
endfunc

func tsservice#initBuffer()
    let b:opened = 1
    let b:endLine = line('$')
    let b:endPos = col([b:endLine, '$'])
    python tssOpen()
    if !exists("g:tsservice_disable_keymap")
        call tsservice#setDefaultKeymap()
    endif
    setlocal omnifunc=tsservice#complete
endfunc

call tsservice#initBuffer()

if !exists("g:tsservice_disable_keymap")
    autocmd BufWritePost *.ts call tsservice#updateBuffer() | call tsservice#fileErr()
else
    autocmd BufWritePost *.ts call tsservice#updateBuffer()
endif
