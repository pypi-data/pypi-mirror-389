
                 Flat ASCII Database and config files modules

   FLAD is family of modules for manipulating Flat ASCII Databases.
Flat ASCII Database is just a text file with strucrured information. For
example, flad/fladm modules operates on the following files:

   # Global comment/header for the entire file
   # It is possible to insert empty line after header

   Name: Orion
   Type: URL
   URL: http://www.orion.web/

   Name: NRSC
   Type: Med domain
   Domain type: N/A

   Well, I hope you get the idea. The database is just a list of records;
records are key/value pairs separated by key_sep (flad/fladm/fladc default is
": ", fladw default is "=", but this can be easyly changed); records are
usually separated by empty line (fladw use different syntax).

COPYRIGHT and LEGAL ISSUES
   The software is copyrighted and free. All  programs  copyrighted by
PhiloSoft Design. Programs are provided "as-is", without any kind of
warranty.
   #include "disclaimer.h"

-------------------------------- flad --------------------------------

   flad.py defines the base object, Flad. The object is real FLADatabase,
and it serves as parent for most FLAD objects. This object provides
framework for checking (during append/insert operations) every record. The
module itself is not using it, but fladm (see below) make use of the
feature.
   The database is a list (UserList, actually) of records, where every
record is just a dictionary mapping keys to values. Keys and values are
just strings (this is not enforced; loading from file create a dictionaries
of string, after loading user can add/change values; but storing to file
routines are expecting string values again).

-------------------------------- fladm -------------------------------

   fladm.py defines the object Flad_WithMustKeys. This is inherently FLAD
with restriction. User should define two set of keys - keys that must be in
every record, and keys that can be. If there are no "must" keys - "other"
keys don't matter. If there are "must" keys, but not "other" keys - every
"must" key must be in every record, but any record can contain any key. If
there are both "must" keys and "other" keys - every record must contain all
"must" keys and some or all of "other" keys, but not other. To create
database with only "must" keys, make "other" keys empty list - []!

-------------------------------- fladc -------------------------------

   fladc.py defines the object Flad_Conf. This is FLAD object to manipulate
config files. Config file is just a FLAD file with EXACTLY one record - one
dictionary of properties, that can be used to query and store properties.
The resulting dictionary can be saved as FLAD file.

-------------------------------- fladw -------------------------------

   fladw.py defines object Flad_WIni to retrieve, manipulate and store
WIN.INI-like files.
   General rules for the object is the same - there are routines to load it
from file and store back, but algorithms are quite different. Records are
sections; sections are separated by section names - [section_name], e.g.
   Every record in Flad_WIni is tuple
(section_name_string, [list_of_comments_and_keys], {dict_of_key-to-value_mapping}).
   There are procedures to add/remove sections, add/del/change/query key values.
