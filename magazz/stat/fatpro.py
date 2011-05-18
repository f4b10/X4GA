#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/fatpro.py
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

import anag.dbtables as dba
import magazz.dbtables as dbm
import magazz.stat.dbtables as dbs

adb  = dba.adb
samefloat = adb.DbTable.samefloat

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab
DV = bt.VALINT_DECIMALS

import magazz.stat.fatpdc_wdr as wdr
import magazz.stat.fatpdc as fatpdc

import report as rpt


FRAME_TITLE_FATT = "Fatturato prodotti"
FRAME_TITLE_FATTPC = "Fatturato prodotti/clienti"


class FatturatoProdottiGrid(fatpdc._FatturatoVenditeGrid):
    
    def GetColDef(self):
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _VAL = bt.GetValIntMaskInfo()
        
        mov = self.dbfat
        pro = mov.prod
        
        return (\
            ( 90, (cn(pro, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(pro, 'descriz'),          "Prodotto",  _STR, False)),
            ( 90, (cn(mov, 'total_statqtafat'), "Qta",       _QTA, False)),
            (110, (cn(mov, 'total_statvalfat'), "Fatturato", _VAL, False)),
            (  1, (cn(pro, 'id'),               "#pro",      _STR, False)),
        )
    
    def SetTotali(self):
        def cn(col):
            return self.dbfat._GetFieldIndex(col)
        self.AddTotalsRow(1, 'Totali', (cn('total_statqtafat'),
                                        cn('total_statvalfat'),))


# ------------------------------------------------------------------------------


class FatturatoProdottiPanel(fatpdc._FatturatoVenditePanel):
    
    rptname = "Fatturato Prodotti"
    
    def InitControls(self):
        wdr.SetClienti()
        wdr.FatturatoPdcFunc(self)
    
    def InitTableFatt(self):
        self.dbfat = dbs.FatturatoProdotti()
        self.dbfat.ShowDialog(self)
    
    def InitGrid(self):
        self.gridfat = FatturatoProdottiGrid(self.FindWindowByName('pangridfat'), 
                                             self.dbfat)
    
    def SetOrder(self):
        tipord = self.FindWindowByName('tipord').GetSelection()
        f = self.dbfat
        f.ClearOrders()
        if   tipord == 1: #per fatturato, da 0
            f.AddOrder('(total_statvalfat)', adb.ORDER_ASCENDING)
        elif tipord == 2: #per fatturato, dal massimo
            f.AddOrder('(total_statvalfat)', adb.ORDER_DESCENDING)
        f.AddOrder('prod.codice')
    
    def OnUpdate(self, event):
        self.UpdateData(self.dbfat, self.gridfat)
        event.Skip()


# ------------------------------------------------------------------------------


class FatturatoProdottiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE_FATT
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(FatturatoProdottiPanel(self))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class FatturatoProCliGrid(FatturatoProdottiGrid):
    
    def GetColDef(self):
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _VAL = bt.GetValIntMaskInfo()
        
        mov = self.dbfat
        pro = mov.prod
        pdc = mov.doc.pdc
        
        return (\
            ( 90, (cn(pro, 'codice'),           "Cod.",      _STR, False)),
            (180, (cn(pro, 'descriz'),          "Prodotto",  _STR, False)),
            ( 60, (cn(pdc, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(pdc, 'descriz'),          "Cliente",   _STR, False)),
            ( 90, (cn(mov, 'total_statqtafat'), "Qta",       _QTA, False)),
            (110, (cn(mov, 'total_statvalfat'), "Fatturato", _VAL, False)),
            (  1, (cn(pro, 'id'),               "#pro",      _STR, False)),
            (  1, (cn(pdc, 'id'),               "#cli",      _STR, False)),
        )
    
    def _SetFitColumn(self):
        self.SetFitColumn(3)


# ------------------------------------------------------------------------------


class FatturatoProCliPanel(FatturatoProdottiPanel):
    
    rptname = "Fatturato Prodotti per Cliente"
    
    def InitControls(self):
        wdr.SetClienti()
        wdr.FatturatoPdcFunc(self)
    
    def InitTableFatt(self):
        self.dbfat = dbs.FatturatoProCli()
        self.dbfat.ShowDialog(self)
    
    def InitGrid(self):
        self.gridfat = FatturatoProCliGrid(self.FindWindowByName('pangridfat'), 
                                           self.dbfat)
    
    def SetOrder(self):
        tipord = self.FindWindowByName('tipord').GetSelection()
        f = self.dbfat
        f.ClearOrders()
        if   tipord == 1: #per fatturato, da 0
            f.AddOrder('(total_statvalfat)', adb.ORDER_ASCENDING)
        elif tipord == 2: #per fatturato, dal massimo
            f.AddOrder('(total_statvalfat)', adb.ORDER_DESCENDING)
        f.AddOrder('prod.codice')
        f.AddOrder('pdc.descriz')
    
    def OnUpdate(self, event):
        self.UpdateData(self.dbfat, self.gridfat)
        event.Skip()
    
    def OnPrint(self, event):
        db = self.dbfat
        tipord = self.FindWindowByName('tipord').GetSelection()
        rptname = self.rptname
        if tipord != 0:
            rptname += ' - flat'
        rpt.Report(self, db, rptname)


# ------------------------------------------------------------------------------


class FatturatoProCliFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE_FATTPC
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(FatturatoProCliPanel(self))
        self.CenterOnScreen()
