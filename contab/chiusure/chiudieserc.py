#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/chiusure/chiudieserc.py
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

import contab
import contab.dbtables as dbc
import cfg.dbtables as dbx

import awc
import awc.controls.windows as aw
import awc.controls.linktable as lt

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLE = "Chiusura esercizio contabile"


class ChiusuraContabilePanel(wx.Panel):
    
    sovrapp = None
    
    def __init__(self, *args, **kwargs):
        self.dbese = dbx.ProgrEsercizio()
        self.dbprg = dbx.ProgrGiornaleDareAvere()
        self.dbgio = dbx.ProgrStampaGiornale()
        self.sovrapp = self.dbese.GetSovrapposizione()
        if self.sovrapp:
            wdr.ChiusuraContabileDescPanelFunc =\
               wdr.ChiusuraContabileSovrapposizioneDescPanelFunc
        else:
            wdr.ChiusuraContabileDescPanelFunc =\
               wdr.ChiusuraContabileNormaleDescPanelFunc
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ChiusuraContabileFunc(self)
        def cn(x):
            return self.FindWindowByName(x)
        if not self.sovrapp:
            ec = self.dbese.GetEsercizioInCorso()
            cn('esercold').SetValue(ec)
            cn('esercnew').SetValue(ec+1)
        self.Bind(wx.EVT_BUTTON, self.OnConferma, cn('update'))
    
    def OnConferma(self, event):
        if aw.awu.MsgDialog(self, "Confermi la chiusura?", 
                            style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
            return
        if self.ChiudiEsercizio():
            event.Skip()
    
    def ChiudiEsercizio(self):
        if self.sovrapp:
            o = self.ChiudiSovrapposizione()
        else:
            o = self.ChiudiNormale()
        if o:
            aw.awu.MsgDialog(self, "La chiusura è stata eseguita", style=wx.ICON_INFORMATION)
        return o
    
    def ChiudiNormale(self):
        def cn(x):
            return self.FindWindowByName(x)
        self.dbese.SetEsercizioInCorso(cn('esercnew').GetValue())
        self.dbese.SetSovrapposizione(False, movim=0)
        self.dbese.SetDataChiusura()
        self.dbprg.AzzeraProgressiviInCorso()
        self.dbgio.AzzeraProgressivi()
        return True
    
    def ChiudiSovrapposizione(self):
        if self.dbprg.ChiudiSovrapposizione():
            if self.dbese.SetSovrapposizione(False, movim=0):
                self.dbese.SetDataChiusura()
                return True
        return False


# ------------------------------------------------------------------------------


class ChiusuraContabileFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ChiusuraContabilePanel(self))
        self.CenterOnScreen()
        def cn(x):
            return self.FindWindowByName(x)
        self.Bind(wx.EVT_BUTTON, self.OnConferma, cn('update'))
    
    def OnConferma(self, event):
        import lib
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        self.Close()
