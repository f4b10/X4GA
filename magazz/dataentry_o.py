#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dataentry_o.py
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

#import wxversion
#wxversion.select('2.5')

import magazz
Env = magazz.Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

from magazz.dataentry import MagazzPanel, _FrameDialogMixin, STATUS_EDITING
import magazz.dataentry_wdr as wdr

import awc.controls.windows as aw

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib


FRAME_TITLE = "Documento magazzino"


class _MagazzPanel_O_Mixin(object):
    """
    Dataentry magazzino per contabilitï¿œ ordinaria
    """
    
    def InitPanelTot(self):
        """Inizializza il pannello dei totali"""
        def ci(x):
            return self.FindWindowById(x)
        if bt.TIPO_CONTAB == "O":
            #ordinaria
            self.gridtotpdc = GridTotPdc_O(ci(wdr.ID_PANGRIDTOTPDC),\
                                           self.dbdoc._info.totpdc)
            ci(wdr.ID_TOTSPLIT).SetSashPosition(400)
            ci(wdr.ID_TOTSPLIT).SetSashGravity(.6)
            self.gridtotiva = GridTotIva(ci(wdr.ID_PANGRIDTOTIVA),\
                                         self.dbdoc._info.totiva)
        else:
            #semplificata
            self.gridtotpdc = GridTotPdc_S(ci(wdr.ID_PANGRIDTOTPDC),\
                                           self.dbdoc._info.totpdc)
            self.gridtotiva = None
        self.GridScad_Init(ci(wdr.ID_SCADPANGRID))
        self.gridscad.SetColMaxChar(self.dbdoc.regcon.scad._GetFieldIndex('note', inline=True), 15)
        def cn(x):
            return self.FindWindowByName(x)
        self.Bind(wx.EVT_CHECKBOX, self.OnSogRitAcc, cn('sogritacc'))
        for name in 'per com imp'.split():
            self.Bind(wx.EVT_TEXT, self.OnRitAccChanged, cn('%sritacc' % name))
        self.Bind(wx.EVT_BUTTON, self.OnRitAccImponib, ci(wdr.ID_BUTRITACC))
    
    def OnSogRitAcc(self, event):
        sra = event.GetEventObject().GetValue()
        doc = self.dbdoc
        doc.sogritacc = sra
        if not sra:
            doc.totritacc = 0
            doc.totdare = doc.totimporto
            if doc.is_split_payment():
                doc.totdare -= doc.totimposta
        self.UpdateRitAcc()
        event.Skip()
    
    def UpdateRitAcc(self):
        doc = self.dbdoc
        us = False
        for ID, val in ((wdr.ID_TOTRITACC, doc.totritacc),
                        (wdr.ID_TOTDARE,   doc.totdare),):
            c = self.FindWindowById(ID)
            if not doc.samefloat((c.GetValue() or 0), (val or 0)):
                c.SetValue(val)
                us = True
        if us:
            doc.CalcolaScadenze()
            self.gridscad.ResetView()
            self.GridScadCheckImporti()
    
    def CalcolaRitAcc(self):
        doc = self.dbdoc
        doc.totritacc = round(doc.perritacc*doc.impritacc/100*doc.comritacc/100, 
                              bt.VALINT_DECIMALS)
        doc.totdare = doc.totimporto-doc.totritacc
        if doc.is_split_payment():
            doc.totdare -= doc.totimposta
    
    def OnRitAccChanged(self, event):
        if hasattr(self, 'stopritacc'):
            return
        def cn(x):
            return self.FindWindowByName(x)
        doc = self.dbdoc
        if self.status == STATUS_EDITING:
            self.stopritacc = True
            s, p, c, i = [cn('%sritacc' % x).GetValue() 
                          for x in 'sog per com imp'.split()]
            doc.sogritacc = s
            doc.perritacc = p
            doc.comritacc = c
            doc.impritacc = i
            self.CalcolaRitAcc()
            def UpdateScad():
                self.UpdateRitAcc()
                del self.stopritacc
            wx.CallAfter(UpdateScad)
        event.Skip()

    def OnRitAccImponib(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        cn('impritacc').SetValue(self.dbdoc.totimponib)
        event.Skip()

    def UpdatePanelFoot(self):
        doc = self.dbdoc
        warnctr = self.FindWindowByName('warnrowserr')
        warnctr.SetForegroundColour(wx.BLACK)
        warnctr.SetLabel("Totalizzazione in corso...")
        try:
            wx.Yield()#onlyIfNeeded=True)
        except:
            pass
        
        self.gridtotpdc.ResetView()
        if self.gridtotiva:
            self.gridtotiva.ResetView()
        self.gridscad.ResetView()
        self.GridScadCheckImporti()
        
        for ID, val in ((wdr.ID_TOTIMPONIB, doc.totimponib),\
                        (wdr.ID_TOTIMPOSTA, doc.totimposta),\
                        (wdr.ID_TOTIMPORTO, doc.totimporto),\
                        (wdr.ID_TOTDARE,    doc.totdare),\
                        (wdr.ID_TOTMERCE,   doc.totmerce),\
                        (wdr.ID_TOTSERVI,   doc.totservi),\
                        (wdr.ID_TOTSPESE,   doc.totspese),\
                        (wdr.ID_TOTTRASP,   doc.tottrasp),\
                        (wdr.ID_TOTSCRIP,   doc.totscrip),\
                        (wdr.ID_TOTSCMCE,   doc.totscmce),\
                        (wdr.ID_TOTSCPRA,   doc.totscpra),\
                        (wdr.ID_TOTOMAGG,   doc.totomagg),\
                        (wdr.ID_VENDITATOT, doc._totvend),\
                        (wdr.ID_COSTOTOT,   doc._totcost),\
                        (wdr.ID_MARGINEVAL, doc._totmargineval),\
                        (wdr.ID_MARGINEPERC,doc._totmargineperc),):
            c = self.FindWindowById(ID)
            c.SetValue(val)
            if c.IsTooBig():
                return False
        self.FindWindowById(wdr.ID_TOTSCTOT).SetValue(doc.totscmce+doc.totscpra)
        
        for ID, val in ((wdr.ID_SOGRITACC,  doc.sogritacc),\
                        (wdr.ID_PERRITACC,  doc.perritacc),\
                        (wdr.ID_COMRITACC,  doc.comritacc),\
                        (wdr.ID_IMPRITACC,  doc.impritacc),\
                        (wdr.ID_TOTRITACC,  doc.totritacc),):
            self.FindWindowById(ID).SetValue(val)
        
        out = False
        warnColor = wx.RED
        if doc.mov.Locate(lambda m: not self.GridBodyIsRowOK()):
            warnText = "Attenzione: sono presenti righe con dati incompleti"
        elif not doc.test_split_payment():
            warnText = "Attenzione: uso promiscuo di aliquote iva in split payment"
        else:
            warnText = "Il documento è composto da %d righe"\
                     % doc.mov.RowsCount()
            if self._headok:
                warnColor = wx.BLACK
                out = True
            else:
                warnText += " - Controllare dati in testata"
        warnctr.SetLabel(warnText)
        warnctr.SetForegroundColour(warnColor)
        self.rowsok = out
        self.UpdatePanelDAcc()
        return out
    
    
# ---------------------------------------------------------------------------


class MagazzPanel_O(MagazzPanel, _MagazzPanel_O_Mixin):
    
    def __init__(self, *args, **kwargs):
        #_MagazzPanel_O_Mixin.__init__(self)
        MagazzPanel.__init__(self, *args, **kwargs)
    
    def SetCausale(self, *args, **kwargs):
        MagazzPanel.SetCausale(self, *args, **kwargs)
        self.gridtotpdc.SetHiLitePdcErr(self.dbdoc.cfgdoc.colcg == 'X')

# ---------------------------------------------------------------------------


class GridTotIva(dbglib.DbGridColoriAlternati):
    """
    Gestione griglia totali iva x dataentry mag. su contab. ordinaria
    """
    def __init__(self, parent, rs):
        #costruzione griglia totali x aliquota iva
        size = parent.GetClientSizeTuple()
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size, style=0)
        
        _STR = gl.GRID_VALUE_STRING
        _FLT = bt.GetValIntMaskInfo()
        
        m = magazz
        cols = (( 40, (m.RSIVA_codiva,  "Codice",       _STR, True )),\
                ( 90, (m.RSIVA_desiva,  "Aliquota IVA", _STR, True )),\
                (110, (m.RSIVA_IMPONIB, "Imponibile",   _FLT, True )),\
                (110, (m.RSIVA_IMPOSTA, "Imposta",      _FLT, True )),\
                (110, (m.RSIVA_IMPORTO, "Totale",       _FLT, True )))        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(rs, colmap, canEdit=True)
        
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


# ------------------------------------------------------------------------------


class GridTotPdc_O(dbglib.DbGridColoriAlternati):
    """
    Gestione griglia totali su sottoconti di costo/ricavo x dataentry 
    mag. su contab. ordinaria
    """
    def __init__(self, parent, rs):
        #costruzione griglia totali x sottoconto di costo/ricavo
        size = parent.GetClientSizeTuple()
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size, style=0)
        self.rs = rs
        self._hilitepdcerr = False
        
        cols = self.CreateColumns()
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        self.SetData(rs, colmap, canEdit=True)
        
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
    
    def CreateColumns(self):
        m = magazz
        _STR = gl.GRID_VALUE_STRING
        _FLT = bt.GetValIntMaskInfo()
        cols = (( 50, (m.RSPDC_codpdc,  "Codice",     _STR, True )),\
                (180, (m.RSPDC_despdc,  "Sottoconto", _STR, True )),\
                (110, (m.RSPDC_IMPONIB, "Imponibile", _FLT, True )))
        return cols
    
    def GetAttr(self, row, col, rscol, attr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        if row<len(self.rs):
            if self._hilitepdcerr and self.rs[row][magazz.RSPDC_ID] is None and not self.rs[row][magazz.RSPDC_ISOMAGG]:
                attr.SetBackgroundColour(stdcolor.VALERR_BACKGROUND)
        return attr
    
    def SetHiLitePdcErr(self, h=True):
        self._hilitepdcerr = h


# ------------------------------------------------------------------------------


class GridTotPdc_S(GridTotPdc_O):
    
    def CreateColumns(self):
        m = magazz
        _STR = gl.GRID_VALUE_STRING
        _FLT = bt.GetValIntMaskInfo()
        cols = (( 50, (m.RSPDC_codpdc,  "Codice",       _STR, True )),
                (180, (m.RSPDC_despdc,  "Sottoconto",   _STR, True )),
                ( 35, (m.RSPDC_aliqcod, "Cod.",         _STR, True )),
                (200, (m.RSPDC_aliqdes, "Aliquota IVA", _STR, True )),
                (110, (m.RSPDC_IMPONIB, "Imponibile",   _FLT, True )),
                (110, (m.RSPDC_IMPOSTA, "Imposta",      _FLT, True )),
                (110, (m.RSPDC_IMPORTO, "Totale",       _FLT, True )),
                (110, (m.RSPDC_DESTOT,  "Desc.Tot.",    _STR, True )),)
        return cols


# ------------------------------------------------------------------------------


class MagazzFrame_O(aw.Frame, _FrameDialogMixin):
    """
    Frame Dataentry documenti magazzino contabilità ordinaria.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = MagazzPanel_O(self, -1, name='dataentrypanel')
        _FrameDialogMixin.__init__(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        def cn(x): return self.FindWindowByName(x)
        for name in 'save del print quit'.split():
            self.Bind(wx.EVT_BUTTON, self.OnCloseFrame, cn('but%s'%name))
    
    def OnCloseFrame(self, event):
        self.FixTimerProblem()
        self.Close()
    
    def OnClose(self, event):
        if self.panel.TestQuit():
            self.FixTimerProblem()
            event.Skip()


# ------------------------------------------------------------------------------


class MagazzDialog_O(aw.Dialog, _FrameDialogMixin):
    """
    Dialog Dataentry documenti magazzino contabilità ordinaria.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = MagazzPanel_O(self, -1, name='dataentrypanel')
        _FrameDialogMixin.__init__(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        for name, func in (("butsave",  self.OnSave),
                           ("butdel",   self.OnDelete),
                           ("butquit",  self.OnQuit),
                           ("butprint", self.OnSave),
                           ):
            self.Bind(wx.EVT_BUTTON, func, self.FindWindowByName(name))
    
    def OnSave(self, event):
        self._Close(magazz.DOC_MODIFIED)
    
    def OnDelete(self, event):
        self._Close(magazz.DOC_DELETED)
    
    def OnQuit(self, event):
        self._Close(magazz.DOC_UNMODIFIED)
    
    def EndModal(self, value):
        self.FixTimerProblem()
        aw.Dialog.EndModal(self, value)
    
    def _Close(self, mode):
        if self.IsModal():
            self.EndModal(mode)
        else:
            self.Close()
