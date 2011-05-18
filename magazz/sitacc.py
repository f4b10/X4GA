#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/sitacc.py
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

import magazz.dataentry_wdr as wdr

import wx
import wx.grid as gl
import awc.controls.windows as aw
import awc.controls.dbgrid as dbglib

import magazz.dbtables as dbm

from magazz.dataentry_b import SelezionaMovimentoAccontoPanel

import Env
from magazz.dbtables import PdcSituazioneAcconti
bt = Env.Azienda.BaseTab


FRAME_TITLE = "Situazione acconti clienti"


class SituazioneGlobaleAccontiGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbacc):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbacc = dbacc
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _IMP = bt.GetValIntMaskInfo()
        
        def cn(col):
            return dbacc._GetFieldIndex(col, inline=True)
        
        cols = (( 50, (cn('pdc_codice'),       "Cod.",       _STR, True )),
                (200, (cn('pdc_descriz'),      "Anagrafica", _STR, True )),
                (110, (cn('acconto_disponib'), "Acc.Disp.",  _IMP, False)),)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData((), colmap, canEdit=False, canIns=False)
        
        self.AddTotalsRow(1, 'Totali:', (cn('acconto_disponib'),))
        
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


# ------------------------------------------------------------------------------


class SituazioneGlobaleAccontiPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        
        wx.Panel.__init__(self, *args, **kwargs)
        self.pdcid = None
        self.lastpdcid = None
        SelezionaMovimentoAccontoPanel(self)
        wdr.SituazioneGlobaleAccontiFunc(self)
        cn = self.FindWindowByName
        
        self.dbacc = dbm.PdcTotaleAcconti()
        self.dbacc.VediSoloAperti()
        self.gridacc = SituazioneGlobaleAccontiGrid(cn('pangridcli'), self.dbacc)
        
        self.UpdateData()
        
        self.Bind(wx.EVT_CHECKBOX, self.OnUpdateData, cn('clientichiusi'))
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelected, self.gridacc)
#        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSelectRow)
#
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        cn = self.FindWindowByName
        dbacc = self.dbacc
        if cn('clientichiusi').IsChecked():
            dbacc.VediTutti()
            cn('anchechiusi').SetValue(True)
        else:
            dbacc.VediSoloAperti()
        dbacc.Retrieve()
        self.gridacc.ChangeData(dbacc.GetRecordset())
        self.UpdateDettagli()
        
    def OnCellSelected(self, event):
        self.UpdateDettagli(event.GetRow())
    
    def UpdateDettagli(self, row=None):
        cn = self.FindWindowByName
        p = cn('accontipanel')
        dbacc = self.dbacc
        if dbacc.IsEmpty():
            p.Disable()
        else:
            if row is None:
                row = self.gridacc.GetSelectedRows()[0]
            if 0 <= row < dbacc.RowsCount():
                dbacc.MoveRow(row)
                pdcid = dbacc.pdc_id
            else:
                pdcid = None
            if pdcid != self.lastpdcid:
                p.SetPdcId(pdcid)
                self.lastpdcid = pdcid
            
#    def OnCellSelected(self, event):
#        row = event.GetRow()
#        acc = self.dbacc
#        if 0 <= row < acc.RowsCount():
#            acc.MoveRow(row)
#            if acc.accomov_id != self.lastmovaccid:
#                self.UpdateStorni()
#                event.Skip()
#    
#    def OnChiusi(self, event):
#        dbacc = self.dbacc
#        if event.IsChecked():
#            dbacc.VediTutti()
#        else:
#            dbacc.VediSoloAperti()
#        self.UpdateData()
#        event.Skip()
#    
#    def OnSelectRow(self, event):
#        self.dbacc.MoveRow(event.GetRow())
#        if (self.dbacc.total_disponib or 0) > 0:
#            event.Skip()
#    
#    def SetPdcId(self, pdcid):
#        self.pdcid = pdcid
#        self.UpdateData()
#    
#    def UpdateData(self):
#        dbacc = self.dbacc
#        dbacc.GetForPdc(self.pdcid)
#        self.gridacc.ChangeData(dbacc.GetRecordset())
#        if not dbacc.IsEmpty():
#            self.gridacc.SelectRow(0)
#            self.UpdateStorni()
#        else:
#            self.gridsto.ChangeData(())
#    
#    def UpdateStorni(self):
#        acc = self.dbacc
#        mov = self.dbsto
#        if acc.IsEmpty():
#            mov.Reset()
#        else:
#            row = self.gridacc.GetSelectedRows()[0]
#            if 0 <= row < acc.RowsCount():
#                acc.MoveRow(row)
#                mov.Retrieve("mov.id_movacc=%s", acc.accomov_id)
#                disp = acc.accomov_importo
#                for mov in mov:
#                    disp -= abs(mov.importo)
#                    mov.acconto_disponib = disp
#                self.lastmovaccid = acc.accomov_id
#        self.gridsto.ChangeData(mov.GetRecordset())


# ------------------------------------------------------------------------------


class SituazioneGlobaleAccontiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = 'Situazione acconti cliente'
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = SituazioneGlobaleAccontiPanel(self)
        self.AddSizedPanel(self.panel)
