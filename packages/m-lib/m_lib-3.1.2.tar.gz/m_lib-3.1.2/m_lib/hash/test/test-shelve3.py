#! /usr/bin/env python


from __future__ import print_function
from m_lib.hash import zshelve

db = zshelve.CompressedShelf("dbz", 'c')
db["test"] = "Test Ok!"
db.close()

db = zshelve.CompressedShelf("dbz", 'r')
print(db["test"])
db.close()
