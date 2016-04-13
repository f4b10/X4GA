#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         syncawc/layout/gestanag.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
# Copyright:    (C) 2016 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
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
import wx
import awc.controls.windows as aw
import stormdb as adb
import datetime
from xml.dom.minidom import Document
from xml.dom import minidom

import Env
bt = Env.Azienda.BaseTab

import os
import shutil
import stat
from time import sleep

import MySQLdb

def opj(x, y):
    return os.path.join(x, y).replace('\\', '/')

class SyncManager(object):
    ruolo = None

    def __init__(self):
        self.ruolo = bt.SYNCTIPOSERVER
        self.table2sync = bt.SYNCTABELLE.split('|')

    def SetLogger(self):
        import logging
        from logging.handlers import RotatingFileHandler
        logFile='%s.log' % os.path.join(self.GetLogPath(), '%03d' % self.GetActualUser() )
        if not os.path.exists(logFile):
            f = file(logFile, "w")
            f.close()
        self.logger = logging.getLogger('sync')
        #hdlr = logging.FileHandler(logFile)
        hdlr = RotatingFileHandler(logFile, maxBytes=50*1024,
                                  backupCount=10)


        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

    def CloseLogger(self):
        if hasattr(self, 'logger'):
            for h in self.logger.handlers:
                try:
                    h.close()
                    self.logger.removeHandler(h)
                except:
                    pass
            self.logger.handlers=[]


    def GetActualUser(self):
        return Env.Azienda.Login.userid

    def GetUserLastFile(self, idUser):
        return os.path.join(self.GetUsersPath(), '%03d' % idUser, '%03d.xml' % idUser)

    def GetBasePath(self):
        return bt.SYNCWRKDIR

    def GetUsersPath(self):
        return os.path.join(self.GetBasePath(), 'USERSYNC')

    def GetUpdatePath(self):
        return os.path.join(self.GetBasePath(), 'DATASYNC', 'UPDATE')

    def GetHistoryPath(self):
        return os.path.join(self.GetBasePath(), 'DATASYNC', 'HISTORY')

    def GetLogPath(self):
        path=os.path.join(self.GetBasePath(), 'DATASYNC', 'LOG', '%03d' % self.GetActualUser())
        if not os.path.exists(path):
            self._mkdir_recursive(path)
        return path

    def _mkdir_recursive(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def IsSyncronized(self):
        return (bt.SYNCFLAG==1)


    def IsMaster(self):
        return (self.ruolo=='M')

    def IsSlave(self):
        return (not self.ruolo=='M')

    def IsTable2Sync(self, tabname):
        return tabname in self.table2sync

    def NeedStore2Sync(self, tabName):
        lNeed=False
        if bt.SYNCFLAG==1:
            if self.IsMaster():
                if self.IsTable2Sync(tabName):
                    lNeed=True
        return lNeed

    def NeedSync(self):
        lNeed=False
        if bt.SYNCFLAG==1:
            if self.IsSlave():
                if '%s'% self.GetActualUser() in bt.SYNCDESTINATARI.split('|'):
                    lNeed=True
        return lNeed


    def GetVersion(self):
        self.version={}
        self.GetX4Version()
        self.GetCustVersion()
        self.GetPluginVersion()

    def GetPluginVersion(self):
        self.pluginVersion={}
        for p in Env.plugins:
            n2i = p
            ver='0.0.00'
            min_ver='0.0.00'
            if not n2i.endswith('_ver'):
                n2i += '_ver'
            try:
                m = __import__(n2i)
                if hasattr(m, 'version'):
                    ver=m.version
                if hasattr(m, 'min_compat_ver'):
                    min_ver=m.min_compat_ver
            except:
                pass
            self.version[p] = (ver, min_ver)

    def GetCustVersion(self):
        ver='0.0.00'
        min_ver='0.0.00'
        try:
            import custver
            ver=custver.v.__modversion__
            min_ver=custver.v.__min_compat_mod__
        except:
            pass
        self.version['cust'] = (ver, min_ver)

    def GetX4Version(self):
        ver='0.0.00'
        min_ver='0.0.00'
        try:
            import version
            ver=version.__version__
            min_ver=version.__min_compat_ver__
        except:
            pass
        self.version['X4'] = (ver, min_ver)

    def StoreUpdate(self, op=None, dbTable=None, recId=None, recNew=None, dataLink=None, fields=None):
        dValue={}
        dValue['operation']=op
        dValue['table']= dbTable
        if op=='DELETE':
            dValue['id']=recId
        else:
            if dataLink:
                for i, (col,ctr) in enumerate(dataLink):
                    dValue[col]=recNew[i]
            elif fields:
                for i, col in enumerate(fields):
                    dValue[col]=recNew[i]

        self.StoreXml(dValue)


    def StoreXml(self, dValue):
        try:
            cBasePath=self.GetUpdatePath()
            now    = datetime.datetime.utcnow()
            nowFile='%s-%s' % (now.strftime('%Y%m%d-%H%M%S'), '%04d' % (now.microsecond /1000))
            nowXml ='%s:%s' % (now.strftime('%Y%m%d-%H:%M:%S'), '%04d' % (now.microsecond /1000))
            doc=Document()
            root = doc.createElement("dbUpdate")
            for k in ['table', 'operation']:
                root.setAttribute( k, dValue[k] )
            root.setAttribute( 'datetime', '%s' % nowXml )
            doc.appendChild(root)

            root.appendChild(self.CreateVersionNode(doc))
            root.appendChild(self.CreateRecordNode(doc, dValue))

            pathName=os.path.join(cBasePath, '%s' % nowFile)
            self._mkdir_recursive(pathName)
            fileName=os.path.join(pathName, '%s.xml' % nowFile )
            doc.writexml( open(fileName, 'w'),
                          indent="  ",
                          addindent="  ",
                          newl='\n')
            doc.unlink()
            lEsito=True
        except:
            lEsito=False
        return lEsito

    def CreateVersionNode(self, doc):
        #-------------------------------------------
        version = doc.createElement("version")
        if not hasattr(self, "version"):
            self.GetVersion()
        x4_ver = doc.createElement("X4_version")
        v, mv = self.version['X4']
        x4_ver.setAttribute( 'version', v )
        x4_ver.setAttribute( 'min_version', mv )
        version.appendChild(x4_ver)

        cust_ver = doc.createElement("cust_version")
        v, mv = self.version['cust']
        cust_ver.setAttribute( 'version', v )
        cust_ver.setAttribute( 'min_version', mv )
        version.appendChild(cust_ver)

        plugin_ver = doc.createElement("plugin_version")

        for k in self.version:
            if not k in ['X4', 'cust']:
                v, mv = self.version[k]
                plugin = doc.createElement("plugin")
                plugin.setAttribute( 'name', k )
                plugin.setAttribute( 'version', v )
                plugin.setAttribute( 'min_version', mv )
                plugin_ver .appendChild(plugin)
        version.appendChild(plugin_ver)
        return version
        #-------------------------------------------

    def CreateRecordNode(self, doc, dValue):
        record = doc.createElement("record")
        for k in dValue:
            if not k in ['table', 'operation']:
                if not type(dValue[k]).__name__== 'NoneType':
                    field = doc.createElement("field")
                    field.setAttribute( 'name', k )
                    try:
                        if type(dValue[k]).__name__=='bool':
                            if dValue[k]:
                                dValue[k]=1
                            else:
                                dValue[k]=0
                        v=dValue[k]
                        v=v.encode('utf-8')
                        dValue[k]=v
                        field.setAttribute( 'value', '%s' % dValue[k] )
                    except:
                        field.setAttribute( 'value', '%s' % dValue[k] )
                    field.setAttribute( 'type', '%s' % type(dValue[k]).__name__ )
                    if k=='id':
                        field.setAttribute( 'primary_key', 'True' )
                    record.appendChild(field)
        return record


    def UpdateTables(self):
        import sync
        if not hasattr(self, 'logger'):
            self.SetLogger()
        dlg = sync.SyncDialog(manager=self)
        dlg.CenterOnScreen()
        dlg.ShowModal()
        dlg.Destroy()
        self.CloseLogger()



    def GetLastSyncDirName(self):
        lastName='%s' % self.ReadLastSyncDate().replace(':', '')
        return lastName

    def ReadLastSyncDate(self, idUser=None):
        lastTime=''
        if idUser==None:
            idUser=self.GetActualUser()
        userFile=self.GetUserLastFile(idUser)
        if os.path.exists(userFile):
            doc = minidom.parse(userFile)
            for r in doc.getElementsByTagName("lastUpdate"):
                lastTime=r.getAttribute("datetime")
            doc.unlink()
        return lastTime

    def UpdateFromXml(self, dir):
        lEsito=True
        fullPath=os.path.join(self.GetUpdatePath(), dir)
        fullName=os.path.join(fullPath, '%s.xml' % dir)
        if not os.path.exists(fullName):
            wait = aw.awu.WaitDialog(None, message="Attesa Dati x sincronizzazione...",
                                           maximum   = 60,
                                           style=wx.ICON_INFORMATION)
            for i in range(1,60):
                wait.SetMessage("%s" % i)
                if os.path.exists(fullName):
                    break
                sleep(1)
                wait.SetValue(i+1)
            try:
                wait.Destroy()
            except:
                pass
        if os.path.exists(fullName):
            #TODO: INSERIRE CONTROLLO SU CONGRUENZA VERSIONE
            spec=self.ReadXmlUpdate(fullName)
            if len(spec)>0:
                lEsito, msg=self.MakeUpdate(spec, dir)
            else:
                lEsito=False
                msg   = '%s %s'% (dir, 'IMPOSSIBILE ACQUISIRE I DATI DI SINCRONIZZAZIONE')
                self.logger.error(msg)
        else:
            msg='%s %s'% (dir, 'FILE XML INESISTENTE')
            self.logger.error(msg)
        return lEsito, msg

    def ReadXmlUpdate(self, fileName):
        updateSpec={}
        doc = minidom.parse(fileName)
        dbUpdateNode = doc.getElementsByTagName("dbUpdate")[0]
        if self.CheckVersion(dbUpdateNode):
            for k in ['datetime', 'operation', 'table']:
                updateSpec[k]=dbUpdateNode.getAttribute(k)
            recordNode   = dbUpdateNode.getElementsByTagName("record")[0]
            lField=[]
            for field in recordNode.getElementsByTagName("field"):
                spec={}
                for k in ['name', 'type', 'value', 'primary_key']:
                    spec[k] = field.getAttribute(k)
                lField.append(spec)
            updateSpec['record']=lField
        doc.unlink()
        return updateSpec


    def MakeMsg2View(self, updateDateTime, op, spec, errMsg=None):
        table=spec['table']
        codice=''
        descriz=''
        for f in spec['record']:
            if f['name']=='codice':
                codice=f['value']
            if f['name']=='descriz':
                descriz=f['value']
        msg=''
        if errMsg==None:
            if op=='UPDATE':
                msg='Aggiornamento nella tabella %s i dati di %s %s' % (table, codice, descriz)
            elif op=='INSERT':
                msg='Inserimento nella tabella %s i dati di %s %s' % (table, codice, descriz)
            elif op=='DELETE':
                msg='Eliminazione da tabella %s i dati di %s %s' % (table, codice, descriz)
            else:
                msg='Operazione sconosciut su tabelle %s' % table
        else:
            msg='Errore su tabella %s %s' % (table, errMsg)
        return '%s - %s ' % (updateDateTime, msg)

    def MakeUpdate(self, spec, updateDateTime):
        lOk=False
        sqlCmd=''
        op=spec['operation']
        if op=='UPDATE':
            if self.CheckUpdate(spec):
                sqlCmd=self.SqlUpdate(spec)
            else:
                sqlCmd=self.SqlInsert(spec)
                op='INSERT'
        elif op=='INSERT':
            if self.CheckInsert(spec):
                sqlCmd=self.SqlInsert(spec)
            else:
                sqlCmd=self.SqlUpdate(spec)
                op='UPDATE'
        elif op=='DELETE':
            sqlCmd=self.SqlDelete(spec)

        if len(sqlCmd)>0:
            if not hasattr(self, 'logger'):
                self.SetLogger()
            logRow='%s - ' % updateDateTime
            try:
                cur=Env.Azienda.DB.connection.cursor()
                cur.execute(sqlCmd)
                self.UpdateLastSyncDate(updateDateTime)
                lOk=True
                logRow='%s %s'% (logRow, sqlCmd)
                self.logger.info(logRow)
                msg=self.MakeMsg2View(updateDateTime, op, spec)
            except MySQLdb.Error, e:
                errMsg=''
                for msg in e:
                    errMsg='%s %s' % (errMsg, msg)
                logRow = '%s ***ERR*** %s %s' % (logRow, errMsg, sqlCmd)
                self.logger.error('%s %s'% (logRow, sqlCmd))
                msg=self.MakeMsg2View(updateDateTime, op, spec, errMsg=errMsg)
            except Exception, e:
                errMsg=''
                for msg in e:
                    errMsg='%s %s' % (errMsg, msg)
                logRow = '%s ***ERR*** %s %s' % (logRow, errMsg, sqlCmd)
                self.logger.error('%s %s'% (logRow, sqlCmd))
                msg=self.MakeMsg2View(updateDateTime, op, spec, errMsg=errMsg)
        return (lOk, msg)

    def CountById(self, spec):
        idPrimary=None
        for f in spec['record']:
            if f['primary_key']=='True':
                idPrimary=f['value']
                break
        if not idPrimary==None:
            sql='SELECT COUNT(*) FROM %s where ID=%s' % (spec['table'], idPrimary)
            cur=Env.Azienda.DB.connection.cursor()
            cur.execute(sql)
            nRecord=cur._rows[0][0]
        else:
            nRecord=self.Check4LinkTable(spec)
        return nRecord

    def Check4LinkTable(self, spec):
        nRecord = 0
        lFilter = self.GetUniqueKeyFilter4LinkTable(spec)
        for filter in lFilter:
            sql='SELECT COUNT(*) FROM %s where %s' % (spec['table'], filter)
            cur=Env.Azienda.DB.connection.cursor()
            cur.execute(sql)
            nRecord=cur._rows[0][0]
            if nRecord >0:
                break
        return nRecord

    def GetUniqueKeyFilter4LinkTable(self, spec):
        lFilter=[]
        defTable=filter(lambda x: x[0] == spec['table'], Env.Azienda.BaseTab.tabelle)
        defIndex=defTable[0][Env.Azienda.BaseTab.TABSETUP_TABLEINDEXES]
        for k in defIndex:
            if k[0]=='UNIQUE KEY':
                cFilter=''
                for f in k[1].split(','):
                    vl=filter(lambda x: x['name'] == f, spec['record'])[0]
                    v=vl['value']
                    exp='%s = %s' % (f, v)
                    cFilter='%s %s and ' % (cFilter, exp )
                if len(cFilter)>0:
                    cFilter=cFilter[:-5]
                lFilter.append(cFilter)
        return lFilter

    def CheckUpdate(self, spec):
        lOk=True
        if self.CountById(spec)==0:
            lOk=False
        return lOk

    def CheckInsert(self, spec):
        lOk=True
        if not self.CountById(spec)==0:
            lOk=False
        return lOk

    def CheckVersion(self, dbUpdateNode):
        lOk=True
        version=self.ReadVersionFromXml(dbUpdateNode)
        if not hasattr(self, "version"):
            self.GetVersion()
        for k in self.version:
            actual_ver, _ = self.version[k]
            _, required_ver = version[k]
            if actual_ver <required_ver:
                msg=u"Attenzione! Fino a quando non verrà effettuato l'aggiornamento del programma non sarà possibile effettuare la sincronizzazione dei dati."
                aw.awu.MsgDialog(None, msg, style=wx.ICON_ERROR|wx.OK)
                print 'NON AGGIORNO: modulo:%s  versione:%s vers.richiesta:%s ' % (k, actual_ver, required_ver)
                lOk=False
                break
        return lOk

    def ReadVersionFromXml(self, node):
        version={}
        versiondNode = node.getElementsByTagName("version")[0]
        for k in versiondNode.getElementsByTagName("plugin_version"):
            for k1 in k.getElementsByTagName("plugin"):
                version[k1.getAttribute('name')]=(k1.getAttribute('version'), k1.getAttribute('min_version'))

        for k in versiondNode.getElementsByTagName("cust_version"):
            version['cust']=(k.getAttribute('version'), k.getAttribute('min_version'))

        for k in versiondNode.getElementsByTagName("X4_version"):
            version['X4']=(k.getAttribute('version'), k.getAttribute('min_version'))
        return version

    def FieldXmlValue(self, type, value, name, table):
        if type=='int':
            v=int(value)
        elif type=='long':
            v=long(value)
        elif type == 'unicode' or type == 'str' :
            v='%s' % value
            v=v.replace('"', '""')
            v='"%s"' % v
        elif type == '_date':
            v='"%s"' % value
        elif  type=='float':
            v='%s' % value
        else:
            print 'tipo sconosciuto %s per il campo %s della tabelle %s' % (type, name, table)
            v='"%s"' % value
        return v


    def SqlUpdate(self, spec):
        keySpec=[]
        sql='UPDATE %s' % spec['table']
        sqlSet='SET'
        sqlWhere = ''
        for f in spec['record']:
            v=self.FieldXmlValue(f['type'], f['value'], f['name'], spec['table'])
            if f['primary_key']=='True':
                sqlWhere = 'WHERE %s=%s' % (f['name'], v)
            sqlSet = '%s %s=%s, ' % (sqlSet, f['name'], v)
        sqlSet = sqlSet[:-2]
        if len(sqlWhere)==0:
            lFilter=self.GetUniqueKeyFilter4LinkTable(spec)
            for filter in lFilter:
                sqlWhere='WHERE %s' % filter
                break
        sql= '%s %s %s' % (sql, sqlSet, sqlWhere)
        return sql

    def SqlInsert(self, spec):
        keySpec=[]
        sql='INSERT INTO %s' % spec['table']
        sqlSet='SET'
        sqlWhere = ''
        for f in spec['record']:
            v=self.FieldXmlValue(f['type'], f['value'], f['name'], spec['table'])
            sqlSet = '%s %s=%s, ' % (sqlSet, f['name'], v)
        sqlSet = sqlSet[:-2]
        sql= '%s %s' % (sql, sqlSet)
        return sql

    def SqlDelete(self, spec):
        keySpec=[]
        sql='DELETE FROM %s' % spec['table']
        sqlWhere = ''
        for f in spec['record']:
            v=self.FieldXmlValue(f['type'], f['value'], f['name'], spec['table'])
            if f['primary_key']=='True':
                sqlWhere = 'WHERE %s=%s' % (f['name'], v)
                break
        sql= '%s %s' % (sql, sqlWhere)
        return sql

    def UpdateLastSyncDate(self, LastSyncDate):
        userFile=self.GetUserLastFile(self.GetActualUser())
        if not os.path.exists(userFile):
            doc=Document()
            root = doc.createElement("lastUpdate")
            root.setAttribute( 'datetime', '%s' % LastSyncDate )
            doc.appendChild(root)
        else:
            doc = minidom.parse(userFile)
            root = doc.getElementsByTagName('lastUpdate')[0]
            root.setAttribute( 'datetime', '%s' % LastSyncDate )
            doc.appendChild(root)
        #doc.unlink()
        doc.writexml( open(userFile, 'w'),
                      indent="  ",
                      addindent="  ",
                      newl='\n')
        return LastSyncDate

    def RemoveOldUpdate(self):
        # Esamina quando i vari urtenti hanno acquisito gli aggiornamenti individuando
        # la data in cui l'utente meno aggiornato ha eseguito l'aggiornamento
        minUpdate=self.GetAlreadyUpdate()
        if len(minUpdate)>0:
            self.RemoveUpdate(minUpdate)

    def RemoveUpdate(self, startDate):
        def del_rw(action, name, exc):
            os.chmod(name, stat.S_IWRITE)
            os.remove(name)
        dirUpdate=self.GetUpdatePath()
        if not os.path.exists(dirUpdate):
            self._mkdir_recursive(dirUpdate)
        dirList=os.listdir(dirUpdate)
        for d in dirList:
            if d <= startDate:
                dirDel    =os.path.join(self.GetUpdatePath(), d)
                aa=d[:4]
                mm=d[4:6]
                gg=d[6:8]
                #dirHistory=os.path.join(self.GetHistoryPath(), d)
                dirHistory = os.path.join(self.GetHistoryPath(), aa, mm, gg, d)
                path, dir = os.path.split(dirHistory)
                if not os.path.exists(path):
                    self._mkdir_recursive(path)
                try:
                    shutil.move(dirDel, dirHistory)
                except:
                    pass

    def GetAlreadyUpdate(self):
        # Restituisce la data del più vecchio aggiornamento eseguito dai destinatari della
        # sincronizzazione
        minUpdate='99999999999'
        for d in bt.SYNCDESTINATARI.split('|'):
            idUser=int(d)
            minUpdate=min(minUpdate, self.ReadLastSyncDate(idUser))
        return minUpdate