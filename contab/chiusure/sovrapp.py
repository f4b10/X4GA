#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         contab/chiusure/sovrapp.py
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


FRAME_TITLE = "Sovrapposizione di esercizio"


class SovrapposizionePanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.SovrapposizioneFunc(self)
        
        self.dbese = dbx.ProgrEsercizio()
        self.dbprg = dbx.ProgrGiornaleDareAvere()
        
        def cn(x):
            return self.FindWindowByName(x)
        
        ec = self.dbese.GetEsercizioInCorso()
        
        cn('esercold').SetValue(ec)
        
        err = ''
        sa = self.dbese.GetSovrapposizione()
        if sa:
            err = 'Sovrapposizione già attiva - Verificare chiusure'
        
        if err:
            cn('warning').SetLabel(err)
            cn('update').Disable()
        else:
            cn('esercnew').SetValue(ec+1)
        
        self.Bind(wx.EVT_BUTTON, self.OnAttiva, cn('update'))
    
    def OnAttiva(self, event):
        if self.AttivaSovrapposizione():
            event.Skip()
    
    def AttivaSovrapposizione(self):
        if aw.awu.MsgDialog(self, "Confermi l'attivazione della sovrapposizione?", style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
            return
        def cn(x):
            return self.FindWindowByName(x)
        def ErrDialog(x):
            return aw.awu.MsgDialog(self, message=x, style=wx.ICON_ERROR)
        ese = self.dbese
        prg = self.dbprg
        err = None
        try:
            prg.AttivaSovrapposizione()
        except Exception, e:
            ErrDialog(repr(e.args))
        else:
            ne = cn('esercnew').GetValue()
            if not ese.SetEsercizioInCorso(ne, sovrapp=True):
                ErrDialog(repr(ese.GetError()))
                return
            aw.awu.MsgDialog(self, message="E' stato creato l'esercizio %s ed attivata la sovrapposizione" % ne, style=wx.ICON_INFORMATION)
            return True
        return False


# ------------------------------------------------------------------------------


class SovrapposizioneFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(SovrapposizionePanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnAttiva, self.FindWindowByName('update'))
    
    def OnAttiva(self, event):
        import lib
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        self.Close()
