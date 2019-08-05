import sys
sys.path.append("..")
from bthreads import *
bp = BProgram()

@bthread(bp)
def enterMove(thread):
    while True:
        thread.sync(request=BEvent("enterMove"))
        yield
        coords = input("Enter coords 'x y':")
        thread.sync(request=BEvent("move"+coords))
        yield

@bthread(bp)
def endTurn(thread):
    isBlueTurn = True
    while True:
        thread.sync(wait=BEventSet("moves", lambda e: e.name.startswith("move")))
        yield
        if isBlueTurn:
            thread.sync(request=BEvent("BlueTurn"))
        else:
            thread.sync(request=BEvent("RedTurn"))
        isBlueTurn = not isBlueTurn
        yield

@bthread(bp)
def switchTurn(thread):
    while True:
        thread.sync(wait=BEventSet("moves", lambda e: e.name.startswith("move")))
        yield
        thread.sync(wait=BEventSet("turnEnded?", lambda e: e.name.endswith("Turn")), block=BEvent("enterMove"))
        yield

bp.run()
