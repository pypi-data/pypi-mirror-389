#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import MKhash


print("Testing (more)...")
db = MKhash.open("db", 'r')
print(len(db))
print(db.keys())
print(db.has_key("test"))
db.close()
