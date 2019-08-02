import sys
sys.path.append("..")
from bthreads import *

bp = BProgram()

@bthread(bp)
def sayWorld(thread):
    thread.sync(request=BEvent("world!"))
    yield

@bthread(bp)
def sayHello(thread):
    thread.sync(request=BEvent("hello"))
    yield

@bthread(bp)
def orderHelloWorld(thread):
    thread.sync(wait=BEventSet("h*", [BEvent("hello"), BEvent("hi")]), \
                block=BEventSet("world*", \
                                lambda e: e.name.startswith("world")))
    yield

@bthread(bp)
def sayComma(thread):
    thread.sync(wait=BEvent("hello"))
    yield
    thread.sync(request=BEvent(", "), block=BEvent("world!"))
    yield

@bthread(bp)
def sayFriends(thread):
    thread.sync(request=BEvent("Friends:"), block=BEvent("hello"))
    yield

bp.run()

