Broytman Library for Python.
Author: Oleg Broytman <phd@phdru.name>.
Copyright (C) 1996-2025 PhiloSoft Design.
License: GPL.

For installation instruction see INSTALL.txt.

Content of the library:

defenc.py - get default encoding.

flad/ - Flat ASCII Database. See README-flad.txt.

flog.py - simple file logger.

hash/ - extended disk hashes package. It extends anydbm/whichdb with ZODB and
   MetaKit-based hashes.

lazy/ - lazy evaluation modules - lazy dictionary and lazy import.

mcrypt.py - crypt module supplement function gen_salt().

metaclasses.py - borrowed from Michele Simionato (mis6@pitt.edu)
   to solve "TypeError: metatype conflict among bases".

md5wrapper.py - just an MD5 wrapper.

m_path.py - simple convenient get_homedir().

m_shutil.py - additional shell utilities (currently only mkhier
   function).

net/ftp/ - modules related to FTP - ftpparse (pure-python parser of LIST
   command output) and ftpscan - recursive scanner of FTP directories.

net/sms.py - Send SMS to subscribers of Moscow operators (Beeline, MTS,
   Megafone) using their Web or SMTP gateways.

net/www/ - modules related to Web/HTTP/HTML/XML/DTML/etc.

opdate.py - additional date/time manipulation routines
   In this module Date is a number of days since 1/1/1600 (up to 31 Dec 3999)
   I am not sure about how easy it might be to extend the modules beyond
   these bounds. Time is just a number of seconds since midnight. User can
   add/subtract dates and times, calculate diffs ("how many days, months
   and years passed since 21 Dec 1967?") and so on. DateTime <==> UTC (GMT)
   conversion routines provided, too.
   This module required flognat's strptime.py.

opstring.py - additional string manipulation routines
   (character padding, encoding conversions).

pbar/ - progress bar for tty.

rus/ - work with russian cyrillic - convert text to/from translit.

tty_menu.py - extremely dumb text-mode menus.
