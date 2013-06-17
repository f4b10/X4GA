#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/modpag.py
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

import awc.layout.gestanag as ga
import anag.modpag_wdr as wdr

import awc.util as util

from Env import Azienda

bt = Azienda.BaseTab

import wx.grid as gl
import awc.controls.dbgrid as dbglib


FRAME_TITLE = "Modalità di pagamento"


class ModPagSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 35, (cn('modpag_codice'),  "Cod.",           _STR, True)),
                (240, (cn('modpag_descriz'), "Descrizione",    _STR, True)),
                ( 50, (cn('modpag_numscad'), "#sc.",           _NUM, True)),
                ( 50, (cn('pdcpi_codice'),   "Cod.",           _STR, True)),
                (200, (cn('pdcpi_descriz'),  "Cassa pag.imm.", _STR, True)),
                (  1, (cn('modpag_id'),      "#mpa",           _STR, True)),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class ModPagPanel(ga.AnagPanel):
    """
    Gestione tabella Moadlità di pagamento.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_MODPAG ] )
        self._sqlrelcol = ", pdcpi.id, pdcpi.codice, pdcpi.descriz"
        self._sqlrelfrm =\
            " LEFT JOIN %s AS pdcpi ON %s.id_pdcpi=pdcpi.id"\
            % (bt.TABNAME_PDC, self.db_tabname)
        self.db_report = "Modalita' di Pagamento"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.ModPagCardFunc( p, True )
        
        for cid, name, opt, evt in (\
            (wdr.ID_TIPOMP,   'tipo',     'CBRIXY', self.OnChanged),
            (wdr.ID_MODOCALC, 'modocalc', 'SDN',    self.OnCalcChanged),
            (wdr.ID_PERIODI,  'tipoper',  'MG',     self.OnCalcChanged)):
            self.FindWindowById(cid).SetDataLink(name, opt)
            self.Bind(wx.EVT_RADIOBOX, evt, id=cid)
        
        self.FindWindowByName('congar').SetDataLink(values=[1, 0])
        
        for cid, name in ((wdr.ID_FINEMESE, 'finemese0'),
                          (wdr.ID_FINEMESE, 'finemese'),
                          (wdr.ID_SC1NOEFF, 'sc1noeff'),
                          (wdr.ID_SC1IVA,   'sc1iva',),
                          (wdr.ID_CONTRASS, 'contrass'),
                          (wdr.ID_ASKBANCA, 'askbanca'),
                          (wdr.ID_ASKSPESE, 'askspese')):
            ctr = self.FindWindowById(cid)
            ctr.SetDataLink(name, { True: 1, False: 0 })
        
        return p

    def UpdateCalcs(self):
        calc = self.FindWindowById(wdr.ID_MODOCALC).GetValue()
        if not calc in "DSN":
            return
        names = {"D": "gg", "S": "mesi", "N": "id_pdcpi"}
        for win in util.GetNamedChildrens(self):
            name = win.GetName()
            for p in names.values():
                if name.startswith(p):
                    win.Enable(name.startswith(names[calc]))
                if name.startswith('sc1'):
                    win.Enable(calc != "N")
        cn = self.FindWindowByName
        cn('ggextra').Enable(cn('id_pdcpi').GetValue() is None)
        for n in range(1,13):
            cn('gem%s' % str(n).zfill(2)).Enable(cn('id_pdcpi').GetValue() is None)

    def UpdateDataControls(self, recno):
        ga.AnagPanel.UpdateDataControls(self, recno)
        self.UpdateCalcs()

    def OnCalcChanged(self, event):
        self.SetDataChanged()
        self.UpdateCalcs()

    def OnChanged(self, event):
        self.SetDataChanged()
    
    def GetSearchResultsGrid(self, parent):
        grid = ModPagSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                       self.db_tabname, self.GetSqlColumns())
        return grid


# ------------------------------------------------------------------------------


class ModPagFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Modalità di pagamento.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ModPagPanel(self, -1))


# ------------------------------------------------------------------------------


class ModPagDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Modalità di pagamento.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ModPagPanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = ModPagDialog()
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
