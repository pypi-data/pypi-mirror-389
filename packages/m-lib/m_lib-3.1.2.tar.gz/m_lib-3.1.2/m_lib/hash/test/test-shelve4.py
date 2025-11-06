#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import zshelve

db = zshelve.CompressedKeysShelf("dbz", 'c')
db["test"] = "Test Ok!"
db.close()

db = zshelve.CompressedKeysShelf("dbz", 'r')
print(db["test"])
db.close()
