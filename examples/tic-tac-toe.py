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
        if len(coords) == 2 and all([i.isnumeric() for i in coords]):
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
                                   needs=["coords"]))
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
                                   needs=["coords"]))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

@bthread(bp)
def illegalNegative(thread):
    while True:
        thread.sync(wait=BEventSet("isNegative?",
                                   lambda e: e.name == "move"\
                                   and (e["coords"][0] < 0 or e["coords"][1] < 0), \
                                   needs=["coords"]))
        yield
        thread.sync(request=BEvent("IllegalMove"), block=BEvent("getInput"))
        yield

@bthread(bp)
def switchTurn(thread):
    isXTurn = True
    thread.sync(request=BEvent("isXTurn"), block=BEvent("getInput"))
    yield
    while True:
        thread.sync(wait=BEvent("LegalMove"))
        yield
        turn = None
        if isXTurn:
            turn = BEvent("XTookTurn")
            turn["player"] = "X"
        else:
            turn = BEvent("OTookTurn")
            turn["player"] = "O"
        turn["coords"] = thread.lastEvent["coords"]
        thread.sync(request=turn, block=BEvent("getInput"))
        isXTurn = not isXTurn
        yield

@bthread(bp)
def trackPositions(thread):
    xMoves = []
    oMoves = []
    while True:
        thread.sync(wait=BEventSet("turnTaken", lambda e: e.name.endswith("TookTurn")))
        yield
        coords = thread.lastEvent["coords"]
        player = thread.lastEvent["player"]
        if coords in xMoves or coords in oMoves:
            thread.sync(request=BEvent("OccupiedSpace"), block=BEvent("getInput"))
        else:
            success = BEvent("MovedSuccessfully")
            if player == "X":
                xMoves.append(coords)
                success["moves"] = xMoves
            else:
                oMoves.append(coords)
                success["moves"] = oMoves
            success["player"] = player
            thread.sync(request=success, block=BEvent("getInput"))
        yield

@bthread(bp)
def determineWin(thread):
    while True:
        thread.sync(wait=BEvent("MovedSuccessfully"))
        yield
        moves = thread.lastEvent["moves"]
        player = thread.lastEvent["player"]
        winner = False
        for coordSet in ([c[0] for c in moves], [c[1] for c in moves]):
            for uniqCoord in set(coordSet):
                if coordSet.count(uniqCoord) == 3:
                    winner = True
                    break
        if winner:
            win = BEvent(player + "Won")
            win["player"] = player
            thread.sync(request=win, block=BEvent("getInput"))
        yield

@bthread(bp)
def endGame(thread):
    thread.sync(wait=BEventSet("victory", lambda e: e.name.endswith("Won")))
    yield
    sys.exit(0)

bp.run()
