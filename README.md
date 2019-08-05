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

## Advanced Usage

While the above examples work well for matching a single
event, what if you wanted to request/wait for a group of
events? That's where `BEventSet` comes in handy. For
example, consider code that reacts to a user entering input:

```
from bthreads import *
bp = BProgram()

@bthread(bp)
def getInput(thread):
    thread.sync(request=BEvent("getInput"))
    yield
    answer = input("Would you like to view a contrived example? [y/n]")
    if answer.lower() == "y":
       thread.sync(request=BEvent("contrivedExample"))
    elif answer.lower() == "n":
       thread.sync(request=BEvent("noExample"))
    yield

@bthread(bp)
def rejectAnswer(thread):
    thread.sync(wait=BEventSet("answers", [BEvent("contrivedExample"), BEvent("noExample")]))
    yield
    thread.sync(request=BEvent("Nevermind"), block=BEvent("getInput"))
    yield

bp.run()
```

Output:

```
Event Occurred: getInput
Would you like to view a contrived example? [y/n]y
Event Occurred: contrivedExample
Event Occurred: Nevermind
```

The first b-thread, `getInput`, requests different events based on the user's
choice. `rejectAnswer` waits for either event to occur, with all the events it
wants to match with in a list within a `BEventSet`. Note that requests can't
use BEventSets; you can only request specific BEvents.

This format works well if you only have a few events, but what if the events
you need to catch have a wide variety of names? Waiting for any event starting
with "movePiece", for example, in a chess program would require you to list all
possible squares on the board! Fortunately, this library has an easier way: predicates.

In addition to accepting lists of BEvent literals, `BEventSet` constructors can
accept a predicate, which is a function that returns True/False if the given
event does/doesn't match the criteria for inclusion in the event set. For example:

```
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
def switchTurn(thread):
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
def endTurn(thread):
    while True:
        thread.sync(wait=BEventSet("moves", lambda e: e.name.startswith("move")))
        yield
        thread.sync(wait=BEventSet("turnEnded?", lambda e: e.name.endswith("Turn")), block=BEvent("enterMove"))
        yield

bp.run()
```

This program allows the user to enter in moves as coordinates, then
alternates between red and blue turns. `switchTurn` waits until any event
with a name starting with "move" to occur, then requests "BlueTurn" or
"RedTurn"; after each loop iteration, a flag is flipped, ensuring that
every time input is entered, the turn switches.

The third bthread, `endTurn`, starting blocking "enterMove", the event
which will trigger another user input, after a move occurs (in the same way
as `switchTurn` does). As soon as `switchTurn` triggers a Blue or RedTurn event,
the block lifts, and "enterMove" can once again happen. This behavior continues
in an infinite loop: enter move, turn is blue/red, turn ends, repeat.

While this example used a short lambda to determine which events belonged in the
event set, any Python function returning True/False would work the same way.
Just pass in the function name as the second argument in `BEventSet()`

I hope you find this project useful and interesting!