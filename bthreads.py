"""
    File: b-threads.py
    Author: Cole Blakley
    Purpose: Implementation of b-threads, a form of append-only programming.
        Supports yielding functions which propose, wait for, or block events from
        being added to an event queue.

TODO:
[X] Add support for predicates for wait/block (but not request)
[X] Instead of matching using strings, match with some compound object
[X] Add decorator to simplify adding b-threads
[ ] Add support for model checking; see https://bpjs.readthedocs.io/en/develop/verification/index.html
"""
import sys, logging
#Set level to logging.DEBUG to see debug messages
logging.basicConfig(level=logging.INFO)

class BEvent:
    #Shortcut callbacks for BEventSet's predicate
    ALL = lambda e: True #Match with all events
    NONE = lambda e: False #Match with no events
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __repr__(self):
        return "Event:" + self.name


class BEventSet:
    def __init__(self, name, predicate):
        self.name = name
        if type(predicate) != list:
            self.predicate = predicate #Boolean function determining what's in set
        else:
            #Shortcut for having explicit list of matching events
            self.predicate = lambda e, lst=predicate: e in lst

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def __contains__(self, other):
        return self.predicate(other)

    def __repr__(self):
        return "EventSet:" + self.name


class BThread:
    def __init__(self, name, callback, program):
        self.name = name
        self.program = program #BProgram this thread belongs to
        self.blocking = [] #All events currently being blocked by this object
        self.callback = callback(self)

    def __eq__(self, other):
        return type(self) == type(other) and self.name == other.name

    def sync(self, wait="", request="", block=""):
        self.program.sync(self, wait, request, block)

    def update(self):
        try:
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
    def __init__(self):
        self.threads = [] #b-threads not currently waiting for an event
        self.requests = [] #Proposed events
        self.queue = [] #Approved requests; list of events to execute
        self.waiters = {} #eventName: [threads waiting for event]
        self.waiterSets = [] #Waiters that are BEventSets
        self.blocked = [] #Names of events not currently allowed to occur

    def add_thread(self, callback):
        #Having thread share name means less duplicated/meaningless names
        name = "bt-" + callback.__name__
        if name in [t.name for t in self.threads]:
            print("Error: Name of Thread:", name, "isn't unique")
            sys.exit(1)
        self.threads.append(BThread(name, callback, self))

    def wait(self, trigger, waiter, blockee=""):
        assert type(trigger) in (BEvent, BEventSet), "Trigger " + str(trigger) + "is not a BEvent/Set"
        assert type(blockee) in (BEvent, BEventSet) or blockee == "", "Blockee " \
            + str(blockee) + "is not a BEvent"
        assert type(waiter) == BThread, "Waiter " + str(waiter) + "is not a BThread"
        logging.debug(waiter.name + " is waiting for " + str(trigger))
        if blockee:
            #When waiter who is blocking is triggered, it will remove
            #correct blockee(s) from self.blocked
            logging.debug("  " + waiter.name + " blocked " + str(blockee))
            self.blocked.append(blockee)
            waiter.blocking.append(blockee)
        if type(trigger) == BEvent:
            if trigger.name not in self.waiters.keys():
                self.waiters[trigger.name] = []
            #When waiter is triggered, it will be
            #removed from waiter list
            self.waiters[trigger.name].append(waiter)
        else:
            #When an event in the set is triggered, waiter will be removed
            #from waiter set list
            self.waiterSets.append({"trigger": trigger, "waiters": [waiter]})

        #Since it is now waiting, remove from normal pool of threads
        self.threads.remove(waiter)

    def sync(self, thread, wait, request, block):
        assert not wait or not request, "Can't have request/wait in 1 statement"
        assert wait or request, "Need to request OR wait for something"
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
            if block:
                #Optional event block removed when done waiting
                self.wait(trigger=request, waiter=thread, blockee=block)
            else:
                self.wait(trigger=request, waiter=thread)
        elif wait:
            if block:
                self.wait(trigger=wait, waiter=thread, blockee=block)
            else:
                self.wait(trigger=wait, waiter=thread)

    def notify(self, eventName, waiterList):
        for waiter in waiterList:
            #Remove any corresponding blocks
            #set to expire after wait occurs
            for blockee in waiter.blocking:
                if blockee in self.blocked:
                    self.blocked.remove(blockee)
            waiter.blocking = []
            self.threads.append(waiter)
            waiter.update()

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
        if event.name in self.waiters.keys():
            self.notify(event.name, self.waiters[event.name])
            #Remove the waiters once they've been notified
            del self.waiters[event.name]
        #Finally, notify all waiter objects with matching event sets (if any)
        for i, item in enumerate(self.waiterSets):
            if event in item["trigger"]:
                self.notify(event.name, item["waiters"])
                #Remove the waiters once they've been notified
                del self.waiterSets[i]
                break

    def run(self):
        self.step()
        self.decide()
        logging.debug("--END OF STEP--")
        while self.requests:
            self.step()
            self.decide()
            logging.debug("--END OF STEP--")
