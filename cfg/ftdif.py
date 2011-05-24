#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/ftdif.py
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

import MySQLdb
import stormdb as adb

import awc.layout.gestanag as ga
import cfg.ftdif_wdr as wdr

import awc.util as awu

from Env import Azienda
bt = Azienda.BaseTab

import lib


FRAME_TITLE = "Fatturazione differita"


class FtDifPanel(ga.AnagPanel):
    """
    Pannello impostazione fatturazione differita
    """
    
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_CFGFTDIF ] )
        self.dbddr = adb.DbTable(bt.TABNAME_CFGFTDDR, "ddr", writable=True)
        self.docs = []

    def InitAnagCard(self, parent):
        ci = lambda x: self.FindWindowById(x)
        p = wx.Panel( parent, -1)
        wdr.FtDifCardFunc( p, True )
        self.FindWindowByName('descriz').ForceUpperCase(False)
        for cbi, name in ((wdr.ID_SEPALL,   'f_sepall'),
                          (wdr.ID_SEPMP,    'f_sepmp'),
                          (wdr.ID_SEPDEST,  'f_sepdest'),
                          (wdr.ID_SOLOSTA,  'f_solosta'),
                          (wdr.ID_SETACQ,   'f_setacq'),
                          (wdr.ID_SETANN,   'f_setann'),
                          (wdr.ID_SETGEN,   'f_setgen'),
                          (wdr.ID_NODESRIF, 'f_nodesrif'),):
            ci(cbi).SetDataLink(name, {True: 1, False: 0})
        ci(wdr.ID_F_CHGMAG).SetDataLink(values=[0,1])
        docs = adb.DbTable(bt.TABNAME_CFGMAGDOC, writable=False)
        docs.AddOrder('descriz')
        if docs.Retrieve():
            l = ci(wdr.ID_DOCS)
            for d in docs:
                l.Append(d.descriz)
                self.docs.append(d.id)
            self.Bind(wx.EVT_CHECKLISTBOX, self.OnDdrModif, l)
        self.Bind(wx.EVT_RADIOBOX, self.OnChgMag, ci(wdr.ID_F_CHGMAG))
        return p
    
    def OnDdrModif(self, event):
        self.SetDataChanged(True)
        event.Skip()
    
    def UpdateDataControls(self, *args, **kwargs):
        ga.AnagPanel.UpdateDataControls(self, *args, **kwargs)
        ddr = self.dbddr
        if self.db_recid is None:
            ddr.Reset()
        else:
            l = self.FindWindowById(wdr.ID_DOCS)
            for i in range(l.GetCount()):
                l.Check(i, False)
            ddr.ClearFilters()
            ddr.AddFilter('ddr.id_ftd=%s', self.db_recid)
            if ddr.Retrieve():
                for d in ddr:
                    if d.id_docrag in self.docs:
                        n = self.docs.index(d.id_docrag)
                        l.Check(n, d.f_attivo == 1)
        self.TestChgMag()
    
    def OnChgMag(self, event):
        self.TestChgMag()
        event.Skip()
    
    def TestChgMag(self):
        def ci(x):
            return self.FindWindowById(x)
        ci(wdr.ID_CHGMAG).Enable(ci(wdr.ID_F_CHGMAG).GetValue())
        
    def TransferDataFromWindow(self, *args, **kwargs):
        out = ga.AnagPanel.TransferDataFromWindow(self, *args, **kwargs)
        if out:
            ddr = self.dbddr
            l = self.FindWindowById(wdr.ID_DOCS)
            for r, d in enumerate(self.docs):
                ddr.ClearFilters()
                ddr.AddFilter('ddr.id_ftd=%s', self.db_recid)
                ddr.AddFilter('ddr.id_docrag=%s', d)
                if ddr.Retrieve():
                    if ddr.IsEmpty():
                        ddr.CreateNewRow()
                        ddr.id_ftd = self.db_recid
                        ddr.id_docrag = d
                    ddr.f_attivo = int(l.IsChecked(r))
                    if not ddr.Save():
                        awu.MsgDialog(self, repr(ddr.GetError()))
                        break
                else:
                    awu.MsgDialog(self, repr(ddr.GetError()))
            evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
            wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        return out
    

# ------------------------------------------------------------------------------


class FtDifFrame(ga._AnagFrame):
    """
    Frame impostazione fatturazione differita
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(FtDifPanel(self, -1))


# ------------------------------------------------------------------------------


class FtDifDialog(ga._AnagDialog):
    """
    Dialog impostazione fatturazione differita
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(FtDifPanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = FtDifDialog()
    win.Show()
    return win


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    import sys,os
    import runtest
    import stormdb as adb
    db = adb.DB()
    db.Connect()
    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
