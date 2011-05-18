#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/chiusure/consocos.py
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
import magazz.chiusure.chiusure_wdr as wdr

import Env
bt = Env.Azienda.BaseTab

import magazz.chiusure.dbtables as dbx


CONSOLIDA_COSTI_TITLE = "Consolidamento costi prodotti"


class ConsolidamentoCostiPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.ConsolidaCostiFunc(self)
        self.dbcoc = dbx.ConsolidaCosti()
        def cn(x):
            return self.FindWindowByName(x)
        d = Env.Azienda.Login.dataElab
        if d.month == 12:
            y = d.year
        else:
            y = d.year-1
        cn('anno').SetValue(y)
        cn('annocanc').SetValue(0)
        self.Bind(wx.EVT_TEXT, self.OnYearChanged, cn('anno'))
        self.Bind(wx.EVT_TEXT, self.OnCancYearChanged, cn('annocanc'))
        self.Bind(wx.EVT_BUTTON, self.OnStart, cn('btnstart'))
        self.Bind(wx.EVT_BUTTON, self.OnCancella, cn('btncanc'))
        self.TestYear()
        self.TestCancYear()
    
    def OnCancella(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        if aw.awu.MsgDialog(self, "Confermi l'eliminazione?",
                            style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            self.CancellaCostiAnno()
            aw.awu.MsgDialog(self, "Costi eliminati per l'anno indicato")
            event.Skip()
    
    def CancellaCostiAnno(self):
        def cn(x):
            return self.FindWindowByName(x)
        anno = cn('annocanc').GetValue()
        self.dbcoc.EliminaCostiConsolidatiAnno(anno)
        self.dbcoc.EliminaGiacenzeAnno(anno)
    
    def OnStart(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        y = cn('anno').GetValue()
        d = cn('datgiac').GetValue()
        err = None
        if not d:
            err = 'La data di determinazione delle giacenze è obbligatoria'
        elif d.year != y:
            err = "L'anno della data di determinazione delle giacenze è diverso dall'anno digitato"
        if err:
            msg = err
            stl = wx.ICON_ERROR
        else:
            msg = "Confermi il consolidamento dei costi e delle giacenze?"
            stl = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
        if aw.awu.MsgDialog(self, msg, style=stl) != wx.ID_YES:
            return
        self.GeneraCosti()
        event.Skip()
    
    def GeneraCosti(self):
        def cn(x):
            return self.FindWindowByName(x)
        w = aw.awu.WaitDialog(self, maximum=0)
        try:
            coc = self.dbcoc
            def Costi_SetMax(i):
                w.SetRange(i.RowsCount())
            def Costi_SetValue(n):
                w.SetValue(n)
            def Giac_SetMag(mag):
                w.SetMessage("Giacenze magazzino %s - %s" % (mag.codice, mag.descriz))
                w.SetRange(0)
            def Giac_SetMax(mag, inv):
                w.SetRange(inv.RowsCount())
            def Giac_SetValue(mag, inv, n):
                w.SetValue(n)
            try:
                anno = cn('anno').GetValue()
                dgia = cn('datgiac').GetValue()
                coc.ConsolidaCostiAnno(anno, func0=Costi_SetMax, func1=Costi_SetValue)
                coc.CreaGiacenzeAnno(anno, dgia, func0=Giac_SetMag, func1=Giac_SetMax, func2=Giac_SetValue)
                aw.awu.MsgDialog(self, "Consolidamento costi e giacenze eseguito.")
            except Exception, e:
                aw.awu.MsgDialog(self, repr(e.args))
        finally:
            w.Destroy()
    
    def OnYearChanged(self, event):
        self.TestYear()
        event.Skip()
    
    def OnCancYearChanged(self, event):
        self.TestCancYear()
        event.Skip()
    
    def TestYear(self):
        def cn(x):
            return self.FindWindowByName(x)
        m = ''
        y = cn('anno').GetValue()
        if not y:
            m = "L'anno di riferimento è obbligatorio"
        elif y < 2000 or y > Env.Azienda.Login.dataElab.year:
            m = "L'anno è errato"
        else:
            cn('datgiac').SetValue(Env.DateTime.Date(y,12,31))
            coc = self.dbcoc
            n = coc.EsistonoCostiAnno(y)
            if n:
                m = "Costi già esistenti per l'anno"
        cn('warning').SetLabel(m)
        cn('btnstart').Enable(not bool(m))
    
    def TestCancYear(self):
        def cn(x):
            return self.FindWindowByName(x)
        m = ''
        y = cn('annocanc').GetValue()
        ok = False
        if not y:
            m = "L'anno di riferimento è obbligatorio"
        elif y < 2000 or y > Env.Azienda.Login.dataElab.year+1:
            m = "L'anno è errato"
        else:
            coc = self.dbcoc
            n = coc.EsistonoCostiAnno(y)
            if n:
                m = "%d prodotti con costo consolidato per il %d" % (n, y)
                ok = True
            else:
                m = "Nessun prodotto con costo consolidato per il %d" % y
        cn('warncanc').SetLabel(m)
        cn('btncanc').Enable(ok)



# ------------------------------------------------------------------------------


class ConsolidamentoCostiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not 'title' in kwargs:
            kwargs['title'] = CONSOLIDA_COSTI_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ConsolidamentoCostiPanel(self))
        self.CenterOnScreen()
        def cn(x):
            return self.FindWindowByName(x)
        self.Bind(wx.EVT_BUTTON, self.OnDone, cn('btnstart'))
        self.Bind(wx.EVT_BUTTON, self.OnDone, cn('btncanc'))
    
    def OnDone(self, event):
        self.Close()
