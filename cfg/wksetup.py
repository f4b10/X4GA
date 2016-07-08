#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/wksetup.py
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

import wx
import Env
bt = Env.Azienda.BaseTab

import awc.controls.windows as aw

import cfg.wksetup_wdr as wdr
import os.path

import stormdb as adb
import lib


class ConfigPanel(aw.Panel):
    """
    Pannello di gestione file configurazione config.ini
    """
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.config = None
        self.hkeys = {}

    def setConfig(self, cfg):
        self.config = cfg
        self.Read()

    def Read(self):
        cfg = self.config
        for sec in cfg.sections():
            for opt in cfg.options(sec):
                self.SetValue(sec, opt, cfg.get(sec, opt))

    def getkey(self, sec, opt):
        return '%s_%s' % (sec, opt)

    def SetValue(self, sec, opt, val):
        key = self.getkey(sec, opt)
        ctr = self.FindWindowByName(key)
        if ctr:
            ctr.SetValue(val)
        else:
            self.hkeys[key] = val

    def GetValue(self, sec, opt):
        key = self.getkey(sec, opt)
        ctr = self.FindWindowByName(key)
        if ctr:
            out = ctr.GetValue()
        else:
            out = self.hkeys[key]
        return out

    def OnSave(self, event):
        if self.config:
            if self.Validate():
                self.Save()
                event.Skip()

    def Validate(self):
        #override
        return True

    def Save(self):
        cfg = self.config
        for sec in cfg.sections():
            for opt in cfg.options(sec):
                cfg.set(sec, opt, self.GetValue(sec, opt))
        cfg.write()
        cfg.read()


# ------------------------------------------------------------------------------


class ConfigDialog(aw.Dialog):

    def setConfig(self, *args):
        return self.panel.setConfig(*args)

    def OnQuit(self, event):
        self.EndModal(wx.ID_CANCEL)

    def OnSave(self, event):
        self.EndModal(wx.ID_OK)

    def SetValue(self, *args):
        return self.panel.SetValue(*args)

    def GetValue(self, *args):
        return self.panel.GetValue(*args)


# ------------------------------------------------------------------------------


class WorkstationSetupPanel(ConfigPanel):
    """
    Impostazione setup workstation: db, path, ecc.
    """
    def __init__(self, *args, **kwargs):

        ConfigPanel.__init__(self, *args, **kwargs)
        wdr.WorkstationSetup(self)

        self.lOldServer=[]
        self.lNewServer=[]

        cn = lambda x: self.FindWindowById(x)
        self.nbServer = cn(wdr.ID_NOTEBOOK_MYSQL)

        if (Env.Azienda.config<>None):
            cfg = Env.Azienda.config
            self.lHost = [e for e in cfg.sections() if e[:5] == "MySQL"]
            self.lHost.sort()
            for i, sec in enumerate(self.lHost):
                if i == 0:
                    item = self.nbServer
                else:
                    nTabName="Server"+sec[5:]
                    item = wx.Panel( self.nbServer, -1 )
                    item.SetName('MySQL_%d' % i)
                    wdr.DbMySql(item, False)
                    for e in ["desc", "host", "port", "user", "pswd"]:
                        x=item.FindWindowByName("MySQL_"+e)
                        x.SetName("MySQL" + str(i)+"_"+e)
                    self.nbServer.AddPage( item, nTabName)

        nPag=self.nbServer.GetPageCount()
        for i in range(nPag):
            if Env.Azienda.firstTime:
                self.lNewServer.append(self.nbServer.GetPageText(i))
            else:
                self.lOldServer.append(self.nbServer.GetPageText(i))

        for cid in (wdr.ID_CSVASGRID,
                    wdr.ID_SITEREMOTE,
                    wdr.ID_SQLSPY,
                    wdr.ID_SITEINETAO):
            c = cn(cid)
            c.SetDataLink(c.GetName(), {True: '1', False: '0'})
        cn(wdr.ID_TABGRID).SetDataLink('Controls_gridtabtraversal', '01')

        self.Bind(wx.EVT_CHECKBOX, self.OnCSVAsGrid, cn(wdr.ID_CSVASGRID))

        for cid, func in ((wdr.ID_CONNTEST,  self.OnConnTest),
                          (wdr.ID_ADDSERVER, self.OnAddServer),
                          (wdr.ID_BTNOK,     self.OnSave)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)

    def setConfig(self, *args, **kwargs):
        ConfigPanel.setConfig(self, *args, **kwargs)
        def cn(x):
            return self.FindWindowByName(x)
        sp = cn('Site_folder')
        p = (sp.GetValue() or '')
        if p.replace('\\','/') == Env.config_base_path.replace('\\','/'):
            sp.SetValue('')
        self.TestCSV()

    def OnCSVAsGrid(self, event):
        self.TestCSV()
        event.Skip()

    def TestCSV(self):
        cn = lambda x: self.FindWindowById(x)
        asgrid = int(cn(wdr.ID_CSVASGRID).GetValue())
        cn(wdr.ID_CSVSPEC).Enable(not asgrid)

    def OnConnTest(self, event):
        n = self.nbServer.GetSelection()
        self.ConnTest(n)
        event.Skip()

    def ConnTest(self, tabno, wait=None, messages=True):
        def FindWindow(name):
            l = [x for x in self.nbServer.GetChildren()[tabno].GetChildren()
                 if ('_%s' % name) in x.GetName()]
            if l:
                out = l[0]
            else:
                out = None
            return out
        host, port, user, pswd, = map(lambda x: FindWindow(x).GetValue(),
                                      ('host', 'port', 'user', 'pswd'))
        if not host or not port or not user or not pswd:
            if wait: wait.Hide()
            aw.awu.MsgDialog(self, 'Definire tutti i parametri')
            return False
        test = adb.DB(dbType='mysql', globalConnection=False)
        ok = test.Connect(host=host, user=user, passwd=pswd, db=None)#, db='x4')
        if ok:
            if test.Retrieve('SELECT VERSION()'):
                print test.rs[0][0]
            test.Close()
            msg = 'Connessione riuscita'
            icon = wx.ICON_INFORMATION
            out = True
        else:
            msg = 'Connessione fallita:\n%s' % test.dbError.description
            icon = wx.ICON_ERROR
            out = False
        if wait: wait.Hide()
        if messages or not out:
            aw.awu.MsgDialog(self, msg, style=icon)
        return out

    def OnSave(self, event):
        n = self.nbServer.GetPageCount()
        do = True
        for n in range(n):
            if not self.ConnTest(n, messages=False):
                do = False
                break
        if not do:
            return
        if self.config:
            cfg = self.config
            for newSec in self.lNewServer + self.lOldServer:
                newSec="MySQL"+newSec[6:]
                if not cfg.has_section(newSec):
                    cfg.add_section(newSec)
                for o in ["host", "port", "desc", "user", "pswd"]:
                    if not cfg.has_option(newSec, o):
                        cfg.set(newSec, o, "")
            baseDir=os.path.dirname(cfg.fileName)
            for sec in cfg.sections():
                for opt in cfg.options(sec):
                    val=self.GetValue(sec, opt)
                    cfg.set(sec, opt, val)
            cfg.write()
        Env.Azienda.config=cfg
        ConfigPanel.OnSave(self, event)

    def OnAddServer(self, event):
        nPag=1
        newPageName=("Server%s" % nPag)
        while ((newPageName in self.lNewServer) or (newPageName in self.lOldServer)):
            nPag=nPag+1
            newPageName=("Server%s" % nPag)
        item = wx.Panel( self.nbServer, -1 )

        wdr.DbMySql(item, False)
        for e in ["desc", "host", "port", "user", "pswd"]:
            x=item.FindWindowByName("MySQL_"+e)
            x.SetName("MySQL" + str(nPag)+"_"+e)
        self.nbServer.AddPage( item, newPageName)
        self.lNewServer.append(newPageName)
        #self.abilitaControlli()
        nPag=self.nbServer.GetPageCount()
        self.nbServer.SetSelection(nPag-1)
        event.Skip()

    def Save(self, *args, **kwargs):
        ConfigPanel.Save(self, *args, **kwargs)
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)


# ------------------------------------------------------------------------------


class WorkstationSetupDialog(ConfigDialog):
    """
    Dialog impostazione setup workstation
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Setup postazione"
        ConfigDialog.__init__(self, *args, **kwargs)
        self.panel = WorkstationSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=wdr.ID_BTNQUIT)
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
        self.CenterOnScreen()
