#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/alleg2011.py
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

import contab
import contab.spesometro_2011_wdr as wdr

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
        
        self.dbspe = dbc.Spesometro2011_AcquistiVendite()
        self.gridspe = SpesometroGrid(cn('gridpanel'), self.dbspe)
        
        self.regspy = None
        self.anno = None
        
        anno, data1, data2 = map(lambda label: cn(label), 'anno data1 data2'.split())
        anno.SetValue(Env.Azienda.Login.dataElab.year)
        self.SetDates()
        
        self.SetModo(self.MODO_AGGIORNA)
        
        self.Bind(wx.EVT_TEXT, self.OnYearChanged, anno)
        for date in (data1, data2):
            self.Bind(EVT_DATECHANGED, self.OnDateChanged, date)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnRegSpy, cn('regspy'))
        self.Bind(EVT_REGSPY_HIDDEN, self.OnRegSpyHidden)
        self.Bind(EVT_REGSPY_CHANGED, self.OnRegSpyChanged)
        
        self.gridspe.Bind(dbgrid.gridlib.EVT_GRID_CMD_SELECT_CELL, self.OnRegSpyRowChanged)
        
        for name, func in (('butupdate', self.OnUpdateButton),
                           ('butestrai', self.OnEstraiButton),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
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
    
    def OnYearChanged(self, event):
        self.SetDates()
        event.Skip()
    
    def OnDateChanged(self, event):
        self.Validate()
        event.Skip()
    
    def OnUpdateButton(self, event):
        self.UpdateData()
        event.Skip()
    
    def OnEstraiButton(self, event):
        self.EstraiReg()
        event.Skip()
    
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
        for err, msg in ((not 2010 <= anno <= 2011,       "L'anno è errato"),
                         (data1 is None or data2 is None, "Le date non possono essere nulle"),
                         (data1.year != anno,             "La data di partenza si riferisce ad altro anno"),
                         (data2.year != anno,             "La data di fine si riferisce ad altro anno"),
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
            acqven = "acquisto vendita".split()[cn('acqven').GetSelection()]
            TTS(cn('butupdate'), "Estrae tutte le operazioni di %(acqven)s del periodo, ordinate per cliente." % locals())
            TTS(cn('butestrai'), "Raggruppa, ove indicato, le operazioni di %(acqven)s ed estrae solo quelle eccedenti i massimali impostati per il %(anno)s." % locals())
        return valid
    
    def UpdateData(self):
        cn = self.FindWindowByName
        wx.BeginBusyCursor()
        spe = self.dbspe
        try:
            spe.GetData([(name, cn(name).GetValue()) for name in 'acqven data1 data2'.split()])
            self.anno = cn('data1').GetValue().year
            self.gridspe.ChangeData(spe.GetRecordset())
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args), style=wx.ICON_ERROR)
        finally:
            wx.EndBusyCursor()
        self.SetModo(self.MODO_AGGIORNA)
    
    def EstraiReg(self):
        if self.modo == self.MODO_AGGIORNA:
            #modalità aggiornamento, eseguo estrazione da massimali
            wx.BeginBusyCursor()
            try:
                spe = self.dbspe
                rs = spe.Chiedi_NuovoRecordsetDaMassimali(self.anno)
                spe.SetRecordset(rs)
                grid = self.gridspe
                grid.ChangeData(rs)
                grid.ResetView()
            finally:
                wx.EndBusyCursor()
            self.SetModo(self.MODO_ESTRAI)
        else:
            #modalità transazioni estratte, lancio lista
            rpt.Report(self, self.dbspe, 'Spesometro')


# ------------------------------------------------------------------------------


class SpesometroGrid(dbgrid.ADB_Grid):
    
    def __init__(self, parent, dbspe):
        
        dbgrid.ADB_Grid.__init__(self, parent, db_table=dbspe, can_edit=True, on_menu_select='row')
        
        self.current_pdc = None
        
        s = dbspe
        _float = self.TypeFloat(6, bt.VALINT_DECIMALS)
        
        self._col_pdccod = s._GetFieldIndex('Anag_Cod')
        self._col_pdcdes = s._GetFieldIndex('Anag_Descriz')
        self._col_smlink = s._GetFieldIndex('Reg_Link')
        
        self.COL_SELECTED = self.AddColumn(s, 'selected', 'Sel.', 
                                           col_width=40, col_type=self.TypeCheck(), 
                                           is_editable=True)
        
        def GetLinkIndicator(row, col):
            none =   ''
            first =  'abb.'
            center = 'abb..'
            last =   'abb.*'
            rs = self.db_table.GetRecordset()
            value = rs[row][col]
            smlink = rs[row][self._col_smlink]
            if smlink is None:
                return none
            if row > 0 and rs[row-1][self._col_smlink] != smlink:
                return first
            if row < (len(s.GetRecordset())-1) and rs[row+1][self._col_smlink] != smlink:
                return last
            return center
        
        self.COL_INDICATR = self.AddColumn(get_cell_func=GetLinkIndicator, 
                                           col_name='indicator', label='Abb?', col_width=50)
        
        self.COL_ANAG_COD = self.AddColumn(s, 'Anag_Cod',       'Cod.', col_width=50)
        self.COL_ANAG_DES = self.AddColumn(s, 'Anag_Descriz',   'Cliente', col_width=300)
        self.COL_ANAG_APF = self.AddColumn(s, 'Anag_AziPer',    'A/P', col_width=35)
        self.COL_ANAG_CFS = self.AddColumn(s, 'Anag_CodFisc',   'Cod.Fiscale', col_width=130)
        self.COL_ANAG_STT = self.AddColumn(s, 'Anag_Nazione',   'Naz.', col_width=40)
        self.COL_ANAG_PIV = self.AddColumn(s, 'Anag_PIVA',      'P.IVA', col_width=90)
        
#        self.COL_CAUS_COD = self.AddColumn(s, 'Cau_Cod',        'Cod.', col_width=40)
#        self.COL_CAUS_DES = self.AddColumn(s, 'Cau_Descriz',    'Causale', col_width=120)

        self.COL_DOCU_DAT = self.AddColumn(s, 'Reg_DatDoc',     'Doc.', col_type=self.TypeDate())
        self.COL_DOCU_NUM = self.AddColumn(s, 'Reg_NumDoc',     'Num.', col_width=60)
        self.COL_RIVA_COD = self.AddColumn(s, 'RegIva_Cod',     'Reg.', col_width=40)
        self.COL_RIVA_NIV = self.AddColumn(s, 'Reg_NumIva',     'Prot.', col_type=self.TypeInteger(6), col_width=50)
        self.COL_TDAV_MCE = self.AddColumn(s, 'DAV_Merce',      'Merce', col_type=_float)
        self.COL_TDAV_SRV = self.AddColumn(s, 'DAV_Servizi',    'Servizi', col_type=_float)
        self.COL_TDAV_ALT = self.AddColumn(s, 'DAV_Altro',      'Altro', col_type=_float)
        self.COL_TIVA_IMP = self.AddColumn(s, 'IVA_Imponib',    'Imponibile', col_type=_float)
        self.COL_TIVA_IVA = self.AddColumn(s, 'IVA_Imposta',    'Imposta', col_type=_float)
        self.COL_TIVA_TOT = self.AddColumn(s, 'IVA_Totale',     'Totale', col_type=_float)
        self.COL_TIVA_NIM = self.AddColumn(s, 'IVA_NonImponib', 'Non Imponib.', col_type=_float)
        self.COL_TIVA_ESE = self.AddColumn(s, 'IVA_Esente',     'Esente', col_type=_float)
        self.COL_TIVA_FCA = self.AddColumn(s, 'IVA_FuoriCampo', 'Fuori Campo', col_type=_float)
        self.COL_REG_ID =   self.AddColumn(s, 'Reg_Id',         '#reg', col_width=1)
        self.SetColorsByColumn(self.COL_ANAG_COD)
        self.CreateGrid()
    
    def IsRowOfPdcOrFree(self, row):
        return self.current_pdc is None or self.db_table.GetRecordset()[row][self._col_pdccod] == self.current_pdc
    
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
        
        if not self.IsRowOfPdcOrFree(row):
            attr.SetReadOnly()
            attr.SetTextColour('lightgray')
        
        if col in (self.COL_TDAV_MCE,
                   self.COL_TDAV_SRV,
                   self.COL_TDAV_ALT,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -32)
            attr.SetBackgroundColour(bg)
            
        elif col in (self.COL_TIVA_IMP,
                     self.COL_TIVA_NIM,
                     self.COL_TIVA_ESE,
                     self.COL_TIVA_FCA,):
            bg = self.AlterColor(attr.GetBackgroundColour(), -64)
            attr.SetBackgroundColour(bg)
        
        return attr
    
    def _SwapCheckValue(self, row, col):
        if not self.IsRowOfPdcOrFree(row):
            return
        checked = dbgrid.ADB_Grid._SwapCheckValue(self, row, col)
        if checked:
            det = self.db_table
            det.MoveRow(row)
            self.current_pdc = det.Anag_Cod
        else:
            if not self.db_table.Locate(lambda det: det.selected is True):
                self.current_pdc = None
        self.Refresh()
    
    def OnCellSelected(self, event):
        self.SelectRow(event.GetRow())
        event.Skip()
    
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
                    dlg = K(self, onecodeonly=id_pdc)
                    dlg.OneCardOnly(id_pdc)
                finally:
                    wx.EndBusyCursor()
                dlg.ShowModal()
                dlg.Destroy()
                e = RegChangedEvent()
                self.GetEventHandler().AddPendingEvent(e)
        event.Skip()
    
    def ShowContextMenu(self, position, row, col):
        
        det = self.db_table
        if not 0 <= row < det.RowsCount():
            return
        det.MoveRow(row)
        
        righe_sel = det.Chiedi_QualiRigheSonoSelezionate()
        
        self.ResetContextMenu()
        ACM = self.AppendContextMenuVoice
        
        def NotificaRegCambiata():
            self.GetEventHandler().AddPendingEvent(RegChangedEvent())
        
        def Reset():
            for d in det:
                if d.selected:
                    d.selected = 0
            self.current_pdc = None
            NotificaRegCambiata()
        
        wx.BeginBusyCursor()
        try:
            
            riga_ok = row in righe_sel
            
            if det.Chiedi_MancanoChiaviNelleRighe(righe_sel):
                
                def AbbinaRighe(event):
                    det.Esegui_AbbinaRighe(righe_sel)
                    Reset()
                    event.Skip()
                ACM('Abbina righe', AbbinaRighe, riga_ok)
                
            if det.Chiedi_CiSonoChiaviNelleRighe(righe_sel):
                def ResettaChiavi(event):
                    det.Esegui_ResettaChiaviNelleRighe(righe_sel)
                    Reset()
                    event.Skip()
                ACM('Resetta abbinamenti', ResettaChiavi, riga_ok)
            
        finally:
            wx.EndBusyCursor()
        
        return dbgrid.ADB_Grid.ShowContextMenu(self, position, row, col)

        
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
        assert bt.TIPO_CONTAB == "O"
        self.dbdet.AddBaseFilter('body.tipriga IN ("S", "C", "A")')
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
    
    def ReadData(self, id_reg=None):
        if id_reg is None:
            id_reg = self.id_reg
        det = self.db_table
        det.Retrieve('reg.id=%s' % id_reg)
        self.ChangeData(det.GetRecordset())
        self.id_reg = id_reg
    
    def ShowContextMenu(self, position, row, col):
        
        det = self.db_table
        
        if not 0 <= row < det.RowsCount():
            return
        det.MoveRow(row)
        
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
