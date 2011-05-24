#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/chiusure/genmov.py
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
from awc.controls.datectrl import EVT_DATECHANGED

import magazz.chiusure.chiusure_wdr as wdr

import stormdb as adb
import magazz.chiusure.dbtables as dbx

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLE = "Generazione movimenti apertura giacenze"


class GeneraMovimentiGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbriep):
        
        self.dbriep = dbriep
        
        def cc(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        rie = self.dbriep
        mag = rie.magazz
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _FLV = bt.GetValIntMaskInfo()
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        
        cols = []
        self.edcols = []
        def a(x, edc=False):
            cols.append(x)
            n = len(cols)-1
            if edc:
                self.edcols.append(n)
            return n
        def b(x):
            return a(x, True)
        
        a(( 35, (cc(rie, "mag_codice"),       "Cod.",         _STR, True)))
        a((120, (cc(rie, "mag_descriz"),      "Magazzino",    _STR, True)))
        a(( 60, (cc(rie, "count_prodotti"),   "Prodotti",     _NUM, True)))
        a((110, (cc(rie, "total_qtagia"),     "Tot.Giacenza", _QTA, True)))
        a((120, (cc(rie, "total_valgia"),     "Tot.Valore",   _FLV, True)))
        a(( 60, (cc(rie, "count_prod_noval"), "No Val.",      _NUM, True)))
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        self.SetData(rie.GetRecordset(), colmap, canedit, canins)
        
        self.AddTotalsRow(1,'Totali:',(cc(rie, "total_qtagia"),
                                       cc(rie, "total_valgia"),
                                       cc(rie, "count_prod_noval")))
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
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        return attr
    
    def ChangeDbRiep(self, dbriep):
        self.dbriep = dbriep
        self.ChangeData(dbriep.GetRecordset())


# ------------------------------------------------------------------------------


class GeneraMovimentiPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        
        wx.Panel.__init__(self, *args, **kwargs)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        self.dbaut = dbx.ChiusAutomTable()
        
        wdr.GeneraMovimentiFunc(self)
        riep = dbx.RiepilogoGiacenzeTable(anno=None, tipval="U")
        self.gridriep = GeneraMovimentiGrid(cn('pangridriep'), riep)
        
        self.id_tipdoc = self.dbaut.GetDocumento()
        self.id_tipmov = self.dbaut.GetMovimento()
        
        cn('id_tipdoc').SetValue(self.id_tipdoc)
        cn('id_tipmov').SetValue(self.id_tipmov)
        
        def CheckDocMov(self):
            msg = None
            if self.id_tipdoc is None:
                msg = "Documento"
            elif self.id_tipmov is None:
                msg = "Movimento"
            if msg:
                msg = """Manca la definizione del tipo di %s.\n"""\
                      """Controllare gli automatismi di magazzino""" % msg
                aw.awu.MsgDialog(self, msg, style=wx.ICON_ERROR)
                aw.awu.GetParentFrame(self).Close()
                return False
            return True
        
        self.TestAnno()
        
        self.Bind(wx.EVT_CHOICE, self.OnAnnoChanged, cn('anno'))
        self.Bind(EVT_DATECHANGED, self.OnDatDocChanged, cn('datdoc'))
        self.Bind(wx.EVT_BUTTON, self.OnEstraiRiep, cn('btnstart'))
        self.Bind(wx.EVT_BUTTON, self.OnGeneraMov,  cn('btngenmov'))
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnOpenGiac, self.gridriep)
        
        wx.CallAfter(lambda: CheckDocMov(self))
    
    def OnDatDocChanged(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        datdoc = cn('datdoc').GetValue()
        if datdoc is None:
            return
        anno = datdoc.year
        doc = adb.DbTable(bt.TABNAME_MOVMAG_H, 'doc', fields=None)
        doc.Synthetize()
        doc.AddMaximumOf('numdoc')
        doc.AddFilter("id_tipdoc=%s", self.id_tipdoc)
        doc.AddFilter("YEAR(datdoc)=%s", anno)
        doc.Retrieve()
        lastnd = doc.max_numdoc or 0
        cn('numdoc').SetValue(lastnd+1)
        event.Skip()
    
    def TestAnno(self):
        def cn(x):
            return self.FindWindowByName(x)
        anno = cn('anno').GetSelectedAnno()
        if anno is not None:
            cn('datdoc').SetValue(Env.DateTime.Date(anno+1, 1, 1))
    
    def OnAnnoChanged(self, event):
        self.TestAnno()
        event.Skip()
    
    def OnGeneraMov(self, event):
        if self.GeneraMovimenti():
            event.Skip()
    
    def GeneraMovimenti(self):
        def cn(x):
            return self.FindWindowByName(x)
        riep = self.gridriep.dbriep
        if not riep.TestMagazzini():
            aw.awu.MsgDialog(self, "Sottoconto non definito su uno o più magazzini.\nControllare la configurazione dei magazzini.",
                             style=wx.ICON_ERROR)
            return False
        datdoc, numdoc, tipval = map(lambda x: cn(x).GetValue(), 
                                     'datdoc numdoc tipval'.split())
        msg = None
        if not datdoc:
            msg = "Definire la data documento"
        elif not numdoc:
            msg = "Definire il numero documento"
        if msg:
            aw.awu.MsgDialog(self, msg, style=wx.ICON_ERROR)
            return False
        msg = "Confermi la generazione dei movimenti?"
        if aw.awu.MsgDialog(self, msg, 
                            style=wx.ICON_QUESTION
                            |wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
            return False
        w = aw.awu.WaitDialog(self, maximum=riep.GetTotalOf("count_prodotti"))
        def Title(m):
            w.SetMessage('Creazione giacenze del magazzino %s' % m.codice)
        def Progr(n):
            w.SetValue(n)
        try:
            try:
                g = riep.GeneraMovimenti(self.id_tipdoc, self.id_tipmov, 
                                         datdoc, numdoc, tipval, 
                                         func=Progr, func0=Title)
            except Exception, e:
                aw.awu.MsgDialog(self, repr(e.args))
                g = False
        finally:
            w.Destroy()
        if g:
            aw.awu.MsgDialog(self, "I movimenti sono stati generati.\nProvvedere ora al ricalcolo dei progressivi.",
                             style=wx.ICON_INFORMATION)
            return True
        return False
    
    def OnOpenGiac(self, event):
        row = event.GetRow()
        col = event.GetRow()
        riep = self.gridriep.dbriep
        if 0 <= row < riep.RowsCount():
            riep.MoveRow(row)
            from magazz.chiusure.editgiac import EditGiacenzeDialog
            f = EditGiacenzeDialog(self)
            def cn(x):
                return self.FindWindowByName(x)
            def dn(x):
                return f.panel.FindWindowByName(x)
            c = dn('anno')
            c.SetValue(cn('anno').GetSelectedAnno())
            c.Disable()
            c = dn('magazz')
            c.SetValue(riep.mag_id)
            c.Disable()
            c = dn('tipval')
            c.SetValue(cn('tipval').GetValue())
            c.Disable()
            dn('btnestrai').Hide()
            del f.panel.gridgiac.edcols[:]
            wx.BeginBusyCursor()
            try:
                f.panel.EstraiGiac()
            finally:
                wx.EndBusyCursor()
            f.ShowModal()
            f.Destroy()
    
    def OnEstraiRiep(self, event):
        self.EstraiRiepilogo()
        b = self.FindWindowByName('btngenmov')
        b.Enable(not self.gridriep.dbriep.IsEmpty())
        event.Skip()
    
    def EstraiRiepilogo(self):
        def cn(x):
            return self.FindWindowByName(x)
        anno = cn('anno').GetSelectedAnno()
        if anno is None:
            aw.awu.MsgDialog(self, "Anno inconsistente")
            return False
        tipval = cn('tipval').GetValue()
        wx.BeginBusyCursor()
        try:
            riep = dbx.RiepilogoGiacenzeTable(anno=anno, tipval=tipval)
            self.gridriep.ChangeDbRiep(riep)
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


class GeneraMovimentiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GeneraMovimentiPanel(self))
        self.CenterOnScreen()
        def cn(x):
            return self.FindWindowByName(x)
        self.Bind(wx.EVT_BUTTON, self.OnGeneraMov,  cn('btngenmov'))
    
    def OnGeneraMov(self, event):
        self.Close()
