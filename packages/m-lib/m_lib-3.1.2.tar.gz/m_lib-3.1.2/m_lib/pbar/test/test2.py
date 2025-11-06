#! /usr/bin/env python
"""
   Test N2 to time file reading
"""

from __future__ import print_function
import sys
from clock import clock


def test():
   print("Test: ", end=' ')
   sys.stdout.flush()

   infile = open(sys.argv[1])
   lines = []
   line = '\n'
   while line:
      line = infile.readline()
      lines.append(line)
   infile.close()

   print("Ok")


if __name__ == "__main__":
   test()
   print("Overall time:", clock())
