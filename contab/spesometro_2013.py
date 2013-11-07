#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/spesometro_2013.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# Copyright:    (C) 2013 Fabio Cassini <fabio.cassini@gmail.com>
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
import os

import awc.controls.windows as aw
import awc.controls.dbgrid as dbgrid

import contab
import contab.spesometro_2013_wdr as wdr

import contab.dbtables as dbc

import Env
bt = Env.Azienda.BaseTab

from awc.controls import EVT_DATECHANGED

import report as rpt


FRAME_TITLE = "Spesometro"


_evtREGSPY_ON = wx.NewEventType()
EVT_REGSPY_ON = wx.PyEventBinder(_evtREGSPY_ON)
class RegSpyOnEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, _evtREGSPY_ON)


# ------------------------------------------------------------------------------


_evtREGSPY_OFF = wx.NewEventType()
EVT_REGSPY_OFF = wx.PyEventBinder(_evtREGSPY_OFF)
class RegSpyOffEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, _evtREGSPY_OFF)


# ------------------------------------------------------------------------------


_evtREGSPY_HIDDEN = wx.NewEventType()
EVT_REGSPY_HIDDEN = wx.PyEventBinder(_evtREGSPY_HIDDEN)
class RegSpyHiddenEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, _evtREGSPY_HIDDEN)


# ------------------------------------------------------------------------------


_evtREGSPY_CHANGED = wx.NewEventType()
EVT_REGSPY_CHANGED = wx.PyEventBinder(_evtREGSPY_CHANGED)
class RegChangedEvent(wx.PyCommandEvent):
    def __init__(self):
        wx.PyCommandEvent.__init__(self, _evtREGSPY_CHANGED)


# ------------------------------------------------------------------------------


class SpesometroPanel(aw.Panel):
    
    MODO_AGGIORNA = 0
    MODO_ESTRAI = 1
    
    modo = MODO_AGGIORNA
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.SpesometroPanelFunc(self)
        cn = self.FindWindowByName
        
        self.dbspe = dbc.Spesometro2013_AcquistiVendite()
        self.gridspe = SpesometroGrid(cn('gridpanel'), self.dbspe)
        
        self.regspy = None
        self.anno = None
        self.maxazi = None
        self.maxpri = None
        
        anno, data1, data2 = map(lambda label: cn(label), 'anno data1 data2'.split())
        
        anno_init = 2012
        anno.SetValue(anno_init)#Env.Azienda.Login.dataElab.year)
        self.SetDates()
        
        self.SetMassimali(anno_init)
        
        self.SetModo(self.MODO_AGGIORNA)
        
        self.Bind(wx.EVT_TEXT, self.OnYearChanged, anno)
        for date in (data1, data2):
            self.Bind(EVT_DATECHANGED, self.OnDateChanged, date)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnRegSpy, cn('regspy'))
        self.Bind(EVT_REGSPY_HIDDEN, self.OnRegSpyHidden)
        self.Bind(EVT_REGSPY_CHANGED, self.OnRegSpyChanged)
        
        self.gridspe.Bind(dbgrid.gridlib.EVT_GRID_CMD_SELECT_CELL, self.OnRegSpyRowChanged)
        
        self.Bind(wx.EVT_RADIOBOX, self.OnTipValoriChanged, cn('tipvalori'))
        
        for name, func in (('butupdate', self.OnUpdateButton),
                           ('butestrai', self.OnEstraiButton),
                           ('butgenera', self.OnGeneraButton),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnTipValoriChanged(self, event):
        cn = self.FindWindowByName
        for name in 'maxazi maxpri'.split():
            cn(name).Enable(cn('tipvalori').GetValue() == "M")
        event.Skip()
    
    def SetModo(self, modo):
        assert modo in (self.MODO_AGGIORNA, self.MODO_ESTRAI)
        self.modo = modo
        self.UpdateModo()
    
    def UpdateModo(self):
        modo = self.modo
        if modo == self.MODO_AGGIORNA:
            label_title = 'Elenco di tutte le transazioni del periodo'
            label_button = 'Estrai'
        else:
            label_title = 'Elenco delle transazioni eccedenti i massimali impostati'
            label_button = 'Lista'
        cn = self.FindWindowByName
        cn('gridtitle').SetLabel(label_title)
        cn('butestrai').SetLabel(label_button)
        cn('butgenera').Enable(modo == self.MODO_ESTRAI)
        self.gridspe.set_can_modify(modo == self.MODO_AGGIORNA)
    
    def OnYearChanged(self, event):
        self.SetDates()
        self.SetMassimali(event.GetEventObject().GetValue())
        event.Skip()
    
    def SetMassimali(self, anno):
        try:
            azi, pri = self.dbspe.Chiedi_MassimaliAnno(anno)
        except:
            azi = pri = 0
        cn = self.FindWindowByName
        cn('maxazi').SetValue(azi)
        cn('maxpri').SetValue(pri)
    
    def OnDateChanged(self, event):
        self.Validate()
        event.Skip()
    
    def OnUpdateButton(self, event):
        self.UpdateData()
        event.Skip()
    
    def OnEstraiButton(self, event):
        self.EstraiReg()
        event.Skip()
    
    def OnGeneraButton(self, event):
        self.GeneraFile()
        event.Skip()
    
    def GeneraFile(self):
        defaultFile = 'Spesometro_%s_%s.csv' % (self.anno, Env.Azienda.piva)
        filename = None
        dlg = wx.FileDialog(self,
                            message="Digita il nome del file da generare",
#                            defaultDir=pathname,
                            defaultFile=defaultFile,
                            wildcard="File di esportazione (*.csv)|*.csv",
                            style=wx.SAVE)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetPath()
        dlg.Destroy()
        if filename:
            if os.path.exists(filename):
                if aw.awu.MsgDialog(self, "Il file indicato è già esistente.\nVuoi sovrascriverlo ?", 
                                    style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                    return
            wait = aw.awu.WaitDialog(self, "Generazione file in corso")
            err = None
            try:
                self.dbspe.genera_file(filename)
            except Exception, e:
                err = repr(e.args)
            finally:
                wait.Destroy()
            if err:
                aw.awu.MsgDialog(self, err, style=wx.ICON_ERROR)
    
    def OnRegSpyChanged(self, event):
        grid = self.gridspe
        row, col = grid.GetGridCursorRow(), grid.GetGridCursorCol()
        self.UpdateData()
        try:
            grid.SetGridCursor(row, col)
        except:
            pass
        event.Skip()
    
    def OnRegSpy(self, event):
        show = event.IsChecked()
        if show:
            if self.regspy is None:
                self.regspy = RegSpyFrame(self)
            self.UpdateRegSpy(self.gridspe.GetGridCursorRow())
            self.regspy.Show()
        else:
            if self.regspy is not None:
                self.regspy.Hide()
        event.Skip()
    
    def OnRegSpyRowChanged(self, event):
        self.UpdateRegSpy(event.GetRow())
        event.Skip()
    
    def UpdateRegSpy(self, row):
        spe = self.dbspe
        if self.regspy is not None and 0 <= row < spe.RowsCount():
            spe.MoveRow(row)
            self.regspy.SetReg(spe.Reg_Id)
    
    def OnRegSpyHidden(self, event):
        s = False
        if self.regspy is not None:
            if self.regspy.IsShown():
                s = True
        self.FindWindowByName('regspy').SetValue(s)
        event.Skip()
    
    def SetDates(self):
        cn = self.FindWindowByName
        year = cn('anno').GetValue()
        try:
            self.dbspe.Chiedi_MassimaliAnno(year)
        except:
            pass
        Date = Env.DateTime.Date
        for name, month, day in (('data1', 1,  1),
                                 ('data2', 12, 31),):
            try:
                date = Date(year, month, day)
            except:
                date = None
            cn(name).SetValue(date)
        self.Validate()
    
    def Validate(self):
        cn = self.FindWindowByName
        anno, data1, data2 = map(lambda label: cn(label).GetValue(), 'anno data1 data2'.split())
        wms = ''
        for err, msg in ((not 2010 <= anno <= 2012,       "L'anno è errato"),
                         (data1 is None or data2 is None, "Le date non possono essere nulle"),
                         (data1 is not None 
                          and data1.year != anno,         "La data di partenza si riferisce ad altro anno"),
                         (data2 is not None
                          and data2.year != anno,         "La data di fine si riferisce ad altro anno"),
                         (data2 < data1,                  "Le date sono invertite"),):
            if err:
                wms = msg
                break
        cn('warning').SetLabel(wms)
        valid = not err
        TTS = wx.Button.SetToolTipString
        for name in 'butupdate butestrai'.split():
            b = cn(name)
            TTS(b, wms)
            b.Enable(valid)
        if valid:
            try:
                acqvencor = "acquisto vendita corrispettivi".split()[cn('acqvencor').GetSelection()]
            except:
                acqvencor = "qualsiasi acquisto o vendita"
            TTS(cn('butupdate'), "Estrae tutte le operazioni di %(acqvencor)s del periodo, ordinate per cliente." % locals())
            TTS(cn('butestrai'), "Raggruppa, ove indicato, le operazioni di %(acqvencor)s ed estrae solo quelle eccedenti i massimali impostati per il %(anno)s." % locals())
        return valid
    
    def UpdateData(self):
        cn = self.FindWindowByName
        wx.BeginBusyCursor()
        spe = self.dbspe
        try:
            spe.GetData([(name, cn(name).GetValue()) for name in 'acqvencor data1 data2'.split()], 
                        solo_anag_all=cn('solo_anag_all').IsChecked(),
                        solo_caus_all=cn('solo_caus_all').IsChecked(),
                        escludi_bl_anag=cn('escludi_bla').IsChecked(),
                        escludi_bl_stato=cn('escludi_bls').IsChecked(),)
            self.anno = cn('data1').GetValue().year
            self.gridspe.ChangeData(spe.GetRecordset())
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args), style=wx.ICON_ERROR)
        finally:
            wx.EndBusyCursor()
        self.SetModo(self.MODO_AGGIORNA)
    
    def EstraiReg(self):
        cn = self.FindWindowByName
        if self.modo == self.MODO_AGGIORNA:
            #modalità aggiornamento, eseguo estrazione globale o da massimali
            wx.BeginBusyCursor()
            try:
                if cn('tipvalori').GetValue() == "T":
                    self.maxazi = self.maxpri = -10**9
                else:
                    self.maxazi = cn('maxazi').GetValue()
                    self.maxpri = cn('maxpri').GetValue()
                spe = self.dbspe
                rs = spe.Chiedi_NuovoRecordsetDaMassimali(self.anno, self.maxazi, self.maxpri)
                spe.SetRecordset(rs)
                grid = self.gridspe
                grid.ChangeData(rs)
                grid.ResetView()
#             except Exception, e:
#                 aw.awu.MsgDialog(self, repr(e.args), style=wx.ICON_ERROR)
            finally:
                wx.EndBusyCursor()
            self.SetModo(self.MODO_ESTRAI)
        else:
            #modalità transazioni estratte, lancio lista
            rpt.Report(self, self.dbspe, 'Spesometro')


# ------------------------------------------------------------------------------


class SpesometroGrid(dbgrid.ADB_Grid):
    
    _can_modify = True
    def set_can_modify(self, can_modify):
        self._can_modify = can_modify
    
    def __init__(self, parent, dbspe):
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbspe, can_edit=True, on_menu_select='row')
        
        self.current_pdc = None
        
        s = dbspe
        _float = self.TypeFloat(6, bt.VALINT_DECIMALS)
        
        self._col_pdc_id = s._GetFieldIndex('Anag_Id')
        self._col_pdccod = s._GetFieldIndex('Anag_Cod')
        self._col_pdcdes = s._GetFieldIndex('Anag_Descriz')
        self._col_smlink = s._GetFieldIndex('Reg_Link')
        self._col_smrrif = s._GetFieldIndex('Reg_Rif')
        
#         self.COL_SELECTED = self.AddColumn(s, 'selected', 'Sel.', 
#                                            col_width=40, col_type=self.TypeCheck(), 
#                                            is_editable=True)
#           
#         def GetLinkIndicator(row, col):
#             none =   ''
#             first =  'AGGR.'
#             center = 'aggr.'
#             last =   'aggr*'
#             rs = self.db_table.GetRecordset()
#             value = rs[row][col]
#             smlink = rs[row][self._col_smlink]
#             if smlink is None:
#                 return none
#             if row > 0 and rs[row-1][self._col_smlink] != smlink:
#                 if rs[row][self._col_smrrif] == 1:
#                     return first
#                 return center
#             if row < (len(s.GetRecordset())-1) and rs[row+1][self._col_smlink] != smlink:
#                 return last
#             return center
#         
#         self.COL_INDICATR = self.AddColumn(get_cell_func=GetLinkIndicator, 
#                                            col_name='indicator', label='Abb?', col_width=50)
        
        self.COL_ANAG_COD = self.AddColumn(s, 'Anag_Cod',       'Cod.', col_width=50)
        self.COL_ANAG_DES = self.AddColumn(s, 'Anag_Descriz',   'Cliente', col_width=300)
        self.COL_ANAG_APF = self.AddColumn(s, 'Anag_AziPer',    'A/P', col_width=35)
        self.COL_ANAG_ALL = self.AddColumn(s, 'Anag_AllegCF',   'All', col_type=self.TypeCheck(), col_width=35)
        self.COL_ANAG_CFS = self.AddColumn(s, 'Anag_CodFisc',   'Cod.Fiscale', col_width=140)
        self.COL_ANAG_STT = self.AddColumn(s, 'Anag_Nazione',   'Naz.', col_width=40)
        self.COL_ANAG_PIV = self.AddColumn(s, 'Anag_PIVA',      'P.IVA', col_width=100)
        
        self.COL_DOCU_DAT = self.AddColumn(s, 'Reg_DatDoc',     'Doc.', col_type=self.TypeDate())
        self.COL_DOCU_NUM = self.AddColumn(s, 'Reg_NumDoc',     'Num.', col_width=60)
        self.COL_RIVA_COD = self.AddColumn(s, 'RegIva_Cod',     'Reg.', col_width=40)
        self.COL_RIVA_NIV = self.AddColumn(s, 'Reg_NumIva',     'Prot.', col_type=self.TypeInteger(6), col_width=50)
        self.COL_TIVA_IMP = self.AddColumn(s, 'IVA_Imponib',    'Imponibile', col_type=_float)
        self.COL_TIVA_NIM = self.AddColumn(s, 'IVA_NonImponib', 'Non Imponib.', col_type=_float)
        self.COL_TIVA_ESE = self.AddColumn(s, 'IVA_Esente',     'Esente', col_type=_float)
        self.COL_TIVA_FCA = self.AddColumn(s, 'IVA_FuoriCampo', 'Fuori Campo', col_type=_float)
        self.COL_TIVA_INE = self.AddColumn(s, 'IVA_AllImpo',    'Importo', col_type=_float)
        self.COL_TIVA_IVA = self.AddColumn(s, 'IVA_Imposta',    'Imposta', col_type=_float)
        self.COL_TIVA_TOT = self.AddColumn(s, 'IVA_Totale',     'Totale', col_type=_float)
        
        self.COL_FAAT_CNT = self.AddColumn(s, 'fa_att_cnt',     '.#att', col_type=self.TypeInteger(3))
        self.COL_FAAT_TOT = self.AddColumn(s, 'fa_att_tot',     'Importo', col_type=_float)
        self.COL_FAAT_IVA = self.AddColumn(s, 'fa_att_iva',     'Imposta', col_type=_float)
        self.COL_FAAT_VAR = self.AddColumn(s, 'fa_att_var',     'Var.Imponib.', col_type=_float)
        self.COL_FAAT_VIV = self.AddColumn(s, 'fa_att_viv',     'Var.Imposta', col_type=_float)
        
        self.COL_FAPA_CNT = self.AddColumn(s, 'fa_pas_cnt',     '.#pas', col_type=self.TypeInteger(3))
        self.COL_FAPA_TOT = self.AddColumn(s, 'fa_pas_tot',     'Importo', col_type=_float)
        self.COL_FAPA_IVA = self.AddColumn(s, 'fa_pas_iva',     'Imposta', col_type=_float)
        self.COL_FAPA_VAR = self.AddColumn(s, 'fa_pas_var',     'Var.Imponib.', col_type=_float)
        self.COL_FAPA_VIV = self.AddColumn(s, 'fa_pas_viv',     'Var.Imposta', col_type=_float)
        
        self.COL_BLAT_CNT = self.AddColumn(s, 'bl_att_cnt',     '.#att/e', col_type=self.TypeInteger(3))
        self.COL_BLAT_TOT = self.AddColumn(s, 'bl_att_tot',     'Importo att.', col_type=_float)
        self.COL_BLAT_IVA = self.AddColumn(s, 'bl_att_iva',     'Imposta att.', col_type=_float)
        
        self.COL_BLPA_CNT = self.AddColumn(s, 'bl_pas_cnt',     '.#pas/e', col_type=self.TypeInteger(3))
        self.COL_BLPA_TOT = self.AddColumn(s, 'bl_pas_tot',     'Importo pas.', col_type=_float)
        self.COL_BLPA_IVA = self.AddColumn(s, 'bl_pas_iva',     'Imposta pas.', col_type=_float)
        
        self.COL_SAAT_CNT = self.AddColumn(s, 'sa_att_cnt',     '.#Sctr', col_type=self.TypeInteger(3))
        self.COL_SAAT_TOT = self.AddColumn(s, 'sa_att_tot',     'Corrispettivi', col_type=_float)
        
        self.COL_REG_ID =   self.AddColumn(s, 'Reg_Id',         '#reg', col_width=1)
        
        self.SetColorsByColumn(self.COL_ANAG_COD)
        
        self.CreateGrid()
        
        self.SetRowLabelSize(40)
        self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        self.SetRowDynLabel(self.GetRowLabel)
    
    def GetRowLabel(self, row):
        if 0 <= row < self.db_table.RowsCount():
            return str(row+1)
        return ''
    
    def IsRowOfPdcOrFree(self, row):
        if row >= self.db_table.RowsCount():
            return True
        return self.current_pdc is None or self.db_table.GetRecordset()[row][self._col_pdc_id] == self.current_pdc
    
    def AlterColor(self, color, delta):
        
        r, g, b = color.Red(), color.Green(), color.Blue()
        
        def AlterChannel(channel, delta):
            channel += delta
            if channel > 255:
                channel -= 255
            elif channel < 0:
                channel = -channel
            return channel
        
        colors = map(lambda channel: AlterChannel(channel, delta), [r, g, b])
        
        return wx.Colour(colors[0], colors[1], b)
    
    def GetAttr(self, row, col, rscol, attr):
         
        attr = dbgrid.ADB_Grid.GetAttr(self, row, col, rscol, attr)
         
#         if not self.IsRowOfPdcOrFree(row):
#             attr.SetReadOnly()
#             attr.SetTextColour('lightgray')
#          
        if col in (self.COL_FAAT_CNT,
                   self.COL_FAAT_TOT,
                   self.COL_FAAT_IVA,
                   self.COL_FAAT_VAR,
                   self.COL_FAAT_VIV,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -32)
            attr.SetBackgroundColour(bg)
             
        elif col in (self.COL_FAPA_CNT,
                     self.COL_FAPA_TOT,
                     self.COL_FAPA_IVA,
                     self.COL_FAPA_VAR,
                     self.COL_FAPA_VIV,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -64)
            attr.SetBackgroundColour(bg)
            
        elif col in (self.COL_BLAT_CNT,
                     self.COL_BLAT_TOT,
                     self.COL_BLAT_IVA,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -96)
            attr.SetBackgroundColour(bg)
            
        elif col in (self.COL_BLPA_CNT,
                     self.COL_BLPA_TOT,
                     self.COL_BLPA_IVA,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -128)
            attr.SetBackgroundColour(bg)
            
        elif col in (self.COL_SAAT_CNT,
                     self.COL_SAAT_TOT,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -160)
            attr.SetBackgroundColour(bg)
         
        return attr
    
#     def _SwapCheckValue(self, row, col):
#         if col != self.COL_SELECTED:
#             return
#         if not self.IsRowOfPdcOrFree(row):
#             return
#         checked = dbgrid.ADB_Grid._SwapCheckValue(self, row, col)
#         if checked:
#             det = self.db_table
#             det.MoveRow(row)
#             self.current_pdc = det.Anag_Id
#         else:
#             if not self.db_table.Locate(lambda det: det.selected is True):
#                 self.current_pdc = None
#         self.Refresh()
    
    def OnCellSelected(self, event):
        row = event.GetRow()
        self.SelectRow(row)
        det = self.db_table
        if det.RowNumber() != row:
            if 0 <= row < det.RowsCount():
                det.MoveRow(row)
            self.UpdateTotAnag(det.Anag_Id)
        event.Skip()
    
    def UpdateTotAnag(self, pdc_id):
        det = self.db_table
        rs = det.GetRecordset()
        row = det.RowNumber()
        tot_imp = tot_iva = tot_tot = 0
        if det.IsEmpty():
            desana = '-'
        else:
            desana = rs[row][self._col_pdcdes]
            row0 = det.LocateRS(lambda r: r[self._col_pdc_id] == pdc_id)
            if row0 is not None:
                row = row0
                col_totimp = det._GetFieldIndex('IVA_AllImpo')
                col_totiva = det._GetFieldIndex('IVA_Imposta')
                col_tottot = det._GetFieldIndex('IVA_Totale')
                while row < len(rs) and rs[row][self._col_pdc_id] == pdc_id:
                    tot_imp += (rs[row][col_totimp] or 0)
                    tot_iva += (rs[row][col_totiva] or 0)
                    tot_tot += (rs[row][col_tottot] or 0)
                    row += 1
        f = aw.awu.GetParentFrame(self)
        cn = f.FindWindowByName
        cn('totanades').SetLabel(desana)
        cn('totanaimp').SetLabel(det.sepnvi(tot_imp))
        cn('totanaiva').SetLabel(det.sepnvi(tot_iva))
        cn('totanatot').SetLabel(det.sepnvi(tot_tot))
        f.Layout()
    
    def ChangeData(self, new_rs):
        dbgrid.ADB_Grid.ChangeData(self, new_rs)
        if len(new_rs) == 0:
            pdc_id = None
        else:
            pdc_id = new_rs[0][self._col_pdc_id]
        self.db_table.MoveFirst()
        self.UpdateTotAnag(pdc_id)
        self.current_pdc = None
    
    def OnCellDoubleClicked(self, event):
        det = self.db_table
        det.MoveRow(event.GetRow())
        id_pdc = det.Anag_Id
        pdc = dbc.adb.DbTable(bt.TABNAME_PDC)
        pdc.Get(id_pdc)
        id_tipo = pdc.id_tipo
        if id_tipo is not None:
            K = contab.GetInterrPdcDialogClass(id_tipo)
            if K:
                wx.BeginBusyCursor()
                try:
                    dlg = K(None, onecodeonly=id_pdc)
                    dlg.OneCardOnly(id_pdc)
                finally:
                    wx.EndBusyCursor()
                dlg.ShowModal()
                dlg.Destroy()
                e = RegChangedEvent()
                self.GetEventHandler().AddPendingEvent(e)
        event.Skip()
    
#     def ShowContextMenu(self, position, row, col):
#         
#         if not self._can_modify:
#             aw.awu.MsgDialog(self, "Aggiornare i dati per apportare modifiche", style=wx.ICON_INFORMATION)
#             return
#         
#         det = self.db_table
#         if not 0 <= row < det.RowsCount():
#             return
#         det.MoveRow(row)
#         
#         righe_sel = det.Chiedi_QualiRigheSonoSelezionate()
#         
#         self.ResetContextMenu()
#         ACM = self.AppendContextMenuVoice
#         
#         def NotificaRegCambiata():
#             self.GetEventHandler().AddPendingEvent(RegChangedEvent())
#         
#         def Reset():
#             for d in det:
#                 if d.selected:
#                     d.selected = 0
#             self.current_pdc = None
#             NotificaRegCambiata()
#         
#         wx.BeginBusyCursor()
#         try:
#             
#             riga_ok = row in righe_sel
#             
#             det.MoveRow(row)
#             if len(righe_sel) == 0:# and det.Anag_Associa:
#                 def AssociaTutte(event):
#                     det.MoveRow(row)
#                     self.current_pdc = det.Anag_Id
#                     det.Esegui_SelezionaRighePdc(det.Anag_Id)
#                     self.ResetView()
#                 ACM('Seleziona tutte le righe del sottoconto', AssociaTutte)
#             
#             det.MoveRow(row)
#             if len(righe_sel) > 0 and det.Anag_Id == self.current_pdc:
#                 def DeselezionaRighe(event):
#                     det.Esegui_DeselezionaRighePdc(det.Anag_Id)
#                     self.current_pdc = None
#                     self.ResetView()
#                 ACM('Deseleziona righe', DeselezionaRighe)
#             
#             det.MoveRow(row)
#             if det.Chiedi_MancanoChiaviNelleRighe(righe_sel):
#                 
#                 def AbbinaRighe(event):
#                     det.Esegui_AbbinaRighe(righe_sel)
#                     Reset()
#                     event.Skip()
#                 ACM('Aggrega righe', AbbinaRighe, riga_ok)
#                 
#             det.MoveRow(row)
#             if det.Chiedi_CiSonoChiaviNelleRighe(righe_sel):
#                 def ResettaChiavi(event):
#                     det.Esegui_ResettaChiaviNelleRighe(righe_sel)
#                     Reset()
#                     event.Skip()
#                 ACM('Resetta aggregazioni', ResettaChiavi, riga_ok)
#             
#             det.MoveRow(row)
#             if det.Reg_Link is not None:
#                 def SetMainReg(event):
#                     det.Esegui_SetMainReg()
#                     Reset()
#                     event.Skip()
#                 ACM('Imposta come riferimento per le registrazioni aggregate', SetMainReg, det.Reg_Rif != 1)
#             
#         finally:
#             wx.EndBusyCursor()
#         
#         return dbgrid.ADB_Grid.ShowContextMenu(self, position, row, col)

        
# ------------------------------------------------------------------------------


class SpesometroFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(SpesometroPanel(self))


# ------------------------------------------------------------------------------


class RegSpyPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.RegSpyPanelFunc(self)
        cn = self.FindWindowByName
        self.dbdet = dbc.RiepMovCon()
        if bt.TIPO_CONTAB == "O":
            f = 'body.tipriga IN ("S", "C", "A")'
        else:
            f = 'body.tipriga IN ("S", "C", "A", "I")'
        self.dbdet.AddBaseFilter(f)
        self.gridreg = RegSpyGrid(cn('pangridbody'), self.dbdet)
    
    def SetReg(self, reg_id):
        self.gridreg.ReadData(reg_id)
        cn = self.FindWindowByName
        for name in 'id_caus datreg numdoc datdoc'.split():
            cn(name).SetValue(getattr(self.dbdet.reg, name))


# ------------------------------------------------------------------------------


class RegSpyGrid(dbgrid.ADB_Grid):
    
    def __init__(self, parent, dbdet):
        
        det = dbdet
        pdc = det.pdc
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbdet, on_menu_select='row')
        
        self.id_reg = None
        
        self._col_numrig = det._GetFieldIndex('numriga', inline=True)
        self._col_tiprig = det._GetFieldIndex('tipriga', inline=True)
        
        _float = self.TypeFloat(6, bt.VALINT_DECIMALS)
        
        self.AddColumn(det, 'numriga', 'Riga', col_width=35, col_type=self.TypeInteger(4))
        self.AddColumn(pdc, 'codice',  'Cod.', col_width=50)
        self.AddColumn(pdc, 'descriz', 'Sottoconto', col_width=300, is_fittable=True)
        
        def GetMerceServiziCellValue(row, col):
            det = self.db_table
            det.MoveRow(row)
            smm, sma = det.f_sermer, det.pdc.f_sermer
            if smm == 'M':
                return 'Merce (mov)'
            elif smm == 'S':
                return 'Servizi (mov)'
            elif sma == 'M':
                return 'Merce'
            elif sma == 'S':
                return 'Servizi'
                if det.numriga>1 and det.tipriga != 'A':
                    return '?'
            return ''
        self.AddColumn(None, 'merser', 'Tipo', col_width=80, get_cell_func=GetMerceServiziCellValue)
        
        self.AddColumn(det, 'dare',    'Dare', col_type=_float)
        self.AddColumn(det, 'avere',   'Avere', col_type=_float)
        
        self.CreateGrid()
    
    def GetAttr(self, row, col, rscol, attr):
        attr = dbgrid.ADB_Grid.GetAttr(self, row, col, rscol, attr)
        r = self.db_table.GetRecordset()[row]
        if r[self._col_numrig] == 1 or r[self._col_tiprig] == "A":
            attr.SetTextColour('gray')
            attr.SetReadOnly()
        return attr
    
    def ReadData(self, id_reg=None):
        if id_reg is None:
            id_reg = self.id_reg
        det = self.db_table
        det.Retrieve('reg.id=%s' % id_reg)
        self.ChangeData(det.GetRecordset())
        if det.Locate(lambda d: d.numriga != 1 and d.tipriga != "A"):
            self.SetGridCursor(det.RowNumber(), 0)
        self.id_reg = id_reg
    
    def ShowContextMenu(self, position, row, col):
        
        det = self.db_table
        
        if not 0 <= row < det.RowsCount():
            return
        det.MoveRow(row)
        
        if det.numriga == 1 or det.tipriga == 'A':
            return
        
        self.ResetContextMenu()
        ACM = self.AppendContextMenuVoice
        
        def SetPdcSerMer(sermer):
            table_name = bt.TABNAME_PDC
            det.MoveRow(row) #posizionamento
            if aw.awu.MsgDialog(self, 
                                "Confermi il cambio di tipologia su %s" % det.pdc.descriz, 
                                style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                return
            det.MoveRow(row) #riposizionamento, il richiamo a wx potrebbe aver spostato il numero di riga corrente
            id_pdc = det.pdc.id
            det._info.db.Execute("""
            UPDATE %(table_name)s SET f_sermer=%(sermer)s WHERE id=%(id_pdc)s""" % locals())
            e = RegChangedEvent()
            self.GetEventHandler().AddPendingEvent(e)
        
        def SetPdcAsMerce(event):
            SetPdcSerMer('"M"')
        ACM('Imposta il sottoconto come MERCE', SetPdcAsMerce, det.pdc.f_sermer != "M")
        
        def SetPdcAsServizi(event):
            SetPdcSerMer('"S"')
        ACM('Imposta il sottoconto come SERVIZI', SetPdcAsServizi, det.pdc.f_sermer != "S")
        
        def ResetPdc(event):
            SetPdcSerMer('NULL')
        ACM('Resetta la classificazione del sottoconto', ResetPdc, det.pdc.f_sermer in ("S", "M"))
        
        ACM('-', None)
        
        def SetBodySerMer(sermer):
            table_name = bt.TABNAME_CONTAB_B
            det.MoveRow(row)
            id_body = det.id
            det._info.db.Execute("""
            UPDATE %(table_name)s SET f_sermer=%(sermer)s WHERE id=%(id_body)s""" % locals())
            e = RegChangedEvent()
            self.GetEventHandler().AddPendingEvent(e)
        
        def SetBodyAsMerce(event):
            SetBodySerMer('"M"')
        ACM('Imposta questa riga come MERCE', SetBodyAsMerce, det.f_sermer != "M")
        
        def SetBodyAsServizi(event):
            SetBodySerMer('"S"')
        ACM('Imposta questa riga come SERVIZI', SetBodyAsServizi, det.f_sermer != "S")
        
        def ResetBody(event):
            SetBodySerMer('NULL')
        ACM('Resetta la classificazione di questa riga', ResetBody, det.f_sermer in ("S", "M"))
        
        ACM('-', None)
        
        def ApriScheda(event):
            det.MoveRow(row)
            id_pdc = det.pdc.id
            id_tipo = det.pdc.id_tipo
            K = contab.GetInterrPdcDialogClass(id_tipo)
            if K:
                dlg = K(self, onecodeonly=id_pdc)
                dlg.OneCardOnly(id_pdc)
                dlg.ShowModal()
                dlg.Destroy()
                e = RegChangedEvent()
                self.GetEventHandler().AddPendingEvent(e)
        ACM('Apri Scheda sottoconto', ApriScheda)
        
        return dbgrid.ADB_Grid.ShowContextMenu(self, position, row, col)


# ------------------------------------------------------------------------------



class RegSpyFrame(wx.MiniFrame):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'Registration Spy'
        kwargs['style'] = wx.DEFAULT_FRAME_STYLE | wx.TINY_CAPTION_HORIZ | wx.STAY_ON_TOP
        wx.MiniFrame.__init__(self, *args, **kwargs)
        self.panel = RegSpyPanel(self)
        self.Fit()
        self.SetMinSize(self.GetSize())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
    
    def SetReg(self, *args, **kwargs):
        return self.panel.SetReg(*args, **kwargs)
    
    def OnSize(self, event):
        self.panel.SetSize(self.GetClientSize())
        event.Skip()
    
    def OnClose(self, event):
        self.Hide()
        e = RegSpyHiddenEvent()
        self.GetEventHandler().AddPendingEvent(e)
