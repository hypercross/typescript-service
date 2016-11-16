import subprocess, sys, json, Queue, threading, os, time, re

try:
    import vim
    in_vim = True
except ImportError:
    in_vim = False

class CmdChannel:
    def __init__(self, cmd):
        cwd = '.'

        if in_vim:
            cwd = vim.eval("getcwd()")

        self.pid = subprocess.Popen(cmd,
                    stdout=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd = cwd)

    def terminate(self):
        self.pid.terminate()

    def process(self):
        self.queue = Queue.Queue()
        t = threading.Thread(target=CmdChannel.worker, args=(self,))
        t.daemon = True
        t.start()

    def worker(self):
        while True:
            line = self.pid.stdout.readline()
            if line == '':
                break
            self.queue.put(line)

    def checkMsgs(self):
        lines = []
        try:
            while True:
                line = self.queue.get(False)
                lines.append(line)
                self.queue.task_done()
        except Queue.Empty:
            return lines
        return lines

    def write(self, content):
        self.pid.stdin.write(content)

    def running(self):
        return self.pid.poll() == None

if in_vim:
    tss = CmdChannel(vim.eval('g:tsserver'))
    tss.process()

tssReqseq = 0

def tssParseLine(line):
    if line.startswith('Content'):
        return None
    line = line.strip()
    if len(line) < 5:
        return None

    return json.loads(line)

def tssHandleAll():
    for line in tss.checkMsgs():
        parsed = tssParseLine(line)
        if parsed == None:
            continue
        tssHandleMsg(parsed)

def tssHandleSeq(seq):
    while tss.running():
        for line in tss.checkMsgs():
            parsed = tssParseLine(line)
            if parsed == None:
                continue
            if not 'request_seq' in parsed:
                continue
            req_seq = parsed['request_seq']
            if req_seq > seq:
                return
            if req_seq < seq:
                continue
            return tssHandleMsg(parsed)
        time.sleep(0.005)

def tssWaitForFileDiag():
    semanticDiag = False
    syntaxDiag = False
    fp = vim.current.buffer.name
    while tss.running() and (semanticDiag == False or syntaxDiag == False):
        for line in tss.checkMsgs():
            parsed = tssParseLine(line)
            if parsed == None:
                continue
            msgType = parsed[u'type']
            if u'event' != msgType:
                continue

            if not 'body' in parsed:
                continue
            body = parsed['body']
            if not 'file' in body:
                continue
            elif body['file'] != fp:
                continue

            eType = parsed[u'event']
            if eType == 'syntaxDiag':
                syntaxDiag = body['diagnostics']
            elif eType == 'semanticDiag':
                semanticDiag = body['diagnostics']

        time.sleep(0.005)

    return tssLoc2Qf(syntaxDiag, fp) or tssLoc2Qf(semanticDiag, fp)

def tssHandleRecent():
    return tssHandleSeq(tssReqseq)

def tssHandleMsg(parsed):
    msgType = parsed[u'type']
    if msgType == 'event':
        msgEvent = parsed[u'event']
        if msgEvent == 'syntaxDiag':
            tssHandleErrMsg(parsed[u'body'])
        elif msgEvent == 'semanticDiag':
            tssHandleErrMsg(parsed[u'body'])
        else:
            print 'unknown event: %s' % msgEvent
            print parsed
    elif msgType == 'response':
        success = parsed[u'success']
        command = parsed['command']
        if not success:
            print parsed['message']
        elif command == 'definition':
            tssHandleDefJump(parsed['body'])
        elif command == 'references':
            tssHandleUsages(parsed['body'])
        elif command == 'completions':
            return tssHandleCompletions(parsed['body'])
        elif command == 'quickinfo':
            return tssHandleQuickinfo(parsed['body'])
        else:
            print 'unknown response: %s' % command
            print parsed

def tssHandleErrMsg(msg):
    print msg

def tssHandleDefJump(msg):
    item = msg[0]
    start = item['start']
    f = item['file']
    vim.command('e %s | call cursor(%d,%d)' % (f, start['line'],start['offset']))

def tssLoc2Qf(msg, fp=None):
    qf = []
    for item in msg:
        start = item['start']
        f = fp or item['file']
        txt = None
        if 'text' in item:
            txt = item['text']
        if 'lineText' in item:
            txt = item['lineText']
        data = {'filename':f,
                   'lnum': start['line'],
                   'col': start['offset']}
        if txt:
            data['text'] = txt
        qf.append(data)
    return qf

def tssHandleUsages(msg):
    qf = tssLoc2Qf(msg['refs'])
    vim.vars['tss_qf'] = qf
    vim.command('call setqflist(g:tss_qf)')
    vim.command('copen')

def tssHandleCompletions(msg):
    completions = []
    for item in msg:
        completions.append({
            'word': item['name'],
            'menu': '%s %s' % (item['kindModifiers'], item['kind'])
        })
    # print completions
    return completions

def tssHandleQuickinfo(msg):
    vim.command('echo \'%s\'' % (msg['displayString']))

def tssReq(cmd, args):
    global tssReqseq
    tssReqseq = tssReqseq + 1
    req = {"type": "request", "seq": tssReqseq, "command": cmd, "arguments":args}
    tssWrite(req)

def tssWrite(req):
    tss.write('%s\n' % json.dumps(req))

def tssOpen():
    if in_vim:
        fp = vim.current.buffer.name
    tssReq('open', {"file": fp})

def tssReload(fp = None):
    if in_vim:
        fp = vim.current.buffer.name
    tssReq('reload', {"file": fp, "tmpfile": fp})

def tssDefinition(fp=None,row=None,col=None):
    if in_vim:
        fp = vim.current.buffer.name
        (row, col) = vim.current.window.cursor
        col = col + 1
    tssReq('definition', {'file': fp, 'line': row, 'offset': col})

def tssQuickinfo(fp=None,row=None,col=None):
    if in_vim:
        fp = vim.current.buffer.name
        (row, col) = vim.current.window.cursor
        col = col + 1
    tssReq('quickinfo', {'file': fp, 'line': row, 'offset': col})

def tssUsages(fp=None,row=None,col=None):
    if in_vim:
        fp = vim.current.buffer.name
        (row, col) = vim.current.window.cursor
        col = col + 1
    tssReq('references', {'file': fp, 'line': row, 'offset': col})

def tssUpdateBuffer():
    if in_vim:
        fp = vim.current.buffer.name
        endLine = int(vim.eval('b:endLine'))
        endPos = int(vim.eval('b:endPos'))
        content = '\n'.join(vim.current.buffer)
        # print '%s, %d, %d, %s' % (fp, endLine, endPos, content)
        tssReq('change', {'file': fp,
                          'line': 1, 'offset': 1,
                          'endLine': endLine, 'endOffset': endPos,
                          'insertString': content})

def tssFindCompletionStart():
    line = vim.current.line
    (row, col) = vim.current.window.cursor 
    start = col
    while start > 0 and re.match('[a-zA-Z]', line[start-1]):
        start = start - 1
    return start

def tssCompletions(fp=None,row=None,col=None,prefix=''):
    if in_vim:
        fp = vim.current.buffer.name
        (row, col) = vim.current.window.cursor
        col = col+1
        prefix = vim.eval('a:base')
        print '%s, %d, %d, %s' % (fp, row, col, prefix)
    tssReq('completions', {'file': fp,
                           'line': row,
                           'offset': col,
                           'prefix': prefix})

def tssFileErr(fp = None):
    if in_vim:
        fp = vim.current.buffer.name
    tssReq('geterr', {"files": [fp], "delay": 0})
