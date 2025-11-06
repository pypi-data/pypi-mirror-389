#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import zshelve

db = zshelve.CompressedKeysShelf("dbz", 'n')
db["test"] = "Test Ok!"
db.close()

db = zshelve.CompressedKeysShelf("dbz", 'r')
print(db.has_key("test"))
print(db.keys())
print(db["test"])
db.close()
