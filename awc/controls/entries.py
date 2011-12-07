#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/controls/entries.py
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
import awc.controls.mixin as cmix
import awc.controls.entries_wdr as wdr
import awc.util as awu
from awc.lib import ControllaPIVA, ControllaCodFisc
import os, sys
import subprocess
from ZSI import FaultException
from report import gcplib


class _EntryCtrlMixin(wx.Window, cmix.ControlsMixin):
    """
    Baseclass per TextCtrl collegati ad un bottone di comportamento (vedi
    sottoclassi).  self.address contiene l'istanza del textctrl vero e proprio;
    self.SetValue()/GetValue() sono proxy per gli stessi metodi del textctrl
    contenuto nel controllo.
    """
    address = None
    
    def __init__(self, parent, id=-1, value=None, 
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        wx.Window.__init__(self, parent, id, pos, size, style=wx.NO_BORDER)
        cmix.ControlsMixin.__init__(self)
        fillfunc = self.GetFiller()
        fillfunc(self)
        self.address = self.FindWindowById(wdr.ID_ADDRESS)
        self.address.Bind(wx.EVT_CHAR, self.OnChar)
        self.Bind(wx.EVT_SET_FOCUS,  self._OnFocusGained)
        self.Bind(wx.EVT_BUTTON, self.OnAction, id=wdr.ID_ACTION)
        self.Bind(wx.EVT_SIZE, self.OnSize)
    
    def OnSize(self, event):
        ci = lambda x: self.FindWindowById(x)
        w = event.GetSize()[0]
        h = ci(wdr.ID_ADDRESS).GetSize()[1]
        try:
            bs = ci(wdr.ID_ACTION).GetSize()[0]
            ci(wdr.ID_ACTION).SetPosition((w-bs, 0))
        except AttributeError:
            bs = 0
        dx = 0
        ci(wdr.ID_ADDRESS).SetSize((w-bs-dx, h))
        event.Skip()
    
    def GetFiller(self):
        raise Exception, "Must subclass"
    
    def OnChar(self, event):
        if not self.address.IsEditable(): return
        obj = event.GetEventObject()
        if event.GetKeyCode() == wx.WXK_TAB and not event.ControlDown():
            if event.ShiftDown():
                self.Navigate(wx.NavigationKeyEvent.IsBackward)
            else:
                try:
                    self.FindWindowById(wdr.ID_ACTION).SetFocus()
                except AttributeError:
                    l = self.GetParent().GetChildren()
                    if self in l:
                        n = l.index(self)
                        if n == len(l):
                            n = 0
                        else:
                            n += 1
                        l[n].SetFocus()
        else:
            event.Skip()
    
    def _OnFocusGained(self, event):
        self.address.SetFocus()
        event.Skip()
    
    def OnAction(self, event):
        raise Exception, "Must subclass"
    
    def SetValue(self, val):
        self.address.SetValue(val)
    
    def GetValue(self):
        return self.address.GetValue()
    
    def Enable(self, e=True):
#        wx.Window.Enable(self, e)
        self.address.Enable(e)
    
    def Disable(self):
        self.Enable(False)
    
    def IsEnabled(self):
#        return wx.Window.IsEnabled(self)
        return self.address.IsEnabled()
    
    def SetEditable(self, e=True):
        self.address.SetEditable(e)
    
    def IsEditable(self):
        return self.address.IsEditable()
    
    def SetForegroundColour(self, *args):
        return self.address.SetForegroundColour(*args)
    
    def SetBackgroundColour(self, *args):
        return self.address.SetBackgroundColour(*args)


# ------------------------------------------------------------------------------


class PartitaIvaEntryCtrl(_EntryCtrlMixin):
    
    askforlink = False
    statectrl = None
    
    def __init__(self, *args, **kwargs):
        _EntryCtrlMixin.__init__(self, *args, **kwargs)
        self.Layout()
        self.ctrpiva = ControllaPIVA()
        self.Bind(wx.EVT_TEXT, self.OnCheckPIva, id=wdr.ID_ADDRESS)
    
    def SetAskForLink(cls, a):
        assert type(a) is bool
        cls.askforlink = a
    SetAskForLink = classmethod(SetAskForLink)
    
    def SetStateControl(self, stc):
        self.statectrl = stc
        def OnStateChanged(event):
            self.ctrpiva.stato = event.GetEventObject().GetValue()
            event.Skip()
        stc.Bind(wx.EVT_TEXT, OnStateChanged)
    
    def OnCheckPIva(self, event):
        self.CheckPIva()
        event.Skip()
    
    def CheckPIva(self):
        def cn(x):
            return self.FindWindowByName(x)
        c = self.ctrpiva
        t = self.GetChildren()[0]
        c.SetPIva(t.GetValue())
        if c.Analizza() not in (c.PIVA_MANCA, c.PIVA_OK):
            t.SetBackgroundColour(t._colors['invalidBackground'])
            t.Refresh()
        else:
            t.AdjustBackgroundColor(focused=(t.FindFocus() == t))
    
    def GetFiller(self):
        return wdr.PartitaIvaEntryFunc

    def OnAction(self, event):
        self.GetAgEntrPIvaDate()
        event.Skip()

    def GetAgEntrPIvaDate(self):
        c = self.ctrpiva
        t = self.GetChildren()[0]
        piva = t.GetValue()
        c.SetPIva(piva)
        if c.Analizza() == c.PIVA_OK:
            if self.askforlink:
                r = awu.MsgDialog(self,\
                                  """Confermi la connessione al sito dell'"""
                                  """Agenzia delle Entrate per verificare le """
                                  """date di inizio e fine attività dell'"""
                                  """azienda con questa Partita IVA?""",
                                  style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
                if r != wx.ID_YES:
                    return
            wait = awu.WaitDialog(self, message="Controllo online in corso...")
            e = 'INDEFINITO'
            try:
                e = 'ESISTENTE'
                wx.BeginBusyCursor()
                try:
                    try:
                        if not c.CheckVies():
                            e = 'NON %s' % e
                        err = None
                    except FaultException, e:
                        err = e.fault.args[1]
                    except Exception, e:
                        err = repr(e.args)
                finally:
                    wx.EndBusyCursor()
                if err:
                    err = "Problema di accesso al webservice del sistema comunitario VIES:\n%s\n\nE' possibile provare con l'accesso via web." % err
                    awu.MsgDialog(self, err, style=wx.ICON_ERROR)
                    e = "ERRORE"
            finally:
                wait.Destroy()
            pos = list(self.GetParent().ClientToScreen(self.GetPosition()))
            pos[1] += self.GetSize()[1]
            dlg = wx.Dialog(self.GetParent(), pos=pos, style=wx.BORDER_SUNKEN)
            wdr.CheckViesFunc(dlg)
            def cn(x):
                return dlg.FindWindowByName(x)
            cn('operat').SetLabel(e)
            def onButtonWEB(event):
                try:
                    wx.BeginBusyCursor()
                    try:
                        self.ctrpiva.GetPIvaDateOpenWebPage()
                    finally:
                        wx.EndBusyCursor()
                except Exception, e:
                    awu.MsgDialog(self, repr(e.args))
            def onButtonQuit(event):
                dlg.EndModal(0)
            for name, func in (('btnweb', onButtonWEB),
                               ('btnquit', onButtonQuit)):
                dlg.Bind(wx.EVT_BUTTON, func, cn(name))
            dlg.ShowModal()
            dlg.Destroy()
            self.SetFocus()
        else:
            awu.MsgDialog(self, message=c.GetStatus(), style=wx.ICON_ERROR)
    
    def GetControllo(self):
        return self.ctrpiva
    
    def SetMaxLength(self, ml):
        self.FindWindowByName('_piva').SetMaxLength(ml)


# ------------------------------------------------------------------------------


class CodiceFiscaleEntryCtrl(_EntryCtrlMixin):
    
    def __init__(self, *args, **kwargs):
        _EntryCtrlMixin.__init__(self, *args, **kwargs)
        self.ctrcf = ControllaCodFisc()
        self.Bind(wx.EVT_TEXT, self.OnCheckCodFisc, id=wdr.ID_ADDRESS)
    
    def OnCheckCodFisc(self, event):
        self.CheckCodFisc()
        event.Skip()
    
    def CheckCodFisc(self):
        def cn(x):
            return self.FindWindowByName(x)
        c = self.ctrcf
        t = self.GetChildren()[0]
        c.SetCodFisc(t.GetValue())
        if c.Analizza() not in (c.CFISC_MANCA, c.CFISC_OK):
            t.AdjustBackgroundColor(error=True)
        else:
            t.AdjustBackgroundColor(focused=(t.FindFocus() == t))
    
    def GetFiller(self):
        return wdr.CodiceFiscaleEntryFunc

    def OnAction(self, event):
        pass
    
    def GetControllo(self):
        return self.ctrcf
    
    def SetMaxLength(self, ml):
        self.FindWindowByName('_codfisc').SetMaxLength(ml)


# ------------------------------------------------------------------------------


class PhoneEntryCtrl(_EntryCtrlMixin):
    
    def GetFiller(self):
        return wdr.PhoneEntryFunc

    def OnAction(self, event):
        self.PhoneTo()
        event.Skip()

    def PhoneTo(self):
        addr = self.FindWindowById(wdr.ID_ADDRESS).GetValue()
        if addr and addr[0].isdigit():
            newaddr = ''
            for c in addr:
                if c.isdigit(): newaddr += c
            addr = '+39%s' % newaddr
        else:
            if ' ' in addr: addr = addr[:addr.index(' ')-1]
        if addr:
            if awu.MsgDialog(self, message="Confermi la chiamata al n.%s?" % addr,
                             style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                os.startfile('callto://%s' % addr)


# ------------------------------------------------------------------------------


class MailEntryCtrl(_EntryCtrlMixin):
    
    def GetFiller(self):
        return wdr.MailEntryFunc

    def OnAction(self, event):
        self.MailTo()
        event.Skip()

    def MailTo(self):
        addr = self.FindWindowById(wdr.ID_ADDRESS).GetValue()
        if addr:
            os.startfile('mailto:%s' % addr)


# ------------------------------------------------------------------------------


class XmppEntryCtrl(_EntryCtrlMixin):
    
    def GetFiller(self):
        return wdr.XmppEntryFunc

    def OnAction(self, event):
        self.XmppTo()
        event.Skip()

    def XmppTo(self):
        #addr = self.FindWindowById(wdr.ID_ADDRESS).GetValue()
        #if addr:
            #os.startfile('mailto:%s' % addr)
        pass


# ------------------------------------------------------------------------------


class HttpEntryCtrl(_EntryCtrlMixin):
    
    def GetFiller(self):
        return wdr.HttpEntryFunc

    def OnAction(self, event):
        self.OpenUrl()
        event.Skip()

    def OpenUrl(self):
        addr = self.FindWindowById(wdr.ID_ADDRESS).GetValue() or ''
        if addr.startswith('http://'):
            os.startfile(addr)


# ------------------------------------------------------------------------------


class FolderEntryCtrl(_EntryCtrlMixin):
    request_description = "Seleziona la cartella:"
    
    def GetFiller(self):
        return wdr.FolderEntryFunc

    def OnAction(self, event):
        self.FolderChoice()
        event.Skip()

    def FolderChoice(self):
        dlg = wx.DirDialog(self, self.request_description,
                          style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)
        addr = self.FindWindowById(wdr.ID_ADDRESS)
        dlg.SetPath(awu.ExpandPath(addr.GetValue()))
        if dlg.ShowModal() == wx.ID_OK:
            addr.SetValue(awu.ReducePath(dlg.GetPath()))
        dlg.Destroy()


# ------------------------------------------------------------------------------


class FileEntryCtrl(_EntryCtrlMixin):
    request_description = "Seleziona il file:"
    
    def GetFiller(self):
        return wdr.FileEntryFunc

    def OnAction(self, event):
        self.FileChoice()
        event.Skip()

    def FileChoice(self, fullpath=False):
        dlg = wx.FileDialog(self, self.request_description, style=wx.OPEN)
        addr = self.FindWindowById(wdr.ID_ADDRESS)
        cwd = os.getcwd().lower()
        dlg.SetPath(os.path.join(cwd, addr.GetValue().replace('./', '')))
        if dlg.ShowModal() == wx.ID_OK:
            if fullpath:
                #name = dlg.GetPath().lower().replace(cwd+'\\', './').replace('\\', '/')
                name = dlg.GetPath().replace(cwd+'\\', './').replace('\\', '/')
            else:
                #name = dlg.GetFilename().lower().replace(cwd+'\\', './').replace('\\', '/')
                name = dlg.GetFilename().replace(cwd+'\\', './').replace('\\', '/')
            addr.SetValue(name)
        dlg.Destroy()
    
    def GetDialogValue(self, dlg):
        return 


# ------------------------------------------------------------------------------


class FullPathFileEntryCtrl(FileEntryCtrl):
    
    def FileChoice(self):
        return FileEntryCtrl.FileChoice(self, fullpath=True)


# ------------------------------------------------------------------------------


GCP_ENABLED = False
GCP_USERNAME = None
GCP_PASSWORD = None

def EnableGoogleGloudPrinting(enable=True):
    global GCP_ENABLED
    GCP_ENABLED = enable

def SetGoogleCloudPrintingUsername(username):
    global GCP_USERNAME
    GCP_USERNAME = username

def SetGoogleCloudPrintingPassword(password):
    global GCP_PASSWORD
    GCP_PASSWORD = password


# ------------------------------------------------------------------------------


class PrintersComboBox(wx.ComboBox):
    
    names = None
    queues = None
    
    def __init__(self, *args, **kwargs):
        
        wx.ComboBox.__init__(self, *args, **kwargs)
        self.names = []
        self.queues = []
        self.types = []
        
        if GCP_ENABLED and GCP_USERNAME and GCP_PASSWORD:
            wx.BeginBusyCursor()
            try:
                if gcplib.AUTH_TOKENS is None:
                    gcplib.InitAuthTokens(GCP_USERNAME, GCP_PASSWORD)
                printers = gcplib.GetPrinters()
                for printer_id, printer in printers.items():
                    name = printer['name']
                    self.names.append('(GCP) %s' % name)
                    self.queues.append('gcp://%s' % printer_id)
                    self.types.append('gcp')
                    self.Append('(GCP) %s' % name)
            except Exception, e:
                awu.MsgDialog(self.GetParent(), repr(e.args), style=wx.ICON_ERROR)
            finally:
                wx.EndBusyCursor()
        if sys.platform == 'win32':
            import win32print
            for tipo in (2,4):
                for a,b,c,d in win32print.EnumPrinters(tipo):
                    self.Append(c)
                    if b.startswith('\\\\'):
                        p = b
                        if ',' in p:
                            p = p.split(',')[0]
                    else:
                        p = c
                    self.names.append(b)
                    self.queues.append(p)
                    self.types.append('true')
        else:
            import cups
            c = cups.Connection()
            printers = c.getPrinters()
            names = printers.keys()
            names.sort()
            for name in printers:
                printer = printers[name]
                desc = printer['printer-info']
                self.names.append(name)
                self.queues.append(name)
                self.types.append('true')
                v = name
                if desc != name:
                    v += (' - %s' % desc)
                self.Append(v)
        self.Append('')
        self.names.append('')
        self.queues.append('')
        self.types.append('dummy')
    
    def GetNames(self):
        return self.names
    
    def GetQueues(self):
        return self.queues
    
    def GetTypes(self):
        return self.types
    
    def SetValue(self, v):
        if sys.platform == 'win32':
            if v is None:
                v = ''
            wx.ComboBox.SetValue(self, v)
        else:
            if v is not None:
                if v in self.queues:
                    n = self.queues.index(v)
                    self.SetSelection(n)
    
    def GetValue(self):
        if sys.platform == 'win32':
            v = wx.ComboBox.GetValue(self)
            if len(v) == 0:
                v = None
        else:
            n = self.GetSelection()
            if n<len(self.queues):
                v = self.queues[n]
        return v
