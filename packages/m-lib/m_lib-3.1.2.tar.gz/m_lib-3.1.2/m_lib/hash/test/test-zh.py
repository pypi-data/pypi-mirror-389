#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import ZODBhash


print("Making...")
db = ZODBhash.open("db", 'c')
db["test"] = "Test Ok!"
db.close()

print("Testing...")
db = ZODBhash.open("db", 'w')
print(db["test"])
print(len(db))
print(db.keys())
print(db.has_key("test"))
print(db.has_key("Test"))
print(db.get("test", "Yes"))
print(db.get("Test", "No"))
del db["test"]
db.close()

print("Testing (more)...")
db = ZODBhash.open("db", 'r')
print(len(db))
print(db.keys())
print(db.has_key("test"))
db.close()
