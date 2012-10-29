#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/calcintpcf.py
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
import awc.controls.windows as aw
import awc.controls.dbgrid as dbgrid

import contab.pdcint_wdr as wdr

import contab.dbtables as dbc


class CalcIntPcfGrid(dbgrid.ADB_Grid):
    
    def __init__(self, parent, dbpcf):
        
        self.dbpcf = pcf = dbpcf
        pdc = pcf.pdc
        cau = pcf.caus
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbpcf, can_edit=False, on_menu_select='row')
        
        AC = self.AddColumn
        self.COL_CAUSAL = AC(cau, 'descriz', label='Causale', col_width=120)
        self.COL_NUMDOC = AC(pcf, 'numdoc', label='Num.', col_width=60)
        self.COL_DATDOC = AC(pcf, 'datdoc', label='Data doc.', col_type=self.TypeDate())
        self.COL_CODCLI = AC(pdc, 'codice', label='Cod.', col_width=50)
        self.COL_DESCLI = AC(pdc, 'descriz', label='Cliente', col_width=300, is_fittable=True)
        self.COL_DATSCA = AC(pcf, 'datscad', label='Scadenza', col_type=self.TypeDate())
        self.COL_SALDOX = AC(pcf, 'saldo', label='Saldo', col_type=self.TypeFloat())
        self.COL_GGRITA = AC(pcf, 'ritardo', label='Ritardo', col_type=self.TypeInteger(5))
        self.COL_INTERE = AC(pcf, 'interessi', label='Interessi', col_type=self.TypeFloat())
        self.COL_ID_PCF = AC(pcf, 'id', label='#pcf', col_width=1)
        self.COL_ID_PDC = AC(pdc, 'id', label='#pdc', col_width=1)
        
        self.CreateGrid()
        
        def gfi(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        self.AddTotalsRow(self.COL_DESCLI, 'Totali', (gfi(pcf, 'saldo'),
                                                      gfi(pcf, 'interessi'),))


class CalcIntPcfPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.InteressiPartiteScaduteFunc(self)
        cn = self.FindWindowByName
        self.dbpcf = dbc.CalcIntPcf()
        self.gridpcf = CalcIntPcfGrid(cn('pangridpcf'), self.dbpcf)
        self.UpdateData()
        self.Bind(wx.EVT_BUTTON, self.OnUpdateData, cn('butupdate'))
#        self.Bind(wx.EVT_BUTTON, self.OnPrintData, cn('butprint'))
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        
        cn = self.FindWindowByName
        
        pcf = self.dbpcf
        pcf.ClearFilters()
        def gfv(name):
            return cn(name).GetValue()
        def gfd(name):
            return cn(name).GetValueDes()
        def gfc(name):
            return cn(name).GetValueCod()
        datdoc1, datdoc2 = map(gfv , 'datdoc1 datdoc2'.split())
        datsca1, datsca2 = map(gfv , 'datsca1 datsca2'.split())
        mingrit, percint = map(gfv, 'giornirit percint'.split())
        despdc1, despdc2 = map(gfd, 'id_pdc1 id_pdc2'.split())
        codmpa1, codmpa2 = map(gfc, 'id_modpag1 id_modpag2'.split())
        if datdoc1:
            pcf.AddFilter('pcf.datdoc>="%s"' % datdoc1.isoformat())
        if datdoc2:
            pcf.AddFilter('pcf.datdoc>="%s"' % datdoc2.isoformat())
        if datsca1:
            pcf.AddFilter('pcf.datscad>="%s"' % datsca1.isoformat())
        if datsca2:
            pcf.AddFilter('pcf.datscad<="%s"' % datsca2.isoformat())
        if despdc1:
            pcf.AddFilter('pdc.descriz>=%s', despdc1)
        if despdc2:
            pcf.AddFilter('pdc.descriz<=%s', despdc2)
        if codmpa1:
            pcf.AddFilter('modpag.codice>=%s', codmpa1)
        if codmpa2:
            pcf.AddFilter('modpag.codice<=%s', codmpa2)
        pcf.SetPercInt(percint)
        wx.BeginBusyCursor()
        try:
            pcf.Retrieve()
        finally:
            wx.EndBusyCursor()
        self.gridpcf.ChangeData(pcf.GetRecordset())


class CalcIntPcfFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Calcolo interessi partite scadute clienti'
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = CalcIntPcfPanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Show()
