#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         contab/scadglobal.py
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
import wx.grid as gl
import awc.controls.dbgrid as dbglib

import awc
import awc.controls.windows as aw

import contab.dbtables as dbc
import contab.pdcint_wdr as wdr

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import stormdb as adb

import report as rpt


RSGLOB_DATE =    0
RSGLOB_PERIODO = 1
RSGLOB_SALDO =   2
RSGLOB_PROGR =   3


PERIODI_DATA = "G" #giornaliero
PERIODI_SETT = "S" #settimanale
PERIODI_MESE = "M" #mensile
PERIODI_BIME = "B" #bimestrale
PERIODI_TRIM = "T" #trimestrale
PERIODI_QUAD = "Q" #quadrimestrale


class GridScadTot(dbglib.DbGrid):
    
    def __init__(self, dbscad, saldimpo, *args, **kwargs):
        
        parent = args[0]
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size)
        
        self.dbscad = dbscad
        self.saldimpo = saldimpo
        self.rsscad = ()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (RSGLOB_PERIODO, "Periodo",     _STR, True )),\
            (110, (RSGLOB_SALDO,   "Saldo",       _IMP, True )),\
            (110, (RSGLOB_PROGR,   "Progressivo", _IMP, True )),\
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData( self.rsscad, colmap, canedit, canins)
        
        def GridAttr(row, col, rscol, attr):
            if row<len(self.rsscad):
                if self.rsscad[row][RSGLOB_SALDO]<0:
                    fgcol = stdcolor.GetColour("red")
                    bgcol = stdcolor.GetColour("azure3")
                else:
                    fgcol = stdcolor.NORMAL_FOREGROUND
                    bgcol = stdcolor.GetColour("bisque")
                attr.SetTextColour(fgcol)
                attr.SetBackgroundColour(bgcol)
            return attr
        self.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def UpdateGrid(self, tipoper):
        
        assert tipoper in (PERIODI_DATA, PERIODI_SETT, PERIODI_MESE, 
                           PERIODI_BIME, PERIODI_TRIM, PERIODI_QUAD),\
               """Tipo periodo errato"""
        
        def GetPeriodo(data):
            if   tipoper == PERIODI_DATA:
                out = data.Format("%d/%m/%Y")
            elif tipoper == PERIODI_SETT:
#                out = "%d/%d" % (data.iso_week[1], data.iso_week[0])
                out = "%s/%d" % (data.strftime('%U'), data.year)
            elif tipoper == PERIODI_MESE:
                out = "%d/%d" % (data.month, data.year)
            elif tipoper == PERIODI_BIME:
                out = "Bim.%d/%d" % (data.month/2+1, data.year)
            elif tipoper == PERIODI_TRIM:
                out = "Trim.%d/%d" % (data.month/3+1, data.year)
            elif tipoper == PERIODI_QUAD:
                out = "Quadr.%d/%d" % (data.month/4+1, data.year)
            return out
        
        if self.saldimpo in "SX":
            name = 'saldo'
        else:
            name = 'imptot'
        ncdata = self.dbscad._GetFieldIndex('datscad')
        ncsald = self.dbscad._GetFieldIndex('total_%s' % name)
        nctipa = self.dbscad.pdc.tipana._GetFieldIndex('tipo', inline=True)
        
        self.rsscad = []
        rs = self.dbscad.GetRecordset()
        nr = self.dbscad.RowsCount()
        progr = 0
        row = 0
        while row < nr:
            periodo = GetPeriodo(rs[row][ncdata])
            total = 0
            dates = [None, None]
            while row < nr and periodo == GetPeriodo(rs[row][ncdata]):
                data =  rs[row][ncdata]
                saldo = rs[row][ncsald]
                if dates[0] is None or data<dates[0]:
                    dates[0] = data
                if dates[1] is None or data>dates[1]:
                    dates[1] = data
                try:
                    dates.index(data)
                except ValueError:
                    dates.append(data)
                total += saldo
                progr += saldo
                row += 1
            if True:#total != 0:
                self.rsscad.append((dates, periodo, total, progr))
        self.ChangeData(self.rsscad)


# ------------------------------------------------------------------------------


class GridPcf(dbglib.DbGrid):
    
    def __init__(self, dbpcf, dbscad, *args, **kwargs):
        
        parent = args[0]
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size)
        
        self.dbpcf = dbpcf
        self.dbscad = dbscad
        
        pcf = self.dbpcf
        pdc = pcf.pdc
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 90, (cn(pcf, 'datscad'), "Scadenza",        _DAT, True )),\
            ( 50, (cn(pdc, 'codice'),  "Cod.",            _STR, True )),\
            (140, (cn(pdc, 'descriz'), "Ragione Sociale", _STR, True )),\
            (110, (cn(pcf, 'imptot'),  "Importo",         _IMP, True )),\
            (110, (cn(pcf, 'imppar'),  "Pareggiamento",   _IMP, True )),\
            (110, (cn(pcf, 'saldo'),   "Saldo",           _IMP, True )),\
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData([], colmap, canedit, canins)
        
        def GridAttr(row, col, rscol, attr):
            if row<self.dbpcf.RowsCount():
                if row != self.dbpcf.RowNumber():
                    self.dbpcf.MoveRow(row)
                if self.dbpcf.pdc.tipana.tipo == "F":
                    fgcol = stdcolor.GetColour("red")
                    bgcol = stdcolor.GetColour("azure3")
                else:
                    fgcol = stdcolor.NORMAL_FOREGROUND
                    bgcol = stdcolor.GetColour("bisque")
                attr.SetTextColour(fgcol)
                attr.SetBackgroundColour(bgcol)
            return attr
        self.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(2)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def UpdateGrid(self, datamin, datamax, clifor, tipmpa, saldo_filter):
        filters = []
        for n, f in enumerate(self.dbscad._info.filters):
            filters.append((f[0].replace('sintesi.', 'pcf.'), f[1]))
        db = self.dbpcf
        db.ClearFilters()
        if datamin is not None:
            db.AddFilter("pcf.datscad>=%s", datamin)
        if datamax is not None:
            db.AddFilter("pcf.datscad<=%s", datamax)
        if clifor in "CF":
            db.AddFilter("tipana.tipo=%s", clifor)
        if tipmpa:
            tm = ','.join(['"%s"' % t for t in tipmpa])
            db.AddFilter("modpag.tipo IN (%s)" % tm)
        if saldo_filter:
            db.AddFilter(saldo_filter)
        db.Retrieve()
        db._info.periodo = (datamin, datamax)
        self.ChangeData(self.dbpcf.GetRecordset())


# ------------------------------------------------------------------------------


class GridMas(dbglib.DbGrid):
    
    def __init__(self, dbpcf, *args, **kwargs):
        
        parent = args[0]
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size)
        
        self.dbpcf = dbpcf
        
        rif = self.dbpcf.rif
        reg = rif.reg
        cau = reg.cau
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 35, (cn(cau, 'codice'),  "Cod.",    _STR, True )),\
            (100, (cn(cau, 'descriz'), "Causale", _STR, True )),\
            ( 60, (cn(reg, 'numdoc'),  "Doc.",    _STR, True )),\
            (100, (cn(reg, 'datdoc'),  "Data",    _DAT, True )),\
            (110, (cn(rif, 'importo'), "Importo", _IMP, True )),\
            ( 70, (cn(rif, 'abbuono'), "Abbuono", _IMP, True )),\
            (100, (cn(rif, 'note'),    "Note",    _STR, True )),\
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData([], colmap, canedit, canins)
        
        #def GridAttr(row, col, rscol, attr):
            #if row<self.dbpcf.RowsCount():
                #if row != self.dbpcf.RowNumber():
                    #self.dbpcf.MoveRow(row)
                #if self.dbpcf.pdc.tipana.tipo == "F":
                    #fgcol = stdcolor.GetColour("red")
                    #bgcol = stdcolor.GetColour("azure3")
                #else:
                    #fgcol = stdcolor.NORMAL_FOREGROUND
                    #bgcol = stdcolor.GetColour("bisque")
                #attr.SetTextColour(fgcol)
                #attr.SetBackgroundColour(bgcol)
            #return attr
        #self.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(6)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def UpdateGrid(self):
        self.dbpcf.UpdateChildrens()
        self.ChangeData(self.dbpcf.rif.GetRecordset())


# ------------------------------------------------------------------------------


class ScadGlobalPanel(aw.Panel):
    
    title = 'Analisi Cash Flow'
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.dbscad = dbc.PdcScadenzarioGlobale()
        self.dbpcf = dbc.Pcf()
        self.dbpcf.SetSilent()
        
        wdr.ScadGlobalFunc(self)
        
        cbn = self.FindWindowByName
        cbi = self.FindWindowById
        
        cbn('id_bancapag').Disable()
        
        for name, val, init in (('periodo', "GSMBTQ", "G"),):
            cbn(name).SetDataLink(name, val)
            cbn(name).SetValue(init)
        
        cbn('datestart').SetValue(Env.Azienda.Login.dataElab)
        
        cbi(wdr.ID_MAINZONE).SetSashPosition(320)
        cbi(wdr.ID_DETZONE).SetSashPosition(320)
        cbi(wdr.ID_DETZONE).SetSashGravity(.8)
        
        self.gridtot = None
        self.gridpcf = None
        self.gridmas = None
        
        self.CreateGrids()
        
        for cid, func in ((wdr.ID_BUTUPD,    self.OnUpdateFilters),
                          (wdr.ID_PRINTRIEP, self.OnPrintRiepilogo),
                          (wdr.ID_PRINTPCF,  self.OnPrintPartite)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
    
    def CreateGrids(self):
        
        cbi = self.FindWindowById
        cbn = self.FindWindowByName
        
        if self.gridtot is not None:
            self.gridtot.Destroy()
        self.gridtot = GridScadTot(self.dbscad, cbn('saldimpo').GetValue(), cbi(wdr.ID_GRIDTOT))
        
        if self.gridpcf is not None:
            self.gridpcf.Destroy()
        self.gridpcf = GridPcf(self.dbpcf, self.dbscad, cbi(wdr.ID_GRIDPCF))
        
        if self.gridmas is not None:
            self.gridmas.Destroy()
        self.gridmas = GridMas(self.dbpcf, cbi(wdr.ID_GRIDMAS))
        
        def OnGridTotSelected(event):
            cn = aw.awu.GetParentFrame(self).FindWindowByName
            clifor = cn('clifor').GetValue()
            #filtro per tipo pagamento
            tipmpa = []
            for flag, name in (('C', 'mpa_coa'),
                               ('B', 'mpa_bon'),
                               ('R', 'mpa_rib'),
                               ('I', 'mpa_rid'),):
                if cn(name).IsChecked():
                    tipmpa.append(flag)
            #filtro per tipo saldo
            tipsal = cn('tipsal').GetValue()
            if tipsal in 'SN':
                if tipsal == 'S':
                    o = '<>'
                else:
                    o = '='
                saldo_filter = 'pcf.imptot%spcf.imppar' % o
            else:
                saldo_filter = None
            row = event.GetRow()
            if row<len(self.gridtot.rsscad):
                dates = self.gridtot.rsscad[row][RSGLOB_DATE]
                self.gridpcf.UpdateGrid(dates[0], dates[1], clifor, tipmpa, saldo_filter)
            event.Skip()
        self.gridtot.Bind(gl.EVT_GRID_SELECT_CELL, OnGridTotSelected)
        
        def OnGridPcfSelected(event):
            row = event.GetRow()
            if row<self.dbpcf.RowsCount():
                self.gridmas.UpdateGrid()
            event.Skip()
        self.gridpcf.Bind(gl.EVT_GRID_SELECT_CELL, OnGridPcfSelected)
        
    def OnPrintRiepilogo(self, event):
        self.PrintRiepilogo()
        event.Skip()
    
    def OnPrintPartite(self, event):
        self.PrintPartite()
        event.Skip()
    
    def OnUpdateFilters(self, event):
        self.CreateGrids()
        if self.UpdateFilters():
            self.UpdateGrid()
        event.Skip()
    
    def UpdateFilters(self):
        
        cn = self.FindWindowByName
        
        pcf = self.dbscad
        pcf.ClearPcfFilters()
        cf = cn('clifor').GetValue()
        if cf in "CF":
            pcf.AddPcfFilter('tipana.tipo=%s', cf)
        #filtro per tipo pagamento
        tipmpa = []
        for flag, name in (('C', 'mpa_coa'),
                           ('B', 'mpa_bon'),
                           ('R', 'mpa_rib'),
                           ('I', 'mpa_rid'),):
            if cn(name).IsChecked():
                tipmpa.append(flag)
        if len(tipmpa) == 0:
            aw.awu.MsgDialog(self, "Selezionare almeno una tipologia di pagamento")
            return False
        tipmpa = ','.join(['"%s"' % t for t in tipmpa])
        pcf.AddPcfFilter('modpag.tipo IN (%s)' % tipmpa)
        #filtro per tipo di saldo
        tipsal = cn('tipsal').GetValue()
        if tipsal in 'SN':
            if tipsal == 'S':
                o = '<>'
            else:
                o = '='
            pcf.AddPcfFilter('sintesi.imptot%ssintesi.imppar' % o)
        for name, tab, field, op in (\
            ('datestart', pcf, 'datscad', '>='),\
            ):
            val = cn(name).GetValue()
            if val:
                pcf.AddPcfFilter('%s.%s%s%%s'\
                                 % (tab.GetTableAlias(), field, op), val)
        
        #bp = cn('id_bancapag').GetValue()
        #if bp:
            #pcf.AddPcfFilter('%s.id_bancapag=%s' % pcf.anag.GetTableAlias(), bp)
        
        return True
    
    def UpdateGrid(self, pdcid=None):
        db = self.dbscad
        if not db.Retrieve():
            awc.util.MsgDialog(self,\
                               "Problema in lettura dati:\n\n%s"\
                               % repr(db.GetError()))
        self.gridtot.UpdateGrid(self.FindWindowByName('periodo').GetValue())
    
    def PrintRiepilogo(self):
        cn = lambda x: self.FindWindowByName(x)
        tipoper = cn('periodo').GetValue()
        if   tipoper == PERIODI_DATA: tipo = 'giornaliero'
        elif tipoper == PERIODI_SETT: tipo = 'settimanale'
        elif tipoper == PERIODI_MESE: tipo = 'mensile'
        elif tipoper == PERIODI_BIME: tipo = 'bimestrale'
        elif tipoper == PERIODI_TRIM: tipo = 'trimestrale'
        elif tipoper == PERIODI_QUAD: tipo = 'quadrimestrale'
        db = adb.DbMem(fields='date,periodo,saldo,progressivo')
        db.SetRecordset(self.gridtot.rsscad)
        db._info.datastart = cn('datestart').GetValue()
        db._info.descperiodi = tipo
        db._info.title = '%s - %s' % (self.title, tipo)
        rpt.Report(self, db, 'Analisi Cash Flow')
    
    def PrintPartite(self):
        db = self.dbpcf
        rpt.Report(self, db, 'Cash Flow - Partite del periodo')


# ------------------------------------------------------------------------------


class ScadGlobalFrameBase(aw.Frame):
    
    _title = None
    _clifor = None
    _eff_no = None
    _eff_yes = None
    _saldimpo = None
    _tiposaldo = None
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = self._title
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = ScadGlobalPanel(self, -1)
        self.panel.title = self._title
        self.AddSizedPanel(self.panel)
        cn = self.FindWindowByName
        cn('clifor').SetValue(self._clifor)
        if self._eff_no is False:
            for name in 'mpa_coa mpa_bon'.split():
                cn(name).SetValue(False)
        if self._eff_yes is False:
            for name in 'mpa_rib mpa_rid'.split():
                cn(name).SetValue(False)
        if (self._saldimpo or ' ') in "SIX":
            cn('saldimpo').SetValue(self._saldimpo)
        if (self._tiposaldo or ' ') in "SQN":
            cn('tipsal').SetValue(self._tiposaldo)
        if self._saldimpo == 'X':
            cn('datestart').SetValue(None)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ScadGlobalFrame(ScadGlobalFrameBase):
    
    _title = "Analisi scadenzario globale"
    _clifor = "T"
    _eff_no = True
    _eff_yes = True
    _saldimpo = 'S'
    _tiposaldo = 'Q'


# ------------------------------------------------------------------------------


class ScadGlobalIncassiFrame(ScadGlobalFrameBase):
    
    _title = "Analisi previsione incassi"
    _clifor = "C"
    _eff_no = True
    _eff_yes = True
    _saldimpo = 'S'
    _tiposaldo = 'Q'


# ------------------------------------------------------------------------------


class ScadGlobalPagamentiFrame(ScadGlobalFrameBase):
    
    _title = "Analisi previsione pagamenti"
    _clifor = "F"
    _eff_no = True
    _eff_yes = True
    _saldimpo = 'S'
    _tiposaldo = 'Q'


# ------------------------------------------------------------------------------


class ScadGlobalEffettiDaEmettereFrame(ScadGlobalFrameBase):
    
    _title = "Portafoglio effetti da emettere"
    _clifor = "C"
    _eff_no = False
    _eff_yes = True
    _saldimpo = 'S'
    _tiposaldo = 'S'


# ------------------------------------------------------------------------------


class ScadGlobalEffettiEmessiFrame(ScadGlobalFrameBase):
    
    _title = "Scadenzario effetti"
    _clifor = "C"
    _eff_no = False
    _eff_yes = True
    _saldimpo = 'I'
    _tiposaldo = 'N'


# ------------------------------------------------------------------------------


class ScadGlobalEffettiInsolutiApertiFrame(ScadGlobalFrameBase):
    
    _title = "Scadenzario insoluti aperti"
    _clifor = "C"
    _eff_no = False
    _eff_yes = True
    _saldimpo = 'X'
    _tiposaldo = 'S'
