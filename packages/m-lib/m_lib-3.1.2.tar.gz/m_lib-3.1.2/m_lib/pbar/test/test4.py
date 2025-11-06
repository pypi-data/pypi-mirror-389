#! /usr/bin/env python
"""
   Test N4: earse()/redraw()
"""

from __future__ import print_function
import sys
from time import sleep
from m_lib.pbar.tty_pbar import ttyProgressBar


def test():
   sys.stdout.write("Displaying... ")
   sys.stdout.flush()

   pbar = ttyProgressBar(0, 100)
   pbar.display(42)
   sleep(2)
   pbar.erase()

   sys.stdout.write("erasing... ")
   sys.stdout.flush()
   sleep(2)

   sys.stdout.write("redisplaying... ")
   sys.stdout.flush()
   pbar.redraw()
   sleep(2)

   del pbar
   print("Ok")


if __name__ == "__main__":
   test()
