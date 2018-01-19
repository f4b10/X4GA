#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/aliqiva.py
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
import anag.aliqiva_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab

import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc.controls.windows as aw
import stormdb as adb

FRAME_TITLE = "Aliquote IVA"


class AliqIvaSearchResultsGrid(ga.SearchResultsGrid):

    def GetDbColumns(self):
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRC = bt.GetPerGenMaskInfo()
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 35, (cn('aliqiva_codice'),      "Cod.",     _STR, True)),
                (240, (cn('aliqiva_descriz'),     "Aliquota", _STR, True)),
                ( 50, (cn('aliqiva_perciva'),     "%IVA",     _PRC, True)),
                ( 50, (cn('aliqiva_percind'),     "%Ind",     _PRC, True)),
                ( 50, (cn('aliqiva_tipo'),        "Tipo",     _STR, True)),
                ( 50, (cn('aliqiva_modo'),        "Modo",     _STR, True)),
                ( 50, (cn('aliqiva_ftel_natura'), "Natura",   _STR, True)),
                ( 50, (cn('aliqiva_sm11_no'),     "No Sp.",   _CHK, True)),
                (  1, (cn('aliqiva_id'),          "#aliq",    _STR, True)),
            )

    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class AliqIvaPanel(ga.AnagPanel):
    """
    Gestione tabella Aliquote IVA.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_ALIQIVA ] )
        self.db_report = "Aliquote IVA"

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.AliqIvaCardFunc( p, True )
        ci = lambda x: self.FindWindowById(x)
        cn = lambda x: self.FindWindowByName(x)
        ci(wdr.ID_TIPO).SetDataLink("tipo", " CSD")
        for cf in 'cf':
            for c in range(4):
                name = 'pral%sc%d' % (cf, c+1)
                cn(name).SetDataLink(name, (0,1,2))
        cn('ftel_natura').SetDataLink('ftel_natura', ('','N1','N2','N3','N4','N5','N6','N7'))

        return p

    def SetInsertMode(self):
        out = ga.AnagPanel.SetInsertMode(self)
        self.FindWindowById(wdr.ID_DATIALLEG).SetSelection(0)
        return out

    def GetSearchResultsGrid(self, parent):
        grid = AliqIvaSearchResultsGrid(parent, ga.ID_SEARCHGRID,
                                        self.db_tabname, self.GetSqlColumns())
        return grid



    def OnRecordSave( self, event ):
        if self.ExistAutomatismo():
            ga.AnagPanel.OnRecordSave(self, event)
        else:
            aw.awu.MsgDialog(self, "Provvedere a definire automatismo contabile", style=wx.ICON_QUESTION)
        
    def ExistAutomatismo(self):
        esito = True
        tipo=self.FindWindowByName('tipo').GetValue()
        if tipo=='D':
            dbAuto = adb.DbTable(bt.TABNAME_CFGAUTOM, 'auto')
            
            for codice, descriz in [
                                    ['ivaacqdif', 'Sottoconto IVA per acquisti a detraibilità differita'],
                                    ['ivavendif', 'Sottoconto IVA per vendite a detraibilità differita'],
                                    ]:
                dbAuto.Retrieve('codice="%s"' % codice)
                if dbAuto.RowsCount()==0:
                    dbAuto.CreateNewRow()
                    dbAuto.codice=codice
                    dbAuto.descriz=descriz
                    esito = dbAuto.Save()
                    if not esito:
                        break
        return esito
        
        #=======================================================================
        # if self.UpdateDataRecord():
        #     if not self.complete:
        #         f = awc.util.GetParentFrame(self)
        #         if issubclass(f.__class__, wx.Dialog) and f.IsModal():
        #             f.EndModal(self.db_recid)
        # event.Skip()
        #=======================================================================

# ------------------------------------------------------------------------------


class AliqIvaFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Aliquote Iva.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(AliqIvaPanel(self, -1))


# ------------------------------------------------------------------------------


class AliqIvaDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Aliquote Iva.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.panel = AliqIvaPanel(self, -1)
        self.LoadAnagPanel(AliqIvaPanel(self, -1))


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = AliqIvaDialog()
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
