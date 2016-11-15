if exists("g:tsservice_loaded")
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

let g:tsservice_loaded = 1

"callbacks

func tsservice#onOpen()
    python tssOpen()
endfunc

func tsservice#onSave()
    python tssReload()
endfunc

func tsservice#onFileErr()
    python tssFileErr()
    python tssHandleAll()
endfunc
