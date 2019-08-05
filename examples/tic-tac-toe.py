import sys, re
sys.path.append("..")
from bthreads import *

bp = BProgram()

@bthread(bp)
def inputMove(thread):
    while True:
        thread.sync(request=BEvent("getInput"))
        yield
        coords = input("Enter move 'x y':").split()
        move = BEvent("move")
        if len(coords) == 2:
            move["coords"] = [int(i) for i in coords]
        thread.sync(request=move)
        yield

@bthread(bp)
def legalMove(thread):
    while True:
        thread.sync(wait=BEventSet("isLegal?",
                                   lambda e: e.name == "move" \
                                   and e["coords"][0] in range(3) \
                                   and e["coords"][1] in range(3),\
                                   keys=["coords"]))
        yield
        legalMove = BEvent("LegalMove")
        legalMove["coords"] = thread.lastEvent["coords"]
        thread.sync(request=legalMove, block=BEvent("getInput"))
        yield

@bthread(bp)
def illegalMove(thread):
    while True:
        thread.sync(wait=BEventSet("isIllegalX?",
                                   lambda e: e.name == "move" \
                                   and (e["coords"][0] > 2 or e["coords"][1] > 2),\
                                   keys=["coords"]))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

@bthread(bp)
def illegalNegative(thread):
    while True:
        thread.sync(wait=BEventSet("isNegative?",
                                   lambda e: e.name == "move"\
                                   and (e["coords"][0] < 0 or e["coords"][1] < 0), \
                                   keys=["coords"]))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

@bthread(bp)
def trackOccupied(thread):
    moves = []
    while True:
        thread.sync(wait=BEvent("LegalMove"))
        yield
        coords = thread.lastEvent["coords"]
        if coords in moves:
            thread.sync(request=BEvent("OccupiedSpace"), block=BEvent("getInput"))
        else:
            thread.sync(request=BEvent("MovedSuccessfully"), block=BEvent("getInput"))
            moves.append(coords)
        yield

bp.run()
