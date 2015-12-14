#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stormdb.dbinnodb
# Author:       Marcello
# Data:          12/nov/2015 - 15:15:29
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

#CONSTRAINT `strumenti_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`id`)
import MySQLdb

import Env
bt = Env.Azienda.BaseTab

class ForeignKeys(list):
    def __init__(self):
        def getKey(item):
            return item[0]

        if self.SetInformationConnection():
            for n, tabstru in enumerate(bt.tabelle):
                for i in range(0,6):
                    if i==4 and not tabstru[i]==[]:
                        for nome, field, tipo in tabstru[i]:
                            self.append([nome, tabstru[0], field, tipo])
            self=sorted(self, key=getKey)

    def SetInformationConnection(self):
        """
        Apre il database delle aziende
        """
        try:
            self.infoconn = MySQLdb.connect(host=Env.Azienda.DB.servername,
                                            user=Env.Azienda.DB.username,
                                            passwd=Env.Azienda.DB.password,
                                            db="information_schema")
            tryToOpenDB = True

        except MySQLdb.Error, e:
            tryToOpenDB = False
            #print 'errore in apertura database x4'
            pass
        return tryToOpenDB


    def GetPhisicalIndex(self, table=None):
        lIndex=[]
        curs = self.infoconn.cursor()
        cmd=""
        cmd='%s %s' % (cmd, "select index_name, column_name, seq_in_index from INFORMATION_SCHEMA.statistics ")
        cmd='%s %s' % (cmd, 'where INDEX_NAME <> "PRIMARY" and table_schema="%s" '  % Env.Azienda.DB.schema)
        cmd='%s %s' % (cmd, 'AND table_name="%s" order by seq_in_index ' % table)
        curs.execute(cmd)
        rs = curs.fetchall()
        for r in rs:
            lIndex.append(r)
        return lIndex



    def GetPhisicalForeignKeys(self, table=None):
        lForeignKey=[]
        curs = self.infoconn.cursor()
        cmd=""
        cmd='%s %s' % (cmd, "SELECT * FROM information_schema.TABLE_CONSTRAINTS ")
        cmd='%s %s' % (cmd, "WHERE information_schema.TABLE_CONSTRAINTS.CONSTRAINT_TYPE = 'FOREIGN KEY'")
        cmd='%s %s' % (cmd, "AND information_schema.TABLE_CONSTRAINTS.TABLE_SCHEMA = '%s'" % Env.Azienda.DB.schema)
        cmd='%s %s' % (cmd, "AND information_schema.TABLE_CONSTRAINTS.TABLE_NAME = '%s'" % table)
        curs.execute(cmd)
        rs = curs.fetchall()
        for r in rs:
            k=r[2]
            cmd=""
            cmd='%s %s' % (cmd, "select * from INFORMATION_SCHEMA.KEY_COLUMN_USAGE" )
            cmd='%s %s' % (cmd, "where constraint_schema = '%s' and constraint_name = '%s'" % (Env.Azienda.DB.schema, k))
            curs.execute(cmd)
            rs1 = curs.fetchall()
            for r1 in rs1:
                lForeignKey.append(r1)
        return lForeignKey

    def GetForeignKeys(self, table=None):
        #CONSTRAINT `strumenti_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`id`)
        new= [x for x in self if x[0] == table]
        for k in new:
            #print k
            wrk='FK_%s_%s' % (k[0], k[2])
            #print 'indice:%s,\t Nome ForeignKey:%s,\t tabella esterna:%s,\t left:%s,\t right:%s' % (k[2], wrk, k[1], k[2], 'id')

    def GetForeignKeysIndex(self, table=None):
        #CONSTRAINT `strumenti_ibfk_1` FOREIGN KEY (`artist_id`) REFERENCES `artists` (`id`)
        return [x for x in self if x[0] == table]




#===============================================================================
# ALTER TABLE Orders
# DROP FOREIGN KEY fk_PerOrders
#===============================================================================

#===============================================================================
# ALTER TABLE Orders
# ADD FOREIGN KEY (P_Id)
# REFERENCES Persons(P_Id)
# To allow naming of a FOREIGN KEY constraint, and for defining a FOREIGN KEY constraint on multiple columns, use the following SQL syntax:
#
# MySQL / SQL Server / Oracle / MS Access:
#
# ALTER TABLE Orders
# ADD CONSTRAINT fk_PerOrders
# FOREIGN KEY (P_Id)
# REFERENCES Persons(P_Id)
#===============================================================================



