import sys
sys.path.append("..")
from bthreads import *

bp = BProgram()

@threadFor(bp)
def sayWorld(thread):
    thread.sync(request=BEvent("world!"))
    yield

@threadFor(bp)
def sayHello(thread):
    thread.sync(request=BEvent("hello"))
    yield

@threadFor(bp)
def orderHelloWorld(thread):
    thread.sync(wait=BEventSet("h*", [BEvent("hello"), BEvent("hi")]), \
                block=BEventSet("world*", \
                                lambda e: e.name.startswith("world")))
    yield

@threadFor(bp)
def sayComma(thread):
    thread.sync(wait=BEvent("hello"))
    yield
    thread.sync(request=BEvent(", "), block=BEvent("world!"))
    yield

@threadFor(bp)
def sayFriends(thread):
    thread.sync(request=BEvent("Friends:"), block=BEvent("hello"))
    yield

bp.run()

