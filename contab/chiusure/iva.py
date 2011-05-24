#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/chiusure/iva.py
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

import contab.chiusure.chiusure_wdr as wdr

import contab.dbtables as dbc
import cfg.dbtables as dbx

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab

YEAR_MIN = 2009


FRAME_TITLE = "Chiusura annuale IVA"


class ChiusuraIVAPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        self.dbpliq = dbx.ProgrLiqIVA()
        
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ChiusuraIVAFunc(self)
        
        cn = self.FindWindowByName
        cn('nuovoanno').SetValue(Env.Azienda.Login.dataElab.year)
        
        self.UpdateStatus()
        
        wx.CallAfter(lambda: cn('nuovoanno').SetFocus())
        
        self.Bind(wx.EVT_TEXT, self.OnYearChanged, cn('nuovoanno'))
        self.Bind(wx.EVT_BUTTON, self.OnGeneraRiporto, cn('butgenera'))
    
    def OnYearChanged(self, event):
        self.UpdateStatus()
        event.Skip()
    
    def UpdateStatus(self):
        cn = self.FindWindowByName
        year = cn('nuovoanno').GetValue()
        m = ''
        ok = False
        if year<YEAR_MIN:
            m = "L'anno non può essere inferiore al %d" % YEAR_MIN
        else:
            p = self.dbpliq
            try:
                s = p.GetUltimaLiquidazione(year-1)
                d = s['data']
                c = s['credito']
            except Exception, e:
                d = c = None
                m = repr(e.args)
            cn('datuliq').SetValue(d)
            cn('creduliq').SetValue(c)
            if d is None:
                m = 'Data ultima liquidazione non definita per l\'anno %d' % (year-1) 
            elif d.month != 12 or d.day != 31:
                m = 'Ultima liquidazione non al 31/12'
            else:
                try:
                    p.GetUltimaLiquidazione(year)
                    m = 'Progressivi già esistenti per il %d!' % year
                except:
                    ok = True
        w = cn('warning')
        w.SetLabel(m)
        if ok:
            c = 'blue'
        else:
            c = 'red'
        w.SetForegroundColour(c)
        cn('butgenera').Enable(ok)
    
    def OnGeneraRiporto(self, event):
        if self.GeneraRiporto():
            event.Skip()
    
    def GeneraRiporto(self):
        if aw.awu.MsgDialog(self, "Confermi la generazione dei progressivi di liquidazione\ncosì come evidenziati?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            try:
                self.dbpliq.CreaProgressiviAnno(self.FindWindowByName('nuovoanno').GetValue())
                return True
            except Exception, e:
                aw.awu.MsgDialog(self, repr(e.args))
        return False


# ------------------------------------------------------------------------------


class ChiusuraIVAFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ChiusuraIVAPanel(self, -1))
        self.CenterOnScreen()
        cn = self.FindWindowByName
        self.Bind(wx.EVT_BUTTON, self.OnRiportoGenerato, cn('butgenera'))
    
    def OnRiportoGenerato(self, event):
        aw.awu.MsgDialog(self, "I progressivi sono stati creati.", style=wx.ICON_INFORMATION)
        self.Close()
