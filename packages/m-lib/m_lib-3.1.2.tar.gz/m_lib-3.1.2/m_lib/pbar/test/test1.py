#! /usr/bin/env python
"""
   Test N1 to time file reading
"""

from __future__ import print_function
import sys
from clock import clock


def test():
   print("Test: ", end=' ')
   sys.stdout.flush()

   infile = open(sys.argv[1])
   lines = infile.readlines()
   infile.close()

   print("Ok")


if __name__ == "__main__":
   test()
   print("Overall time:", clock())
