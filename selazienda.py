#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         selazienda.py
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
Selezione azienda
=================
Consente di stabilire una connessione con il database delle aziende,
selezionare l'azienda di lavoro, effettuare l'autenticazione con i
parametri di username e password richiesti e di stabilire la data di
lavoro.

Consente inoltre di creare nuove aziende e di acquisire i dati da
installazioni di Mirage, compatibilmente con i privilegi dell'utente.

"""

import wx
import wx.lib.dialogs

import MySQLdb
import stormdb as adb

from mx import DateTime

import Env

from selazienda_wdr import *

import awc.controls.windows as aw

import stormdb as adb

import cfg.utenti as ute
import cfg.password as psw

import wx.lib.newevent
NewAziendaEvent, EVT_NEWAZI_CREATED = wx.lib.newevent.NewEvent()

import report


import wx.grid as gl
import awc.controls.dbgrid as dbglib

from cfg.cfgcontab import CfgContab


try:
    from dbfpy.dbf import Dbf #usato solo nel modulo di acquisizione da mirage
    import mirconv_acquis as miracq
#except ImportError:
except Exception, e:
    #aw.awu.MsgDialog(None, message=repr(e.args), style=wx.ICON_ERROR)
    miracq = None


class ListAziende(adb.DbMem):
    def __init__(self):
        adb.DbMem.__init__(self, 'id,codice,azienda,nomedb')


# ------------------------------------------------------------------------------


class SelAziendaGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbaz, *args, **kwargs):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbaz = dbaz
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        
        cols = (\
            ( 60, (cn(dbaz, "codice"),  "Cod.",    _STR, True)),
            (100, (cn(dbaz, "azienda"), "Azienda", _STR, True)),
            (  1, (cn(dbaz, "id"),      "#azi",    _STR, True)),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(dbaz.GetRecordset(), colmap, canedit, canins)
        
        ca = self.colAttr
        face = 'Bitstream Vera Sans'
        ca[0].SetFont(wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL, False, face))
        ca[1].SetFont(wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD, False, face))
#        self.SetRowHeight(20)
        #self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class SelAziendaPanel(aw.Panel):
    """
    Selezione azienda di lavoro.
    
    Vengono settati:
    database dell'azienda
    descrizione dell'azienda
    nome utente
    data di elaborazione
    
    Il Dialog di selezione è modale, e ritorna:
    ID_SELECTED se è avvenuta correttamente la selezione azienda e l'autenticazione
    ID_QUIT     altrimenti
    """
    
    ID_SELECTED = 1
    ID_QUIT = 0
    
    dbaz = None
    x4conn = None
    pswAdmin = None
    supervisor = False

    def __init__(self, *args, **kwargs):
        """
        Costruttore panel selezione azienda.
        """
        
        aw.Panel.__init__(self, *args, **kwargs)
        self.dbaz = ListAziende()
        self.login = True
        
        def ci(x):
            return self.FindWindowById(x)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        SelAziendaFunc(self)
        cn('plugins').Hide()

        self.Fit()
        self.Layout()
        
        self.gridaz = SelAziendaGrid(ci(ID_LISTAZIENDE), self.dbaz)
        
        ci(ID_USER).SetValue(Env.Azienda.config.get('Database', 'user'))
        
        def fmt(x):
            return str(x or '').replace('&', '&&')
        l = Env.Azienda.license
        
        self.LoadServerName()
        
        ci(ID_DATAELAB).SetValue(DateTime.today())
        
        self.UpdateUserControls()
        
        for evt, func, cid in ((wx.EVT_BUTTON, self.OnLogin,    ID_LOGIN),
                               (wx.EVT_BUTTON, self.OnSelect,   ID_BTNAZISEL),
                               (wx.EVT_BUTTON, self.OnCreate,   ID_NEWAZI),
                               (wx.EVT_BUTTON, self.OnUtenti,   ID_UTENTI),
                               (wx.EVT_BUTTON, self.OnWksSetup, ID_WKSETUP),
                               (wx.EVT_BUTTON, self.OnChgPsw,   ID_CHANGEPWD),
                               (wx.EVT_CHOICE, self.OnServer,   ID_SERVER),
                               ):
            self.Bind(evt, func, id=cid)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        
        self.SetAcceleratorKey('N', ID_NEWAZI,  'Nuova Azienda',     'Crea una nuova azienda')
        self.SetAcceleratorKey('U', ID_UTENTI,  'Setup Utenti',      'Richiama la gestione degli utenti')
        self.SetAcceleratorKey('W', ID_WKSETUP, 'Setup Workstation', 'Richiama l\'impostazione della workstation')
        
        self.Bind(gl.EVT_GRID_SELECT_CELL,      self.OnAziMove, self.gridaz)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSelect,  self.gridaz)
        self.gridaz.Bind(wx.EVT_KEY_DOWN, self.OnTestGridChar)
        
        self.Bind(EVT_NEWAZI_CREATED, self.UpdateAziende)
        
        self.test_mod_name = True
        ci(ID_PSWD).Bind(wx.EVT_KEY_DOWN, self.OnTestKey)
        ci(ID_PSWD).Bind(wx.EVT_KEY_UP, self.OnTestKey)
        
        self.UpdateServerUrl(0)
    
    def OnTestKey(self, event):
        self.test_mod_name = not event.ControlDown()
        event.Skip()
    
    def OnTestGridChar(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_RETURN or key == 370: #370=enter del tastierino num.
            self.AziSelect()
        event.Skip()
    
    def OnAziMove(self, event):
        wx.CallAfter(self.UpdateAziendaDetails)
        event.Skip()

    def OnWksSetup(self, event):
        import os
        def opj(x,y):
            return os.path.join(x,y).replace('\\','/')
        config = Env.GeneralSetup()
        import cfg.wksetup as wks
        d = wks.WorkstationSetupDialog()
        d.setConfig(config)
        if not d.ShowModal() == 1:
            out = False
        d.Destroy()
        config.loadHosts()
        self.LoadServerName()
    
    def LoadServerName(self):
        """
        Vengono caricati nel controllo di scelta Server, l'elenco dei server presenti nel file di
        configurazione CONFIG.INI
        """
        sl = self.FindWindowById(ID_SERVER)
        sl.GetCount()
        for i in range(sl.GetCount()-1,-1, -1):
            sl.Delete(i)
        for s in Env.dbservers:
            if s[1]==None:
                pass
            else:
                sl.Append(s[1], s[0])
        sl.SetSelection(0)
    
    def OnChgPsw(self, event):
        cn = lambda x: self.FindWindowById(x)
        host, user, pwd = [cn(x).GetValue() 
                           for x in(ID_SERVER, ID_USER, ID_PSWD)]
        chgPswType=0
        if len(pwd)==0:
            chgPswType=1
        changepsw = psw.PswDialog( username=user, password=pwd, msgType=chgPswType, pswAdmin=self.pswAdmin )
        changepsw.ShowModal()
        changepsw.Destroy()
        self.OnLogin(event)
        cn(ID_PSWD).SetValue("")
        event.Skip()
    
    def OnServer(self, event):
        self.UpdateServerUrl(event.GetEventObject().GetSelection())
        event.Skip()
    
    def OnLogin(self, event):
        cn = lambda x: self.FindWindowById(x)
        if self.login:
            cfg = Env.Azienda.config
            sec = 'MySQL'
            n = cn(ID_SERVER).GetSelection()
            if n>0:
                sec += str(n)
            host, user, pswd = map(lambda x: cfg.get(sec, x),
                                   ('host', 'user', 'pswd'))
            x4user, x4pswd = [cn(x).GetValue() for x in(ID_USER, ID_PSWD)]
            
            if self.OpenX4db(host, user, pswd):
                
                if self.AutorizzoUser(x4user, x4pswd):
                    
                    cfg.set('Database', 'user', x4user)
                    cfg.write()
                    
                    now = DateTime.now()
                    if    4 < now.hour <= 14:
                        welcome = "Buongiorno"
                    elif 14 < now.hour <= 17:
                        welcome = "Buon pomeriggio"
                    elif 17 < now.hour <= 22:
                        welcome = "Buonasera"
                    else:
                        welcome = "Ciao"
                    welcome += " "+user
                    
                    self.login = False
                    
                    self.ReadAziende()
                    
                    c = self.x4conn.cursor()
                    c.execute("SELECT id, codice, amministratore FROM utenti WHERE descriz=%s", x4user)
                    rs = c.fetchone()
                    Env.Azienda.Login.username = x4user
                    Env.Azienda.Login.userid = rs[0]
                    Env.Azienda.Login.usercode = rs[1]
                    self.supervisor = (rs[2] == "X")
                    c.close()
                    
                    x4db = adb.DB(globalConnection=False)
                    x4db.Connect(host=Env.Azienda.DB.servername,
                                 user=Env.Azienda.DB.username,
                                 passwd=Env.Azienda.DB.password,
                                 db='x4')
                    u = adb.DbTable('utenti', db=x4db)
                    u.Get(Env.Azienda.Login.userid)
                    Env.Azienda.Login.userdata = u
                    x4db.Close()
                    
                    if len(x4pswd)==0:
                        self.OnChgPsw(event)
                        self.login = False
                else:
                    self.login = True
                    self.gridaz.Reset()
        else:
            self.login = True
            self.gridaz.Reset()
        
        self.UpdateUserControls()
        self.UpdateAziendaDetails()
        event.Skip()

    def AutorizzoUser(self, user, psw):
        
        c = self.x4conn.cursor()
        if (c.execute("SELECT psw FROM utenti WHERE descriz=%s", user)>0):
            psw_memo = c.fetchone()[0]
            c.execute("select old_password(%s)", psw)
            psw_digi=c.fetchone()[0]
        else:
            psw_memo='1'
            psw_digi='2'
        
        if (psw_memo <> psw_digi):
            dlg = wx.MessageDialog(
                parent=None,
                message = "Utente non autorizzato!\nVerificare nome utente e password e riprovare.",
                caption = "X4 :: Errore",
                style = wx.OK|wx.ICON_WARNING)
            dlg.ShowModal()
            dlg.Destroy()
        
        ok = (psw_memo==psw_digi)
        if ok:
            try:
                c.execute("SELECT max_sqlrows FROM utenti WHERE descriz=%s", user)
                maxrows = c.fetchone()[0]
                Env.SetUserMaxSqlCount(maxrows)
                import awc.controls.linktable as lt
                lt.SetMaxSqlCount(maxrows)
            except:
                pass
            
        return ok

    def OnSelect(self, event):
        self.AziSelect()
        event.Skip()
    
    def AziSelect(self):
        
        retVal = 0
        errMessage = None
        
        def ErrMsg(msg):
            aw.awu.MsgDialog(self, message=msg, style=wx.ICON_EXCLAMATION)
        
        dbaz = self.dbaz
        
        row = self.gridaz.GetSelectedRows()[0]
        if row >= self.dbaz.RowsCount():
            ErrMsg("Nessuna azienda selezionata")
            return 0
        
        dbaz.MoveRow(row)
        
        codice, nomeazi, nomedb = dbaz.codice, dbaz.azienda, dbaz.nomedb
        
        ctrUser = self.FindWindowById(ID_USER)
        ctrPswd = self.FindWindowById(ID_PSWD)
        if len(ctrPswd.GetValue())==0:
            ErrMsg("La password è obbligatoria")
            return 0
        
        username = ctrUser.GetValue()
        password = ctrPswd.GetValue()
        
        if len(username) == 0:
            ErrMsg("Indicare il nome dell'utente")
            return 0
        
        data = self.FindWindowById(ID_DATAELAB).GetValue()
        if data is None:
            ErrMsg("Indicare la data di elaborazione")
            return 0
        
        Env.Azienda.DB.schema = adb.DEFAULT_DATABASE = nomedb
        
        bt = Env.Azienda.BaseTab
        
        if self.AutorizzoUser(username, password):
            if self.CheckLogin(nomeazi, nomedb, codice, data):
                #bt.defstru()
                try:
                    bt.ReadAziendaSetup()
                except bt.AziendaSetupException, e:
                    aw.awu.MsgDialog(self, e.args[0], style=wx.ICON_ERROR)
                Env.Azienda.Login.dataElab = data
                cfg = CfgContab()
                cfg.SetEsercizio(data)
                Env.Azienda.config.setReportSub()
                aw.SetTitleAppend('(%s) %s' % (codice, nomeazi))
                self.GetParent().EndModal(1)

    def CheckLogin(self, nomeazi, nomedb, codice, data):
        """
        Verifica l'accesso al database spacificato
        """
        lEsito=True
        errMessage = None
        try:
            conn = MySQLdb.connect(host=Env.Azienda.DB.servername,
                                   user=Env.Azienda.DB.username,
                                   passwd=Env.Azienda.DB.password,
                                   db=nomedb,
                                   use_unicode=True)
            Env.Azienda.DB.connection = conn
            Env.Azienda.codice = codice
            Env.Azienda.descrizione = nomeazi
            report.SetPathSub('azienda_%s' % codice)
            
            db = adb.DB()
            db._dbCon = conn
            db.connected = True
#             db = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGSETUP, 'setup', db=db)
#             for key in 'indirizzo cap citta prov codfisc stato piva numtel numfax email titprivacy infatti codateco'.split():
#                 if db.Retrieve('setup.chiave=%s',
#                                'azienda_%s' % key) and db.RowsCount() == 1:
#                     if db.flag:
#                         setattr(Env.Azienda, key, db.flag)
#                     elif db.importo:
#                         setattr(Env.Azienda, key, db.importo)
#                     elif db.descriz:
#                         setattr(Env.Azienda, key, db.descriz)
            Env.Azienda.read_dati_azienda(db)
            Env.Azienda.BaseTab.ReadAziendaSetup()
            wx.GetApp().dbcon = conn
            #conn.close()
            
        except MySQLdb.Error, e:
            errMessage = "Non è possibile accedere al database\n\n%s: %s" \
            % (e.args[0], e.args[1])
            aw.awu.MsgDialog(self, message=errMessage, style=wx.ICON_EXCLAMATION)            
            lEsito=False
        return lEsito
    
    def OnCreate(self, event):
        """
        Crea una nuova azienda.
        """
        ctrHost = self.FindWindowById(ID_SERVER)
        ctrUser = self.FindWindowById(ID_USER)
        ctrPswd = self.FindWindowById(ID_PSWD)
        hostname = ctrHost.GetValue()
        username = ctrUser.GetValue()
        password = ctrPswd.GetValue()
        
        if len(username) == 0:
            aw.awu.MsgDialog(self, "Manca il nome dell'utente", style=wx.ICON_EXCLAMATION)
            
        else:
            dlg = AziendaSetup(None, -1, "Creazione nuova azienda")
            dlg.x4conn = self.x4conn
            do = (dlg.ShowModal() is True)
            dlg.Destroy()
            if do:
                #completamento creazione azienda con creazione record progressivi contabili
                #viene impostato l'anno corrente come esercizio in corso
                db_name = dlg.FindWindowById(ID_NOMEDB).GetValue()
                tabname = '%s.cfgprogr' % db_name
                anno = Env.Azienda.Login.dataElab.year
                c = self.x4conn.cursor()
                c.execute("""INSERT INTO %(tabname)s (codice, keydiff, progrnum, progrimp1, progrimp2) 
                VALUES ("ccg_esercizio", 0, %(anno)s, 0, 0)""" % locals())
                c.execute("""INSERT INTO %(tabname)s (codice, keydiff, progrnum, progrimp1, progrimp2) 
                VALUES ("ccg_giobol",    0,        0, 0, 0)""" % locals())
                c.execute("""INSERT INTO %(tabname)s (codice, keydiff,           progrimp1, progrimp2) 
                VALUES ("ccg_giobol_ec",           0, 0, 0)""" % locals())
                c.execute("""INSERT INTO %(tabname)s (codice, keydiff,           progrimp1, progrimp2) 
                VALUES ("ccg_giobol_ep",           0, 0, 0)""" % locals())
                c.close()
                aw.awu.MsgDialog(self, "L'azienda è stata creata.\nProvvedere al completamento del setup dei dati aziendali.", style=wx.ICON_INFORMATION)
                self.ReadAziende()
    
    def OnQuit(self, event):
        """
        Evento associato all'abbandono del Dialog
        """
        self.GetParent().EndModal( self.ID_QUIT )

    def OnUtenti(self, event):
        
        Env.Azienda.DB.connection = self.x4conn
        adb.DEFAULT_DATABASE = "x4"
        db = adb.DB()
        if db.Connect():
            if ute.CheckUtentiStructure():
                wx.BeginBusyCursor()
                try:
                    dlg = ute.UtentiDialog(self)
                finally:
                    wx.EndBusyCursor()
                dlg.ShowModal()
                dlg.Destroy()
        else:
            aw.awu.MsgDialog(self, repr(db.dbError.description))
        event.Skip()
    
    def UpdateUserControls(self):
        
        cn = lambda x: self.FindWindowById(x)
        psw = cn(ID_PSWD).GetValue()
        
        for id, enab in ((ID_SERVER,      self.login),
                         (ID_USER,        self.login),
                         (ID_PSWD,        self.login),
                         (ID_CHANGEPWD,   not self.login),
                         (ID_BTNAZISEL,   not self.login and len(psw)>0),
                         (ID_LISTAZIENDE, not self.login),
                         (ID_DATAELAB,    not self.login)):
            cn(id).Enable(enab)
        user = cn(ID_USER).GetValue()
        #for id in (ID_ADMIN, ID_NEWAZI, ID_UTENTI):
            #cn(id).Show(user == "x4admin" and not self.login)
        cn(ID_SETUP).Show(self.supervisor and not self.login)
        cn(ID_DETAILS).Show(self.dbaz.RowsCount()>0 and not self.login)
        if self.login:
            cn(ID_LOGIN).SetLabel("Login")
            cn(ID_PSWD).SetValue('')
            cn(ID_USER).SetFocus()
            defbut = cn(ID_LOGIN)
        else:
            cn(ID_LOGIN).SetLabel("Cambia utente")
            defbut = cn(ID_BTNAZISEL)
            self.gridaz.SetFocus()
        #defbut.SetDefault()
        self.SetDefaultItem(defbut)
        self.Layout()
    
    def UpdateServerUrl(self, n):
        cn = lambda x: self.FindWindowById(x)
        if n < cn(ID_SERVER).GetCount():
            cn(ID_SERVERURL).SetLabel(cn(ID_SERVER).GetClientData(n))
    
    def UpdateAziendaDetails(self):
        def cn(x):
            return self.FindWindowByName(x)
        row = self.gridaz.GetSelectedRows()[0]
        dbaz = self.dbaz
        cod = des = tab = ''
        if 0<=row<dbaz.RowsCount():
            dbaz.MoveRow(row)
            cod, des, tab = dbaz.codice, dbaz.azienda, dbaz.nomedb
        cn('azi_codice').SetLabel(cod)
        cn('azi_schema').SetLabel(tab)
    
    def UserExist(self, user):
        curs = self.x4conn.cursor()
        if curs.execute("SELECT codice, nome, psw, datePsw FROM utenti where nome=%s", user)==0:
            return False
        else:
            return True

    def CheckUserPassword(self, user, psw):
        curs = self.x4conn.cursor()
        curs.execute("SELECT psw FROM utenti where nome=" + chr(34) + user + chr(34) + ";")
        memoPsw = curs.fetchone()[0]
        curs.execute("SELECT old_PASSWORD(" + chr(34) + psw + chr(34) + ");")
        digiPsw = curs.fetchone()[0]
        if memoPsw == digiPsw:
            return True                 
        else:
            return False
        
    
    def CheckUser( self, user, psw):
        lOk=False
        msg=None
        if self.UserExist(user)==False:
            msg="Utente non codificato"
        elif self.CheckUserPassword(user, psw)==False:
            msg="Password Errata"
        return msg
        
    def OpenX4db(self, hostname, username, password):
        """
        Apre il database delle aziende
        """
        retVal = False
        tryToOpenDB = True
        
        while (tryToOpenDB):
            tryToOpenDB = False
            try:
                self.x4conn = MySQLdb.connect(host=hostname,
                                              user=username,
                                              passwd=password,
                                              db="x4")
                Env.Azienda.DB.servername = adb.DEFAULT_HOSTNAME = hostname
                Env.Azienda.DB.username =   adb.DEFAULT_USERNAME = username
                Env.Azienda.DB.password =   adb.DEFAULT_PASSWORD = password
                Env.Azienda.DB.schema =     adb.DEFAULT_DATABASE = 'x4'
                retVal = True
                
            except MySQLdb.Error, e:
                if e.args[0] == 1049:
                    style = wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT
                    if aw.awu.MsgDialog(self,
                                        """Il database delle aziende non è """
                                        """stato trovato.\n"""
                                        """Se questo è il primo avvio di X4 """
                                        """dell'installazione, è possibile """
                                        """creare tale database ora.\n"""
                                        """Vuoi creare ora il database """
                                        """delle aziende?""",
                                        style=style) == wx.ID_YES:
                        self.CreaX4db(hostname, username, password)
                        continue
                if e.args[0] == 1045:
                    aw.awu.MsgDialog(self, "Non sei stato riconosciuto. Verifica le tue credenziali.")
                else:
                    msg = "Non è possibile accedere al database delle aziende:\n%s" % repr(e.args)
                    if aw.awu.MsgDialog(self, "%s\n\nVuoi riprovare ?" % msg,
                                        caption = "X4 :: Errore di accesso",
                                        style = wx.YES_NO|wx.ICON_EXCLAMATION) == wx.ID_YES:
                        tryToOpenDB = True
            
        return retVal
    
    def CreaX4db(self, hostname, username, password):
        
        con = MySQLdb.connect(host=hostname, user=username, passwd=password)
        cur = con.cursor()
        
        cur.execute("""CREATE DATABASE x4""")
        
        cur.execute("""
        CREATE TABLE `x4`.`aziende` (
        `id`      INT(10)     UNSIGNED NOT NULL AUTO_INCREMENT,
        `azienda` VARCHAR(60)          NOT NULL DEFAULT '',
        `nomedb`  VARCHAR(45)          NOT NULL DEFAULT '',
        `codice`  VARCHAR(10)          NOT NULL DEFAULT '',
        `modname` VARCHAR(20),
        PRIMARY KEY  (`id`), 
        UNIQUE KEY `Index_2` (`codice`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """)
        
        cur.execute("""
        CREATE TABLE `x4`.`utenti` (
        `id`             INT(10) unsigned NOT NULL AUTO_INCREMENT,
        `codice`         CHAR(2)          NOT NULL DEFAULT '',
        `descriz`        VARCHAR(16)      NOT NULL DEFAULT '',
        `psw`            VARCHAR(41)      NOT NULL DEFAULT '',
        `datePsw`        TIMESTAMP        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        `amministratore` CHAR(1)                   DEFAULT NULL,
        PRIMARY KEY  (`id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """)
        utente = self.FindWindowById(ID_USER).GetValue()
        cur.execute("""
        INSERT INTO `x4`.`utenti` (id, codice, descriz, amministratore)
        VALUES (1, '01', %s, 'X')
        """, utente)
        
        cur.execute("""
        CREATE TABLE `x4`.`diritti` (
        `id` INT(10) UNSIGNED            NOT NULL AUTO_INCREMENT,
        `id_azienda` INT(10)    UNSIGNED NOT NULL DEFAULT '0',
        `id_utente`  INT(10)    UNSIGNED NOT NULL DEFAULT '0',
        `attivo`     TINYINT(1) UNSIGNED NOT NULL DEFAULT '0',
        PRIMARY KEY  (`id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """)
        
        cur.execute("""
        CREATE TABLE `x4`.`bilcee` (
          `id` int(6) NOT NULL auto_increment COMMENT 'ID PDC CEE',
          `codice` char(9) default NULL COMMENT 'Codice',
          `descriz` char(128) default NULL COMMENT 'Descrizione',
          `sezione` char(1) default NULL COMMENT 'Sezione',
          `voce` char(1) default NULL COMMENT 'Voce',
          `capitolo` char(4) default NULL COMMENT 'Capitolo',
          `dettaglio` char(2) default NULL COMMENT 'Dettaglio',
          `subdett` char(1) default NULL COMMENT 'Sub-dettaglio',
          `selectable` tinyint(4) default NULL,
          PRIMARY KEY  (`id`),
          UNIQUE KEY `index1` (`codice`)
        ) ENGINE=MyISAM AUTO_INCREMENT=459 DEFAULT CHARSET=utf8 COMMENT='Bilancio CEE'
        """)
        
        cur.execute("""
        INSERT INTO `x4`.`bilcee` (`id`,`codice`,`descriz`,`sezione`,`voce`,`capitolo`,`dettaglio`,`subdett`,`selectable`) VALUES 
         (307,'1','ATTIVO','1','','','','',0),
         (308,'1A','CREDITI VERSO SOCI PER VERSAMENTI ANCORA DOVUTI','1','A','','','',0),
         (309,'1A      a','PARTE RICHIAMATA','1','A','','','a',1),
         (310,'1A      b','PARTE NON RICHIAMATA','1','A','','','b',1),
         (311,'1B','IMMOBILIZZAZIONI','1','B','','','',0),
         (312,'1BI','IMMOBILIZZAZIONI IMMATERIALI','1','B','I','','',0),
         (313,'1BI   01','COSTI DI IMPIANTO E DI AMPLIAMENTO','1','B','I','01','',1),
         (314,'1BI   02','COSTI DI RICERCA, DI SVILUPPO E DI PUBBLICITA','1','B','I','02','',1),
         (315,'1BI   03',"DIRITTI BREV. INDUSTR. E DIR. UTILIZZO OPERE DELL'INGEGNO",'1','B','I','03','',1),
         (316,'1BI   04','CONCESSIONI, LICENZE, MARCHI E DIRITTI SIMILI','1','B','I','04','',1),
         (317,'1BI   05','AVVIAMENTO','1','B','I','05','',1),
         (318,'1BI   06','IMMOBILIZZAZIONI IN CORSO E ACCONTI','1','B','I','06','',1),
         (319,'1BI   07','ALTRE','1','B','I','07','',1),
         (320,'1BII','IMMOBILIZZAZIONI MATERIALI','1','B','II','','',0),
         (321,'1BII  01','TERRENI E FABBRICATI','1','B','II','01','',1),
         (322,'1BII  02','IMPIANTI E MACCHINARIO','1','B','II','02','',1),
         (323,'1BII  03','ATTREZZATURE INDUSTRIALI E COMMERCIALI','1','B','II','03','',1),
         (324,'1BII  04','ALTRI BENI','1','B','II','04','',1),
         (325,'1BII  05','IMMOBILIZZAZIONI IN CORSO E ACCONTI','1','B','II','05','',1),
         (326,'1BIII','IMMOBILIZZAZIONI FINANZIARIE','1','B','III','','',0),
         (327,'1BIII 01','PARTECIPAZIONI','1','B','III','01','',0),
         (328,'1BIII 01a','IMPRESE CONTROLLATE','1','B','III','01','a',1),
         (329,'1BIII 01b','IMPRESE COLLEGATE','1','B','III','01','b',1),
         (330,'1BIII 01c','ALTRE IMPRESE','1','B','III','01','c',1),
         (331,'1BIII 02','CREDITI','1','B','III','02','',0),
         (332,'1BIII 02a','CREDITI VERSO IMPRESE CONTROLLATE','1','B','III','02','a',1),
         (333,'1BIII 02b','CREDITI VERSO IMPRESE COLLEGATE','1','B','III','02','b',1),
         (334,'1BIII 02c','CREDITI VERSO IMPRESE CONTROLLANTI','1','B','III','02','c',1),
         (335,'1BIII 02d','CREDITI VERSO ALTRI','1','B','III','02','d',1),
         (336,'1BIII 03','ALTRI TITOLI','1','B','III','03','',1),
         (337,'1BIII 04','AZIONI PROPRIE','1','B','III','04','',1),
         (338,'1C','ATTIVO CIRCOLANTE','1','C','','','',0),
         (339,'1CI','RIMANENZE','1','C','I','','',0),
         (340,'1CI   01','MATERIE PRIME, SUSSIDIARIE E DI CONSUMO','1','C','I','01','',1),
         (341,'1CI   02','PRODOTTI IN CORSO DI LAVORAZIONE E SEMILAVORATI','1','C','I','02','',1),
         (342,'1CI   03','LAVORI IN CORSO SU ORDINAZIONE','1','C','I','03','',1),
         (343,'1CI   04','PRODOTTI FINITI E MERCI','1','C','I','04','',1),
         (344,'1CI   05','ACCONTI','1','C','I','05','',1),
         (345,'1CII','CREDITI','1','C','II','','',0),
         (346,'1CII  01','CREDITI VERSO CLIENTI','1','C','II','01','',1),
         (347,'1CII  02','CREDITI VERSO IMPRESE CONTROLLATE','1','C','II','02','',1),
         (348,'1CII  03','CREDITI VERSO IMPRESE COLLEGATE','1','C','II','03','',1),
         (349,'1CII  04','CREDITI VERSO CONTROLLANTI','1','C','II','04','',1),
         (350,'1CII  05','CREDITI VERSO ALTRI','1','C','II','05','',1),
         (351,'1CIII',"ATTIVITA' FINANZIARIE NON IMMOBILIZZAZIONI",'1','C','III','','',0),
         (352,'1CIII 01','PARTECIPAZIONI IN IMPRESE CONTROLLATE','1','C','III','01','',1),
         (353,'1CIII 02','PARTECIPAZIONI IN IMPRESE COLLEGATE','1','C','III','02','',1),
         (354,'1CIII 03','ALTRE PARTECIPAZIONI','1','C','III','03','',1),
         (355,'1CIII 04','AZIONI PROPRIE','1','C','III','04','',1),
         (356,'1CIII 05','ALTRI TITOLI','1','C','III','05','',1),
         (357,'1CIV',"DISPONIBILITA' LIQUIDE",'1','C','IV','','',0),
         (359,'1CIV  01','DEPOSITI BANCARI E POSTALI','1','C','IV','01','',1),
         (360,'1CIV  02','ASSEGNI','1','C','IV','02','',1),
         (361,'1CIV  03','DENARO E VALORI IN CASSA','1','C','IV','03','',1),
         (362,'1D','RATEI E RISCONTI','1','D','','','',0),
         (363,'1D    01','DISAGGIO SUI PRESTITI','1','D','','01','',1),
         (364,'1D    02','ALTRI','1','D','','02','',1),
         (365,'2','PASSIVO','2','','','','',0),
         (366,'2A','PATRIMONIO NETTO','2','A','','','',0),
         (367,'2AI','CAPITALE','2','A','I','','',1),
         (368,'2AII','RISERVA DA SOVRAPREZZO AZIONI','2','A','II','','',1),
         (369,'2AIII','RISERVE DI RIVALUTAZIONE','2','A','III','','',1),
         (370,'2AIV','RISERVA LEGALE','2','A','IV','','',1),
         (371,'2AV','RISERVA PER AZIONI PROPRIE IN PORTAFOGLIO','2','A','V','','',1),
         (372,'2AVI','RISERVE STATUTARIE','2','A','VI','','',1),
         (373,'2AVII','ALTRE RISERVE','2','A','VII','','',0),
         (374,'2AVII 01','RISERVA STRAORDINARIA','2','A','VII','01','',1),
         (375,'2AVII 02','RISERVA STRAORDINARIA DA FUSIONE','2','A','VII','02','',1),
         (376,'2AVII 03','VERSAMENTO SOCI IN CONTO CAPITALE','2','A','VII','03','',1),
         (377,'2AVIII','UTILI (PERDITE) PORTATI A NUOVO','2','A','VIII','','',1),
         (378,'2B','FONDI PER RISCHI E ONERI','2','B','','','',0),
         (379,'2B    01','F. TRATTAMENTI DI QUIESCENZA E OBBLIGHI SIMILI','2','B','','01','',1),
         (380,'2B    02','FONDO IMPOSTE E TASSE','2','B','','02','',1),
         (381,'2B    03','ALTRI FONDI','2','B','','03','',1),
         (382,'2C','TRATTAMENTO DI FINE RAPPORTO DI LAVORO SUBORDINATO','2','C','','','',1),
         (383,'2D','DEBITI','2','D','','','',0),
         (384,'2D    01','OBBLIGAZIONI','2','D','','01','',1),
         (385,'2D    02','OBBLIGAZIONI CONVERTIBILI','2','D','','02','',1),
         (386,'2D    03','DEBITI VERSO BANCHE','2','D','','03','',1),
         (387,'2D    04','DEBITI VERSO ALTRI FINANZIATORI','2','D','','04','',1),
         (388,'2D    05','ACCONTI','2','D','','05','',1),
         (389,'2D    06','DEBITI VERSO FORNITORI','2','D','','06','',1),
         (390,'2D    07','DEBITI RAPPRESENTATI DA TITOLI DI CREDITO','2','D','','07','',1),
         (391,'2D    08','DEBITI VERSO IMPRESE CONTROLLATE','2','D','','08','',1),
         (392,'2D    09','DEBITI VERSO IMPRESE COLLEGATE','2','D','','09','',1),
         (393,'2D    10','DEBITI VERSO CONTROLLANTI','2','D','','10','',1),
         (394,'2D    11','DEBITI TRIBUTARI','2','D','','11','',1),
         (395,'2D    12','DEBITI VERSO ISTITUTI DI PREVIDENZA E SICUREZZA SOCIALE','2','D','','12','',1),
         (396,'2D    13','ALTRI DEBITI','2','D','','13','',1),
         (397,'2E','RATEI E RISCONTI','2','E','','','',0),
         (398,'2E    01','AGGIO SUI PRESTITI','2','E','','01','',1),
         (399,'2E    02','ALTRI','2','E','','02','',1),
         (400,'3',"STATO PATRIMONIALE - CONTI D'ORDINE",'3','','','','',0),
         (401,'3 I',"CONTI D'ORDINE ATTIVO",'3','','I','','',1),
         (402,'3 II',"CONTI D'ORDINE PASSIVO",'3','','II','','',1),
         (403,'4','CONTO ECONOMICO','4','','','','',0),
         (404,'4A','VALORE DELLA PRODUZIONE','4','A','','','',0),
         (405,'4A    01','RICAVI DELLE VENDITE E DELLE PRESTAZIONI','4','A','','01','',1),
         (406,'4A    02','VARIAZIONE DELLE RIMANENZE','4','A','','02','',1),
         (407,'4A    03','VARIAZIONE DEI LAVORI IN CORSO SU ORDINAZIONE','4','A','','03','',1),
         (408,'4A    04','INCREMENTI DI IMMOBILIZZAZIONI PER LAVORI INTERNI','4','A','','04','',1),
         (409,'4A    05','ALTRI RICAVI E PROVENTI','4','A','','05','',1),
         (410,'4B','COSTI DELLA PRODUZIONE','4','B','','','',0),
         (411,'4B    06','COSTI DELLA PROD. PER MATERIE I, SUSSID., DI CONSUMO E MERCI','4','B','','06','',1),
         (412,'4B    07','COSTI DELLA PRODUZIONE PER SERVIZI','4','B','','07','',1),
         (413,'4B    08','COSTI DELLA PRODUZIONE PER GODIMENTO DI BENI DI TERZI','4','B','','08','',1),
         (414,'4B    09','COSTI DELLA PRODUZIONE PER IL PERSONALE','4','B','','09','',0),
         (415,'4B    09a','SALARI E STIPENDI','4','B','','09','a',1),
         (416,'4B    09b','ONERI SOCIALI','4','B','','09','b',1),
         (417,'4B    09c','TRATTAMENTO DI FINE RAPPORTO','4','B','','09','c',1),
         (418,'4B    09d','TRATTAMENTO DI QUIESCENZA E SIMILI','4','B','','09','d',1),
         (419,'4B    09e','ALTRI COSTI','4','B','','09','e',1),
         (420,'4B    10','AMMORTAMENTI E SVALUTAZIONI','4','B','','10','',0),
         (421,'4B    10a','AMMORTAMENTO DELLE IMMOBILIZZAZIONI IMMATERIALI','4','B','','10','a',1),
         (422,'4B    10b','AMMORTAMENTO DELLE IMMOBILIZZAZIONI MATERIALI','4','B','','10','b',1),
         (423,'4B    10c','ALTRE SVALUTAZIONI DELLE IMMOBILIZZAZIONI','4','B','','10','c',1),
         (424,'4B    10d',"SVAL. DEI CREDITI DELL'ATTIVO CIRCOLANTE E DISPONIB. LIQUIDE",'4','B','','10','d',1),
         (425,'4B    11','VARIAZIONE DELLE RIMANENZE','4','B','','11','',1),
         (426,'4B    12','ACCANTONAMENTI PER RISCHI','4','B','','12','',1),
         (427,'4B    13','ALTRI ACCANTONAMENTI','4','B','','13','',1),
         (428,'4B    14','ONERI DIVERSI DI GESTIONE','4','B','','14','',1),
         (429,'4C','PROVENTI E ONERI FINANZIARI','4','C','','','',0),
         (430,'4C    15','PROVENTI DA PARTECIPAZIONI IN IMPRESE','4','C','','15','',0),
         (431,'4C    15a','PROV. DA PARTECIPAZIONI IN IMPRESE CONTROLLATE','4','C','','15','a',1),
         (432,'4C    15b','PROV. DA PARTECIPAZIONI IN IMPRESE COLLEGATE','4','C','','15','b',1),
         (433,'4C    16','ALTRI PROVENTI FINANZIARI','4','C','','16','',0),
         (434,'4C    16a','ALTRI PROVENTI FIN. DA CREDITI ISCRITTI NELLE IMMOBILIZ.','4','C','','16','a',1),
         (435,'4C    16b','DA TITOLI ISCRITTI NELLE IMM. CHE NON COST. PARTECIPAZIONI','4','C','','16','b',1),
         (436,'4C    16c',"DA TITOLI ISCRITTI NELL'ATTIVO CIRCOL. CHE NON COST. PARTEC.",'4','C','','16','c',1),
         (437,'4C    16d','PROVENTI DIVERSI DAI PRECEDENTI','4','C','','16','d',1),
         (438,'4C    17','INTERESSI E ALTRI ONERI FINANZIARI','4','C','','17','',0),
         (439,'4C    17a','INT. E ALTRI ONERI FINAN. DA IMPRESE CONTROLLATE','4','C','','17','a',1),
         (440,'4C    17b','INT. E ALTRI ONERI FIN. DA IMPRESE CONTROLLANTI','4','C','','17','b',1),
         (441,'4C    17c','INT. E ALTRI ONERI FIN. DA IMPRESE COLLEGATE','4','C','','17','c',1),
         (442,'4C    17d','INT. E ALTRI ONERI FIN. DA ALTRE IMPRESE','4','C','','17','d',1),
         (443,'4D',"RETTIFICHE DI VALORE DI ATTIVITA' FINANZIARIE",'4','D','','','',0),
         (444,'4D    18','RIVALUTAZIONI','4','D','','18','',0),
         (445,'4D    18a','RIVALUTAZIONI DI PARTECIPAZIONI','4','D','','18','a',1),
         (446,'4D    18b','RIVALUT. DI IMMOBILIZ. FINANZ. CHE NON COST. PARTECIPAZIONI','4','D','','18','b',1),
         (447,'4D    18c',"RIV. DI TIT. ISCRITTI NELL'ATTIVO CIRC. CHE NON COST. PART.",'4','D','','18','c',1),
         (448,'4D    19','SVALUTAZIONI','4','D','','19','',0),
         (449,'4D    19a','SVAL. DI PARTECIPAZIONI','4','D','','19','a',1),
         (450,'4D    19b','SVAL. DI IMMOB. FIN. CHE NON COSTITUISCONO PARTECIPAZIONI','4','D','','19','b',1),
         (451,'4D    19c',"SVAL. DI TIT. ISCRITTI ALL'ATTIVO CIRC. CHE NON COST. PART.",'4','D','','19','c',1),
         (452,'4E','PROVENTI E ONERI STRAORDINARI','4','E','','','',0),
         (453,'4E    20','PROVENTI','4','E','','20','',1),
         (454,'4E    21','ONERI','4','E','','21','',1),
         (455,'4E    22',"IMPOSTE SUL REDDITO DELL'ESERCIZIO",'4','E','','22','',1),
         (456,'4E    24','RETTIF. DI VAL. OPERATE ESCLUSIV. IN APPLIC. DI NORME TRIB.','4','E','','24','',1),
         (457,'4E    25','ACCANT. OPERATI ESCLUSIV. IN APPLIC. DI NORME TRIBUTARIE','4','E','','25','',1);
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `x4`.`cfgmail` (
          `id` int(6) NOT NULL auto_increment COMMENT 'ID',
          `azienda`  char(16)   default NULL COMMENT 'Codice Azienda',
          `sender`   char(128)  default NULL COMMENT 'Indirizzo Mittente',
          `smtpaddr` char(64)   default NULL COMMENT 'Indirizzo Server SMTP',
          `smtpport` int(4)     default NULL COMMENT 'Porta Server SMTP',
          `authreq`  tinyint(1) default NULL COMMENT 'Autorizzazione richiesta',
          `authuser` char(128)  default NULL COMMENT 'Nome utente per login smtp',
          `authpswd` char(128)  default NULL COMMENT 'Password per login smtp',
          `authtls`  tinyint(1) default NULL COMMENT 'Flag uso TLS per login smtp',
          PRIMARY KEY  (`id`),
          UNIQUE KEY `index1` (`azienda`)
        ) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Setup SMTP'
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS `x4`.`cfgxmpp` (
          `id`         int(6) NOT NULL auto_increment COMMENT 'ID',
          `azienda`    char(16)   default NULL COMMENT 'Codice Azienda',
          `xmppaddr`   char(128)  default NULL COMMENT 'URL Server XMPP',
          `xmppport`   int(5)     default NULL COMMENT 'Porta Server XMPP',
          `authuser`   char(128)  default NULL COMMENT 'Nome utente per login smtp',
          `authpswd`   char(128)  default NULL COMMENT 'Password per login XMPP',
          `onlineonly` tinyint(1) default NULL COMMENT 'Flag invio solo a contatto online',
          PRIMARY KEY  (`id`),
          UNIQUE KEY `index1` (`azienda`)
        ) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Setup XMPP'
        """)
        
        cur.execute("""
CREATE TABLE IF NOT EXISTS `x4`.`stati` (
  `id`             INT(6)      NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `codice`         CHAR(10)    DEFAULT NULL COMMENT 'Codice/Sigla Stato',
  `vatprefix`      CHAR(10)    DEFAULT NULL COMMENT 'Prefisso partite iva',
  `descriz`        VARCHAR(60) DEFAULT NULL COMMENT 'Denominazione Stato',
  `desceng`        VARCHAR(60) DEFAULT NULL COMMENT 'Denominazione Stato in lingua inglese',
  `is_cee`         TINYINT(1)  DEFAULT NULL COMMENT 'Flag Stato CEE',
  `is_blacklisted` TINYINT(1)  DEFAULT NULL COMMENT 'Flag Blacklist acquisti/vendite',
  `codunico`       CHAR(3)     DEFAULT NULL COMMENT 'Codice Unico',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `index1` (`codice`),
  UNIQUE KEY `index2` (`descriz`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Stati'""")
        
        cur.execute("""
INSERT INTO `x4`.`stati`  
    (`id`,`codice`,`vatprefix`,`descriz`,`desceng`,`is_cee`,`is_blacklisted`) 
VALUES 
    (  1, "AT", "AT", "AUSTRIA",         "AUSTRIA",        1, 0),
    (  2, "BE", "BE", "BELGIO",          "BELGIUM",        1, 0),
    (  3, "BG", "BG", "BULGARIA",        "BULGARIA",       1, 0),
    (  4, "CY", "CY", "CIPRO",           "CYPRUS",         1, 0),
    (  5, "DK", "DK", "DANIMARCA",       "DENMARK",        1, 0),
    (  6, "EE", "EE", "ESTONIA",         "ESTONIA",        1, 0),
    (  7, "FI", "FI", "FINLANDIA",       "FINLAND",        1, 0),
    (  8, "FR", "FR", "FRANCIA",         "FRANCE",         1, 0),
    (  9, "DE", "DE", "GERMANIA",        "GERMANY",        1, 0),
    ( 10, "GB", "GB", "GRAN BRETAGNA",   "UNITED KINGDOM", 1, 0),
    ( 11, "EL", "EL", "GRECIA",          "GREECE",         1, 0),
    ( 12, "IE", "IE", "IRLANDA",         "IRELAND",        1, 0),
    ( 13, "IT", "IT", "ITALIA",          "ITALY",          1, 0),
    ( 14, "LV", "LV", "LETTONIA",        "LATVIA",         1, 0),
    ( 15, "LT", "LT", "LITUANIA",        "LITHUANIA",      1, 0),
    ( 16, "LU", "LU", "LUSSEMBURGO",     "LUXEMBOURG",     1, 0),
    ( 17, "MT", "MT", "MALTA",           "MALTA",          1, 0),
    ( 18, "NL", "NL", "OLANDA",          "NETHERLANDS",    1, 0),
    ( 19, "PL", "PL", "POLONIA",         "POLAND",         1, 0),
    ( 20, "PT", "PT", "PORTOGALLO",      "PORTUGAL",       1, 0),
    ( 21, "CZ", "CZ", "REPUBBLICA CECA", "CZECH REPUBLIC", 1, 0),
    ( 22, "RO", "RO", "ROMANIA",         "ROMANIA",        1, 0),
    ( 23, "SK", "SK", "SLOVACCHIA",      "SLOVAKIA",       1, 0),
    ( 24, "SI", "SI", "SLOVENIA",        "SLOVENIA",       1, 0),
    ( 25, "ES", "ES", "SPAGNA",          "SPAIN",          1, 0),
    ( 26, "SE", "SE", "SVEZIA",          "SWEDEN",         1, 0),
    ( 27, "HU", "HU", "UNGHERIA",        "HUNGARY",        1, 0),
    ( 28, "SM", "SM", "SAN MARINO",      "SAN MARINO",     0, 1),
    ( 29, "MC", "FR", "MONACO",          "MONACO",         0, 1),
    ( 30, "CH", "CH", "SVIZZERA",        "SWISS",          0, 1),
    (999, "ZZ", "ZZ", "ZZ-INDEFINITO-",  "ZZ-UNDEFINED-",  0, 0)""")
        
        aw.awu.MsgDialog(self, """Il database delle aziende è stato creato.\n"""
                         """E' stato creato l'utente '%s', privo di password."""
                         % utente)
        
        cur.close()
        con.close()
        
        return True
    
    def ReadAziende( self ):
        """
        Identifica le aziende installate leggendo dal database aziende
        """
        try:
            curs = self.x4conn.cursor()
            filtmod = ''
            if self.test_mod_name:
                try:
                    curs.execute("SELECT modname FROM aziende LIMIT 1")
                    filtmod = "AND (azi.modname"
                    if version.MODVERSION_NAME:
                        filtmod += '="%s")' % version.MODVERSION_NAME
                    else:
                        filtmod += ' IS NULL OR azi.modname="")'
                except MySQLdb.Error, e:
                    pass
            order = 'azi.azienda, azi.codice'
            curs.execute("DESCRIBE x4.aziende")
            if filter(lambda r: r[0] == 'ordine', curs.fetchall()):
                order = 'azi.ordine, %s' % order
            cn = lambda x: self.FindWindowById(x)
            sql = r"""
              SELECT azi.id, azi.codice, azi.azienda, azi.nomedb
                FROM aziende azi
                JOIN diritti dir ON azi.id=dir.id_azienda
                JOIN utenti ute ON dir.id_utente=ute.id
               WHERE dir.id_utente=ute.id AND
                     dir.attivo=1 AND ute.descriz=%%s %s
            ORDER BY %s""" % (filtmod, order)
            curs.execute(sql, (cn(ID_USER).GetValue(),))
            self.dbaz.SetRecordset(curs.fetchall())
            self.gridaz.ChangeData(self.dbaz.GetRecordset())
            
        except MySQLdb.Error, e:
            dlg = wx.MessageDialog(
            parent=None,
            message = "Non è possibile accedere al database delle aziende.\n\n%s: %s\n\nVuoi riprovare ?"
            % (e.args[0], e.args[1]),
            caption = "X4 :: Errore di accesso",
            style = wx.OK )
            dlg.ShowModal()
            dlg.Destroy()

    def UpdateAziende( self ):
        if self.x4conn:
            self.ReadAziende()


# ------------------------------------------------------------------------------


class SelAziendaDialog(aw.Dialog):
    """
    Dialog selezione azienda
    """
    def __init__(self, *args, **kwargs):
        for key, val in (('title', 'Selezione azienda'),
                         ('style', wx.DEFAULT_FRAME_STYLE)):
            if not key in kwargs:
                kwargs[key] = val
        aw.Dialog.__init__(self, *args, **kwargs)
        self.selazpanel = SelAziendaPanel(self)
        self.AddSizedPanel(self.selazpanel, 'selaziendapanel')
        self.CentreOnScreen()


# ------------------------------------------------------------------------------


class AziendaSetup(aw.Dialog):
    """
    Creazione nuova azienda
    =======================
    
    Imposta i dati di intestazione dell'azienda e provvede a creare il database
    relativo.  E' possibile acquisire una azienda Mirage esistente tramite l'apposito
    bottone.
    
    Il Dialog è modale; i possibili valori di ritorno sono:::
    
        True   in caso di creazione database terminato correttamente (azienda creata)
        False  altrimenti
        
    """
    
    ID_QUIT = 0
    ID_DONE = 1
    
    x4conn = None
    dbconn = None
    
    _mirfrom = False
    _mirpath = False
    _mircode = False
    
    def __init__(self, parent, id, title,
        pos = wx.DefaultPosition, size = wx.DefaultSize,
        style = wx.DEFAULT_FRAME_STYLE ):
        """
        Costruttore Dialog standard
        """
        aw.Dialog.__init__(self, parent, id, title, pos, size, style)
        
        panel = aw.Panel( self, -1 )
        AziendaSetupFunc( panel, True )
        self.UpdateCreationLabel()
        
        self.Fit()
        
        ctrIntestaz = self.FindWindowById(ID_INTESTAZ)
        
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=ID_BTNQUIT)
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=ID_BTNOK)
        if miracq:
            self.Bind(wx.EVT_BUTTON, self.OnMirAcq, id=ID_BTNMIRAGE)
        else:
            self.FindWindowById(ID_BTNMIRAGE).Hide()

    def OnConfirm( self, event ):
        """
        Handler evento bottone di conferma creazione azienda.
        Avvia la funzione L{CreateAzienda} che provvede a:
            - creare il database dell'azienda
            - aggiungere la voce relativa nel database delle aziende
        """
        Env.Azienda.BaseTab.defstru()
        self.CreateAzienda()
        
    def OnQuit( self, event ):
        """
        Handler evento chiusura dialog per abbandonno operazione
        """
        self.EndModal( False )

    def OnMirAcq( self, event ):
        """
        Handler evento bottone di acquisizione dati da Mirage.
        """
        mirAzi = self.FindAziendaMirage()
        
        if mirAzi:
            
            bt = Env.Azienda.BaseTab
            
            self._mirfrom = True
            self._mirpath, self._mircode = ( mirAzi[0][0], mirAzi[0][1] )
            
            dbfTab = Dbf('%sMGTABE%s.DBF' % (self._mirpath, self._mircode))
            rectot = len(dbfTab)
            for n in range(rectot):
                rec = dbfTab[n]
                DA = rec["DA"]
                if rec['TIPTAB'] == '0':
                    bt.VALINT_DECIMALS = int(DA[61])
                    bt.MAGQTA_DECIMALS= int(DA[51])
                    bt.MAGPRE_DECIMALS= int(DA[52])
                    break
            dbfTab.close()
            
            for cid, val in ((ID_NOMEDB,    'x4_%s' % self._mircode.lower()),
                             (ID_CODICE,    self._mircode),
                             (ID_INTESTAZ,  mirAzi[1]),
                             (ID_INDIRIZZO, mirAzi[2]),
                             (ID_CAP,       mirAzi[3]),
                             (ID_CITTA,     mirAzi[4]),
                             (ID_PROVINCIA, mirAzi[5]),
                             (ID_CODFISC,   mirAzi[6]),
                             (ID_STATO,     mirAzi[7]),
                             (ID_PIVA,      mirAzi[8])):
                self.FindWindowById(cid).SetValue(val)
            
            for cid in (ID_ESERCIZIOGG, ID_ESERCIZIOMM):
                self.FindWindowById(cid).SetValue(1)
            
        else:
            self._mirfrom = False
        
        self.UpdateCreationLabel()
        
        return mirAzi is not None
    
    def UpdateCreationLabel(self):
        label1 = 'Confermando, verrà '
        label2 = ''
        if self._mirfrom:
            label1 += 'acquisita l\'azienda %s di Mirage' % self._mircode
            label2 = 'da '+self._mirpath
        else:
            label1 += 'creata una nuova azienda'
        for cid, val in ((ID_CONFACTION1, label1),
                         (ID_CONFACTION2, label2)):
            self.FindWindowById(cid).SetLabel(val)
    
    def CreateAzienda(self):
        """
        Provvede a creare il database dell'azienda e ad inserirne l'intestazione
        nel database delle aziende.
        
        In caso di richiesta, provvede inoltre ad effettuare l'acquisizione dagli
        archivi di Mirage.
        
        @param Mirage: flag per avviare l'acquisizione da Mirage
        @type: C{logical}  (I{Default=B{False}})
        
        """
        retVal = False
        
        intest = self.FindWindowById(ID_INTESTAZ).GetValue()
        nomedb = self.FindWindowById(ID_NOMEDB).GetValue()
        codice = self.FindWindowById(ID_CODICE).GetValue()
        
        errMessage = None
        if len(nomedb) == 0:
            errMessage = "Specificare il nome del database"
        elif len(codice) == 0:
            errMessage = "Specificare il codice azienda"
        elif len(intest) == 0:
            errMessage = "Specificare l'intestazione dell'azienda"
        
        if errMessage != None:
            dlg = wx.MessageDialog(
            parent=None,
            message = errMessage,
            caption = "X4 :: Errore di accesso",
            style = wx.OK|wx.ICON_EXCLAMATION )
            dlg.ShowModal()
        
        else:
            dlg = wx.MessageDialog( parent=None,
                                    message = "Confermi la creazione del database %s ?" % (nomedb,), 
                                    caption = "X4 :: Creazione database",
                                    style = wx.YES_NO|wx.ICON_QUESTION )
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp != wx.ID_YES:
                return False
            
            errMessage = None
            curs = self.x4conn.cursor()
            for nome, desc in (('nomedb',  'questo nome di database'),
                               ('codice',  'questo codice'),
                               ('descriz', 'questa intestazione')):
                try:
                    curs.execute(r"SELECT azienda FROM aziende WHERE nomedb=%s;",\
                                 (nomedb,))
                    rs = curs.fetchone()
                    if rs:
                        errMessage = "Esiste già un'azienda con %s: \n%s" % (desc, rs[0])
                        break
                
                except MySQLdb.Error, e:
                    errMessage = "Non è possibile creare il database\n\n%s: %s" % (e.args[0], e.args[1])
            
            if errMessage is None:
                droponerr = False
                try:
                    curs.execute("CREATE DATABASE %s;" % (nomedb,))
                    droponerr = True
                    conn = MySQLdb.connect(host=Env.Azienda.DB.servername,
                                           user=Env.Azienda.DB.username,
                                           passwd=Env.Azienda.DB.password,
                                           db=nomedb)
                    self.dbconn = conn
                    mv = version.MODVERSION_NAME or None
                    curs.execute("""
                    INSERT INTO aziende (azienda, nomedb, codice, modname) 
                    VALUES (%s, %s, %s, %s)""", (intest, nomedb, codice, mv))
                    
                    if self.CreateTables(droptables=False):
                        #push dati aziendali su cfgsetup
                        cmd = r"""
                        INSERT INTO cfgsetup (chiave, descriz)
                        VALUES (%s, %s)"""
                        c = self.dbconn.cursor()
                        for cid, key in ((ID_CODICE,    'codice'),
                                         (ID_INTESTAZ,  'ragsoc'),
                                         (ID_INDIRIZZO, 'indirizzo'),
                                         (ID_CAP,       'cap'),
                                         (ID_CITTA,     'citta'),
                                         (ID_PROVINCIA, 'prov'),
                                         (ID_CODFISC,   'codfisc'),
                                         (ID_STATO,     'stato'),
                                         (ID_PIVA,      'piva')):
                            c.execute(cmd, ('azienda_'+key,
                                            self.FindWindowById(cid).GetValue()))
                        cmd = r"""
                        INSERT INTO cfgsetup (chiave, importo)
                        VALUES (%s, %s)"""
                        for val, key in ((1, 'startgg'),
                                         (1, 'startmm')):
                            c.execute(cmd, ('esercizio_'+key, val))
                        c.close()
                        retVal = True
                
                except MySQLdb.Error, e:
                    dlg = wx.MessageDialog(parent=None, message = "Non è possibile accedere al database\n\n%s: %s" % (e.args[0], e.args[1]),
                    caption = "X4 :: Errore di accesso",
                    style = wx.CANCEL|wx.ICON_EXCLAMATION )
                    dlg.ShowModal()
                    dlg.Destroy()
                    if droponerr:
                        try:
                            curs.execute("DROP DATABASE IF EXISTS %s;" % (nomedb, ) )
                            curs.execute("DELETE FROM azienda WHERE codice=", codice)
                        except Exception, e:
                            pass
            else:
                dlg = wx.MessageDialog(parent=None, message = errMessage, 
                caption = "X4 :: Errore di accesso",
                style = wx.CANCEL|wx.ICON_EXCLAMATION )
                dlg.ShowModal()
                dlg.Destroy()
        
        if retVal:
            
            self.attivaUtenti(nomedb)
            
            bt = Env.Azienda.BaseTab
            
            c = self.dbconn.cursor()
            cmd = "INSERT INTO %s (chiave,importo) VALUES (%%s, %%s)"\
                % bt.TABNAME_CFGSETUP
            for name, val in (('contab_decimp', bt.VALINT_DECIMALS),
                              ('magdec_qta',    bt.MAGQTA_DECIMALS),
                              ('magdec_prez',   bt.MAGPRE_DECIMALS)):
                c.execute(cmd, (name, val))
            c.close()
            
            if self._mirfrom:
                appmir = miracq.AppendFromMirage(self, self.dbconn, self._mirpath, self._mircode, nomedb)
            else:
                dlg = AziendaCopyDialog(self, nomedb)
                dlg.ShowModal()
                dlg.Destroy()
            
            self.EndModal(retVal)
    
    def existSupervisor(self):
        lEsito=False
        db = adb.DB()
        db._dbCon = self.x4conn
        db.connected = True
        ute = adb.DbTable('utenti', db=db, writable=False)
        if not ute.Retrieve("amministratore='X'"):
            aw.awu.MsgDialog(None,\
                             "Impossibile accedere alla tabella Utenti:\n"\
                             % repr(ute.GetError()))
        else:
            if ute.RowsCount()>0:
                lEsito=True
        return lEsito

    def attivaUtenti(self, aziname):
        db = adb.DB()
        db._dbCon = self.x4conn
        db.connected = True
        azi = adb.DbTable('aziende', db=db, writable=False)
        if not azi.Retrieve('nomedb=%s', aziname):
            aw.awu.MsgDialog(None,\
                             "Impossibile accedere alla tabella aziende:\n"\
                             % repr(azi.GetError()))
            return False
        ute = adb.DbTable('utenti',  db=db, writable=False)
        dir = adb.DbTable('diritti', db=db, writable=True)
        if not ute.Retrieve():
            aw.awu.MsgDialog(None,\
                             "Impossibile accedere alla tabella utenti:\n"\
                             % repr(ute.GetError()))
            return False
        
        dlg = wx.Dialog(self, -1, "Diritti utenti")
        UtentiNewAzienda(dlg)
        
        cu = dlg.FindWindowById(ID_UTENTI)
        map(lambda u: cu.Append(u.descriz), ute)
        
        def OnConferma(event):
            dlg.EndModal(1)
        
        dlg.Bind(wx.EVT_BUTTON, OnConferma, dlg.FindWindowById(ID_CONFERMA))
        
        if dlg.ShowModal() == 1:
            
            def creaDiritto(n):
                ute.MoveRow(n)
                dir.CreateNewRow()
                dir.id_azienda = azi.id
                dir.id_utente = ute.id
                dir.attivo = int(cu.IsChecked(n))
            
            map(lambda n: creaDiritto(n), range(cu.GetCount()))
            
            if not dir.Save():
                aw.awu.MsgDialog(None,\
                                 "Impossibile aggiornare i diritti utenti:\n"\
                                 % repr(dir.GetError()))
        
        dlg.Destroy()
    
    def CreateTables( self, droptables=True ):
        """
        Creazione struttura tabelle nel database dell'azienda.
        """
        retVal = False
        pd = aw.awu.WaitDialog(None, maximum=len(Env.Azienda.BaseTab.tabelle))
        try:
            curs = self.dbconn.cursor()
            for n, (tbname, tbdesc, tbdef, tbind, tbctr, tbvoi) in enumerate(Env.Azienda.BaseTab.tabelle):
                pd.SetMessage("Creazione tabella %s" % tbname)
                if droptables:
                    curs.execute("DROP TABLE IF EXISTS %s;" % tbname)
                cmd = "CREATE TABLE %s (" % tbname
                for cname,ctype,clen,ndec,cdes,cattr in tbdef:
                    cmd += cname + ' ' + ctype
                    if clen != None:
                        cmd += "(%d" % (clen+(ndec or 0))
                        if ndec != None and ndec != 0:
                            cmd += ",%d" % ndec
                        cmd += ")"
                    if cattr != None:
                        cmd += ' %s' % cattr
                    if cdes is not None:
                        cdes = cdes.replace("'", "\\'")
                        cdes = cdes.replace("%", "perc.")
                        cmd += " COMMENT '%s'" % cdes
                    cmd += ", "
                #cmd += ", ".join([ ind for ind in tbind ]) + ")"
                for i, (indtype, indexpr) in enumerate(tbind):
                    ind = indtype
                    if not "PRIMARY" in indtype:
                        ind += ' index%d' % i
                    ind += ' (%s)' % indexpr
                    cmd += ind+', '
                cmd = cmd[:-2]+')'
                cmd += r' ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT=%s'
                curs.execute(cmd, (tbdesc,))
                pd.SetValue(n)
            curs.close()
            retVal = True
            
        except MySQLdb.Error, e:
            dlg = wx.MessageDialog(parent=None,
                                   message = "Si sono verificati problemi durante la creazione delle tabelle.\n\n%s: %s"
                                   % (e.args[0], e.args[1]), 
                                   caption = "X4 :: Errore di setup",
                                   style = wx.CANCEL|wx.ICON_EXCLAMATION )
            dlg.ShowModal()
            dlg.Destroy()
        
        pd.Destroy()
        
        return retVal

    def FindAziendaMirage(self):
        if miracq:
            return miracq.FindAziendaMirage(self)


# ------------------------------------------------------------------------------


class AziendaCopyPanel(aw.Panel):
    def __init__(self, parent, namedbdst):
        aw.Panel.__init__(self, parent)
        self.db = adb.DB(globalConnection=False)
        self.db.Connect(host=Env.Azienda.DB.servername,
                        user=Env.Azienda.DB.username,
                        passwd=Env.Azienda.DB.password,
                        db=namedbdst)
        self.copyfrom = None
        self.copydest = namedbdst
        AziendaCopyFunc(self)
        self.dbaz = ListAziende()
        cur = self.db._dbCon.cursor()
        sql = r"""
        SELECT azi.id, azi.codice, azi.azienda, azi.nomedb 
          FROM x4.aziende as azi
         ORDER BY azi.azienda, azi.codice"""
        cur.execute(sql)
        self.dbaz.SetRecordset(cur.fetchall())
        cur.close()
        self.gridaz = SelAziendaGrid(self.FindWindowById(ID_PANGRIDAZI),
                                     self.dbaz)
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, self.FindWindowByName('btnok'))
    
    def OnConfirm(self, event):
        if aw.awu.MsgDialog(self, "Confermi l'acquisizione di queste informazioni?",
                            style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
            rowsel = self.gridaz.GetSelectedRows()[0]
            self.dbaz.MoveRow(rowsel)
            self.copyfrom = self.dbaz.nomedb
            self.CopyData()
            event.Skip()
    
    def CopyData(self):
        bt = Env.Azienda.BaseTab
        copytables = (
            ('concau', (bt.TABNAME_CFGCONTAB,
                        bt.TABNAME_REGIVA,
                        bt.TABNAME_CFGMAGRIV,)),
            ('congrs', (bt.TABNAME_SCADGRP,)),
            ('conpdc', (bt.TABNAME_BILMAS,
                        bt.TABNAME_BILCON,
                        bt.TABNAME_BRIMAS,
                        bt.TABNAME_BRICON,
                        bt.TABNAME_PDC,
                        bt.TABNAME_PDCRANGE,)),
            ('concli', (bt.TABNAME_CLIENTI,
                        bt.TABNAME_DESTIN,
                        bt.TABNAME_BANCF,
                        bt.TABNAME_CATCLI,
                        bt.TABNAME_STATCLI,
                        bt.TABNAME_TIPLIST,
                        bt.TABNAME_SCONTICC,)),
            ('confor', (bt.TABNAME_FORNIT,
                        bt.TABNAME_CATFOR,
                        bt.TABNAME_STATFOR,)),
            ('concas', (bt.TABNAME_CASSE,)),
            ('conban', (bt.TABNAME_BANCHE,)),
            ('magcau', (bt.TABNAME_CFGMAGDOC,
                        bt.TABNAME_CFGMAGMOV,
                        bt.TABNAME_MAGAZZ,
                        bt.TABNAME_CFGFTDIF,
                        bt.TABNAME_CFGFTDDR,)),
            ('magpro', (bt.TABNAME_TIPART,
                        bt.TABNAME_CATART,
                        bt.TABNAME_GRUART,
                        bt.TABNAME_MARART,
                        bt.TABNAME_STATART,
                        bt.TABNAME_GRUPREZ,
                        bt.TABNAME_PROD,
                        bt.TABNAME_CODARTCF,
                        bt.TABNAME_LISTINI,
                        bt.TABNAME_GRIGLIE,)),
            ('magage', (bt.TABNAME_AGENTI,)),
            ('magzne', (bt.TABNAME_ZONE,)),
            ('magtra', (bt.TABNAME_TRAVET,
                        bt.TABNAME_TRACAU,
                        bt.TABNAME_TRACUR,
                        bt.TABNAME_TRAASP,
                        bt.TABNAME_TRAPOR,
                        bt.TABNAME_TRACON,)),
            ('geniva', (bt.TABNAME_ALIQIVA,)),
            ('genval', (bt.TABNAME_VALUTE,)),
            ('genpag', (bt.TABNAME_MODPAG,
                        bt.TABNAME_SPEINC,)),
            ('genaut', (bt.TABNAME_CFGAUTOM,)),
            (None,     (bt.TABNAME_PDCTIP,
                        bt.TABNAME_MACRO,
                        bt.TABNAME_CFGEFF,)))
        numtab = 0
        for section, tables in copytables:
            numtab += len(tables)
        wait = aw.awu.WaitDialog(self, "Acquisizione da '%s'"
                                 % self.copyfrom, maximum=numtab)
        def cn(x):
            return self.FindWindowByName(x)
        try:
            numtab = 0
            for section, tables in copytables:
                if section is None:
                    copy = True
                else:
                    copy = cn('copy%s' % section).GetValue()
                for table in tables:
                    if copy:
                        wait.SetMessage("Copia tabella '%s'" % table)
                        if table == bt.TABNAME_PDC:
                            self._CopyPdc(table,
                                          cn('copyconcli').GetValue(),
                                          cn('copyconfor').GetValue(),
                                          cn('copyconcas').GetValue(),
                                          cn('copyconban').GetValue())
                        else:
                            self._CopyTable(table)
                    numtab += 1
                    wait.SetValue(numtab)
        finally:
            wait.Destroy()
    
    def _CopyTable(self, tabname, filt=''):
        dbtfrom = adb.DbTable('%s.%s' % (self.copyfrom, tabname), 'tabfrom', 
                              db=self.db)
        dbtdest = adb.DbTable('%s.%s' % (self.copydest, tabname), 'tabdest', 
                              db=self.db, forceInsert=True)
        if dbtfrom.Retrieve(filt):
            if ','.join(dbtdest.GetFieldNames()) == ','.join(dbtfrom.GetFieldNames()):
                dbtdest.SetRecordset(dbtfrom.GetRecordset())
            else:
                for row in dbtfrom:
                    dbtdest.CreateNewRow()
                    for col in dbtdest._GetFieldNames():
                        try:
                            value = getattr(dbtfrom, col)
                        except:
                            value = None
                        setattr(dbtdest, col, value)
            dbtdest.WriteAll()
            if not dbtdest.Save():
                raise Exception, repr(dbtdest.GetError())
        return True
    
    def _CopyPdc(self, tabname, copycli, copyfor, copycas, copyban):
        if copycli and copyfor and copycas and copyban:
            return self._CopyTable(tabname)
        tipana = adb.DbTable('%s.pdctip' % self.copyfrom, 'tipana', 
                             writable=False)
        tipiexcl = []
        for do, tipo in ((copycli, 'C'),
                         (copyfor, 'F'),
                         (copycas, 'A'),
                         (copyban, 'B')):
            if not do:
                if tipana.Retrieve("tipana.tipo=%s", tipo):
                    for t in tipana:
                        tipiexcl.append(str(t.id))
                else:
                    raise Exception, repr(tipana.GetError())
        if tipiexcl:
            filt = "id_tipo NOT IN (%s)" % ','.join(tipiexcl)
        else:
            filt = ''
        return self._CopyTable(tabname, filt)


# ------------------------------------------------------------------------------


class AziendaCopyDialog(aw.Dialog):
    
    def __init__(self, parent, namedbdst):
        aw.Dialog.__init__(self, parent, -1, 
                           'Inizializzazione database azienda')
        self.AddSizedPanel(AziendaCopyPanel(self, namedbdst))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, self.FindWindowByName('btnok'))
    
    def OnConfirm(self, event):
        self.EndModal(wx.ID_OK)
