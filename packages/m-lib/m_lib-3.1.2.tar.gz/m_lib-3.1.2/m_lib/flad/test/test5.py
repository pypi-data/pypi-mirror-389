#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import fladc


def test():
   print("Test:", end=' ')

   try: # Note! This must raise fladc.error - too many records in the file
      conf = fladc.load_file("test.txt")
   except fladc.error:
      print("Ok")
   else:
      print("Error!")


if __name__ == "__main__":
   test()
