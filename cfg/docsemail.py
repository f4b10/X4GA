#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/docsemail.py
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
import os
import wx
import cfg.docsemail_wdr as wdr

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab

from cfg.azisetup import _SetupPanel

from awc.util import MsgDialog



FRAME_TITLE = "Setup invio documenti per email"


class DocsEmailSetupPanel(_SetupPanel):
    """
    Pannello impostazione setup documenti per email.
    """
    
    def __init__(self, *args, **kwargs):
        
        _SetupPanel.__init__(self, *args, **kwargs)
        wdr.DocEmailFunc(self)
        self.SetupRead()
        if not self.IsSendingInternalMail():
            sender = self.GetSenderFromCmailConfig()
            print sender
            if len(sender)==0:
                MsgDialog(self, "Provvedere alla corretta configurazione di cMail per l'invio delle mail.\nNon è stato indicato l'opzione from: nel file di configurazione")
                self.GetParent().Close()
            else:
                self.FindWindowByName('setup_docsemail_sendaddr').SetValue(sender)
        self.EnableControls()
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BUTOK)
        self.Bind(wx.EVT_CHECKBOX, self.OnEnableChanged)
    


    def GetCmailConfigFile(self):
        self.db_conn = Env.Azienda.DB.connection
        self.db_curs = self.db_conn.cursor() 
        codAzi = Env.Azienda.codice
        fileCfg = ""
        try: 
            cmd ='select cmailcfg from x4.cfgmail where azienda="%s"' % codAzi
            self.db_curs.execute(cmd)
            rs = self.db_curs.fetchone()
            if rs:
                fileCfg = rs[0]
        except:
            fileCfg = ""
        return fileCfg
        
    def GetSenderFromCmailConfig(self):
        fileCfg = self.GetCmailConfigFile()
        if os.path.exists(fileCfg):
            sender = self.GetSender(fileCfg)
        else:
            print 'verificare parametri di setup posta'
            sender=''
        return sender
        
    def GetSender(self, cfg):
        m=''
        config = open(cfg, 'r')
        Lines = config.readlines()
        for line in Lines:
            if 'from:' in line:
                c,m = line.split(':')
                if '\n' in m:
                    m= m.replace('\n', '')
                break
        config.close()
        return m        
        
        
        
        
        
    
    def IsSendingInternalMail(self):
        self.db_conn = Env.Azienda.DB.connection
        self.db_curs = self.db_conn.cursor() 
        codAzi = Env.Azienda.codice
        out = 1
        try: 
            cmd ='select internalmail from x4.cfgmail where azienda="%s"' % codAzi
            self.db_curs.execute(cmd)
            rs = self.db_curs.fetchone()
            if rs:
                out = rs[0]
                if out==None:
                    out=1
        except:
            out=1
        print out
        return out
        
        
        
             
        
    
    def OnEnableChanged(self, event):
        self.EnableControls()
        event.Skip()
    
    def EnableControls(self):
        def cn(name):
            return self.FindWindowByName('setup_docsemail_%s' % name)
        for name in 'senddesc sendaddr dallbody'.split():
            cn(name).Enable(cn('sendflag').IsChecked())
    
    def Validate(self):
        out = True
        def cn(x):
            return self.FindWindowByName('setup_docsemail_%s' % x)
        for name in 'senddesc sendaddr dallbody'.split():
            ctr = cn(name)
            if ctr.GetValue():
                ctr.SetBackgroundColour(None)
            else:
                ctr.SetBackgroundColour(Env.Azienda.Colours.VALERR_BACKGROUND)
                out = False
        self.Refresh()
        if out:
            old = (bt.MAGDEMSENDFLAG,
                   bt.MAGDEMSENDDESC,
                   bt.MAGDEMSENDADDR,
                   bt.MAGDEMDALLBODY,)
            bt.MAGDEMSENDFLAG = int(cn('sendflag').GetValue())
            bt.MAGDEMSENDDESC = cn('senddesc').GetValue()
            bt.MAGDEMSENDADDR = cn('sendaddr').GetValue()
            bt.MAGDEMDALLBODY = cn('dallbody').GetValue()
#            bt.defstru()
#            out = wx.GetApp().TestDBVers(force=True)
            if True:#not out:
                bt.MAGDEMSENDFLAG,
                bt.MAGDEMSENDDESC,
                bt.MAGDEMSENDADDR,
                bt.MAGDEMDALLBODY = old
        return out


# ------------------------------------------------------------------------------


class DocsEmailSetupDialog(aw.Dialog):
    """
    Dialog impostazione setup documenti per email.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = DocsEmailSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BUTOK)
    
    def OnSave(self, event):
        self.EndModal(1)
