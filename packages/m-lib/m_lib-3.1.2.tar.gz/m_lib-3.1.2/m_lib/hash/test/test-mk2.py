#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import MKhash


print("Testing...")
db = MKhash.open("db", 'w')
print(db["test"])
print(len(db))
print(db.keys())
print(db.has_key("test"))
print(db.has_key("Test"))
print(db.get("test", "Yes"))
print(db.get("Test", "No"))
del db["test"]
db.close()
