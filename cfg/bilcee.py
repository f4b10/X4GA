#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/bilcee.py
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
import cfg.bilcee_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab

import stormdb as adb
import cfg.dbtables as dbx

import report as rpt

import wx.grid as gl
import awc.controls.dbgrid as dbglib


FRAME_TITLE = "Bilancio CEE"


class BilCeeSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 30, (cn('bilcee_sezione'),    "Sez",         _STR, True)),
                ( 30, (cn('bilcee_voce'),       "Voce",        _STR, True)),
                ( 30, (cn('bilcee_capitolo'),   "Cap.",        _STR, True)),
                ( 30, (cn('bilcee_dettaglio'),  "Dett.",       _STR, True)),
                ( 30, (cn('bilcee_subdett'),    "Sub",         _STR, True)),
                (300, (cn('bilcee_descriz'),    "Descrizione", _STR, True)),
                ( 30, (cn('bilcee_selectable'), "Selez",       _CHK, True)),
                (  1, (cn('bilcee_id'),         "#cee",        _STR, True)),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(5)


# ------------------------------------------------------------------------------


class BilCeePanel(ga.AnagPanel):
    """
    Gestione tabella Bilancio CEE.
    """
    def __init__(self, *args, **kwargs):
        
        ga.AnagPanel.__init__(self, *args, **kwargs)
        
        self.db_schema = 'x4.'
        self.db_tabname = 'bilcee'
        self.db_tabdesc = "Tabella Bilancio CEE"
        self.db_columns =\
            [ [ "id",         "INT",    6, None, "ID Destinatario", "AUTO_INCREMENT" ],
              [ "codice",     "CHAR",   9, None, "Codice", None ],
              [ "descriz",    "CHAR", 128, None, "Descrizione", None ],
              [ "sezione",    "CHAR",   1, None, "Sezione", None ],
              [ "voce",       "CHAR",   1, None, "Voce", None ],
              [ "capitolo",   "CHAR",   4, None, "Capitolo", None ],
              [ "dettaglio",  "CHAR",   2, None, "Dettaglio", None ],
              [ "subdett",    "CHAR",   1, None, "Sub-dettaglio", None ],
              [ "selectable", "CHAR",   1, None, "Sub-dettaglio", None ],
          ]
        self.SetDbOrderColumns((("Bilancio",      ('bilcee.sezione','bilcee.voce','bilcee.capitolo','bilcee.dettaglio','bilcee.subdett')),
                                ("Descrizione", ('bilcee.descriz',)),))
        self.db_tabconstr = ()
        self.db_searchfilter = ""
        
        self.db_report = "Struttura Bilancio CEE"
        
        self.HelpBuilder_SetDir('anag.pdccee.classif')

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.BilCeeCardFunc(p, True)
        cn = self.FindWindowByName
        cn('codice').SetEditable(False)
        for name in 'sezione voce capitolo dettaglio subdett'.split():
            self.Bind(wx.EVT_TEXT, self.OnDatiCeeChanged, cn(name))
        return p
    
    def OnDatiCeeChanged(self, event):
        cn = self.FindWindowByName
        def cnv(x):
            return cn(x).GetValue()
        def f(x,n):
            return str(x).ljust(n)
        cn('codice').SetValue(f(cnv('sezione'),   1)+
                              f(cnv('voce'),      1)+
                              f(cnv('capitolo'),  4)+
                              f(cnv('dettaglio'), 2)+
                              f(cnv('subdett'),   1))
        event.Skip()
    
    #def InitControls(self, *args, **kwargs):
        #ga.AnagPanel.InitControls(self, *args, **kwargs)
        #self.FindWindowById(wdr.ID_RADIOBIL).SetDataLink('tipo', 'PEO')
    
    #def GetSpecializedSearchPanel(self, parent):
        #p = wx.Panel(parent, -1)
        #wdr.BilMasSpecSearchFunc(p)
        #p.FindWindowById(wdr.ID_FILT_PEO).SetDataLink('tipo', 'TPEO')
        #return p
    
    def GetSearchResultsGrid(self, parent):
        grid = BilCeeSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid
    
    def GetDbPrint(self):
        return dbx.BilancioCeeTable()


# ------------------------------------------------------------------------------


class BilCeeFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Bilancio CEE.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BilCeePanel(self, -1))


# ------------------------------------------------------------------------------


class BilCeeDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Bilancio CEE.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BilCeePanel(self, -1))
