import sys, re
sys.path.append("..")
from bthreads import *

bp = BProgram()

#@addThread(bp)
def inputMove(thread):
    while True:
        thread.sync(request=BEvent("getInput"))
        yield
        move = input("Enter move 'x y':")
        thread.sync(request=BEvent("move"+move))
        yield

def match(pattern, string):
    return re.findall(pattern, string)

def legalMove(thread):
    while True:
        thread.sync(wait=BEventSet("isLegal?", lambda e: match(r'move[0-2] [0-2]$',
                                                                 e.name)))
        yield
        thread.sync(request=BEvent("LegalMove"), block=BEvent("getInput"))
        yield

def illegalMove(thread):
    while True:
        thread.sync(wait=BEventSet("isIllegalX?",
                                   lambda e: match(r'^move[3-9] [0-9]$', e.name) \
                                   or match(r'^move[0-9]+ [3-9]+$', e.name)))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

def illegalNegative(thread):
    while True:
        thread.sync(wait=BEventSet("isNegative?",
                                   lambda e: match(r'^move\-[0-9]+ \-?[0-9]+$', e.name) \
                                   or match(r'^move\-?[0-9]+ \-[0-9]+$', e.name)))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

def main():
    bp.add_thread(inputMove)
    bp.add_thread(legalMove)
    bp.add_thread(illegalMove)
    bp.add_thread(illegalNegative)

    bp.run()

main()
