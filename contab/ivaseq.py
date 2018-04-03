#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/ivaseq.py
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
import contab.regiva_wdr as wdr

import contab.dbtables as dbc

import Env
bt = Env.Azienda.BaseTab

from awc.controls.linktable import EVT_LINKTABCHANGED

import report as rpt


FRAME_TITLE = "Controllo sequenza protocolli IVA"


"""
Controllo sequesta protocollo IVA.
"""


class CtrIvaSeqRisGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, db):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(),
                                              idGrid='checkseqprot')
        
        self.dbris = db
        
        def cn(col):
            return db._GetFieldIndex(col, inline=True)
        
        ris = self.dbris
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            ( 80, (cn("datreg"),   "Data reg.", _DAT, True)),
            ( 40, (cn("caucod"),   "Cod.",      _STR, True)),
            (120, (cn("caudes"),   "Causale",   _STR, True)),
            ( 50, (cn("numdoc"),   "Num.doc.",  _STR, True)),
            ( 80, (cn("datdoc"),   "Data doc.", _DAT, True)),
            ( 50, (cn("numiva"),   "Prot.",     _STR, True)),
            (300, (cn("problema"), "Problema",  _STR, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = ris.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(-1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
#        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
#    
#    def OnDblClick(self, event):
#        pdc = self.dbmas
#        mov = pdc.GetMastro()
#        row = event.GetRow()
#        mov.MoveRow(row)
#        try:
#            cls = contab.RegConDialogClass(mov.id_reg)
#            if cls:
#                wx.BeginBusyCursor()
#                dlg = cls(aw.awu.GetParentFrame(self))
#                dlg.SetOneRegOnly(mov.id_reg)
#                wx.EndBusyCursor()
#                if dlg.ShowModal() in (ctb.REG_MODIFIED, ctb.REG_DELETED):
#                    evt = contab.RegChangedEvent(contab._evtREGCHANGED, 
#                                                 self.GetId())
#                    evt.SetEventObject(self)
#                    evt.SetId(self.GetId())
#                    #self.GetEventHandler().ProcessEvent(evt)
#                    self.GetEventHandler().AddPendingEvent(evt)
#                dlg.Destroy()
#                event.Skip()
#        except:
#            pass


# ------------------------------------------------------------------------------


class CtrIvaSeqPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.CtrIvaSeqFunc(self)
        self.dbreg = dbc.CtrIvaSeqCheck()
        self.dbris = None
        self.gridris = CtrIvaSeqRisGrid(self.FindWindowByName('pangridris'), dbc.CtrIvaSeqRis())
        cn = self.FindWindowByName
        wx.CallAfter(lambda: cn('id_regiva').SetFocus())
        self.Bind(EVT_LINKTABCHANGED, self.OnRegIvaChanged, cn('id_regiva'))
        for name, func in (('butstart', self.OnStart),
                           ('butprint', self.OnPrint),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnRegIvaChanged(self, event):
        ri = event.GetEventObject()
        self.FindWindowByName('butstart').Enable(ri.GetValue() is not None)
        event.Skip()
    
    def OnStart(self, event):
        self.UpdateGridRis()
        event.Skip()
    
    def OnPrint(self, event):
        if self.dbris is None:
            return
        ri = self.dbreg.regiva
        self.dbris._info.regiva = '%s - %s' % (ri.codice, ri.descriz)
        rpt.Report(self, self.dbris, "Lista protocolli IVA fuori sequenza")
        event.Skip()
    
    def UpdateGridRis(self):
        cn = self.FindWindowByName
        ri = cn('id_regiva').GetValue()
        if ri is None:
            return
        self.dbris = self.dbreg.CtrSeq(ri)
        self.gridris.ChangeData(self.dbris.GetRecordset())
        if self.dbris.IsEmpty():
            aw.awu.MsgDialog(self, "Nessun problema di sequenza riscontrato", style=wx.ICON_INFORMATION)


# ------------------------------------------------------------------------------


class CtrIvaSeqFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = CtrIvaSeqPanel(self)
        self.AddSizedPanel(self.panel, 'ctrivaseq')
