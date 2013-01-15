#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/regiva.py
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
import regiva_wdr as wdr

from awc.util import MsgDialog, MsgDialogDbError, ListSearch

from Env import Azienda

bt = Azienda.BaseTab

import wx.grid as gl
import awc.controls.dbgrid as dbglib


FRAME_TITLE = "Registri IVA"


class RegIvaSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 40, (cn('regiva_codice'),     "Cod.",       _STR, True)),
                (240, (cn('regiva_descriz'),    "Mastro",     _STR, True)),
                ( 40, (cn('regiva_tipo'),       "Tipo",       _STR, True)),
                ( 50, (cn('regiva_numdocsez'),  "/sez",       _STR, True)),
                ( 50, (cn('regiva_rieponly'),   "/anno",      _CHK, True)),
                (110, (cn('regiva_lastprtdat'), "Ult.Stampa", _DAT, True)),
                ( 80, (cn('regiva_lastprtnum'), "Ult.Prot.",  _NUM, True)),
                ( 60, (cn('regiva_intanno'),    "Anno St.",   _STR, True)),
                ( 60, (cn('regiva_intpag'),     "Pag.",       _NUM, True)),
                (  1, (cn('regiva_id'),         "#reg",       _STR, True)),
            )


# ------------------------------------------------------------------------------


class RegIvaPanel(ga.AnagPanel):
    """
    Gestione della tabella Registri IVA.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_REGIVA ] )
        self.db_report = "Registri IVA"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.RegIvaCardFunc( p, True )
        cn = self.FindWindowByName
        cn("tipo").SetDataLink("tipo", ["A",  #acquisti
                                        "V",  #vendite
                                        "C"]) #riepilogativo
        cn("rieponly").SetDataLink(values=(1,0))
        self.Bind(wx.EVT_RADIOBOX, self.OnRiepChanged, cn('rieponly'))
        self.Bind(wx.EVT_TEXT, self.OnNumDocTest, cn('numdocsez'))
        self.Bind(wx.EVT_CHECKBOX, self.OnNumDocTest, cn('numdocann'))
        return p
    
    def OnNumDocTest(self, event):
        self.NumDocTest()
        event.Skip()
    
    def NumDocTest(self):
        cn = self.FindWindowByName
        test = '12345'
        sez = cn('numdocsez').GetValue()
        if sez:
            test += ('/%s' % sez)
        if cn('numdocann').IsChecked():
            test += ('/%s' % Azienda.Login.dataElab.year)
        cn('_numdoctest').SetLabel(test)
        self.Layout()
    
    def OnRiepChanged(self, event):
        self.TestRiepilogat()
        event.Skip()
    
    def TestRiepilogat(self):
        cn = self.FindWindowByName
        ro = cn('rieponly').GetValue()
        for name in 'noprot lastprtnum lastprtdat'.split():
            cn(name).Enable(ro != 1)
    
    def UpdateDataControls(self, *args, **kwargs):
        ga.AnagPanel.UpdateDataControls(self, *args, **kwargs)
        self.TestRiepilogat()
        self.NumDocTest()
    
    def GetSearchResultsGrid(self, parent):
        grid = RegIvaSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid


# ---------------------------------------------------------------------------


class RegIvaFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Registri IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(RegIvaPanel(self, -1))


# ------------------------------------------------------------------------------


class RegIvaDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Registri IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(RegIvaPanel(self, -1))
