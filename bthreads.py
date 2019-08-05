"""
    File: b-threads.py
    Author: Cole Blakley
    Purpose: Implementation of b-threads, a form of append-only programming.
        Supports yielding functions which propose, wait for, or block events from
        being added to an event queue.

TODO:
[X] Add some way to assert invariants about data stored in BEvents
[ ] Add support for model checking; see https://bpjs.readthedocs.io/en/develop/verification/index.html
"""
import sys, logging
#Set level to logging.DEBUG to see debug messages
logging.basicConfig(level=logging.INFO)

class BEvent:
    """A triggerable item which can potentially carried data;
    when triggered, waiting BThreads are notified"""
    #Shortcut callbacks for BEventSet's predicate
    ALL = lambda e: True #Match with all events
    NONE = lambda e: False #Match with no events
    def __init__(self, name):
        self.name = name
        self.data = {}

    def __setitem__(self, key, value):
        self.data[key] = value

    def __getitem__(self, key):
        return self.data[key]

    def __contains__(self, key):
        return key in self.data

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __hash__(self):
        return hash((self.name, type(self)))

    def __repr__(self):
        return "Event:" + self.name


class BEventSet:
    """A generalized event which recognizes its members by matching its
       predicate (a boolean lambda)"""
    def __init__(self, name, predicate, keys=[]):
        assert type(keys) == list, "Arg 3 is keys"
        self.name = name
        self.keys = keys #Keys assumed to be in the event's data
        if type(predicate) != list:
            self.predicate = predicate #Boolean function determining what's in set
        else:
            #Shortcut for having explicit list of matching events
            self.predicate = lambda e, lst=predicate: e in lst

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __hash__(self):
        return hash((self.name, type(self)))

    def __contains__(self, event):
        for key in self.keys:
            #Ensure keys used in predicate won't raise KeyError
            if key not in event:
                logging.debug(str(key) + " missing from " + str(event) \
                              + " when checked by " + str(self))
                return False

        return self.predicate(event)

    def __repr__(self):
        return "EventSet:" + self.name


class BThread:
    """Procedure with several steps, each of which yields; acts like
       a coroutine which can request, wait for, or block events from
       happening in its assigned program"""
    def __init__(self, name, callback, program):
        self.name = name
        self.program = program #BProgram this thread belongs to
        self.blocking = [] #All events currently being blocked by this object
        self.callback = callback(self)
        self.lastEvent = None

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def sync(self, wait="", request="", block=""):
        self.program.sync(self, wait, request, block)

    def update(self, lastEvent=None):
        try:
            self.lastEvent = lastEvent
            next(self.callback)
            return True
        except StopIteration:
            return False

    def __repr__(self):
        return "Thread:" + self.name


#Decorator for BProgram.add_thread()
def bthread(program):
    assert program, "Need to specify program for bthread to be added to"
    def decorator(func):
        program.add_thread(func)
    return decorator

class BProgram:
    """Schedules multiple BThreads, blocking/triggering events
       as specified by them"""
    def __init__(self):
        self.threads = [] #b-threads not currently waiting for an event
        self.requests = [] #Proposed events
        self.queue = [] #Approved requests; list of events to execute
        self.waiters = {} #event: [threads waiting for event]
        self.waiterSets = {} #event set: [threads waiting for event set]
        self.blocked = [] #Names of events not currently allowed to occur

    def add_thread(self, callback):
        name = "bt-" + callback.__name__
        if name in [t.name for t in self.threads]:
            print("Error: Name of Thread:", name, "isn't unique")
            sys.exit(1)
        self.threads.append(BThread(name, callback, self))

    def wait(self, trigger, waiter, blockee):
        assert type(trigger) in (BEvent, BEventSet), "Trigger " + str(trigger) \
            + " is not a BEvent/Set"
        assert type(blockee) in (BEvent, BEventSet) or blockee == "", "Blockee " \
            + str(blockee) + "is not a BEvent"
        assert type(waiter) == BThread, "Waiter " + str(waiter) + "is not a BThread"
        assert waiter in self.threads, "Waiter" + str(waiter) + "not in threads list"
        logging.debug(waiter.name + " is waiting for " + str(trigger))
        if blockee:
            #When waiter who is blocking is triggered, it will remove
            #correct blockee(s) from self.blocked
            logging.debug("  " + waiter.name + " blocked " + str(blockee))
            self.blocked.append(blockee)
            waiter.blocking.append(blockee)
        if type(trigger) == BEvent:
            if trigger not in self.waiters.keys():
                self.waiters[trigger] = []
            #When waiter is triggered, it will be
            #removed from waiter list
            self.waiters[trigger].append(waiter)
        else:
            #When an event in the set is triggered, waiter will be removed
            #from waiter set list
            if trigger not in self.waiterSets.keys():
                self.waiterSets[trigger] = []
            self.waiterSets[trigger].append(waiter)

        #Since it is now waiting, remove from normal pool of threads
        self.threads.remove(waiter)

    def sync(self, thread, wait="", request="", block=""):
        assert not wait or not request, "Can't have request/wait in 1 statement"
        assert wait or request or block, "Need to have wait/request/block"
        assert type(request) == BEvent or request == "", "Request needs to be BEvent"
        assert type(wait) in (BEvent, BEventSet) or wait == "", "Wait needs to be BEvent/Set"
        assert type(block) in (BEvent, BEventSet) or block == "", "Block needs to be BEvent/Set"
        assert type(thread) == BThread, "thread must be a BThread"
        if thread not in self.threads:
            print("Unknown thread:", thread.name)
            sys.exit(1)

        if request:
            logging.debug(thread.name + " requested " + str(request))
            self.requests.append(request)
            #Optional block of an event; removed once request or wait is met
            self.wait(trigger=request, waiter=thread, blockee=block)
        elif wait:
            self.wait(trigger=wait, waiter=thread, blockee=block)
        elif block:
            #Permanent blocking of an event; can't be removed
            self.blocked.append(block)

    def notify(self, event, waiterList):
        for waiter in waiterList:
            #Remove any corresponding blocks
            #set to expire after wait occurs
            for blockee in waiter.blocking:
                if blockee in self.blocked:
                    self.blocked.remove(blockee)
            waiter.blocking = []
            self.threads.append(waiter)
            waiter.update(event)

    def step(self):
        #First, allow all threads to make requests, make wait statements,
        #or specify events to block
        self.threads.reverse()
        i = len(self.threads) - 1
        while i >= 0:
            succeeded = self.threads[i].update()
            if not succeeded:
                #When threads end, destroy them
                logging.debug("Destroyed " + self.threads[i].name)
                del self.threads[i]
            i -= 1

        #Then, decide which requested event to trigger
        for i, event in enumerate(self.requests):
            #Check against all current blocked BEvents/BEventSets
            if event not in self.blocked and not any([event in bset for bset in self.blocked \
                                                      if type(bset) == BEventSet]):
                self.queue.append(event)
                del self.requests[i]

        logging.debug(" Requests: " + str(self.requests))
        logging.debug(" Queue: " + str(self.queue))
        logging.debug(" Thread Pool: " + str(self.threads))
        logging.debug(" Waiting Pool: " + str(self.waiters))
        logging.debug(" Waiting Pool of Event Sets: " + str(self.waiterSets))
        logging.debug(" Blocking Pool: " + str(self.blocked))

    def decide(self):
        if not self.queue:
            #If no successful requests, there's nothing
            #to decide on
            return

        event = self.queue.pop(0)
        print("Event Occurred:", event.name)
        #Next, notify all waiter objects for that event (if any)
        if event in self.waiters.keys():
            self.notify(event, self.waiters[event])
            #Remove the waiters once they've been notified
            del self.waiters[event]
        #Finally, notify all waiter objects under matching event sets (if any)
        notifiedSets = [] #Track for bulk removal
        for eventSet, waiters in self.waiterSets.items():
            if event in eventSet:
                self.notify(event, waiters)
                #Remove the waiters once they've been notified
                notifiedSets.append(eventSet)
        for eventSet in notifiedSets:
            del self.waiterSets[eventSet]

    def run(self):
        self.step()
        self.decide()
        logging.debug("--END OF STEP--")
        while self.requests:
            self.step()
            self.decide()
            logging.debug("--END OF STEP--")
