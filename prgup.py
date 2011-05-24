#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         prgup.py
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
Sistema di controllo aggiornamenti versione programma.
"""


import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib

import Env

import awc.controls.windows as aw
msgbox = aw.awu.MsgDialog

import X_wdr as wdr

import version as ver

import urllib2, base64

import os, sys

from cfg.wksetup import ConfigPanel, ConfigDialog


MODE_VERIFY =   0
MODE_UPDATE =   1
MODE_DOWNLOAD = 2
MODE_SETUP =    3
MODE_CLOSE =    4


KB = 1024.0
MB = KB*1024
GB = MB*1024
TB = GB*1024


BUFSIZE = int(8*KB)


def SizeRepr(bytes):
    if bytes < MB:
        msg = '%.0f KB' % (bytes/KB)
    elif bytes < GB:
        msg = '%.3f MB' % (bytes/MB)
    elif bytes < TB:
        msg = '%.3f GB' % (bytes/GB)
    else:
        msg = '%d Bytes' % bytes
    return msg


# ------------------------------------------------------------------------------


import stormdb as adb
RSVER_PRGNAME =  0
RSVER_PRGTYPE =  1
RSVER_PRGAUTH =  2
RSVER_PRGUURL =  3
RSVER_VERINST =  4
RSVER_VERDISP =  5
RSVER_VERDESC =  6
RSVER_FILEURL =  7
RSVER_TYPEURL =  8
RSVER_UPDATEP =  9
RSVER_MESSAGE = 10


class VersionsDb(adb.DbMem):
    
    def __init__(self):
        adb.DbMem.__init__(self, 'prgname,prgtype,prgauth,prguurl,verinst,verdisp,verdesc,fileurl,typeurl,update,message')
        rs = []
        serverx4 = Env.Azienda.config.Updates_url
        if serverx4.endswith('/'):
            serverx4 = serverx4[:-1]
        fileurl = '%s-%s.exe' % (wx.GetApp().setupname, Env.__version__)
        typeurl = 'H'
        rs.append(['x4ga', 'X4 Gestione Aziendale', 'Astra S.r.l.', 
                   serverx4, Env.__version__, '?', '', fileurl, typeurl, False, ''])
        try:
            import custapp
            fileurl = '%s-%s.zip' % (Env.MODVERSION_NAME, Env.__modversion__)
            typeurl = 'C'
            rs.append([custapp.name, custapp.title, custapp.author, 
                       serverx4, Env.__modversion__, '?', '', fileurl, typeurl, False, ''])
        except:
            pass
        for p in Env.plugins:
            m = Env.plugins[p]
            try:
                server = m.updates_url
                if server.endswith('/'):
                    server = server[:-1]
            except:
                server = serverx4
            fileurl = '%s-%s.zip' % (p, m.version)
            typeurl = 'P'
            rs.append([p, m.title, m.author, 
                       server, m.version, '?', m.description, fileurl, typeurl, False, ''])
        self.SetRecordset(rs)
    
    def CheckUpdates(self):
        
        downloads = []
        
        for e in self:
            server = e.prguurl
            name = e.fileurl
            if server.endswith('/'):
                server = server[:-1]
            if not server.endswith('/updates'):
                server += '/updates'
            url = '%s/latestver.php' % server
            if e.typeurl == 'H':
                url += '?inst='
            elif e.typeurl == 'C':
                url += '?cust='
            elif e.typeurl == 'P':
                url += '?plugin='
            url += name
            err = None
            try:
                h = urlopen(url)
                setup = h.read()
                h.close()
                if setup != 'updated':
                    if not setup[-4:] in ('.exe','.zip'):
                        err = "Risposta dal server non riconosciuta"
                        break
            except IOError, e:
                err = 'Problema durante la connessione al server\n%s'\
                        % repr(e.msg)
                break
            except Exception, e:
                err = 'Problema durante la connessione al server\n%s'\
                        % repr(e.args)
                break
            if '/' in setup:
                n = setup.rindex('/')
                dlfile = setup[n+1:]
                parts = dlfile[:-4].split('-')
                dlver = parts[1]
                e.verdisp = dlver
                e.update = (e.verdisp>e.verinst)
                if e.update:
                    e.message = 'Da aggiornare'
                    downloads.append((server+'/'+setup, e.typeurl))
                else:
                    e.message = 'Ok'
                    e.verdisp = '-'
                if e.update:
                    update = True
            else:
                e.update = False
                e.message = 'Ok'
                e.verdisp = '-'
        
        if err:
            raise Exception, err
        
        return downloads
        
            


# ------------------------------------------------------------------------------


class VersionsGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbver):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent,
                                              size=parent.GetClientSizeTuple())
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        
        cols = (\
            ( 80, (RSVER_PRGNAME, "Package",   _STR, True)),
            (260, (RSVER_PRGTYPE, "Tipo",      _STR, True)),
            ( 80, (RSVER_VERINST, "Ver.Inst.", _STR, True)),
            ( 80, (RSVER_VERDISP, "Ver.Disp.", _STR, True)),
            (120, (RSVER_MESSAGE, "Azione",    _STR, True)),
        )                                           
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(dbver.GetRecordset(), colmap, canedit, canins)
        
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
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def OnDblClick(self, event):
        event.Skip()


# ------------------------------------------------------------------------------


class URLrequest(urllib2.Request):
    def __init__(self, url, user=None, pswd=None):
        urllib2.Request.__init__(self, url)
        config = Env.Azienda.config
        user = user or config.Updates_user
        pswd = pswd or config.Updates_pswd
        string = '%s:%s' % (user, pswd)
        stringb64 = base64.encodestring(string)[:-1]
        self.add_header("Authorization", "Basic %s" % stringb64)


# ------------------------------------------------------------------------------


def urlopen(url, user=None, pswd=None):
    return urllib2.urlopen(URLrequest(url, user, pswd))


# ------------------------------------------------------------------------------


class ProgramUpdatePanel(aw.Panel):
    mode = MODE_VERIFY
    dlurl = None
    dlfile = None
    runexe = None
    download = False
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.downloads = []
        wdr.ProgramUpdateFunc(self)
        ci = lambda x: self.FindWindowById(x)
        ci(wdr.ID_URL).SetLabel('%s/updates' % Env.Azienda.config.get('Updates', 'url'))
        self.dbver = VersionsDb()
        self.gridver = VersionsGrid(ci(wdr.ID_PANGRIDUPDATES), self.dbver)
        self.action, self.message =\
            map(ci, (wdr.ID_ACTION, wdr.ID_MESSAGE))
        #ci(wdr.ID_MODNAME).SetLabel(Env.MODVERSION_NAME or 'head')
        #ver = Env.__version__
        #if Env.MODVERSION_NAME:
            #ver += ' - %s' % Env.__modversion__
        #ci(wdr.ID_VERACT).SetLabel(ver)
        ci(wdr.ID_MESSAGE).SetLabel("Premi 'Verifica' per cercare gli aggiornamenti su internet.")
        #ci(wdr.ID_INFO).Show(False)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnAction, id=wdr.ID_ACTION)
        #self.Bind(wx.EVT_BUTTON, self.OnInfo, id=wdr.ID_INFO)
    
    def OnInfo(self, event):
        self.HttpInfo()
        event.Skip()
    
    def OnAction(self, event):
        ci = lambda x: self.FindWindowById(x)
        but, msg = self.action, self.message
        setmsg = lambda x: msg.SetLabel(x)
        setbut = lambda x: but.SetLabel(x)
        if self.mode == MODE_VERIFY:
            self.HttpQuery()
        elif self.mode == MODE_UPDATE:
            self.HttpDownload()
            self.InstallUpdates()
            event.Skip()
        elif self.mode == MODE_DOWNLOAD:
            if msgbox(self, message='Interrompo il download?',
                      style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                self.download = False
                self.SetStop("Download interrotto")
        elif self.mode == MODE_CLOSE:
            event.Skip()
    
    def SetStop(self, msg):
        for cid, label in ((wdr.ID_MESSAGE, msg),
                           (wdr.ID_ACTION,  "Chiudi")):
            self.FindWindowById(cid).SetLabel(label)
            self.FindWindowById(wdr.ID_CANCEL).Show(False)
            self.Layout()
        self.mode = MODE_CLOSE
    
    def HttpQuery(self):
        but, msg = self.action, self.message
        setmsg = lambda x: msg.SetLabel(x)
        setbut = lambda x: but.SetLabel(x)
        ci = lambda x: self.FindWindowById(x)
        setmsg("Verifica aggiornamenti in corso...")
        setbut("Interrompi")
        try:
            self.downloads = self.dbver.CheckUpdates()
            self.gridver.Refresh()
            if self.downloads:
                setmsg("E' disponibile una nuova versione!")
                setbut("Download")
                self.Layout()
                self.mode = MODE_UPDATE
                self.gridver.SetFocus()
            else:
                self.SetStop("Non ci sono aggiornamenti rispetto alla versione in uso.")
        except Exception, e:
            msgbox(self, message=repr(e.args))
            self.SetStop("Download annullato")
    
    def GetDownloadPath(self):
        path = Env.Azienda.config.Updates_folder.replace('\\', '/')
        if path[-1] != '/': path += '/'
        if not os.path.isdir(path):
            try:
                os.mkdir(path)
            except OSError, e:
                aw.awu.MsgDialog(self, "Impossibile creare la cartella per il download dei files:\n%s\n%s" % (path, repr(e.args)))
        return path
    
    def GetTemporaryPath(self):
        return self.GetDownloadPath()+'temp/'
        
    def HttpDownload(self):
        ci = lambda x: self.FindWindowById(x)
        but, msg = self.action, self.message
        setmsg = lambda x: msg.SetLabel(x)
        setbut = lambda x: but.SetLabel(x)
        dlpath = self.GetDownloadPath()
        err = None
        if not dlpath:
            err = "Specificare il percorso dove scaricare gli aggiornamenti"
        elif not os.path.isdir(dlpath):
            err = "Il percorso indicato per il download degli aggiornamenti non esiste\n(%s)" % dlpath
        else:
            tmpath = self.GetTemporaryPath()
            if not os.path.isdir(tmpath):
                try:
                    os.mkdir(tmpath)
                except OSError, e:
                    err = "Impossibile creare la cartella per i file temporanei:\n%s\n%s" % (tmpath, repr(e.args))
        if err:
            msgbox(self, message=err, style=wx.ICON_ERROR)
            self.SetStop("Download annullato")
            return
        setmsg("Download in corso...")
        setbut("Interrompi")
        ci(wdr.ID_CANCEL).Show(False)
        #ci(wdr.ID_INFO).Show(False)
        self.Layout()
        self.mode = MODE_DOWNLOAD
        pro, byt = map(ci, (wdr.ID_PROGRESS, wdr.ID_BYTES))
        err = None
        for dlurl, dltype in self.downloads:
            n = dlurl.rindex('/')
            server = dlurl[:n]
            dlfile = dlurl[n+1:]
            if not server.endswith('/updates'):
                server += '/updates'
            if tmpath.endswith('/'):
                tmpath = tmpath[:-1]
            pro.SetRange(100)
            try:
                nametemp = '%s/%s.tmp' % (tmpath, dlfile)
                filetemp = open(nametemp, 'wb')
                stream = urlopen(dlurl)
                filesize = int(stream.headers['content-length'])
                bytes = 0
                self.download = True
                while self.download:
                    data = stream.read(BUFSIZE)
                    if data:
                        filetemp.write(data)
                        bytes += len(data)
                    else:
                        break
                    pro.SetValue(bytes*1.0/filesize*100)
                    byt.SetLabel('%s/%s (%d%%)' % (SizeRepr(bytes),
                                                   SizeRepr(filesize),
                                                   bytes*1.0/filesize*100))
                    wx.SafeYield(onlyIfNeeded=True)
                stream.close()
                filetemp.seek(0,2)
                wrisize = filetemp.tell()
                filetemp.close()
                if not self.download:
                    raise Exception, 'Interruzione manuale'
                if wrisize != filesize:
                    raise Exception, 'Dimensione errata'
                nameexe = '%s/%s' % (dlpath, dlfile)
                if os.path.isfile(nameexe):
                    os.remove(nameexe)
                os.rename(nametemp, nameexe)
                if dltype == 'H':
                    self.runexe = nameexe
            except urllib2.HTTPError, e:
                err = e.info
                break
            except Exception, e:
                err = repr(e.args)
                break
        if err:
            msgbox(self, message='Download non riuscito\n(%s)' % err,
                   style=wx.ICON_ERROR)
            self.SetStop('Download non riuscito')
            del self.downloads[:]
        else:
            self.SetStop('Download terminato')
        return
    
    def HttpInfo(self):
        dlpath = self.GetDownloadPath()
        tmpath = self.GetTemporaryPath()
        try:
            if not os.path.isdir(tmpath):
                try:
                    os.mkdir(tmpath)
                except Exception, e:
                    raise Exception, "Impossibile creare cartella file temporanei"
            dlfile = self.dlfile.replace('.exe', '-changes.txt')
            url = '%s/%s' % (self.dlurl, dlfile)
            nametemp = '%s/%s.tmp' % (tmpath, dlfile)
            filetemp = open(nametemp, 'wb')
            stream = urlopen(url)
            filesize = int(stream.headers['content-length'])
            bytes = 0
            while True:
                data = stream.read(BUFSIZE)
                if data:
                    filetemp.write(data)
                    bytes += len(data)
                else:
                    break
            stream.close()
            filetemp = open(nametemp, 'r')
            #filetemp.seek(0,2)
            #wrisize = filetemp.tell()
            #filetemp.seek(0,0)
            info = filetemp.read()
            filetemp.close()
            nametxt = '%s/%s' % (dlpath, dlfile)
            if os.path.isfile(nametxt):
                os.remove(nametxt)
            os.rename(nametemp, nametxt)
            dlg = aw.Dialog(self, title="X4 :: Informazioni sull'aggiornamento")
            panel = aw.Panel(dlg)
            wdr.VersionInfoFunc(panel)
            txt = panel.FindWindowById(wdr.ID_VERINFO)
            txt.SetValue(info)
            txt.SetEditable(False)
            dlg.AddSizedPanel(panel)
            def OnQuit(event):
                dlg.EndModal(wx.ID_OK)
            dlg.Bind(wx.EVT_BUTTON, OnQuit, id=wdr.ID_OK)
            dlg.ShowModal()
            dlg.Destroy()
        except Exception, e:
            msgbox(self, message='Download non riuscito\n(%s)' % repr(e.args), 
                   style=wx.ICON_ERROR)
            return
    
    def InstallUpdates(self):
        path = Env.Azienda.config.Updates_folder
        if not path:
            return
        if not path.endswith('/'):
            path += '/'
        wx.GetApp().InstallUpdatedZipFiles(path, request=False)
        if self.runexe:
            #installato head, lancio setup scaricato
            if msgbox(self, message=\
                      """Il setup della nuova versione è stato scaricato e """\
                      """pronto all'uso. Vuoi eseguire l'aggiornamento ora ?""",
                      style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                os.execl(self.runexe)
        #msgbox(self, message=\
               #"""Riavviare il programma per rendere effettive le modifiche""",
               #style=wx.ICON_INFORMATION)
        msgbox(None, 
               "Il programma verrà riavviato per rendere effettive le modifiche",
               style=wx.ICON_INFORMATION)
        os.execl(sys.argv[0])


# ------------------------------------------------------------------------------


class ProgramUpdateDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Aggiornamenti'
        kwargs['style'] = wx.SIMPLE_BORDER#BORDER_RAISED
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = ProgramUpdatePanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_ACTION)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=wdr.ID_CANCEL)
        self.CenterOnScreen()
    
    def OnQuit(self, event):
        self.EndModal(wx.ID_CANCEL)
    
    def OnClose(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class ProgramUpdatesSetupPanel(ConfigPanel):
    """
    Impostazione setup aggiornamenti
    """
    
    def __init__(self, *args, **kwargs):
        
        ConfigPanel.__init__(self, *args, **kwargs)
        wdr.ProgramUpdateSetupFunc(self)
        self.Bind(wx.EVT_BUTTON, self.OnConnTest, id=wdr.ID_BTNTEST)
        self.Bind(wx.EVT_BUTTON, self.OnPathFind, id=wdr.ID_BTNFIND)
        self.Bind(wx.EVT_BUTTON, self.OnSave,     id=wdr.ID_BTNOK)
    
    def setConfig(self, *args, **kwargs):
        ConfigPanel.setConfig(self, *args, **kwargs)
        def cn(x):
            return self.FindWindowByName(x)
        up = cn('Updates_folder')
        if ':' in up.GetValue():
            up.SetValue('')
    
    def OnConnTest(self, event):
        msg = None
        icon = wx.ICON_ERROR
        cnv = lambda x: self.FindWindowByName('Updates_%s' % x).GetValue()
        server = cnv('url')
        if not server.startswith('http://'):
            msg = 'Indirizzo non valido'
        else:
            url = '%s/updates/serverinfo.php' % server
            try:
                h = urlopen(url, user=cnv('user'), pswd=cnv('pswd'))
                srvinfo = h.read()
                h.close()
                tag = ':serverinfo:'
                if srvinfo.startswith(tag):
                    srvinfo = srvinfo.replace(tag, '')
                    msg = 'Connessione riuscita al %s' % srvinfo
                    icon = wx.ICON_INFORMATION
                else:
                    msg = 'Risposta non riconosciuta dal server'
            except IOError, e:
                if hasattr(e, 'code'):
                    if e.code == 401:
                        msg = 'Username o password errati'
                    else:
                        msg = 'Problema durante la connessione al server\n(%s:%s)'\
                        % (e.code, e.msg)
                else:
                    msg = 'Indirizzo non trovato'
        if msg:
            msgbox(self, message=msg, style=icon|wx.OK)
        event.Skip()
    
    def OnPathFind(self, event):
        dlg = wx.DirDialog(self, "Seleziona la cartella dove mettere gli aggiornamenti scaricati:",
                          style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            self.FindWindowByName('Updates_folder').SetValue(dlg.GetPath())
        dlg.Destroy()
        event.Skip()


# ------------------------------------------------------------------------------


class ProgramUpdateSetupDialog(ConfigDialog):
    """
    Dialog impostazione setup aggiornamenti
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Setup postazione"
        ConfigDialog.__init__(self, *args, **kwargs)
        self.panel = ProgramUpdatesSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=wdr.ID_BTNQUIT)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = ProgramUpdateDialog()
    win.ShowModal()
    win.Destroy()
    return win

if __name__ == '__main__':
    import sys,os
    import runtest
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
