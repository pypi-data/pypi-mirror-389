#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import fladm


def test():
   print("Test:", end=' ')
   datalist = fladm.load_file("test.txt", fladm.check_record, ["Type"], ["Name"])
   datalist.store_to_file("test3.out")
   print("Ok")


if __name__ == "__main__":
   test()
