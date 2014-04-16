#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/reddvend.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
# Copyright:    (C) 2012 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
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
import awc.controls.dbgrid as dbgrid

import anag.dbtables as dba
import magazz.dbtables as dbm
import magazz.stat.dbtables as dbs

import magazz.stat.stat_wdr as wdr

adb  = dba.adb
samefloat = adb.DbTable.samefloat

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab
NI = 6#bt.VALINT_INTEGERS
ND = bt.VALINT_DECIMALS

import report as rpt


FRAME_TITLE_FATT = "Redditività vendite"


class ReddVendGrid(dbgrid.ADB_Grid):
    
    def __init__(self, parent, dbred):
        
        self.dbtic = red = dbred
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbred, can_edit=True, on_menu_select='row')
        
        AC = self.AddColumn
        AC(dbred, 'causale', label='Causale', col_width=150)
        AC(dbred, 'doc_numero', label='Num.', col_type=self.TypeInteger(5))
        AC(dbred, 'doc_data', label='Data', col_type=self.TypeDate())
        AC(dbred, 'cliente_cod', label='Cod.', col_width=50)
        AC(dbred, 'cliente', label='Cliente', col_width=250, is_fittable=True)
        AC(dbred, 'ricavo', label='Ricavo', col_type=self.TypeFloat(NI, ND))
        AC(dbred, 'costo', label='Costo', col_type=self.TypeFloat(NI, ND))
        AC(dbred, 'utile', label='Utile', col_type=self.TypeFloat(NI, ND))
        AC(dbred, 'ricarica', label='%Ricar', col_type=self.TypeFloat(4,2))
        AC(dbred, 'margine', label='%Marg', col_type=self.TypeFloat(4,2))
        AC(dbred, 'doc_id', label='#doc', col_width=1)
        AC(dbred, 'cliente_id', label='#pdc', col_width=1)
        
        self.CreateGrid()


class ReddVendPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ReddVendFunc(self)
        cn = self.FindWindowByName
        self.dbtic = dbs.ReddVend()
        self.gridred = ReddVendGrid(cn('pangridven'), self.dbtic)
        for name, func in (('butupd', self.OnUpdateData),
                           ('butprt', self.OnPrintData),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        cn = self.FindWindowByName
        d1, d2 = map(lambda x: cn(x).GetValue(), 'data1 data2'.split())
        red = self.dbtic
        red.ClearFilters()
        if d1:
            red.AddFilter("doc_data>=%s", d1)
        if d2:
            red.AddFilter("doc_data<=%s", d2)
        wx.BeginBusyCursor()
        try:
            red.Retrieve()
            totric, totcos = red.GetTotalOf(((red, 'ricavo'),
                                             (red, 'costo'),))
            i = red._info
            i._totali = t = {}
            t['totric'] = totric = totric or 0
            t['totcos'] = totcos = totcos or 0
            t['totuti'] = totric-totcos
            if totric:
                t['prcmar'] = prcmar = 100*(totric-totcos)/totric
            else:
                t['prcmar'] = prcmar = 100
            if totcos:
                t['prcric'] = prcric = 100*(totric-totcos)/totcos
            else:
                t['prcric'] = prcric = 100
            cn('totricavo').SetValue(totric)
            cn('totcosto').SetValue(totcos)
            cn('totutile').SetValue(totric-totcos)
            cn('prcmar').SetValue(prcmar)
            cn('prcric').SetValue(prcric)
        finally:
            wx.EndBusyCursor()
        self.gridred.ChangeData(red.GetRecordset())
    
    def OnPrintData(self, event):
        self.PrintData()
        event.Skip()
    
    def PrintData(self):
        rpt.Report(self, self.dbtic, "Redditivita' vendite")


# ------------------------------------------------------------------------------


class ReddVendFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE_FATT
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ReddVendPanel(self))
        self.CenterOnScreen()
