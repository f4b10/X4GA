#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         stormdb.dbsto
# Author:       Marcello
# Data:          03/ott/2015 - 10:09:20
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

import Env
import version
import MySQLdb
import stormdb as adb


_SUFFIX = 'a'

class StoreConnection(adb.DB):
    x4conn     = None
    dbconn     = None
    canProceed = None
    newDb      = None
    newCod     = None

    def __init__(self, *args, **kwargs):
        self.newDb  ='%s_%s' % (Env.Azienda.DB.schema, _SUFFIX)
        self.newCod ='%s_%s' % (Env.Azienda.codice, _SUFFIX)
        if len(self.newCod)>10:
            self.newCod='%s_%s' % (Env.Azienda.codice[0:(len(Env.Azienda.codice)-2)], _SUFFIX)

        self.SetX4Connection()
        self.canProceed=False
        if self.x4conn:
            if not self.ExistAzienda():
                if self.CreateAzienda():
                    self.canProceed=True
            else:
                self.canProceed=True

        if self.canProceed:
            self.canProceed=False
            if not self.ExistDb():
                self.CreateDb()
                if self.ExistDb():
                    self.canProceed=True
            else:
                self.canProceed=True

        if self.canProceed:
            adb.DB.__init__(self, *args, **kwargs)

            self.Connect(host =   Env.Azienda.DB.servername,
                         user =   Env.Azienda.DB.username,
                         passwd = Env.Azienda.DB.password,
                         db =     self.newDb)

    def CopyAllTable(self):
        bt = Env.Azienda.BaseTab
        for i, (name, desc, stru, index, constr, voice) in enumerate(bt.tabelle):
            sourceDb=adb.DbTable(name)
            sourceDb.Store(self)

    def ExistDb(self):
        lExist=False
        self.SetDbConnection()
        if self.dbconn:
            lExist=True
        return lExist

    def CreateDb(self):
        curs = self.x4conn.cursor()
        curs.execute("CREATE DATABASE %s;" % (self.newDb,))

    def CreateAzienda(self):
        prefix = 'ARCHIVIAZIONE'
        azienda = '%s - %s' % (prefix, Env.Azienda.descrizione)
        while len(azienda)>60:
            prefix=prefix[0:len(prefix)-1]
            azienda = '%s - %s' % (prefix, Env.Azienda.descrizione)

        nomedb  = self.newDb
        codice  = self.newCod
        modname = version.MODVERSION_NAME
        curs = self.x4conn.cursor()
        try:
            curs.execute("""
                        INSERT INTO aziende (azienda, nomedb, codice, modname)
                        VALUES (%s, %s, %s, %s)""", (azienda, nomedb, codice, modname))
            lEsito=True
        except:
            lEsito=False
        return lEsito

    def ExistAzienda(self):
        retValue=False
        curs = self.x4conn.cursor()
        curs.execute(r"SELECT azienda FROM aziende WHERE nomedb=%s;", (self.newDb,))
        rs = curs.fetchone()
        if rs:
            retValue=True
        return retValue

    def SetX4Connection(self):
        """
        Apre il database delle aziende
        """
        tryToOpenDB = False
        try:
            self.x4conn = MySQLdb.connect(host=Env.Azienda.DB.servername,
                                          user=Env.Azienda.DB.username,
                                          passwd=Env.Azienda.DB.password,
                                          db="x4")

        except MySQLdb.Error, e:
            #print 'errore in apertura database x4'
            pass


    def SetDbConnection(self):
        """
        Apre il database dell' azienda
        """
        lSuccess = False
        try:
            self.dbconn = MySQLdb.connect(host=Env.Azienda.DB.servername,
                                          user=Env.Azienda.DB.username,
                                          passwd=Env.Azienda.DB.password,
                                          db=self.newDb)
            self.dbconn.autocommit(True)
            lSuccess = True
        except MySQLdb.Error, e:
            #print 'errore in apertura database %s' % self.newDb
            pass


