#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/fatclifor.py
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

import awc.controls.windows as aw

import Env
from awc.lib import ControllaCodFisc, ControllaPIVA
from anag.clienti import ClientiDialog
from anag.fornit import FornitDialog
bt = Env.Azienda.BaseTab

import contab.dbtables as dbc

from contab import regiva_wdr as wdr

import report as rpt
from awc.controls.linktable import EVT_LINKTABCHANGED


FRAME_TITLE = "Analisi del fatturato contabile clienti/fornitori"


class FatturatoContabileClientiFornitGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia fatturato contabile clienti/fornitori
    """
    
    valwidth = 110
    
    def __init__(self, parent, dbfat, detail=False):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable fatturato (derivati da contab.dbtables.FatturatoContabileClientiFornit)
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbfat = fat = dbfat
        
        _STR = gl.GRID_VALUE_STRING
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _DAT = gl.GRID_VALUE_DATETIME
        _VAL = bt.GetValIntMaskInfo()
        def cn(col):
            return fat._GetFieldIndex(col, inline=True)
        
        w = self.valwidth
        
        cols = []
        AC = cols.append
        AC(( 50, (cn('pdc_codice'),       "Cod.",           _STR, True)))
        AC((240, (cn('pdc_descriz'),      "Cliente",        _STR, True)))
        AC(( 40, (cn('anag_stato'),       "Stato",          _STR, True)))
        AC((100, (cn('anag_piva'),        "P.IVA",          _STR, True)))
        AC((130, (cn('anag_codfisc'),     "Cod.Fiscale",    _STR, True)))
        AC(( 30, (cn('anag_statocee'),    "CEE",            _CHK, True)))
        AC(( 30, (cn('anag_statobl'),     "SBL",            _CHK, True)))
        AC(( 30, (cn('anag_anagbl'),      "ABL",            _CHK, True)))
        if detail:
            AC(( 40, (cn('cau_codice'),   "Cod.",           _STR, True)))
            AC((120, (cn('cau_descriz'),  "Causale",        _STR, True)))
            AC(( 60, (cn('reg_numdoc'),   "Num.Doc.",       _STR, True)))
            AC(( 80, (cn('reg_datdoc'),   "Data",           _DAT, True)))
            AC(( 40, (cn('aliq_codice'),  "IVA",            _STR, True)))
        AC((  w, (cn('total_operazioni'), "Tot.Operazioni", _VAL, True)))
        AC((  w, (cn('total_imponibile'), "Imponibile",     _VAL, True)))
        AC((  w, (cn('total_impostaiva'), "Imposta",        _VAL, True)))
        AC((  w, (cn('total_nonimponib'), "Non Imponib.",   _VAL, True)))
        AC((  w, (cn('total_esente_iva'), "Esente",         _VAL, True)))
        AC((  w, (cn('total_fuoricampo'), "Fuori campo",    _VAL, True)))
        if detail:
            AC((120, (cn('aliq_descriz'), "Aliquota IVA",   _STR, True)))
        AC((  1, (cn('pdc_id'),           "#pdc",           _STR, True)))
        
        self._col_codfisc = cn('anag_codfisc')
        self._col_piva = cn('anag_piva')
        self._col_stato = cn('anag_stato')
        
        self._cols=cols
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(self.dbfat.GetRecordset(), colmap)
        
        self.AddTotalsRow(1,'Totali:',(cn('total_imponibile'),
                                       cn('total_impostaiva'),
                                       cn('total_nonimponib'),
                                       cn('total_esente_iva'),
                                       cn('total_fuoricampo'),
                                       cn('total_operazioni')))
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=dbglib.gridlib.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr=attr)   
        if 0 <= row < self.dbfat.RowsCount():
            err = False
            if rscol == self._col_codfisc:
                cf = self.dbfat.GetRecordset()[row][self._col_codfisc]
                if len(cf or '') > 0:
                    c = ControllaCodFisc(cf)
                    if not c.Controlla():
                        err = True
            elif rscol == self._col_piva:
                rs = self.dbfat.GetRecordset()
                pi = rs[row][self._col_piva]
                if len(pi or '') > 0:
                    c = ControllaPIVA()
                    c.SetPIva(pi, rs[row][self._col_stato])
                    if not c.Controlla():
                        err = True
            if err:
                attr.SetBackgroundColour('red')
                attr.SetTextColour('yellow')
        return attr


# ------------------------------------------------------------------------------


class FatturatoContabileClientiFornitPanel(aw.Panel):
    """
    Pannello fatturato contabile clienti/fornitori
    """
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        self.detail = False
        wdr.FatturatoContabileClientiFornitFunc(self)
        cn = self.FindWindowByName
        self.dbfat = dbc.FatturatoContabileClienti() #cambia in base a radiobox acquisti/vendite
        self.gridfat = FatturatoContabileClientiFornitGrid(cn('pangridfat'), self.dbfat)
        self.Bind(wx.EVT_RADIOBOX, self.OnAcqVenChanged, cn('acqven'))
        self.Bind(EVT_LINKTABCHANGED, self.OnStatoChanged, cn('id_stato'))
        for name, func in (('butupd', self.OnUpdateData),
                           ('butprt', self.OnPrintData),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        
        self.TestRegIva()
        
        wx.CallAfter(lambda: cn('datmin').SetFocus())
    
    def GetPanelDataSource(self):
        return self.fat
        
    def OnCellDblClick(self, event):
        row = event.GetRow()
        self.dbfat.MoveRow(row)
        tipo = self.dbfat.pdc_tipo
        if tipo == "C":
            Dialog = ClientiDialog
        elif tipo == "F":
            Dialog = FornitDialog
        else:
            aw.awu.MsgDialog(self, "Tipo panagrafico non riconosciuto")
            return
        id_pdc = self.dbfat.pdc_id
        wx.BeginBusyCursor()
        try:
            dlg = Dialog(self, onecodeonly=id_pdc)
            dlg.OneCardOnly(id_pdc)
            dlg.CenterOnScreen()
        finally:
            wx.EndBusyCursor()
        dlg.ShowModal()
        dlg.Destroy()
        def update_data():
            self.UpdateData()
        wx.CallAfter(update_data)
        event.Skip()
    
    def OnAcqVenChanged(self, event):
        self.TestRegIva()
        event.Skip()
    
    def TestRegIva(self):
        cn = self.FindWindowByName
        av = cn('acqven').GetValue()
        if av == 'A':
            tipi = 'A'
        else:
            tipi = 'VC'
        rr = cn('registri')
        rr.ClearVoices()
        regs = dbc.adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
        regs.AddOrder('regiva.codice')
        regs.Retrieve()
        for reg in regs:
            if reg.tipo in tipi:
                rr.AppendVoice(reg)
    
    def OnStatoChanged(self, event):
        self.TestStato()
        event.Skip()
    
    def TestStato(self):
        cn = self.FindWindowByName
        s = cn('id_stato').GetValue()
        for name in 'ita cee ext'.split():
            cn('stati_%s'%name).Enable(s is None)
    
    def OnUpdateData(self, event):
        if self.Validate():
            self.UpdateData()
            event.Skip()
    
    def Validate(self):
        cn = self.FindWindowByName
        d1, d2 = map(lambda x: cn(x).GetValue(), 'datmin datmax'.split())
        if not d1 or not d2 or d2<d1:
            aw.awu.MsgDialog(self, "Date non valide", style=wx.ICON_ERROR)
            return False
        return True
    
    def UpdateData(self):
        cn = self.FindWindowByName
        av, qa, d1, d2, ss, si, sc, sx, ct = map(lambda x: cn(x).GetValue(), 
                                                 'acqven qualianag datmin datmax id_stato stati_ita stati_cee stati_ext congr_tipana'.split())
        self.detail = dr = cn('detail').IsChecked()
        if av == 'A':
            fat = self.dbfat = dbc.FatturatoContabileFornitori(detail=dr)
        else:
            fat = self.dbfat = dbc.FatturatoContabileClienti(detail=dr)
        fat.ClearFilters()
        ri = []
        regs = cn('registri')
        for n in range(len(regs.valori)):
            if regs.IsChecked(n):
                ri.append(regs.valori[n])
        if not ri:
            aw.awu.MsgDialog(self, "Nessun registro selezionato")
            return
        fat.AddFilter('reg.id_regiva IN (%s)' % ', '.join(map(str, ri)))
        if ct:
            fat.AddFilter('tipana.tipo=%s', fat.clifor)
        fat.AddFilter('reg.datreg>=%s', d1)
        fat.AddFilter('reg.datreg<=%s', d2)
        if qa == "A":
            #solo anagrafiche in blacklist
            fat.AddFilter('IF(tipana.tipo="C", cliente.is_blacklisted=1, fornit.is_blacklisted=1)')
        elif qa == "S":
            #solo anagrafiche con stato in blacklist
            fat.AddFilter('IF(tipana.tipo="C", stato_cli.is_blacklisted=1, stato_for.is_blacklisted=1)')
        sf = ''
        if ss:
            sf = 'IF(tipana.tipo="C", stato_cli.id=%d, stato_for.id=%d)' % (ss, ss)
        elif not (si and sc and sx):
            if si:
                if sf:
                    sf += ' OR '
                sf += 'IF(tipana.tipo="C", stato_cli.codice="IT", stato_for.codice="IT")'
            if sc:
                if sf:
                    sf += ' OR '
                sf += 'IF(tipana.tipo="C", stato_cli.codice<>"IT" AND stato_cli.is_cee=1, stato_for.codice<>"IT" AND stato_for.is_cee=1)'
            if sx:
                if sf:
                    sf += ' OR '
                sf += 'IF(tipana.tipo="C", stato_cli.codice<>"IT" AND stato_cli.is_cee=0, stato_for.codice<>"IT" AND stato_for.is_cee=0)'
        if sf:
            fat.AddFilter(sf)
            
        self.fat=fat
        wx.BeginBusyCursor()
        try:
            if not fat.Retrieve():
                aw.awu.MsgDialog(self, repr(fat.GetError()), style=wx.ICON_ERROR)
                return False
        finally:
            wx.EndBusyCursor()
        self.gridfat.Destroy()
        self.gridfat = FatturatoContabileClientiFornitGrid(cn('pangridfat'), fat, detail=dr)
        self.gridfat.ChangeData(fat.GetRecordset())
        self.Bind(dbglib.gridlib.EVT_GRID_CELL_LEFT_DCLICK, self.OnCellDblClick, self.gridfat)
    
    def OnPrintData(self, event):
        self.PrintData()
        event.Skip()
    
    def PrintData(self):
        cn = self.FindWindowByName
        fat = self.dbfat
        for name in 'datmin datmax'.split():
            fat.SetPrintValue(name, cn(name).GetValue())
        
        fat._info.titolo = ''
        name = 'Fatturato Contabile Acquisti-Vendite'
        if self.detail:
            name = 'Dettaglio %s' % name
        rpt.Report(self, fat, name)


# ------------------------------------------------------------------------------


class FatturatoContabileClientiFornitFrame(aw.Frame):
    """
    Frame fatturato contabile clienti/fornitori
    """
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = FatturatoContabileClientiFornitPanel(self)
        self.AddSizedPanel(self.panel)
