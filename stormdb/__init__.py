#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stormdb/__init__.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------
# This file is part of X4GA
# 
# X4GA is free software: you can redistribute it and/or modify
# it under the terms of the Affero GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# X4GA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with X4GA.  If not, see <http://www.gnu.org/licenses/>.
# ------------------------------------------------------------------------------

"""
Database Wrapper
"""

__author__ = "Fabio Cassini <fabio.cassini@gmail.com>"
__date__ =    "2005/03/10"
__version__ = "0.2"


import pyodbc

try:
    import decimal
    D = decimal.Decimal
    del decimal.Decimal
except:
    D = None

from mx import DateTime

import MySQLdb
import MySQLdb.converters #questo import deve rimanere qui anche se non usato in questo modulo 

if D:
    try:
        import decimal
        decimal.Decimal = D
    except:
        pass

#fix unicode: la funzione character_set_name della connessione ritorna sempre latin-1, anche se è utf-8
_connect_original = MySQLdb.connect
def connect_fixutf(*args, **kwargs):
    connection = _connect_original(*args, **kwargs)
    #TODO FIX UNICODE da modificare per MySql 7.1
    #print 'fix unicode: la funzione character_set_name della connessione ritorna sempre latin-1, anche se è utf-8'
    #print connection.character_set_name()
    connection.set_character_set('utf8')
    return connection
MySQLdb.connect = MySQLdb.Connect = MySQLdb.Connection = connect_fixutf


OPENMODE_READONLY = 0
OPENMODE_WRITE =    1
OPENMODE_STANDARD = OPENMODE_WRITE

JOIN_ALL =          0
JOIN_LEFT =         1
JOIN_RIGHT =        2

ORDER_ASCENDING =   0
ORDER_DESCENDING =  1

__defOpenMode__ =   OPENMODE_STANDARD

DEFAULT_HOSTNAME = "localhost"
DEFAULT_USERNAME = "username"
DEFAULT_PASSWORD = "password"
DEFAULT_DATABASE = None


# ------------------------------------------------------------------------------


def SetDefaultOpenMode(openMode=None):
    global __defOpenMode__
    oldMode = __defOpenMode__
    if openMode is not None:
        if not openMode in (OPENMODE_READONLY, OPENMODE_WRITE):
            raise Exception,\
                  """Open mode type error"""
        __defOpenMode__ = openMode
    return oldMode
    

# ------------------------------------------------------------------------------


from stormdb.db import DB
from stormdb.dbtable import DbTable, SubDbTable, DbMem, SplittedTable,\
     SetForeignKeyTemplate,ClearCache
