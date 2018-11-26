#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/password.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
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
import os
import cfg.utenti_wdr as wdr

import awc.util as util
import MySQLdb

import awc.controls.windows as aw

import Env
from Env import Azienda

PSWD_MIN = Azienda.params['password-length']

def mysql_hash_password(password):
    retValue = ''
    nr = 1345345333
    add = 7
    nr2 = 0x12345671
    if len(password.strip())>0:
        for c in (ord(x) for x in password if x not in (' ', '\t')):
            nr^= (((nr & 63)+add)*c)+ (nr << 8) & 0xFFFFFFFF
            nr2= (nr2 + ((nr2 << 8) ^ nr)) & 0xFFFFFFFF
            add= (add + c) & 0xFFFFFFFF
        retValue = "%08x%08x" % (nr & 0x7FFFFFFF,nr2 & 0x7FFFFFFF)
    return retValue


class PswPanel(aw.Panel):
    my=None
    canModify=None

    def __init__(self, *args, **kwargs):
        """
        Costruttore panel selezione azienda.
        """
        
        self.username = kwargs.pop('username')
        self.oldpsw = kwargs.pop('password')
        self.pswAdmin = kwargs.pop('pswAdmin')
        self.msgType = kwargs.pop('msgType')
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        # insert main window here
        
        panel = wx.Panel(self,-1)
        wdr.PswCardFunction( panel )
        
        self.canModify = True
        try:
            self.x4conn = MySQLdb.connect( host = Azienda.DB.servername,
                                           user = Azienda.DB.username,
                                           passwd = Azienda.DB.password,
                                           db = "x4" )
            self.x4cursor = self.x4conn.cursor()
        except MySQLdb.Error, e:
            self.canModify = False
        
        cn = lambda x: self.FindWindowById(x)
        if self.msgType == 0:
            cn(wdr.ID_MSG).SetLabel("")
        elif self.msgType == 1:
            cn(wdr.ID_MSG).SetLabel("PASSWORD VUOTA NON AMMESSA." +chr(13)+chr(10)+"IMPOSTARE PASSWORD VALIDA.")
        
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_CONFIRM)
        self.Bind(wx.EVT_BUTTON, self.OnAbort,   id=wdr.ID_ABORT)
        self.Bind(wx.EVT_TEXT,   self.OnChange,  id=wdr.ID_PSW1)
        self.Bind(wx.EVT_TEXT,   self.OnChange,  id=wdr.ID_PSW2)
    
    def OnActivate(self, event):
        if not self.canModify:
            util.MsgDialog(self, "Impossibile impostare nuova password")
            cn = lambda x: self.FindWindowById(x)
            psw1 = cn(wdr.ID_PSW1).Enable(False)
            psw2 = cn(wdr.ID_PSW2).Enable(False)
            cn(wdr.ID_CONFIRM).Enable(False)
        event.Skip()

    def OnChange(self, event ):
        cn = lambda x: self.FindWindowById(x)
        psw1 = cn(wdr.ID_PSW1).GetValue()
        psw2 = cn(wdr.ID_PSW2).GetValue()
        if self.canModify and psw1==psw2 and len(psw1)>0:
            cn(wdr.ID_CONFIRM).Enable(True)
        else:
            cn(wdr.ID_CONFIRM).Enable(False)
        event.Skip()

    def OnConfirm(self, event ):
        cn = lambda x: self.FindWindowById(x)
        psw1 = cn(wdr.ID_PSW1).GetValue()
        psw2 = cn(wdr.ID_PSW2).GetValue()
        if psw1==psw2==self.oldpsw:
            util.MsgDialog(self, "La nuova password non puo' essere uguale alla vecchia password")
        elif len(psw1)<PSWD_MIN and psw1==psw2:
            util.MsgDialog(self, "La password deve avere un lunghezza minima di %d caratteri" % PSWD_MIN)
        else:
            try:
                self.x4cursor.execute("select old_password('%s');" % psw1)
                e_psw=self.x4cursor.fetchone()[0]
            except:
                e_psw=mysql_hash_password(psw1)
                
                
            sql="UPDATE utenti SET psw='%s' WHERE descriz='%s';" % (e_psw, self.username )
            self.x4cursor.execute(sql)
            self.OnAbort(event)
        event.Skip()
    
    def OnAbort(self, event ):
        self.GetParent().EndModal(1)
        event.Skip()
  

# ------------------------------------------------------------------------------


class PswDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        username = None
        password = None
        pswAdmin = None
        msgType=0
        if 'username' in kwargs: username = kwargs.pop('username')
        if 'password' in kwargs: password = kwargs.pop('password')
        if 'pswAdmin' in kwargs: pswAdmin = kwargs.pop('pswAdmin')
        if 'msgType' in kwargs: msgType = kwargs.pop('msgType')
        for key, val in (('title', 'Modifica Password'),
                         ('style', wx.DEFAULT_DIALOG_STYLE)):
            if not key in kwargs:
                kwargs[key] = val
        aw.Dialog.__init__(self, *args, **kwargs)
        
        self.pswPanel = PswPanel(self, username=username, password=password, pswAdmin=pswAdmin, msgType=msgType)
        self.AddSizedPanel(self.pswPanel)
        self.CentreOnScreen()
        
        self.Bind( wx.EVT_INIT_DIALOG,    self.pswPanel.OnActivate)
