#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         sync.py
# Author:       gio
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

import sys
import awc.controls.linktable as linktab
import awc
import awc.controls.windows as aw
from awc.util import MsgDialog, MsgDialogDbError, DictNamedChildrens
from awc.tables.util import CheckRefIntegrity
#import awc.controls.dbgrid as dbglib
#import contab.pcf_wdr as wdr
#
#import stormdb as adb

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib
from   awc.controls.dbgrid import ADB_Grid

import awc.layout.gestanag as ga

import sync_wdr as wdr

import awc.util as util

from Env import Azienda
bt = Azienda.BaseTab
import manager
import time
import os

FRAME_TITLE = "Acquisizione Dati"

# ------------------------------------------------------------------------------


class SyncPanel(aw.Panel):
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.SyncFunc(self)

class SyncDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        try:
            self.SyncManager=kwargs.pop('manager')
        except:
            self.SyncManager=manager.SyncManager()
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = SyncPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.btnExport = self.FindWindowByName('btnExport')
        self.log=self.FindWindowByName('loglist')
        self.btnExport.Bind(wx.EVT_BUTTON, self.OnExport)
        wx.CallAfter(lambda: self.UpdateTables())
        self.btnExport.Hide()

    def OnExport(self, evt):
        
        for i in range(self.log.GetCount()):
            print i, self.log.GetString(i)
        self.Close()
        evt.Skip()

    def UpdateTables(self):
        lOk=True
        lUpdated=False
        lastUpdate=self.SyncManager.GetLastSyncDirName()
        dirUpdate=self.SyncManager.GetUpdatePath()
        #TODO: ORDINARE CRONLOGICAMENTE LE DIRECTORY
        dirList=sorted(os.listdir(dirUpdate))
        for d in dirList:
            if not hasattr(self.SyncManager, 'logger'):
                self.SyncManager.SetLogger()
            if d > lastUpdate:
                lUpdated=True
                lEsito, msg = self.SyncManager.UpdateFromXml(d)
                self.AddMessage(msg)
                if not lEsito:
                    self.SyncManager.logger.error('%s -  %s'% (d, 'AGGIORNAMENTO INTERROTTO'))
                    lOk=False
                    break
        if lUpdated:
            self.SyncManager.logger.info('')
        if lOk:
            self.Close()
        else:
            self.btnExport.Show()

    def AddMessage(self, msg):
        self.log.Append(msg)
        self.log.Refresh()
        try:
            wx.Yield()
        except:
            pass


