#!/bin/env python
# -*- coding: utf-8 -*-
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

class SituazioneGlobaleAccontiGrid(dbglib.ADB_Grid):

    def __init__(self, parent, dbacc):

        dbglib.ADB_Grid.__init__(self, parent, db_table=dbacc,
                                 can_edit=False, can_insert=False,
                                 on_menu_select='row',
                                 idGrid="acccli")
        acc = self.dbacc = dbacc

        AC = self.AddColumn
        AC(acc, 'pdc_codice',        'Cod.',       col_width=50)
        AC(acc, 'pdc_descriz',  '     Anagrafica', col_width=50, is_fittable=True)
        AC(acc, 'acconto_disponib',  'Acconto',    col_type=self.TypeFloat())
        self.CreateGrid()
        #=======================================================================
        # def cn(col):
        #     return dbacc._GetFieldIndex(col, inline=True)        
        # self.AddTotalsRow(1, 'Totali:', (cn('acconto_disponib'),))
        #=======================================================================



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
        
        
        wx.CallAfter(self.UpdateData)
        #self.UpdateData()
        
        self.Bind(wx.EVT_CHECKBOX, self.OnUpdateData, cn('clientichiusi'))
        self.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnCellSelected, self.gridacc)
        
        
        #=======================================================================
        # x = self.GetSize().GetHeight()
        # y = self.GetSize().GetWidth()+100
        # self.SetSize(wx.Size(x, y))
        # self.SetClientSize(self.GetSize())
        # self.Refresh()
        #=======================================================================
#        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSelectRow)
#
    
    def OnUpdateData(self, event):
        self.gridacc.ChangeData([])
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        wait = aw.awu.WaitDialog(self, message='Recupero Situazione Acconti',
                                           style=wx.ICON_INFORMATION)
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
        wait.Destroy()        
        
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
            if 0 <= row < dbacc.RowsCount() and len(self.gridacc.GetTable().data)>0:
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
