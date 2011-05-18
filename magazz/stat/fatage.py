#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/fatage.py
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

import magazz.stat.fatpdc as fatpdc


FRAME_TITLE_FATT = "Fatturato Agenti"


class FatturatoAgentiGrid(fatpdc._FatturatoVenditeGrid):
    
    def GetColDef(self):
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _VAL = bt.GetValIntMaskInfo()
        
        mov = self.dbfat
        age = mov.doc.agente
        
        return (\
            ( 60, (cn(age, 'codice'),           "Cod.",      _STR, False)),
            (220, (cn(age, 'descriz'),          "Agente",    _STR, False)),
            (110, (cn(mov, 'total_statvalfat'), "Fatturato", _VAL, False)),
            (  1, (cn(age, 'id'),               "#age",      _STR, False)),
        )
    
    def SetTotali(self):
        def cn(col):
            return self.dbfat._GetFieldIndex(col)
        self.AddTotalsRow(1, 'Totali', (cn('total_statvalfat'),))


# ------------------------------------------------------------------------------


class FatturatoAgentiPanel(fatpdc.FatturatoClientiPanel):
    
    rptname = "Fatturato Agenti"
    
    def SetOrder(self):
        tipord = self.FindWindowByName('tipord').GetSelection()
        f = self.dbfat
        f.ClearOrders()
        if tipord == 0: # per categoria
            f.AddOrder('agente.codice')
        elif tipord == 1: #per fatturato, da 0
            f.AddOrder('(total_statvalfat)', adb.ORDER_ASCENDING)
        elif tipord == 2: #per fatturato, dal massimo
            f.AddOrder('(total_statvalfat)', adb.ORDER_DESCENDING)
    
    def InitTableFatt(self):
        self.dbfat = dbs.FatturatoAgenti()
        self.dbfat.ShowDialog(self)
    
    def InitGrid(self):
        self.gridfat = FatturatoAgentiGrid(self.FindWindowByName('pangridfat'), 
                                           self.dbfat)


# ------------------------------------------------------------------------------


class FatturatoAgentiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE_FATT
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(FatturatoAgentiPanel(self))
        self.CenterOnScreen()
