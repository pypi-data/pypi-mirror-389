#! /usr/bin/env python
"""
   Test N3 to time file reading
"""

from __future__ import print_function
import sys, os
from clock import clock
from m_lib.pbar.tty_pbar import ttyProgressBar


def test():
   print("Test: ", end=' ')
   sys.stdout.flush()

   size = os.path.getsize(sys.argv[1])
   infile = open(sys.argv[1])
   pbar = ttyProgressBar(0, size)

   lines = []
   line = '\n'
   lng = 0

   # This is for DOS - it counts CRLF, which len() counts as 1 char!
   if os.name == 'dos' or os.name == 'nt' :
      dos_add = 1
   else:
      dos_add = 0 # UNIX' and Mac's len() counts CR or LF correct

   while line:
      line = infile.readline()
      lines.append(line)

      lng = lng + len(line) + dos_add
      pbar.display(lng)

   infile.close()
   pbar.erase()

   print("Ok")


if __name__ == "__main__":
   test()
   print("Overall time:", clock())
