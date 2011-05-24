#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/stati.py
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
import cfg.stati_wdr as wdr

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb
import cfg.dbtables as dbx

import report as rpt

import wx.grid as gl
import awc.controls.dbgrid as dbglib


FRAME_TITLE = "Stati"


class StatiSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        cn = lambda x: self.db._GetFieldIndex(x)
        return (( 50, (cn('stati_codice'),         "Cod.",        _STR, True)),
                (300, (cn('stati_descriz'),        "Descrizione", _STR, True)),
                (200, (cn('stati_desceng'),        "Description", _STR, True)),
                ( 50, (cn('stati_is_cee'),         "CEE",         _CHK, True)),
                ( 50, (cn('stati_is_blacklisted'), "B.L.",        _CHK, True)),
                (  1, (cn('stati_id'),             "#stt",        _STR, True)),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class StatiPanel(ga.AnagPanel):
    """
    Gestione tabella Stati.
    """
    def __init__(self, *args, **kwargs):
        
        ga.AnagPanel.__init__(self, *args, **kwargs)
        
        self.db_schema = 'x4.'
        self.db_tabname = 'stati'
        self.db_tabdesc = "Stati"
        self.db_columns =\
            [ [ "id",             "INT",       6, None, "ID Destinatario", "AUTO_INCREMENT" ],
              [ "codice",         "CHAR",     10, None, "Codice/Sigla Stato", None ],
              [ "vatprefix",      "CHAR",     10, None, "Prefisso VAT Numbers", None ],
              [ "descriz",        "VARCHAR",  60, None, "Descrizione", None ],
              [ "desceng",        "VARCHAR",  60, None, "Descrizione in inglese", None ],
              [ "is_cee",         "TINYINT",   1, None, "Flag CEE", None ],
              [ "is_blacklisted", "TINYINT",   1, None, "Flag Blacklist", None ],
          ]
        self.SetDbOrderColumns((("Codice",      ('stati.codice',)),
                                ("Descrizione", ('stati.descriz',)),))
        self.db_tabconstr = ()
        self.db_searchfilter = ""
        
        self.db_report = "Elenco Stati"
        
        self.HelpBuilder_SetDir('cfg.stati')

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.StatiFunc(p, True)
        return p
    
    def GetSearchResultsGrid(self, parent):
        grid = StatiSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                      self.db_tabname, self.GetSqlColumns())
        return grid
    
    def GetDbPrint(self):
        return dbx.StatiTable()


# ------------------------------------------------------------------------------


class StatiFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Stati.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(StatiPanel(self, -1))


# ------------------------------------------------------------------------------


class StatiDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Stati.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(StatiPanel(self, -1))
    
    def EndModal(self, x):
        ga._AnagDialog.EndModal(self, x)
