#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/scad.py
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


import stormdb as adb
import wx
import wx.grid as gl
import awc.controls.windows as aw
import awc.util as awu
import awc.controls.dbgrid as dbglib
import contab  as c
import magazz.dataentry_wdr as wdr
import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

from contab.pdcint import GridScadenzario


class ScadLinkPanel(aw.Panel):
    pcfdata = None
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.ScadLinkFunc(self)
        self.dbscad = c.dbtables.PdcScadenzario()
        pp = self.FindWindowById(wdr.ID_PANGRIDSCAD)
        self.gridscad = GridScadenzario(pp, self.dbscad)
        self.pcfdata = [None, None, None, None]
        self.Bind(wx.EVT_BUTTON, self.OnPcfSelect, id=wdr.ID_BTNSEL)
    
    def OnPcfSelect(self, event):
        rows = self.gridscad.GetSelectedRows()
        if rows:
            row = rows[0]
            pcf = self.dbscad.GetPartite()
            pcf.MoveRow(row)
            self.pcfdata[0] = pcf.id
            self.pcfdata[1] = pcf.datscad
            self.pcfdata[2] = pcf.riba
            self.pcfdata[3] = pcf.id_effbap
            event.Skip()
    
    def SetPdc(self, pdcid):
        self.dbscad.Get(pdcid)
        self.gridscad.ChangeData(self.dbscad.GetPartite().GetRecordset())
    
    def GetPcfData(self, *args, **kwargs):
        return self.pcfdata

# ------------------------------------------------------------------------------


class ScadLinkDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Aggancio partita'
        if 'pdcid' in kwargs:
            pdcid = kwargs.pop('pdcid')
        else:
            pdcid = None
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = ScadLinkPanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnPcfSelect, id=wdr.ID_BTNSEL)
        if pdcid:
            self.SetPdc(pdcid)
    
    def OnPcfSelect(self, event):
        self.EndModal(wx.ID_OK)
    
    def SetPdc(self, *args, **kwargs):
        self.panel.SetPdc(*args, **kwargs)
    
    def GetPcfData(self, *args, **kwargs):
        return self.panel.GetPcfData(*args, **kwargs)


# ------------------------------------------------------------------------------


class GridScad(object):
    """
    Griglia scadenze del documento
    """
    def __init__(self, dbreg):
        object.__init__(self)
        self.dbreg = dbreg
        self.gridscad = None
        self.caneditscad = True
        self.pcflinks = {}
    
    def GridScadSetReg(self, dbreg):
        self.dbreg = dbreg
        self.gridscad.ChangeData(dbreg.scad.GetRecordset())
    
    def GridScadSetCanEdit(self, c):
        self.caneditscad = c
    
    def GridScad_Init(self, parent):
        #costruzione griglia scadenze
        size = parent.GetClientSizeTuple()
        
        import contab  as c
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (c.RSSCA_DATSCAD, "Data",    _DAT, True )),\
            (100, (c.RSSCA_IMPORTO, "Importo", _IMP, True )),\
            ( 40, (c.RSSCA_ISRIBA,  "R.B.",    _CHK, True )),\
            (140, (c.RSSCA_NOTE,    "Note",    _STR, True )),\
            (  1, (c.RSSCA_ID,      "#sca",    _STR, True )),\
            (  1, (c.RSSCA_IDREG,   "#reg",    _STR, True )),\
            (  1, (c.RSSCA_IDPCF,   "#pcf",    _STR, True )),\
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        links = None
        
        afteredit = None
        #afteredit = ( (dbglib.CELLEDIT_BEFORE_UPDATE, 1,\
                       #self.GridBodyVerifyTipMov),\
                      #(dbglib.CELLEDIT_AFTER_UPDATE,  -1,\
                       #self.GridBodyEditedValues), )
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1,\
                       self.GridScadEditedValues), )
        
        grid = dbglib.DbGrid(parent, -1, size=size, style=0, idGrid='docmagscad')
        grid.SetData( self.dbreg.scad._info.rs, colmap,\
                      canedit, canins, links, afteredit,\
                      self.GridScadAddNewRow )
        grid.SetRowLabelSize(30)
        grid.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        grid.SetRowDynLabel(self.GridScad_GetRowLabel)
        grid.SetCellDynAttr(self.GridScadGetAttr)
        self.Bind(wx.EVT_BUTTON, self.GridScadOnCreate, id=wdr.ID_SCADBUTNEW)
        self.Bind(wx.EVT_BUTTON, self.GridScadOnDelete, id=wdr.ID_SCADBUTDEL)
        self.Bind(wx.EVT_BUTTON, self.GridScadOnsuddividi, id=wdr.ID_SCADBUTSUD)
        self.Bind(wx.EVT_BUTTON, self.GridScadOnsuddividiRim, id=wdr.ID_SCADBUTSUR)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.SetBackgroundColour(stdcolor.GetColour('grey84'))
        
        grid.SetFitColumn(3)
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.gridscad = grid
        
        grid.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.GridScadOnCellRightClick)
    
    def GridScad_GetRowLabel(self, row):
        label = "#%d" % (row+1)
        return label
    
    def GridScadOnCellRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < len(self.dbreg.scad.GetRecordset()):
            if not self.gridscad.IsReadOnly(row, 0):
                self.GridScadMenuPopup(event)
    
    def GridScadMenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        self.gridscad.SetGridCursor(row, col)
        self.gridscad.SelectRow(row)
        menu = wx.Menu()
        linkId = wx.NewId()
        menu.Append(linkId, "Lega la scadenza ad un'altra partita dell'anagrafica")
        self.Bind(wx.EVT_MENU, self.GridScadOnPdcLink, id=linkId)
        rs = self.dbreg.scad.GetRecordset()
        if rs[row][c.RSSCA_IDPCF]:
            resetId = wx.NewId()
            menu.Append(resetId, "Sgancia scadenza da partita esistente")
            self.Bind(wx.EVT_MENU, self.GridScadOnPdcUnlink, id=resetId)
        xo, yo = event.GetPosition()
        self.gridscad.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()
    
    def GridScadOnPdcLink(self, event):
        self.GridScadPdcLink()
        event.Skip()
    
    def GridScadOnPdcUnlink(self, event):
        self.GridScadPdcUnlink()
        event.Skip()
    
    def GridScadPdcLink(self):
        dlg = ScadLinkDialog(self, pdcid=self.dbdoc.id_pdc)
        if dlg.ShowModal() == wx.ID_OK:
            rows = self.gridscad.GetSelectedRows()
            if rows:
                row = rows[0]
                rs = self.dbreg.scad.GetRecordset()
                pcfdata = dlg.GetPcfData()
                rs[row][c.RSSCA_IDPCF] = pcfdata[0]
                rs[row][c.RSSCA_DATSCAD] = pcfdata[1]
                rs[row][c.RSSCA_ISRIBA] = pcfdata[2]
                if self.dbdoc.regcon.scad:
                    self.dbdoc.regcon._info.id_effbap = pcfdata[3]
        dlg.Destroy()
        self.gridscad.Refresh()
    
    def GridScadPdcUnlink(self):
        rows = self.gridscad.GetSelectedRows()
        if rows:
            row = rows[0]
            rs = self.dbreg.scad.GetRecordset()
            rs[row][c.RSSCA_IDPCF] = None
        self.gridscad.Refresh()
    
    def GridScadReset(self):
        self.gridscad.ResetView()
        self.GridScadCheckImporti()
    
    def GridScadGetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr.SetReadOnly(not rscol in (c.RSSCA_DATSCAD,
                                       c.RSSCA_IMPORTO,
                                       c.RSSCA_ISRIBA,
                                       c.RSSCA_NOTE) or not self.caneditscad)
        attr.SetTextColour(stdcolor.NORMAL_FOREGROUND)
        if self.caneditscad:
            attr.SetBackgroundColour(stdcolor.NORMAL_BACKGROUND)
        else:
            attr.SetBackgroundColour(self.gridscad.GetBackgroundColour())
        return attr

    def GridScadEditedValues(self, row, gridcol, col, value):
        out = True
        if 0 <= row < self.dbreg.scad.RowsCount():
            scadrs = self.dbreg.scad.GetRecordset()
            if col in (c.RSSCA_DATSCAD, c.RSSCA_IMPORTO):
                self.GridScadCheckImporti()
        return True

    def GridScadCheckImporti(self):
        out = True
        pf = awu.GetParentFrame(self.gridscad)
        st = pf.FindWindowByName('scadtot')
        for s in self.dbreg.scad:
            if s.f_riba is None:
                s.f_riba = 0
        if st:
            tot = self.dbreg.scad.GetTotalOf('importo')
            st.SetValue(tot)
        try:
            out = self.CheckScad()
            sw = pf.FindWindowByName('scadwarning')
            if out:
                l = ''
            else:
                l = 'Controllare scadenze ed importi'
            sw.SetLabel(l)
        except AttributeError:
            pass
        return out
    
    def GridScadAddNewRow(self):
        sca = self.dbreg.scad
        sca.MoveNewRow()
        sca.AppendNewRow()
        map(sca._ResetTableVar, 'datscad importo f_riba'.split())
    
    def GridScadOnSelected(self, event):
        row = event.GetRow()
        enable = (1 <= row < self.dbdoc.regcon.scad.RowsCount())
        ctr = self.FindWindowById(wdr.ID_BTNSCADEL)
        ctr.Enable(enable)
        if enable:
            self.dbreg.scad.MoveRow(row)
        event.Skip()
    
    def GridScadOnCreate(self, event):
        if self.caneditscad:
            self.GridScadAddNewRow()
            self.gridscad.ResetView()
            self.gridscad.SetGridCursor(self.dbreg.scad.RowsCount()-1,0)
            self.GridScadCheckImporti()
            event.Skip()

    def GridScadOnDelete(self, event):
        if self.caneditscad:
            sr = self.gridscad.GetSelectedRows()
            if sr:
                row = sr[-1]
                sca = self.dbreg.scad
                self.gridscad.DeleteRows(row)
                sca._info.recordCount -= 1
                if sca._info.recordNumber >= sca._info.recordCount:
                    sca._info.recordNumber -= 1
                sca._UpdateTableVars()
                #after deletion, record cursor is on the following one
                #so for iterations we decrement iteration index and count
                sca._info.iterIndex -= 1
                sca._info.iterCount -= 1
                self.SetDataChanged()
                self.GridScadCheckImporti()
            event.Skip()
    
    def GridScadOnsuddividi(self, event):
        if self.caneditscad:
            sca = self.dbreg.scad
            if sca.RowsCount()<1:
                return
            doc = self.dbdoc
            sf = doc.samefloat
            totdoc = doc.totdare
            ir = round(totdoc/sca.RowsCount(), bt.VALINT_DECIMALS)
            t = 0
            for n in range(sca.RowsCount()-1):
                sca.MoveRow(n)
                sca.importo = ir
                t += sca.importo
            sca.MoveLast()
            sca.importo = round(totdoc-t, bt.VALINT_DECIMALS)
            self.gridscad.ResetView()
            self.GridScadCheckImporti()
            event.Skip()
    
    def GridScadOnsuddividiRim(self, event):
        if self.caneditscad:
            sca = self.dbreg.scad
            rn = self.gridscad.GetSelectedRows()[0]+1
            if sca.RowsCount()<1 or rn >= (sca.RowsCount()-1):
                return
            doc = self.dbdoc
            sf = doc.samefloat
            totdoc = doc.totdare
            t = 0
            for n in range(rn):
                sca.MoveRow(n)
                t += (sca.importo or 0)
            dif = round(totdoc-t, 2)
            ir = round(dif/(sca.RowsCount()-rn), bt.VALINT_DECIMALS)
            for n in range(rn, sca.RowsCount(), 1):
                sca.MoveRow(n)
                sca.importo = ir
                t += (sca.importo or 0)
            if not sf(totdoc, t):
                sca.MoveLast()
                sca.importo = round(sca.importo+(totdoc-t), bt.VALINT_DECIMALS)
            self.gridscad.ResetView()
            self.GridScadCheckImporti()
            event.Skip()
