#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/comsetup/smtpsetup.py
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

from cfg.azisetup import _SetupPanel

import lib
import base64

import comm.comsmtp as smtp


FRAME_TITLE = "Setup Posta elettronica"


class _CommSetupPanel(_SetupPanel):
    
    tabname = None
    wdr_filler = None
    
    def __init__(self, *args, **kwargs):
        
        _SetupPanel.__init__(self, *args, **kwargs)
        self.dbsetup = adb.DbTable(self.tabname, 'setup')
        self.dbsetup.AddBaseFilter('setup.azienda=%s', Env.Azienda.codice)
        self.wdr_filler(self)
        self.SetupRead()
    
    def SetupRead(self):
        db = self.dbsetup
        db.Retrieve('setup.azienda=%s', Env.Azienda.codice)
        cn = lambda x: self.FindWindowByName(x)
        for name in db.GetFieldNames():
            if name != 'id':
                c = self.FindWindowByName(name)
                if c:
                    v = self.DecodeValue(getattr(db, name), name)
                    c.SetValue(v)
    
    def SetupWrite(self):
        out = True
        db = self.dbsetup
        db.Retrieve('setup.azienda=%s', Env.Azienda.codice)
        if db.IsEmpty():
            db.CreateNewRow()
            db.azienda = Env.Azienda.codice
        cn = self.FindWindowByName
        for name in db.GetFieldNames():
            if name != 'id':
                c = cn(name)
                if c:
                    v = self.EncodeValue(cn(name).GetValue(), name)
                    setattr(db, name, v)
        if db.Save():
            self.SetFuncPar()
        else:
            aw.awu.MsgDialog(self, repr(db.GetError()))
            out = False
        return out
    
    def EncodeValue(self, value, name):
        if name == 'authpswd':
            value = base64.b64encode(value or '')
        else:
            value = _SetupPanel.EncodeValue(self, value, name)
        return value
    
    def DecodeValue(self, value, name):
        if name == 'authpswd':
            value = base64.b64decode(value or '')
        else:
            value = _SetupPanel.EncodeValue(self, value, name)
        return value


# ------------------------------------------------------------------------------


class EmailSetupPanel(_CommSetupPanel):
    """
    Impostazione setup posta elettronica.
    """
    
    tabname = 'x4.cfgmail'
    wdr_filler = wdr.EmailConfigFunc
    
    def __init__(self, *args, **kwargs):
        _CommSetupPanel.__init__(self, *args, **kwargs)
        self.FindWindowByName('authreq').EnableUserPW()
        for name, func in (('btntest', self.OnTestSend),
                           ('btnok', self.OnConfirm),):
            self.Bind(wx.EVT_BUTTON, func, self.FindWindowByName(name))
    
    def OnTestSend(self, event):
        keys = {}
        for key in 'smtpaddr smtpport sender authreq authuser authpswd authtls'.split():
            keys[key] = self.FindWindowByName(key).GetValue()
        miss = False
        for key in keys:
            miss = (key.startswith('auth') and keys['authreq'] and keys[key] is None) or keys[key] is None
            if miss:
                break
        if miss:
            aw.awu.MsgDialog(self, "Definire tutti i valori")
            return
        s = smtp.SendMail(keys['smtpaddr'], keys['smtpport'])
        if keys['authreq']:
            s.set_auth(keys['authuser'], keys['authpswd'], keys['authtls'])
        p = aw.awu.WaitDialog(self, message='Invio messaggio in corso')
        msg = "Messaggio inviato con successo"
        try:
            try:
                if not s.send(keys['sender'], 'Messaggio di prova', 'Messaggio di verifica', keys['sender']):
                    msg = s.get_error()
            except Exception, e:
                msg = repr(e.args)
        finally:
            p.Destroy()
        aw.awu.MsgDialog(self, msg)
        event.Skip()
    
    def SetFuncPar(self):
        cn = self.FindWindowByName
        smtp.SetSMTP_Addr(cn('smtpaddr').GetValue())
        smtp.SetSMTP_Port(cn('smtpport').GetValue())
        smtp.SetAUTH_User(cn('authuser').GetValue())
        smtp.SetAUTH_Pswd(cn('authpswd').GetValue())
        smtp.SetAUTH_TLS(cn('authtls').GetValue())
    
    def Validate(self):
        out = True
        for name in 'sender smtpaddr smtpport'.split():
            ctr = self.FindWindowByName(name)
            if ctr.GetValue():
                ctr.SetBackgroundColour(None)
            else:
                ctr.SetBackgroundColour(Env.Azienda.Colours.VALERR_BACKGROUND)
                out = False
        self.Refresh()
        return out


# ------------------------------------------------------------------------------


class EmailSetupDialog(aw.Dialog):
    """
    Dialog impostazione setup posta elettronica
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = EmailSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTNOK)
    
    def OnSave(self, event):
        self.EndModal(1)
