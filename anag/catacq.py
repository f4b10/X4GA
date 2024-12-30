#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/catfor.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
# Copyright:    (C) 2011 Astra S.r.l. Via Serena 23 18012 Bordighera (IM)
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
import anag.catacq_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab


FRAME_TITLE = "Categorie Acquisti fornitori"


class CatAcqPanel(ga.AnagPanel):
    """
    Gestione tabella Categorie Acquisti fornitori.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_CATACQ ] )
        self.db_report = "Categorie acquisti"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.CatAcqCardFunc( p, True )
        return p


# ------------------------------------------------------------------------------


class CatAcqFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Categorie fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(CatAcqPanel(self, -1))


# ---------------------------------------------------------------------------


class CatAcqDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Categorie fornitori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(CatAcqPanel(self, -1))


# ---------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = CatAcqDialog()
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
