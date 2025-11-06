#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import fladc


def test():
   print("Test:", end=' ')
   conf = fladc.load_file("test.cfg", ["Type", "Name"])
   conf.store_to_file("test6.out")
   print("Ok")


if __name__ == "__main__":
   test()
