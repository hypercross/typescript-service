import subprocess, sys, json, Queue, threading, os, time

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
    while True:
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
            tssHandleMsg(parsed)
            return
        time.sleep(0.005)

def tssHandleRecent():
    tssHandleSeq(tssReqseq)

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
        else:
            print 'unknown response: %s' % command
            print parsed

def tssHandleErrMsg(msg):
    print msg

def tssHandleDefJump(msg):
    item = msg[0]
    start = item['start']
    f = item['file']
    vim.command('e +%d %s' % (start['line'], f))

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
    tssReq('definition', {'file': fp, 'line': row, 'offset': col})

def tssUsages(fp=None,row=None,col=None):
    if in_vim:
        fp = vim.current.buffer.name
        (row, col) = vim.current.window.cursor
    tssReq('occurrences', {'file': fp, 'line': row, 'offset': col})

def tssCompletions(fp=None,row=None,col=None):
    if in_vim:
        fp = vim.current.buffer.name
        (row, col) = vim.current.window.cursor
    tssReq('completions', {'file': fp, 'line': row, 'offset': col})

def tssFileErr(fp = None):
    if in_vim:
        fp = vim.current.buffer.name
    tssReq('geterr', {"files": [fp], "delay": 0})
