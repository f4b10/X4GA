#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/comsetup/xmppsetup.py
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
import Env
bt = Env.Azienda.BaseTab

import awc.controls.windows as aw

import comm_wdr as wdr
import stormdb as adb

from cfg.comsetup.smtpsetup import _CommSetupPanel

import lib
import base64

import comm.comxmpp as xmpp


FRAME_TITLE = "Setup Messaggistica immediata"


class XmppSetupPanel(_CommSetupPanel):
    """
    Impostazione setup XMPP.
    """
    
    tabname = 'x4.cfgxmpp'
    wdr_filler = wdr.XmppConfigFunc
    
    def __init__(self, *args, **kwargs):
        
        _CommSetupPanel.__init__(self, *args, **kwargs)
        for name, func in (('btntest', self.OnTestSend),
                           ('btnok', self.OnConfirm),):
            self.Bind(wx.EVT_BUTTON, func, self.FindWindowByName(name))
    
    def OnTestSend(self, event):
        keys = {}
        for key in 'xmppaddr xmppport authuser authpswd'.split():
            keys[key] = self.FindWindowByName(key).GetValue()
        miss = False
        for key in keys:
            miss = not bool(keys[key])
            if miss:
                break
        if miss:
            aw.awu.MsgDialog(self, "Definire tutti i valori")
            return
        user2notify = keys['authuser']
        p = aw.awu.WaitDialog(self, message='Invio messaggio in corso')
        msg = "Messaggio inviato con successo"
        try:
            try:
                p.SetMessage("Connessione al server XMPP")
                s = xmpp.NotifyClient(keys['authuser'], keys['authpswd'], keys['xmppaddr'], keys['xmppport'])
                p.SetMessage("Invio messaggio test")
                if not s.connect_and_sendto(user2notify, 'Messaggio di verifica'):
                    msg = "Invio non effettuato: l'utente non risulta essere online"
            except Exception, e:
                msg = repr(e.args)
        finally:
            p.Destroy()
        aw.awu.MsgDialog(self, msg)
        event.Skip()
    
    def SetFuncPar(self):
        cn = self.FindWindowByName
        xmpp.SetXMPP_Addr(cn('xmppaddr').GetValue())
        xmpp.SetXMPP_Port(cn('xmppport').GetValue())
        xmpp.SetAUTH_User(cn('authuser').GetValue())
        xmpp.SetAUTH_Pswd(cn('authpswd').GetValue())
        xmpp.SetOnlineOnly(cn('onlineonly').GetValue())
    
    def Validate(self):
        out = True
        for name in 'xmppaddr xmppport authuser'.split():
            ctr = self.FindWindowByName(name)
            if ctr.GetValue():
                ctr.SetBackgroundColour(None)
            else:
                ctr.SetBackgroundColour(Env.Azienda.Colours.VALERR_BACKGROUND)
                out = False
        self.Refresh()
        return out


# ------------------------------------------------------------------------------


class XmppSetupDialog(aw.Dialog):
    """
    Dialog impostazione setup posta elettronica
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = XmppSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def OnSave(self, event):
        self.EndModal(1)
