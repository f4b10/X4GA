#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         anag/gruprez.py
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
import anag.gruprez_wdr as wdr

import awc.util as util

from Env import Azienda
bt = Azienda.BaseTab

import anag.dbtables as dba
adb = dba.adb

import report as rpt

import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw


FRAME_TITLE = "Gruppi prezzi"


class GruPrezSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 35, (cn('gruprez_codice'),  "Cod.",                                _STR, True)),
                (350, (cn('gruprez_descriz'), "Gruppo prezzi",                       _STR, True)),
                ( 30, (cn('gruprez_calcpc'),  "P/C",                                 _STR, True)),
                ( 35, (cn('gplbase_codice'),  "Cod.",                                _STR, True)),
                (350, (cn('gplbase_descriz'), "Gruppo di riferimento per i listini", _STR, True)),
                (  1, (cn('gruprez_id'),      "#gpr",                                _STR, True )),
                (  1, (cn('gplbase_id'),      "#rif",                                _STR, True )),
            )                                         
    
    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class GruPrezPanel(ga.AnagPanel):
    """
    Gestione tabella Gruppi prezzi.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_GRUPREZ ] )
        self._sqlrelcol = ", gplbase.id, gplbase.codice, gplbase.descriz"
        self._sqlrelfrm =\
            " LEFT JOIN %s AS gplbase ON %s.id_lisdagp=gplbase.id"\
            % (bt.TABNAME_GRUPREZ, bt.TABNAME_GRUPREZ)
        self.db_tabprefix = "%s." % bt.TABNAME_GRUPREZ
        self.db_report = "Gruppi prezzi"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.GruPrezCardFunc( p, True )
        self.Bind(wx.EVT_RADIOBOX, self.OnTipoChanged, id=wdr.ID_TIPOCP)
        self.Bind(wx.EVT_RADIOBOX, self.OnTipoChanged, id=wdr.ID_TIPOLIS)
        from awc.controls.linktable import EVT_LINKTABCHANGED
        self.Bind(EVT_LINKTABCHANGED, self.OnLisGPChanged, 
                  self.FindWindowByName('id_lisdagp'))
        wx.CallAfter(self.TestTipoCalc)
        return p
    
    def OnLisGPChanged(self, event):
        self.TestTipoCalc()
        def SetFocus():
            def cn(x):
                return self.FindWindowByName(x)
            if cn('id_lisdagp').GetValue() is None:
                for name in 'prclisric1 prclissco1 prclisvar1'.split():
                    c = cn(name)
                    if c.IsEnabled():
                        c.SetFocus()
                        break
        wx.CallAfter(SetFocus)
        event.Skip()
    
    def GetSearchResultsGrid(self, parent):
        grid = GruPrezSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                        self.db_tabname, self.GetSqlColumns())
        return grid
    
    def OnTipoChanged(self, event):
        self.TestTipoCalc()
        event.Skip()
    
    def TestTipoCalc(self, obj=None):
        def cn(x):
            return self.FindWindowByName(x)
        es = {'calcpc':  {'P': ['prccosric'], 'C': ['prcpresco']},
              'calclis': {'C': ['prclisric'], 'P': ['prclissco'], 'V': ['prclisvar', 'prclisbas']}}
        ctrls = aw.awu.GetAllChildrens(self)
        f = None
        for e in es:
            v = cn(e).GetValue()
            for t in es[e]:
                for c in ctrls:
                    en = list(es[e][t])
                    for ex in en:
                        if c.GetName().startswith(ex):
                            x = t == v
                            if e == 'calclis' and t == 'V':
                                cn('id_lisdagp').Enable(x)

                                x = x and cn('id_lisdagp').GetValue() == None
                            c.Enable(x)
                            if x and f is None:
                                if obj:
                                    if obj.GetName() == e:
                                        f = c
        if f:
            wx.CallAfter(f.SetFocus)
    
    def UpdateDataControls(self, *args, **kwargs):
        out = ga.AnagPanel.UpdateDataControls(self, *args, **kwargs)
        self.TestTipoCalc()
        return out


# ------------------------------------------------------------------------------


class GruPrezFrame(ga._AnagFrame):
    """
    Frame Gestione tabella gruppi prezzi.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(GruPrezPanel(self, -1))


# ------------------------------------------------------------------------------


class GruPrezDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Gruppi prezzi.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(GruPrezPanel(self, -1))
