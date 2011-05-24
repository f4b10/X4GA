#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/tiplist.py
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

import awc.layout.gestanag as ga
import anag.tiplist_wdr as wdr

import awc.util as util

from Env import Azienda
bt = Azienda.BaseTab

import anag.dbtables as dba
adb = dba.adb

import report as rpt


FRAME_TITLE = "Tipi di Listino"


class TipListPanel(ga.AnagPanel):
    """
    Gestione tabella Tipi di listino.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_TIPLIST ] )
        self.db_report = "Tipi di Listino"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TipListCardFunc( p, True )
        name = "tipoprezzo"
        ctr = self.FindWindowByName(name)
        ctr.SetDataLink(name, "123456789")
        return p
    
    def GetDbPrint(self):
        return dba.TipoListino()


# ------------------------------------------------------------------------------


class TipListFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Tipi di listino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TipListPanel(self, -1))


# ------------------------------------------------------------------------------


class TipListDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Tipi di listino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TipListPanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = TipListDialog()
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
