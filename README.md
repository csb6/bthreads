# Bthreads

This is an implementation of a Behavioral Programming (BP) system in Python.
Unlike other programming paradigms, BP focuses on incrementally adding "rules"
or behaviors that should occur when events that match certain criteria happen.
The program is made of of b-threads, which are blocks of code that can
request an event to happen, block a requested event from happening, or
wait for an event to occur. After any one of these actions, the b-thread
should yield control back to the scheduler, which determines which events,
if any, to trigger. When an event triggers, all of the objects that requested
it or decided to wait for it get notified and regain control, allowing them
to request, wait for, or block more events.

While many BP implementations are fully parallel, this implementation is
single-threaded, making use of Python generators as a sort of coroutine.

## Installation

Just clone this repository. The only file you need is bthreads.py.
Add that to your interpreter's path, and import it like any other
Python module. Feel free to look at/run the example programs
to see the features of the library. Be aware that this is an
experimental project and so subject to unstable changes/bugs.

The module is tested with 3.7.0, but should work with any Python 3
version.

## Usage

Usage is fairly simple. Firstly, you need to create a BProgram object, which
keeps track of the b-threads and schedules/decides which event occurs:

```
from bthreads import *

bp = BProgram()
```

Creating bthreads is as easy as creating normal Python
generators. Just include your BProgram instance as an argument
in the decorator in order to add a new b-thread to it:

```
@bthread(bp)
def sayWorld(thread):
    thread.sync(request=BEvent("World!"))
    yield

bp.run()
```

Output:

```
Event occurred: World!
```

`thread` is a BThread object, representing the state of the b-thread
and also including a handy method, `sync()`, which allows the function
to request or wait for an event of set of events, with an option to
block an event/set of events until that happens (not used here).
`sayWorld` requests an event, yields back control, and since no other
b-thread blocked the request, the event occurs. Here's a slightly more
complex example:

```
@bthread(bp)
def sayWorld(thread):
    thread.sync(request=BEvent("World!"))
    yield

@bthread(bp)
def sayHello(thread):
    thread.sync(request=BEvent("Hello,"), block=BEvent("World!"))
    yield

bp.run()
```

Output:

```
Event occurred: Hello,
Event occurred: World!
```

The sayHello b-thread blocks any event named
"World!" from happening until its requested event, "Hello,", occurs.
Since no other b-thread is blocking "Hello,", it occurs, ending the
temporary block and allowing BEvent("World!") to trigger.

Here's an example involving wait:

```
@bthread(bp)
def sayWorld(thread):
    thread.sync(request=BEvent("World!"))
    yield

@bthread(bp)
def sayHello(thread):
    thread.sync(request=BEvent("Hello,"), block=BEvent("World!"))
    yield

@bthread(bp)
def sayGodForsaken(thread):
    thread.sync(wait=BEvent("Hello,"))
    yield
    thread.sync(request=BEvent("God-forsaken"), block=BEvent("World!"))
    yield

bp.run()
```

Output:

```
Event occurred: Hello,
Event occurred: God-forsaken
Event occurred: World!
```

The third b-thread waits until the "Hello," event occurs.
When it occurs, it is given back control, causing it to
request a new event, "God-forsaken" and block "World!"
until "God-forsaken" occurs. Since no other b-thread is
blocking it, "God-forsaken" occurs, thus lifting the
block on "World!", which then occurs.

This is a really powerful way of programming, even though
it seems kind of verbose for such a simple task as printing
out one's dissatisfaction with Planet Earth. But it becomes more
useful when you think about adding to existing programs.

Say you just had the first snippet running, containing the "Hello,"
b-thread, but you didn't have access to the source code.
Replicating the second snippet would be pretty easy without
knowing the old code; you can see from the event log
that "Hello," occurs and then the program ends. You can
simply add another b-thread that requests a new event, blocking
"Hello," until it happens, in order to change the behavior.

Going from the second to the third snippet is similar. Just
look at the event log, see what events you need to wait
for in order to insert your new event, and request it while
blocking the next event, "World!"

By building new "rules" or behaviors like this, one on top the other,
without necessarily understanding all the prior code, you can create
immensely complex behavior with simple rules that basically say:
"Do this thing after this event happens, and block this other
event until you do it." or "Request this thing to happen."

I hope that you find this project interesting!
