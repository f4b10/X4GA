#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         backexp.py
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

import os, sys

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc.controls.windows as aw

import X_wdr as wdr

import stormdb as adb

import Env
bt = Env.Azienda.BaseTab

from awc.controls.attachbutton import AttachTableMemo
class AttachTable(AttachTableMemo):
    def __init__(self, table=bt.TABNAME_ALLEGATI, *args, **kwargs):
        AttachTableMemo.__init__(self, table, *args, **kwargs)
        self.ClearFilters()

import lib


FRAME_TITLE  ="X4 Backup Explorer"


def CanUserBackupData():
    o = True
    try:
        o = (Env.Azienda.Login.userdata.can_backupdata == 1)
    except:
        pass
    return o


def CanUserRestoreBackup():
    o = True
    try:
        o = (Env.Azienda.Login.userdata.can_restoredata == 1)
    except:
        pass
    return o


class BackupExplorerGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=parent.GetClientSizeTuple())
        
        self.dbdir = None
        
        _NUM = gl.GRID_VALUE_NUMBER+":7"
        _STR = gl.GRID_VALUE_STRING
        _CHK = gl.GRID_VALUE_BOOL+":'all','partial'"
        _DTT = gl.GRID_VALUE_DATETIME+":withtime"
        
        cols = (\
            (180, (0, "Nome file", _STR, True )),
            ( 90, (3, "Database",  _STR, True )),
            (140, (1, "Data",      _DTT, True )),
            (100, (2, "Bytes",     _NUM, True )),
            ( 35, (4, "(*)",       _CHK, True )),
            (300, (5, "Commento",  _STR, True )),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData((), colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(5)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def SetContent(self, dbdir):
        self.dbdir = dbdir
        self.ChangeData(dbdir.GetRecordset() or ())


# ------------------------------------------------------------------------------


class SpecificheBackupPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        self._mode = None
        self.cando = True
        wdr.SpecificheBackupFunc(self)
        cn = self.FindWindowByName
        self.CheckTables()
        self.Bind(wx.EVT_BUTTON, self.OnProceed, cn('butok'))
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckTables, cn('alltables'))
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckAllTables, cn('selectall'))
#        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnCheckTables, cn('tables'))
    
    def SetModeBackup(self, filename):
        self._SetMode('backup', filename)
    
    def SetModeRestore(self, filename):
        self._SetMode('restore', filename)
    
    def _SetMode(self, mode, filename):
        self._mode = mode
        cn = self.FindWindowByName
        t = cn('tables')
        b = cn('butok')
        if mode == 'backup':
            b.SetLabel('Avvia Backup')
            t.SetModeBackup()
            m = 'Creazione nuovo file di backup'
            c = 'blue'
        elif mode == 'restore':
            b.SetLabel('Avvia Ripristino')
            cn('comment').SetEditable(False)
            cn('allegati').Hide()
            cn('alltables').SetLabel('Includi tutte le tabelle definite nel backup')
            wx.BeginBusyCursor()
            try:
                db_name, content, comment, tabrows =\
                        adb.db.__database__.ADB_GetFileInfo(filename, read_tables=True)
                cn('comment').SetValue(comment)
                t.SetModeRestore(tabrows)
                if db_name != adb.db.__database__.database:
                    self.cando = False
                    cn('warning').SetLabel('Il backup è di un\'altra azienda')
                    self.CheckTables()
            finally:
                wx.EndBusyCursor()
            m = 'Ripristino azienda da file di backup'
            c = 'red'
        else:
            raise Exception, 'Modo non valido'
        def OnCheckItem(index, flag):
            self.CheckTables()
        t.OnCheckItem = OnCheckItem
        t = cn('titletext')
        t.SetLabel(m)
        t.SetForegroundColour(c)
        b.SetForegroundColour(c)
        f = cn('filename')
        f.SetValue(filename)
        f.SetEditable(False)
        self.CheckTables()
    
    def OnCheckTables(self, event):
        self.CheckTables()
        cn = self.FindWindowByName
        a = cn('alltables').IsChecked()
        cn('selectall').SetValue(not a)
        event.Skip()
    
    def CheckTables(self):
        cn = self.FindWindowByName
        a = cn('alltables').IsChecked()
        e = cn('tables')
        if a:
            for n in range(e.GetItemCount()):
                e.CheckItem(n, a)
        e.Enable(not a)
        cn('selectall').Enable(not a)
        if a:
            c = True
        else:
            c = False
            for n in range(e.GetItemCount()):
                if e.IsChecked(n):
                    c = True
                    break
        cn('butok').Enable(c and self.cando and 
                           (self._mode == 'backup' and CanUserBackupData() or 
                            self._mode == 'restore' and CanUserRestoreBackup()))
    
    def OnCheckAllTables(self, event):
        self.CheckAllTables()
        event.Skip()
    
    def CheckAllTables(self):
        cn = self.FindWindowByName
        a = cn('selectall').IsChecked()
        e = cn('tables')
        for n in range(e.GetItemCount()):
            e.CheckItem(n, a)
        self.CheckTables()
    
    def OnProceed(self, event):
        cn = self.FindWindowByName
        e = cn('tables')
        if Env.Azienda.Login.userdata.amministratore != "X":
            for n in range(e.GetItemCount()):
                if not e.IsChecked(n):
                    aw.awu.MsgDialog(self, "Non hai le credenziali per effettuare/ripristinare\nun backup parziale.", style=wx.ICON_ERROR)
                    return
        event.Skip()


# ------------------------------------------------------------------------------


class SpecificheBackupDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = 'Crea nuovo backup'
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = SpecificheBackupPanel(self)
        self.AddSizedPanel(self.panel)
        cn = self.FindWindowByName
        self.Bind(wx.EVT_BUTTON, self.OnProceed, cn('butok'))
    
    def SetModeBackup(self, filename):
        self.panel.SetModeBackup(filename)
    
    def SetModeRestore(self, filename):
        self.panel.SetModeRestore(filename)
    
    def GetComment(self):
        return self.FindWindowByName('comment').GetValue() or ''
    
    def GetAllegati(self):
        return self.FindWindowByName('allegati').IsChecked()
    
    def GetTables(self):
        return self.FindWindowByName('tables').GetTables()
    
    def OnProceed(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class BackupExplorerPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.BackupExplorerFunc(self)
        cn = self.FindWindowByName
        cn('backupdir').SetValue(bt.OPTBACKUPDIR)
        self.griddir = BackupExplorerGrid(cn('pangridbackup'))
        self.UpdateContent()
        self.Bind(wx.EVT_BUTTON, self.OnNewBackup, cn('butnew'))
        self.Bind(wx.EVT_BUTTON, self.OnUpdateContent, cn('butrefresh'))
        self.Bind(wx.EVT_TEXT, self.OnUpdateContent, cn('backupdir').address)
        self.Bind(wx.EVT_CHECKBOX, self.OnUpdateContent, cn('solazi'))
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnRowDoubleClick, self.griddir)
    
    def OnNewBackup(self, event):
        self.CreateNewBackup()
        event.Skip()
    
    def OnRowDoubleClick(self, event):
        dbdir = self.griddir.dbdir
        dbdir.MoveRow(event.GetRow())
        self.OpenBackup(dbdir.filename)
        event.Skip()
    
    def OnUpdateContent(self, event):
        self.UpdateContent()
        event.Skip()
    
    def CreateNewBackup(self):
        
        cn = self.FindWindowByName
        
        pathname = cn('backupdir').GetValue()
        filename = None
        allegati = False
        comment = None
        tables = None
        
        d = Env.DateTime.DateTime.now()
        z = lambda x, l: str(x).zfill(l)
        defaultFile = '%s %s-%s-%s %s-%s-%s' % (Env.Azienda.codice, 
                                                z(d.year,4), z(d.month,2), z(d.day,2), 
                                                z(d.hour,2), z(d.minute,2), z(d.second,2))
        dlg = wx.FileDialog(self,
                            message="Digita il nome del file da generare",
                            defaultDir=pathname,
                            defaultFile=defaultFile,
                            wildcard="File di Backup (*.adb)|*.adb",
                            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()
        
        if filename:
            if not filename.lower().endswith('.adb'):
                filename += '.adb'
            if os.path.exists(filename):
                if aw.awu.MsgDialog(self, "Il file esiste già, vuoi sovrascriverlo?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                    filename = None
        
        if filename:
            dlg = SpecificheBackupDialog(self)
            dlg.SetModeBackup(filename)
            if dlg.ShowModal() == wx.ID_OK:
                comment = dlg.GetComment()
                allegati = dlg.GetAllegati()
                tables = dlg.GetTables()
            else:
                filename = None
            dlg.Destroy()
        
        if filename:
            
            tab_classes = {bt.TABNAME_ALLEGATI: AttachTable}
            special_encoders = {}
            if allegati:
                def IncludeRecordInfo(t, row):
                    t.MoveRow(row)
                    encimg = t.GetBase64EncodedImage()
                    return t._info.db.ADB_EncodeValue(None, base64_encoded=encimg)
                special_encoders[bt.TABNAME_ALLEGATI] = {"attach_stream": IncludeRecordInfo}
            
            wait = aw.awu.WaitDialog(self, "Creazione backup in corso...", maximum=len(tables), progress2=True)
            wait._msg1 = wait._msg2 = ''
            wait._val1 = wait._val2 = 0
            self.timer = wx.Timer(wait)
            def UpdateRecordInfo():
                wait.SetMessage2(wait._msg2)
                wait.SetValue2(wait._val2)
            def OnTimer(event):
                UpdateRecordInfo()
            wait.Bind(wx.EVT_TIMER, OnTimer, self.timer)
            self.timer.Start(500)
            wx.BeginBusyCursor()
            
            try:
                
                def TableRecord(t, row):
                    try:
                        p = float(row)/t.RowsCount()*100
                    except ZeroDivisionError:
                        p = 0
                    wait._msg2 = 'Riga %d (%d%%)' % (row, p)
                    wait._val2 = row
                    wx.YieldIfNeeded()
                
                def TableRead(t):
                    wait.SetMessage('Tabella: %s (%s righe)' % (t.GetTableName(), t.RowsCount()))
                    wait.SetValue(wait.GetValue()+1)
#                    wait.SetMessage2('')
#                    wait.SetValue2(0)
#                    wait._msg2 = ''
#                    wait._val2 = 0
                    wait.SetRange2(t.RowsCount())
                    TableRecord(t, 0)
                    UpdateRecordInfo()
                
                content = 'all'
                if len(tables) != len(bt.tabelle):
                    content = 'partial'
                adb.db.__database__.ADB_CreateFile(tables, filename, comment, content=content,
                                                   tab_classes=tab_classes, 
                                                   special_encoders=special_encoders,
                                                   on_table_read=TableRead,
                                                   on_table_row=TableRecord)
            finally:
                wx.EndBusyCursor()
                del self.timer
                wait.Destroy()
            
            aw.awu.MsgDialog(self, 'Il file di backup è stato generato correttamente:\n%s' % filename, style=wx.ICON_INFORMATION)
        
        self.UpdateContent()
    
    def UpdateContent(self):
        cn = self.FindWindowByName
        folder = cn('backupdir').GetValue()
        database = None
        if cn('solazi').IsChecked():
            database = adb.db.__database__.database
        wx.BeginBusyCursor()
        try:
            try:
                content = adb.db.__database__.ADB_GetBackupFolderContent(folder, database=database, read_tables=False, order_by='datetime', order_reverse=True)
            except:
                content = None
        finally:
            wx.EndBusyCursor()
        self.griddir.SetContent(content)
        cn('butnew').Enable(bool(folder) and os.path.isdir(folder) and CanUserBackupData())
    
    def OpenBackup(self, filename):
        cn = self.FindWindowByName
        fullname = os.path.join(cn('backupdir').GetValue(), filename)
        dlg = SpecificheBackupDialog(self)
        dlg.SetModeRestore(fullname)
        do = False
        if dlg.ShowModal() == wx.ID_OK:
            do = False
            msg =\
            """Attenzione!!!\n\n"""\
            """Confermando il ripristino, i dati attualmente presenti nell'azienda\n"""\
            """verranno sovrascritti con quelli contenuti nel file!!!\n"""\
            """Procedere solo se si è certi che il ripristino è effettivamente da fare!!!"""
            if aw.awu.MsgDialog(self, msg, "Conferma del ripristino", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                do = True
                tables = dlg.GetTables()
                if len(bt.tabelle) != len(tables):
                    msg =\
                    """ATTENZIONE !!!\n\n"""\
                    """Si sta ripristinando una copia dell'azienda con meno tabelle del previsto.\n"""\
                    """Questo potrebbe portare ad inconsistenze nel database!\n"""\
                    """Procedere solo se si è certi che questo particolare ripristino è corretto!!!"""
                    if aw.awu.MsgDialog(self, msg, "Conferma di ripristino particolare", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                        do = False
        dlg.Destroy()
        if do:
            if self.RestoreBackup(fullname, tables):
                aw.awu.MsgDialog(self, "Il backup è stato ripristinato", style=wx.ICON_INFORMATION)
    
    def RestoreBackup(self, filename, tables):
        
        wait = aw.awu.WaitDialog(self, "Ripristino backup in corso...", maximum=len(tables), progress2=True)
        wait._msg1 = wait._msg2 = ''
        wait._val1 = wait._val2 = wait._rows = 0
        self.timer = wx.Timer(wait)
        def UpdateRecordInfo():
            wait.SetMessage2(wait._msg2)
            wait.SetValue2(wait._val2)
        def OnTimer(event):
            UpdateRecordInfo()
        wait.Bind(wx.EVT_TIMER, OnTimer, self.timer)
        self.timer.Start(500)
        wx.BeginBusyCursor()
        
        try:
            
            def TableRecord(tab_name, row):
                try:
                    p = float(row)/wait._rows*100
                except ZeroDivisionError:
                    p = 0
                wait._msg2 = 'Riga %d (%d%%)' % (row, p)
                wait._val2 = row
                wx.YieldIfNeeded()
            
            def TableStart(tab_name, rows):
                wait.SetMessage('Ripristino tabella: %s (%s righe)' % (tab_name, rows))
                wait.SetValue(wait.GetValue()+1)
                wait.SetRange2(rows)
                wait._rows = rows
                wait._msg2 = 'Riga %d (%d%%)' % (0, 0)
                wait._val2 = 0
            
            dbatt = AttachTable()
            def AttachWriteFile(row, column, value, columns, values):
                col_id = columns.index('id')
                col_file = columns.index('file')
                att_id = values[col_id]
#                filename = values[col_file]
                stream = db.ADB_DecodeValue(value)
                if dbatt.Get(att_id):
                    dbatt
                fullname = dbatt.GetFileName().replace('\\', '/')
                pathname, filename = os.path.split(fullname)
                if not os.path.isdir(pathname):
                    partpath = ''
                    for path in pathname.split('/'):
                        if partpath:
                            partpath += '/'
                        partpath += path
                        if not os.path.isdir(partpath):
                            os.mkdir(partpath)
                f = file(fullname, 'wb')
                f.write(stream)
                f.close()
            
            db = adb.db.__database__
            db.ADB_RestoreFile(filename, db.database,
                               special_decoders={bt.TABNAME_ALLEGATI: {'attach_stream': AttachWriteFile}},
                               on_table_init=TableStart,
                               on_table_write=TableRecord)
        finally:
            wx.EndBusyCursor()
            del self.timer
            wait.Destroy()
        
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        
        return True
        

# ------------------------------------------------------------------------------


class BackupExplorerFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BackupExplorerPanel(self))


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    
    #sostitizione logo
    name = 'X4Logo'
    import images
    for suffix in 'Bitmap Data Image'.split():
        setattr(images, 'get%s%s' % (name, suffix), getattr(images, 'get%sBackup%s' % (name, suffix)))
    
    class BackupExplorerApp(wx.PySimpleApp):
        
        def OnInit(self):
            
            if not Env.InitSettings(ask_missing_config=False):
                aw.awu.MsgDialog(None, "File di configurazione non trovato.")
                return False
            
            from selazienda import SelAziendaDialog
            aziDialog = SelAziendaDialog()
            d = aziDialog.FindWindowByName('appdesc')
            d.SetLabel('X4 Backup Explorer')
            d.SetForegroundColour('red')
            import X_wdr as wdr
            aziDialog.FindWindowById(wdr.ID_VERSION).Hide()
            aziDialog.FindWindowByName('licinfo').Hide()
            aziDialog.FindWindowByName('verinfo').Hide()
            do = aziDialog.ShowModal() == 1
            aziDialog.Destroy()
            
            if do:
                db = adb.db.__database__
                if not db.Connect(host=Env.Azienda.DB.servername,
                                  user=Env.Azienda.DB.username,
                                  passwd=Env.Azienda.DB.password,
                                  db=Env.Azienda.DB.schema):
                    aw.awu.MsgDialog(None, repr(db.dbError.description), style=wx.ICON_ERROR)
                    do = False
            else:
                do = False
            
            if do:
                f = BackupExplorerFrame(None)
                f.Show()
                return True
            
            os._exit(1)
    
    adb.dbtable.DbInfo.GetEnv = classmethod(lambda *x: Env)
    
    import xpaths
    config_base_path = xpaths.GetConfigPath()
    
    Env.SetConfigBasePath()
    
    import erman
    def _exceptionhook(type, err, traceback):
        erman.ErrorWarning(err, traceback)
    sys.excepthook = _exceptionhook

    a = BackupExplorerApp()
    a.MainLoop()
    
    os._exit(0)
