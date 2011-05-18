#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/progriva.py
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
import awc.util as awu
import awc.controls.windows as aw

import contab.liqiva as ctbliq
from contab import regiva_wdr as wdr

import stormdb as adb

import Env
bt = Env.Azienda.BaseTab


FRAME_TITLE = "Progressivi Liquidazioni IVA"


class LiqEffPanel(aw.Panel):
    
    lastliqid = None
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.LiqEffFunc(self)
        self.Bind(wx.EVT_BUTTON, self.OnDelLast, self.FindWindowByName('butdelast'))
    
    def SetYear(self, year):
        cn = self.FindWindowByName
        cn('year').SetValue(year)
        le = adb.DbTable(bt.TABNAME_LIQIVA,  'liqeff', writable=True)
        le.AddFilter("liqeff.anno=%s", year)
        le.AddOrder("liqeff.datliq")
        le.AddOrder("liqeff.datmin")
        if le.Retrieve() and not le.IsEmpty():
            le.MoveLast()
            self.lastliqid = le.id
            ctbliq.GridUtiCIC(cn('pangridliq'), le)
            cn('butdelast').Enable()
    
    def OnDelLast(self, event):
        if self.lastliqid is not None:
            if aw.awu.MsgDialog(self, "Confermi l'eliminazione dei dati relativi\nall'ultima liquidazione?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                le = adb.DbTable(bt.TABNAME_LIQIVA,  'liqeff', writable=True)
                if le.Get(self.lastliqid) and le.OneRow():
                    le.Delete()
                    if le.Save():
                        aw.awu.MsgDialog(self, "Liquidazione eliminata")
                        event.Skip()
                    else:
                        aw.awu.MsgDialog(self, repr(le.GetError()))


# ------------------------------------------------------------------------------


class LiqEffDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Liquidazioni effettuate nell'anno"
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = LiqEffPanel(self)
        self.AddSizedPanel(self.panel)
        self.Bind(wx.EVT_BUTTON, self.OnDelLast, self.FindWindowByName('butdelast'))
    
    def SetYear(self, *args, **kwargs):
        return self.panel.SetYear(*args, **kwargs)
    
    def OnDelLast(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class ProgrLiqIvaPanel(aw.Panel):
    """
    Progressivi Liquidazione IVA
    """
    def __init__(self, *args, **kwargs):
        
        self.values = {}
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.ProgrLiqIvaFunc(self)
        
        ci = lambda x: self.FindWindowById(x)
        cn = lambda x: self.FindWindowByName(x)
        
        s = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')
        s.Retrieve('setup.chiave=%s', 'liqiva_periodic')
        self.periodic = s.flag
        
        curyear = Env.Azienda.Esercizio.dataElab.year
        
        self.progr = adb.DbTable(bt.TABNAME_CFGPROGR, "progr", writable=True)
         
        p = adb.DbTable(bt.TABNAME_CFGPROGR, "progr")
        p.Retrieve('progr.codice=%s', "iva_liqreg")
        cn('intestaz').SetValue(p.progrdesc or '')
        cn('regiva').SetValue(p.progrimp1)
        
        p = adb.DbTable(bt.TABNAME_CFGPROGR, "progr", fields=None)
        
        p.AddGroupOn("progr.keydiff")
        p.AddOrder("progr.keydiff")
        p.AddFilter("progr.keydiff<%s", curyear)
        p.AddFilter("progr.codice IN %s" % repr(
            ('iva_debcred', 'iva_cricomstart', 'iva_cricomdisp')))
        p.ClearOrders()
        p.AddOrder("progr.keydiff", adb.ORDER_DESCENDING)
        
        l = ci(wdr.ID_ANNI)
        l.Append(str(curyear), curyear)
        if p.Retrieve():
            for p in p:
                l.Append(p.keydiff, int(p.keydiff))
        else:
            awu.MsgDialog(self, "Problema nella lettura dei progressivi\n%s"\
                          % repr(p.GetError()))
        cn = self.FindWindowByName
        for name in 'periodo debcred cricomstart cricomdisp'.split():
            self.Bind(wx.EVT_TEXT, self.OnValueChanged, cn(name))
        from awc.controls.datectrl import EVT_DATECHANGED
        self.Bind(EVT_DATECHANGED, self.OnValueChanged, cn('datlast'))
        self.Bind(wx.EVT_RADIOBOX, self.OnValueChanged, cn('laspom'))
        self.Bind(wx.EVT_LISTBOX, self.OnYear,   ci(wdr.ID_ANNI))
        self.Bind(wx.EVT_BUTTON,  self.OnSave,   ci(wdr.ID_SALVA))
        self.Bind(wx.EVT_BUTTON,  self.OnLiqEff, ci(wdr.ID_LIQEFF))
        
        self.SetYear(curyear)
        l.SetSelection(0)
    
    def OnValueChanged(self, event):
        if not hasattr(self, 'stopevents'):
            l = self.FindWindowByName('anni')
            y = l.GetClientData(l.GetSelection())
            if y in self.values:
                v = self.values[y]
            else:
                self.values[y] = v = [None, None, None, None, None]
            def cnv(x):
                return self.FindWindowByName(x).GetValue()
            v[0] = cnv('datlast')
            v[1] = cnv('periodo')
            v[2] = cnv('debcred')
            v[3] = cnv('laspom')
            v[4] = cnv('cricomstart')
            v[5] = cnv('cricomdisp')
        event.Skip()
    
    def OnYear(self, event):
        l = event.GetEventObject()
        self.SetYear(l.GetClientData(event.GetSelection()))
        event.Skip()
    
    def SetYear(self, year):
        if year in self.values:
            lasdat, lasnum, lascre, laspom, ccstart, ccdisp = self.values[year]
        else:
            p = self.progr
            p.ClearFilters()
            p.AddFilter("progr.keydiff=%s", year)
            p.AddFilter("progr.codice='iva_debcred'")
            p.Retrieve()
            lasdat = p.progrdate
            lasnum = p.progrnum
            lascre = p.progrimp1
            if p.progrimp2 is not None:
                laspom = int(p.progrimp2)
            else:
                laspom = 1
            p.ClearFilters()
            p.AddFilter("progr.keydiff=%s", year)
            p.AddFilter("progr.codice='iva_cricomstart'")
            p.Retrieve()
            ccstart = p.progrimp1
            p.ClearFilters()
            p.AddFilter("progr.keydiff=%s", year)
            p.AddFilter("progr.codice='iva_cricomdisp'")
            p.Retrieve()
            ccdisp = p.progrimp1
            self.values[year] = [lasdat, lasnum, lascre, laspom, ccstart, ccdisp]
        self.stopevents = True
        cn = self.FindWindowByName
        for name, val in (('datlast', lasdat),
                          ('periodo', lasnum),
                          ('debcred', lascre),
                          ('laspom',  laspom),
                          ('cricomstart', ccstart),
                          ('cricomdisp',  ccdisp),):
            cn(name).SetValue(val)
        def DelStopEvents():
            del self.stopevents
        wx.CallAfter(DelStopEvents)
    
    def OnSave(self, event):
        if self.SaveData():
            event.Skip()
    
    def SaveData(self):
        years = self.values.keys()
        years.sort()
        p = adb.DbTable(bt.TABNAME_CFGPROGR, "progr")
        p.Retrieve('progr.codice=%s', "iva_liqreg")
        if p.IsEmpty():
            p.CreateNewRow()
            p.codice = 'iva_liqreg'
        cn = self.FindWindowByName
        p.progrdesc = cn('intestaz').GetValue()
        p.progrimp1 = cn('regiva').GetValue()
        if not p.Save():
            aw.awu.MsgDialog(self, repr(p.GetError()))
            return False
        p = self.progr
        for year in years:
            v = self.values[year]
            p.ClearFilters()
            p.AddFilter("progr.keydiff=%s", year)
            p.AddFilter("progr.codice='iva_debcred'")
            p.Retrieve()
            if p.IsEmpty():
                p.CreateNewRow()
                p.keydiff = year
                p.codice = 'iva_debcred'
            p.progrdate = v[0]
            p.progrnum = v[1]
            p.progrimp1 = v[2]
            p.progrimp2 = v[3]
            p.Save()
            p.ClearFilters()
            p.AddFilter("progr.keydiff=%s", year)
            p.AddFilter("progr.codice='iva_cricomstart'")
            p.Retrieve()
            if p.IsEmpty():
                p.CreateNewRow()
                p.keydiff = year
                p.codice = 'iva_cricomstart'
            p.progrimp1 = v[4]
            p.Save()
            p.ClearFilters()
            p.AddFilter("progr.keydiff=%s", year)
            p.AddFilter("progr.codice='iva_cricomdisp'")
            p.Retrieve()
            if p.IsEmpty():
                p.CreateNewRow()
                p.keydiff = year
                p.codice = 'iva_cricomdisp'
            p.progrimp1 = v[5]
            p.Save()
        return True
    
    def OnLiqEff(self, event):
        o = self.FindWindowByName('anni')
        year = o.GetClientData(o.GetSelection())
        dlg = LiqEffDialog(self)
        dlg.SetYear(year)
        dlg.Fit()
        dlg.Layout()
        dlg.CenterOnScreen()
        dlg.ShowModal()
        event.Skip()


# ------------------------------------------------------------------------------


class ProgrLiqIvaFrame(aw.Frame):
    """
    Frame Gestione Progressivi liquidazioni IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        if not kwargs.has_key('size') and len(args) < 5:
            kwargs['size'] = (970,600)
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProgrLiqIvaPanel(self, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, self.FindWindowById(wdr.ID_SALVA))
    
    def OnClose(self, event):
        self.Close()
