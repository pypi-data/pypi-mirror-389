#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import flad


def test():
   print("Test 1:", end=' ')
   datalist = flad.load_from_file("test.txt")
   datalist.store_to_file("test2.o1")
   print("Ok")

   print("Test 2:", end=' ')
   datalist = flad.load_from_file("comment.txt")
   datalist.store_to_file("test2.o2")
   print("Ok")


if __name__ == "__main__":
   test()
