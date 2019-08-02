import sys
sys.path.append("..")
from bthreads import *

def sayWorld(thread):
    thread.sync(request=BEvent("world!"))
    yield

def sayHello(thread):
    thread.sync(request=BEvent("hello"))
    yield

def orderHelloWorld(thread):
    thread.sync(wait=BEventSet("h*", [BEvent("hello"), BEvent("hi")]), \
                block=BEventSet("world*", \
                                lambda e: e.name.startswith("world")))
    yield

def sayComma(thread):
    thread.sync(wait=BEvent("hello"))
    yield
    thread.sync(request=BEvent(", "), block=BEvent("world!"))
    yield

def sayFriends(thread):
    thread.sync(request=BEvent("Friends:"), block=BEvent("hello"))
    yield

def main():
    bp = BProgram()
    bp.add_thread(sayWorld)
    bp.add_thread(sayHello)
    bp.add_thread(orderHelloWorld)
    bp.add_thread(sayComma)
    bp.add_thread(sayFriends)

    bp.run()

main()
