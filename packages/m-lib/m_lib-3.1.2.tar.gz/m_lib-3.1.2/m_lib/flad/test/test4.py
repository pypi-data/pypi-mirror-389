#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import fladc


def test():
   print("Test:", end=' ')
   conf = fladc.load_file("test.cfg")
   print("Ok")

   print("Property 'Type' is", conf["Type"])


if __name__ == "__main__":
   test()
