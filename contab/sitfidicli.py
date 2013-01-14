#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/sitfidicli.py
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
import awc.controls.windows as aw
import awc.controls.dbgrid as dbgrid

import contab.pdcint_wdr as wdr

import magazz.dbtables as dbm

import Env
bt = Env.Azienda.BaseTab


class SitFidiClientiGrid(dbgrid.ADB_Grid):
    
    def __init__(self, parent, dbfid):
        
        self.dbfid = fid = dbfid
        cli = fid.anag
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbfid, can_edit=False, on_menu_select='row')
        
        AC = self.AddColumn
        I = self.TypeFloat(5, bt.VALINT_DECIMALS)
        N = self.TypeInteger(5)
        self.COL_CLICOD = AC(fid, 'codice', label='Cod.', col_width=50)
        self.COL_CLIDES = AC(fid, 'descriz', label='Cliente', col_width=200, is_fittable=True)
        self.COL_SCOATT = AC(fid, 'fido_scoatt', label='Scoperto', col_type=I)
        self.COL_SCOMAX = AC(cli, 'fido_maximp', label='Scop.MAX', col_type=I)
        self.COL_ESPATT = AC(fid, 'fido_espatt', label='Esposiz.', col_type=I)
        self.COL_ESPMAX = AC(cli, 'fido_maxesp', label='Esp.MAX', col_type=I)
        self.COL_PCFATT = AC(fid, 'fido_pcfatt', label='Scad.', col_type=N)
        self.COL_PCFMAX = AC(cli, 'fido_maxpcf', label='Sc.M.', col_type=N)
        self.COL_GGSATT = AC(fid, 'fido_ggsatt', label='G.Rit', col_type=N)
        self.COL_GGSMAX = AC(cli, 'fido_maxggs', label='GR.M.', col_type=N)
        self.COL_CLI_ID = AC(fid, 'id', label='#pdc', col_width=1)
        
        self.CreateGrid()
        
#        def gfi(tab, col):
#            return tab._GetFieldIndex(col, inline=True)
#        self.AddTotalsRow(self.COL_DESCLI, 'Totali', (gfi(pcf, 'saldo'),
#                                                      gfi(pcf, 'interessi'),))


class SitFidiClientiPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.SitFidiClientiFunc(self)
        cn = self.FindWindowByName
        self.dbfid = dbm.SituazioneFidiClienti()
        self.gridfid = SitFidiClientiGrid(cn('pangridfid'), self.dbfid)
#        self.UpdateData()
        self.Bind(wx.EVT_BUTTON, self.OnUpdateData, cn('butupdate'))
#        self.Bind(wx.EVT_BUTTON, self.OnPrintData, cn('butprint'))
    
    def OnUpdateData(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        
        cn = self.FindWindowByName
        
        fid = self.dbfid
        fid.ClearFilters()
        id_agente = cn('id_agente').GetValue()
        cf_all = cn('clifid_all').IsChecked()
        cf_sco = cn('clifid_sco').IsChecked()
        cf_esp = cn('clifid_esp').IsChecked()
        cf_pcf = cn('clifid_pcf').IsChecked()
        cf_ggs = cn('clifid_ggs').IsChecked()
        if id_agente:
            fid.AddFilter('anag.id_agente=%s', id_agente)
        w = aw.awu.WaitDialog(self, maximum=0)
        w.init_range = True
        def update():
            if w.init_range:
                w.SetRange(fid.RowsCount())
                w.init_range = False
            w.SetValue(fid.RowNumber())
        wx.BeginBusyCursor()
        try:
            fid.Retrieve(progr_func=update)
            if not cf_all:
                rs = []
                for row, f in enumerate(fid):
                    if cf_sco and ((f.anag.fido_maximp>0 and (f.fido_scoatt or 0) > (f.anag.fido_maximp or 0)) or \
                                   (f.anag.fido_maxesp>0 and (f.fido_espatt or 0) > (f.anag.fido_maxesp or 0)) or \
                                   (f.anag.fido_maxpcf>0 and (f.fido_pcfatt or 0) > (f.anag.fido_maxpcf or 0)) or \
                                   (f.anag.fido_maxggs>0 and (f.fido_ggsatt or 0) > (f.anag.fido_maxggs or 0))):
                        rs.append([]+fid.GetRecordset()[row])
                fid.SetRecordset(rs)
        finally:
            wx.EndBusyCursor()
            w.Destroy()
        self.gridfid.ChangeData(fid.GetRecordset())


class SitFidiClientiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Calcolo interessi partite scadute clienti'
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = SitFidiClientiPanel(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Show()
