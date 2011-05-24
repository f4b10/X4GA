#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dataentry_gw.py
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
Gateway per Data Entry Documenti Magazzino
Utile per agganciare il dataentry a funzioni esterne: carica la classe del dataentry
una sola volta, nascondendone la finestra invece che distruggerla alla chiusura/abbandono/cancellazione
di un documento.
"""

import wx

import magazz.dataentry_o as deo
import magazz.dataentry as dem

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab


_evtDOCCHANGED = wx.NewEventType()
EVT_DOCCHANGED = wx.PyEventBinder(_evtDOCCHANGED, 1)
class DocChangedEvent(wx.PyCommandEvent):
    
    def __init__(self, message=None):
        wx.PyCommandEvent.__init__(self, _evtDOCCHANGED)
        self._msg = message
    
    def GetMessage(self):
        return self._msg


# ------------------------------------------------------------------------------


class DEGW_DataEntryPanel(deo.MagazzPanel_O):
    
    degw_status = None
    def DEGW_SetStatus(self, s):
        self.degw_status = s
    def DEGW_GetStatus(self):
        return self.degw_status
    
    def PendDocChangedEvent(self, message=None):
        e = DocChangedEvent(message=(message or self.degw_status))
        self.GetEventHandler().AddPendingEvent(e)
        
    def OnDocEnd(self, event):
        if self.DocSave():
            self.DEGW_SetStatus('saved')
            self.PendDocChangedEvent()
    
    def OnButPrint(self, event):
        if self.PrintDoc():
            self.DEGW_SetStatus('printed')
            self.PendDocChangedEvent()
    
    def OnDocQuit(self, event):
        if self.TestQuit():
            self.DEGW_SetStatus('quitted')
            self.PendDocChangedEvent()
    
    def OnDocDelete(self, event):
        action = aw.awu.MsgDialog(self,\
"""Sei sicuro di voler cancellare il documento?  Confermando, non sarà """\
"""più recuperabile in alcun modo.  """\
"""Confermi l'operazione di eliminazione ?""",\
                  style = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if action == wx.ID_YES:
            if self.RegDelete():
                self.DEGW_SetStatus('deleted')
                self.PendDocChangedEvent()


# ------------------------------------------------------------------------------


class DEGW_DataEntryFrame(deo.MagazzFrame_O):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = deo.FRAME_TITLE
        DEPC = kwargs.pop('DataEntryPanelClass', DEGW_DataEntryPanel)
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = DEPC(self, -1, name='dataentrypanel')
        dem._FrameDialogMixin.__init__(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        cn = self.FindWindowByName
        for name in 'save del print quit'.split():
            self.Bind(wx.EVT_BUTTON, self.OnCloseFrame, cn('but%s'%name))
    
    def OnClose( self, event ):
        if self.panel.TestQuit():
            self.panel.PendDocChangedEvent(message='closed')
            event.Skip()


# ------------------------------------------------------------------------------


class DEGW_DataEntryDialog(deo.MagazzDialog_O):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = deo.FRAME_TITLE
        DEPC = kwargs.pop('DataEntryPanelClass', DEGW_DataEntryPanel)
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = DEPC(self, -1, name='dataentrypanel')
        dem._FrameDialogMixin.__init__(self)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        cn = self.FindWindowByName
        for name in 'save del print quit'.split():
            self.Bind(wx.EVT_BUTTON, self.OnCloseDialog, cn('but%s'%name))
    
    def OnCloseDialog( self, event ):
        if self.IsModal():
            self.EndModal(wx.ID_OK)
        else:
            self.Close()
    
    def OnClose( self, event ):
        if self.panel.TestQuit():
            self.panel.PendDocChangedEvent(message='closed')
            event.Skip()


# ------------------------------------------------------------------------------


class DataEntry_Gateway(object):
    
    degw_parent = None #parent del frame/dialog di dataentry
    
    def DEGW_SetParent(self, p):
        self.degw_parent = p
    
    def DEGW_GetParent(self):
        return self.degw_parent

    def DEGW_SetFrame(self, f):
        setattr(self.DEGW_GetParent(), 'degw_frame', f)
    
    def DEGW_GetFrame(self):
        return getattr(self.DEGW_GetParent(), 'degw_frame', None)
        
    def DEGW_SetDialog(self, d):
        setattr(self.DEGW_GetParent(), 'degw_dialog', d)
    
    def DEGW_GetDialog(self):
        return getattr(self.DEGW_GetParent(), 'degw_dialog', None)
        
    def DEGW_OpenDataEntryFrame(self, **kwargs):
        
        if self.DEGW_GetParent() is None:
            raise Exception, "Parent del dataentry non definito"
        
        if self.DEGW_GetFrame() is None:
            wx.BeginBusyCursor()
            try:
                self.DEGW_SetFrame(DEGW_DataEntryFrame(self.DEGW_GetParent(), **kwargs))
                def FrameClosed(event):
                    self.DEGW_SetFrame(None)
                    event.Skip()
                self.DEGW_GetFrame().Bind(EVT_DOCCHANGED, self.DEGW_OnDocChanged_Frame)
            finally:
                wx.EndBusyCursor()
    
    def DEGW_OnDocChanged_Frame(self, event):
#        if event.GetMessage() == 'closed':
#            self.DEGW_SetFrame(None)
#        else:
#            try:
#                self.DEGW_GetFrame().Hide()
#            except:
#                pass
        try:
            self.DEGW_GetFrame().Hide()
        except:
            pass
        event.Skip()
        
    def DEGW_OpenDataEntryDialog(self, **kwargs):
        
        if self.DEGW_GetParent() is None:
            raise Exception, "Parent del dataentry non definito"
        
        if self.DEGW_GetDialog() is None:
            wx.BeginBusyCursor()
            try:
                self.DEGW_SetDialog(DEGW_DataEntryDialog(self.DEGW_GetParent(), **kwargs))
                def DialogClosed(event):
                    self.DEGW_SetDialog(None)
                    event.Skip()
                self.DEGW_GetDialog().Bind(EVT_DOCCHANGED, self.DEGW_OnDocChanged_Dialog)
            finally:
                wx.EndBusyCursor()
    
    def DEGW_OnDocChanged_Dialog(self, event):
#        if event.GetMessage() == 'closed':
#            self.DEGW_SetDialog(None)
#        else:
#            try:
#                self.DEGW_GetDialog().Hide()
#            except:
#                pass
#        event.Skip()
        try:
            self.DEGW_GetDialog().Hide()
        except:
            pass
