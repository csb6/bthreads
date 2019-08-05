import sys, re
sys.path.append("..")
from bthreads import *

bp = BProgram()

@bthread(bp)
def inputMove(thread):
    while True:
        thread.sync(request=BEvent("getInput"))
        yield
        move = input("Enter move 'x y':")
        thread.sync(request=BEvent("move"+move))
        yield

def match(pattern, string):
    return re.findall(pattern, string)

@bthread(bp)
def legalMove(thread):
    while True:
        thread.sync(wait=BEventSet("isLegal?",
                                   lambda e: match(r'move[0-2] [0-2]$', e.name)))
        yield
        thread.sync(request=BEvent("LegalMove"), block=BEvent("getInput"))
        yield

@bthread(bp)
def illegalMove(thread):
    while True:
        thread.sync(wait=BEventSet("isIllegalX?",
                                   lambda e: match(r'^move[3-9] [0-9]$', e.name) \
                                   or match(r'^move[0-9]+ [3-9]+$', e.name)))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

@bthread(bp)
def illegalNegative(thread):
    while True:
        thread.sync(wait=BEventSet("isNegative?",
                                   lambda e: match(r'^move-[0-9]+ -?[0-9]+$', e.name) \
                                   or match(r'^move-?[0-9]+ -[0-9]+$', e.name)))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

bp.run()
