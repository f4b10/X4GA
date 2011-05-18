#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         anag/banche.py
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

from anag import pdcrel

from anag.pdcrel_wdr import *

from awc.util import MsgDialog

from Env import Azienda
bt = Azienda.BaseTab


FRAME_TITLE = "Banche"


class BanchePanel(pdcrel._PdcRelPanel):
    """
    Gestione della tabella banche.
    """
    def __init__(self, *args, **kwargs):
        
        self.pdctipo = "B"
        self.tabanag = Azienda.BaseTab.TABNAME_BANCHE
        pdcrel._PdcRelPanel.__init__(self, *args, **kwargs)
        
        self.anag_db_columns = [ c for c in Azienda.BaseTab.tabelle\
                                 [bt.TABSETUP_TABLE_BANCHE]\
                                 [bt.TABSETUP_TABLESTRUCTURE] ]
        
        self._Auto_AddKeys( { "pdctip_banche": True,
                              "bilmas_banche": True,
                              "bilcon_banche": True,
                              "bilcee_banche": bt.CONBILRCEE == 1, } )
        self.ReadAutomat()
        self._auto_pdctip = getattr(self, "_auto_pdctip_banche", None)
        self._auto_bilmas = getattr(self, "_auto_bilmas_banche", None)
        self._auto_bilcon = getattr(self, "_auto_bilcon_banche", None)
        self._auto_bilcee = getattr(self, "_auto_bilcee_banche", None)
        
        self.db_report = "Banche"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        BancheCardFunc( p, True )
        return p
    
    def GetLinkTableClass(self):
        import anag.lib as alib
        return alib.LinkTableBanca


# ------------------------------------------------------------------------------


class BancheFrame(pdcrel.ga._AnagFrame):
    """
    Frame Gestione tabella Banche.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BanchePanel(self, -1))


# ------------------------------------------------------------------------------


class BancheDialog(pdcrel.ga._AnagDialog):
    """
    Dialog Gestione tabella Banche.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BanchePanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = BancheDialog()
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
