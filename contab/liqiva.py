#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/liqiva.py
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
import awc.util as awu

import awc
import awc.controls.windows as aw
from awc.controls.linktable import EVT_LINKTABCHANGED
from awc.controls.datectrl import EVT_DATECHANGED

import Env
import contab.dbtables as dbc

from contab import regiva_wdr as wdr

import report as rpt

_evtLIQEND = wx.NewEventType()
EVT_LIQEND = wx.PyEventBinder(_evtLIQEND, 1)

class FineLiquidEvent(wx.PyCommandEvent):
    pass


FRAME_TITLE = "Liquidazione IVA"


adb = dbc.adb
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

colprot = None
colrimp = None
colriva = None
colaimp = None
colaiva = None
colaind = None


class GridRegStatus(dbglib.DbGrid):
    """
    Griglia Registri IVA per riepilogo status ultima stampa
    """
    def __init__(self, parent, dbstatus):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable registro iva (derivati da contab.dbtables.RegIva)
        """
        
        self.dbstatus = dbstatus
        
        size = parent.GetClientSizeTuple()
        
        reg = self.dbstatus
        ust = reg.stareg
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (
            ( 60, (cn(reg, 'codice'),     "Cod.",        _STR, True)),
            (360, (cn(reg, 'descriz'),    "Registro",    _STR, True)),
            ( 50, (cn(reg, 'tipo'),       "Tipo",        _STR, True)),
            ( -1, (cn(reg, 'lastprtdat'), "Data Stampa", _DAT, True)),
            ( 60, (cn(reg, 'lastprtnum'), "Protocollo",  _NUM, True)),
        )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData( self.dbstatus._info.rs, colmap, canedit, canins,\
                      links, afteredit)
        #self.SetRowLabelSize(100)
        #self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        #self.SetRowDynLabel(self.GetRowLabel)
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        return attr


# ------------------------------------------------------------------------------


class GridRiepAliq(dbglib.DbGrid):
    """
    Griglia riepilogo aliquote iva.
    E' usato sia per il riepilogo delle aliquote per tipo di registro che per
    il riepilogo aliquote di ogni singolo registro.
    """
    
    def __init__(self, parent):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable registro iva (derivati da contab.dbtables.RegIva)
        """
        
        size = parent.GetClientSizeTuple()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER
        _PRC = bt.GetPerGenMaskInfo()
        _FLT = bt.GetValIntMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            ( 40, (dbc.LIQIVA_ALIQ_COD,    "Cod.",         _STR, True )),\
            (150, (dbc.LIQIVA_ALIQ_DESC,   "Aliquota",     _STR, True )),\
            ( 20, (dbc.LIQIVA_ALIQ_TIPO,   "T.",           _STR, True )),\
            ( 50, (dbc.LIQIVA_ALIQ_PERC,   "%IVA",         _PRC, True )),\
            ( 50, (dbc.LIQIVA_ALIQ_INDED,  "%Ind.",        _PRC, True )),\
            (110, (dbc.LIQIVA_TOTIMPONIB,  "Imponibile",   _FLT, True )),\
            (110, (dbc.LIQIVA_TOTIMPOSTA,  "Imposta",      _FLT, True )),\
            (110, (dbc.LIQIVA_TOTINDEDUC,  "Indeducibile", _FLT, True )),\
            )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData((), colmap, canedit, canins, links, afteredit)
        #self.SetRowLabelSize(100)
        #self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        #self.SetRowDynLabel(self.GetRowLabel)
        self.SetCellDynAttr(self.GetAttr)
        
        for label, cbfilt in (\
            ("Totali:",
             lambda rs, row: not rs[row][dbc.LIQIVA_ALIQ_TIPO]),
            ("Acquisti CEE:",
             lambda rs, row: rs[row][dbc.LIQIVA_ALIQ_TIPO] == "C"),
            ("Vendite in sospensione:",
             lambda rs, row: rs[row][dbc.LIQIVA_ALIQ_TIPO] == "S")):
            self.AddTotalsRow(1, label, (dbc.LIQIVA_TOTIMPONIB,
                                         dbc.LIQIVA_TOTIMPOSTA,
                                         dbc.LIQIVA_TOTINDEDUC), cbfilt)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        if self.IsOnTotalRow(row):
            if self.CurrentTotalRow(row) == 0:
                fgcol = 'blue'
            else:
                fgcol = 'blueviolet'
        else:
            fgcol = stdcolor.NORMAL_FOREGROUND
        attr.SetTextColour(fgcol)
        return attr


# ------------------------------------------------------------------------------


class GridUtiCIC(dbglib.DbGrid):
    """
    Griglia utilizzi precedenti del credito compensabile
    """
    def __init__(self, parent, dbliqeff):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable utilizzi precedenti
        """
        
        self.dbliqeff = dbliqeff
        
        size = parent.GetClientSizeTuple()
        
        le = self.dbliqeff
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _FLT = bt.GetValIntMaskInfo()
        
        cols = (\
            ( -1, (cn(le, 'datliq'),  "Data liq.",    _DAT, True )),\
            ( -1, (cn(le, 'datmin'),  "Da data",      _DAT, True )),\
            ( -1, (cn(le, 'datmax'),  "A data",       _DAT, True )),\
            ( 30, (cn(le, 'periodo'), "Per",          _STR, True )),\
            (110, (cn(le, 'ciciniz'), "Disp.Inizio",  _FLT, True )),\
            (110, (cn(le, 'ciculiq'), "Util.Liquid.", _FLT, True )),\
            (110, (cn(le, 'cicuf24'), "Util.F24",     _FLT, True )),\
            (110, (cn(le, 'cicfine'), "Disp.Fine",    _FLT, True )),\
            )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData(le._info.rs, colmap, canedit, canins,\
                     links, afteredit)
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        return attr


# ------------------------------------------------------------------------------


class LiqIvaPanel(aw.Panel):
    """
    Pannello per liquidazione iva.
    """
    
    regivasta = None
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        wdr.LiqIvaFunc(self)
        cn = self.FindWindowByName
        
        tipi = {'P': ("Stampa Provvisoria",\
                      """Vengono estratte solo le registrazioni IVA non """
                      """ancora stampate in modo definitivo.\nL'elaborazione"""
                      """può essere eseguita in qualsiasi momento."""),\
                'D': ("Stampa Definitiva",\
                      """Vengono estratte solo le registrazioni IVA non """
                      """ancora stampate in modo definitivo.\nL'elaborazione"""
                      """può essere eseguita una sola volta.""")}
        self.tipoliq = 'P'
        self.tipiliq = tipi
        self.totaliq = {}
        
        self.dbstatus = dbc.RegIvaStatus()
        self.dbliq = dbc.LiqIva()
        
        anno = Env.Azienda.Esercizio.dataElab.year
        mese = Env.Azienda.Esercizio.dataElab.month
        if self.dbliq._tipoper == "M":
            if mese == 1:
                anno -= 1
                mese = 12
            else:
                mese -= 1
            cn('mese').SetSelection(mese-1)
        else:
            trim = int((mese-1)/3)
            if trim == 0:
                anno -= 1
                trim = 3
            cn('trim').SetSelection(trim)
        cn('anno').SetValue(anno)
        cn('tipoper').SetSelection(0)
        
        lastnum = lastdat = None
        p = self.dbliq._progr
        p.Retrieve('progr.codice=%s', 'iva_liqreg')
        self.regivasta = p.progrimp1
        
        cn('regivasta').SetValue(self.regivasta)
        cn('intdes').SetValue(p.progrdesc)
        self.UpdateLastPag()
        self.UpdateLastLiq()
        
#        if not lastnum or not lastdat:
#            aw.awu.MsgDialog(self, "Progressivi liquidazione mancanti.",
#                             style=wx.ICON_ERROR)
#            cn('butupd').Disable()
        self.lastnum = lastnum
        self.lastdat = lastdat
        
        if self.dbliq._tipoper == "M":
            cn('trim').Show(False)
        else:
            cn('mese').Show(False)
        for name in 'percint inttri1'.split():
            cn(name).Enable(self.dbliq._tipoper == "T")
        self.SetSize((0,0)) #impedito dal sizer, ridimensiona la sez. nascosta
        
        cn('tipoliq').SetDataLink('tipoliq', 'PD')
        self.SetTipoLiq('P')
        
        r = self.dbstatus
        r.SetYear(anno)
        r.Retrieve()
        
        g = GridRegStatus(cn('panel_regstatus'), self.dbstatus)
        g.ChangeData(r.GetRecordset())
        self.gridstatus = g
        
        g = GridRegStatus(cn('panel_registri'), self.dbstatus)
        g.ChangeData(r.GetRecordset())
        g.Bind(gl.EVT_GRID_SELECT_CELL, self.OnRegChanged)
        self.gridriepreg = g
        
        g = GridRiepAliq(cn('panel_riepaliqxtipreg'))
        self.gridaliqxtip = g
        
        g = GridRiepAliq(cn('panel_riepaliqxreg'))
        self.gridaliqxreg = g
        
        cn('splitriep').SetSashPosition(180)
        cn('splitriep').SetSashGravity(.5)
        
        for evt, func, cid in (\
            (wx.EVT_RADIOBOX,    self.OnTipoLiqChanged,  wdr.ID_TIPOLIQ),\
            (wx.EVT_CHECKBOX,    self.OnIntesta,         wdr.ID_ATTRIST),\
            (wx.EVT_BUTTON,      self.OnUpdateLiq,       wdr.ID_BUTUPD),\
            (wx.EVT_BUTTON,      self.OnSaveLiq,         wdr.ID_SAVELIQ),\
            (wx.EVT_BUTTON,      self.OnStampa,          wdr.ID_BUTSTA),\
            (EVT_DATECHANGED,    self.OnDateChanged,     wdr.ID_DATMIN),\
            (wx.EVT_RADIOBOX,    self.OnPeriodicChanged, wdr.ID_TIPOPER),
            (wx.EVT_TEXT,        self.OnAnnoChanged,     wdr.ID_ANNO),
            (wx.EVT_RADIOBOX,    self.OnMeseChanged,     wdr.ID_MESE),
            (wx.EVT_RADIOBOX,    self.OnTrimChanged,     wdr.ID_TRIM),
            (wx.EVT_RADIOBOX,    self.OnTipRegChanged,   wdr.ID_TIPREG)):
            self.Bind(evt, func, id=cid)
        
        for func, cid in ((self.OnWorkZoneChanged, wdr.ID_WORKZONE),
                          (self.OnRiepZoneChanged, wdr.ID_RIEPZONE)):
            self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, func, id=cid)
        
        self.calcdigit = ('vennor1', 'vennor2', 'vencor1', 'vencor2',
                          'venven1', 'venven2', 'acqnor1', 'acqnor2',
                          'vensos1', 'vensos2', 'ivaind1', 'ivaind2')
        
        self.calccalc = ('tivper1', 'tivper2', 'docper1', 'docper2')
        
        self.prospdigit = ('varpre1', 'varpre2', 'invpre1', 'invpre2',
                           'docpre1', 'docpre2', 'cricom2', 
                           'crsdet2', 'inttri1', 'acciva2', 'cicuf24')
        
        self.prospcalc = ('ivadcp1', 'ivadcp2', 'ivaesi1', 'ivadet2', 
                          'ivadov1', 'ivadov2', 'docfin1', 'docfin2', 
                          'vertra1', 'ciculiq', 'cicfine')
        
        self.calcola = True
        
        for key in self.calcdigit+self.prospdigit:
            cn(key).Bind(wx.EVT_TEXT, self.OnCalcola)
        
        self.Bind(wx.EVT_TEXT, self.OnCalcInteressi, cn('percint'))
        
        cn('cricom2').Bind(wx.EVT_SET_FOCUS, self.OnCriComHelp)
        
        self.TestIntest()
        
        self.CalcolaDate()
    
    def UpdateLastPag(self):
        r = self.regivasta
        if r is not None:
            ri = adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
            ri.Get(r)
            cn = self.FindWindowByName
            cn('intanno').SetValue(ri.intanno)
            cn('intpag').SetValue((ri.intpag or 0)+1)
    
    def UpdateLastLiq(self):
        cn = self.FindWindowByName
        lastnum = lastdat = None
        p = self.dbliq._progr
        p.ClearFilters()
        p.AddFilter('progr.codice=%s', 'iva_debcred')
        p.AddFilter('progr.keydiff=%s', cn('anno').GetValue() or 0)
        if p.Retrieve() and p.OneRow():
            lastnum = p.progrnum
            lastdat = p.progrdate
        cn('lastliq_periodo').SetValue(lastnum)
        cn('lastliq_data').SetValue(lastdat)
    
    def OnIntesta(self, event):
        self.TestIntest(setfocus=True)
        event.Skip()
    
    def TestIntest(self, setfocus=False):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        i = cn('intatt').GetValue()
        for name in 'intdes,intanno,intpag'.split(','):
            cn(name).Enable(i)
        
        if i:
            c = cn('intanno')
            if not c.GetValue():
                c.SetValue(cn('anno').GetValue())
            c = cn('intpag')
            if not c.GetValue():
                c.SetValue(1)
            if setfocus:
                cn('intdes').SetFocus()
    
    def OnWorkZoneChanged(self, event):
        self.UpdateButtonPrint()
        event.Skip()
    
    def OnRiepZoneChanged(self, event):
        self.UpdateButtonPrint()
        event.Skip()
    
    def UpdateButtonPrint(self):
        def ci(x):
            return self.FindWindowById(x)
        wz = ci(wdr.ID_WORKZONE).GetSelection()
        rz = ci(wdr.ID_RIEPZONE).GetSelection()
        b = ci(wdr.ID_BUTSTA)
        if wz == 1:
            #riepilogo aliquote
            if rz == 0:
                #per registro
                l = 'Riep. Aliquote x Registro'
            else:
                #per tipo di registro
                l = 'Riep. Aliq. x Tipo Reg.'
        elif wz == 2:
            #calcolo debito/credito
            l = 'Calcolo Debito/Credito'
            ci(wdr.ID_VENNOR1).SetFocus()
        else:
            #prospetto di liquidazione
            l = 'Prospetto di liquidazione'
            ci(wdr.ID_VARPRE1).SetFocus()
        b.Enable(wz>=1)
        b.SetLabel('Stampa %s' % l)
    
    def OnCalcInteressi(self, event):
        self.CalcolaInteressi()
        event.Skip()
    
    def CalcolaInteressi(self):
        if not hasattr(self, '_calcolando_'):
            self._calcolando_ = True
            cn = lambda x: self.FindWindowByName(x)
            perc = cn('percint').GetValue()
            sl = cn('ivadov1').GetValue() - cn('ivadov2').GetValue()
            if sl > 0:
                cn('inttri1').SetValue(sl/100*perc)
            del self._calcolando_
    
    def OnCalcola(self, event):
        if self.calcola:
            self.Calcola()
        self.CalcolaInteressi()
        event.Skip()
    
    def Calcola(self):
        liq = self.dbliq
        mt = liq._totali
        for key in self.calcdigit+self.prospdigit:
            mt[key] = self.FindWindowByName(key).GetValue()
        try:
            liq.Calcola()
        except dbc.ValoriErrati_Exception, e:
            awu.MsgDialog(self, e.args[0])
        for key in self.calccalc+self.prospcalc:
            self.FindWindowByName(key).SetValue(mt[key])
    
    def OnPeriodicChanged(self, event):
        cn = lambda x: self.FindWindowById(x)
        datenab = cn(wdr.ID_TIPOPER).GetSelection() == 1
        d1 = cn(wdr.ID_DATMIN)
        d2 = cn(wdr.ID_DATMAX)
        d1.Enable(datenab)
        d2.Enable(datenab)
        cn = self.FindWindowByName
        m = cn('mese')
        t = cn('trim')
        m.Enable(not datenab)
        t.Enable(not datenab)
        if not datenab:
            self.CalcolaDate()
        if datenab:
            f = d1
        else:
            if m.IsShown():
                f = m
            else:
                f = t
        wx.CallAfter(lambda: f.SetFocus())
        event.Skip()
    
    def OnAnnoChanged(self, event):
        cn = lambda x: self.FindWindowById(x)
        if cn(wdr.ID_TIPOPER).GetSelection() == 0:
            self.CalcolaDate()
            self.SetYear(cn(wdr.ID_ANNO).GetValue())
            self.UpdateLastLiq()
        event.Skip()
    
    def SetYear(self, year):
        r = self.dbstatus
        r.SetYear(year)
        r.Retrieve()
        for grid in (self.gridstatus, self.gridriepreg):
            grid.ChangeData(r.GetRecordset())
        self.dbliq.SetYear(year)
    
    def OnMeseChanged(self, event):
        cn = lambda x: self.FindWindowById(x)
        if cn(wdr.ID_TIPOPER).GetSelection() == 0:
            self.CalcolaDate()
        event.Skip()
    
    def OnTrimChanged(self, event):
        cn = lambda x: self.FindWindowById(x)
        if cn(wdr.ID_TIPOPER).GetSelection() == 0:
            self.CalcolaDate()
        event.Skip()
    
    def CalcolaDate(self):
        cn = lambda x: self.FindWindowById(x)
        anno = cn(wdr.ID_ANNO).GetValue()
        d1 = d2 = None
        if not (anno is None or anno<2009 or anno>2020):
            try:
                if self.dbliq._tipoper == "M":
                    mese = cn(wdr.ID_MESE).GetSelection()+1
                    d1 = adb.DateTime.Date(anno, mese, 1)
                    d2 = adb.DateTime.Date(anno, mese, d1.GetDaysInMonth())
                else:
                    trim = cn(wdr.ID_TRIM).GetSelection()
                    d0 = adb.DateTime.Date(anno, 1, 1)
                    #d1 = d0+adb.DateTime.RelativeDate(0,trim*3)
                    #d2 = d1+adb.DateTime.RelativeDate(0,3)-1
                    d1 = adb.DateTime.Date(anno, trim*3+1, 1)
                    d2 = adb.DateTime.Date(anno, (trim+1)*3, 1)
                    d2 = adb.DateTime.Date(d2.year, d2.month, d2.GetDaysInMonth())
            except ValueError:
                pass
        cn(wdr.ID_DATMIN).SetValue(d1)
        cn(wdr.ID_DATMAX).SetValue(d2)
        cn(wdr.ID_BUTUPD).Enable(d1 is not None)
    
    def OnDateChanged(self, event):
        cn = lambda x: self.FindWindowById(x)
        date = event.GetValue()
        if cn(wdr.ID_TIPOPER).GetSelection() == 0 and date is not None:
            self.SetYear(date.year)
    
    def OnTipoLiqChanged(self, event):
        self.SetTipoLiq(event.GetEventObject().GetValue())
        self.UpdateLastPag()
        awu.MsgDialog(self, "Controllare il numero di pagina iniziale sul cartaceo.")
        event.Skip()
    
    def OnStampa(self, event):
        def ci(x):
            return self.FindWindowById(x)
        def cn(x):
            return self.FindWindowByName(x)
        wz = ci(wdr.ID_WORKZONE).GetSelection()
        rz = ci(wdr.ID_RIEPZONE).GetSelection()
        db, rn = None, None
        d1 = ci(wdr.ID_DATMIN).GetValue()
        d2 = ci(wdr.ID_DATMAX).GetValue()
        if wz == 1:
            #riepilogo aliquote
            if rz == 0:
                #per registro
                rs = []
                tot = self.dbliq._totxreg
                for reg in self.dbstatus:
                    if not reg.id in tot:
                        continue
                    if reg.tipo in "VC":
                        segnop = "D"
                        segnom = "A"
                    else:
                        segnop = "A"
                        segnom = "D"
                    db = dbc.RiepIva(reg.id, segnop, segnom, d1, d2)
                    #per compatilibità alias tabelle con riep.iva fatto x lista mov.
                    db.reg.regiva = db.reg.rei
                    db.aliqiva = db.iva
                    for aid,acod,ades,aprc,apin,atip,aimp,aiva,aind in tot[reg.id]:
                        db.CreateNewRow()
                        db.reg.id_regiva = reg.id
                        db.id_aliqiva = aid
                        db.total_imponib = aimp
                        db.total_imposta = aiva
                        db.total_indeduc = aind
                    rs += db.GetRecordset()
                    db.SetRecordset(rs)
                rn = 'Riepilogo IVA'
            else:
                #per tipo di registro
                #per registro
                rs = []
                tot = self.dbliq._totxtip
                for tipo in 'AVC':
                    tot = self.dbliq._totxtip[tipo]
                    db = dbc.RiepIva(None, None, None, d1, d2)
                    #per compatilibità alias tabelle con riep.iva fatto x lista mov.
                    db.reg.regiva = db.reg.rei
                    db.aliqiva = db.iva
                    for aliq in tot:
                        db.CreateNewRow()
                        db.reg.regiva.tipo = tipo
                        db.id_aliqiva = aliq[dbc.LIQIVA_ALIQ_ID]
                        db.total_imponib = aliq[dbc.LIQIVA_TOTIMPONIB]
                        db.total_imposta = aliq[dbc.LIQIVA_TOTIMPOSTA]
                        db.total_indeduc = aliq[dbc.LIQIVA_TOTINDEDUC]
                    rs += db.GetRecordset()
                db.SetRecordset(rs)
                rn = 'Riepilogo IVA per tipo Registro'
        elif wz in (2, 3):
            db = adb.DbTable(bt.TABNAME_LIQIVA,  'liqeff', writable=True)
            db._info.datmin = d1
            db._info.datmax = d2
            db.CreateNewRow()
            tot = self.dbliq._totali
            for col in tot:
                if col in db.GetFieldNames():
                    setattr(db, col, tot[col])
            if wz == 2:
                #calcolo debito/credito
                rn = 'Liquidazione IVA - Calcolo del Debito-Credito'
            else:
                #prospetto di liquidazione
                rn = 'Liquidazione IVA - Prospetto di Liquidazione'
        if db is None or db.IsEmpty():
            aw.awu.MsgDialog(self, "Non c'è nulla da stampare", style=wx.ICON_INFORMATION)
            return
        if db and rn:
            i = db._info
            i.tiposta = cn('tipoliq').GetValue() #self.dbliq._tipelab
            i.intatt =  cn('intatt').GetValue()
            i.intdes =  cn('intdes').GetValue()
            i.intanno = cn('intanno').GetValue()
            i.intpag =  cn('intpag').GetValue()
            s = rpt.Report(self, db, rn)
#            if i.intatt and i.tiposta == "D" and s.usedReport is not None:
            if i.intatt and s.usedReport is not None:
                r = s.usedReport.oCanvas.userVariableList['intpag']
                cn('intpag').SetValue(r.valore+1)
            event.Skip()
    
    def OnUpdateLiq(self, event):
        if self.IsValidDates():
            self.UpdateLiq()
        event.Skip()
    
    def OnSaveLiq(self, event):
        liq = self.dbliq
        if liq.TestValori():
            mt = self.dbliq._totali
            ver, deb, cred = mt['vertra1'], mt['docfin1'], mt['docfin2']
            if ver:
                message =\
                        """Questa liquidazione porta ad un versamento """\
                        """di Euro """+Env.StrImp(ver)
            else:
                if deb:
                    message =\
                            """Questa liquidazione porta ad un debito di imposta di Euro %s\n"""\
                            """da non versare poiché inferiore al limite minimo di versamento\n"""\
                            """di Euro 25,82.\n"""\
                            """Il debito di Euro %s verrà riportato nella prossima liquidazione."""\
                            % (Env.StrImp(deb), Env.StrImp(deb))
                elif cred:
                    message =\
                            """Con questa liquidazione non c'è da versare nulla.\n"""\
                            """Il credito di Euro %s verrà riportato nella prossima liquidazione."""\
                            % Env.StrImp(cred)
                else:
                    message =\
                            """Questa liquidazione è a zero."""
            message += """\n\nConfermi l'operazione?"""
            r = awu.MsgDialog(self, message, "Conferma liquidazione",
                              style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
            if r == wx.ID_YES:
                cn = self.FindWindowByName
                if liq.SaveLiq(self.regivasta, cn('intanno').GetValue(), cn('intpag').GetValue()-1):
                    awu.MsgDialog(self,
                                  """La liquidazione è stata confermata.""")
                    evt = FineLiquidEvent(_evtLIQEND)
                    evt.SetEventObject(self)
                    self.GetEventHandler().AddPendingEvent(evt)
                else:
                    awu.MsgDialog(self,
                                  """Problemi nel salvataggio della """
                                  """liquidazione\n%s""" % repr(liq.GetError()))
        event.Skip()
    
    def OnCriComHelp(self, event):
        self.CriComHelp()
        event.Skip()
    
    def SetTipoLiq(self, tipoliq):
        """
        Imposta tipo liquidazione:
            "P" liquidazione provvisoria
            "D" liquidazione definitiva
        """
        if not tipoliq in "PD":
            raise Exception, "Tipo stampa errato (%s)" % tipoliq
        self.tipoliq = tipoliq
        cn = lambda x: self.FindWindowById(x)
        cn(wdr.ID_TIPOTIT).SetLabel(self.tipiliq[self.tipoliq][0])
        cn(wdr.ID_TIPODES).SetLabel(self.tipiliq[self.tipoliq][1])
        cn(wdr.ID_SAVELIQ).Enable(tipoliq == "D")
    
    def GetPeriodo(self):
        cn = lambda x: self.FindWindowById(x)
        per = self.dbliq._tipoper
        if cn(wdr.ID_TIPOPER).GetSelection() == 1:
            out = 0 #selezione manuale delle date, periodo=0
        else:
            if per == "M":
                out = cn(wdr.ID_MESE).GetSelection()+1
            else:
                out = cn(wdr.ID_TRIM).GetSelection()+1
        return out
    
    def UpdateLiq(self):
        """
        Aggiornamento dati.
        """
        
        cn = self.FindWindowByName
        
        if cn('tipoliq').GetValue() == 'D':
            
            lastdat, datmin = map(lambda x: cn(x).GetValue(), 
                                  'lastliq_data datmin'.split())
            
            if datmin <= lastdat:
                msg =\
                    """La data di inizio del periodo da liquidare non è congruente\n"""\
                    """con la data dell'ultima liquidazione effettuata."""
                aw.awu.MsgDialog(self, msg, style=wx.ICON_ERROR)
                return
        
        wait = awc.util.WaitDialog(self, message=\
                                   """Estrazione dati dai registri """
                                   """iva in corso...""",\
                                   maximum=0)
        
        r = self.dbliq
        r.SetPeriodo(self.GetPeriodo(),
                     cn('datmin').GetValue(),
                     cn('datmax').GetValue())
        r.Retrieve()
        
        wait.progress.SetRange(r.RowsCount())
        def UpdateBar(reg):
            wait.SetValue(reg.RowNumber())
        
        r.Totalizza(UpdateBar)
        
        self.UpdateAll()
        
        wait.Close()
        wait.Destroy()
        
        cn('workzone').SetSelection(1)
        cn('riepzone').SetSelection(0)
        cn('tipreg').SetSelection(0)
    
    def UpdateAll(self):
        self.UpdateGridAliqxReg()
        self.UpdateGridAliqxTip()
        self.UpdateProspetto()
    
    def UpdateProspetto(self):
        self.calcola = False
        for key, val in self.dbliq._totali.iteritems():
            ctr = self.FindWindowByName(key)
            if ctr is not None:
                ctr.SetValue(val)
        def EnableCalc(*x):
            self.calcola = True
        wx.CallAfter(EnableCalc)
    
    def OnRegChanged(self, event):
        self.UpdateGridAliqxReg(event.GetRow())
        event.Skip()
    
    def UpdateGridAliqxReg(self, row=0):
        g = self.gridaliqxreg
        reg = self.dbstatus
        reg.MoveRow(row)
        liq = self.dbliq
        if reg.id in liq._totxreg:
            g.ChangeData(liq._totxreg[reg.id])
            g.SetGridCursor(0,0)
    
    def OnTipRegChanged(self, event):
        self.UpdateGridAliqxTip(event.GetSelection())
        event.Skip()
    
    def UpdateGridAliqxTip(self, sel=0):
        g = self.gridaliqxtip
        liq = self.dbliq
        g.ChangeData(liq._totxtip["AVC"[sel]])
        g.SetGridCursor(0,0)
    
    def IsValidDates(self):
        out = True
        cn = lambda name: self.FindWindowByName(name)
        datlas = cn('lastliq_data').GetValue()
        datmin, datmax = [cn(name).GetValue() for name in ('datmin', 'datmax')]
        if datmin is None or datmax is None or datmax<datmin:
            out = False
        if cn('tipoliq').GetValue() == "D":
            if out and datlas is not None:
                if datmin<datlas:
                    awu.MsgDialog(self, "La data di partenza è inferiore all'ultima liquidazione", style=wx.ICON_ERROR)
                    return False
                elif datmin != (datlas+1):
                    if awu.MsgDialog(self, "La data di partenza non è consequenziale\nall'ultima liquidazione. Confermi l'esattezza?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                        return False
            if out:
                for ri in self.dbstatus:
                    if ri.rieponly != 1 and (ri.lastprtdat is None or ri.lastprtdat<datmin):
                        awu.MsgDialog(self, "Alcuni registri non sono allineati alla data di stampa.", style=wx.ICON_ERROR)
                        return False
        if not out:
            awu.MsgDialog(self, "Date errate", style=wx.ICON_ERROR)
        return out
    
    def OnZoneChanged(self, event):
        b = self.FindWindowById(wdr.ID_BUTSTA)
        t = event.GetSelection()
        if t == 0:   #tab. selezioni
            b.Disable()
        elif t == 1: #tab. registrazioni
            b.Enable()
            b.SetLabel("&Stampa Registro IVA")
            b.Fit()
        elif t == 2: #tab. riepilogo aliquote
            b.Enable()
            b.SetLabel("&Stampa riepilogo")
            b.Fit()
        event.Skip()
    
    def CriComHelp(self):
        
        liq = self.dbliq
        mt = liq._totali
        cc = liq._cricom
        
        class CriComHelp(wx.PopupTransientWindow):
            """
            Frame aiuto credito iva compensabile
            Viene evidenziato il credito ad inizio anno e quello residuo
            """
            def __init__(self, parent):
                
                wx.PopupTransientWindow.__init__(self, parent,\
                                                 style=wx.SIMPLE_BORDER)
                wdr.LiqIvaCriComHelpFunc(self)
                
                cn = lambda x: self.FindWindowById(x)
                
                cn(wdr.ID_STORIACIC).Enable(liq._liqeff.RowsCount()>0)
                cn(wdr.ID_USACIC).Enable(\
                    cc['cricomdisp'] > 0 and mt['docfin1'] > 0)
                
                def UsaCIC(*args):
                    c = parent.FindWindowById(wdr.ID_CRICOM2)
                    c.SetValue(min(cc['cricomdisp'], mt['docfin1']))
                self.Bind(wx.EVT_BUTTON, UsaCIC, id=wdr.ID_USACIC)
                
                def StoriaCIC(*args):
                    scc = wx.Dialog(parent,
                                    title="Utilizzo credito iva compensabile",
                                    size=(750,300),
                                    style=wx.DEFAULT_DIALOG_STYLE)
                    GridUtiCIC(scc, liq._liqeff)
                    scc.Fit()
                    scc.Layout()
                    scc.CenterOnScreen()
                    scc.Show()
                    scc.SetFocus()
                self.Bind(wx.EVT_BUTTON, StoriaCIC, id=wdr.ID_STORIACIC)
        
        year = self.dbliq._year
        t = self.FindWindowById(wdr.ID_CRICOM2)
        p = t.ClientToScreen((0,0))
        s = t.GetSize()
        h = CriComHelp(self)
        for lid, lbl in (\
            (wdr.ID_CCHELP_TITLE, "Disponibile all'inizio del %s" % year),\
            (wdr.ID_CCHELP_START, Env.StrImp(cc['cricomstart'])),\
            (wdr.ID_CCHELP_DISP,  Env.StrImp(cc['cricomdisp']))):
            h.FindWindowById(lid).SetLabel(lbl)
        h.Fit()
        h.Layout()
        h.Position(p, (s[0]+10, 0))
        h.Popup()


# ------------------------------------------------------------------------------


class LiqIvaFrame(aw.Frame):
    """
    Frame Liquidazione IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        if not kwargs.has_key('size') and len(args) < 5:
            kwargs['size'] = (970,600)
        aw.Frame.__init__(self, *args, **kwargs)
        p = LiqIvaPanel(self, -1)
        self.AddSizedPanel(p)
        self.Bind(EVT_LIQEND, self.OnEnd)
    
    def OnEnd(self, event):
        self.Close()


# ------------------------------------------------------------------------------


class LiqIvaDialog(aw.Dialog):
    """
    Dialog Liquidazione IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        if not kwargs.has_key('size') and len(args) < 5:
            kwargs['size'] = (970,600)
        aw.Dialog.__init__(self, *args, **kwargs)
        p = LiqIvaPanel(self, -1)
        self.AddSizedPanel(p)
        self.Bind(EVT_LIQEND, self.OnEnd)
    
    def OnEnd(self, event):
        if self.IsModal():
            self.EndModal(1)
        else:
            self.Close()


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    
    class _testApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            Env.Azienda.DB.testdb()
            db = adb.DB()
            db.Connect()
            return True
    
    app = _testApp(True)
    app.MainLoop()
    Env.InitSettings()
    test = LiqIvaDialog()
    test.CenterOnScreen()
    test.ShowModal()
