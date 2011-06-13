#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/datectrl.py
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
import wx.lib.masked as masked
import wx.calendar
from mx import DateTime

from awc.controls import evt_DATECHANGED, EVT_DATECHANGED
from awc.controls import evt_DATEFOCUSLOST, EVT_DATEFOCUSLOST

import awc.controls.windows as aw
import awc.controls.mixin as cmix
import awc.util as awu


YEAR_DEFAULT = DateTime.today().year
def SetYearDefault(yd):
    global YEAR_DEFAULT
    YEAR_DEFAULT = yd


class DateChangedEvent(wx.PyCommandEvent):
    def __init__(self, *args, **kwargs):
        wx.PyCommandEvent.__init__(self, *args, **kwargs)
        self._date = None
    def SetValue(self, date):
        self._date = date
    def GetValue(self):
        return self._date

class DateFocusLostEvent(wx.PyCommandEvent):
    def __init__(self, evtType, id):
        wx.PyCommandEvent.__init__(self, evtType, id)
        self._selection = None

    def SetSelection(self, val):
        self._selection = val

    def GetSelection(self):
        return self._selection

# ------------------------------------------------------------------------------


class DateCtrl(wx.Control, cmix.TextCtrlMixin):
    """
    Controllo per la digitazione delle date.
    Si basa su C{wx.lib.masked.Ctrl} compostato con C{autoformat} =
    C{EUDATEDDMMYYYY.}
    """
    _time = False
    def __init__(self, parent, id, caption = "", pos = wx.DefaultPosition, 
                 size = wx.DefaultSize, style = 0):
        
        wx.Control.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)
        cmix.TextCtrlMixin.__init__(self)
        
        self.colors['normalBackground'] = wx.TheColourDatabase.Find('white')
        
        self.maskedCtrl = None
        self._cal = None
        
        if self._time:
            fmt = "EUDATE24HRTIMEDDMMYYYY.HHMM"
        else:
            fmt = "EUDATEDDMMYYYY."
        
        p = wx.Panel(self, -1)
        self.maskedCtrl = masked.Ctrl(p, -1, autoformat=fmt,
                                      emptyBackgroundColour=self.colors['normalBackground'],
                                      validBackgroundColour=self.colors['normalBackground'],
                                      invalidBackgroundColour=self.colors['invalidBackground'],
                                      foregroundColour=self.colors['normalForeground'],
                                      signedForegroundColour=self.colors['normalForeground'])
        self.maskedCtrl._fixSelection = lambda *x: None
        if wx.Platform == '__WXGTK__':
            maskedCtrl = self.maskedCtrl
            def _OnKeyDown(event):
                if event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                else:
                    masked.TextCtrl._OnKeyDown(self, event)
            maskedCtrl._OnKeyDown = _OnKeyDown
            def _OnChar(event):
                if event.GetKeyCode() == wx.WXK_RETURN:
                    event.Skip()
                else:
                    start, stop = maskedCtrl.GetSelection()
                    if start == 0 and stop == len(maskedCtrl.GetValue()) and 48 <= event.GetKeyCode() <= 57:
                        maskedCtrl.SetValue('')
                        maskedCtrl.SetSelection(0,0)
                        maskedCtrl.SetInsertionPoint(0)
                    masked.TextCtrl._OnChar(self, event)
            maskedCtrl._OnChar = _OnChar
            def _OnReturn(event):
                event.Skip()
                return True
            maskedCtrl._OnReturn = maskedCtrl._keyhandlers[13] = _OnReturn
            
#        if wx.Platform == '__WXGTK__':
#            if wx.WXK_RETURN in self.maskedCtrl._nav:
#                _nav = self.maskedCtrl._nav
#                _nav.pop(_nav.index(wx.WXK_RETURN))
        
        if wx.WXK_RETURN in self.maskedCtrl._nav:
            _nav = self.maskedCtrl._nav
            _nav.pop(_nav.index(wx.WXK_RETURN))
        
        self.SetFont(self.maskedCtrl.GetFont())
        dw, dh = self.maskedCtrl.GetSize()
        sz = wx.FlexGridSizer( 0, 2, 0, 0 )
        sz.Add( self.maskedCtrl, 0, wx.ALIGN_LEFT )
        self.buttonCalendar = wx.Button(p, -1, "...", size=(dh,dh))
        sz.Add( self.buttonCalendar, 0, wx.ALIGN_CENTER )
        p.SetSizer(sz)
        #self.SetSizer(sz)
        sz.SetSizeHints(self)
        p.Fit()
        self.Bind(wx.EVT_BUTTON, self.OnCalendarCall, self.buttonCalendar)
        self.Bind(wx.EVT_TEXT, self.OnDateChanged, self.maskedCtrl)
        
        #quando DateCtrl riceve il focus, lo passa al TextCtrl interno
        self.Bind(wx.EVT_SET_FOCUS, self.OnFocusGain)
        self.maskedCtrl.Bind(wx.EVT_KEY_DOWN, self.OnChar)
        self.maskedCtrl.Bind(wx.EVT_CHAR, self.OnCharX)
        if wx.Platform == '__WXGTK__':
            self.maskedCtrl.Bind(wx.EVT_PAINT, self.OnPaint)
        for obj in (self.maskedCtrl, self.buttonCalendar):
            obj.Bind(wx.EVT_SET_FOCUS, self.OnFocusGain)
            obj.Bind(wx.EVT_KILL_FOCUS, self.OnFocusLost)
    
    def _PostEventFocusLost(self):
        evt = DateFocusLostEvent(evt_DATEFOCUSLOST, self.GetId())
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        #self.GetEventHandler().ProcessEvent(evt)
        self.GetEventHandler().AddPendingEvent(evt)
    
    def HasFocus(self):
        return self.FindFocus() in awu.GetAllChildrens(self)
    
    def OnCharX(self, event):
        if event.GetKeyCode() == wx.WXK_RETURN:
            self.CheckDate()
        event.Skip()
    
    def OnChar(self, event):
        skip = False
        if event.GetKeyCode() == wx.WXK_TAB:
            d = wx.NavigationKeyEvent.IsForward
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                self.buttonCalendar.SetFocus()
        elif event.GetKeyCode() == wx.WXK_F1:
            cmix.TextCtrlMixin.OnKeyDown_TestHelp(self, event)
        else:
            if wx.Platform == '__WXGTK__':
                m = self.maskedCtrl
                start, stop = m.GetSelection()
                if start == 0 and stop == len(m.GetValue()) and 48 <= event.GetKeyCode() <= 57:
                    self.SetValue(None)
                    m.SetSelection(0, 0)
            skip = True
        if skip:
            event.Skip()
    
    def OnPaint(self, event):
        if self.IsEnabled():
            wx.Control.OnPaint(self, event)
        else:
            self.PaintDisabled(self.maskedCtrl.GetValue(), self.maskedCtrl)
        event.Skip()

    def OnFocusGain(self, event):
        if self.FindFocus() is self.maskedCtrl:
            self.AdjustBackgroundColor(self.IsEditable(), self.maskedCtrl, 
                                       self.AdaptMaskedColors)
            self.SetFocus()
        elif self.FindFocus() is not self.buttonCalendar:
            self.maskedCtrl.SetFocus()
        aw.SetFocusedControl(self)
        event.Skip()
    
    def OnFocusLost(self, event):
        if not aw.awu.GetParentFrame(self).IsShown():
            #su gtk la chiusura del frame con focus su DateCtrl crasha l'app
            return
        self.CheckDate()
#        if self.FindFocus() is self.maskedCtrl:
#            self.AdjustBackgroundColor()
        self.AdjustBackgroundColor()
        if not self.FindFocus() in (self.maskedCtrl, self.buttonCalendar):
            self._PostEventFocusLost()
        event.Skip()
    
    def CheckDate(self):
        masked = self.maskedCtrl.GetValue()
#        if ' ' in masked[:10] or len(masked) == 16 and ' ' in masked[-5:]:
#            self.SetValue(None)
#            return
        try:
            year = int(masked[6:10].strip() or 0)
        except:
            year = 0
        if year == 0:
            _year = YEAR_DEFAULT
        elif year<1000:
            _year = year+2000
        else:
            _year = None
        if _year is not None:
            self.CheckDate_AdaptYear(_year)
        masked = self.maskedCtrl.GetValue()
        if ' ' in masked[:10] or len(masked) == 16 and ' ' in masked[-5:]:
            self.SetValue(None)
    
    def CheckDate_AdaptYear(self, year):
        masked = self.maskedCtrl.GetValue() #dd.mm.yyyy hh:mm
        if len(masked) == 16 and masked[-5:] == '  :  ':
            now = DateTime.now()
            masked = '%s%s:%s' % (masked[:-5], now.hour, now.minute)
        self.maskedCtrl.SetValue('%s%s%s' % (masked[:5], str(year).zfill(4), masked[10:]))
    
    def AdaptMaskedColors(self, bg):
        m = self.maskedCtrl
        m._emptyBackgroundColour = bg
        m._validBackgroundColour = bg
        m._applyFormatting()
    
    def SetFocus(self):
        self.maskedCtrl.SetFocus()
        def Seleziona():
            self.maskedCtrl.SetSelection(0, len(self.maskedCtrl._curValue))
        wx.CallAfter(Seleziona)
    
    def Disable(self):
        self.maskedCtrl.Enable(False)
    
    def Enable(self, e=True, set_editable=True):
        if set_editable:
            self.maskedCtrl.SetEditable(e)
        self.buttonCalendar.Enable(e)
        self.AdjustBackgroundColor()
    
    def AdjustBackgroundColor(self, focused=False, obj=None, func=None, error=False):
        cmix.TextCtrlMixin.AdjustBackgroundColor(self, focused, 
                                                 self.maskedCtrl, func, error,
                                                 refresh_func=self.maskedCtrl._Refresh)
    
    def IsEnabled(self):
        return self.maskedCtrl.IsEditable()
    
    def IsEditable(self):
        return self.maskedCtrl.IsEditable()
    
    def OnDateChanged(self, event):
        if self.notifyChanges:
            evt = DateChangedEvent(evt_DATECHANGED, self.GetId())
            evt.SetEventObject(self)
            evt.SetId(self.GetId())
            evt.SetValue(self.GetValue(adapt_date=False))
            self.GetEventHandler().AddPendingEvent(evt)
        event.Skip()

    def SetDimensions(self, x, y, w, h, f):
        wx.Control.SetDimensions(self, x, y, w+20, h, f)
        #aggiunti 20 pix in x per fare spazio al bottone calendario

    def OnCalendarCall( self, event ):
        if self._cal is None:
            pos = self.GetParent().ClientToScreen( self.GetPosition() )
            pos[1] += 20
            dlg = CalDialog(self, -1, "", pos)
            dlg.SetDate( self.GetValue() )
            if dlg.ShowModal() == 1:
                d = dlg.date
                self.SetValue( DateTime.Date( d.GetYear(),
                                              d.GetMonth()+1,
                                              d.GetDay() ) )
            dlg.Destroy()
        event.Skip()

    def SetValue( self, d ):
        if d is None:
            self.maskedCtrl.SetValue("")
        else:
            dd = ("00%d" % d.day)[-2:]
            mm = ("00%d" % d.month)[-2:]
            yyyy = ("0000%d" % d.year)[-4:]
            self.maskedCtrl.SetValue("%s.%s.%s" % (dd,mm,yyyy) )

    def GetValue(self, adapt_date=True, adapt_year=True):
        out = None
        try:
            masked = self.maskedCtrl
            cdate = masked.GetValue()
            dd = int(cdate[0:2])
            mm = int(cdate[3:5])
            yyyy = int((cdate[6:10]).strip() or 0)
            if not yyyy and adapt_year:
                yyyy = YEAR_DEFAULT
            out = DateTime.Date( yyyy, mm, dd )
            if adapt_date:
                if int(cdate[0:2].strip() or 0) != out.day\
                or int(cdate[3:5].strip() or 0) != out.month\
                or int(cdate[6:10].strip() or 0) != out.year:
                    ndate = str(out.day).zfill(2)+cdate[2]+str(out.month).zfill(2)+cdate[5]+str(out.year).zfill(2)
                    s1, s2 = masked.GetSelection()
                    masked.SetValue(ndate)
                    masked.SetSelection(s1, s2)
        except:
            pass
        return out

    
# ------------------------------------------------------------------------------


class CalDialog(wx.Dialog):
    def __init__(self, parent, id, title = "", pos = wx.DefaultPosition, 
                 size=wx.DefaultSize, style = wx.NO_BORDER):
        wx.Dialog.__init__(self, parent, id, title, pos, size, style)
        sz = wx.FlexGridSizer(0,1,0,0)
        self.cal = wx.calendar.CalendarCtrl(\
            self, -1, wx.DateTime_Now(), pos = (pos[0],pos[1]+20),
            style = wx.calendar.CAL_SHOW_HOLIDAYS
                   |wx.calendar.CAL_SUNDAY_FIRST
                   |wx.calendar.CAL_SEQUENTIAL_MONTH_SELECTION )
        sz.Add(self.cal)
        self.SetSizer(sz)
        sz.SetSizeHints(self)
        self.cal.Bind(wx.calendar.EVT_CALENDAR, self.OnCalSelected,\
                      source=self.cal)
        self.Fit()
        self.Show()

    def OnCalSelected( self, event ):
        d = self.cal.GetDate()
        self.date = d
        event.Skip()
        self.EndModal(1)

    def SetDate( self, d ):
        if d is not None:
            caldate = wx.DateTimeFromDMY( d.day, d.month-1, d.year )
            self.cal.SetDate( caldate )


# ------------------------------------------------------------------------------


class DateTimeCtrl(DateCtrl):
    _time = True
    
    def OnCalendarCall( self, event ):
        if self._cal is None:
            pos = self.GetParent().ClientToScreen( self.GetPosition() )
            pos[1] += 20
            dlg = CalDialog(self, -1, "", pos)
            dlg.SetDate( self.GetValue() )
            if dlg.ShowModal() == 1:
                d = dlg.date
                now = DateTime.now()
                self.SetValue(DateTime.DateTime(d.GetYear(),
                                                d.GetMonth()+1,
                                                d.GetDay(),
                                                now.hour,
                                                now.minute))
            dlg.Destroy()
        event.Skip()

    def SetValue( self, d ):
        if d is None:
            self.maskedCtrl.SetValue("")
        else:
            dd = ("00%d" % d.day)[-2:]
            mm = ("00%d" % d.month)[-2:]
            yyyy = ("0000%d" % d.year)[-4:]
            if hasattr(d, 'hour'):
                hh = d.hour
                mn = d.minute
            else:
                now = DateTime.now()
                hh = mn = 0
            def f(x):
                return str(x).zfill(2)
            self.maskedCtrl.SetValue("%s.%s.%s %s:%s" % (dd,mm,yyyy,f(hh),f(mn)))
    
    def GetValue(self, adapt_date=True, adapt_year=True):
        out = None
        try:
            masked = self.maskedCtrl
            cdate = masked.GetValue()
            dd = int(cdate[0:2])
            mm = int(cdate[3:5])
            yyyy = int((cdate[6:10]).strip() or 0)
            if not yyyy and adapt_year:
                yyyy = YEAR_DEFAULT
            hh = int(cdate[11:13])
            mn = int(cdate[14:16])
            out = DateTime.DateTime(yyyy, mm, dd, hh, mn)
            if adapt_date:
                if int(cdate[0:2].strip() or 0) != out.day\
                or int(cdate[3:5].strip() or 0) != out.month\
                or int(cdate[6:10].strip() or 0) != out.year:
                    ndate = str(out.day).zfill(2)+cdate[2]+str(out.month).zfill(2)+cdate[5]+str(out.year).zfill(2)+cdate[9]+str(out.hour).zfill(2)+cdate[11]+str(out.minute).zfill(2)+cdate[13]
                    s1, s2 = masked.GetSelection()
                    masked.SetValue(ndate)
                    masked.SetSelection(s1, s2)
        except:
            pass
        return out
