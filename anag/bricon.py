#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         anag/bricon.py
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
import anag.bilcon_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab


import anag.dbtables as dba
adb = dba.adb

import report as rpt

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import anag.bilcon as bilcon


FRAME_TITLE = "Conti Bilancio Riclassificato"


class BriConSearchResultsGrid(bilcon.BilConSearchResultsGrid):
    
    def __init__(self, *args, **kwargs):
        bilcon.BilConSearchResultsGrid.__init__(self, *args, **kwargs)
        self.tabalias = 'bricon'
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 35, (cn('brimas_codice'),  "Cod.",   _STR, True)),
                (240, (cn('brimas_descriz'), "Mastro", _STR, True)),
                ( 35, (cn('bricon_codice'),  "Cod.",   _STR, True)),
                (240, (cn('bricon_descriz'), "Conto",  _STR, True)),
                (  1, (cn('brimas_id'),      "#mas",   _STR, True )),
                (  1, (cn('bricon_id'),      "#con",   _STR, True )),
            )


# ------------------------------------------------------------------------------


class BriConPanel(bilcon.BilConPanel):
    """
    Gestione tabella Conti di bilancio.
    """
    def __init__(self, *args, **kwargs):
        bilcon.BilConPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_BRICON ] )
        self.SetDbOrderColumns((
            #ordinamento bilancio: sezione,cod.mastro,cod.conto,sottoconto
            #sottoconto x descrizione se cli/for, altrimenti codice
            ("Bilancio",    ('IF(brimas.tipo="P",0,IF(brimas.tipo="E",1,IF(brimas.tipo="O",2,3)))', 
                             'brimas.codice',
                             'bricon.codice')),
            ("Codice",      ('bricon.codice',)),
            ("Descrizione", ('bricon.descriz',)),
        ))
        self._sqlrelcol = ", brimas.tipo, brimas.id, brimas.codice, brimas.descriz"
        self._sqlrelfrm =\
            " INNER JOIN %s AS brimas ON %s.id_bilmas=brimas.id"\
            % ( bt.TABNAME_BRIMAS, bt.TABNAME_BRICON )
        self.db_tabprefix = "%s." % bt.TABNAME_BRICON
        
        self.db_report = "Conti Bilancio Riclassificato"
    
    def GetSearchResultsGrid(self, parent):
        grid = BriConSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid
    
    def InitAnagCard(self, parent):
        p = wx.Panel(parent, -1)
        wdr.BriConCardFunc(p, True)
        return p
    
    def GetDbPrint(self):
        db = dba.TabContiRicl()
        db.bilmas = db.brimas
        return db


# ------------------------------------------------------------------------------


class BriConFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Conti di bilancio.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BriConPanel(self, -1))


# ------------------------------------------------------------------------------


class BriConDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Conti di bilancio.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(BriConPanel(self, -1))
