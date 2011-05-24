#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/trasp.py
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
import anag.trasp_wdr as wdr

from awc.util import MsgDialog

from awc.controls.linktable import EVT_LINKTABCHANGED

from Env import Azienda
bt = Azienda.BaseTab


FRAME_TITLECAU = "Causali trasporto"


class TraCauPanel(ga.AnagPanel):
    """
    Gestione tabella Causali di trasporto.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_TRACAU ] )
        self.db_report = "Causali di Trasporto"

    def InitControls(self, *args, **kwargs):
        ga.AnagPanel.InitControls(self, *args, **kwargs)
        name = 'esclftd'
        self.FindWindowByName(name).SetDataLink(name, {True: 1, False: 0})
    
    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TraCauCardFunc( p, True )
        return p


# ------------------------------------------------------------------------------


class TraCauFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Causali trasporto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECAU
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraCauPanel(self, -1))


# ------------------------------------------------------------------------------


class TraCauDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Causali trasporto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECAU
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraCauPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLECUR = "Trasporto a cura"


class TraCurPanel(ga.AnagPanel):
    """
    Gestione tabella Trasporto a cura.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_TRACUR ] )
        self.db_report = "Cura Trasporto"

    def InitControls(self, *args, **kwargs):
        ga.AnagPanel.InitControls(self, *args, **kwargs)
        name = "askvet"
        self.FindWindowByName(name).SetDataLink(name, {True: 1, False: 0})
    
    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TraCurCardFunc( p, True )
        return p


# ------------------------------------------------------------------------------


class TraCurFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Trasporto a cura.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECUR
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraCurPanel(self, -1))


# ------------------------------------------------------------------------------


class TraCurDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Trasporto a cura.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECUR
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraCurPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLEASP = "Aspetto esteriore beni"


class TraAspPanel(ga.AnagPanel):
    """
    Gestione tabella Aspetto esteriore dei beni.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_TRAASP ] )
        self.db_report = "Tipi di Aspetto esteriore dei beni"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TraAspCardFunc( p, True )
        return p


# ------------------------------------------------------------------------------


class TraAspFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Aspetto esteriore beni.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEASP
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraAspPanel(self, -1))


# ------------------------------------------------------------------------------


class TraAspDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Aspetto esteriore beni.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEASP
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraAspPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLEPOR = "Porto"


class TraPorPanel(ga.AnagPanel):
    """
    Gestione tabella Porto.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_TRAPOR ] )
        self.db_report = "Tipi di Porto"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TraPorCardFunc( p, True )
        return p


# ---------------------------------------------------------------------------


class TraPorFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Porto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEPOR
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraPorPanel(self, -1))


# ------------------------------------------------------------------------------


class TraPorDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Porto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEPOR
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraPorPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLECON = "Tipi incasso contrassegno"


class TraConPanel(ga.AnagPanel):
    """
    Gestione tabella Tipi incasso contrassegno.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_TRACON ] )
        self.db_report = "Tipi di Incasso Contrassegno"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TraConCardFunc( p, True )
        return p


# ------------------------------------------------------------------------------


class TraConFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Tipi incasso contrassegno.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECON
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraConPanel(self, -1))


# ------------------------------------------------------------------------------


class TraConDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Tipi incasso contrassegno.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLECON
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraConPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLEVET = "Vettori"


class TraVetPanel(ga.AnagPanel):
    """
    Gestione tabella Vettori.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_TRAVET ] )
        self.db_report = "Vettori"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.TraVetCardFunc( p, True )
        cn = self.FindWindowByName
        cn('piva').SetStateControl(cn('nazione'))
        self.Bind(EVT_LINKTABCHANGED, self.OnStatoChanged, cn('id_stato'))
        return p
    
    def OnStatoChanged(self, event):
        cn = self.FindWindowByName
        cn('nazione').SetValue(cn('id_stato').GetVatPrefix())


# ------------------------------------------------------------------------------


class TraVetFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Vettori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEVET
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraVetPanel(self, -1))


# ------------------------------------------------------------------------------


class TraVetDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Vettori.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLEVET
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(TraVetPanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    for x in ("Cau", "Cur", "Asp", "Por", "Con", "Vet"):
        cls = eval("Tra%sDialog" % x)
        win = cls()
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
