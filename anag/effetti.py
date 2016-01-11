#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/effetti.py
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

from anag import pdcrel
from anag.pdcrel_wdr import *

from Env import Azienda
bt = Azienda.BaseTab

import stormdb as adb


FRAME_TITLE = "Effetti"


class EffettiResultsGridTable(pdcrel.dbglib.DbGridTable):
    """
    Ritorna il contenuto di ogni cella della griglia per il suo disegno.
    """
    def GetValue(self, row, gridcol):
        out = None
        db = self.grid.db
        if 0 <= row < self.data:
            col = self.rsColumns[gridcol]
            if db.GetFieldName(col) == 'anag_tipo':
                val = self.data[row][col]
                if val == 'R':
                    out = 'RIBA'
                elif val == 'I':
                    out = 'RID'
                elif val == 'S':
                    out = 'SDD'
                else:
                    out = 'err'
            if out is None:
                out = pdcrel.dbglib.DbGridTable.GetValue(self, row, gridcol)
        return out


# ------------------------------------------------------------------------------


class EffettiResultsGrid(pdcrel.ga.SearchResultsGrid):

    tableClass = EffettiResultsGridTable

    def GetDbColumns(self):
        _NUM = pdcrel.gl.GRID_VALUE_NUMBER
        _STR = pdcrel.gl.GRID_VALUE_STRING
        _DAT = pdcrel.gl.GRID_VALUE_DATETIME
        cn = lambda x: self.db._GetFieldIndex(x)
        tab = self.tabalias
        return (( 50, (cn('pdc_codice'),    "Cod.",            _STR, True)),
                (190, (cn('pdc_descriz'),   "Effetto",         _STR, True)),
                ( 40, (cn('anag_tipo'),     "Tipo",            _STR, True)),
                ( 50, (cn('banca_codice'),  "Cod.",            _STR, True)),
                (180, (cn('banca_descriz'), "Banca associata", _STR, True)),
                ( 35, (cn('caus_codice'),   "Cod.",            _STR, True)),
                (140, (cn('caus_descriz'),  "Causale contab.", _STR, True)),
                (444, (cn('anag_filepath'), "Percorso file",   _STR, True)),
                (  1, (cn('pdc_id'),        "#pdc",            _STR, True)),
                (  1, (cn('banca_id'),      "#ban",            _STR, True)),
                (  1, (cn('caus_id'),       "#cau",            _STR, True)),
            )

    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class EffettiPanel(pdcrel._PdcRelPanel):
    """
    Gestione della tabella Effetti.
    """
    def __init__(self, *args, **kwargs):

        self.pdctipo = "D"
        self.tabanag = bt.TABNAME_EFFETTI
        pdcrel._PdcRelPanel.__init__(self, *args, **kwargs)

        self.anag_db_columns = [ c for c in Azienda.BaseTab.tabelle\
                                 [bt.TABSETUP_TABLE_EFFETTI]\
                                 [bt.TABSETUP_TABLESTRUCTURE] ]

        self._sqlrelcol += ", banca.id, banca.codice, banca.descriz"
        self._sqlrelcol += ", caus.id, caus.codice, caus.descriz"

        self._sqlrelfrm +=\
            " LEFT JOIN %s AS banca ON anag.id_banca=banca.id"\
            " LEFT JOIN %s AS caus ON anag.id_caus=caus.id"\
            % (bt.TABNAME_PDC, bt.TABNAME_CFGCONTAB)

        self._Auto_AddKeys( { "pdctip_effetti": True,
                              "bilmas_effetti": True,
                              "bilcon_effetti": True,
                              "bilcee_effetti": bt.CONBILRCEE == 1, } )
        self.ReadAutomat()
        self._auto_pdctip = getattr(self, "_auto_pdctip_effetti", None)
        self._auto_bilmas = getattr(self, "_auto_bilmas_effetti", None)
        self._auto_bilcon = getattr(self, "_auto_bilcon_effetti", None)
        self._auto_bilcee = getattr(self, "_auto_bilcee_effetti", None)

        self.db_report = "Sottoconti Effetto"

    def GetSqlColumns(self):
        fields = pdcrel._PdcRelPanel.GetSqlColumns(self)+', '
        for s in self.anag_db_columns:
            fields += 'anag.%s, ' % s[0]
        fields = fields[:-2]
        return fields

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        EffettiCardFunc( p, True )
        cn = lambda x: self.FindWindowById(x)
        cn(ID_TIPO).SetDataLink('tipo', 'RIS')
        #filtro su banca associata
        tipana = adb.DbTable(bt.TABNAME_PDCTIP, 'tipana', writable=False)
        if tipana.Retrieve('tipo="B"'):
            cn(ID_EFFBANCA).SetFilter("id_tipo IN (%s)"\
                                      % ','.join([str(t.id) for t in tipana]))
        tipi = {}
        for tipo in "CBD":
            tipi[tipo] = [None, []]
            tipana.ClearFilters()
            tipana.AddFilter("tipana.tipo='%s'" % tipo)
            if tipana.Retrieve():
                tipi[tipo][0] = tipana.id
                for t in tipana:
                    tipi[tipo][1].append(t.id)
        del tipana
        #filtro su causale contabile da generare
        lt = cn(ID_EFFCAUS)
        lt.SetFilter("pcf=1 AND pcfscon=1 AND id_pdctippa IN (%s)"\
                     % ",".join(map(str, tipi["C"][1])))
        return p

    def GetLinkTableClass(self):
        import anag.lib as alib
        return alib.LinkTableEffetto

    def GetSearchResultsGrid(self, parent):
        grid = EffettiResultsGrid(parent, pdcrel.ga.ID_SEARCHGRID,
                                  self.db_tabname, self.GetSqlColumns())
        return grid


# ------------------------------------------------------------------------------


class EffettiFrame(pdcrel.ga._AnagFrame):
    """
    Frame Gestione tabella Effetti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(EffettiPanel(self, -1))


# ------------------------------------------------------------------------------


class EffettiDialog(pdcrel.ga._AnagDialog):
    """
    Dialog Gestione tabella Effetti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        pdcrel.ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(EffettiPanel(self, -1), forceComplete=True)


# ------------------------------------------------------------------------------


def runTest(frame, nb, log):
    win = EffettiDialog()
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
