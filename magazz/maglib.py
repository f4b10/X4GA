#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/maglib.py
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
import awc.util as awu
import awc.controls.dbgrid as dbglib

import magazz
import magazz.dbtables as dbm


class GridTable(dbglib.DbGridTable):
    
    def __init__(self, *args, **kwargs):
        dbglib.DbGridTable.__init__(self, *args, **kwargs)
        self.dbmov = None
    
    def GetDataValue(self, row, col, gridcols=False):
        mov = self.dbmov
        rscol = self.rsColumns[col]
        rsmov = mov.GetRecordset()
        if row >= len(rsmov):
            try:
                out = dbglib.DbGridTable.GetDataValue(self, row, col, gridcols)
            except Exception, e:
                out = ''
        else:
            if   rscol == -1: # qta evasa
                out = rsmov[row][mov._GetFieldIndex('total_evas_qta')] or 0
            elif rscol == -2: # qta residua
                if rsmov[row][mov._GetFieldIndex('f_ann')]:# or rsmov[row][mov._GetFieldIndex('qta',inline=True)]:
                    out = 0
                else:
                    out = (rsmov[row][mov._GetFieldIndex('qta')] or 0)\
                        -( rsmov[row][mov._GetFieldIndex('total_evas_qta')] or 0)
            else:
                out = dbglib.DbGridTable.GetDataValue(self, row, col, gridcols)
        return out


# ------------------------------------------------------------------------------


class GridMov(object):
    
    def __init__(self, dlg):
        object.__init__(self)
        self.dlg = dlg
        self.dbmov = None
        self.gridmov = None
    
    def PostInit(self):
        self.gridmov.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc)
    
    def OnCallDoc(self, event):
        row = event.GetRow()
        dbmov = self.dbmov
        if 0 <= row < dbmov.RowsCount():
            dbmov.MoveRow(row)
            if magazz.CheckPermUte(dbmov.doc.id_tipdoc, 'leggi'):
                wait = awu.WaitDialog(self.dlg, 
                                      message="Caricamento documento in corso")
                try:
                    Dialog = magazz.GetDataentryDialogClass()
                    dlg = Dialog(self.dlg)
                    dlg.SetOneDocOnly(dbmov.doc.id)
                    dlg.CenterOnScreen()
                finally:
                    wait.Destroy()
                r = dlg.ShowModal()
                if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                    self.UpdateMov()
                    if r == magazz.DOC_MODIFIED:
                        self.gridmov.SelectRow(row)
                dlg.Destroy()
        event.Skip()
    
    def UpdateMov(self, retrieve=True):
        
        cn = lambda x: self.dlg.FindWindowByName(x)
        
        mov = self.dbmov
        mov.ClearFilters()
        order = dbm.adb.ORDER_ASCENDING
        c = cn('ordinv')
        if c:
            if c.GetValue():
                order = dbm.adb.ORDER_DESCENDING
        to = cn('tipord')
        if to is None:
            to = "D"
        else:
            to = cn('tipord').GetValue()
            
        mov.ClearOrders()
        if to == 'D':
            #ordinamento per data, tipodoc, numero
            mov.AddOrder('doc.datreg',    order)
            mov.AddOrder('tipdoc.codice', order)
            mov.AddOrder('doc.datdoc',    order)
            mov.AddOrder('doc.numdoc',    order)
            mov.AddOrder('mov.numriga')
        elif to == 'A':
            #ordinamento per anagrafica, data, tipodoc, numero
            mov.AddOrder('pdc.descriz',   order)
            mov.AddOrder('doc.datreg',    order)
            mov.AddOrder('tipdoc.codice', order)
            mov.AddOrder('doc.datdoc',    order)
            mov.AddOrder('doc.numdoc',    order)
            mov.AddOrder('mov.numriga')
        elif to == 'T':
            #tipodoc, anno, numero
            mov.AddOrder('tipdoc.codice',    order)
            mov.AddOrder('YEAR(doc.datreg)', order)
            mov.AddOrder('doc.numdoc',       order)
            mov.AddOrder('mov.numriga')
        elif to == 'X':
            #ordinamento per tipodoc, anagrafica, anno, numero
            mov.AddOrder('tipdoc.codice',    order)
            mov.AddOrder('pdc.descriz',   order)
            mov.AddOrder('YEAR(doc.datreg)', order)
            mov.AddOrder('doc.numdoc',       order)
            mov.AddOrder('mov.numriga')
        
        for tab, name in (("doc", "id_magazz"),\
                          ("doc", "id_tipdoc"),\
                          ("doc", "id_pdc"),\
                          ("doc", "id_agente"),\
                          ("mov", "id_prod"),\
                          ("mov", "id_tipmov"),\
                          ("mov", "id_aliqiva"),\
                          ):
            ctr = cn("mas%s" % name)
            if ctr:
                val = ctr.GetValue()
                if val is not None:
                    if tab:
                        name = "%s.%s" % (tab, name)
                    mov.AddFilter("%s=%%s" % name, val)
        
        #filtro descrizione
        c = cn('masdescriz')
        if c:
            val = c.GetValue()
            if val:
                val = '%%%s%%' % val.replace('..', r'%')
                mov.AddFilter("mov.descriz LIKE %s", val)
        
        if cn('escdocacq').GetValue():
            mov.AddFilter('doc.f_acq IS NULL OR doc.f_acq<>1')
        if cn('escdocann').GetValue():
            mov.AddFilter('(doc.f_ann IS NULL OR doc.f_ann<>1)')
        if cn('escmovann').GetValue():
            mov.AddFilter('(mov.f_ann IS NULL OR mov.f_ann<>1)')
        
        for name in ("num", "dat"):
            for tipo in ("doc", "reg", "rif"):
                for estr in '12':
                    if estr == '1': oper = ">="
                    else:           oper = "<="
                    field = "mas%s%s%s" % (name, tipo, estr)
                    val = cn(field).GetValue()
                    if val:
                        field = "doc.%s%s" % (name, tipo)
                        mov.AddFilter("%s%s%%s" % (field, oper), val)
        
        c = cn('soloprmanca')
        if c:
            if c.IsChecked():
                mov.AddFilter('tipmov.askvalori IN ("T", "V") AND (mov.importo IS NULL OR mov.importo=0)')
        
        if retrieve:
            
            if not mov.Retrieve():
                awu.MsgDialog(self.gridmov, message=repr(mov.GetError()))
            
            self.GridMovUpdate()
    
    def GridMovUpdate(self):
        
        mov = self.dbmov
        self.gridmov.ChangeData(mov.GetRecordset())
        
        cols = {}
        filt = {}
        tots = {}
        flds = []
        for field, cond in (("importo",  lambda tipo: True),
                            ("impmerce", lambda tipo: tipo == "M"),
                            ("impspese", lambda tipo: tipo == "S"),
                            ("impservi", lambda tipo: tipo == "V"),
                            ("imptrasp", lambda tipo: tipo == "T"),
                            ("impscrip", lambda tipo: tipo == "I"),
                            ("impscmce", lambda tipo: tipo == "E"),
                            ("impomagg", lambda tipo: tipo == "O")):
            flds.append(field)
            filt[field] = cond
            cols[field] = mov._GetFieldIndex(field, inline=True)
            tots[field] = 0
        cols['tipcol'] = mov.tipmov._GetFieldIndex('tipologia', inline=True)
        
        def Totalizza(r):
            tipo = r[cols['tipcol']]
            if tipo is not None:
                for field in flds:
                    if filt[field](tipo):
                        imp = r[cols['importo']] or 0
                        if field == 'importo' and tipo in 'IE':
                            imp *= -1
                        tots[field] += imp
        
        wx.BeginBusyCursor()
        map(Totalizza, mov.GetRecordset())
        wx.EndBusyCursor()
        
        mov._info.tots = tots
        
        for field in tots:
            ctr = self.dlg.FindWindowByName('tot%s' % field)
            if ctr:
                ctr.SetValue(tots[field])
        self.dlg.FindWindowByName('totnummov').SetValue(mov.RowsCount())
    
    def GridMovOnUpdateFilters(self, event):
        self.UpdateMov()
        event.Skip()


# ------------------------------------------------------------------------------


class GridMovEva(object):
    
    def __init__(self, dlg):
        object.__init__(self)
        self.dlg = dlg
        self.dbmov = None
        self.gridmov = None
    
    def UpdateMov(self):
        
        cn = lambda x: self.dlg.FindWindowByName(x)
        
        mov = self.dbmov
        mov.ClearFilters()
        
        for tab, name in (("doc", "id_magazz"),\
                          ("doc", "id_tipdoc"),\
                          ("doc", "id_pdc"),\
                          ("doc", "id_agente"),\
                          ("mov", "id_prod"),\
                          ("mov", "id_tipmov"),\
                          ("mov", "id_aliqiva"),\
                          ):
            ctr = cn("mas%s" % name)
            if ctr:
                val = ctr.GetValue()
                if val is not None:
                    if tab:
                        name = "%s.%s" % (tab, name)
                    mov.AddFilter("%s=%%s" % name, val)
        
        if cn('escdocacq').GetValue():
            mov.AddFilter('doc.f_acq IS NULL OR doc.f_acq<>1')
        if cn('escdocann').GetValue():
            mov.AddFilter('(doc.f_ann IS NULL OR doc.f_ann<>1)')
        if cn('escmovann').GetValue():
            mov.AddFilter('(mov.f_ann IS NULL OR mov.f_ann<>1)')
        
        for name in ("num", "dat"):
            for tipo in ("doc", "reg", "rif"):
                for estr in '12':
                    if estr == '1': oper = ">="
                    else:           oper = "<="
                    field = "mas%s%s%s" % (name, tipo, estr)
                    val = cn(field).GetValue()
                    if val:
                        field = "doc.%s%s" % (name, tipo)
                        mov.AddFilter("%s%s%%s" % (field, oper), val)
        
        mov.ClearHavings()
        if True:#cn('moveva').GetSelection() == 1:
            filt = []
            for name, cond in (
                ('evaparz',   '(total_evas_qta>0 AND total_evas_qta<mov.qta)'),
                ('evachiusi', '(total_evas_qta=mov.qta OR count_evas_movim>=1)'),
                ('evanone',   '((total_evas_qta IS NULL OR total_evas_qta=0) AND (NOT count_evas_movim))')):
                if cn(name).GetValue():
                    filt.append(cond)
            if filt:
                filt = '(mov.f_ann IS NULL OR mov.f_ann=0) AND (%s)'\
                     % ' OR '.join(filt)
            else:
                filt = 'FALSE'
            mov.AddHaving(filt)
        
        wx.BeginBusyCursor()
        try:
            if not mov.Retrieve():
                awu.MsgDialog(self.gridmov, message=repr(mov.GetError()))
        finally:
            wx.EndBusyCursor()
        self.GridMovUpdate()
    
    def GridMovUpdate(self):
        
        mov = self.dbmov
        self.gridmov.ChangeData(mov.GetRecordset())
        
        cols = {}
        for field in\
            ("qta", "prezzo", "importo",
             "total_evas_qta", "total_evas_importo", 
             "total_resid_qta", "total_resid_importo"):
            cols[field] = mov._GetFieldIndex(field, inline=True)
        cols['doc.f_ann'] = mov.doc._GetFieldIndex("f_ann", inline=True)
        
        tots = {}
        for tipo in ("doc", "acq", "res"):
            for col in "qv":
                name = "mastot%s%s" % (tipo, col)
                tots[name] = 0
        
        def Totalizza(r):
            docqta = r[cols['qta']] or 0
            docimp = r[cols['importo']] or 0
            evaqta = r[cols['total_evas_qta']] or 0
            evaimp = r[cols['total_evas_importo']] or 0
            name = "mastotdoc" #qta,importo su movimento
            tots["%sq" % name] += docqta
            tots["%sv" % name] += docimp
            name = "mastotacq" #qta,importo evasi su totale evasione
            tots["%sq" % name] += evaqta
            tots["%sv" % name] += evaimp
            name = "mastotres" #qta,importo,lordo evasi su totale evasione
            tots["%sq" % name] += docqta-evaqta
            tots["%sv" % name] += docimp-evaimp
        
        wx.BeginBusyCursor()
        map(Totalizza, mov.GetRecordset())
        wx.EndBusyCursor()
        
        mov._info.tots = tots
        
        for name, val in tots.iteritems():
            ctr = self.dlg.FindWindowByName(name)
            ctr.SetValue(val)
        self.dlg.FindWindowByName('mastotnummov').SetValue(mov.RowsCount())
    
    def GridMovOnUpdateFilters(self, event):
        self.UpdateMov()
        event.Skip()
