import unittest
from bthreads import *

class TestBEvents(unittest.TestCase):
    def setUp(self):
        self.eventA = BEvent("addColdWater")
        self.eventB = BEvent("addColdWater")
        self.eventC = BEvent("addHotWater")
        self.setA = BEventSet("addHotWater", lambda e: True)
        self.threadA = BThread("addColdWater", lambda e: True, None)

    def test_eq(self):
        self.assertEqual(self.eventA, self.eventB)

    def test_ne(self):
        self.assertNotEqual(self.eventA, self.eventC)
        self.assertNotEqual(self.eventC, self.setA)
        self.assertNotEqual(self.eventA, self.threadA)

def oneYield(thread):
    yield

def twoYields(thread):
    yield
    yield

class TestBThread(unittest.TestCase):
    def setUp(self):
        self.threadA = BThread("threadA", oneYield, None)
        self.threadB = BThread("threadB", twoYields, None)

    def test_yields(self):
        self.assertTrue(self.threadA.update())
        self.assertFalse(self.threadA.update())

        for i in range(2):
            self.assertTrue(self.threadB.update())
        self.assertFalse(self.threadB.update())

if __name__ == "__main__":
    unittest.main()
