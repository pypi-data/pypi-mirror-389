#! /usr/bin/env python


from __future__ import print_function
import sys
from time import sleep
from m_lib.pbar.tty_pbar import ttyProgressBar

def test():
   print("Test: ", end=' ')
   sys.stdout.flush()

   x1 = 217
   x2 = 837

   pbar = ttyProgressBar(x1, x2)
   for i in range(x1, x2+1):
      pbar.display(i)
      sleep(0.05)

   pbar.erase()
   print("Ok")


if __name__ == "__main__":
   test()
