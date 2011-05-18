#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         awc/layout/helpsys.py
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

"""
Help System HTML
"""

import os

import wx
import wx.html as html

import awc.controls.windows as aw
import awc.layout.helpsys_wdr as wdr

HELP_ROOT = 'help'
def SetHelpRoot(hr):
    global HELP_ROOT
    HELP_ROOT = hr
def GetHelpRoot():
    return HELP_ROOT


class HelpHtmlPanel(aw.Panel):
    
    home = None
    
    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.home = os.path.join(GetHelpRoot(), '%s - Manuale utente.html' % wx.GetApp().GetAppName())
        wdr.HelpHtmlFunc(self)
        self.html = html.HtmlWindow(self.FindWindowByName('htmlpanel'), -1)
        #self.html.SetRelatedFrame(self.GetParent(), 'test')
        #self.html.SetRelatedStatusBar(0)
        wx.CallAfter(lambda: self.html.SetFocus())
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(html.EVT_HTML_LINK_CLICKED, self.OnLinkClicked)
        for name, func in (('butprev', self.OnGoPrevious),
                           ('butnext', self.OnGoNext),
                           ('buthome', self.OnGoHome),
                           ('butbrow', self.OnOpenBrowser),):
            self.Bind(wx.EVT_BUTTON, func, self.FindWindowByName(name))
        self.AdaptHtmlPanelSize()
    
    def OnLinkClicked(self, event):
        wx.CallAfter(lambda: self.EnableButtons())
        event.Skip()
    
    def OnGoPrevious(self, event):
        h = self.html
        if h.HistoryCanBack():
            h.HistoryBack()
            self.EnableButtons()
    
    def OnGoNext(self, event):
        h = self.html
        if h.HistoryCanForward():
            h.HistoryForward()()
            self.EnableButtons()
    
    def OnGoHome(self, event):
        h = self.html
        if self.home:
            self.LoadPage(self.home)
    
    def OnOpenBrowser(self, event):
        url = self.html.GetOpenedPage()
        if url:
            url = os.path.abspath(url)
            os.startfile(url)
    
    def OnSize(self, event):
        self.AdaptHtmlPanelSize()
        event.Skip()
    
    def AdaptHtmlPanelSize(self):
        self.html.SetSize(self.GetClientSize())
    
    def LoadPage(self, filename):
        self.html.LoadPage(filename)
        self.EnableButtons()
    
    def EnableButtons(self):
        h = self.html
        for name, enable in (('butprev', h.HistoryCanBack()),
                             ('butnext', h.HistoryCanForward()),):
            self.FindWindowByName(name).Enable(enable)


# ------------------------------------------------------------------------------


class HelpHtmlFrame(aw.Frame):
    
    def __init__(self, parent, *args, **kwargs):
        filename = kwargs.pop('filename', None)
        aw.Frame.__init__(self, parent, *args, **kwargs)
        self.panel = HelpHtmlPanel(self)
        self.AddSizedPanel(self.panel, 'browser')
        self.CenterOnScreen()
        if filename is not None:
            self.LoadPage(filename)
    
    def LoadPage(self, *args, **kwargs):
        return self.panel.LoadPage(*args, **kwargs)
