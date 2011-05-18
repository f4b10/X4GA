#!/bin/env python
# -*- coding: iso-8859-1 -*-
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

import wx
import cfg.docsemail_wdr as wdr

import awc.controls.windows as aw

import Env
bt = Env.Azienda.BaseTab

from cfg.azisetup import _SetupPanel


FRAME_TITLE = "Setup invio documenti per email"


class DocsEmailSetupPanel(_SetupPanel):
    """
    Pannello impostazione setup documenti per email.
    """
    
    def __init__(self, *args, **kwargs):
        
        _SetupPanel.__init__(self, *args, **kwargs)
        wdr.DocEmailFunc(self)
        self.SetupRead()
        self.EnableControls()
        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BUTOK)
        self.Bind(wx.EVT_CHECKBOX, self.OnEnableChanged)
    
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
