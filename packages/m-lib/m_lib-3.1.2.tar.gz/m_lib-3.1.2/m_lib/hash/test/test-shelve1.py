#! /usr/bin/env python


import shelve

db = shelve.open("db", 'c')
db["test"] = "Test Ok!"
db.close()
