#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import MKhash


print("Making...")
db = MKhash.open("db", 'c')
db["test"] = "Test Ok!"
db.close()
