#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/utenti.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
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


import MySQLdb


class userMySql:
    
    def __init__(self):
        self.conn=None
        self.cursor=None
    
    def OpenMySqldb(self, hostname, username, password):
        """
        Apre il database delle aziende
        """
        retVal = False
        try:
            self.conn = MySQLdb.connect( host = hostname,
                                         user = username,
                                         passwd = password,
                                         db = "mysql" )
            self.cursor=self.conn.cursor()
            retVal = True
        except MySQLdb.Error, e:
            #print e
            pass
        return retVal

    def loadUserHost(self, username):
        hosts=[]
        sql="select host from user where user='%s';" % username
        if self.cursor.execute(sql)>=1:
            rs=self.cursor.fetchall()
            for x in rs:
                hosts=hosts+[x[0]]
            
        return hosts



    def userExist(self, username, host):
        lExist=False
        sql="select user, host from user where user='%s' and host='%s';" % (username, host)
        if self.cursor.execute(sql)>=1:
            lExist=True
        return lExist


    def setUserDbRight(self, username, host, dbName):
        if dbName:#len(dbName)>0:
            sql= "grant all on %s.* to '%s'@'%s' with grant option;" % (dbName, username, host)
            self.cursor.execute(sql)

    def criptoPassword(self, psw):
        sql = "select old_password('%s');" % psw
        self.cursor.execute(sql)
        rs=self.cursor.fetchone()
        return rs[0]
        

    def setUserPassword(self, username, host, psw):
        sql = "SET PASSWORD FOR '%s'@'%s' = '%s';" % (username, host, psw)
        self.cursor.execute(sql)
        
    def _userCreate(self, username, host, psw):
        sql = "create user '%s'@'%s' identified by '%s';" % (username, host, psw)
        self.cursor.execute(sql)

    def userCreate(self, username, psw, nomedb, accesso, hosts=['%', 'localhost']):
        lExist=False
        for host in hosts:
            if not self.userExist(username, host):
                self._userCreate(username, host, psw)
            self.setUserPassword(username, host, psw)
            self.setUserDbRight(username, host, 'x4')
            if accesso==1:
                self.setUserDbRight(username, host, nomedb)
        return lExist
        
    def _userDelete(self, username, host):
        sql= "drop user '%s'@'%s';" % (username, host)
        self.cursor.execute(sql)
        

    def userDelete(self, username):
        lExist=False
        sql= "select * from user where user='%s';" % username
        self.cursor.execute(sql)
        rs=self.cursor.fetchall()
        for x in rs:
            self._userDelete(x[1], x[0])
        
 
