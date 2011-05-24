#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/brimas.py
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
import anag.bilmas_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab

import anag.dbtables as dba
adb = dba.adb

import report as rpt

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import anag.bilmas as bilmas


FRAME_TITLE = "Mastri bilancio riclassificato"


class _BilMasPanel(ga.AnagPanel):
    
    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.BilMasCardFunc( p, True )
        return p
    
    #def InitAnagCard(self, parent):
        #p = wx.Panel( parent, -1)
        #wdr.BilMasCardFunc( p, True )
        #return p
    
    def InitControls(self, *args, **kwargs):
        ga.AnagPanel.InitControls(self, *args, **kwargs)
        self.FindWindowById(wdr.ID_RADIOBIL).SetDataLink('tipo', 'PEO')
    
    def GetSpecializedSearchPanel(self, parent):
        p = wx.Panel(parent, -1)
        wdr.BilMasSpecSearchFunc(p)
        p.FindWindowById(wdr.ID_FILT_PEO).SetDataLink('tipo', 'TPEO')
        return p


# ------------------------------------------------------------------------------


class BilMasSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 30, (cn('bilmas_tipo'),    "Tipo",   _STR, True )),
                ( 35, (cn('bilmas_codice'),  "Cod.",   _STR, True )),
                (120, (cn('bilmas_descriz'), "Mastro", _STR, True )),
                (  1, (cn('bilmas_id'),      "#mas",   _STR, True )),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(2)


# ------------------------------------------------------------------------------


class BilMasPanel(_BilMasPanel):
    """
    Gestione tabella Mastri di bilancio.
    """
    def __init__(self, *args, **kwargs):
        
        _BilMasPanel.__init__(self, *args, **kwargs)
        
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_BILMAS ] )
        self.SetDbOrderColumns((
            #ordinamento bilancio: sezione,cod.mastro,cod.conto,sottoconto
            #sottoconto x descrizione se cli/for, altrimenti codice
            ("Bilancio",    ('IF(bilmas.tipo="P",0,IF(bilmas.tipo="E",1,IF(bilmas.tipo="O",2,3)))', 
                             'bilmas.codice')),
            ("Codice",      ('bilmas.codice',)),
            ("Descrizione", ('bilmas.descriz',)),
        ))
        
        self._valfilters['tipo'] = ['bilmas.tipo', 'T', None]
        self._nulfilters['tipo'] = ['T']
        self._hasfilters = True
        
        self.db_report = "Mastri di Bilancio"

    def GetSearchResultsGrid(self, parent):
        grid = BilMasSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid


# ------------------------------------------------------------------------------


class BilMasFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Mastri di bilancio.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BilMasPanel(self, -1))


# ------------------------------------------------------------------------------


class BilMasDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Mastri di bilancio.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BilMasPanel(self, -1))


# ------------------------------------------------------------------------------


class BriMasSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 30, (cn('brimas_tipo'),    "Tipo",   _STR, True )),
                ( 35, (cn('brimas_codice'),  "Cod.",   _STR, True )),
                (120, (cn('brimas_descriz'), "Mastro", _STR, True )),
                (  1, (cn('brimas_id'),      "#mas",   _STR, True )),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(2)


# ------------------------------------------------------------------------------


class BriMasPanel(_BilMasPanel):
    """
    Gestione tabella Mastri bilancio riclassificato.
    """
    def __init__(self, *args, **kwargs):
        
        _BilMasPanel.__init__(self, *args, **kwargs)
        
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_BRIMAS ] )
        self.SetDbOrderColumns((
            #ordinamento bilancio: sezione,cod.mastro,cod.conto,sottoconto
            #sottoconto x descrizione se cli/for, altrimenti codice
            ("Bilancio",    ('IF(brimas.tipo="P",0,IF(brimas.tipo="E",1,IF(brimas.tipo="O",2,3)))', 
                             'brimas.codice')),
            ("Codice",      ('brimas.codice',)),
            ("Descrizione", ('brimas.descriz',)),
        ))
        
        self._valfilters['tipo'] = ['brimas.tipo', 'T', None]
        self._nulfilters['tipo'] = ['T']
        self._hasfilters = True
        
        self.db_report = "Mastri Bilancio Riclassificato"

    def GetSearchResultsGrid(self, parent):
        grid = BriMasSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid
    
    def GetDbPrint(self):
        return dba.TabMastriRicl()


# ------------------------------------------------------------------------------


class BriMasFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Mastri bilancio riclassificato.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BriMasPanel(self, -1))


# ------------------------------------------------------------------------------


class BriMasDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Mastri bilancio riclassificato.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BriMasPanel(self, -1))
