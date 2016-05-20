#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stormdb/db.py
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


import stormdb
from stormdb import DateTime, MySQLdb, pyodbc,\
     OPENMODE_READONLY, OPENMODE_WRITE, OPENMODE_STANDARD
adodb = None

import re

import base64

__database__ =    None

def GetConnection():
    return __database__

log = False

def setlog(dolog=True):
    global log
    log = dolog

def logmsg(*msgs):
    if not log:
        return
    for msg in msgs:
        print msg


class DbError(object):
    code = 0
    description = ""
    duplicatedKey = False
    exception = None

    def Reset(self):
        self.code =          0
        self.description =   ""
        self.duplicatedKey = False
        self.exception =     None


# ------------------------------------------------------------------------------


class DB(object):
    """
    Manages the database connection.
    Supported databases:
        mysql
        adodb (ms jet)
        odbc

    Class variables::
        DB.dbCon       database connection
        DB.rs          recordset containing the data retrieved by Retrieve()
        DB.recordCount number of records present in recordset
        DB.fieldCount  number of fields present in recordset
        DB.fieldNames  list containing fields present in recordset
    """
    connected   = False      # flag connected
    rs          = ()         # recordset containing data
    recordCount = 0          # number of records in the recordset
    fieldCount  = 0          # number of columns in the recordset
    description = None       # description obtained by specific db cursor
    fieldNames  = []         # list of fieldnames relating to the recordset
    lastrowid   = None       # contains last inserter row id
    dbError     = DbError()  # storage for database errors
    _dbType     = 'mysql'    # database type, default is mysql
    _dbClass    = MySQLdb    # class to use for the database
    _dbCon      = None       # connection object

    TYPES_STRING =   (-1,)
    TYPES_BINARY =   (-1,)
    TYPES_INT =      (-1,)
    TYPES_FLOAT =    (-1,)
    TYPES_DATETIME = (-1,)

    STRMAP_TYPES = {}

    WILDCARD_ONE =   ""
    WILDCARD_ALL =   ""

    DUPKEY_ERRCODE = None

    def __init__(self, dbType='mysql', globalConnection=True,\
                 openMode=OPENMODE_STANDARD):
        """
        Constructor.
        Optional parameters:
            dbType (string) database type (default='mysql')
            globalConnection (boolean) if True makes the instance available
            to the next uses
            openMode (int) tables open mode:
                OPENMODE_READONLY
                OPENMODE_WRITE
        """
        object.__init__(self)
        self._SetDbType(dbType)
        stormdb.SetDefaultOpenMode(openMode)
        if globalConnection:
            stormdb.db.__database__ = self

    def _SetDbType(self, dbType):
        """
        Sets the appropriate class and field types regarding passed type.
        dbType must be a string with the name of database.
        Accepted types are:
            'mysql'
            'adodb'
        """
        self._dbType = dbType
        if dbType == 'mysql':
            self.WILDCARD_ONE = r"_"
            self.WILDCARD_ALL = r"%"
            self._dbClass = MySQLdb
            T = MySQLdb.FIELD_TYPE
            self.TYPES_STRING =   (T.CHAR, T.ENUM, T.STRING, T.VAR_STRING)
            self.TYPES_BINARY =   (T.BLOB, T.LONG_BLOB, T.MEDIUM_BLOB,\
                                   T.TINY_BLOB)
            self.TYPES_INT =      (T.DOUBLE, T.INT24, T.LONG, T.LONGLONG,\
                                   T.TINY, T.YEAR)
            #if hasattr(T, "DECIMAL_50"):
                #self.TYPES_FLOAT = (T.DECIMAL, T.DECIMAL_50, T.FLOAT)
                #self.STRMAP_TYPES[T.DECIMAL_50] = "DECIMAL"
            if hasattr(T, "NEWDECIMAL"):
                self.TYPES_FLOAT = (T.DECIMAL, T.NEWDECIMAL, T.FLOAT)
                self.STRMAP_TYPES[T.NEWDECIMAL] = "DECIMAL"
            else:
                self.TYPES_FLOAT = (T.DECIMAL, T.FLOAT)
            self.TYPES_DATETIME = (T.DATE, T.NEWDATE, T.TIME, T.TIMESTAMP,\
                                   T.DATETIME)

            self.STRMAP_TYPES[T.DECIMAL] =     "DECIMAL"
            self.STRMAP_TYPES[T.TINY] =        "TINYINT"
            #self.STRMAP_TYPES[T.LONG] =        "LONG"
            self.STRMAP_TYPES[T.LONG] =        "INT"
            if hasattr(T, "INTEGER"):
                self.STRMAP_TYPES[T.INTEGER] =  "INT"
            self.STRMAP_TYPES[T.FLOAT] =       "FLOAT"
            self.STRMAP_TYPES[T.DOUBLE] =      "DOUBLE"
            self.STRMAP_TYPES[T.NULL] =        "NULL"
            self.STRMAP_TYPES[T.TIMESTAMP] =   "TIMESTAMP"
            self.STRMAP_TYPES[T.LONGLONG] =    "LONGLONG"
            self.STRMAP_TYPES[T.DATE] =        "DATE"
            self.STRMAP_TYPES[T.DATETIME] =    "DATETIME"
            self.STRMAP_TYPES[T.ENUM] =        "ENUM"
            self.STRMAP_TYPES[T.TINY_BLOB] =   "TINYBLOB"
            self.STRMAP_TYPES[T.MEDIUM_BLOB] = "MEDIUMBLOB"
            self.STRMAP_TYPES[T.LONG_BLOB] =   "LONGBLOB"
            self.STRMAP_TYPES[T.BLOB] =        "BLOB"
            self.STRMAP_TYPES[T.VAR_STRING] =  "VARCHAR"
            self.STRMAP_TYPES[T.STRING] =      "CHAR"
            self.STRMAP_TYPES[T.CHAR] =        "CHAR"

            self.DUPKEY_ERRCODE = 1062

        elif dbType == 'adodb':
            self._dbClass = adodb

        elif dbType == 'odbc':
            self._dbClass = pyodbc

        return self._dbClass

    def Connect(self, **kwargs):
        """
        Connection method.

        Keyword arguments for mysql:
            host   string host name
            user   string user name
            passwd string password
            db     string database name

        Keyword arguments for adodb:
            conn   string connection string
        """
        success = False
        # determine defaults and mandadory keywords for the database
        if self._dbType == 'mysql':
            defargs = {"host":   stormdb.DEFAULT_HOSTNAME,\
                       "user":   stormdb.DEFAULT_USERNAME,\
                       "passwd": stormdb.DEFAULT_PASSWORD,\
                       "db":     stormdb.DEFAULT_DATABASE,\
                       "port":   3306}
            mandKeys = ("host", "user", "passwd", "db")

        elif self._dbType == 'odbc':
            defargs = { "DSN": 'dsn_name', \
                        "autocommit": True}
            mandKeys = ("DSN", "autocommit")

        elif self._dbType == 'adodb':
            defargs = { "connString":\
                        """Provider=Microsoft.Jet.OLEDB.4.0;"""\
                        """Data Source=E:/Mirage/DAT;"""\
                        """Extended Properties=dBASE III;"""\
                        """User ID=Admin;Password=""" }
            mandKeys = ("connString",)

        else:
            raise Exception,\
                  """Unknown db type"""

        for da_name, da_val in defargs.iteritems():
            if not kwargs.has_key(da_name):
                kwargs[da_name] = da_val

        # check for mandatory keywords
        for key in mandKeys:
            if not kwargs.has_key(key):
                raise Exception,\
                      """Missing '%s' parameter""" % key

        # try to establish the connection
        if self._dbType == 'mysql':
            hostname = kwargs['host']
            username = kwargs['user']
            password = kwargs['passwd']
            database = kwargs['db']
            if kwargs['db'] is None:
                kwargs.pop('db')
            kwargs['use_unicode'] = True
            try:
                self._dbCon = self._dbClass.connect(**kwargs)
                self.hostname = hostname
                self.username = username
                self.password = password
                self.database = database
                self._dbCon.autocommit(True)
                success = True
            except MySQLdb.Error, e:
                self._dbCon = None
                self._Error_MySQLdb(e)

        elif self._dbType == 'odbc':

            defargs = { "DSN": 'Test su Mirage', \
                        "autocommit": True}
            DSN = kwargs['DSN']
            autocommit = kwargs['autocommit']
            try:
                self._dbCon = self._dbClass.connect(**kwargs)
                success = True
            except pyodbc.Error, e:
                self._dbCon = None
                self._Error_ODBC(e)

        elif self._dbType == 'adodb':
            try:
                connString = kwargs['connString']
                self._dbCon = self._dbClass.connect(connString)
                self.connString = connString
                success = True
            except adodb.DatabaseError, e:
                self._dbCon = None
                self._Error_AdoDb(e)

        if success:
            self.connected = True

        return success

    def GetConnection(self):
        return self._dbCon

    def Retrieve(self, sql, par=[], asList=True):
        """
        Data retrieving method. This causes to populate the internal
        recordset.
        """
        success = False
        self.dbError.Reset()
        if not self.connected:
            self.dbError.description = "Connection is closed"

        elif self._dbType == 'mysql':
            self.lastInsertedId = None
            try:
                dbCursor = self._dbCon.cursor()
                logmsg('retrieve: %s' % sql)
                logmsg('parameters: %s' % repr(par))
                if len(par) == 0:
                    dbCursor.execute(sql)
                else:
                    dbCursor.execute(sql, par)
                logmsg('done')
                #TODO: per compatibilità con MySql 5.7
                #===============================================================
                # if 'cfgeff' in sql:
                #     for r in dbCursor.description:
                #         print r
                #===============================================================
                rs = dbCursor.fetchall()
                if asList:
                    logmsg('convert to list')
                    self.rs = [list(r) for r in rs]
                    logmsg('conversion done')
                else:
                    self.rs = rs
                self.recordCount = dbCursor.rowcount
                self.description = dbCursor.description
                dbCursor.close()
                success = True
            except MySQLdb.Error, e:
                self._Error_MySQLdb(e)
                self.dbError.exception = e
                self.rs = []
                self.recordCount = 0
                self.description = None
            except Exception, e:
                self.dbError.code = 0
                self.dbError.description = repr(e.args)
                self.dbError.exception = e


        elif self._dbType == 'odbc':
            sql = sql.replace(r'%s', '?')
            self.lastInsertedId = None
            try:
                dbCursor = self._dbCon.cursor()
                logmsg('retrieve: %s' % sql)
                logmsg('parameters: %s' % repr(par))
                if len(par) == 0:
                    dbCursor.execute(sql)
                else:
                    dbCursor.execute(sql, par)
                logmsg('done')
                rs = dbCursor.fetchall()
                if asList:
                    logmsg('convert to list')
                    self.rs = [list(r) for r in rs]
                    logmsg('conversion done')
                else:
                    self.rs = rs
                self.recordCount = dbCursor.rowcount
                self.description = dbCursor.description
                dbCursor.close()
                success = True
            except pyodbc.Error, e:
                self._Error_ODBC(e)
                self.dbError.exception = e
                self.rs = []
                self.recordCount = 0
                self.description = None
            except Exception, e:
                self.dbError.code = 0
                self.dbError.description = repr(e.args)
                self.dbError.exception = e

        elif self._dbType == 'adodb':
            self.lastInsertedId = None
            try:
                dbCursor = self._dbCon.cursor()
                dbCursor.execute(sql)
                rs = dbCursor.fetchall()
                if asList:
                    self.rs = [list(r) for r in rs]
                else:
                    self.rs = rs
                self.recordCount = dbCursor.rowcount
                self.description = dbCursor.description
                dbCursor.close()
                success = True
            except adodb.DatabaseError, e:
                self._Error_AdoDb(e)
                self.rs = []
                self.recordCount = 0
                self.description = None

        return success

    def Reset(self):
        if type(self.rs) is list:
            del self.rs[:]
        else:
            self.rs = ()
        self.recordCount = 0
        self.description = None
        self.dbError.Reset()
        logmsg('reset')

    def Execute(self, sql, par=None):
        """
        Method used for updating/inserting values on the tables based on a
        single list of parameters, if present.
        """
        success = False
        if type(par) is list:
            par = tuple(par)
        self.dbError.Reset()
        if self._dbType == 'mysql':
            try:
                dbCursor = self._dbCon.cursor()
                logmsg('execute: %s' % sql, 'parameters: %s' % repr(par))
                self.recordCount = dbCursor.execute(sql, par)
                logmsg('done')
                self.lastInsertedId = dbCursor.lastrowid
                dbCursor.close()
                del dbCursor
                success = True
            except MySQLdb.Error, e:
                self.recordCount = 0
                self._Error_MySQLdb(e)
                self.dbError.exception = e
            except Exception, e:
                self.recordCount = 0
                self._Error_MySQLdb(e)
                self.dbError.exception = e
            self.description = None

        elif self._dbType == 'odbc':
            try:
                sql = sql.replace(r'%s', '?')
                dbCursor = self._dbCon.cursor()
                logmsg('execute: %s' % sql, 'parameters: %s' % repr(par))
                self.recordCount = dbCursor.execute(sql, par)
                logmsg('done')
                #self.lastInsertedId = dbCursor.lastrowid
                dbCursor.close()
                del dbCursor
                success = True
            except pyodbc.Error, e:
                self.recordCount = 0
                self._Error_ODBC(e)
                self.dbError.exception = e
            except Exception, e:
                self.recordCount = 0
                self._Error_ODBC(e)
                self.dbError.exception = e
            self.description = None

        elif self._dbType == 'adodb':
            try:
                dbCursor = self._dbCon.cursor()
                self.recordCount = dbCursor.execute(sql, par)
                self.lastInsertedId = dbCursor.lastrowid
                dbCursor.close()
                del dbCursor
                success = True
            except adodb.DatabaseError, e:
                self.recordCount = 0
                self._Error_AdoDb(e)
            self.description = None

        return success

    def ExecuteMany(self, sql, par=None):
        """
        Method used for updating/inserting values on the tables based on a
        multiple list of parameters, if present.
        """
        success = False
        self.dbError.Reset()
        if self._dbType == 'mysql':
            try:
                dbCursor = self._dbCon.cursor()
                self.recordCount = dbCursor.executemany(sql, par)
                dbCursor.close()
                del dbCursor
                success = True
            except MySQLdb.Error, e:
                self.recordCount = 0
                self._Error_MySQLdb(e)
                self.dbError.exception = e
            except Exception, e:
                self.recordCount = 0
                self.dbError.code = 0
                self.dbError.description = "%s - %s"\
                    % (repr(e), repr(e.args))
                self.dbError.exception = e
            self.description = None

        elif self._dbType == 'odbc':
            sql = sql.replace(r'%s', '?')
            try:
                dbCursor = self._dbCon.cursor()
                self.recordCount = dbCursor.executemany(sql, par)
                dbCursor.close()
                del dbCursor
                success = True
            except pyodbc.Error, e:
                self.recordCount = 0
                self._Error_ODBC(e)
                self.dbError.exception = e
            except Exception, e:
                self.recordCount = 0
                self.dbError.code = 0
                self.dbError.description = "%s - %s"\
                    % (repr(e), repr(e.args))
                self.dbError.exception = e
            self.description = None

        elif self._dbType == 'adodb':
            try:
                dbCursor = self._dbCon.cursor()
                for y in range(len(par)):
                    for x in range(len(par[y])):
                        if type(par[y][x]) in (str, unicode):
                            par[y][x] = unicode(par[y][x])
                self.recordCount = dbCursor.executemany(sql, par)
                dbCursor.close()
                del dbCursor
                success = True
            except adodb.DatabaseError, e:
                self.recordCount = 0
                self._Error_MySQLdb(e)
            self.description = None

        return success

    def GetInsertedId(self):
        """
        Returns the id assigned by the database to a record just inserted on
        a table.
        """
        return self.lastInsertedId

    def TableExists(self, tabname):
        out = True
        if self._dbType == 'mysql':
            if not self.Execute("SELECT COUNT(*) FROM %(tabname)s" % locals()):
                if self.dbError.code == 1146:
                    out = False
        else:
            raise Exception, 'not implemented'
        return out

    def Close(self):
        """
        Closes the connection to the database.
        """
        closed = False
        if self._dbCon:
            if self.connected:
                self._dbCon.close()
                self.connected = False
                closed = True
        return closed

    def QuoteStart(self, string):
        return "%s%s" % (string, self.WILDCARD_ALL)

    def QuoteEnd(self, string):
        return "%s%s" % (self.WILDCARD_ALL, string)

    def QuoteContent(self, string):
        return "%s%s%s" % (self.WILDCARD_ALL, string, self.WILDCARD_ALL)

    def _Error_MySQLdb(self, e):
        """
        Gets the error returned by MySQLdb and fills appopriate values on
        the internal instance on DbError.
        See DbError class for details.
        """
        err = self.dbError
        err.Reset()
        if len(e.args) >= 2:
            err.code = e.args[0]
            err.description = e.args[1]
        elif len(e.args) == 1:
            if type(e.args[0]) == int:
                err.code = e.args[0]
            else:
                err.description = e.args[0]
        if err.code == 1062:
            err.duplicatedKey = True
        return True

    def _Error_ODBC(self, e):
        """
        Gets the error returned by ODBC and fills appopriate values on
        the internal instance on DbError.
        See DbError class for details.
        """
        err = self.dbError
        err.Reset()
        if len(e.args) >= 2:
            err.code = e.args[0]
            err.description = e.args[1]
        elif len(e.args) == 1:
            if type(e.args[0]) == int:
                err.code = e.args[0]
            else:
                err.description = e.args[0]
        if err.code == 1062:
            err.duplicatedKey = True
        return True

    def _Error_AdoDb(self, e):
        """
        Gets the error returned by MySQLdb and fills appopriate values on
        the internal instance on DbError.
        See DbError class for details.
        """
        err = self.dbError
        err.Reset()
        if type(e) == tuple and len(e) >= 1:
            err.code = e[0][2][5]
            err.description = e[0][2][2]
        elif isinstance(e, adodb.DatabaseError):
            err.description = e.args[0]
        if err.code == 1062:
            err.duplicatedKey = True
        return True

    def ADB_EncodeValue(self, x, base64_encoded=None):
        if base64_encoded:
            return '!BASE64|%s|' % base64_encoded
        if type(x) in (str, unicode):
            if '\n' in x or '"' in x or '=' in x:
                return '!BASE64|%s|' % base64.b64encode(x)
            x = x.encode('utf-8')
        else:
            x = str(x)
        return x.replace('<', '&lt; ').replace('>', '&gt; ').replace('"', '&quot; ').replace('&', '&amp; ')

    def ADB_DecodeValue(self, x, conv=None):
        if callable(conv):
            x = conv(x)
        if type(x) in (str, unicode):
            if x.startswith('!BASE64|'):
                v = base64.b64decode(x.split('|')[1])
            else:
                v = x.decode('utf-8')
                v = v.replace('&amp; ', '&').replace('&lt; ', '<').replace('&gt; ', '>').replace('&quot; ', '"')
        else:
            return x
        return v

    def ADB_CreateFile(self, tables, filename, comment='', content='undefined',
                       tab_classes=None, special_encoders=None,
                       on_table_init=None, on_table_read=None, on_table_row=None, on_table_end=None):

        ADBVER = 3

        f = open(filename, 'w')

        def w(x, i=0, s=4):
            f.write(' '*(i*s)+'%s\n' % x)

    #    w('<?xml version="1.0" encoding="UTF-8" ?>')
    #    w('<!DOCTYPE tablesBackup SYSTEM "null">')

        #inizio backup
        comment_enc = self.ADB_EncodeValue(comment)
        database_name = self.ADB_EncodeValue(self.database)
        w('<tablesBackup version="%(ADBVER)s" database="%(database_name)s" content="%(content)s" comment="%(comment_enc)s">' % locals())

        class DescriptionTable(stormdb.DbMem):
            def __init__(mem, tabname):
                stormdb.DbMem.__init__(mem, 'field_name,field_type,can_null,key_type,default_value,extra')
                self.Retrieve("DESCRIBE %s" % tabname)
                mem.SetRecordset(self.rs)

        class SchemaInfoTable(stormdb.DbMem):
            def __init__(mem, tabname):
                stormdb.DbMem.__init__(mem, 'table,create_command')
                self.Retrieve("SHOW CREATE TABLE %s" % tabname)
                mem.SetRecordset(self.rs)
            def GetAutoIncrementValue(self):
                s = self.create_command
                if s:
                    x = re.search('AUTO_INCREMENT=[0-9+]+', s)
                    if x:
                        p = s[x.start():x.end()]
                        v = p.split("=")
                        return int(v[1])
                return None
            def GetCharset(self):
                s = self.create_command
                if s:
                    x = re.search('DEFAULT CHARSET=[A-Za-z0-9+]+', s)
                    if x:
                        p = s[x.start():x.end()]
                        v = p.split("=")
                        return v[1]
            def GetComment(self):
                s = self.create_command
                if s:
                    x = re.search("COMMENT='.+'", s)
                    if x:
                        p = s[x.start():x.end()]
                        v = p.split("=")
                        return v[1][1:-1]

        class DescriptionIndexes(stormdb.DbMem):
            def __init__(mem, tabname):
                stormdb.DbMem.__init__(mem, 'index_name,index_family,index_type,fields')

                fields = 'table,not_unique,key_name,seq_in_index,column_name,collation,cardinality,sub_part,packed,null,index_type,comment'
                try:
                    self.Retrieve('SELECT VERSION()')
                    mySqlVersion = self.rs[0][0][:3]
                    if mySqlVersion >= '5.5':
                        fields += ',index_comment'
                except:
                    pass
                indexes = stormdb.DbMem(fields)


                #===============================================================
                #
                # indexes = stormdb.DbMem('table,not_unique,key_name,seq_in_index,column_name,collation,cardinality,sub_part,packed,null,index_type,comment')
                #===============================================================
                self.Retrieve("SHOW INDEX IN %s" % tabname)
                indexes.SetRecordset(self.rs)
                lastname = None
                for index in indexes:
                    if index.key_name != lastname:
                        lastname = index.key_name
                        mem.CreateNewRow()
                        mem.index_name = index.key_name
                        if index.key_name == 'PRIMARY':
                            mem.index_family = 'PRIMARY KEY'
                        else:
                            if index.not_unique == 0:
                                mem.index_family ='UNIQUE KEY'
                            else:
                                mem.index_family ='KEY'
                        mem.index_type = index.index_type
                        mem.fields = ''
                    if mem.fields:
                        mem.fields += ','
                    mem.fields += index.column_name

        for table in tables:
            #print table
            tab_class = stormdb.DbTable
            if tab_classes and table in tab_classes:
                tab_class = tab_classes[table]
            t = tab_class(table)
            if callable(on_table_init):
                on_table_init(t)

            cc = SchemaInfoTable(table)
            charset = cc.GetCharset() or 'utf8'
            autoinc = cc.GetAutoIncrementValue()
            comment = cc.GetComment()

            #inizio tabella
            tabdef = 'name="%s"' % table
            if autoinc:
                tabdef += ' autoincrement_start="%d"' % autoinc
            if charset:
                tabdef += ' charset="%s"' % charset
            if comment:
                tabdef += ' comment="%s"' % self.ADB_EncodeValue(comment)

            w('<table %s>' % tabdef, 1)

            #struttura
            w('<structure>', 2)

            #definizione colonne
            deftab = DescriptionTable(table)
            for field_name, field_type, can_null, key_type, default_value, extra in deftab.GetRecordset():
                w('<column name="%(field_name)s" type="%(field_type)s" can_null="%(can_null)s" key_type="%(key_type)s" default_value="%(default_value)s" extra="%(extra)s" />' % locals(), 3)

            #definizione indici
            defind = DescriptionIndexes(table)
            for index_name, index_family, index_type, fields in defind.GetRecordset():
                w('<index name="%(index_name)s" family="%(index_family)s" type="%(index_type)s" fields="%(fields)s" />' % locals(), 3)

            #fine struttura
            w('</structure>', 2)

            #inizio contenuto

            t.Retrieve()
            if callable(on_table_read):
                on_table_read(t)
            se = {}
            if special_encoders and table in special_encoders:
                se = special_encoders[table]

            rows = t.RowsCount()
            cols = t.GetFieldNames()
            coll = len(cols)
            rs = t.GetRecordset()
            w('<content rows="%d">' % rows, 2)
            for row in range(len(rs)):
                r = rs[row]
                c = ''
                for col in range(coll):
                    if col in se:
                        continue
                    v = r[col]
                    if v is not None:
                        c += '%s="%s" ' % (cols[col], self.ADB_EncodeValue(v))
                if se:
                    for se_col in se:
                        se_func = se[se_col]
                        c += '%s="%s" ' % (se_col, se_func(t, row))
                w('<row %s />' % c, 3)
                if callable(on_table_row):
                    on_table_row(t, row)

            #fine contenuto
            w('</content>', 2)

            if callable(on_table_end):
                on_table_end(t)

            #fine tabella
            w('</table>', 1)

        #fine backup
        w('</tablesBackup>')

        f.close()

    def ADB_RestoreFile(self, filename, database_name, tables=None, special_decoders=None,
                        on_table_init=None, on_table_write=None, on_table_end=None):

        re_table_search = 'name="[A-Za-z0-9 _]+"'
        re_table_srcdes = 'comment=".+"'
        re_table_chrset = 'charset="[A-Za-z0-9_-]+"'
        re_table_autinc = 'autoincrement_start="[0-9]+"'
        re_column_search = '[A-Za-z0-9_]+="[A-Za-z0-9 !\(\)=_,]+"'
        re_content_search = '[A-Za-z0-9_]+="[^"]*"'

        f = file(filename, 'r')
        tab_name = None
        tab_desc = None
        tab_auti = None
        tab_cset = None
        tab_stru = None
        col_list = None
        ind_list = None
        tab_row = None
        special_decoder = None

        structure_reading = False
        content_reading = False
        record_values = []

        row = 0
        def RaiseXmlError(m="Errore di struttura del file XML"):
            m = '%s (riga %d)' % (m, row+1)
            raise Exception, m
        def RaiseXmlErrorNoTable():
            RaiseXmlError('Dichiarazione della struttura senza nome della tabella')

        def str2date(x):
            y, m, d = x.split('-')
            if int(y)<1900:
                y = '1900'
            return stormdb.DateTime.Date(int(y), int(m), int(d))

        def str2datetime(x):
            dd, dh = x.split()
            y, m, d = dd.split('-')
            hh, mm, ss = dh.split(':')
            if int(y)<1900:
                y = '1900'
            return stormdb.DateTime.DateTime(int(y), int(m), int(d), int(hh), int(mm), int(ss))

        if not self.Execute('CREATE DATABASE %s' % database_name):
            if self.dbError.code != 1007:
                raise Exception, self.dbError.description

        while True:

            l = f.readline()
            row += 1
            if len(l) == 0:
                break
            l = l.strip()

            if l.startswith('<table '):

                #inizio dichiarazione tabella

                if structure_reading or content_reading:
                    RaiseXmlError()

                s = re.search(re_table_search, l)
                if s:
                    tab_name = l[s.start():s.end()].split('"')[1]
                    special_decoder = {}
                    if special_decoders and tab_name in special_decoders:
                        special_decoder = special_decoders[tab_name]

                s = re.search(re_table_srcdes, l)
                if s:
                    tab_desc = l[s.start():s.end()].split('=')[1][1:-1]

                s = re.search(re_table_autinc, l)
                if s:
                    tab_auti = int(l[s.start():s.end()].split('=')[1][1:-1])

                s = re.search(re_table_chrset, l)
                if s:
                    tab_cset = l[s.start():s.end()].split('=')[1][1:-1]

            elif l.startswith('<structure'):

                #inizio dichiarazione struttura

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif structure_reading:
                    RaiseXmlError('Inizio struttura già definito')
                elif content_reading:
                    RaiseXmlError('Inizio struttura durante la lettura del contenuto')

                structure_reading = True

                tab_stru = {}
                col_list = []
                ind_list = []

            elif l.startswith('<column'):

                #definizione colonna

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif not structure_reading:
                    RaiseXmlError('Definizione colonna fuori dalla definizione della struttura')

                kw = {}
                t = None
                values = []
                for c in re.findall(re_column_search, l):
                    n = c.index("=")
                    s = c[:n]
                    v = c[n+1:]
                    v = v[1:]
                    v = v[:-1]
                    if s == 'type':
                        if v.startswith('int') or v.startswith('tinyint') or v.startswith('bigint'):
                            t = int
                        elif v.startswith('decimal'):
                            t = float
                        elif v.startswith('datetime'):
                            t = str2datetime
                        elif v.startswith('date'):
                            t = str2date
                        elif v.startswith('char') or v.startswith('varchar') or v.startswith('text') or v.startswith('mediumtext') or v.startswith('longtext') or v.startswith('blob') or v.startswith('longblob') or v.startswith('varbinary'):
                            t = unicode
                        else:
                            print "unknown lom type: %s" % v
                            pass
                    kw[s] = self.ADB_DecodeValue(v)
                if t is None:
                    raise Exception, 'Tipo colonna non interpretabile (tabella %s, colonna %s)' % (tab_name, kw['name'])
                kw['conv'] = t
                tab_stru[kw['name']] = kw
                col_list.append(kw['name'])

            elif l.startswith('<index'):

                #definizione indice

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif not structure_reading:
                    RaiseXmlError('Definizione indice fuori dalla definizione della struttura')

                kw = {}
                t = None
                values = []
                for c in re.findall(re_column_search, l):
                    n = c.index("=")
                    s = c[:n]
                    v = c[n+1:]
                    v = v[1:]
                    v = v[:-1]
                    kw[s] = self.ADB_DecodeValue(v)
                ind_list.append(kw)

            elif l.startswith('</structure'):

                #fine dichiarazione struttura

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif not structure_reading:
                    RaiseXmlError('Fine struttura priva dell\'inizio')
                elif content_reading:
                    RaiseXmlError('Fine struttura durante la lettura del contenuto')

                structure_reading = False
                structure = []
                indexes = []

                for name in col_list:
                    stru = tab_stru[name]
                    s = '    `%s`' % stru['name']
                    s += ' %s' % stru['type']
                    if stru['can_null'] == 'NO':
                        s += ' NOT NULL'
                    if 'extra' in stru:
                        e = stru['extra']
                    else:
                        e = None
                    if not e:
                        if 'default_value' in stru:
                            dv = stru['default_value']
                            if dv != 'None':
                                s += ' DEFAULT %s' % dv
                    if e:
                        s += ' %s' % e
                    structure.append(s)

                for index in ind_list:
                    index_family = index['family']
                    index_fields = ','.join(['`%s`' % col for col in index['fields'].split(',')])
                    if 'PRIMARY' in index_family:
                        index_name = ''
                    else:
                        index_name = index['name']
                    indexes.append('%(index_family)s %(index_name)s (%(index_fields)s)' % locals())

                if not self.Execute('DROP TABLE `%s`.`%s`' % (database_name, tab_name)):
                    if self.dbError.code != 1051:
                        raise Exception, self.dbError.description

                coldef = structure+indexes
                #TODO: Parametrizzare engine
                cmd = 'CREATE TABLE `%s`.`%s` (\n%s) ENGINE=MyISAM' % (database_name, tab_name, ',\n'.join(coldef))
                if tab_auti:
                    cmd += " AUTO_INCREMENT=%d" % tab_auti
                if tab_cset:
                    cmd += " DEFAULT CHARSET=%s" % tab_cset
                if tab_desc:
                    cmd += " COMMENT='%s'" % tab_desc

                if not self.Execute(cmd):
                    raise Exception, self.dbError.description

            elif l.startswith('<content'):

                #inizio dichiarazione contenuto

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif structure_reading:
                    RaiseXmlError('Inizio contenuto durante la lettura della struttura')
                elif content_reading:
                    RaiseXmlError('Inizio contenuto già definito')

                content_reading = True

                tab_row = 0

                if callable(on_table_init):
                    s = re.search('rows="\d+"', l)
                    if s.group():
                        records = int(s.group().split('"')[1])
                    else:
                        records = 0
                    on_table_init(tab_name, records)

            elif l.startswith('<row'):

                #definizione contenuto record

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif structure_reading:
                    RaiseXmlError('Definizione contenuto durante la lettura della struttura')

                if tables is None or tab_name in tables:

                    columns = []
                    values = []
                    se_info = []
                    for c in re.findall(re_content_search, l):
#                        n = c.index("=")
#                        col_name = c[:n]
#                        col_value = c[n+2:]
#                        col_value = col_value[:-1]
                        col_name, col_value = c.split('=', 1)
                        col_value = col_value[1:-1]
                        if col_name in special_decoder:
                            se_func = special_decoder[col_name]
                            se_info.append((se_func, col_name, col_value))
                        else:
                            columns.append(col_name)
                            values.append(self.ADB_DecodeValue(col_value, tab_stru[col_name]['conv']))

                    value_wildcards = ','.join([r'%s']*len(columns))
                    columns = ','.join(columns)

                    #TODO: MODIFICARE PER MYSQL 5.7
                    #===========================================================
                    # if tab_name=='clienti':
                    #     for x, y in enumerate(values):
                    #         #TODO: MODIFICARE PER MYSQL 5.7
                    #         if x==38:
                    #             print '%s %s %s' % (values[0], x, y)
                    #             #print values[x]
                    #             values[x]=y.encode('utf-8')
                    #             print values[x]
                    #             values[x]=unicode(values[x], "utf-8")
                    #             if values[0]==1172:
                    #                 pass
                    #===========================================================

                    if not self.Execute("INSERT INTO %(database_name)s.%(tab_name)s (%(columns)s) VALUES (%(value_wildcards)s)" % locals(), values):
                        raise Exception, '%s (riga %d)' % (self.dbError.description, row)

                    if se_info:
                        for se_func, se_col, se_val in se_info:
                            se_func(tab_row, se_col, se_val, columns.split(','), values)

                    if callable(on_table_write):
                        on_table_write(tab_name, tab_row)

                    tab_row += 1

            elif l.startswith('</content'):

                #fine dichiarazione contenuto

                if tab_name is None:
                    RaiseXmlErrorNoTable()
                elif not content_reading:
                    RaiseXmlError('Fine struttura priva dell\'inizio')

                content_reading = False

                if callable(on_table_end):
                    on_table_end(tab_name)

        f.close()

    def ADB_GetFileInfo(self, filename, read_tables=True):

        import re

        re_content_search = '[A-Za-z0-9_]+="[^"]*"'

        f = file(filename, 'r')

        db_name = None
        comment = None
        content = None
        tab_name = None
        tab_rows = {}
        row = 0

        while True:

            l = f.readline()
            row += 1
            if len(l) == 0:
                break
            l = l.strip()

            if l.startswith('<tablesBackup'):

                #dichiarazione backup
                s = re.search('database="[^"]*"', l)
                if s and s.group():
                    db_name = self.ADB_DecodeValue(s.group().split('"')[1])
                s = re.search('content="[^"]*"', l)
                if s and s.group():
                    content = self.ADB_DecodeValue(s.group().split('"')[1])
                s = re.search('comment="[^"]*"', l)
                if s and s.group():
                    comment = self.ADB_DecodeValue(s.group().split('"')[1])

                if not read_tables:
                    break

            elif l.startswith('<table'):

                #dichiarazione tabella
                s = re.search('name="[^"]*"', l)
                if s and s.group():
                    tab_name = self.ADB_DecodeValue(s.group().split('"')[1])

            elif l.startswith('<content'):

                #dichiarazione tabella
                s = re.search('rows="[^"]*"', l)
                if s and s.group():
                    rows = self.ADB_DecodeValue(s.group().split('"')[1], int)
                    tab_rows[tab_name] = rows

        f.close()

        return db_name, content, comment, tab_rows

    def ADB_GetBackupFolderContent(self, pathname, database=None, read_tables=True, order_by=None, order_reverse=False):

        class BackupFolderContent(stormdb.DbMem):

            def __init__(self):
                stormdb.DbMem.__init__(self, 'filename,datetime,filesize,database,content,comment,table_rows')

        c = BackupFolderContent()

        import os, glob, time
        for r in glob.glob(os.path.join(pathname, '*.*')):
            try:
                db_name, content, comment, tables = self.ADB_GetFileInfo(r, read_tables=read_tables)
                if not (db_name == database or database is None):
                    continue
            except:
                continue
            if db_name:
                stats = os.stat(r)
                dt = time.localtime(stats[8])
                c.CreateNewRow()
                c.filename = os.path.split(r)[1]
                c.datetime = DateTime.DateTime(dt[0], dt[1], dt[2], dt[3], dt[4], dt[5])
                c.filesize = stats[6]
                c.database = db_name
                c.content = content
                c.comment = comment
                if read_tables:
                    c.table_rows = tables

        if order_by:
            rs = c.GetRecordset()
            ci = c._GetFieldIndex(order_by)
            ors = [(r[ci], r) for r in rs]
            ors.sort(reverse=order_reverse)
            rs = [r[1] for r in ors]
            c.SetRecordset(rs)

        return c
