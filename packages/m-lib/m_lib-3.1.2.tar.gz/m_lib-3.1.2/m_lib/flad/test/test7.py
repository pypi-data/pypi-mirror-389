#! /usr/bin/env python


from __future__ import print_function
from m_lib.flad import fladw


def test():
   print("Test:", end=' ')
   ini = fladw.load_file("C:\\WINDOWS\\WIN.INI")
   ini.store_to_file("test7.out")
   print("Ok")

   print("windows/BorderWidth =", ini.get_keyvalue("windows", "BorderWidth"))


if __name__ == "__main__":
   test()
