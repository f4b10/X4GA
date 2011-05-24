#!/bin/env python
# -*- coding: utf-8 -*-
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

import wx

import MySQLdb
import stormdb as adb

import awc.layout.gestanag as ga
import cfg.utenti_wdr as wdr

import awc.util as util

from Env import Azienda
bt = Azienda.BaseTab


FRAME_TITLE = "Utenti"


UTENTI_STRUCTURE = [["id",              "INT",       6, None, "ID Destinatario", "AUTO_INCREMENT" ],
                    ["codice",          "CHAR",      2, None, "Codice", None ],
                    ["descriz",         "VARCHAR",  16, None, "Nome", None ],
                    ["psw",             "VARCHAR",  41, None, "Password", None ],
                    ["datePsw",         "TIMESTAMP", 6, None, "Validita' dal", None ],
                    ["Amministratore",  "TINYINT1",  1, None, "Amministratore", None ],
                    ["can_setupcontab", "TINYINT1",  1, None, "Flag permesso setup: contabilità", None ],
                    ["can_setupmagazz", "TINYINT1",  1, None, "Flag permesso setup: magazzino", None ],
                    ["can_setupsetup",  "TINYINT1",  1, None, "Flag permesso setup: impostazioni", None ],
                    ["can_setupother",  "TINYINT1",  1, None, "Flag permesso setup: altro (da esterno)", None ],
                    ["can_setupoption", "TINYINT1",  1, None, "Flag permesso setup: opzioni", None ],
                    ["can_setupoptoth", "TINYINT1",  1, None, "Flag permesso setup: opzioni (da esterno)", None ],
                    ["can_contabins",   "TINYINT1",  1, None, "Flag permesso contabilità: inserimento", None ],
                    ["can_contabint",   "TINYINT1",  1, None, "Flag permesso contabilità: interrogazione", None ],
                    ["can_contabges",   "TINYINT1",  1, None, "Flag permesso contabilità: gestione", None ],
                    ["can_contabfis",   "TINYINT1",  1, None, "Flag permesso contabilità: stampe fiscali", None ],
                    ["can_contabbil",   "TINYINT1",  1, None, "Flag permesso contabilità: bilanci", None ],
                    ["can_contabsca",   "TINYINT1",  1, None, "Flag permesso contabilità: scadenzari", None ],
                    ["can_contabeff",   "TINYINT1",  1, None, "Flag permesso contabilità: effetti", None ],
                    ["can_contabchi",   "TINYINT1",  1, None, "Flag permesso contabilità: chiusure", None ],
                    ["can_magazzins",   "TINYINT1",  1, None, "Flag permesso magazzino: inserimento", None ],
                    ["can_magazzint",   "TINYINT1",  1, None, "Flag permesso magazzino: interrogazione", None ],
                    ["can_magazzdif",   "TINYINT1",  1, None, "Flag permesso magazzino: operazioni differite", None ],
                    ["can_magazzela",   "TINYINT1",  1, None, "Flag permesso magazzino: elaborazioni", None ],
                    ["can_magazzchi",   "TINYINT1",  1, None, "Flag permesso magazzino: elaborazioni", None ],
                    ["can_backupdata",  "TINYINT1",  1, None, "Flag permesso backup: effettuare backup", None ],
                    ["can_restoredata", "TINYINT1",  1, None, "Flag permesso backup: ripristinare backup", None ],]


def CheckUtentiStructure():
    u = adb.DbTable('utenti', 'utenti')
    u.Reset()
    if not 'can_setupcontab' in u.GetFieldNames():
        if util.MsgDialog(None,
                          """La tabella di configurazione degli utenti\n"""
                          """deve essere modificata.\n\nProcedo?""", 
                          "Variazione struttura database", 
                          style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) != wx.ID_YES:
            return False
        err = None
        cmd = """
        ALTER TABLE `x4`.`utenti` 
        ADD COLUMN `can_setupcontab` TINYINT(1) AFTER `amministratore`,
        ADD COLUMN `can_setupmagazz` TINYINT(1) AFTER `can_setupcontab`,
        ADD COLUMN `can_setupsetup`  TINYINT(1) AFTER `can_setupmagazz`,
        ADD COLUMN `can_setupother`  TINYINT(1) AFTER `can_setupsetup`,
        ADD COLUMN `can_setupoption` TINYINT(1) AFTER `can_setupother`,
        ADD COLUMN `can_setupoptoth` TINYINT(1) AFTER `can_setupoption`,
        ADD COLUMN `can_contabins`   TINYINT(1) AFTER `can_setupoptoth`,
        ADD COLUMN `can_contabint`   TINYINT(1) AFTER `can_contabins`,
        ADD COLUMN `can_contabges`   TINYINT(1) AFTER `can_contabint`,
        ADD COLUMN `can_contabfis`   TINYINT(1) AFTER `can_contabges`,
        ADD COLUMN `can_contabbil`   TINYINT(1) AFTER `can_contabfis`,
        ADD COLUMN `can_contabsca`   TINYINT(1) AFTER `can_contabbil`,
        ADD COLUMN `can_contabeff`   TINYINT(1) AFTER `can_contabsca`,
        ADD COLUMN `can_contabchi`   TINYINT(1) AFTER `can_contabeff`,
        ADD COLUMN `can_magazzins`   TINYINT(1) AFTER `can_contabchi`,
        ADD COLUMN `can_magazzint`   TINYINT(1) AFTER `can_magazzins`,
        ADD COLUMN `can_magazzdif`   TINYINT(1) AFTER `can_magazzint`,
        ADD COLUMN `can_magazzela`   TINYINT(1) AFTER `can_magazzdif`,
        ADD COLUMN `can_magazzchi`   TINYINT(1) AFTER `can_magazzela`,
        ADD COLUMN `can_backupdata`  TINYINT(1) AFTER `can_magazzchi`,
        ADD COLUMN `can_restoredata` TINYINT(1) AFTER `can_backupdata`;"""
        if u._info.db.Execute(cmd):
            adb.dbtable.ClearCache()
            cmd = """
            UPDATE utenti SET
            can_setupcontab=1,
            can_setupmagazz=1,
            can_setupsetup=1,
            can_setupother=1,
            can_setupoption=1,
            can_setupoptoth=1,
            can_contabins=1,
            can_contabint=1,
            can_contabges=1,
            can_contabfis=1,
            can_contabbil=1,
            can_contabsca=1,
            can_contabeff=1,
            can_contabchi=1,
            can_magazzins=1,
            can_magazzint=1,
            can_magazzdif=1,
            can_magazzela=1,
            can_magazzchi=1,
            can_backupdata=1,
            can_restoredata=1"""
            if not u._info.db.Execute(cmd):
                err = repr(u._info.db.dbError.description)
        else:
            err = repr(u._info.db.dbError.descripion)
        if err:
            util.MsgDialog(None, err, style=wx.ICON_ERROR)
            return False
    return True


# ------------------------------------------------------------------------------


class UtentiPanel(ga.AnagPanel):
    """
    Pannello gestione utenti
    """
    oldUsername=None
    oldPassword=None
    my=None
    
    
    
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        #self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_AGENTI ] )
        self.db_tabname = 'utenti'
        self.db_tabdesc = "Tabella Utenti"
        self.db_report = "Utenti"
        self.db_columns = UTENTI_STRUCTURE
        self.SetDbOrderColumns((("Codice",      ('utenti.codice',)),
                                ("Descrizione", ('utenti.descriz',)),))
        self.db_tabconstr = ()
        #self.SetDbSearchColumns( ("descriz", "codice", "id") )
        self.db_searchfilter = ""
        self.dbdir = adb.DbTable('diritti', writable=True)
        self.dbdir.AddMultiJoin("aziende", "azi", idLeft="id_azienda", idRight="id")        
        self.aziende = []
        

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.UtentiCardFunc( p, True )
        azi = adb.DbTable('aziende', writable=False)
        azi.AddOrder('azienda')
        azi.AddOrder('codice')
        self.aziende = []
        for name, val in ( ("Amministratore",     { True: 'X', False: ' '} ),\
                           ):
            ctr = self.FindWindowByName(name)
            ctr.SetDataLink(name, val)
        
        if azi.Retrieve():
            l = self.FindWindowById(wdr.ID_AZIENDE)
            for a in azi:
                l.Append('%s (%s)' % (a.azienda, a.codice))
                self.aziende.append(a.id)
            self.Bind(wx.EVT_CHECKLISTBOX, self.OnAziModif, l)
        return p
    
    def OnAziModif(self, event):
        self.SetDataChanged(True)
        event.Skip()


    def OnRecordNew( self, event ):
        ga.AnagPanel.OnRecordNew( self, event )
        l = self.FindWindowById(wdr.ID_AZIENDE)
        for i in range(l.GetCount()):
            l.Check(i, False)
        event.Skip()

    def OnRecordDelete( self, event ):
        lMemo=True
        id = self.FindWindowByName("id")
        ctr = self.FindWindowByName("Amministratore")
        if not self.existSupervisor(id.GetValue()):
            dlg = wx.MessageDialog(
            parent=None,
            message = "Operazione non consentita.\n\n"+
            "Si sta cercando di eliminare l'unico utente che gode \n"+
            "del diritto di Amministratore.\n"+
            "Poichè deve essere previsto almeno un utente con il ruolo\n"+
            "di Amministratore, l'operazione è annullata.",
            caption = "X4 :: Errore",
            style = wx.OK|wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            lMemo=False
        
        if lMemo:
            username = self.FindWindowById(wdr.ID_UTENTE).GetValue()
            id_utente=self.db_recid
            out=ga.AnagPanel.OnRecordDelete( self, event )
            if out:
                # annullo diritti utente cancellato
                du = self.dbdir
                du.ClearFilters()
                du.AddFilter('diritti.id_utente=%s', id_utente)
                du.Retrieve()
                for d in du:
                    d.Delete()
                    d.Save()
        event.Skip()
        
    def UpdateSearch(self, *args, **kwargs):
        out = ga.AnagPanel.UpdateSearch(self, *args, **kwargs)
        self.checkDiritti()
        return out
        
    def UpdateDataControls(self, *args, **kwargs):
        """
        Il metodo provvede a caricare i controlli a video con i dati presenti negli archivi.
        """
        ga.AnagPanel.UpdateDataControls(self, *args, **kwargs)
        du = self.dbdir
        self.oldUsername=None
        self.oldPassword=None
        if self.db_recid is None:
            du.Reset()
        else:
            self.oldUsername=self.FindWindowById(wdr.ID_UTENTE).GetValue()
            self.oldPassword=self.FindWindowById(wdr.ID_PSW).GetValue()
            l = self.FindWindowById(wdr.ID_AZIENDE)
            for i in range(l.GetCount()):
                l.Check(i, False)
            du.ClearFilters()
            du.AddFilter('diritti.id_utente=%s', self.db_recid)
            if du.Retrieve():
                for d in du:
                    if d.id_azienda in self.aziende:
                        n = self.aziende.index(d.id_azienda)
                        l.Check(n, d.attivo == 1)

    def UpdateDataRecord(self, *args, **kwargs):
        out = True
        
        id = self.FindWindowByName("id")
        code = self.FindWindowByName("codice")
        user = self.FindWindowById(wdr.ID_UTENTE)
        
        cn = lambda x: self.FindWindowByName(x)
        
        codice = code.GetValue()
        utente = user.GetValue()
        if self.existUser(codice, utente, (self.db_recno < 0) ):
            dlg = wx.MessageDialog(
            parent=None,
            message = "Operazione non consentita.\n\n"+
            "Esiste gia' un utente con il codice o la descrizione specificata.\n"+
            "Poichè la codifica degli utenti deve essere univoca, l'operazione è annullata.",
            caption = "X4 :: Errore",
            style = wx.OK|wx.ICON_ERROR )
            dlg.ShowModal()
            dlg.Destroy()
            out = False
        
        if out:
            amm = cn("Amministratore")
            if not amm.GetValue() == "X":
                if not self.existSupervisor(id.GetValue()):
                    dlg = wx.MessageDialog(
                    parent=None,
                    message = "Operazione non consentita.\n\n"+
                    "Si sta cercando di rimuovere il diritto di Amministratore \n"+
                    "all'unico utente che gode di tale diritto.\n"+
                    "Poichè deve essere previsto almeno un utente con il ruolo\n"+
                    "di Amministratore, l'operazione è annullata.",
                    caption = "X4 :: Errore",
                    style = wx.OK|wx.ICON_ERROR )
                    dlg.ShowModal()
                    dlg.Destroy()
                    amm.SetValue("X")
                    out = False
        
        if out:
            out = ga.AnagPanel.UpdateDataRecord(self, *args, **kwargs)
        
        return out
    
    def TransferDataFromWindow(self, *args, **kwargs):
        """
        Il metodo si fa carico di memorizzare i dati presentati a video, in particolare
        per l'utente identificato da self.db_recid e per ogni azienda presente in self.aziende
        viene memorizzato un record nella tabella x4.diritti che indica se l'utente è abilitato
        o meno ad operare sull'azienda.
        
        Prima di richiamare il metodo padre che provvede alla memorizzazione dei dati nel database
        il valore crittografato della chiave digitata, viene assegnato al controllo identificato da
        wx.ID_PSW.
        
        """
        id = self.FindWindowByName("id")
        code = self.FindWindowByName("codice")
        user = self.FindWindowById(wdr.ID_UTENTE)
        
        psw=self.FindWindowById(wdr.ID_PSW).GetValue()
        if self.oldPassword<>psw:
            self.db_curs.execute("select old_password('%s');" % psw)
            ecrypt_psw=self.db_curs.fetchone()[0]
            self.FindWindowById(wdr.ID_PSW).SetValue(ecrypt_psw)
        out = ga.AnagPanel.TransferDataFromWindow(self, *args, **kwargs)
        
        if out:
            du = self.dbdir
            l = self.FindWindowById(wdr.ID_AZIENDE)
            for r, a in enumerate(self.aziende):
                attivo=False
                du.ClearFilters()
                du.AddFilter('diritti.id_utente=%s', self.db_recid)
                du.AddFilter('diritti.id_azienda=%s', a)
                if du.IsEmpty():
                    self.checkDiritti()
                    du.ClearFilters()
                    du.AddFilter('diritti.id_utente=%s', self.db_recid)
                    du.AddFilter('diritti.id_azienda=%s', a)
                if du.Retrieve() and du.OneRow():
                    attivo=l.IsChecked(r)
                    du.attivo = int(l.IsChecked(r))
                    if not du.Save():
                        util.MsgDialog(self, repr(du.GetError()))
                else:
                    util.MsgDialog(self, repr(du.GetError()))
                record=(self.db_recid, a, attivo)
                pass
            self.createMySqlUser()        
        return out
    
    def createMySqlUser(self):
        user = self.FindWindowById(wdr.ID_UTENTE).GetValue()
        psw = self.FindWindowById(wdr.ID_PSW).GetValue() 
        du = self.dbdir
        du.ClearFilters()
        du.AddFilter('diritti.id_utente=%s', self.db_recid)
        du.Retrieve() 
        
    def checkDiritti(self):
        """
        Il metodo provvede ad controllare per ogni utente e per ogni azienda l'esistenza del
        corrispondente record sulla tabella dei diritti (x4.diritti). Nel caso tale record
        non fosse presente, viene creato negando il diritto dell'utente ad operare sull'azienda.
        """
        du = self.dbdir
        for u in self.db_rs:
            for a in self.aziende:
                if not self.existDiritti(u[2], a):
                    if not du.New(id_utente=u[2], id_azienda=a, attivo=0):
                        util.MsgDialog(self, repr(du.GetError()))
                        return

    def existDiritti(self, id_user, id_azienda):
        """
        Il metodo controlla l'esistenza nella tabella x4.diritti del record relativo
        al diritto per l'utente id_use ad operare sull'azienda id_azienda
        """
        lFound = True
        du = self.dbdir
        du.ClearFilters()
        du.AddFilter('diritti.id_utente=%s', id_user)
        du.AddFilter('diritti.id_azienda=%s', id_azienda)
        du.Retrieve()
        if du.IsEmpty():
            lFound = False
        return lFound

    
    def existSupervisor(self, id):
        lEsito=False
        db = adb.DB()
        db._dbCon = self.db_conn
        db.connected = True
        ute = adb.DbTable('utenti', db=db, writable=False)
        if not ute.Retrieve("amministratore='X' and not id=%s" % id):
            util.MsgDialog(None,\
                           "Impossibile accedere alla tabella Utenti:\n"\
                           % repr(ute.GetError()))
        else:
            if ute.RowsCount()>0:
                lEsito=True
        return lEsito
    
    
    def existUser(self, code, user, lNew):
        lEsito=False
        db = adb.DB()
        db._dbCon = self.db_conn
        db.connected = True
        ute = adb.DbTable('utenti', db=db, writable=False)
        if not ute.Retrieve("codice='%s' or descriz='%s'" % (code, user)):
            util.MsgDialog(None,\
                             "Impossibile accedere alla tabella Utenti:\n"\
                             % repr(ute.GetError()))
        else:
            if ute.RowsCount()>0 and lNew:
                lEsito=True
            elif ute.RowsCount()>1 and not lNew:
                lEsito=True
        return lEsito
    
    

# ------------------------------------------------------------------------------


class UtentiDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Utenti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(UtentiPanel(self, -1), forceComplete=True)
