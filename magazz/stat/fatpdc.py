#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/fatpdc.py
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

import report as rpt


FRAME_TITLE_FATT = "Fatturato clienti"
FRAME_TITLE_FATTCC = "Fatturato clienti/categoria prodotto"


class _FatturatoVenditeGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbfat):
        
        self.dbfat = dbfat
        
        coldef = self.GetColDef()
        sizes =  [c[0] for c in coldef]
        colmap = [c[1] for c in coldef]
        
        canedit = True
        canins = False
        
        dbglib.DbGridColoriAlternati.__init__(self, 
                                              parent, 
                                              size=parent.GetClientSizeTuple())
        
        self.SetData(dbfat.GetRecordset(), colmap, canedit, canins)
        
        self.SetTotali()
        
        #self.SetCellDynAttr(self.GetAttr)
        for c,s in enumerate(sizes):
            self.SetColumnDefaultSize(c,s)
        self._SetFitColumn()
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def _SetFitColumn(self):
        self.SetFitColumn(1)
    
    def GetColDef(self):
        raise Exception, 'Classe non istanziabile'
    
    def ResetView(self):
        dbglib.DbGridColoriAlternati.ResetView(self)
        db = self.dbfat
        rs = db._info.rs
        def cn(c):
            return db._GetFieldIndex(c, inline=True)
        cq, ci = map(lambda c: cn(c), 
                     'total_statqtafat total_statvalfat'.split())
        tq = ti = 0
        for r in range(db.RowsCount()):
            tq += rs[r][cq] or 0
            ti += rs[r][ci] or 0
        db._info.totqta = tq
        db._info.totval = ti


# ------------------------------------------------------------------------------


class _FatturatoVenditePanel(aw.Panel):
    
    dbfat = None
    rptname = None
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.InitControls()
        def cn(x):
            return self.FindWindowByName(x)
        today = Env.Azienda.Login.dataElab
        cn('datreg1').SetValue(Env.DateTime.Date(today.year,1,1))
        cn('datreg2').SetValue(today)
        self.InitTableFatt()
        self.InitGrid()
        for name, func in (('btnok', self.OnUpdate),
                           ('btnprint', self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, self.FindWindowByName(name))
    
    def OnUpdate(self, event):
        raise Exception, 'Classe non istanziabile'
    
    def InitTableFatt(self, event):
        raise Exception, 'Classe non istanziabile'
    
    def UpdateData(self, db, grid):
        db.Reset()
        grid.ResetView()
        def cn(x):
            return self.FindWindowByName(x)
        f = db
        f.ClearFilters()
        #filtro anagrafica
        for n,s in ((1, '>='),
                    (2, '<=')):
            col = 'pdc%d' % n
            val = cn(col).GetValueDes()
            if val:
                f.AddFilter('pdc.descriz%s%%s' % s, val)
        #filtro prodotto
        for n,s in ((1, '>='),
                    (2, '<=')):
            col = 'codart%d' % n
            val = cn(col).GetValue()
            if val:
                f.AddFilter('prod.codice%s%%s' % s, val)
        #filtri su classificazioni anagrafica e prodotto
        for tab, cols in (('pdc', 'agente,catana'),
                          ('pro', 'tipart,catart,gruart,statart')):
            for name in cols.split(','):
                for n,s in ((1, '>='),
                            (2, '<=')):
                    col = '%s%d' % (name, n)
                    val = cn(col).GetValueCod()
                    if val:
                        f.AddFilter('%s.codice%s%%s' % (name, s), val)
        db._info.datmin = db._info.datmax = None
        #filtro periodo
        for n,s in ((1, '>='),
                    (2, '<=')):
            col = 'datreg%d' % n
            val = cn(col).GetValue()
            if val:
                f.AddFilter('doc.datreg%s%%s' % s, val)
                if n == 1:
                    db._info.datmin = val
                else:
                    db._info.datmax = val
        spc = cn('soloprod').GetValue()
        if spc:
            db.AddFilter('prod.id IS NOT NULL')
        f.ClearHavings()
        fatmin, fatmax = map(lambda x: cn(x).GetValue(), 
                             'fatmin fatmax'.split())
        if fatmin:
            f.AddHaving('total_statvalfat>=%s', fatmin)
        if fatmax:
            f.AddHaving('total_statvalfat<=%s', fatmax)
        self.SetOrder()
        f.Retrieve()
        grid.ResetView()
    
    def SetOrder(self):
        tipord = self.FindWindowByName('tipord').GetSelection()
        f = self.dbfat
        f.ClearOrders()
        if tipord == 0: # per anagrafica
            f.AddOrder('pdc.descriz')
        elif tipord == 1: #per fatturato, da 0
            f.AddOrder('(total_statvalfat)', adb.ORDER_ASCENDING)
        elif tipord == 2: #per fatturato, dal massimo
            f.AddOrder('(total_statvalfat)', adb.ORDER_DESCENDING)
    
    def OnPrint(self, event):
        db = self.dbfat
        rpt.Report(self, db, self.rptname)


# ------------------------------------------------------------------------------


class FatturatoClientiGrid(_FatturatoVenditeGrid):
    
    def GetColDef(self):
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _VAL = bt.GetValIntMaskInfo()
        
        mov = self.dbfat
        pdc = mov.doc.pdc
        
        return (\
            ( 60, (cn(pdc, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(pdc, 'descriz'),          "Cliente",   _STR, False)),
            (110, (cn(mov, 'total_statvalfat'), "Fatturato", _VAL, False)),
            (  1, (cn(pdc, 'id'),               "#cli",      _STR, False)),
        )
    
    def SetTotali(self):
        def cn(col):
            return self.dbfat._GetFieldIndex(col)
        self.AddTotalsRow(1, 'Totali', (cn('total_statvalfat'),))


# ------------------------------------------------------------------------------


class FatturatoClientiPanel(_FatturatoVenditePanel):
    
    rptname = "Fatturato Clienti"
    
    def InitControls(self):
        wdr.SetClienti()
        wdr.FatturatoPdcFunc(self)
    
    def InitTableFatt(self):
        self.dbfat = dbs.FatturatoClienti()
        self.dbfat.ShowDialog(self)
    
    def InitGrid(self):
        self.gridfat = FatturatoClientiGrid(self.FindWindowByName('pangridfat'), 
                                            self.dbfat)
    
    def OnUpdate(self, event):
        self.UpdateData(self.dbfat, self.gridfat)
        event.Skip()


# ------------------------------------------------------------------------------


class FatturatoClientiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE_FATT
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(FatturatoClientiPanel(self))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class FatturatoCliCatArtGrid(_FatturatoVenditeGrid):
    
    def GetColDef(self):
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _VAL = bt.GetValIntMaskInfo()
        
        mov = self.dbfat
        pdc = mov.doc.pdc
        cat = mov.prod.catart
        
        return (\
            ( 60, (cn(pdc, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(pdc, 'descriz'),          "Cliente",   _STR, False)),
            ( 60, (cn(cat, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(cat, 'descriz'),          "Categoria", _STR, False)),
            (110, (cn(mov, 'total_statvalfat'), "Fatturato", _VAL, False)),
            (  1, (cn(pdc, 'id'),               "#cli",      _STR, False)),
            (  1, (cn(cat, 'id'),               "#cat",      _STR, False)),
        )
    
    def SetTotali(self):
        def cn(col):
            return self.dbfat._GetFieldIndex(col)
        self.AddTotalsRow(1, 'Totali', (cn('total_statvalfat'),))


# ------------------------------------------------------------------------------


class FatturatoCliCatArtPanel(_FatturatoVenditePanel):
    
    rptname = "Fatturato Clienti per Categoria prodotto"
    
    def InitControls(self):
        wdr.SetClienti()
        wdr.FatturatoPdcFunc(self)
    
    def InitTableFatt(self):
        self.dbfat = dbs.FatturatoCliCatArt()
        self.dbfat.ShowDialog(self)
    
    def InitGrid(self):
        self.gridfat = FatturatoCliCatArtGrid(self.FindWindowByName('pangridfat'), 
                                              self.dbfat)
    
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


class FatturatoCliCatArtFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE_FATTCC
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(FatturatoCliCatArtPanel(self))
        self.CenterOnScreen()
