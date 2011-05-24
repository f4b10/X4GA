#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/vendazipriv.py
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

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab

import contab.dbtables as dbc

from contab import regiva_wdr as wdr

import report as rpt


FRAME_TITLE = "Sintesi vendite privati/aziende"


class VendAziPrivGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia anagrafiche e totali
    """
    
    valwidth = 110
    
    def __init__(self, parent, dbven):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable sintesi vendite (derivati da contab.dbtables.VendAziPriv)
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbven = ven = dbven
        
        _STR = gl.GRID_VALUE_STRING
        _VAL = bt.GetValIntMaskInfo()
        
        def cn(col):
            return ven._GetFieldIndex(col, inline=True)
        def ct(col):
            return cn('total_%s' % col)
        
        w = self.valwidth
        
        cols = (( 60, (cn('pdc_codice'),     "Cod.",             _STR, True)),
                (240, (cn('pdc_descriz'),    "Anagrafica",       _STR, True)),
                ( 40, (cn('anag_stato'),     "Stato",            _STR, True)),
                (110, (cn('anag_piva'),      "P.IVA",            _STR, True)),
                (140, (cn('anag_codfisc'),   "Cod.Fiscale",      _STR, True)),
                (  w, (ct('imponib_priv'),   "Imponib.Privati",  _VAL, True)),
                (  w, (ct('imposta_priv'),   "Imposta Privati",  _VAL, True)),
                (  w, (ct('noimpes_priv'),   "NoImp/Es.Privati", _VAL, True)),
                (  w, (ct('imponib_aziita'), "Imponib.Az.ITA",   _VAL, True)),
                (  w, (ct('imposta_aziita'), "Imposta Az.ITA",   _VAL, True)),
                (  w, (ct('noimpes_aziita'), "NoImp/Es.Az.ITA",  _VAL, True)),
                (  w, (ct('imponib_azicee'), "Imponib.Az.CEE",   _VAL, True)),
                (  w, (ct('imposta_azicee'), "Imposta Az.CEE",   _VAL, True)),
                (  w, (ct('noimpes_azicee'), "NoImp/Es.Az.CEE",  _VAL, True)),
                (  w, (ct('imponib_estero'), "Imponib Estero",   _VAL, True)),
                (  w, (ct('imposta_estero'), "Imposta Estero",   _VAL, True)),
                (  w, (ct('noimpes_estero'), "NoImp/Es.Estero",  _VAL, True)),
                (  1, (cn('pdc_id'),         "#pdc",             _STR, True)),)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(self.dbven.GetRecordset(), colmap)
        
        self.AddTotalsRow(1,'Totali:',(ct('imponib_priv'),
                                       ct('imposta_priv'),
                                       ct('noimpes_priv'),
                                       ct('imponib_aziita'),
                                       ct('imposta_aziita'),
                                       ct('noimpes_aziita'),
                                       ct('imponib_azicee'),
                                       ct('imposta_azicee'),
                                       ct('noimpes_azicee'),
                                       ct('imponib_estero'),
                                       ct('imposta_estero'),
                                       ct('noimpes_estero'),))
        
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
    
    def GetTotale(self, rscol):
        def cn(col):
            return self.dbven._GetFieldIndex(col, inline=True)
        def ct(col):
            return cn('total_%s' % col)
        t = self.GetTable()
        try:
            n = t.totals[0][2].index(ct(rscol))
            out = t.totals[0][3][n]
        except Exception, e:
            out = 0
        return out


# ------------------------------------------------------------------------------


class VendAziPrivPanel(aw.Panel):
    """
    Pannello sintesi vendite privati/aziende
    """
    
    tipi = 'priv aziita azicee estero'.split()
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.VendAziPrivFunc(self)
        self.dbven = dbc.VendAziPriv()
        self.dbven.ShowDialog(self)
        cn = self.FindWindowByName
        self.gridven = VendAziPrivGrid(cn('pangridven'), self.dbven)
        self.TestRegIva()
        self.totimponib = None
        self.totimposta = None
        self.totnoimpes = None
        self.totvaloper = None
        self.colpriv =\
        self.colaziita =\
        self.colazicee =\
        self.colestero = None
        for tipo in self.tipi:
            self.AdaptColumnsWidth(cn('get%s'%tipo))
        for name, func in (('butupd', self.OnUpdateData),
                           ('butprt', self.OnPrintData),):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
        self.Bind(wx.EVT_CHECKBOX, self.OnCheckBoxChanged)
        
        wx.CallAfter(lambda: cn('datmin').SetFocus())
    
    def TestRegIva(self):
        cn = self.FindWindowByName
        rr = cn('registri')
        rr.ClearVoices()
        regs = dbc.adb.DbTable(bt.TABNAME_REGIVA, 'regiva')
        regs.AddOrder('regiva.codice')
        regs.Retrieve()
        for reg in regs:
            if reg.tipo in 'VC':
                rr.AppendVoice(reg)
    
    def OnCheckBoxChanged(self, event):
        self.AdaptColumnsWidth(event.GetEventObject())
        event.Skip()
    
    def AdaptColumnsWidth(self, o):
        c = o.IsChecked()
        g = self.gridven
        name = o.GetName()
        if name.startswith('get'):
            name = name[3:]
            ven = self.dbven
            for tipo in 'imponib imposta noimpes'.split():
                n = ven._GetFieldIndex('total_%s_%s' % (tipo, name), inline=True)
                if n is not None:
                    n = g.GetTable().rsColumns.index(n)
                    if c:
                        w = g.valwidth
                    else:
                        w = 0
                    g.SetColSize(n, w)
                    setattr(self, 'col%s'%name, c)
            g.ResetView()
    
    def OnUpdateData(self, event):
        if self.Validate():
            self.UpdateData()
            event.Skip()
    
    def Validate(self):
        cn = self.FindWindowByName
        d1, d2 = map(lambda x: cn(x).GetValue(), 'datmin datmax'.split())
        if not d1 or not d2 or d2<d1:
            aw.awu.MsgDialog(self, "Date non valide", style=wx.ICON_ERROR)
            return False
        return True
    
    def UpdateData(self):
        ven = self.dbven
        cn = self.FindWindowByName
        d1, d2 = map(lambda x: cn(x).GetValue(), 'datmin datmax'.split())
        ven.ClearFilters()
        ri = []
        regs = cn('registri')
        for n in range(len(regs.valori)):
            if regs.IsChecked(n):
                ri.append(regs.valori[n])
        if not ri:
            aw.awu.MsgDialog(self, "Nessun registro selezionato")
            return
        ven.AddFilter('reg.id_regiva IN (%s)' % ', '.join(map(str, ri)))
        ven.SetDebug()
        ven.AddFilter('reg.datreg>=%s', d1)
        ven.AddFilter('reg.datreg<=%s', d2)
        if not ven.Retrieve():
            aw.awu.MsgDialog(self, repr(ven.GetError()), style=wx.ICON_ERROR)
            return False
        grid = self.gridven
        grid.ChangeData(ven.GetRecordset())
        self.totimponib = sum(map(lambda tipo: grid.GetTotale('imponib_%s' % tipo) or 0, self.tipi))
        self.totimposta = sum(map(lambda tipo: grid.GetTotale('imposta_%s' % tipo) or 0, self.tipi))
        self.totnoimpes = sum(map(lambda tipo: grid.GetTotale('noimpes_%s' % tipo) or 0, self.tipi))
        self.totvaloper = self.totimponib+self.totnoimpes
        for name in 'totvaloper totimposta'.split():
            self.FindWindowByName(name).SetValue(getattr(self, name))
        return True
    
    def OnPrintData(self, event):
        cn = self.FindWindowByName
        ven = self.dbven
        for name in 'datmin datmax'.split():
            ven.SetPrintValue(name, cn(name).GetValue())
        s = {}
        for tipo in self.tipi:
            s[tipo] = cn('get%s'%tipo).IsChecked()
        ven.SetSpecs(**s)
        rpt.Report(self, ven, 'Vendite aziende-privati')
        event.Skip()


# ------------------------------------------------------------------------------


class VendAziPrivFrame(aw.Frame):
    """
    Frame sintesi vendite privati/aziende
    """
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = VendAziPrivPanel(self)
        self.AddSizedPanel(self.panel)
