#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/linktable.py
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

import string
import wx
import wx.lib.newevent

import MySQLdb

from linktable_wdr import LinkTableGridFunc, CodiceDescrizTextCtrl,\
     ID_TXT_CODICE, ID_TXT_DESCRIZ, ID_BTN_NEW, ID_BTN_FLT

import awc.util as awu
import awc.controls.mixin as cmix
from awc.controls.textctrl import TextCtrl
from awc.controls.windows import SetDefaultButton
import wx.grid as gridlib

from awc.controls.button import FlatButton

import images

import stormdb as adb

import awc.wxinit as wxinit


evt_LINKTABCHANGED = wx.NewEventType()
EVT_LINKTABCHANGED = wx.PyEventBinder(evt_LINKTABCHANGED, 1)

evt_LINKTABFORCED = wx.NewEventType()
EVT_LINKTABFORCED = wx.PyEventBinder(evt_LINKTABFORCED, 1)

evt_LTABHELPSELECTED = wx.NewEventType()
EVT_LTABHELPSELECTED = wx.PyEventBinder(evt_LTABHELPSELECTED, 1)

evt_LINKTABFOCUSLOST = wx.NewEventType()
EVT_LINKTABFOCUSLOST = wx.PyEventBinder(evt_LINKTABFOCUSLOST, 1)


COLOR_NORMAL = None
COLOR_PLURICOD = "aquamarine"
COLOR_ERROR = "red"

import awc.controls
COLORS_GRID = awc.controls.SEARCH_COLORS1
COLORS_LABEL = 'black darkseagreen3'.split()

GRID_HEIGHT = 200


class LinkTableChangedEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self._selection = None

    def SetSelection(self, val):
        self._selection = val

    def GetSelection(self):
        return self._selection


# ------------------------------------------------------------------------------


class LinkTableForcedEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self._selection = None

    def SetSelection(self, val):
        self._selection = val

    def GetSelection(self):
        return self._selection


# ------------------------------------------------------------------------------


class LinkTableFocusLostEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self._selection = None

    def SetSelection(self, val):
        self._selection = val

    def GetSelection(self):
        return self._selection


# ------------------------------------------------------------------------------


def _OpApp(s1, s2, op):
    s = s1
    if s1 and s2:
        s += ' %s ' % op
    s += s2
    return s


# ------------------------------------------------------------------------------


def AndApp(s1, s2):
    return _OpApp(s1, s2, 'AND')


# ------------------------------------------------------------------------------


def OrApp(s1, s2):
    return _OpApp(s1, s2, 'OR')


# ------------------------------------------------------------------------------


# ------------------------------------------------------------------------------

INITFOCUS_CODICE = 0
INITFOCUS_DESCRIZ = 1

class LinkTable(wx.Control,\
                cmix.ControlsMixin):
    """
    Help ricerca tabelle.
    """
    db_name = ''
    db_alias = ''

    digitsearch_oncode = True
    @classmethod
    def SetDigitSearchOnCode(self, ds):
        self.digitsearch_oncode = ds
    
    digitsearch_ondescriz = True
    @classmethod
    def SetDigitSearchOnDescriz(self, ds):
        self.digitsearch_ondescriz = ds
    
    tabsearch_oncode = False
    @classmethod
    def SetTabSearchOnCode(self, ts):
        self.tabsearch_oncode = ts
    
    tabsearch_ondescriz = False
    @classmethod
    def SetTabSearchOnDescriz(self, ts):
        self.tabsearch_ondescriz = ts
    
    def SetCodExclusive(self, ce):
        self.codexclusive = ce
    
    codice_fieldname = 'codice'
    def SetCodiceFieldName(self, fn):
        self.codice_fieldname = fn
    def GetCodiceFieldName(self):
        return self.codice_fieldname
    
    descriz_fieldname = 'descriz'
    def SetDescrizFieldName(self, fn):
        self.descriz_fieldname = fn
    def GetDescrizFieldName(self):
        return self.descriz_fieldname
    
    isapp = (wx.GetApp() is not None)
    if not isapp:
        dummy_app = wx.PySimpleApp()
    f = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FIXED_FONT)
    if not isapp:
        dummy_app.Destroy()
    
    _codewidth = wxinit.GetCodiceStandardWidth()#40
    _descwidth = None
    
    def __init__(self, parent, id, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.NO_BORDER, **lt_kwargs):
        
        wx.Control.__init__(self, parent, id, pos, size, style)
        cmix.ControlsMixin.__init__(self)
        
        self.obligatory = False
        self.currentid = None
        self.iderror = False
        self.canedit = True
        self.canins = True
        self.cansee = True
        self.initfocus = INITFOCUS_CODICE
        
        self._ctrcod = None
        self._ctrdes = None
        self._win = None
        
        self.PreSetVal = None
        
        self.db_curs = None
        self.cardclass = None
        self.dyncard = None
        self.filter = None
        self.apply_filter_on_setvalue = True
        self.basefilter = None
        self.filterdyn = None
        self.valuesearch = []
        self.fixvaluesearch = False
        self.filterlinks = []
        self.filtervalues = []
        self.filterlinkstitle = None
        self.exactcode = False
        self.codexclusive = False #ricerca esclusiva sul codice (se esatto, prende il record anche se ce ne sono altri con lo stesso inizio di codice)
        
        self._fltlink_ydes = 12
        self._fltlink_ydelta = 20
        self._resize = False
        self._minwidth = 200
        self.NORECALCS = False
        
        self._grid_maxcode = None
        self._grid_maxdesc = None
        
        self.reset_fields_on_focus_lose = True
        
        self._rs = None
        
        self._stopevents = False
        
        self._helpInProgress = False
        self._testNone = True
        self._basestyle = self.GetWindowStyle()
        
        global COLOR_NORMAL
        COLOR_NORMAL = wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW)
        
#        self._panel = wx.Panel(self, -1, style=wx.NO_BORDER)
        LinkTableGridFunc(self)#self._panel)
        
        s = wx.FlexGridSizer( 0, 1, 0, 0 )
        s.AddGrowableCol( 0 )
#        s.Add( self._panel, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0 )
        s.Add(self, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
#        self._panel.SetSizer(s)
        self.SetSizer(s)
        s.SetSizeHints(self)
        
#        if self._codewidth is not None:
#            self.SetCodeWidth(self._codewidth)
#        if self._descwidth is not None:
#            self.SetDescriptionWidth(self._descwidth)
        
        self._ctrcod = self.FindWindowById( ID_TXT_CODICE )
        self._ctrdes = self.FindWindowById( ID_TXT_DESCRIZ )
        self._btncrd = self.FindWindowById( ID_BTN_NEW )
        w, h = self._ctrcod.GetSize()
        self._btncrd.SetSize((h, h))
        self._btnflt = self.FindWindowById( ID_BTN_FLT )
        self._btnflt.SetToolTipString('Visualizza filtro (F12)')
        self._btnflt.Show(False)
        
        self._ctrcod.SetName("_lt%d_codice" % self.GetId())
        self._ctrdes.SetName("_lt%d_descriz" % self.GetId())
        self._btncrd.SetName("_lt%d_button_card" % self.GetId())
        self._btnflt.SetName("_lt%d_button_filt" % self.GetId())
        
        try:
            self.db_curs = wx.GetApp().dbcon.cursor()
        except MySQLdb.Error, e:
            dlg = wx.MessageDialog(parent=self,
                                   caption="Errore",
                                   message=repr(e.args),
                                   style=wx.ICON_ERROR)
            dlg.Destroy()
        
##        wx.CallAfter(self._setDim) 
#        def InitDim():
#            s = self._ctrcod.GetSize()
#            self._ctrcod.SetSize((self._codewidth or  40, s[1]))
#            s = self._ctrdes.GetSize()
#            self._ctrdes.SetSize((self._descwidth or 120, s[1]))
#            self._setDim(firstTime=True)
#        wx.CallAfter(InitDim)
        
        awu.GetParentFrame(self).Bind(wx.EVT_MOVE, self.OnFatherMove)
#        awu.GetParentFrame(self).Bind(wx.EVT_SIZE, self.OnSizeChanged)
        self.Bind(wx.EVT_SIZE, self.OnSizeChanged, awu.GetParentFrame(self))
        
        for control in (self._ctrcod, self._ctrdes):
            control.Bind(wx.EVT_LEFT_DCLICK, self.OnLeft_DClick)
            control.Bind(wx.EVT_CHAR,        self.OnChar)
            control.Bind(wx.EVT_SET_FOCUS,   self.OnSetFocus)
            control.Bind(wx.EVT_KILL_FOCUS,  self.OnKillFocus)
        
        self.Bind(wx.EVT_BUTTON, self.OnCard, id=ID_BTN_NEW)
        self.Bind(wx.EVT_BUTTON, self.OnFilters, id=ID_BTN_FLT)
        
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocusGain)
    
        self.Bind(wx.EVT_SIZE, self.OnSizeChanged)
        wx.CallAfter(self._setDim)
    
    def Disable(self):
        self.Enable(False)
    
    def Enable(self, e=True, set_editable=True):
        for c in (self._ctrcod, self._ctrdes):
            c.Enable(e)
        if set_editable:
            for c in (self._ctrcod, self._ctrdes):
                c.SetEditable(e)
    
    def AdjustBackgroundColor(self, focused=False, obj=None, func=None, error=False):
        for c in (self._ctrcod, self._ctrdes):
            c.AdjustBackgroundColor(c.FindFocus() is c)
    
    def IsEnabled(self):
        return self._ctrcod.IsEnabled() or self._ctrdes.IsEnabled()
    
    def IsEditable(self):
        return self._ctrcod.IsEditable() or self._ctrdes.IsEditable()
    
    def ApplyFilterOnSetValue(self, aposv=True):
        self. apply_filter_on_setvalue = aposv
    
    def SetGridMaxCodeWidth(self, wmax):
        self._grid_maxcode = wmax
        
    def GetGridMaxCodeWidth(self):
        return self._grid_maxcode
    
    def SetGridMaxDescWidth(self, wmax):
        self._grid_maxdesc = wmax
        
    def GetGridMaxDescWidth(self):
        return self._grid_maxdesc
    
    def SetFont(self, *args, **kwargs):
        for c in (self._ctrcod, self._ctrdes):
            c.SetFont(*args, **kwargs)
    
    def SetTips(self):
        tt = """Digitare %(cd1)s. Per cercare mediante iniziali, digitarle e premere il tasto 
freccia giù per ottenere l'elenco delle voci che iniziano con il testo digitato.
Per cercare mediante contenuto, digitare .. seguito dal testo da ricercare all'interno del%(cd2)s.
(Doppio-click) Visualizza tutte le voci a prescindere dal testo digitato.
(F3) Azzera la selezione attiva"""
        
        if self.cardclass or self.dyncard:
            tt += """
(Ctrl-Ins) Inserisce una nuova voce.
(F11) Richiama la scheda della voce selezionata.
(F8)  Imposta le selezioni di Cerca valori."""
        
        tt += self.GetExtraToolTip()
        
        self._ctrcod.SetToolTipString(tt % {'cd1': 'il codice',
                                            'cd2': ' codice'})
        self._ctrdes.SetToolTipString(tt % {'cd1': 'la descrizione',
                                            'cd2': 'la descrizione'})
    
    def GetExtraToolTip(self):
        return ""
    
    def OnFatherMove(self, event):
        try:
            self.AdjustFilterLinksTitle()
        except wx.PyDeadObjectError:
            pass
        event.Skip()
    
    def OnFilters(self, event):
        wx.CallAfter(self.ShowFilters)
        event.Skip()
    
    def IsIdErr(self):
        return self.iderror
    
    def GetCtrlCodice(self):
        return self._ctrcod
    
    def GetCtrlDescriz(self):
        return self._ctrdes
    
    def GetCtrlScheda(self):
        return self._btncrd
    
    def SetName(self, name):
        wx.Control.SetName(self, name)
        self._ctrcod.SetName("_%s_codice" % name)
        self._ctrdes.SetName("_%s_descriz" % name)
        self._btncrd.SetName("_%s_button_card" % name)
    
    def OnFocusGain(self, event):
        self.TestInitFocus()
        event.Skip()
    
    def TestInitFocus(self):
        def SetFocus():
            if self.initfocus == INITFOCUS_CODICE:
                self._ctrcod.SetFocus()
            elif self.initfocus == INITFOCUS_DESCRIZ:
                self._ctrdes.SetFocus()
        wx.CallAfter(SetFocus)
    
    def SetInitFocus(self, f):
        o = self.initfocus
        self.initfocus = f
        return o
    
    def SetExactCode(self, ec):
        out = self.exactcode
        self.exactcode = ec
        return out
    
    def NotifyChanges(self, notify=True):
        current = self.notifyChanges
        self.notifyChanges = notify
        return current
    
    #def SetFocus(self, *args):
        #return wx.Control.SetFocus(self, *args)
    
    def OnSetFocus(self, event):
        if not self: return
        if self.FindFocus() in (self._ctrcod, self._ctrdes):
            if self.filterlinks or self.valuesearch:
                self.ShowFilterLinksTitle()
        event.Skip()
    
    def OnKillFocus(self, event):
        if not self: return
        if not self.HasFocus():
            if self.currentid is None:
                if self.reset_fields_on_focus_lose:
                    for c in (self._ctrcod, self._ctrdes):
                        if c.GetValue():
                            c.SetValue('')
            if not self._ctrcod.GetValue() and not self._ctrdes.GetValue() and self.GetValue() is None and not self._helpInProgress:
                self.SetValue(None)
            self._PostEventFocusLost()
            self.HideFilterLinksTitle()
        event.Skip()
    
    def ShowFilterLinksTitle(self):
        if self.filterlinkstitle is not None:
            self.HideFilterLinksTitle()
        if not self.IsEnabled() or not self.IsShown() or not self.HasFocus():
            return
        if wx.Platform == '__WXGTK__':
            parent = self.GetParent()
        else:
            parent = self
        x, y = self.GetPosition()
        w, h = self.GetSize()
        th = 18
        ph = th*len(self.filterlinks)
        if self.valuesearch:
            ph += th
        c = wx.PopupWindow(parent, wx.SIMPLE_BORDER)
        p = wx.Panel(c)
        fg, bg = COLORS_GRID
        p.SetForegroundColour(fg)
        p.SetBackgroundColour(bg)
        c.panel = p
        self.filterlinkstitle = c
        sz = wx.FlexGridSizer(0,2,0,0)
        sz.AddGrowableCol(1)
        align = wx.ALIGN_BOTTOM|wx.LEFT
        for n, fl in enumerate(self.filterlinks):
            label = wx.StaticText(p, -1, fl[0]+":")
            sz.Add(label, 0, align|wx.ALIGN_RIGHT, 5)
            v = self.filtervalues[n][2]
            if v is None:
                v = "QUALSIASI"
                tt = "Nessun filtro impostato su %s" % fl[0].lower()
            else:
                v = '%s - %s' % (v[0] or '', v[1] or '')
                tt = "Verranno mostrate solo le voci che hanno %s = %s"\
                   % (fl[0].lower(), v)
            value = wx.StaticText(p, -1, v)
            for c in (label, value):
                c.SetToolTipString(tt)
            sz.Add(value, 0, align|wx.ALIGN_LEFT, 5)
        if self.valuesearch:
            label = wx.StaticText(p, -1, "Cerca valori:")
            sz.Add(label, 0, align|wx.ALIGN_RIGHT, 5)
            label = wx.StaticText(p, -1, "ATTIVO (%d selez.)" \
                                  % len(self.valuesearch))
            label.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD))
            sz.Add(label, 0, align|wx.ALIGN_LEFT, 5)
            tt = []
            for tab,col,val in self.valuesearch:
                t = '%s.%s = ' % (tab, col)
                if type(val) in (str, unicode):
                    t += '<%s>' % val
                else:
                    t += repr(val)
                tt.append(t)
            tt.sort(lambda x,y: len(x)>len(y))
            if tt:
                label.SetToolTipString('\n'.join(tt))
        p.SetSizer(sz)
        for f in awc.util.GetAllChildrens(c):
            f.Bind(wx.EVT_LEFT_UP, lambda *x: self.HideFilterLinksTitle())
        c = self.filterlinkstitle
        c.SetSize((0,ph))
        self.AdjustFilterLinksTitle()
        c.Show()
    
    def AdjustFilterLinksTitle(self):
        c = self.filterlinkstitle
        if c:
            w, h = (self.GetSize()[0], c.GetSize()[1])
            c.SetSize((0,0))
            if wx.Platform == '__WXGTK__':
                pos = self.ClientToScreen((0,self.GetSize()[1]))
                c.SetPosition(pos)
            else:
                c.SetPosition((0,self.GetSize()[1]))
            c.SetSize((w,h))
            c.panel.SetSize(c.GetClientSize())
    
    def HideFilterLinksTitle(self):
        if self.filterlinkstitle:
            self.filterlinkstitle.Destroy()
            self.filterlinkstitle = None
    
    def Destroy(self):
        if self.filterlinkstitle:
            self.filterlinkstitle.Destroy()
        wx.Control.Destroy()
    
    def HasFocus(self):
        return self.FindFocus() in awc.util.GetAllChildrens(self)
        
    def TestValueNone(self):
        if not self._ctrcod.GetValue() and\
           not self._ctrdes.GetValue():
            self.ResetValue()
    
    def SetCodeWidth(self, cw):
        self._codewidth = cw
        def Dim():
            self._ctrcod.SetSize((cw, self._ctrcod.GetSize()[1]))
            self._setDim()
        wx.CallAfter(Dim)

    def SetDescriptionWidth(self, dw):
        self._descwidth = dw
        def Dim():
            self._ctrdes.SetSize((dw, self._ctrdes.GetSize()[1]))
            self._setDim()
        wx.CallAfter(Dim)

    def _setDim(self, firstTime=False):
        if self.NORECALCS:
            return
        x = self.GetPosition()[0]
        y = self.GetPosition()[1]
        if firstTime:
            wcod = self._ctrcod.GetSize()[0]
            if self._descwidth == 0:
                wdes = 0
            else:
                wdes = self._ctrdes.GetSize()[0]
        else:
            if self._codewidth is None:
                wcod = self._ctrcod.GetSize()[0]
                if self._descwidth == 0:
                    wdes = 0
                elif self._descwidth is None:
                    wdes = self.GetSize()[0]-wcod
                else:
                    wdes = self._descwidth
            else:
                wcod = self._codewidth
                if self._descwidth == 0:
                    wdes = 0
                else:
                    wdes = self.GetSize()[0]-wcod
        if wcod and wdes:
            wdes -= 5
        if self._btncrd.IsShown():
            w = self._btncrd.GetSize()[0]
            if wdes:
                wdes -= w
            else:
                wcod -= w
        if self._btnflt.IsShown():
            w = self._btnflt.GetSize()[0]
            if wdes:
                wdes -= w
            else:
                wcod -= w
#        if wdes<80 and self._descwidth is None:
#            wdes = 80
        self.SetDimensions(x, y, wcod, wdes, self.GetSize()[1],\
                           wx.SIZE_ALLOW_MINUS_ONE)
    
    def SetDimensions(self, x, y, wcod, wdes, h, f):
        ydelta = self._fltlink_ydelta
        ydes = self._fltlink_ydes
        wtot = wcod+wdes
        if wcod and wdes:
            wtot += 2
        if self.NORECALCS:
            if self._btncrd.IsShown():
                w = self._btncrd.GetSize()[0]
                if wdes:
                    wdes -= w
                else:
                    wcod -= w
            if self._btnflt.IsShown():
                w = self._btnflt.GetSize()[0]
                if wdes:
                    wdes -= w
                else:
                    wcod -= w
        else:
            if self._btncrd.IsShown():
                wtot += self._btncrd.GetSize()[0]
            if self._btnflt.IsShown():
                wtot += self._btnflt.GetSize()[0]
        wx.Control.SetDimensions(self, x, y, wtot, h, f)
        self._ctrcod.SetPosition((0,0))
        self._ctrcod.SetSize((wcod, h))
        if wcod == 0:
            self._ctrcod.Hide()
        elif wdes == 0:
            self._ctrdes.Hide()
        _x = wcod
        if wcod and wdes:
            _x += 2
        self._ctrdes.SetPosition((_x, 0))
        self._ctrdes.SetSize((wdes, h))
        _x += wdes
        self._btncrd.SetPosition((_x, 0))
        if self._btncrd.IsShown():
            _x += self._btncrd.GetSize()[0]
        self._btnflt.SetPosition((_x, 0))
        self.Refresh()

    def OnLeft_DClick(self, event):
        if not self._ctrcod.IsEditable(): return
        obj = event.GetEventObject()
        self.HelpChoice(obj, forceAll = True)
        #event.Skip()

    #def OnTextChanged(self, event):
        #obj = event.GetEventObject()
    def TextChangedOn(self, obj, cp1):
        assert isinstance(obj, CodiceDescrizTextCtrl)
        if self._stopevents:
            return
        if obj is self._ctrcod and (not self.digitsearch_oncode and obj.GetValue()):
            return
        if obj is self._ctrdes and (not self.digitsearch_ondescriz and obj.GetValue()):
            return
        if not self._helpInProgress and obj.IsEditable() and not '..' in (obj.GetValue() or ''):
            if obj.notifyChanges:
                if obj.GetValue():
                    #codice/descriz con contenuto, attivo ricerca x
                    #determinazione immediata
                    obj.notifyChanges = False
                    self.HelpChoice(obj, False)
                    obj.notifyChanges = True
                    cp2 = len(obj.GetValue())
                    if cp1 != cp2:
                        #seleziono la parte di testo rimanente rispetto a quanto digitato
                        wx.CallAfter(lambda: obj.SetSelection(cp2,cp1))
                else:
#                    #codice/descriz annullato, annullo il valore di linktable
                    self.SetValue(None)
            if self._testNone:
                self._testNone = False
                self.TestValueNone()
                self._testNone = True

    def OnChar(self, event):
        
        if not self.IsShown():
            return
        
        obj = event.GetEventObject()
        active = (self.IsEnabled() and self.IsEditable())
        
        if event.GetKeyCode() == wx.WXK_DOWN and active:
            #FRECCIA GIU' richiama elenco
            self._fromkeydown = True
            self.HelpChoice(obj, exact=False, resetFields=False)
            del self._fromkeydown
            
        elif event.GetKeyCode() == wx.WXK_TAB and not event.ControlDown():
            #TAB controllo prossimo focus
            if event.ShiftDown():
                if obj == self._ctrdes:
                    self._ctrcod.SetFocus()
                elif obj == self._ctrcod:
                    self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                if obj == self._ctrcod:
                    do = True
                    if self.tabsearch_oncode:
                        if self._ctrcod.GetValue():
                            self._fromtab = True
                            do = self.HelpChoice(obj, exact=False, resetFields=False)
                            del self._fromtab
                    if do:
                        self._ctrdes.SetFocus()
                elif obj == self._ctrdes:
                    do = True
                    if self.tabsearch_ondescriz:
                        if self._ctrdes.GetValue():
                            do = self.HelpChoice(obj, exact=False, resetFields=False)
                    if do:
                        self.Navigate(wx.NavigationKeyEvent.IsForward)
            
        elif event.GetKeyCode() == wx.WXK_F3 and active:
            #F3 azzera selezione attiva
            self.ResetValue()
            
        elif event.GetKeyCode() == wx.WXK_F8 and active:
            #F8 richiama cerca valori (filtro da contenuto campi)
            obj = event.GetEventObject()
            if obj in (self._ctrcod, self._ctrdes):
                if self.CallValueSearch():
                    if not self.HelpChoice(obj):
                        self.ShowFilterLinksTitle()
            
        elif event.GetKeyCode() == wx.WXK_F11:
            #F11 richiama scheda elemento
            self.CallCard()
            
        elif event.GetKeyCode() == wx.WXK_INSERT and event.ControlDown() and active:
            #Ctrl-Ins nuovo elemento
            self.CallCard(new=True)
            
        elif event.GetKeyCode() == wx.WXK_F12 and self._btnflt.IsShown() and active:
            #F12 finestra filtri
            self.ShowFilters()
            
        else:
            
            event.Skip()
    
    def OnSizeChanged(self, event):
        self.AdjustFilterLinksTitle()
        if not getattr(self, '_redim', False):
            self._redim = True
            self._setDim()
            def DelVar():
                try:
                    del self._redim
                except:
                    pass
            wx.CallAfter(DelVar)
        event.Skip()
    
    def OnValueChanged( self, event ):
        if not self._helpInProgress:
            obj = event.GetEventObject()
            self.HelpChoice(obj)
    
    def GetSql(self):
        return "SELECT %(alias)s.id, %(alias)s.%(codice)s, %(alias)s.%(descriz)s FROM %(table)s %(alias)s"\
               % {'table': self.db_name,
                  'alias': self.db_alias,
                  'codice': self.codice_fieldname,
                  'descriz': self.descriz_fieldname}
    
    def GetValueSearchSqlJoins(self):
        return ''
    
    def SetDataGrid(self, grid, rs):
        grid.SetData(rs, self.GetDataGridColumns())
        self.AdjustColumnsSize(grid)
    
    def AdjustColumnsSize(self, grid):
        pass
    
    def GetDataGridColumns(self):
        _STR = gridlib.GRID_VALUE_STRING
        return (( 1, "Cod.",        _STR, False),
                ( 2, "Descrizione", _STR, False))
    
    def SetData(self, rs):
        self._rs = rs
    
    def GetData(self):
        return self._rs
    
    def HelpChoice(self, obj, showgrid=True, forceAll=False, exact=None, resetFields=True):
        out = False
        if self._helpInProgress:
            return out
        self._helpInProgress = True
        cmd, par = self.GetSqlSearch(obj, forceAll, exact)
        if cmd:
            if showgrid:
                w = True
            else:
                cmd += " LIMIT 2"
                w = False
            self.SetData(None)
            db = adb.db.__database__
            if w:
                wx.BeginBusyCursor()
            try:
                if db.Retrieve(cmd, par):
                    rs = db.rs
                    if len(rs) == 0:
                        self.currentid = None
                        if obj == self._ctrcod:
                            obj2 = self._ctrdes
                        else:
                            obj2 = self._ctrcod
                        obj2.SetValue('')
                    elif not forceAll and (len(rs) == 1 or (self.codexclusive and obj == self._ctrcod and rs[0][1] == obj.GetValue())):
                        self.SetValue(rs[0][0], obj.GetValue())
                        out = True
                    else:
                        if showgrid:
                            if not resetFields:
                                self.reset_fields_on_focus_lose = False
                            out = self.ShowGrid(rs)
                            self.reset_fields_on_focus_lose = True
                else:
                    self.SetErrorValues(db.dbError.exception)
                    rs = None
            finally:
                if w:
                    wx.EndBusyCursor()
        self._helpInProgress = False
        if out and not self.fixvaluesearch:
            del self.valuesearch[:]
        return out
    
    def GetSqlSearch(self, obj, forceAll, exact):
        cmd = None
        par = []
        if obj == self._ctrcod:
            fltf = self.codice_fieldname
            fltv = self._ctrcod.GetValue()#.strip()
        elif obj == self._ctrdes:
            fltf = self.descriz_fieldname
            fltv = self._ctrdes.GetValue()#.strip()
        else:
            fltf = None
        if fltf:
            if exact is None:
                exact = (fltf == self.codice_fieldname and self.exactcode)
            cmd = self.GetSql()
            filter = ""
            if self.basefilter:
                #filtro base da SetFilter - ha prevalenza su tutto
                filter = AndApp("(%s)" % self.basefilter, filter)
            if self.filter:
                #filtro base da SetFilter - ha prevalenza su tutto
                filter = AndApp("(%s)" % self.filter, filter)
            for col,val,tit in self.filtervalues:
                #filtri da filterlinks
                if val is not None:
                    filter = AndApp(filter, "%s=%%s" % col)
                    par.append(val)
            if self.valuesearch:
                #filtri da cerca valori
                cmd += self.GetValueSearchSqlJoins()
                for tab, col, val in self.valuesearch:
                    op = '='
                    if type(val) in (str, unicode):
                        val = val.replace(r'%', '')
                        val = val.replace('..', r'%')
                        endby = val.startswith("*")
                        if endby:
                            val = "%%%s" % val[1:]
                        if val.endswith("*"):
                            val = val[:-1]
                        if not endby:
                            val += "%"
                        if '%' in val:
                            op = ' LIKE '
                    filter = AndApp(filter, "%s.%s%s%%s" % (tab, col, op))
                    par.append(val)
            flttxt, partxt = self.GetSqlTextSearch(obj, forceAll, exact)
            if flttxt:
                if filter:
                    filter = AndApp(filter, "(%s)" % flttxt)
                else:
                    filter = flttxt
                par += partxt
            if self.filterdyn:
                fd = self.filterdyn()
                if fd:
                    if filter:
                        filter = "(%s) AND " % filter
                    filter += fd
            if filter:
                cmd += " WHERE %s " % filter
            g = self.GetSqlGroup()
            if g:
                cmd += (' '+g)
            g, p = self.GetSqlHaving()
            if g:
                cmd += (' '+g)
                par += p
            cmd += " ORDER BY %s" % self.GetSqlOrder(fltf)
        return cmd, par
    
    def GetSqlOrder(self, field):
        o = field
        if not '.' in o:
            o = '%s.%s' % (self.db_alias, o)
        return o
    
    def GetSqlGroup(self):
        return ''
    
    def GetSqlHaving(self):
        return '', []
    
    def GetSqlTextSearch(self, obj, forceAll, exact):
        cmd = ''
        par = []
        fltv = obj.GetValue()
        expand = True
        if obj == self._ctrcod:
            fltf = self.codice_fieldname
            expand = getattr(self, '_fromkeydown', False) is True or getattr(self, '_fromtab', False) is True
        elif obj == self._ctrdes:
            fltf = self.descriz_fieldname
        if fltv and not forceAll:
            #filtro da valore digitato in codice o descrizione
            if fltv:
                fltv = fltv.replace('..', r'%')
                #endby = fltv.startswith("*")
                #if endby:
                    #fltv = "%%%s" % fltv[1:]
                #if fltv.endswith("*"):
                    #fltv = fltv[:-1]
                #if not exact and not endby:
                    #fltv += "%"
                if expand and not fltv.endswith('%'):
                    fltv += '%'
                f = "%s LIKE %%s" % fltf
                if not '.' in fltf:
                    f = "%s.%s" % (self.db_alias, f)
                cmd = AndApp(cmd, f) 
                par.append(fltv)
        return cmd, par
    
    def SetMinWidth(self, mw):
        self._minwidth = mw
    
    def ShowGrid(self, rs):
        out = False
        parent = self.GetParent()
        #imposto la posizione del dialog
        pos = self.GetPosition()
#        pos = parent.ClientToScreen(pos)
        codw = self._ctrcod.GetSize()[0]
        _mcw = self.GetGridMaxCodeWidth()
        if _mcw is not None and codw>_mcw:
            codw = _mcw
        desw = self._ctrdes.GetSize()[0]
        _mdw = self.GetGridMaxDescWidth()
        if _mdw is not None and desw>_mdw:
            desw = _mdw
        btnw = self.FindWindowById(ID_BTN_NEW)#.GetSize()[0]
        w = self.GetSize()[0]+4#codw+desw+btnw+2
        if w<self._minwidth:
            w = self._minwidth
        size = (w, GRID_HEIGHT)
        pos = list(pos)
        pos[1] += self._ctrcod.GetSize()[1]
        if hasattr(self, 'GetGridColumnSizes'):
            colsizes = self.GetGridColumnSizes()
        else:
            colsizes = (codw+5, desw)
        if hasattr(self, 'GetGridColumn2Fit'):
            c2f = self.GetGridColumn2Fit()
        else:
            c2f = 1
        dlg = LinkTableDialog(parent, -1, "", pos, size=size, linktab=self, 
                              rs=rs, colsizes=colsizes, column2fit=c2f,
                              valsrc=self._btncrd.IsShown(),
                              fixsrc=self.fixvaluesearch,
                              resetvs=len(self.valuesearch)>0, owner=self,
                              shownew=btnw.IsShown() and btnw.IsEnabled())
        val = dlg.ShowModal()
        if val >= 0:
            self.SetValue(val)
            out = True
        elif val == -2:
            #inserimento nuovo elemento
            self.CallCard(new=True)
        elif val == -3:
            #richiama scheda elemento per selezioni cerca valori
            self.CallValueSearch()
            self.ShowFilterLinksTitle()
        elif val == -4:
            #azzera selezioni cerca valori
            del self.valuesearch[:]
            self.fixvaluesearch = False
            self.ShowFilterLinksTitle()
        dlg.Destroy()
        return out
    
    def SetErrorValues(self, err):
        self._ctrcod.SetValue("!!!")
        if len(err.args) == 1:
            self._ctrdes.SetValue("%s" % err.args[0] )
        elif len(err.args) == 2:
            self._ctrdes.SetValue("%s: %s" % (err.args[0], err.args[1]) )

    def SetDynCard(self, func):
        self.dyncard = func
        s = self.canins
        s = s and (self.cardclass is not None or self.dyncard is not None)
        self.FindWindowById(ID_BTN_NEW).Show(s)
        self._setDim()
        self.SetTips()

    def OnCard( self, evt ):
        self.CallCard()
        evt.Skip()
    
    def CallValueSearch(self):
        out = False
        if not self.IsEnabled():
            return out
        dlg = None
        try:
            args = (self,)
            kwargs = {'valuesearch': True}
            wx.BeginBusyCursor()
            if self.dyncard:
                dlg = self.dyncard()
                if dlg:
                    dlg = dlg(*args, **kwargs)
            elif self.cardclass:
                dlg = self.cardclass(*args, **kwargs)
        finally:
            wx.EndBusyCursor()
        if dlg:
            dlg.CenterOnScreen()
            bric = dlg.FindWindowByName('fixvaluesearch')
            if bric:
                bric.SetValue(self.fixvaluesearch)
            focus = True
            for n, (tab, col, val) in enumerate(self.valuesearch):
                ctr = dlg.FindWindowByName(col)
                if ctr:
                    if isinstance(ctr, wx.RadioBox):
                        ctr.Hide()
                    elif hasattr(ctr, 'SetValue'):
                        ctr.SetValue(val)
                    if focus:
                        ctr.SetFocus()
                        focus = False
            wx.CallAfter(self.HideFilterLinksTitle)
            ret = dlg.ShowModal()
            if ret == wx.ID_OK:
                #impostate selezioni x cerca valori
                if bric:
                    self.fixvaluesearch = bric.GetValue()
                self.valuesearch = dlg.GetValueSearchValues()
                out = True
            elif ret == wx.ID_RESET:
                #azzerate selezioni x cerca valori
                del self.valuesearch[:]
                self.fixvaluesearch = False
                self.ShowFilterLinksTitle()
            dlg.Destroy()
        return out
    
    def CallCard(self, new=False):
        canins = self.canins and self.IsEnabled() and self.IsEditable()
        if self.iderror:
            return
        if (new or self.currentid is None) and not canins:
            return
        args = (self,)#(None, -1, "Scheda")
        elid = exid = self.currentid
        if new:
            elid = None
        kwargs = {'onecodeonly': elid}
        dlg = None
        try:
            wx.BeginBusyCursor()
            if self.dyncard:
                dlg = self.dyncard()
                if dlg:
                    dlg = dlg(*args, **kwargs)
            elif self.cardclass:
                dlg = self.cardclass(*args, **kwargs)
        finally:
            wx.EndBusyCursor()
        if dlg:
            if (new and exid is None) or elid is not None:
                for name, val in (('codice',  self._ctrcod.GetValue()),\
                                  ('descriz', self._ctrdes.GetValue())):
                    ctr = dlg.FindWindowByName(name)
                    if ctr:
                        ctr.SetValue(val)
            dlg.OneCardOnly(elid)
            if not self.canedit or not self.IsEnabled() or not self.IsEditable():
#                for child in dlg.GetChildren():
#                    child.Enable(False)
                awu.EnableControls(dlg, False)
            dlg.CenterOnScreen()
            self.HideFilterLinksTitle()
            self.DialogCardCreated(dlg)
            recid = dlg.ShowModal()
            dlg.Destroy()
            self.RemoveChild(dlg)
            if recid>=0:
                if self.PreSetVal:
                    self.PreSetVal(recid)
                self.SetValue(recid)
            self.SetFocus()
    
    def DialogCardCreated(self, dlg):
        pass
    
    def SetPreSetVal(self, psv):
        self.PreSetVal = psv

    def SetDataLink( self, tabname, 
                     colname = None, 
                     cardclass = None, 
                     filter = None,
                     filterlinks = None,
                     canedit=True,
                     canins=True,
                     cansee=True):
        """
        Imposta i parametri per l'aggancio della colonna C{colname} alla 
        tabella C{tabname}.
        
        @param colname: nome colonna da agganciare
        @type colname: C{string}
        @param tabname: nome tabella da agganciare
        @type tabname: C{string}
        @param cardclass: classe per l'inserimento di nuovo record
        @type cardclass: class object
        @param filter: espressione di filtro
        @type filter: str
        @param filterlink: LinkTables aggiuntivi per filtro
        @type filterlink: tuple
        @return: C{None}
        """
        if colname is not None:
            self.SetName(colname)
        else:
            self.SetName("")
        
        self.db_name = tabname
        if not self.db_alias:
            self.db_alias = tabname
        self.cardclass = cardclass
        self.canedit = canedit
        self.canins = canins
        self.cansee = cansee
        s = self.canins 
        s = s and (self.cardclass is not None or self.dyncard is not None)
#        self.FindWindowById(ID_BTN_NEW).Show(s)
        self._btncrd.Show(s)
        self._setDim()
        self.filter = filter
        self.SetFilterLinks(filterlinks)
        self.SetTips()

    def SetFilterLinks(self, filterlinks):
        """
        LinkTables aggiuntivi per filtro.
        In C{filterlinks} ogni elemento è una tupla costituita da::
            - descrizione filtro per label
            - nome tabella da agganciare (la primary key deve essere 'id')
            - nome colonna sul LinkTable principale con cui relazionare
            - nome classe per scheda record su tab. relazionata
            - filtro su tabella relazionata
            - valore iniziale (id) su tabella relazionata
        @param filterlinks: elenco parametri per linktables
        @type filterlinks: n.filtri-tuple di 6-tuple
        """
        try:
            if type(filterlinks) in (list, tuple):
                if not type(filterlinks[0]) in (list, tuple):
                    filterlinks = [filterlinks]
        except:
            pass
        else:
            if filterlinks:
                filterlinks = [list(fl) for fl in filterlinks]
                self.filterlinks = filterlinks
                for n, (fl_des, fl_tab, fl_col, fl_cls, fl_flt, fl_ins)\
                  in enumerate(filterlinks):
                    self.filtervalues.append([fl_col, fl_ins, None])
                    self.SetFilterValueTitle()
                self.ActivateFilterButton()
    
    def SetFilterValueTitle(self, num=0):
        fl_des, fl_tab, fl_col, fl_cls, fl_flt, fl_ins = self.filterlinks[num]
        fl_val = self.filtervalues[num][1]
        if fl_val:
            import awc.tables.util as awtu
            fl_tit = awtu.GetRecordInfo(self.db_curs, fl_tab, fl_val, (self.codice_fieldname,
                                                                       self.descriz_fieldname))
        else:
            fl_tit = None
        self.filtervalues[num][2] = fl_tit
    
    def ShowFilters(self):
        
        if not self.IsEnabled() or not self.IsEditable():
            return
        
        dlg = FiltersPopup(self)#self.GetParent())
        #dlg.Show(False)
        parent = dlg
        
        fg, bg = COLORS_GRID
        dlg.SetForegroundColour(fg)
        dlg.SetBackgroundColour(bg)
        
        ydes = self._fltlink_ydes
        ydelta = self._fltlink_ydelta
        ypos = 0#ydelta
        
        def OnFilterApply(event):
            dlg.EndModal(wx.ID_OK)
        
        ctrls = []
        cbs = 12
        lt0 = None
        for n, (fl_des, fl_tab, f1_col, fl_cls, fl_flt, fl_ins)\
          in enumerate(self.filterlinks):
            w, h = self.GetClientSize()
            wd = w
            if n == 0:
                wd -= (cbs+1)
            des = wx.StaticText(parent, -1,\
                "Filtra in base a: %s" % fl_des, pos=(0, ypos), size=(wd,cbs))
            des.SetForegroundColour(fg)
            des.SetBackgroundColour(bg)
            ypos += des.GetSize()[1]#ydes
            
            if n == 0:
                btnclose = FlatButton(parent, -1, 'x', 
                                      pos=(wd, 0),
                                      size=(cbs,cbs))
                btnclose.SetForegroundColour("black")
                btnclose.SetBackgroundColour("gray")
                btnclose.SetName('closefilters')
                btnclose.SetToolTipString('Chiude i filtri')
                btnclose.SetForegroundColour(fg)
                btnclose.SetBackgroundColour(bg)
                def OnFilterQuit(event):
                    dlg.EndModal(wx.ID_NO)
                btnclose.Bind(wx.EVT_BUTTON, OnFilterQuit)
            
            ID_LINKTABLE = wx.NewId()
            lt = LinkTable(parent, ID_LINKTABLE, pos=(0, ypos))
            if n == 0:
                lt0 = lt
            lt.SetSize(self.GetSize())
            lt.SetName('Filter_LinkTable')
            ypos += lt.GetSize()[1]
            lt.SetDataLink(fl_tab, cardclass = fl_cls, filter = fl_flt)
            lt.NotifyChanges(False)
            val = self.filtervalues[n][1]
            if val is None:
                if type(fl_ins) in (int, long):
                    #valore iniziale passato come id
                    val = fl_ins
            if val is not None:
                lt.SetValue(val)
            elif type(fl_ins) in (str, unicode):
                #valore iniziale passato come codice
                lt._ctrcod.SetValue(fl_ins)
            ctrls.append(lt)
            for c in lt._ctrcod, lt._ctrdes, lt._btncrd:
                c.Bind(wx.EVT_CHAR, dlg.OnChar)
            wx.CallAfter(lambda: lt.NotifyChanges(True))
#            dlg.Bind(EVT_LINKTABCHANGED, OnFilterApply)
        
        if len(self.filterlinks) >= 1:
            wb = 80
            b = wx.Button(parent, -1, "Applica", size=(wb,-1), 
                          pos=(self.GetSize()[0]-wb-2, ypos))
            b.Bind(wx.EVT_BUTTON, OnFilterApply)
            b.SetDefault()
            ypos += lt.GetSize()[1]+2
        
        p = (0, self.GetSize()[1])
        p = self.ClientToScreen(p)
        dlg.SetPosition((p[0]-2,p[1]))
        dlg.SetSize((w+4,ypos+6))
        wx.CallAfter(lambda: lt0.SetFocus())
        
        if self.filterlinkstitle:
            wx.CallAfter(self.HideFilterLinksTitle)
        
        if dlg.ShowModal() == wx.ID_OK:
            changed = False
            for n, (fl_des, fl_tab, f1_col, fl_cls, fl_flt, fl_ins)\
              in enumerate(self.filterlinks):
                ctrl = ctrls[n]
                if self.filtervalues[n][1] != ctrl.GetValue():
                    changed = True
                self.filtervalues[n][1] = ctrl.GetValue()
                if self.filtervalues[n][1] is None:
                    self.filtervalues[n][2] = None
                else:
                    self.filtervalues[n][2] = (ctrl.GetValueCod(),
                                               ctrl.GetValueDes())
            del self.valuesearch[:]
            if changed:
                self.SetValue(None)
        
        dlg.Destroy()
        self.SetFocus()
    
    def SetFilterValue(self, val, num=0):
        self.filtervalues[num][1] = val
        self.SetFilterValueTitle()
    
    def SetFilterFilter(self, filt, num=0):
        self.filterlinks[num][4] = filt
    
    def GetFilterValue(self, num=0):
        return self.filtervalues[num][1]
    
    def ActivateFilterButton(self):
        b = self._btnflt
        if b.IsShown():
            return
        d = self._ctrdes
        s = list(d.GetSize())
        s[0] -= b.GetSize()[0]
        d.SetSize(s)
        b.Show()
    
    def GetFilterObjects(self):
        fv = []
        cl = self.GetChildren()
        if len(cl)>1:
            fp = cl[1]
            for x in fp.GetChildren():
                if isinstance(x, LinkTable):
                    fv.append(x)
        return fv
    
    def SetObligatory( self, obblig = True ):
        """
        Imposta l'obbligatorietà del controllo; settando a C{True}, la 
        validazione sarà soddisfatta solo se è presente un id significativo.
        
        @param obblig: Obbligatorietà del controllo
        @type obblig: bool
        """
        self.obligatory = obblig

    def Validate( self ):
        out = True
        if self.GetValue() is None and self.IsEnabled():
            out = not self.obligatory
        return out
    
    def SetFilter(self, filter, resetOnError=False, onError=None):
        newfilter = False
        if filter != self.filter:
            actualid = self.GetValue()
            self.filter = filter
            if self.apply_filter_on_setvalue:
                self.SetValue(actualid)
                if not self.Validate() or (self.iderror and resetOnError):
                    self.ResetValue()
                    if onError is not None:
                        onError(self)
            newfilter = True
        return newfilter
    
    def SetBaseFilter(self, basefilter, resetOnError=False, onError=None):
        newfilter = False
        if basefilter != self.basefilter:
            actualid = self.GetValue()
            self.basefilter = basefilter
            self.SetValue(actualid)
            if not self.Validate() or (self.iderror and resetOnError):
                self.ResetValue()
                if onError is not None:
                    onError(self)
            newfilter = True
        return newfilter
    
    def SetFilterDyn(self, filterdyn):
        newfilter = False
        if filterdyn != self.filterdyn:
            actualid = self.GetValue()
            self.filterdyn = filterdyn
            self.SetValue(actualid)
            if not self.Validate():
                self.ResetValue()
            newfilter = True
        return newfilter
    
    def ResetValue( self ):
        old = self.GetValue()
        if old != None:
            self.SetValue(None)
        return old
    
    def SetValue(self, id, txt=None, stopevents=True):
        """
        Seleziona il record sulla tabella collegata in base all'C{ID} passato
        
        @param id: ID da cercare
        @type id: int
        """
        self.HideFilterLinksTitle()
        self.currentid = id
        if id is not None and type(id) not in (int, long, float):
            raise Exception,\
                  "Tipo di informazione non corretto (%s)" % type(id)
        if id is not None:
            id = int(id)
        oldhip = self._helpInProgress
        self._helpInProgress = True
        b = self.FindWindowById(ID_BTN_NEW)
        if id is None:
            self._ctrcod.SetValue("")
            self._ctrdes.SetValue("")
            if self.obligatory:
                color = COLOR_ERROR
            else:
                color = COLOR_NORMAL
            self.iderror = False
            data = None
            bmp = images.getCardEmpty16Bitmap()#bmpempty
            tip = "Inserisce un nuovo elemento (Ctrl-Ins)"
            enab = self.canins
            self._rs = None
        else:
            cmd = self.GetSql()
            par = []
            cmd += r' WHERE %s.id=%%s' % self.db_alias
            par.append(id)
            if self.filter and self.apply_filter_on_setvalue:
                cmd += " AND (%s)" % self.filter
            if self.filterdyn:
                fd = self.filterdyn()
                if fd:
                    cmd += " AND %s" % fd
            g = self.GetSqlGroup()
            if g:
                cmd += (' '+g)
            g, p = self.GetSqlHaving()
            if g:
                cmd += (' '+g)
                par += p
            rs = None
            try:
                self.db_curs.execute(cmd, par)
                rs = self.db_curs.fetchone()
            except MySQLdb.Error, e:
                self.SetErrorValues(e)
                self.iderror = True
                bmp = images.getCardError16Bitmap()#bmperr
                tip = "Valore errato (%s)" % id
                #self.SetValue(None)
                color = COLOR_ERROR
                enab = False
            else:
                if not rs:
                    self.iderror = True
                    bmp = images.getCardError16Bitmap()#bmperr
                    tip = "Valore errato (%s)" % id
                    #self.SetValue(None)
                    color = COLOR_ERROR
                    enab = True
                    self.currentid = None
                    valcd = (None, None)
                else:
                    self.iderror = False
                    color = COLOR_NORMAL
                    bmp = images.getCardFull16Bitmap()#bmpfull
                    tip = "Visualizza la scheda anagrafica (F11)"
                    enab = self.canedit or self.cansee
                    valcd = (rs[1] or "", rs[2] or "")
                self._stopevents = stopevents
                self._ctrcod.SetValue(valcd[0])
                self._ctrdes.SetValue(valcd[1])
                def ResumeEvents():
                    self._stopevents = False
                wx.CallAfter(ResumeEvents)
            self.SetData(rs)
        b.SetBitmapLabel(bmp)
        b.Refresh()
        b.SetToolTipString(tip)
        b.Enable(enab)
        
        self._helpInProgress = oldhip
        
        if id is None:
            self.ShowFilterLinksTitle()
        
        if self.notifyChanges:
            self._PostEventChanged(id)

    def SetValueCod(self, val):
        return self._ctrcod.SetValue(val)
    
    def SetValueDes(self, val):
        return self._ctrdes.SetValue(val)
    
    def SetBackgroundColour(self, *args, **kwargs):
        for ctr in self._ctrcod, self._ctrdes:
            ctr.SetBackgroundColour(*args, **kwargs)
            ctr.Refresh()
    
    def GetValue( self ):
        return self.currentid
    
    def GetValueCod( self ):
        return self._ctrcod.GetValue()
    
    def GetValueDes( self ):
        return self._ctrdes.GetValue()
    
    def _PostEventChanged( self, data ):
        evt = LinkTableChangedEvent(evt_LINKTABCHANGED, self.GetId())
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        evt.SetSelection(data)
        #self.GetEventHandler().ProcessEvent(evt)
        self.GetEventHandler().AddPendingEvent(evt)
    
    def _PostEventForced( self, data ):
        evt = LinkTableChangedEvent(EVT_LINKTABFORCED, self.GetId())
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        evt.SetSelection(data)
        #self.GetEventHandler().ProcessEvent(evt)
        self.GetEventHandler().AddPendingEvent(evt)
    
    def _PostEventFocusLost(self):
        evt = LinkTableFocusLostEvent(evt_LINKTABFOCUSLOST, self.GetId())
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        #self.GetEventHandler().ProcessEvent(evt)
        self.GetEventHandler().AddPendingEvent(evt)
    
    def GetGridClass(self):
        import awc.controls.dbgrid as dbglib
        return dbglib.DbGridColoriAlternati
    

# ------------------------------------------------------------------------------


class LinkTableDialog(wx.Dialog):
    
    def __init__(self, parent, id, title="", pos = wx.DefaultPosition, 
                 size=wx.DefaultSize, style=wx.THICK_FRAME, linktab=None,
                 rs=None, colsizes=(-1, -1), valsrc=False, fixsrc=False, 
                 resetvs=False, owner=None, column2fit=1, shownew=False):
        
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        
        pos = list(pos)
        pos[0] -= 4
        apos = parent.ClientToScreen(wx.Point(pos[0], pos[1]))
        brc = (apos[0]+self.GetSize()[0], apos[1]+self.GetSize()[1])
        sx, sy = wx.GetDisplaySize()
        if brc[0] > sx:
            apos[0] = sx-self.GetSize()[0]
        if brc[1] > sy:
            apos[1] -= linktab.GetSize()[1]
            apos[1] -= size[1]
#        pos = parent.ScreenToClient(apos)
        self.SetPosition(apos)
        colsizes = map(lambda n: n-2, colsizes)
        self.owner = owner
        p = wx.Panel(self, -1)
        self.rs = rs
        sz = wx.FlexGridSizer(0, 1, 0,0)
        sz.AddGrowableCol(0)
        sz.AddGrowableRow(0)
#        self.grid = dbglib.DbGridColoriAlternati(p, -1, (0,0), size)
        self.grid = linktab.GetGridClass()(p, -1, (0,0), size)
        self.grid.SetSearchColors()
        c3 = COLORS_LABEL
        self.grid.SetLabelTextColour(c3[0])
        self.grid.SetLabelBackgroundColour(c3[1])
        self.grid.SetRatioFactor(2)
        #self.grid.SetColSize(0, colsizes[0]+5)
        #self.grid.SetColSize(1, colsizes[1])
        for col, colsize in enumerate(colsizes):
            #self.grid.SetColSize(col, colsize)
            self.grid.SetColumnDefaultSize(col, colsize)
        linktab.SetDataGrid(self.grid, rs)
        self.grid.SetFitColumn(column2fit)
#        self.grid.AutoSizeColumns()
        sz.Add(self.grid, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL)
        szb = wx.FlexGridSizer(1, 0, 0,0)
        szbl = wx.FlexGridSizer(1, 0, 0,0)
        bw = 80
        bh = -1
        txt = wx.StaticText(p, -1, "Cerca valori:", wx.DefaultPosition, wx.DefaultSize, 0)
        szbl.Add(txt, 0, wx.ALIGN_CENTER|wx.RIGHT, 5)
        bsrc = wx.Button(p, -1, "&Imposta", wx.DefaultPosition, (bw, bh), 0)
        szbl.Add(bsrc, 0, wx.ALIGN_CENTER|wx.RIGHT, 5)
        bazz = wx.Button(p, -1, "&Elimina", wx.DefaultPosition, (bw, bh), 0)
        szbl.Add(bazz, 0, wx.ALIGN_CENTER|wx.RIGHT, 5)
        for c in (txt, bsrc):
            c.Show(valsrc)
        bazz.Show(valsrc and resetvs)
        szb.Add(szbl, 0, wx.ALIGN_LEFT)
        szbr = wx.FlexGridSizer(1, 0, 0,0)
        if shownew:
            bnew = wx.Button(p, -1, "&Nuovo", size = (bw, bh))
            szbr.Add(bnew)
            self.Bind(wx.EVT_BUTTON, self.OnNew, bnew)
        bclose = wx.Button(p, -1, "Chiudi", size = (bw, bh))
        szbr.Add(bclose)
        bselec = wx.Button(p, -1, "Seleziona", size = (bw, bh))
        bselec.SetDefault()
        szbr.Add(bselec)
        szb.Add(szbr, 0, wx.ALIGN_RIGHT)
        szb.AddGrowableCol(1)
        sz.Add(szb, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.TOP, 5)
        p.SetSizer(sz)
        sz.SetSizeHints(self)
        self.Fit()
        #p.SetDefaultItem(bselec)
        #aw.awu.GetParentFrame(p).SetDefaultItem(bselec)
        bselec.SetDefault()
        wx.CallAfter(lambda *x: self.grid.SetFocus())
        self.Show()
        
        self.grid.Bind( gridlib.EVT_GRID_CELL_LEFT_DCLICK,\
                        self.OnCellSelected )
        for b, func in ((bclose, self.OnQuit),
                        (bselec, self.OnSel),
                        (bazz, self.OnValSrcReset),
                        (bsrc, self.OnValSrc)):
            self.Bind(wx.EVT_BUTTON, func, b)
        self.grid.Bind( EVT_LTABHELPSELECTED, self.OnHelpSelected )
        self.grid.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)
        self.Bind(wx.EVT_CHAR, self.OnChar)
    
    def OnNew(self, event):
        self.EndModal(-2)
    
    def OnValSrc(self, event):
        self.EndModal(-3)
    
    def OnValSrcReset(self, event):
        self.EndModal(-4)
    
    def OnKeyDown(self, evt):
        ret = None
        kc = evt.GetKeyCode()
        if kc == wx.WXK_RETURN or kc == 370: #370=enter del tastierino num.
            row = self.grid.GetGridCursorRow()
            ret = self.rs[row][0]
        elif kc == wx.WXK_ESCAPE:
            ret = -1
        if ret is None:
            evt.Skip()
        else:
            self.EndModal(ret)
    
    def OnChar(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(-1)
        event.Skip()
    
    #def EndModal(self, val):
        #self.grid.Destroy()
        #wx.Dialog.EndModal(self, val)

    def OnQuit(self, event):
        self.EndModal(-1)

    def OnSel(self, event):
        row = self.grid.GetGridCursorRow()
        self.EndModal(self.rs[row][0])
    
    def OnHelpSelected(self, event):
        self.EndModal( event.GetSelection() )

    def OnCellSelected( self, event ):
        row = event.GetRow()
        self.EndModal(self.rs[row][0])


# ------------------------------------------------------------------------------


class FiltersPopup(wx.Dialog):
    
    def __init__(self, parent, id=-1, title='', pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.RAISED_BORDER):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        
    def OnChar(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.EndModal(wx.ID_NO)
        event.Skip()
    
    def EndModal(self, r):
        wx.Dialog.EndModal(self, r)
