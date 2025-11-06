#! /usr/bin/env python


from __future__ import print_function
import shelve

db = shelve.open("db", 'r')
print(db["test"])
db.close()
