#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stormdb/dbtable.py
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


import copy

import stormdb as adb
from stormdb import DateTime,\
     OPENMODE_READONLY, OPENMODE_WRITE, OPENMODE_STANDARD,\
     JOIN_ALL, JOIN_LEFT, JOIN_RIGHT, ORDER_ASCENDING, ORDER_DESCENDING
logmsg = adb.db.logmsg

import awc.controls.windows as aw
import mx

ADEG_MISSINGTABLE =  0
ADEG_MISSINGFIELD =  1
ADEG_WRONGTYPE =     2
ADEG_WRONGLENGHT =   3
ADEG_WRONGDECIMALS = 4
ADEG_INDEX =         5
ADEG_REINDEX =       6

I_TABLE =      0
I_NOTUNIQUE =  1
I_KEYNAME =    2
I_SEQUENCE =   3
I_COLUMN =     4
I_COLLATION =  5
I_CARDINAL =   6
I_SUBPART =    7
I_PACKED =     8
I_NULL =       9
I_INDEXTYPE = 10
I_COMMENT =   11

import locale

FORCE_TO_LATIN1 = False


__env__ = None


_JOIN_TABLE =       0
_JOIN_FIELDLEFT =   1
_JOIN_FIELDRIGHT =  2
_JOIN_TYPE =        3
_JOIN_FIELDS =      4

_AGGR_TOT =         0
_AGGR_MAX =         1
_AGGR_MIN =         2
_AGGR_AVG =         3
_AGGR_CNT =         4


__fktemplate__ = lambda table: "id_%s" % table


WaitDialogClass = None
def SetWaitDialogClass(c):
    global WaitDialogClass
    WaitDialogClass = c
def GetWaitDialogClass():
    c = WaitDialogClass
    if c is None:
        try:
            m = __import__('awc.util')
            c = m.util.WaitDialog
        except ImportError:
            pass
    if c is None:
        def c(*args, **kwargs):
            pass
    return c


NUMDEC_IMP = 2
def SetNumDecImp(n):
    global NUMDEC_IMP
    NUMDEC_IMP = n

NUMDEC_PRZ = 2
def SetNumDecPrz(n):
    global NUMDEC_PRZ
    NUMDEC_PRZ = n

NUMDEC_QTA = 0
def SetNumDecQta(n):
    global NUMDEC_QTA
    NUMDEC_QTA = n


PAGE_ROWS = None
def SetPageRows(pr):
    global PAGE_ROWS
    PAGE_ROWS = pr

NAVIGATION_PAGES = 20
def SetNavigationPages(np):
    global NAVIGATION_PAGES
    NAVIGATION_PAGES = np



import csv

CSVFORMAT_DELIMITER = ','
def SetCSV_Delimiter(x=','):
    global CSVFORMAT_DELIMITER
    CSVFORMAT_DELIMITER = x

CSVFORMAT_QUOTECHAR = '"'
def SetCSV_QuoteChar(x='"'):
    global CSVFORMAT_QUOTECHAR
    CSVFORMAT_QUOTECHAR = x

CSVFORMAT_QUOTING = csv.QUOTE_MINIMAL
def SetCSV_Quoting(x=csv.QUOTE_MINIMAL):
    global CSVFORMAT_QUOTING
    CSVFORMAT_QUOTING = x


class DbInfo(object):
    def __init__(self):
        object.__init__(self)
        class ExternalData:
            dict = {}
        self.mParent =            None
        self.iRoot =              None
        self.iParent =            None
        self.iChildrens =         []
        self.mChildrens =         []
        self.aChildrens =         []
        self.fieldsOffset =       0
        self.db =                 None
        self.tableName =          ""
        self.tableAlias =         ""
        self.primaryKey =         ""
        self.primaryCol =         -1
        self.fields =             []
        self.mandatoryFields =    []
        self.rs =                 []
        self.fieldCount =         -1
        self.fieldNames =         []
        self.addedFields =        []
        self.fieldBooleans =      []
        self.fieldsAlias =        False
        self.recordNumber =       -1
        self.recordCount =        -1
        self.description =        None
        self.iterIndex =          None
        self.iterCount =          None
        self.writable =           False
        self.writeall =           False
        self.defaults =           {}
        self.modifiedRecords =    []
        self.deletedRecords =     []
        self.forceInsert =        False
        self.filters =            []
        self.filtersSaved =       []
        self.basefilters =        []
        self.printfilters =       {}
        self.printvalues =        {}
        self.orders =             []
        self.relTab =             []
        self.relDb =              []
        self.relId =              []
        self.relation =           None
        self.group =              None
        self.dbError =            DbError()
        self.synthetized =        False
        self.getFilters =         False
        self.externalData =       ExternalData()
        self.updateIChildrens =   True
        self.updateMChildrens =   True
        self.level =              0
        self.limit =              None
        self.limit_rows =         None
        self.flatView =           False
        self.flatViewGroups =     []
        self.page_rows =          None
        self.waitDialog =         None
        self.debug =              False

    def GetEnv(self):
        return __env__

    def SetEnv(self, e):
        global __env__
        __env__ = e

    def Debug(self):
        print 'debug'
        return True

    def ResetPrintFilterValues(self):
        self.printfilters.clear()

    def SetPrintFilterValue(self, key, val):
        self.printfilters[key] = val

    def GetPrintFilterValue(self, key, default=''):
        if not key in self.printfilters:
            return default
        return self.printfilters[key]

    def HasPrintFilterValues(self):
        return len(self.printfilters)>0

    def SetPrintValue(self, name, value):
        self.printvalues[name] = value

    def GetPrintValue(self, name, default=None):
        if name in self.printvalues:
            return self.printvalues[name]
        return default

    def DeletePrintValue(self, name):
        if name in self.printvalues:
            self.printvalues.pop(name)

    def ResetPrintValues(self):
        self.printvalues.clear()

# ------------------------------------------------------------------------------


class DbRelation(object):
    def __init__(self):
        self.leftTable =  None
        self.leftAlias =  None
        self.leftId =     None
        self.rightTable = None
        self.rightAlias = None
        self.rightId =    None
        self.operator =   None
        self.joinType =   None
        self.expression = None


# ------------------------------------------------------------------------------


class DbGroup(object):
    def __init__(self):
        self.fields =       []
        self.groups =       []
        self.filters =      []
        self.filtersSaved = []
        self.aggregated =   False

    def ClearGroups(self):
        del self.groups[:]

    def AddGroup(self, field, alias=None):
        self.groups.append([field, alias])

    def Aggregate(self, field, alias, aType, prefix):
        if aType in (_AGGR_TOT, _AGGR_CNT, _AGGR_MAX, _AGGR_MIN, _AGGR_AVG):
            self.fields.append([field, prefix+alias, aType])
        else:
            raise Exception,\
                  """Invalid type for aggregation"""

    def ClearFilters(self):
        """
        Resets the filters list.
        """
        oldFilters = copy.copy(self.filters)
        del self.filters[:]
        return oldFilters

    def AddFilter(self, expr, params=None):
        self.filters.append((expr, params))
        return self

    def StoreFilters(self):
        self.filtersSaved.append(copy.deepcopy(self.filters))

    def ResumeFilters(self):
        assert len(self.filtersSaved) > 0,\
               """No filters to resume on group"""
        self.filters = copy.deepcopy(self.filtersSaved[-1])
        self.filtersSaved.pop()


# ------------------------------------------------------------------------------


class DbError(object):
    def __init__(self):
        self.code = 0
        self.description = ""
        self.duplicatedKey = False
        self.duplicatedKeyNumber = -1

    def Reset(self):
        self.code =          0
        self.description =   ""
        self.duplicatedKey = False
        self.duplicatedKeyNumber = -1


# ------------------------------------------------------------------------------


USE_CACHE = True

_cachetabs = {}

def ClearCache():
    global _cachetabs
    _cachetabs.clear()

def EnableChache(ec=True):
    global USE_CACHE
    USE_CACHE = ec


# ------------------------------------------------------------------------------


class DbTable(object):
    """
    Table(s) management.
    Provides all the necessary to:
        retrieve data from a table or a group of tables
        insert/update that data
        treat that data as a group of class variables, one for each
        retrieved column (field)
    Joins can be of type:
        1:1 relationship: related tables are not updatable or insertable
        1:N relationship: related tables are updatable and insertable,
        with the automatic detection and store of the id that makes the
        relationship.
    In either cases, joins can be INNER JOIN or LEFT JOIN.
    """
    pb       = None
    adbStore = None


    def __init__(self, tabName, tabAlias=None, primaryKey="id",\
                 fields="*", writable=None, mandatoryFields="",\
                 defaults=None, db=None, getFilters=None, forceInsert=False):
        """
        Constructor.
        The only required parameter is the table name
        Optional parameters are:
            tabAlias  (string) table alias
            primayKey (string) column name (default="id")
            fields    (string) fields to retrieve, separated by commas
                      (default="*")
            writable  (bool)   flag to allow insert/update/delete operations
                      (default=__defOpenMode__==OPENMODE_STANDARD)
            mandatoryFields (string) list of all the mandatory columns on
                      the table, separated by commas (default="")
            defaults  (dictionary) default values for fields that require
                      initial values (default={})
            database  (DB) database object used to execute all the database
                      commands (default=__connection__)
        """
        if db is None:
            db = adb.db.__database__
        if db is None:
            raise Exception, "Database connection is missing"
        if tabAlias is None:
            tabAlias = tabName
        if writable is None:
            writable = True#(adb.__defOpenMode__ == OPENMODE_WRITE)
        if defaults is None:
            defaults = {}
        self._info = DbInfo()
        self._info.db = db
        self._info.tableName = tabName
        self._info.tableAlias = tabAlias
        self._info.primaryKey = primaryKey
        self._info.writable = writable
        self._info.forceInsert = forceInsert
        if mandatoryFields:
            self._info.mandatoryFields = mandatoryFields.split(",")
        else:
            self._info.mandatoryFields = []
        self._info.defaults = defaults
        self._info.iterIndex = 0
        self._info.iterCount = 0
        self._info.relId = None
        if getFilters is not None:
            self._info.getFilters = getFilters
        self._info.group = DbGroup()
        if fields is not None:
            fieldslist = self._SetFields(fields)
            readstru = True
            logmsg('read <%s> structure' % tabName)
            cache_key = '%s:%s' % (tabName, fields)
            if USE_CACHE and cache_key in _cachetabs:
                self._info.description = _cachetabs[cache_key]
            #if USE_CACHE and tabName in _cachetabs:
                ##read structure from cache
                #if fields == '*':
                    ##read all columns
                    #self._info.description = _cachetabs[tabName]
                #else:
                    ##read specific columns: test if cached
                    #self._info.description = []
                    #ct = _cachetabs[tabName]
                    #for f in fieldslist:
                        #try:
                            #n = awu.ListSearch(ct, lambda x: x[0] == f)
                            #self._info.description.append(ct[n])
                        #except:
                            #pass
                self._GetFieldNames()
                logmsg('using cached version')
                readstru = False
            if readstru:
                if self._info.db._dbType == "mysql":
                    cmd = "SELECT %s FROM %s LIMIT 1"\
                        % (", ".join(self._info.fields), tabName)
                elif self._info.db._dbType == "adodb":
                    cmd = "SELECT TOP 1 %s FROM %s"\
                        % (", ".join(self._info.fields), tabName)
                elif self._info.db._dbType == "odbc":
                    cmd = "SELECT TOP 1 %s FROM %s"\
                        % (", ".join(self._info.fields), tabName)
                if self._info.db.Retrieve(cmd):
                    logmsg('structure loaded from database')
                    self._info.description = self._info.db.description
                    self._GetFieldNames()
                    #if fields == '*':
                        #if USE_CACHE and not tabName in _cachetabs:
                            #_cachetabs[tabName] = self._info.description
                    _cachetabs[cache_key] = self._info.db.description
                else:
                    self.GetError()
                    raise Exception,\
                          """Error retrieving '%s' structure: %s, %s"""\
                          % (tabName, db.dbError.code,\
                             db.dbError.description)

    def AddLimit(self, max=1):
        self._info.limit = max

    def SetLimits(self, max=0, rows=None):
        self._info.limit = max
        self._info.limit_rows = rows

    def GetLimits(self):
        return self._info.limit, self._info.limit_rows

    def ShowDialog(self, show=None):
        """
        Imposta il parent dei dialog di attesa automatici.
        show = parent dialog
        """
        pass
#        self._info.waitDialog = show

    def _SetFields(self, fields):
        """
        Internal, stores field names in a list.
        """
        if type(fields) in (str, unicode):
            fields = fields.split(",")
        if not "*" in fields:
            if not self._info.primaryKey in fields:
                fields.append(self._info.primaryKey)
        self._info.fields = fields
        return self._info.fields

    def AddField(self, field, alias):
        """
        Add a field (or sql column expression) to the fields list.
        """
        #self._info.fields.append(field)
        #self._info.fieldNames.append(alias)
        self._info.addedFields.append([field, alias])
        self._info.fieldCount += 1

    def ClearFilters(self):
        """
        Resets the filters list.
        """
        oldFilters = copy.deepcopy(self._info.filters)
        del self._info.filters[:]
        return oldFilters

    def AddFilter(self, expr, *params):
        self._info.filters.append((expr, params))
        return self

    def ClearBaseFilters(self):
        """
        Resets the base filters list.
        """
        olfFilters = copy.deepcopy(self._info.basefilters)
        del self._info.basefilters[:]
        return olfFilters

    def AddBaseFilter(self, expr, *params):
        self._info.basefilters.append((expr, params))
        return self

    def ClearHavings(self):
        """
        Resets the havings list.
        """
        oldHavings = copy.deepcopy(self._info.group.filters)
        del self._info.group.filters[:]
        return oldHavings

    def AddHaving(self, expr, params=None):
        self._info.group.filters.append((expr, params))
        return self

    def ClearOrders(self):
        """
        Resets the filters list.
        """
        oldFilters = copy.copy(self._info.orders)
        del self._info.orders[:]
        return oldFilters

    def AddOrder(self, order, orderType=ORDER_ASCENDING):
        """
        Adds one order expression.
        """
        assert type(order) in (str, unicode),\
               """Order expressions must be string"""
        assert orderType in (ORDER_ASCENDING, ORDER_DESCENDING),\
               """Wrong order type"""
        if not '.' in order and not "(" in order:
            order = "%s.%s" % (self._info.tableAlias, order)
        self._info.orders.append((order, orderType))
        return self

    def AddReversedOrder(self, order):
        """
        Adds a reversed order expression.
        """
        return self.AddOrder(order, ORDER_DESCENDING)

    def AddJoin(self, table, alias=None, idLeft=None, join=JOIN_ALL,\
                fields = "*", where=None, order=None, idRight=None,\
                dbTabClass=None, pkRight="id", relexpr=None):
        """
        Add a join 1:1.
        table   (string) table to join
        alias   (string) desired table alias
                (default: table name)
        idLeft  (string) left table's column name
                (default: template for foreign keys based on right table, see
                SetForeignKeyTemplate function)
        fields  (string) list of fields to retrieve, separated by commas
                (default: "*")
        where   (string) where (filter) condition to apply
                (default: None)
        order   (string) order expression
                (default: None)
        idRight (string) right table column name
                (default: right table primary key column name)
        pkRight (string) right table primary key column name
                (default: "id")
        This makes a DbTable instance available via table alias name
        For example:
            cust = DbTable("customers")
            cust.AddJoin("category", join=JOIN_LEFT)
            print cust.description, cust.category.description
        With alias:
            cust.AddJoin("category", "cat", join=JOIN_LEFT)
            print cust.description, cust.cat.description
        The 1:1 join causes a unique SELECT performed at left table Retrieve
        time; in the example, only one SELECT is done over the database
        returning the entire customers-categories recordset.
        """
        tabLeft = self._info.tableAlias
        if alias is None:
            alias = table
        if dbTabClass is None:
            dbTabClass = DbTable
        dbrel = dbTabClass(table, alias, primaryKey=pkRight, fields=fields,
                           writable=self._info.writable, db=self._info.db)
        if self._info.synthetized:
            dbrel.Synthetize()
        if idLeft is None:
            idLeft = __fktemplate__(alias)
            if not idLeft in self._info.fieldNames:
                idLeft = __fktemplate__(table)
        if idRight is None:
            idRight = pkRight
        rel = DbRelation()
        rel.leftTable =  self._info.tableName
        rel.leftAlias =  self._info.tableAlias
        rel.rightTable = table
        rel.rightAlias = alias
        rel.joinType =   join
        if relexpr is None:
            rel.leftId =     idLeft
            rel.rightId =    idRight
            rel.operator =   "="
        else:
            rel.expression = relexpr
        dbrel._info.relation = rel
        iroot = self
        while True:
            if iroot._info.iRoot is None or\
               iroot._info.iRoot == iroot:
                break
            iroot = iroot._info.iRoot
        #iroot._info.iChildrens.append(dbrel)
        iroot._info.fieldCount += dbrel._info.fieldCount
        self._info.iChildrens.append(dbrel)
        self._info.relTab.append(alias)
        self._info.relDb.append(dbrel)
        if where:
            self.AddFilter(where)
        if order:
            self.AddOrder(order)
        dbrel._info.iRoot = iroot
        dbrel._info.iParent = self
        self.__setattr__(alias, dbrel)
        return dbrel

    def AddMultiJoin(self, table=None, alias=None, idRight=None,\
                     join=JOIN_ALL, fields = "*", where=None,\
                     order=None, writable=None, idLeft=None,\
                     dbTabClass=None, pkRight="id"):
        """
        Add a join 1:N.
        table   (string) table to join
        alias   (string) desired table alias
                (default: table name)
        idRight (string) right table's column name
                (default: template for foreign keys based on left table, see
                SetForeignKeyTemplate function)
        fields  (string) list of fields to retrieve, separated by commas
                (default: "*")
        where   (string) where (filter) condition to apply
                (default: None)
        order   (string) order expression
                (default: None)
        idLeft  (string) left table column name
                (default: table's primary key column name)
        pkRight (string) right table primary key column name
                (default: "id")
        This makes a DbTable instance available via table alias name
        For example:
            cust = DbTable("customers")
            cust.AddJoin("orders", join=JOIN_LEFT)
            print cust.description
            for order in cust.orders:
                print "%d, %s" % (order.number, order.date)
        With alias:
            cust.AddJoin("orders", "ord", join=JOIN_LEFT)
            print cust.description
            for order in cust.ord:
                print "%d, %s" % (order.number, order.date)
        The 1:N join causes a unique SELECT performed at left table Retrieve
        time to obtain informations relative on that table, plus eventual
        joined tables; informations relative to the table joined with
        method AddMultiJoin are retrieved separately everytime cursor
        changes position; in the example, a sigle SELECT is done over the
        database to retrieve customers, and a SELECT on the orders is made
        for every customer examined.
        """
        if writable is None:
            writable = self._info.writable
        if alias is None:
            alias = table
        if dbTabClass is None:
            dbTabClass = DbTable
        dbrel = dbTabClass(table, alias, primaryKey=pkRight, fields=fields,
                           writable=writable, db=self._info.db)
        if idLeft is None:
            idLeft = dbrel._info.primaryKey
        if idRight is None:
            idRight = __fktemplate__(self._info.tableAlias)
            if not idRight in dbrel._info.fieldNames:
                idRight = __fktemplate__(self._info.tableName)
        rel = DbRelation()
        rel.leftTable =  self._info.tableName
        rel.leftAlias =  self._info.tableAlias
        rel.leftId =     idLeft
        rel.rightTable = table
        rel.rightAlias = alias
        rel.rightId =    idRight
        rel.operator =   "="
        rel.joinType =   join
        dbrel._info.relation = rel
        dbrel._info.mParent = self
        if where:
            self.AddFilter(where)
        if order:
            self.AddOrder(order)
        iroot = self
        while True:
            if iroot._info.iRoot is None or\
               iroot._info.iRoot == iroot:
                break
            iroot = iroot._info.iRoot
        self._info.mChildrens.append(dbrel)
        self._info.relTab.append(alias)
        self._info.relDb.append(dbrel)
        self.__setattr__(alias, dbrel)
        return dbrel

    def Synthetize(self):
        if len(self._info.group.fields)>0:
            raise Exception,\
                  """Cannot synthetize here, make sure aggregations """\
                  """do not preceed this method"""
        dbs = []
        def addchildrens(dbs, tab):
            dbs.append(tab)
            if tab._info.iChildrens:
                for i in tab._info.iChildrens:
                    cld = addchildrens(dbs, i)
                    if type(cld) is list:
                        dbs += cld
                return dbs
            return None
        addchildrens(dbs, self)

        for db in dbs:
            del db._info.fieldNames[:]
            db._info.fieldNames = []
            db._info.fieldCount = 0
            db._info.synthetized = True

    def AggregateOnItself(self):
        return self.Synthetize()

    def Aggregate(self, table=None, alias=None, idRight=None,\
                     join=JOIN_ALL, idLeft=None, pkRight="id"):
        """
        Add a join 1:N.
        table   (string) table to join
        alias   (string) desired table alias
                (default: table name)
        idRight (string) right table's column name
                (default: template for foreign keys based on left table, see
                SetForeignKeyTemplate function)
        idLeft  (string) left table column name
                (default: table's primary key column name)
        pkRight (string) right table primary key column name
                (default: "id")
        """
        if alias is None:
            alias = table
        dbrel = DbTable(table, alias, pkRight, fields=None)
        if idLeft is None:
            idLeft = dbrel._info.primaryKey
        if idRight is None:
            idRight = __fktemplate__(self._info.tableAlias)
            if not idRight in dbrel._info.fieldNames:
                idRight = __fktemplate__(self._info.tableName)
        rel = DbRelation()
        rel.leftTable =  self._info.tableName
        rel.leftAlias =  self._info.tableAlias
        rel.leftId =     idLeft
        rel.rightTable = table
        rel.rightAlias = alias
        rel.rightId =    idRight
        rel.operator =   "="
        rel.joinType =   join
        dbrel._info.relation = rel
        dbrel._info.mParent = self
        dbrel._info.group.aggregated = True
        iroot = self
        while True:
            if iroot._info.iRoot is None or\
               iroot._info.iRoot == iroot:
                break
            iroot = iroot._info.iRoot
        self._info.aChildrens.append(dbrel)
        self._info.relTab.append(alias)
        self._info.relDb.append(dbrel)
        return dbrel

    def _SetForeignKey(self, relKey):
        """
        Sets the id value for multijoin.
        """
        self._info.relId = relKey
        return self

    def ClearGroups(self):
        #raise "Da implementare (non toglie le colonne aggiunte in fieldNames"
        return self._info.group.ClearGroups()

    def AddGroupOn(self, group, alias=None):
        if alias is None:
            if '.' in group:
                alias = group.split('.')[1]
            else:
                alias = group
        addedGroup = self._info.group.AddGroup(group, alias)
        setattr(self, alias, None)

    def ChangeGroupExpression(self, alias, expr):
        g = self._info.group.groups
        for n, (g_expr, g_alias) in enumerate(g):
            if g_alias == alias:
                g[n][0] = expr
                return True
        raise Exception, "Group not found"

    def GetGroup(self):
        return self._info.group

    def _Aggregate(self, field, alias, atype, prefix):
        if alias is None:
            if '.' in field:
                alias = field.split('.')[1]
            else:
                alias = field
        self._info.group.Aggregate(field, alias, atype, prefix)
        setattr(self, prefix+(alias or ''), None)
        return self

    def AddTotalOf(self, field, alias=None):
        return self._Aggregate(field, alias, _AGGR_TOT, "total_")

    def AddCountOf(self, field, alias=None):
        return self._Aggregate(field, alias, _AGGR_CNT, "count_")

    def AddMinimumOf(self, field, alias=None):
        return self._Aggregate(field, alias, _AGGR_MIN, "min_")

    def AddMaximumOf(self, field, alias=None):
        return self._Aggregate(field, alias, _AGGR_MAX, "max_")

    def AddAverageOf(self, field, alias=None):
        self._info.group.Aggregate(field, alias, _AGGR_AVG, "avg_")
        return self

    def _MakeSQL_Fields(self, dbs):

        fields = ""
        offset = 0
        for db in dbs:

            nf = 0

            if not db._info.synthetized:
                for field in db._info.fields:
                    if '.' in field or field == "NULL":
                        fields += "%s, " % field
                    else:
                        fields += "%s.%s" % (db._info.tableAlias, field)
                        if db._info.fieldsAlias and field != "*":
                            fields += " AS %s_%s" % (db._info.tableAlias, field)
                        fields += ", "
                nf = len(db._info.fieldNames)

            af = db._info.addedFields
            for group, alias in db._info.group.groups:
                do = True
                for n in range(len(af)):
                    if af[n][1] == group:
                        do = False
                        break
                if do:
                    fields += group
                    if self._info.fieldsAlias:
                        if alias is None:
                            if not '.' in group:
                                group = "%s.%s" % (db._info.tableAlias, group)
                            alias = group.replace(".","_")
                        fields += " AS %s" % alias
                else:
                    fields += 'NULL'
                fields += ", "
                nf += 1

            for field, alias, aType in db._info.group.fields:
                if not '.' in field:
                    field = "%s.%s" % (db._info.tableAlias, field)
                if alias:
                    if db._info.fieldsAlias:
                        alias = " AS %s_%s" % (db._info.tableAlias, alias)
                    else:
                        alias = " AS %s" % alias
                else:
                    alias = ""
                if   aType == _AGGR_TOT:
                    fields += "SUM(%s)%s, " % (field, alias)
                elif aType == _AGGR_MAX:
                    fields += "MAX(%s)%s, " % (field, alias)
                elif aType == _AGGR_MIN:
                    fields += "MIN(%s)%s, " % (field, alias)
                elif aType == _AGGR_AVG:
                    fields += "AVG(%s)%s, " % (field, alias)
                elif aType == _AGGR_CNT:
                    fields += "COUNT(%s)%s, " % (field, alias)
                nf += 1

            for field, alias in db._info.addedFields:
                fields += field
                if alias:
                    fields += " AS %s" % alias
                fields += ", "
                nf += 1

            if self._info.iRoot is None and db != self:
                db._info.fieldsOffset = offset
            offset += nf

        fields = fields[:-2]

        return fields

    def _MakeSQL_Joins(self, dbs):
        tables = ""
        if len(dbs)>1:
            for child in dbs[1:]:#self._info.iChildrens:
                rel = child._info.relation
                if rel.joinType == JOIN_ALL:
                    tables += " INNER JOIN"
                elif rel.joinType == JOIN_RIGHT:
                    tables += " RIGHT JOIN"
                else:
                    tables += " LEFT JOIN"
                tables += " %s" % rel.rightTable
                if rel.rightTable != rel.rightAlias:
                    tables += " AS %s" % rel.rightAlias
                if rel.expression is None:
                    tables += " ON %s.%s %s %s.%s"\
                        % (rel.leftAlias, rel.leftId, rel.operator,\
                           rel.rightAlias, rel.rightId)
                else:
                    tables += " ON %s" % rel.expression
        return tables, []

    def SetRelation(self, expr):
        self._info.relation.expression = expr

    def _MakeSQL_Tables(self, dbs):

        tabFrom = self._info.tableName
        if self._info.tableName != self._info.tableAlias:
            tabFrom += " AS %s" % self._info.tableAlias
        tables = tabFrom #"%s%s" % ("("*(len(dbs)-1), tabFrom)

        tab, par = self._MakeSQL_Joins(dbs)
        tables += tab

        return tables, par

    def _GetITables(self, doJoins=True):
        dbs = [self]
        if doJoins:
            dbs = FindDbiChildrens(self)
        return dbs

    def _MakeSQL(self, filterExpr="", *filterParams, **kwargs):

        if not kwargs.has_key("doJoins"):   kwargs["doJoins"] =   True
        if not kwargs.has_key("unique"):    kwargs["unique"] =    False

        doJoins = kwargs["doJoins"]

        if kwargs.has_key("limit"):
            limit = kwargs["limit"]
        else:
            limit = self._info.limit

        params = []
        filters = []

        if filterExpr:
            #if len(filterParams) == 1:
                #filterParams = filterParams[0]
            filters.append((filterExpr, filterParams))

        #iRoot = self
        dbs = self._GetITables(doJoins)

        count_only = 'getcount' in kwargs
        if count_only:
            fields = "COUNT(*)"
            limit = limit_rows = None
        else:
            fields = self._MakeSQL_Fields(dbs)
            if kwargs.has_key("limit"):
                limit = kwargs["limit"]
            else:
                limit = self._info.limit
            if kwargs.has_key("limit_rows"):
                limit_rows = kwargs["limit_rows"]
            else:
                limit_rows = self._info.limit_rows

        tables, par = self._MakeSQL_Tables(dbs)
        params += par

        orders = []#self._info.orders

        for db in dbs:

            if db._info.basefilters:
                filters += db._info.basefilters

            if db._info.filters:# and\
               #(not filterExpr or\
                #(self._info.getFilters)):# and\
                 ##db._info.relation.joinType == JOIN_ALL)):
                filters += db._info.filters

            if db._info.orders:
                orders += db._info.orders

            del db._info.modifiedRecords[:]
            del db._info.deletedRecords[:]

        where = ""
        if filters:
            for expr, par in filters:
                if where: where += " and "
                where += "(%s)" % expr
                if "%" in expr.replace("%%",""): params += par#params.append(par)

        group = ""
        if self._info.group is not None:
            af = self._info.addedFields
            for grp,als in self._info.group.groups:
                do = True
                for n in range(len(af)):
                    if af[n][1] == grp:
                        do = False
                if do:
                    if not '.' in grp and not grp.startswith('('):
                        group += "%s." % self._info.tableAlias
                group += grp
                group += ", "
            group = group[:-2]

        havings = ""
        for db in dbs:
            for expr, par in db._info.group.filters:
                if havings: havings += " and "
                havings += "(%s)" % expr
                if r"%" in expr: params.append(par)

        order = ""
        for oExpr, oType in orders:
            if order:
                order += ", "
            order += oExpr
            if oType == ORDER_DESCENDING:
                order += " DESC"

        if doJoins:
            mParent = self._info.mParent
            if mParent:
                #keyName =  mParent._info.primaryKey
                #keyValue = mParent.__getattr__(keyName)
                keyName =  self._info.relation.rightId
                keyValue = self._info.relId
                rel = self._info.relation
                if where:
                    where += " and "
                where += "%s.%s " % (rel.rightAlias, rel.rightId)
                if rel.rightId is None or keyValue is None:
                    where += "IS NULL"
                    self._info.defaults[rel.rightId] = None
                else:
                    #if type(keyValue) == str:
                        #keyValue = "'%s'" % keyValue.replace("'","\\'")
                    where += "%s%%s" % rel.operator#, keyValue)
                    params.append(keyValue)
                    self._info.defaults[rel.rightId] = keyValue

        cmd = "SELECT %s" % fields

        if kwargs["unique"]:
            cmd += "DISTINCT "

        cmd += " FROM %s" % tables

        if where:
            cmd += " WHERE %s" % where
        if group:
            cmd += " GROUP BY %s" % group
        if havings:
            cmd += " HAVING %s" % havings
        if order:
            cmd += " ORDER BY %s" % order
        if limit is not None:
            if limit_rows is None:
                cmd += " LIMIT %d" % limit
            else:
                cmd += " LIMIT %d,%d" % (limit, limit_rows)

        if self._info.debug:
            print "="*60
            print "SQL Construct:\n%s" % cmd
            if params:
                print "   Parameters:\n%s" % params
            print "="*60

        return cmd, params

    def GetSqlCount(self, filterExpr="", *filterParams, **kwargs):
        kwargs['getcount'] = True
        return self.Retrieve(filterExpr="", *filterParams, **kwargs)

    def Retrieve(self, filterExpr="", *filterParams, **kwargs):
        """
        Retrieve data.
        """

        if not kwargs.has_key("doJoins"):   kwargs["doJoins"] =   True
        if not kwargs.has_key("refresh"):   kwargs["refresh"] =   False
        if not kwargs.has_key("nullread"):  kwargs["nullread"] =  False
        doJoins =  kwargs["doJoins"]
        refresh =  kwargs["refresh"]
        nullread = kwargs["nullread"]

        if nullread:

            self._MakeSQL_Fields(self._GetITables(doJoins))
            self._info.db.Reset()
            for db in self._GetITables(doJoins):
                db._info.db.Reset()
            logmsg('reset <%s> optimized' % self._info.tableName)
            success = True

        else:

            cmd, par = self._MakeSQL(filterExpr, *filterParams, **kwargs)

            if self._info.debug:
                print "***RETRIEVE***"

            if self._info.waitDialog is not None:
                wait = GetWaitDialogClass()(self._info.waitDialog, dataread=True)

            success = self._info.db.Retrieve(cmd, par,\
                                             asList=self._info.writable)

            if self._info.waitDialog is not None:
                wait.Destroy()

            if self._info.debug:
                if success:
                    print "Success=OK, %d rows extracted" % len(self._info.db.rs)
                else:
                    print "Extraction failed, reason: %s" % repr(self.GetError())

        if 'getcount' in kwargs:
            n = 0
            if len(self._info.rs)>0:
                if len(self._info.rs[0])>0:
                    n = self._info.db.rs[0][0]
            return n

        dbs = [self]
        if doJoins:
            dbs = FindDbiChildrens(self)

        if success:

            #suboffset = 0
            #def AddChildsOffsets(iRoot, stopDBT):
                #os = len(iRoot._info.fieldNames)
                #if iRoot._info.iChildrens:
                    #for child in iRoot._info.iChildrens:
                        #if child == stopDBT:
                            #break
                        #os += AddChildsOffsets(child, stopDBT)
                #return os

            #if self._info.iRoot:
                #suboffset = AddChildsOffsets(self._info.iRoot, self)

            self._info.dbError.Reset()
            if refresh:
                if self._info.db.rs:
                    for colNum, colVal in enumerate(self._info.db.rs[0]):
                        self._info.rs[self._info.recordNumber][colNum] =\
                            colVal
            else:
                if self._info.iRoot:
                    suboffset = self._info.fieldsOffset
                    #ensure ther is at least one record in recordset
                    if len(self._info.rs) == 0:
                        self._info.rs.append([None]*(self._info.fieldCount+
                                                     len(self._info.group.fields)))
                    #retrieve executed on joined table
                    #update main recordset
                    iRoot = self._info.iRoot
                    row = iRoot._info.recordNumber
                    if len(self._info.db.rs) >= 1:
                        rec = self._info.db.rs[0]
                        for col in range(len(rec)):
                            iRoot._info.rs[row][col+suboffset] = rec[col]
                    else:
                        for col in range(self._info.fieldCount):
                            iRoot._info.rs[row][col+suboffset] = None
                else:
                    #retrieve execute on main table, all records retrieved
                    #update internal main recordset
                    if self._info.writable:
                        #recordset is writable, so transform database
                        #specific recordset (tuple) into a list
                        del self._info.rs[:]
                        for rec in self._info.db.rs:
                            #self._info.rs.append(copy.deepcopy(rec))
                            self._info.rs.append(list(rec))
                        #self._info.rs = list(self._info.db.rs)
                    else:
                        #recordset is not writable, make database specific
                        #recordset (tuple) as the internal recordset
                        self._info.rs = self._info.db.rs
                    self._info.recordCount = len(self._info.rs)
                    self._info.recordNumber = 0
                    for db in dbs[1:]:
                        db._info.recordCount = 1
                        db._info.recordNumber = 0
                        db._info.dbError.Reset()
            self._UpdateTableVars(doJoins)
        else:
            print self._info.db.dbError.description
            for db in dbs:
                db.GetError()
                db._info.recordCount = -1
                db._info.recordNumber = -1

        return success

    def RowNumber(self):
        """
        Returns current cursor position in the internal recordset.
        """
        return self._info.recordNumber

    def RowsCount(self):
        """
        Returns number of records retrieved.
        """
        return max(self._info.recordCount, 0)

    def GetRecordset(self):
        """
        Returns internal recordset
        """
        return self._info.rs

    def SetRecordset(self, rs):
        """
        Sets internal recordset
        """
        self._info.rs = rs
        self._info.recordCount = len(rs)
        self._info.recordNumber = 0

    def GetFieldCount(self):
        """
        Returns retrieved fields number.
        """
        return len(self._info.fieldNames)

    def GetFieldNames(self):
        """
        Returns a list with all the retrieved fields.
        """
        return self._info.fieldNames

    def GetAllColumnsNames(self):
        """
        Returns a list with all the retrieved fields, plus field groups, aggregated fields and added fields
        """
        allcols = []
        allcols += self._info.fieldNames
        for g_expr, g_field in self._info.group.groups:
            allcols.append(g_field)
        for g_expr, g_field, g_type in self._info.group.fields:
            allcols.append(g_field)
        for g_expr, g_field in self._info.addedFields:
            allcols.append(g_field)
        return allcols

    def SetFieldNames(self, fn):
        """
        Set fields to retrieve.
        """
        self._info.fieldNames = fn
        self._info.fieldCount = len(fn)

    def GetFieldName(self, fieldNum):
        """
        Returns the name of the field at C{fielNum} position, empty string
        if not found.
        """
        try:
            name = self._info.fieldNames[fieldNum]
        except IndexError:
            name = ""
        return name

    def Locate(self, srcfunc, startPos=0):
        """
        Locate a record in the internal recordset matching condition
        expressed in function srcfunc, starting at startPos position
        (0=first record by default).
        Search is done by variable names and the entire dbtable is passed to
        the searching function for the filter evaluation.
        """
        found = False
        for recno in range(startPos, len(self._info.rs)):
            self.MoveRow(recno)
            if srcfunc(self):
                found = True
                break
        return found

    def LocateRow(self, srcfunc, startPos=0, position=True):
        """
        Locate a record in the internal recordset matching condition
        expressed in function srcfunc, starting at startPos position
        (0=first record by default).
        Search is done by direct recordset reference, no variable names are
        updated and only a row of the recordset is passed to the searching
        function for the filter evaluation.
        LocateRow is faster than Locate, especially on large recordsets;
        however, the searching function cannot test field variables (because
        they are not updated in the searching cycle): it must refer to the
        recordset columns by their indexes.
        """
        found = False
        for recno in range(startPos, len(self._info.rs)):
            rowrs = self.GetRecordset()[recno]
            if srcfunc(rowrs):
                if position:
                    self.MoveRow(recno)
                found = True
                break
        return found

    def LocateRS(self, srcfunc, startPos=0, position=True):
        """
        Locate a record in the internal recordset matching condition
        expressed in function srcfunc, starting at startPos position
        (0=first record by default).
        Search is done by direct recordset reference, no variable names are
        updated and only a row of the recordset is passed to the searching
        function for the filter evaluation.
        LocateRow is faster than Locate, especially on large recordsets;
        however, the searching function cannot test field variables (because
        they are not updated in the searching cycle): it must refer to the
        recordset columns by their indexes.
        If found, returns the row number, otherwise None.
        """
        found = False
        for recno in range(startPos, len(self._info.rs)):
            rowrs = self.GetRecordset()[recno]
            if srcfunc(rowrs):
                if position:
                    return recno
        return None

    def _GetFieldNames(self):
        """
        Internal, read field names from the table, and check primary key
        field position in fields list.
        """
        self._info.fieldCount = 0
        self._info.fieldNames = []
        self._info.primaryCol = -1
        for ncol, field in enumerate(self._info.description):
            fieldName = field[0]
            self._info.fieldNames.append(fieldName)
            self.__setattr__(fieldName, self._GetField(fieldName),\
                             setChanged=False)
            if field[0] == self._info.primaryKey:
                self._info.primaryCol = ncol
            self._info.fieldCount += 1

        if self._info.primaryCol < 0:
            raise Exception,\
                  """Unable to detect primary key column on table '%s'"""\
                  % self._info.tableName

        if len(self._info.fields) > 0:
            if self._info.fields[0] == "*":
                self._info.fields = []+self._info.fieldNames

        return self._info.fieldNames

    def _GetField(self, field, iRoot=True):
        """
        Internal, returns field content from the internal recordset.
        """
        value = None
        ncol = self._GetFieldIndex(field)
        if iRoot and self._info.iRoot:
            info = self._info.iRoot._info
            ncol += self._info.fieldsOffset
        else:
            info = self._info
        rs = info.rs
        recno = info.recordNumber
        if 0 <= recno < len(rs):
            value = rs[recno][ncol]
            if type(value) == unicode and FORCE_TO_LATIN1:
                value = value.encode('latin-1')
        return value

    def _GetFieldIndex(self, fieldName, inline=False):
        """
        Returns fieldName position in the internal fields list.
        """
        try:
            pos = self._info.fieldNames.index(fieldName)
            if inline:
                pos += self._info.fieldsOffset
        except:
            pos = None
            #campo non trovato, cerco su gruppi
            for n, (g_expr, g_field) in enumerate(self._info.group.groups):
                if g_field == fieldName:
                    pos = n
                    if not self._info.synthetized:
                        pos += len(self._info.fieldNames)
                    if inline:
                        pos += self._info.fieldsOffset
                    break
            if pos is None:
                #campo non trovato, cerco su campi aggregati
                for n, (a_expr, a_field, a_type) in enumerate(self._info.group.fields):
                    if a_field == fieldName:
                        pos = len(self._info.group.groups)+n
                        if not self._info.synthetized:
                            pos += len(self._info.fieldNames)
                        if inline:
                            pos += self._info.fieldsOffset
                        break
            if pos is None:
                #campo non trovato, cerco su campi aggiunti
                for n, (g_expr, g_field) in enumerate(self._info.addedFields):
                    if g_field == fieldName:
                        pos = len(self._info.group.groups)+len(self._info.group.fields)+n
                        if not self._info.synthetized:
                            pos += len(self._info.fieldNames)
                        if inline:
                            pos += self._info.fieldsOffset
                        break
        return pos

    def _IsDetailed(self):
        return len(self._info.group.fields) == 0 or\
               len(self._info.group.groups) > 0

    def GetFieldType(self, fieldName):
        """
        Returns fieldName type; it can be:
            string, int, float, mx.DateTime, object
        """
        info = self._info
        fieldInfo = info.description[self._GetFieldIndex(fieldName)]
        nType = fieldInfo[1]
        if   nType in info.db.TYPES_BINARY:   xType = object
        elif nType in info.db.TYPES_DATETIME: xType = DateTime
        elif nType in info.db.TYPES_FLOAT:    xType = float
        elif nType in info.db.TYPES_INT:      xType = int
        elif nType in info.db.TYPES_STRING:   xType = str
        else:                                 xType = None
        return xType

    def GetFilters(self):
        """
        Return active filters.
        """
        return self._info.filters

    def HasFilters(self):
        """
        Return active filters.
        """
        return len(self._info.filters)>0

    def MoveFirst(self):
        """
        Moves internal record pointer to the first one, and updates all the
        class field-variables.
        """
        self._info.recordNumber = 0
        self._UpdateTableVars()
        return True

    def MoveLast(self):
        """
        Moves internal record pointer to the last one, and updates all the
        class field-variables.
        """
        if self._info.flatView: self._RaiseFlatViewMoveError()
        self._info.recordNumber = self._info.recordCount-1
        self._UpdateTableVars()
        return True

    def CheckNextSkipping(self):
        """
        Check if a call to MoveNext will skip current row pointer.
        """
        willskip = True
        if self._info.flatView:
            for n in range(len(self._info.flatViewGroups), 0, -1):
                db = self._info.flatViewGroups[n-1]
                if not db.IsLastRow():
                    willskip = False
                    break
        return willskip

    def MoveNext(self):
        """
        Moves internal record pointer to the next one, and updates all the
        class field-variables.
        """
        move = True
        skipped = False
        if self._info.flatView:
            for n in range(len(self._info.flatViewGroups), 0, -1):
                db = self._info.flatViewGroups[n-1]
                if db.MoveNext():
                    skipped = True
                    move = False
                    break
        if move:
            if self._info.recordNumber < self._info.recordCount-1:
                self._info.recordNumber += 1
                self._UpdateTableVars()
                skipped = True
        return skipped

    def MovePrevious(self):
        """
        Moves internal record pointer to the previous one, and updates all
        the class field-variables.
        """
        if self._info.flatView: self._RaiseFlatViewMoveError()
        skipped = False
        if self._info.recordNumber > 0:
            self._info.recordNumber -= 1
            self._UpdateTableVars()
            skipped = True
        return skipped

    def MoveRow(self, recno):
        """
        Moves internal record pointer to the passed one, and updates all the
        class field-variables.  Raises an Exception in the passed number
        exceeds (or is equal to, record position is 0-offset) the number
        of records present.
        """
        skipped = False
        if self._info.flatView: self._RaiseFlatViewMoveError()
        if 0 <= recno < self._info.recordCount:
            if True:#recno != self._info.recordNumber:
                self._info.recordNumber = recno
                self._UpdateTableVars()
                skipped = True
        else:
            raise Exception,\
                  """Record %d not in range of %d records present"""\
                  % (recno, self._info.recordCount)
        return skipped

    def MoveNewRow(self):
        """
        Moves internal record pointer to the insertion one (-1)
        """
        if self._info.flatView: self._RaiseFlatViewMoveError()
        skipped = False
        if not self._info.writable:
            raise Exception,\
                  """Table '%s' is retrieved in readonly mode, """\
                  """cannot insert row""" % self._info.tableAlias
        #elif self._info.recordNumber == -1:
            #raise Exception,\
                  #"""Table '%s' is already on insert row"""\
                  #% self._info.tableAlias
        update = self._info.recordNumber != -1
        self._info.recordNumber = -1
        if update:
            self._UpdateTableVars()
        skipped = True
        return skipped

    def AppendNewRow(self, updateRS=True):
        """
        Stores all class field-variables on the internal recordset; for
        the effective database insertion, a call to Commit...() must be done.
        This last cannot be done until AppendNewRecord is performed.
        Normal usage is:
            if instance.MoveNewRow():
                <make some attribution, like instance.var = content>
                if instance.AppendNewRow():
                    instance.Save()
        For an immediate inserion on the table, see method New()
        """
        appended = False
        if not self._info.writable:
            raise Exception,\
                  """Table '%s' is retrieved in readonly mode, """\
                  """cannot append new record""" % self._info.tableName
        elif self._info.recordNumber != -1:
            raise Exception,\
                  """Cannot append new record now, move to inserting row """\
                  """first on table '%s'"""\
                  % self._info.tableName
        else:
            recno = len(self._info.rs)
            self._info.recordCount = recno+1
            totfields = self._info.fieldCount
            for tab in self._info.iChildrens:
                totfields += tab._info.fieldCount
            self._info.rs.append([None]*totfields)
            colno = 0
            if updateRS:
                for field in self._info.fieldNames:
                    self._info.rs[recno][colno] = self.__getattr__(field)
                    colno += 1
            self._info.recordNumber = recno
            appended = True
        return appended

    def Delete(self):
        return self.DeleteRow()

    def Erase(self):
        out = False
        if self.Delete():
            out = self._SaveRecords([], self._info.deletedRecords)
        return out


    def DeleteRow(self):
        """
        Phisically deletes the record on the table based on the internal
        record's id.  Raises an Exception on insert row.
        """
        deleted = False
        info = self._info
        if info.recordNumber < 0 and info.writable:
            raise Exception,\
                  """Deletion cannot be done on insert row"""
        elif info.recordNumber < 0:
            raise Exception,\
                  """Deletion cannot be done on this row"""
        elif not info.writable:
            raise Exception,\
                  """Table '%s' is retrieved in readonly mode, """\
                  """cannot delete""" % info.tableName
        elif info.iRoot:
            raise Exception,\
                  """Table '%s' is joined to '%s', """\
                  """no deletion can be done here"""\
                  % (info.tableName,\
                     info.iRoot._info.tableName)
        if 0 <= info.recordNumber < info.recordCount:
            id = info.rs[info.recordNumber][info.primaryCol]
            if id is not None and id not in self._info.deletedRecords:
                self._info.deletedRecords.append(id)
            del info.rs[info.recordNumber]
            info.recordCount -= 1
            if info.recordNumber >= info.recordCount:
                info.recordNumber -= 1
            self._UpdateTableVars()
            #after deletion, record cursor is on the following one
            #so for iterations we decrement iteration index and count
            self._info.iterIndex -= 1
            self._info.iterCount -= 1
            deleted = True
        return deleted

    def Save(self):
        return self.SaveAll()

    def SaveAll(self):
        """
        Causes a call to SaveRecord for all modified (or inserted) records.
        """
        return self._SaveRecords(self._info.modifiedRecords,\
                                 self._info.deletedRecords)

    def _UpdateMultiChildrens(self, masterId):
        """
        Updates multi joined tables (on insert/update)
        """
        #masterId shouls be None ONLY for deletions
        out = True
        #update all multijoined childrens
        for child in self._info.mChildrens:
            if child._info.writable:
                if masterId is not None:
                    child._SetForeignKey(masterId)
                    ncol = child._GetFieldIndex(
                        child._info.relation.rightId)
                    for i in range(child.RowsCount()):
                        child._info.rs[i][ncol] = masterId
                if not child.Save():
                    self.SetError(child._info.dbError)
                    out = False
                child.SetDebug(False)
        return out

    def _DeleteMultiChildrens(self, masterId):
        """
        Updates multi joined tables (on delete)
        """
        assert masterId is not None
        out = True
        #update all multijoined childrens
        for child in self._info.mChildrens:
            info = child._info
            if info.writable:
                cmd = "DELETE FROM %s WHERE %s.%s=%%s"\
                    % (info.tableName, info.tableName, info.relation.rightId)
                out = info.db.Execute(cmd, masterId)
        return out

    def WriteAll(self, wa=True):
        self._info.writeall = wa

    def AddDeletion(self, did):
        self._info.deletedRecords.append(did)

    def _SaveRecords(self, records, deletions):
        """
        Update all modified records on the table.
        For new records, a loop on inserted items is done and for each one
        the new id is retrieved from the database.
        For modified or deleted records, :db:executemany is used
        """
        written = False
        info = self._info
        if not info.writable:
            raise Exception,\
                  """Table '%s' is retrieved in readonly mode, """\
                  """cannot write""" % self._info.tableName

        setCol = ""
        for field in self._info.fieldNames:
            if (field != info.primaryKey or info.forceInsert):
                setCol += "%s=%%s, " % field
        setCol = setCol[:-2]

        curid = self.__getattr__(self._info.primaryKey)

        #search in the recordset to detect rows to update and insert
        recInsert = []
        parInsert = []
        parUpdate = []
        for recno in range(self.RowsCount()):
            recId = info.rs[recno][info.primaryCol]
            if recId is None or recId in records or info.writeall or info.forceInsert:
                # move to actual inserting record to update variables
                # if needed in (overriden) RecordInserting callback
                if recId is None or info.forceInsert:
                    self.RecordInserting(recno)
                par = []
                for field in self._info.fieldNames:
                    if (field != info.primaryKey or info.forceInsert):
                        colno = self._GetFieldIndex(field)
                        value = info.rs[recno][colno]
                        par.append(value)
                if recId is None or info.forceInsert:
                    parInsert.append(par)
                    recInsert.append(recno)
                else:
                    par.append(recId)
                    parUpdate.append(par)

        do = True
        self._info.dbError.Reset()

        #delete recordset deleted rows from table
        parDelete = deletions
        if parDelete and do and not info.forceInsert:
            cmdDelete = "DELETE FROM %s WHERE %s.%s=%%s"\
                      % (info.tableName, info.tableName, info.primaryKey)
            for recdel, pardel in enumerate(parDelete):
                if self._DeleteMultiChildrens(pardel):
                    if self._info.debug:
                        print "="*60
                        print "SQL Construct:\n%s" % cmdDelete
                        if parDelete:
                            print "   Parameters:\n%s" % parDelete
                        print "="*60
                    written = info.db.Execute(cmdDelete, pardel)
            #del deletions[:]

        #insert new rows into table
        if parInsert:
            cmdInsert = "INSERT INTO %s SET %s"\
                      % (info.tableName, setCol)
            for recins, parins in enumerate(parInsert):
                if self._info.debug:
                    print "="*60
                    print "SQL Construct:\n%s" % cmdInsert
                    if parins:
                        print "   Parameters:\n%s" % parins
                    print "="*60
                written = info.db.Execute(cmdInsert, parins)
                if written:
                    curid = info.db.GetInsertedId()

                    # update inserted id in the recordset
                    info.rs[recInsert[recins]][info.primaryCol] = curid

                    # update inserted id class variable
                    self.__setattr__(info.primaryKey, curid)

                    ## now refresh all columns in the current record
                    ## to update joined tables and eventually default
                    ## values defined at database level
                    ## recordset will not be modified, except for all
                    ## columns in the (just inserted) actual row
                    #filterExpr = "%s.%s=%%s"\
                               #% (self._info.tableAlias,\
                                  #self._info.primaryKey)
                    #self.Retrieve(filterExpr, curid, refresh=True)
                    self.RecordInserted()
                else:
                    do = False

        #update modified rows into table
        if parUpdate and do and not info.forceInsert:
            cmdUpdate = "UPDATE %s SET %s WHERE %s.%s=%%s"\
                      % (info.tableName, setCol, info.tableName,\
                         info.primaryKey)
            if self._info.debug:
                print "="*60
                print "SQL Construct:\n%s" % cmdUpdate
                if parUpdate:
                    print "   Parameters:\n%s" % parUpdate
                print "="*60
            for recupd, parupd in enumerate(parUpdate):
                curid = parupd[-1]
                self.RecordUpdating(parupd)
                do = info.db.Execute(cmdUpdate, parupd)
                if do:
                    self.RecordUpdated(parupd)
                else:
                    break
            del records[:]

        if do and curid:
            do = self._UpdateMultiChildrens(curid)

        return do

    def RecordInserting(self, row):
        """
        Callback before new record insertion into the database.
        Nothing happens here, override if needed.
        """
        return self

    def RecordInserted(self):
        """
        Callback after new record insertion into the database.
        Nothing happens here, override if needed.
        """
        return self

    def RecordUpdating(self, parupd):
        """
        Callback before record update into the database.
        Nothing happens here, override if needed.
        """
        return self

    def RecordUpdated(self, parupd):
        """
        Callback after record update into the database.
        Nothing happens here, override if needed.
        """
        return self

    def GetId(self):
        """
        Returns the record id.
        """
        return self.__getattr__(self._info.primaryKey)

    def GetTableName(self):
        """
        Returns managed table name.
        """
        return self._info.tableName

    def GetTableAlias(self):
        """
        Returns managed table alias.
        """
        return self._info.tableAlias

    def GetTable(self):
        """
        Returns self ref
        """
        return self

    def GetFieldFromRow(self, field, row):
        out = None
        if self._info.iRoot:
            root = self._info.iParent
        else:
            root = self
        if 0 <= row < root.RowsCount():
            col = self._GetFieldIndex(field)
            if col < 0:
                raise Exception,\
                      """Field %s not found on table '%s'"""\
                      % (field, self._info.tableAlias)
            out = root._info.rs[row][col]
        return out

    def Get(self, id, doJoins=True):
        """
        Retrieve record with corresponding id.
        Recordset will contain only the corresponding row, no rows if
        not found.
        """
        if id is None:
            id = -1
        if self._info.db._dbType == 'adodb':
            filter = "%s.%s='%s'" % (self._info.tableAlias,\
                                     self._info.primaryKey,\
                                     id)
        else:
            filter = "%s.%s=%%s" % (self._info.tableAlias,\
                                    self._info.primaryKey)
        nullread = (id == -1)
        success = self.Retrieve(filter, id, doJoins=doJoins, nullread=nullread)
        return success

    def New(self, **kwargs):
        """
        Automatically appends to the table the new record created on the fly
        by passing field values by keyword arguments.
        If defined, all the mandatory fields must be passed to New().
        """
        added = False
        for mfield in self._info.mandatoryFields:
            if not mfield in kwargs:
                raise Exception,\
                      """Cannot create new record on table '%s': """\
                      """mandatory field '%s' is missing"""\
                      % (self._info.tableName, mfield)
        if self._info.recordNumber != -1:
            self.MoveNewRow()
        self._SetDefaults()
        for field in kwargs:
            self.__setattr__(field, kwargs[field])
        if self.AppendNewRow():
            added = self.Save()
        return added

    def CreateNewRow(self):
        out = self.MoveNewRow()
        if out:
            out = self.AppendNewRow(updateRS=False)
            if out:
                self._SetDefaults(updateRS=True)
        return out

    def Reset(self):
        return self.Get(-1)

    def GetValue(self, field):
        try:
            out = self.__getattr__(field)
        except:
            out = None
        return out

    def IsEmpty(self):
        return self.RowsCount() == 0

    def OneRow(self):
        return self.RowsCount() == 1

    def LastRow(self):
        """
        Returns last row number (offset=0).
        """
        return self.RowsCount()-1

    def IsLastRow(self):
        """
        Returns True if record position is on the last one.
        """
        return self.RowNumber() < 0 or self.RowNumber() == self.LastRow()

    def IsNewRow(self):
        """
        Returns True if primary key is None.
        """
        return getattr(self, self._info.primaryKey) is not None

    def IsWritable(self):
        """
        Returns True if recordset is updatable.
        """
        return self._info.writable

    def HasError(self):
        return (self._info.dbError.code > 0) or\
               (self._info.dbError.description != "")

    def SetError(self, err):
        assert isinstance(err, DbError),\
               """Wrong error type"""
        info = self._info
        info.dbError.code =          err.code
        info.dbError.description =   err.description
        info.dbError.duplicatedKey = err.duplicatedKey

    def GetError(self):
        info = self._info
        info.dbError.Reset()
        ecode = info.db.dbError.code
        edesc = info.db.dbError.description
        edupk = info.db.dbError.code == info.db.DUPKEY_ERRCODE
        edupn = info.dbError.duplicatedKeyNumber
        if edupk:
            try:
                n = edesc.index('for key ')
                edupn = int(edesc[n+8:])
            except:
                pass
        info.dbError.code =          ecode
        info.dbError.description =   edesc
        info.dbError.duplicatedKey = edupk
        info.dbError.duplicatedKeyNumber = edupn
        return (ecode, edesc)

    def IsDuplicated(self):
        """
        Returns True if a duplicate key error is returned by the database
        after an insertion failure.
        """
        self.GetError()
        return self._info.dbError.duplicatedKey

    def GetDuplicatedKeyNumber(self):
        """
        Returns True if a duplicate key error is returned by the database
        after an insertion failure.
        """
        self.GetError()
        return self._info.dbError.duplicatedKeyNumber

    def StoreFilters(self):
        i = self._info
        i.filtersSaved.append(copy.deepcopy(i.filters))

    def DeletedRows(self):
        return self._info.deletedRecords

    def IsDeleted(self):
        curid = self.__getattr__(self._info.primaryKey)
        return curid in self._info.deletedRecords

    def HasModifies(self):
        """
        Checks wheter dbtable is modified or not: check is done over the
        recordset, it is true if a row is modified or deleted.
        It is recursively done on all multichildren also.
        """
        mod = len(self._info.modifiedRecords)>0
        if not mod:
            mod = len(self._info.deletedRecords)>0
        if not mod:
            for tab in self._info.mChildrens:
                mod = tab.HasModifies()
                if mod:
                    break
        return mod

    def ResumeFilters(self):
        i = self._info
        assert len(i.filtersSaved) > 0,\
               """No filters to resume"""
        i.filters = copy.deepcopy(i.filtersSaved[-1])
        i.filtersSaved.pop()

    def ForceBooleanFields(self, bools):
        if type(bools) in (str, unicode):
            bools = bools.split(',')
        elif type(bools) == tuple:
            bools = list(bools)
        self._info.fieldBooleans = bools

    def SetSilent(self, sil=True):
        self._info.updateMChildrens = not sil

    def SetRowModified(self):
        out = False
        if self.IsWritable():
            row = self.RowNumber()
            if 0 <= row < self.RowsCount():
                recid = self._info.rs[row][self._info.primaryCol]
                if not recid in (self._info.modifiedRecords):
                    self._info.modifiedRecords.append(recid)
                    out = True
        return out

    def _UpdateTableVars(self, iRoot=True):
        """
        Updates all the class field-variables in respect at the (class)
        cursor position; in the cursor is in insert position (-1), all
        the variables are initialized to None, except for that ones that
        have a default value (defined by dictionary in __init__).
        """
        success = True
        if iRoot and self._info.iRoot:
            infoRoot = self._info.iRoot._info
        else:
            infoRoot = self._info
        recno = infoRoot.recordNumber
        if -1 <= recno < infoRoot.recordCount:
            #record in recordset, updates variables and defaults
            for field in self._info.fieldNames:
                #retrieved columns
                self.__setattr__(field, self._GetField(field, iRoot),\
                                 setChanged=False)
            for expr, field in self._info.group.groups:
                #grouping fields
                self.__setattr__(field, self._GetField(field, iRoot),\
                                 setChanged=False)
            for a_expr, a_field, a_type in self._info.group.fields:
                #aggregated fields
                self.__setattr__(a_field, self._GetField(a_field, iRoot),\
                                 setChanged=False)
            for expr, field in self._info.addedFields:
                #added expressions
                self.__setattr__(field, self._GetField(field, iRoot),\
                                 setChanged=False)
            if recno == -1:
                self._SetDefaults()
        else:
            #empty recordset, reset all variables
            for field in self._info.fieldNames:
                #retrieved columns
                self.__setattr__(field, None, setChanged=False)
            for expr, field in self._info.group.groups:
                #grouping fields
                self.__setattr__(field, None, setChanged=False)
            for a_expr, a_field, a_type in self._info.group.fields:
                #aggregated fields
                self.__setattr__(a_field, None, setChanged=False)
            for expr, field in self._info.addedFields:
                #added expressions
                self.__setattr__(field, None, setChanged=False)

        #recursive variables update for all inline childrens
        if self._info.updateIChildrens:
            for child in self._info.iChildrens:
                child._UpdateTableVars()

        if self._info.updateMChildrens:
            success = success and self.UpdateChildrens()

        return success

    def UpdateChildrens(self):
        success = True
        #updates all multi-joined tables recordsets
        for child in self._info.mChildrens:
            relKey = child._info.relation.leftId
            relId = self.__getattr__(relKey)
            child._SetForeignKey(relId)
            if relId is None:
                ok = child.Get(-1)
            else:
                ok = child.Retrieve()
            if not ok:
                success = False
                raise Exception,\
                      """Problem retrieving related table """\
                      """'%s': %s, %s"""\
                      % (child._info.tableName,\
                         child._info.dbError.code,\
                         child._info.dbError.description)
        #updates all aggregated contents
        for child in self._info.aChildrens:
            relKey = child._info.relation.leftId
            relId = self.__getattr__(relKey)
            child._SetForeignKey(relId)
            if not child.Retrieve():
                success = False
                raise Exception,\
                      """Problem retrieving related table """\
                      """'%s': %s, %s"""\
                      % (child._info.tableName,\
                         child._info.dbError.code,\
                         child._info.dbError.description)
        return success

    def _ResetTableVar(self, field):
        if not field in self._info.fieldNames:
            raise Exception,\
                  """Field '%s' not in retrieved list of table '%s'"""\
                  % (field, self._info.tableAlias)
        valType = self.GetFieldType(field)
        if   valType == str:     newVal = str("")
        elif valType == unicode: newVal = unicode("")
        elif valType == int:     newVal = int(0)
        elif valType == float:   newVal = float(0)
        else:                    newVal = None
        self.__setattr__(field, newVal)

    def _SetDefaults(self, updateRS=False):
        """
        Internal, initializes field class vars with defaults values
        """
        for field, value in self._info.defaults.iteritems():
            self.__setattr__(field, value, setChanged=updateRS)

    def __repr__(self):
        try:
            r = "Table '%s'" % self._info.tableAlias
            if not self._info.writable:
                r += " (readonly)"
            if self._info.tableAlias != self._info.tableName:
                r += " (name='%s')" % self._info.tableName
            if self._info.recordCount < 0:
                r += ": empty recordset"
            else:
                if self._info.recordCount == 0:
                    r += ", no rows"
                else:
                    r += ", row %d/%d (row position is %d)"\
                      % (self._info.recordNumber+1, self._info.recordCount,\
                         self._info.recordNumber)
        except:
            r = object.__repr__(self)
        return r

    def __iter__(self):
        self._info.iterIndex = 0
        self._info.iterCount = self._info.recordCount
        return self

    def next(self):
        if self._info.iterIndex >= self._info.iterCount:
            raise StopIteration
        self.MoveRow(self._info.iterIndex)
        self._info.iterIndex += 1
        return self

    def __len__(self):
        return max(0, (self._info.recordCount or 0))

    def QuoteStart(self, string):
        return self._info.db.QuoteStart(string)

    def QuoteEnd(self, string):
        return self._info.db.QuoteEnd(string)

    def QuoteContent(self, string):
        return self._info.db.QuoteContent(string)

    def SetVar(self, name, value):
        self._info.externalData.dict[name] = value

    def GetVar(self, name):
        try:
            out = self._info.externalData.dict[name]
        except IndexError:
            out = None
        return out

    def DelVar(self, name):
        if self._info.externalData.dict.has_key(name):
            self._info.externalData.dict.pop(name)

    def GetCountOf(self, filtdef=None, func=None):
        """
        Counts records and return total(s).
        filtdef is a callable that filters the counting; for each row in the
        recordset, C{filtdef} is called with the recordset's row as parameter.
        C{filtdef] can be a tuple or a list of callables, in this case the
        method returns a tuple of counters, one for every C{filtdef} defined.
        C{func}, if defined, is called for each row in the recordset.
        """
        if type(filtdef) not in (tuple, list):
            filtdef = (filtdef,)
        numtot = len(filtdef)
        totals =  []
        filters = []
        for n, flt in enumerate(filtdef):
            if flt is None:
                flt = lambda *args: True
            totals.append(0)
            filters.append(flt)

        rs = self.GetRecordset()
        for row in range(self.RowsCount()):
            for n in range(numtot):
                if filters[n](rs[row]):
                    totals[n] += 1
            if func is not None:
                func(self, row)

        if numtot > 1:
            out = totals
        else:
            out = totals[0]

        return out

    def GetTotalOf(self, sumdef, cbf=None):
        """
        Sum column(s) and return total(s).
        sumdef can be a string (1 column sum) or a tuple of:
        - strings for more columns on the same table;
        - 2/3-tuples for columns on joined tables and/or for filtering
        rows:
        - dbtable if the column is on a joined table
        - column name
        - filter (optional): the row is added if this callable returns True;
        row number is passed.
        C{cbf}, if defined, is called for each row in the recordset.
        """
        if type(sumdef) in (str, unicode):
            sumdef = (sumdef,)
        numtot = len(sumdef)
        colpos =  []
        totals =  []
        filters = []
        for n, sdef in enumerate(sumdef):
            flt = lambda *args: True
            if type(sdef) in (str, unicode):
                tab = self
                col = sdef
            else:
                tab = sdef[0]
                col = sdef[1]
                try:
                    flt = sdef[2]
                except IndexError:
                    pass
            cp = tab._GetFieldIndex(col, inline=True)
            if cp<0:
                raise Exception,\
                      """Column '%s' not present in table '%s'"""\
                      % (col, tab.GetTableAlias())
            colpos.append(tab._GetFieldIndex(col, inline=True))
            totals.append(0)
            filters.append(flt)

        if self._info.iRoot is None:
            rs = self.GetRecordset()
            n = self.RowsCount()
        else:
            rs = self._info.iRoot.GetRecordset()
            n = self._info.iRoot.RowsCount()
        for row in range(n):
            for n in range(numtot):
                if filters[n](rs[row]):
                    totals[n] += rs[row][colpos[n]] or 0
            if cbf is not None:
                cbf(self, row)

        if numtot > 1:
            out = totals
        else:
            out = totals[0]

        return out

    def SetDebug(self, debug=True):
        self._info.debug=debug

    def SetFlatView(self, f=True):
        """
        Set flat view mode.
        In flat view mode, movement on the recordset is done in a flat view
        of the recordset itself; if there are multi join childrens on the table,
        movement are done in respect of that childrens: true movement on the
        recordset is performed only when all multi joined tables are on the
        last row.
        Here is an example:
        table a => moltijoined on table b => multi joined on table c
        a.MoveNext() causes:
        c.MoveNext() if c not on the lastrow, or
        b.MoveNext() if b not on the lastrow, or
        a.MoveNext() otherwise
        """
        self._info.flatView = f

    def IsFlatView(self):
        return self._info.flatView

    def ClearFlatViewGroups(self):
        """
        Clear all flat groups
        """
        del self._info.flatViewGroups[:]

    def AddFlatViewGroup(self, db):
        """
        Adds a flat group: it bust be a multijoined table
        """
        self._info.flatViewGroups.append(db)

    def _RaiseFlatViewMoveError(self):
        """
        Only MoveFirst and MoveNext can be done in flat view mode, here it is
        the errors raising when other movement methods are called
        """
        raise Exception,\
              """Sorry, only MoveNext in flat view mode"""

    def __setattr__(self, field, content, setChanged=True):
        try:
            if field in self._info.fieldBooleans and type(content) != int:
                if content:
                    content = 1
                else:
                    content = 0
        except:
            pass
        object.__setattr__(self, field, content)
        if field[:1] != "_":
            if self._info.iRoot:
                root = self._info.iRoot
            else:
                root = self
            row = root._info.recordNumber
            if 0 <= row < len(root._info.rs) and setChanged:
                #if self.IsWritable():
                    #ncol = self._GetFieldIndex(field)
                    #root._info.rs[row][ncol] = content
                    #if self is not root and self.RowsCount() == 1:
                        #ncol = self._GetFieldIndex(field, inline=False)
                        #self._info.rs[0][ncol] = content
                    #recid = self._info.rs[row][self._info.primaryCol]
                    #if not recid in (self._info.modifiedRecords):
                        #self._info.modifiedRecords.append(recid)
                #for child in self._info.iChildrens:
                    #if child._info.relation.leftId == field:
                        #child.Get(content)
                if root.IsWritable():
                    ncol = self._GetFieldIndex(field, inline=True)
                    if ncol is not None:
                        root._info.rs[row][ncol] = content
                        #if self is not root and self.RowsCount() == 1:
                            #ncol = self._GetFieldIndex(field, inline=False)
                            #self._info.rs[0][ncol] = content
                        recid = root._info.rs[row][root._info.primaryCol]
                        if not recid in (root._info.modifiedRecords):
                            root._info.modifiedRecords.append(recid)
                for child in self._info.iChildrens:
                    if child._info.relation.leftId == field:
                        child.Get(content)

#    def __getattr__(self, field):
#        value = None
#        if field[:1] != "_" and field in self._info.relTab:
#            n = self._info.relTab.index(field)
#            value = self._info.relDb[n]
#        else:
#            value = object.__getattribute__(self, field)
#        return value

    def __getattr__(self, field):
        return object.__getattribute__(self, field)

    def __getitem__(self, table):
        if type(table) in (str, unicode):
            info = self._info
            if table in info.relTab:
                n = info.relTab.index(table)
                return info.relDb[n]
        raise TypeError, """Scriptable index bust be a table name"""

    def _GetDbMem(self):
        raise Exception, "Not implemented"
        if self._info.iRoot:
            raise Exception, "Not implemented on joined table"

    def SeekOrCreate(self, key):
        """
        Searches for primary column value = key, creates a new row if not found
        Returns True if added
        """
        i = self._info
        rs = i.rs
        col = i.primaryCol
        add = True
        for row in range(i.recordCount):
            if rs[row][col] == key:
                self.MoveRow(row)
                add = False
                break
        if add:
            self.CreateNewRow()
            self.__setattr__(i.primaryKey, key)
        return add

    def _GetStructure(self):
        if self._info.db._dbType == 'mysql':
            des = self._info.description
            return tuple([(name, self._info.db.STRMAP_TYPES[mType], mLen, dec)
                          for name, mType, unk1, mLen, mLen2, dec, unk2 in des])

    def SavePosition(self):
        l=[[self, self.RowNumber()]]
        childs = self._info.relDb
        for child in childs:
            l+=child.SavePosition()
        return l

    def RestorePosition(self, lRecno):
        for t in lRecno:
            if self._info.debug:
                print "table:%s recno:%s" % (t[0], t[1])
            t[0]._ForceMoveRow(t[1])
        pass


    def _ForceMoveRow(self, recno):
        skipped = False
        if 0 <= recno < self._info.recordCount:
            self._info.recordNumber = recno
            self._UpdateTableVars()
            skipped = True
        return skipped

    def GetNewEAN13code(self, field, prefix=''):
        table = self._info.tableName
        cmd = "SELECT MAX(%s) FROM %s" % (field, table)
        if prefix:
            cmd += " WHERE %s LIKE '%s___________'" % (field, prefix)
        cur = self._info.db._dbCon.cursor()
        cur.execute(cmd)
        rs = cur.fetchone()
        cur.close()
        if rs:
            last = rs[0] or ''
        else:
            last = ''
        if last.startswith(prefix):
            last = last[len(prefix):]
        if len(last)>1:
            last = last[:-1]
        try:
            last = int(last)
        except ValueError:
            last = 0
        new = prefix+str(last+1).zfill(13-len(prefix)-1)
        import reportlab.graphics.barcode.eanbc as eanbc
        new += eanbc.Ean13BarcodeWidget._checkdigit(new)
        return new

    def ExportCSV(self, filename, progrfunc=None, expidcol=False, headings=True,
                  delimiter=None, quotechar=None,
                  doublequote=None, quoting=None):

        if delimiter is None: delimiter = CSVFORMAT_DELIMITER
        if quotechar is None: quotechar = CSVFORMAT_QUOTECHAR
        if doublequote is None: doublequote = True
        if quoting is None: quoting = int(CSVFORMAT_QUOTING)

        def strdate(x):
            if x is None: return ''
            return x.Format().split(' ')[0]
        def strnum(x):
            if x is None: return ''
            return locale.format('%.6f', x)
        def strbool(x):
            if x is None: return ''
            return [' ', 'X'][int(bool(x))]
        def strstr(x):
            if x is None: return ''
            return str(x)
        def strnone(x):
            return ''

        def strconv(val):
            if type(val) in (int, long):
                return locale.format('%.0f', val)
            if type(val) == float:
                return locale.format('%.6f', val)
            elif type(val) in (str, unicode):
                return val
            elif type(val) is bool:
                return [' ', 'X'][int(val)]
            elif type(val) is DateTime.Date:
                return val.Format().split(' ')[0]
            elif val is None:
                return ''
            else:
                pass

        if hasattr(filename, 'write'):
            fh = filename
        else:
            fh = open(filename, 'wb')

#        writer = csv.writer(fh)
#
#        d = writer.dialect
#        d.delimiter = CSVFORMAT_DELIMITER
#        d.quotechar = CSVFORMAT_QUOTECHAR
#        d.quoting = int(CSVFORMAT_QUOTING)

        writer = csv.writer(fh,
                            delimiter=delimiter,
                            quotechar=quotechar,
                            doublequote=doublequote,
                            skipinitialspace=False,
                            lineterminator='\r\n',
                            quoting=quoting)

        csvrs = []

        rs = self.GetRecordset()
        pkc = self._info.primaryCol

        if headings:
            #intestazioni di colonna
            csvrs.append([self.GetFieldName(col)
                          for col in range(self.GetFieldCount())
                          if col != pkc or expidcol])

        for row, rec in enumerate(rs):
            crs = []
            for col in range(self.GetFieldCount()):
                if col != pkc or expidcol:
                    val = rec[col]
                    crs.append(strconv(val))
            csvrs.append(crs)
            if callable(progrfunc):
                progrfunc(row, rec)

        writer.writerows(csvrs)

        if fh != filename:
            fh.close()

    def MakeFiltersDict(self, filters):
        assert isinstance(filters, (list, tuple))
        keys = {}
        for name, value in filters:
            keys[name] = value
        return keys


    def GetEnv(self):
        return self._info.GetEnv()


    # metodi di classe

    @classmethod
    def dita(self, date):
        out = None
        try:
            if date is not None: out = date.Format().split()[0]
        except:
            pass
        return out

    @classmethod
    def dhita(self, date):
        out = None
        try:
            if date is not None: out = '%s %s' % (date.Format().split())
        except:
            pass
        return out

    @classmethod
    def dtos(cls, date):
        out = ' '*8
        if date is not None:
            try:
                def z(n,l):
                    return str.zfill(str(n),l)
                out = z(date.year,4)+z(date.month,2)+z(date.day,2)
            except:
                pass
        return out

    @classmethod
    def sepn(cls, num, dec=0, sepm=True, zeroblank=False):
        num = num or 0
        if (num is None or num == 0) and zeroblank:
            out = ""
        else:
            out = locale.format("%%.%df" % dec, num, sepm, monetary=True)
        return out

    @classmethod
    def sepnvi(cls, num, dec=None, sepm=True, zeroblank=False):
        if dec is None:
            dec = NUMDEC_IMP
        return cls.sepn(num, dec, sepm, zeroblank)

    @classmethod
    def sepnpr(cls, num, dec=None, sepm=True, zeroblank=False):
        if dec is None:
            dec = NUMDEC_PRZ
        return cls.sepn(num, dec, sepm, zeroblank)

    @classmethod
    def sepnqt(cls, num, dec=None, sepm=True, zeroblank=False):
        if dec is None:
            dec = NUMDEC_QTA
        return cls.sepn(num, dec, sepm, zeroblank)

    @staticmethod
    def samefloat(f1, f2, dec=2):
#        return abs((f1 or 0)-(f2 or 0))<0.0000001
#        mask = '%%.%df' % dec
#        return (mask % (f1 or 0)) == (mask % (f2 or 0))
        if f1 is None:
            f1 = 0
        if f2 is None:
            f2 = 0
        mask = '%%.%df' % dec
        return (mask % (max(f1,f2)-min(f1,f2))) == (mask % 0)

    @staticmethod
    def round(value, decimals=0):
        return round(value, decimals)

    @classmethod
    def tabinfo(cls, tabname, tabid, field, pk='id'):
        out = None
        db = adb.db.__database__
        if db.Retrieve("SELECT %s FROM %s WHERE %s=%%s" % (field, tabname, pk), (tabid,)):
            if len(db.rs)>0:
                out = db.rs[0][0]
        return out

    @classmethod
    def sqlinfo(cls, sqlcmd, sqlpar=None):
        out = None
        sqlpar = sqlpar or []
        db = adb.db.__database__
        if db.Retrieve(sqlcmd, sqlpar):
            if len(db.rs) == 1:
                out = db.rs[0][0]
        return out

    @classmethod
    def iif(cls, test, v1, v2):
        if test:
            return v1
        return v2

    @classmethod
    def GetUnspecifiedVal(cls, val):
        if not val:
            val = '-n/s-'
        return val

    @classmethod
    def GetExternalInfo(cls, table, pkval, outcols, pkcol='id'):
        dbe = DbTable(table, primaryKey=pkcol)
        dbe.Get(pkval)
        if isinstance(outcols, basestring):
            out = getattr(dbe, outcols)
        else:
            out = []
            for outcol in outcols:
                out.append(getattr(dbe, outcol))
            out = tuple(out)
        return out

    # metodi proxy per DbInfo

    def ResetPrintFilterValues(self, *args, **kwargs):
        return self._info.ResetPrintFilterValues(*args, **kwargs)

    def SetPrintFilterValue(self, *args, **kwargs):
        return self._info.SetPrintFilterValue(*args, **kwargs)

    def GetPrintFilterValue(self, *args, **kwargs):
        return self._info.GetPrintFilterValue(*args, **kwargs)

    def HasPrintFilterValues(self, *args, **kwargs):
        return self._info.HasPrintFilterValues(*args, **kwargs)

    def SetPrintValue(self, *args, **kwargs):
        return self._info.SetPrintValue(*args, **kwargs)

    def GetPrintValue(self, *args, **kwargs):
        return self._info.GetPrintValue(*args, **kwargs)

    def DeletePrintValue(self, *args, **kwargs):
        return self._info.DeletePrintValue(*args, **kwargs)

    def ResetPrintValues(self, *args, **kwargs):
        return self._info.ResetPrintFilterValues(*args, **kwargs)

    # -----------------------------------------------------------------------
    #integrazioni per web

    def WebRetrieve(self, filterExpr="", *filterParams, **kwargs):
        if 'page_start' in kwargs:
            ps = kwargs.pop('page_start')
            if 'page_rows' in kwargs:
                pr = kwargs.pop('page_rows')
            else:
                pr = PAGE_ROWS
            self.SetPageRows(pr)
            self.SetLimits(pr*(ps-1)+0, pr)
        return self.Retrieve(filterExpr, *filterParams, **kwargs)

    def SetPageRows(self, pr):
        self._info.page_rows = pr

    def GetPageRows(self):
        return self._info.page_rows

    def GetSqlPage(self):
        return int(self._info.limit/self.GetPageRows()+.999)+1

    def GetSqlPagePrevious(self):
        return self.GetSqlPage()-1

    def GetSqlPageNext(self):
        return self.GetSqlPage()+1

    def GetSqlPages(self, **kwargs):
        pt = int(float(self.GetSqlCount(**kwargs))/self.GetPageRows()+.999)+1
        pa = self.GetSqlPage()
        if pt<=NAVIGATION_PAGES:
            ps = 1
            pe = pt
        else:
            ps = max(1, pa-int(NAVIGATION_PAGES/2))
            if ps == 1:
                pe = NAVIGATION_PAGES+1
            else:
                pe = min(ps+NAVIGATION_PAGES, pt)
        return range(ps, pe, 1)

    def GetSqlLastPage(self):
        return int(float(self.GetSqlCount())/self.GetPageRows()+.999)

    def GetSqlPagesLast(self):
        return self.GetSqlPages()[-1]

    def JSONdump(self, prefix, fields, item=''):
        """
        fields rappresenta l'elenco dei campi da serializzare
        vista la struttura della dbtable, tale elenco è strutturato come segue:
        lista/tupla di campi; ogni elemento e' a sua volta una lista/tupla di due
        elementi: il primo è la dbtable di riferimento, il secondo è il nome
        del campo
        Si consideri, per esempio, la dbtable seguente:
        pdc = DbTable('pdc')
        cli = pdc.AddJoin('clienti', 'cli', idLeft='id', idRight='id')
        in python, l'accesso al campo 'codice' su pdc si ha con 'pdc.codice',
        mentre l'accesso al campo 'citta' dei clienti si ha con 'pdc.cli.citta'
        Volendo serializzare codice, descrizione, citta si avra':
        pdc.JSONdump([[pdc, 'codice'], [pdc, 'descriz'], [pdc.cli, 'citta'])
        """
        #rscols = [['%s_%s' % (tab.GetTableAlias().replace('.', '_'), col), tab._GetFieldIndex(col, inline=True)] for tab, col in fields]
        rscols = [['%s_%s' % ({True: item, False: tab.GetTableAlias()}[len(item)>0].replace('.', '_'), col), tab._GetFieldIndex(col, inline=True)] for tab, col in fields]
        def GetValues(r):
            v = {}
            for name, index in rscols:
                if not isinstance(r[index],str):
                    v[name] = str(r[index])
                else:
                    v[name] = r[index]
            return v
#            rows = map(GetValues, self.GetRecordset())
#            return simplejson.dumps(rows)
#            base = ''
#            for r in self.GetRecordset():
#                base += '%s' % repr(GetValues(r))
        base = ', '.join(map(lambda x: repr(GetValues(x)), self.GetRecordset()))
        return '{"totalResultsCount":%d,"%s":[%s]}' % (self.RowsCount(), prefix, base)

#======================================================================================


    def SetConnectionStore(self, adbStore=None):
        if adbStore==None:
            if self.adbStore == None:
                import stormdb.dbsto as adbSto
                adbStore=adbSto.StoreConnection(globalConnection=False)
            else:
                adbStore=self.adbStore
        self.adbStore=adbStore

    def Store(self, adbStore=None):
        self.SetConnectionStore(adbStore)
        if self.CheckStore():
            self.Copy2Store()

    def CheckStore(self, adbStore=None):
        self.SetConnectionStore(adbStore)
        self.adeg={}
        self.CheckStoreTable()
        return self.Adegua()

    def Move2Store(self, adbStore=None):
        self.SetConnectionStore(adbStore)
        if self.pb:
            self.pb.SetRange(self.RowsCount())
        for i, r in enumerate(self):
            if self.pb:
                self.pb.SetValue(i)
            cmd='INSERT INTO %s ' % self.GetTableName()
            setCol = self.MakeSetExpression()
            cmd = '%s SET %s' % (cmd, setCol)
            cmd = cmd[:-2]
            if self.adbStore.Execute(cmd):
                cmd='DELETE FROM %s where ID=%s' % (self.GetTableName(), r.id)
                if not self._info.db.Execute(cmd):
                    logmsg('Move2Store - errore in execute command: %s' % cmd)
        if self.pb:
            self.pb.SetValue(0)

    def Copy2Store(self, adbStore=None):
        self.SetConnectionStore(adbStore)
        tabName=self._info.tableName
        fields=self.GetFieldNames()
        storeTable=DbTable(tabName, db=self.adbStore)
        self.Retrieve()
        if self.pb:
            self.pb.SetRange(self.RowsCount())
        for i, r in enumerate(self):
            if self.pb:
                self.pb.SetValue(i)

            storeTable.Retrieve('id=%s' % r.id)
            if not storeTable.OneRow():
                cmd='INSERT INTO %s ' % tabName
                setCol=self.MakeSetExpression(fields=fields)
                cmd = '%s SET %s' % (cmd, setCol)
                cmd = cmd[:-2]

                esito=self.adbStore.Execute(cmd)
                if not esito:
                    logmsg('Copy2Store - errore in execute command: %s' % cmd)
                storeTable.Retrieve('id=%s' % r.id)

            for fn in fields:
                setattr(storeTable, fn, getattr(self,fn ))
            storeTable.Save()

        if self.pb:
            self.pb.SetValue(0)


    def MakeSetExpression(self, fields=None):
        if fields==None:
            fields=self.GetFieldNames()
        setCol=''
        for fn in fields:
            v=getattr(self,fn )
            if not v==None:
                if isinstance(v, mx.DateTime._date) or isinstance(v, mx.DateTime._datetime):
                    setCol += '%s="%s", ' % (fn, v)
                elif isinstance(v, unicode) or isinstance(v, str):
                    v=v.replace('"', '\\"')
                    setCol += '%s="%s", ' % (fn, v)
                else:
                    setCol += '%s=%s, ' % (fn, v)
        return setCol


    def CheckStoreTable(self):
        import Env
        blobs = ("BLOB", "LONGBLOB", "VARBINARY", "VARCHAR", "TEXT")

        adeg = []
        bt = Env.Azienda.BaseTab
        t = aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == self._info.tableName)
        name, desc, stru, index, constr, voice =bt.tabelle[t]

        try:
            tab = DbTable(self._info.tableName, writable=False, db=self.adbStore)
            tab.Get(-1)
            tabchange = False
            tabcreate = False
            struphys  = tab._GetStructure()
            #controllo struttura campi
            for fname, ftype, flen, fdec, fnote, fspec in stru:
                change = False
                #test esistenza campo
                try:
                    n = aw.awu.ListSearch(struphys, lambda x: x[0] == fname)
                except IndexError:
                    adeg.append((fname, ADEG_MISSINGFIELD))
                    change = True
                #test congruenza tipologia
                if not change:
                    if not struphys[n][1] == "CHAR" and ftype == "STRING":
                        change = struphys[n][1] != ftype and not\
                               (struphys[n][1] in blobs and ftype in blobs)
                        if change:
                            adeg.append((fname, ADEG_WRONGTYPE))

                #test lunghezza
                if not change and flen:
                    change = struphys[n][2] < (flen + (fdec or 0))
                    if change:
                        adeg.append((fname, ADEG_WRONGLENGHT))

                #test decimali
                if not change and type(fdec) is int:
                    change = struphys[n][3] < fdec
                    if change:
                        adeg.append((fname, ADEG_WRONGDECIMALS))

                if change:
                    tabchange = True

            #controllo indici
            c = tab._info.db._dbCon.cursor()
            c.execute("SHOW INDEXES FROM %s" % name)
            rsi = c.fetchall()
            for i, (indtype, indexpr) in enumerate(index):
                if "PRIMARY" in indtype:
                    indname = "PRIMARY"
                    keydesc = "primaria"
                else:
                    indname = "index%d" % i
                    keydesc = "#%d" % i
                expr = ''
                for r in rsi:
                    if r[I_KEYNAME] == indname:
                        expr += ','+r[I_COLUMN]
                        isun = not r[I_NOTUNIQUE]
                if expr: expr = expr[1:]
                do = not expr == indexpr
                if not do:
                    stun = ("UNIQUE" in indtype or "PRIMARY" in indtype)
                    do = (stun and not isun) or (not stun and isun)
                if do:
                    if expr:
                        adegtype = ADEG_REINDEX
                    else:
                        adegtype = ADEG_INDEX
                    adeg.append(("Chiave "+keydesc, adegtype, i))
                    tabchange = True
            c.close()

        except Exception, e:
            #if '1146' in e.args[0]:
            err = e.args[0]
            if type(err) in (list, tuple):
                err = err[0]
            if '1146' in str(err):
                adeg.append(('-', ADEG_MISSINGTABLE))
                for i, (indtype, indexpr) in enumerate(index):
                    if "PRIMARY" in indtype:
                        indname = "PRIMARY"
                        keydesc = "primaria"
                    else:
                        indname = "index%d" % i
                        keydesc = "#%d" % i
                    adeg.append(("Chiave "+keydesc, ADEG_INDEX, i))
                tabcreate = True
            else:
                aw.awu.MsgDialog(self,\
                                 """Errore durante la lettura della """
                                 """tabella %s\n%s"""
                                 % (name, repr(e.args)))
                p = self.GetParent()
                if p.IsModal():
                    p.EndModal(2)
                else:
                    p.Close()

        if tabchange:
            self.adeg[name] = adeg

        elif tabcreate:
            self.adeg[name] = adeg
        else:
            pass

    def Adegua(self):
        import Env
        import wx
        errors = False

        bt = Env.Azienda.BaseTab
        db = self.adbStore

        for n, tab in enumerate(self.adeg):

            t = aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == tab)
            stru = bt.tabelle[t][bt.TABSETUP_TABLESTRUCTURE]
            indx = bt.tabelle[t][bt.TABSETUP_TABLEINDEXES]

            create = False
            if self.adeg[tab][0][1] == ADEG_MISSINGTABLE:
                cmd = "CREATE TABLE %s (" % tab
                diffs = [(c[bt.TABSETUP_COLUMNNAME], ADEG_MISSINGFIELD)
                         for c in stru]
                create = True
            else:
                cmd = "ALTER TABLE %s " % tab
                diffs = [(x[1], x) for x in self.adeg[tab] if x[1] < ADEG_INDEX]
                diffs.sort()
                diffs = [x[1] for x in diffs]

            diffs += [x for x in self.adeg[tab] if x[1] >= ADEG_INDEX]

            #diffs = lista differenze:
            #0 = nome colonna
            #1 = tipo differenza, ADEG_*
            #2 = (eventuale) numero indice da (ri)creare

            #creazione/adeguamento struttura campi
            for d in diffs:

                field = d[0]
                diff = d[1]

                if field == '-' or diff >= ADEG_INDEX:
                    continue

                if not create:
                    if diff == ADEG_MISSINGFIELD:
                        cmd += "ADD COLUMN "
                    else:
                        cmd += "MODIFY COLUMN "

                c = aw.awu.ListSearch(stru, lambda c: c[0] == field)
                col = stru[c]
                fname, ftype, flen, fdec, fadd, fdes =\
                     (col[bt.TABSETUP_COLUMNNAME],
                      col[bt.TABSETUP_COLUMNTYPE],
                      col[bt.TABSETUP_COLUMNLENGTH],
                      col[bt.TABSETUP_COLUMNDECIMALS],
                      col[bt.TABSETUP_COLUMNATTRIBUTES],
                      col[bt.TABSETUP_COLUMNDESCRIPTION])

                cmd += "%s %s" % (fname, ftype)

                if flen:
                    cmd += "(%d" % (flen + (fdec or 0))
                    if fdec:
                        cmd += ",%d" % fdec
                    cmd += ")"
                if fadd:
                    cmd += " %s" % fadd
                if fdes:
                    fdes = fdes.replace("'", "\\'")
                    fdes = fdes.replace("%", "perc.")
                    cmd += " COMMENT '%s'" % fdes
                cmd += ", "

            #creazione primary key
            if create:
                cmd += "PRIMARY KEY (%s), " % stru[0][bt.TABSETUP_COLUMNNAME]

            #creazione/adeguamento indici
            for d in diffs:
                if d[1] >= ADEG_INDEX:
                    i = d[2]
                    #cancellazione indice se incongruente
                    if d[1] == ADEG_REINDEX:
                        cmd += "DROP INDEX index%d, " % i
                    indtype, indexpr = indx[i]
                    #creazione nuovo indice
                    if not create:
                        cmd += "ADD "
                    if "UNIQUE" in indtype:
                        cmd += "UNIQUE "
                    else:
                        cmd += "INDEX "
                    cmd += "index%d (%s), " % (i, indexpr)

            cmd = cmd[:-2]
            if create:
                cmd += ") ENGINE = MYISAM"

            if not db.Execute(cmd):
                if create:
                    action = "la creazione"
                else:
                    action = "l'adeguamento di struttura"
                aw.awu.MsgDialog(self,
                                 """Si è verificato un problema durante """
                                 """%s della tabella %s:\n%s"""\
                                 % (action, tab, db.dbError.description))
                #self.GetParent().EndModal(2)
                errors = True
        return (not errors)

# ---------------------------------------------------------------------------


def SetForeignKeyTemplate(func):
    """
    Sets the template for foreign keys.
    Default can be one of the following:
        'id_tabname' if it is present in linked table fields list
        'id_aliasname' otherwise
    func is the function that returns the foreign key field name, following
    the preferred template.

    Example:
        SetForeignKeyTemplate(lambda x: "%sID") =>
        if related table is 'foo' aliased 'bar', then foreign key is
        assumed to be 'fooID' if there is a field called 'fooID', 'barID'
        otherwise.
    """

    global __fktemplate__
    __fktemplate__ = func


# ---------------------------------------------------------------------------


def FindDbiChildrens(iRoot):
    childs = [iRoot]
    for child in iRoot._info.iChildrens:
        childs += FindDbiChildrens(child)
    return childs


# ---------------------------------------------------------------------------


def FindAllDbmChildrens(mRoot):
    childs = mRoot._info.mChildrens
    iChilds = FindDbiChildrens(mRoot)
    for iChild in iChilds:
        childs += FindDbmChildrens(iChild)
    return childs


# ---------------------------------------------------------------------------


def GetHierarchy(root, level=0, tipo=0):
    iChildrens = root._info.iChildrens
    mChildrens = root._info.mChildrens
    hierarchy = [[level, tipo, root, iChildrens]]
    for childs, tipo in ((iChildrens, 0), (mChildrens, 1)):
        for child in childs:
            hierarchy += GetHierarchy(child, level+1, tipo)
    return hierarchy


# ---------------------------------------------------------------------------


def FindDbmChildrens(mRoot, offset=""):
    childs = mRoot._info.relDb

    #print mRoot.GetTableName()

    print "%s %s" % (offset, mRoot)
    offset=offset+"  | "
    for child in childs:
        childs += FindDbmChildrens(child, offset+"   ")
    return childs


# ------------------------------------------------------------------------------


class SubDbTable(DbTable):
    """
    Sublassed fromto DbTable, its table is another DbTable, to make
    a subselect:
        SELECT ... FROM (SELECT ... FROM ...) AS ...
    The SELECT construct inside parenthesis is obtained by passed
    DbTable SQL construct.
    Every column in the subquery recordset is prefixed with subquery
    table name followed by an undercore: table_column
    """
    def __init__(self, subTable, subAlias, primaryKey=None,\
                 fields="*", db=None, getFilters=None, debug=False):
        """
        Constructor.
        Parameters:
            DbTable object
            SubQuery alias name
            tabAlias  (string) table alias
            database  (DB) database object used to execute all the database
                      commands (default=__connection__)
        """
        if db is None: db = adb.db.__database__
        if db is None: raise Exception, "Database connection is missing"

        self._info = DbInfo()
        self._info.db = db
        self._info.tableName = subAlias
        self._info.tableAlias = subAlias
        self._info.subTable = subTable
        self._info.subAlias = subAlias
        self._info.writable = False
        self._info.iterIndex = 0
        self._info.iterCount = 0
        self._info.relId = None
        self._info.debug = debug

        if getFilters is not None:
            self._info.getFilters = getFilters

        innerTable = None
        db = self._info.subTable
        while True:
            db._info.level += 1
            if not isinstance(db, SubDbTable):
                innerTable = db
                if primaryKey is None:
                    if fields == "*":
                        primaryKey = "id"
                    else:
                        primaryKey = "%s_id" % db._info.tableAlias
                    for t in db._GetITables():
                        t._info.fieldsAlias = True
                break
            db = db._info.subTable

        self._info.primaryKey = primaryKey

        self._info.group = DbGroup()
        subTable.Get(-1)

        if fields is not None:
            if self._info.debug:
                print "Reading structure of '%s'" % self._info.subAlias
            self._SetFields(fields)
            if self._info.db._dbType == "mysql":
                tab, par = self._MakeSQL_Tables(self._GetITables())
                n = tab.rindex(")")
                tab = "%s LIMIT 0%s" % (tab[:n], tab[n:])
                cmd = "SELECT %s FROM %s"\
                    % (", ".join(self._info.fields),\
                        tab)
            elif self._info.db._dbType == "adodb":
                raise Exception, "Not implemented"
                #TODO: Da implementare subselect x adodb
            else:
                raise "Database type not recognized"
            innerTable._info.limit = 0
            if self.Retrieve():
                innerTable._info.limit = None
                self._info.description = self._info.db.description
                self._GetFieldNames()
                self.__setattr__(self._info.subTable._info.tableAlias, self._info.subTable)
            else:
                if self._info.debug:
                    print "Invalid SQL syntax:"
                    print cmd
                self.GetError()
                raise Exception,\
                      """Error retrieving '%s' structure: %d, %s"""\
                      % (subAlias, self._info.db.dbError.code,\
                         self._info.db.dbError.description)

    def _MakeSQL_Fields(self, *args, **kwargs):
        fields = DbTable._MakeSQL_Fields(self, *args, **kwargs)
        childs = []
        db = self
        while True:
            childs += FindDbiChildrens(db._info.subTable)
            db = db._info.subTable
            if not isinstance(db, SubDbTable): break
        #self._info.fieldsOffset = childs[-1]._info.fieldsOffset + len(childs[-1]._info.fieldNames)
        return fields

    def _MakeSQL_Tables(self, dbs):

        tab, par = self._info.subTable._MakeSQL()
        jtb, jpr = self._MakeSQL_Joins(dbs)
        par += jpr
        level = self._info.level+1
        return "(\n%s%s\n%s) AS %s%s" %\
            ('   '*level, tab, '   '*(level-1), self._info.subAlias, jtb), par

    def __repr__(self):
        try:
            if isinstance(self._info.subTable, SubDbTable):
                subType = "SubTable"
            else:
                subType ="DbTable"
            r = "SubTable '%s', external of %s '%s'" %\
                (self._info.tableAlias, subType, self._info.subTable._info.tableAlias)
            if not self._info.writable:
                r += " (readonly)"
            if self._info.tableAlias != self._info.tableName:
                r += " (name='%s')" % self._info.tableName
            if self._info.recordCount < 0:
                r += ": empty recordset"
            else:
                if self._info.recordCount == 0:
                    r += ", no rows"
                else:
                    r += ", row %d/%d (row position is %d)"\
                      % (self._info.recordNumber+1, self._info.recordCount,\
                         self._info.recordNumber)
        except:
            r = object.__repr__(self)
        return r

    def _UpdateTableVars(self, iRoot=True):
        success = DbTable._UpdateTableVars(self, iRoot)
        #recursive variables update for all inline childrens of any subtable
        if success:
            self._UpdateSubVars()
        return success

#    def Retrieve(self, *args, **kwargs):
#        success = DbTable.Retrieve(self, *args, **kwargs)
#        #recursive variables update for all inline childrens of any subtable
#        if success:
#            self._UpdateSubVars()
#        return success

    def _UpdateSubVars(self):
        childs = []
        db = self
        while True:
            childs += FindDbiChildrens(db._info.subTable)
            db = db._info.subTable
            if not isinstance(db, SubDbTable): break

        for child in childs:
            if child._info.fields:
                child._info.iRoot = self
                child._UpdateTableVars()

    def _GetFieldNames(self):
        """
        Internal, read field names from the table, and check primary key
        field position in fields list.
        """
        self._info.fieldCount = 0
        self._info.fieldNames = []
        self._info.primaryCol = -1
        for ncol, field in enumerate(self._info.description):
            fieldName = field[0]
            self._info.fieldNames.append(fieldName)
            self.__setattr__(fieldName, self._GetField(fieldName),\
                             setChanged=False)
            if fieldName == self._info.primaryKey:
                self._info.primaryCol = ncol
            self._info.fieldCount += 1

        #if self._info.primaryCol < 0:
            #raise Exception,\
                  #"""Unable to detect primary key column on table '%s'"""\
                  #% self._info.tableName

        return self._info.fieldNames

    def _GetField(self, field, iRoot=True):
        """
        Internal, returns field content from the internal recordset.
        """
        value = None
        ncol = self._GetFieldIndex(field, iRoot)
        info = self._info
        rs = info.rs
        recno = info.recordNumber
        if 0 <= recno < len(rs):
            value = rs[recno][ncol]
            if type(value) == unicode and FORCE_TO_LATIN1:
                value = value.encode('latin-1')
        return value


# ------------------------------------------------------------------------------


class DbMem(DbTable):
    """
    DbTable che opera in memoria
    """
    def __init__(self, fields=None, primaryKey=None, mandatoryFields="",\
                 defaults=None):
        if defaults is None:
            defaults = {}
        self._info = DbInfo()
        self._info.writable = True
        if mandatoryFields:
            self._info.mandatoryFields = mandatoryFields.split(",")
        else:
            self._info.mandatoryFields = []
        self._info.defaults = defaults
        self._info.iterIndex = 0
        self._info.iterCount = 0
        self._info.relId = None
        self._info.primaryKey = primaryKey
        self._info.primaryCol = 0
        self._info.group = DbGroup()
        if fields is not None:
            self._SetFields(fields)
            self._GetFieldNames()
        self.Reset()

    def SetRecordset(self, rs):
        assert type(rs) in (list, tuple)
        if len(rs)>0:
            assert len(rs[0]) == len(self._GetFieldNames())
        self._info.rs = rs
        self._info.recordCount = len(rs)
        self._info.recordNumber = -1
        self._info.iterCount = 0
        self._info.iterIndex = -1
        self.MoveFirst()

    def Reset(self, *args, **kwargs):
        del self._info.rs[:]
        self._info.recordCount = 0
        self._info.recordNumber = -1
        self._info.iterCount = 0
        self._info.iterIndex = -1

    def _SetFields(self, fields):
        """
        Internal, stores field names in a list.
        """
        if type(fields) in (str, unicode):
            fields = fields.split(",")
        self._info.fields = fields
        return self._info.fields

    def _GetFieldNames(self):
        self._info.fieldCount = 0
        self._info.fieldNames = []
        self._info.primaryCol = -1
        for ncol, field in enumerate(self._info.fields):
            fieldName = field
            self._info.fieldNames.append(field)
            self.__setattr__(fieldName, self._GetField(field),\
                             setChanged=False)
            if field == self._info.primaryKey:
                self._info.primaryCol = ncol
            self._info.fieldCount += 1

        return self._info.fieldNames

    def Retrieve(self, *args, **kwargs): pass
    def Get(self, *args, **kwargs): pass
    def _WriteRecords(self, *args, **kwargs): pass
    def __repr__(self):
        try:
            r = "DbMem"
            if self._info.recordCount < 0:
                r += ": empty recordset"
            else:
                if self._info.recordCount == 0:
                    r += ", no rows"
                else:
                    r += ", row %d/%d (row position is %d)"\
                      % (self._info.recordNumber+1, self._info.recordCount,\
                         self._info.recordNumber)
            return r
        except:
            return object.__repr__(self)

    def GetEnv(self):
        return self._info.GetEnv()


# ------------------------------------------------------------------------------


class SplittedTable(DbMem):

    def __init__(self, dbt, qtacol, colonne=1, func=None, qtadefault=None):
        assert isinstance(dbt, DbTable)
        fields = dbt.GetFieldNames()
        mycols = []
        for n in range(colonne):
            for c in fields:
                mycols.append('%s_%d' % (c, n))
        DbMem.__init__(self, ','.join(mycols))
        self._info.colonne = colonne
        self._info.currentcol = 0
        self._info.recordoffset = 0
        rs = dbt.GetRecordset()
        nc = 0
        newrow = []
        for r, row in enumerate(dbt):
            try:
                q = int(getattr(dbt, qtacol))
            except:
                if qtadefault is not None:
                    q = qtadefault
                else:
                    q = 0
            for c in range(q):
                newrow += copy.deepcopy(rs[r])
                nc += 1
                if nc >= colonne:
                    self._info.rs.append(newrow)
                    newrow = []
                    nc = 0
            if func is not None:
                func(r)
        if len(newrow)>0:
            if nc>0:
                newrow += (None,)*(len(mycols)*(colonne-nc))
                self._info.rs.append(newrow)
        self._info.recordCount = len(self._info.rs)
        self.MoveFirst()


# ------------------------------------------------------------------------------


class SplittedMultiEticTable(DbMem):

    def __init__(self, dbt, qtacol, colonne=1, func=None, qtadefault=None):
        assert isinstance(dbt, DbTable)
        dbs = dbt._GetITables()
        fields = dbt._MakeSQL_Fields(dbs).replace(' ', '').replace('.','_').split(',')
        mycols = []
        for n in range(colonne):
            for c in fields:
                mycols.append('%s_%d' % (c, n))
        DbMem.__init__(self, ','.join(mycols))
        self._info.colonne = colonne
        self._info.currentcol = 0
        self._info.recordoffset = 0
        rs = dbt.GetRecordset()
        nc = 0
        newrow = []
        for r, row in enumerate(dbt):
            try:
                q = int(getattr(dbt, qtacol))
            except:
                if qtadefault is not None:
                    q = qtadefault
                else:
                    q = 0
            for c in range(q):
                newrow += copy.deepcopy(rs[r])
                nc += 1
                if nc >= colonne:
                    self._info.rs.append(newrow)
                    newrow = []
                    nc = 0
            if func is not None:
                func(r)
        if len(newrow)>0:
            if nc>0:
                newrow += (None,)*(len(mycols)*(colonne-nc))
                self._info.rs.append(newrow)
        self._info.recordCount = len(self._info.rs)
        self.MoveFirst()


# ------------------------------------------------------------------------------


class MultiEticList(DbMem):

    def __init__(self, dbEtic, colonne=1):
        dbs = dbEtic._GetITables()
        fields = dbEtic._MakeSQL_Fields(dbs).replace(' ', '').replace('.','_').split(',')
        DbMem.__init__(self, ','.join(fields), 'id')
        self._info.dbetic = dbEtic
        self._info.colonne = colonne

#    def __setattr__(self, name, val, **kw):
#        adb.DbMem.__setattr__(self, name, val, **kw)
#        if name == 'id' and hasattr(self._info, 'dbetic'):
#            p = self._info.dbetic
#            if p.Get(val):
#                rs = self.GetRecordset()
#                for col in p.GetAllColumnsNames():
#                    if not col in ('id', 'qtaetic'):
#                        setattr(self, col, getattr(p, col))
#
    def GetPrintTable(self, rptdef, rows, cols, row0, col0,
                      startFunc=None, progrFunc=None, endFunc=None):
        rs0 = self._info.dbetic.GetRecordset()
        rsp = copy.deepcopy(rs0)
        self._info.colonne = cols
        if callable(startFunc):
            startFunc(self)
        pt = None
        try:
            if row0>1 or col0>1:
                rs = [None]*len(rsp[0])
                rs = [rs]*(cols*(row0-1)+col0-1)
                self._info.dbetic.SetRecordset(rs+rsp)
            pt = SplittedMultiEticTable(self._info.dbetic, 'qtaetic', self._info.colonne,
                                        progrFunc, qtadefault=1)
        finally:
            if callable(endFunc):
                endFunc(self)
        self.SetRecordset(rsp)
        self._info.dbetic.SetRecordset(rs0)
        return pt
