#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/chiusure/editgiac.py
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
import magazz.chiusure.chiusure_wdr as wdr

import anag.lib as alib
import awc.controls.dbgrideditors as gred
from anag.prod import ProdDialog

import Env
bt = Env.Azienda.BaseTab

import magazz.chiusure.dbtables as dbx
import stormdb as adb

import report as rpt


EDITGIAC_TITLE = "Manutenzione giacenze rilevate"


class ProdottoHelperEditor(alib.DataLinkProdCellEditor):
    
    qtacol = 3
    def SetQtaCol(self, qc):
        self.qtacol = qc
    
    def EndEdit(self, row, col, grid):
        if not self.editing:
            return
        if self._tc._helpInProgress:
            self.Show(0)
        changed = False
        rel_id = self._tc.GetValue()
        relcod = self._tc.GetValueCod()
        reldes = self._tc.GetValueDes()
        if rel_id != self.startValue:
            table = grid.GetTable()
            try:
                r = aw.awu.ListSearch(table.data, lambda x: x[grid.proidcol] == rel_id)
                def Muovi():
                    grid.MakeCellVisible(r, self.qtacol)
                    grid.SetGridCursor(r, self.qtacol)
                wx.CallAfter(Muovi)
            except IndexError:
                pass
        self.editing = False
        self.startValue = None
        return changed


# ------------------------------------------------------------------------------


class DescrizCellEditor(gred.TextCellEditor):
    
    qtacol = 0
    def SetQtaCol(self, qc):
        self.qtacol = qc
    
    def EndEdit(self, row, col, grid):
        """
        Complete the editing of the current cell. Returns True if the value
        has changed.  If necessary, the control may be destroyed.
        *Must Override*
        """
        if not self.editing:
            return
        changed = False
        val = self._tc.GetValue()
        if val != self.startValue:
            table = grid.GetTable()
            try:
                r = aw.awu.ListSearch(table.data, lambda x: (x[grid.descrizcol] or '').startswith(val.lstrip()))
                def Muovi():
                    grid.MakeCellVisible(r, self.qtacol)
                    grid.SetGridCursor(r, self.qtacol)
                wx.CallAfter(Muovi)
            except IndexError:
                pass
        self.editing = False
        self.startValue = None
        return changed


# ------------------------------------------------------------------------------


_evtUPDATETOTALS = wx.NewEventType()
EVT_UPDATETOTALS = wx.PyEventBinder(_evtUPDATETOTALS, 0)

class UpdateTotalsEvent(wx.PyCommandEvent):
    totqtacon = None
    totvalcon = None
    totqtafis = None
    totvalfis = None


# ------------------------------------------------------------------------------


class EditGiacenzeGrid(dbglib.DbGridColoriAlternati):
    
    id_magazz = None
    anno = None
    
    def __init__(self, parent, dbpro, tipval):
        
        self.dbpro = dbpro
        self.dbcos = adb.DbTable(bt.TABNAME_PROCOS, 'procos')
        self.dbgia = adb.DbTable(bt.TABNAME_PROGIA, 'progia')
        self.tipval = tipval
        
        def cc(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        pro = self.dbpro
        cst = pro.procos
        gia = pro.progia
        mag = gia.magazz
        
        self.proidcol = cc(pro, 'id')
        self.descrizcol = cc(pro, 'descriz')
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
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
        
        self.COL_procod = b(( 80, (cc(pro, "codice"),  "Codice",         _STR, True)))
        self.COL_prodes = b((200, (cc(pro, "descriz"), "Prodotto",       _STR, True)))
        self.COL_GIACON = a((110, (cc(gia, "giacon"),  "Giac.Contabile", _QTA, True)))
        
        self.rscqtafis = cc(gia, "giafis")
        self.COL_GIAFIS = b((110, (self.rscqtafis,     "Giac.Rilevata",  _QTA, True)))
        
        if tipval == "U":
            self.rscvaluni = cc(cst, "costou")
            self.COL_VALUNI = b((110, (self.rscvaluni, "Costo Ult.",     _PRZ, True)))
        elif tipval == "M":
            self.rscvaluni = cc(cst, "costom")
            self.COL_VALUNI = b((110, (self.rscvaluni, "Costo Medio",    _PRZ, True)))
        
        self.COL_VALORE =     a((120, (-1,             "Valore",         _FLV, True)))
        
        self.COL_ID_GIA = a((  1, (cc(gia, "id"),      "#gia",           _STR, True)))
        self.COL_ID_PRO = a((  1, (cc(pro, "id"),      "#pro",           _STR, True)))
        self.COL_ID_MAG = a((  1, (cc(mag, "id"),      "#mag",           _STR, True)))
        
        class GiacGridTable(dbglib.DbGridTable):
            def GetDataValue(self, row, col):
                rs = self.data
                if col == self.grid.COL_VALORE: #colonna valore giacenze
                    g = self.grid
                    r = rs[row]
                    def gdv(c):
                        return dbglib.DbGridTable.GetDataValue(self, row, c)
                    try:
                        value = round((gdv(g.COL_GIAFIS) or 0)*(gdv(g.COL_VALUNI) or 0), 
                                      bt.VALINT_DECIMALS)
                    except:
                        value = 0
                else:
                    value = dbglib.DbGridTable.GetDataValue(self, row, col)
                return value
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              tableClass=GiacGridTable,
                                              size=parent.GetClientSizeTuple())
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        editors = []
        prod_editor = ProdottoHelperEditor(bt.TABNAME_PROD,    #table
                                           cc(pro, 'id'),      #rs col id
                                           cc(pro, 'codice'),  #rs col cod
                                           cc(pro, 'descriz'), #rs col des
                                           ProdDialog)         #card class
        editors.append((0, prod_editor))
        
        descriz_editor = DescrizCellEditor()
        descriz_editor.SetQtaCol(1)#self.COL_GIAFIS)
        editors.append((1, descriz_editor))
        
        afteredit = []
        afteredit.append((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.EditedValues))
        
        self.SetData(gia.GetRecordset(), colmap, canedit, canins, 
                     afterEdit=afteredit, editors=editors)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetColumnsFunc(self.MoveColumnAfterEdit)
        self.SetColDefault(0)
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def MoveColumnAfterEdit(self, grid, row, col):
        pro = self.dbpro
        if 0 <= row < pro.RowsCount():
            if col in (self.COL_GIAFIS, self.COL_VALUNI):
                if row < pro.RowsCount()-1:
                    row += 1
            elif col is not None:
                col = grid.GetTable().rs2col(col)
        return row, col
    
    def SetGridCursorNewRowCol(self):
        data = self.GetTable().data
        if len(data)>0:
            row = self.GetSelectedRows()[0]
            if row < len(data)-1:
                row += 1
            col = self._coldefault
            self.SetGridCursor(row, col)
            self.MakeCellVisible(row, col)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        if 0 <= row < self.dbpro.RowsCount():
            r = self.dbpro.GetRecordset()[row]
            if r[self.rscqtafis] and not r[self.rscvaluni]:
                bgcol = Env.Azienda.Colours.VALMISS_BACKGROUND
                attr.SetBackgroundColour(bgcol)
            attr.SetReadOnly(not col in self.edcols)
        return attr
    
    def EditedValues(self, row, gridcol, col, value):
        pro = self.dbpro
        if 0 <= row < pro.RowsCount():
            pro.MoveRow(row)
            if gridcol == self.COL_GIAFIS:
                pro.progia.giafis = value
                gia = self.dbgia
                gia.Retrieve("id_prod=%d AND anno=%d AND id_magazz=%d" % (pro.id, self.anno, self.id_magazz))
                if value:
                    if gia.IsEmpty():
                        gia.CreateNewRow()
                        gia.id_prod = pro.id
                        gia.anno = self.anno
                        gia.id_magazz = self.id_magazz
                    gia.giafis = value
                else:
                    if gia.OneRow():
                        gia.Delete()
                if not gia.Save():
                    aw.awu.MsgDialog(self, repr(gia.GetError()))
            elif gridcol == self.COL_VALUNI:
                if self.tipval == "U":
                    pro.procos.costou = value
                elif self.tipval == "M":
                    pro.procos.costom = value
                cos = self.dbcos
                if cos.Retrieve("id_prod=%s AND anno=%s", pro.id, self.anno):
                    if cos.IsEmpty():
                        cos.CreateNewRow()
                        cos.id_prod = pro.id
                        cos.anno = self.anno
                        cos.id_magazz = self.id_magazz
                    if cos.OneRow():
                        if self.tipval == "U":
                            cos.costou = value
                        elif self.tipval == "M":
                            cos.costom = value
                        if not cos.Save():
                            aw.awu.MsgDialog(self, repr(cos.GetError()))
                else:
                    aw.awu.MsgDialog(self, repr(cos.GetError()))
            self.UpdateTotali()
    
    def ChangeData(self, *args):
        dbglib.DbGridColoriAlternati.ChangeData(self, *args)
        self.UpdateTotali()
    
    def UpdateTotali(self):
        t = self.GetTable()
        gdv = t.GetDataValue
        rs = self.dbpro.GetRecordset()
        tqc = tvc = tqf = tvf = 0
        ND = bt.VALINT_DECIMALS
        for n in range(len(rs)):
            q = gdv(n, self.COL_GIACON) or 0
            v = gdv(n, self.COL_VALUNI) or 0
            tqc += q
            tvc += round(q*v, ND)
            q = gdv(n, self.COL_GIAFIS) or 0
            v = gdv(n, self.COL_VALUNI) or 0
            tqf += q
            tvf += round(q*v, ND)
        e = UpdateTotalsEvent(_evtUPDATETOTALS, self.GetId())
        e.SetEventObject(self)
        e.SetId(self.GetId())
        e.totqtacon = tqc
        e.totvalcon = tvc
        e.totqtafis = tqf
        e.totvalfis = tvf
        self.GetEventHandler().AddPendingEvent(e)


# ------------------------------------------------------------------------------


class ListGiacenzePanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ListGiacenzeFunc(self)


# ------------------------------------------------------------------------------


class ListGiacenzeDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Lista giacenze rilevate"
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ListGiacenzePanel(self))
        self.Bind(wx.EVT_BUTTON, self.OnPrint, self.FindWindowByName('btnprint'))
    
    def OnPrint(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class EditGiacenzePanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.EditGiacenzeFunc(self)
        def cn(x):
            return self.FindWindowByName(x)
        self.dbpro = dbx.EditGiacenzeTable()
        self.gridgiac = EditGiacenzeGrid(cn('pangrid'), self.dbpro, "U")
        for name, func in (('btnestrai', self.OnEstrai),
                           ('btnlist', self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        self.Bind(EVT_UPDATETOTALS, self.OnUpdateTotali)
    
    def OnPrint(self, event):
        self.PrintGiac()
        event.Skip()
    
    def PrintGiac(self):
        d = ListGiacenzeDialog(self)
        if d.ShowModal() == wx.ID_OK:
            def cn(x):
                return self.FindWindowByName(x)
            def dc(x):
                return d.FindWindowByName(x)
            gia = self.dbpro
            if dc('tipoprod').GetValue() == "S":
                inv = dbx.EditGiacenzeTable(tipval=gia.GetTipVal())
                for f, p in gia._info.filters:
                    inv.AddFilter(f, *p)
                magid, anno, tpv = map(lambda x: cn(x).GetValue(), 'magazz anno tipval'.split())
                inv.AddBaseFilter("giafis IS NOT NULL AND giafis<>0")
                inv.procos.SetRelation("procos.id_prod=prod.id AND procos.anno=%d" % anno)
                inv.progia.SetRelation("progia.id_prod=prod.id AND progia.anno=%d AND progia.id_magazz=%d" % (anno, magid))
                self.GetParent().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
                try:
                    inv.Retrieve()
                finally:
                    self.GetParent().SetCursor(wx.NullCursor)
            else:
                inv = gia
            i = inv._info
            i.proval = dc('tipoval').GetValue()
            i.giacon = dc('stagcon').GetValue()
            i.tipval = cn('tipval').GetValue()
            rpt.Report(self, inv, "Lista giacenze rilevate")
        d.Destroy()
    
    def OnUpdateTotali(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        for tipo in 'con fis'.split():
            for tot in 'qta val'.split():
                name = 'tot%s%s' % (tot, tipo)
                cn(name).SetValue(getattr(event, name))
        event.Skip()
    
    def OnEstrai(self, event):
        self.EstraiGiac()
        event.Skip()
    
    def EstraiGiac(self):
        def cn(x):
            return self.FindWindowByName(x)
        magid, anno, tpv = map(lambda x: cn(x).GetValue(), 'magazz anno tipval'.split())
        if not magid:
            err = 'il magazzino'
        elif not anno:
            err = 'l\'anno'
        else:
            err = None
        if err:
            aw.awu.MsgDialog(self, "Definire %s" % err,
                             style=wx.ICON_WARNING)
            return
        try:
            self.GetParent().SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
#            self.gridgiac.Destroy()
            wx.CallAfter(self.gridgiac.Destroy)
            self.gridgiac = EditGiacenzeGrid(cn('pangrid'), self.dbpro, tpv)
            pro = self.dbpro
            pro.procos.SetRelation("procos.id_prod=prod.id AND procos.anno=%d" % anno)
            pro.progia.SetRelation("progia.id_prod=prod.id AND progia.anno=%d AND progia.id_magazz=%d" % (anno, magid))
            pro.ClearFilters()
            tg = cn('tipgiacon').GetValue()
            if tg in 'ZPN':
                if tg == 'Z':
                    pro.AddFilter('progia.giacon=0 OR progia.giacon IS NULL')
                elif tg == 'P':
                    pro.AddFilter('progia.giacon>0')
                elif tg == 'N':
                    pro.AddFilter('progia.giacon<0')
            tg = cn('tipgiafis').GetValue()
            if tg in 'ZPN':
                if tg == 'Z':
                    pro.AddFilter('progia.giafis=0 OR progia.giafis IS NULL')
                elif tg == 'P':
                    pro.AddFilter('progia.giafis>0')
                elif tg == 'N':
                    pro.AddFilter('progia.giafis<0')
            pro.ClearOrders()
            to = cn('tipord').GetValue()
            if to == "C":
                pro.AddOrder('prod.codice')
            elif to == "D":
                pro.AddOrder('prod.descriz')
            pro.Retrieve()
            pro.SetTipVal(tpv)
            grid = self.gridgiac
            grid.id_magazz = magid
            grid.anno = anno
            grid.ChangeData(pro.GetRecordset())
        finally:
            self.GetParent().SetCursor(wx.NullCursor)
        grid.SetGridCursor(0,0)


# ------------------------------------------------------------------------------


class EditGiacenzeFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = EDITGIAC_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = EditGiacenzePanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class EditGiacenzeDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = EDITGIAC_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = EditGiacenzePanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
