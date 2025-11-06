#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import fladm


def test():
   print
   print("Test 1:", end=' ')
   fladm.load_from_file("test.txt", fladm.check_record, None, None)
   print("Ok")

   print("Test 2:", end=' ')
   fladm.load_from_file("test.txt", fladm.check_record, ["Type"], None)
   print("Ok")

   print("Test 3:", end=' ')
   fladm.load_from_file("test.txt", fladm.check_record, ["Type", "Name"], None)
   print("Ok")

   print("Test 4:", end=' ')
   fladm.load_from_file("test.txt", fladm.check_record, ["Type"], ["Name"])
   print("Ok")

   print("Test 5:", end=' ')
   try: # Note! This must raise KeyError - "Name" key is not listed
      fladm.load_from_file("test.txt", fladm.check_record, ["Type"], [""])
   except KeyError:
      print("Ok")
   else:
      print("Error!")

   print("Test 6:", end=' ')
   fladm.load_from_file("test.txt", fladm.check_record, None, ["Type", "Name"])
   print("Ok")

   print("Test 7:", end=' ')
   try: # Note! This must raise KeyError - "Error" key is listed in must field
      fladm.load_from_file("test.txt", fladm.check_record, ["Error"], ["Type"])
   except KeyError:
      print("Ok")
   else:
      print("Error!")

   print("Test 8:", end=' ')
   datalist = fladm.load_from_file("test.txt", fladm.check_record, None, ["Type", "Name", "Error"])
   print("Ok")

   print("\nLast but not test: just printing loaded list")
   print(datalist)
   print


if __name__ == "__main__":
   test()
