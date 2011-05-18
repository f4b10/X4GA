#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/vsynt.py
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

#import wx
#
#import awc.util as awu
#import awc.controls.windows as aw
#
#import Env
#adb = Env.adb
#bt = Env.Azienda.BaseTab
#
#import vsynt_wdr as wdr
#
#import awc.tts as tts
#
#ci = lambda self, x: self.FindWindowById(x)
#
#
#FRAME_TITLE = "Sintetizzatore vocale"
#
#
#class VoiceSyntPanel(aw.Panel):
#    """
#    Impostazione del sintetizzatore vocale.
#    """
#    
#    def __init__(self, *args, **kwargs):
#        
#        aw.Panel.__init__(self, *args, **kwargs)
#        wdr.VoiceSyntFunc(self)
#        
#        if tts.tts is None:
#            self.talker = tts.Sapi4()
#        else:
#            self.talker = tts.tts
#        
#        ci(self, wdr.ID_ENABLE).SetDataLink('', {True: True, False: False})
#        map(lambda voice: ci(self, wdr.ID_VOICE).Append(voice), 
#            self.talker.getVoiceList())
#        
#        self.setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable=True)
#        
#        t = self.talker
#        self.values = {'Enabled': [tts._vs_enabled, wdr.ID_ENABLE],
#                       'Voice':   [t.voice_no,      wdr.ID_VOICE],
#                       'Speed':   [t.Speed,         wdr.ID_SPEED],
#                       'Pitch':   [t.Pitch,         wdr.ID_PITCH],
#                       'VolSx':   [t.VolumeLeft,    wdr.ID_VOLSX],
#                       'VolDx':   [t.VolumeRight,   wdr.ID_VOLDX]}
#        
#        self.Bind(wx.EVT_CHECKBOX, self.OnEnable, ci(self,wdr.ID_ENABLE))
#        self.Bind(wx.EVT_LISTBOX,  self.OnVoice,  ci(self,wdr.ID_VOICE))
#        self.Bind(wx.EVT_SCROLL,   self.OnSpeed,  ci(self,wdr.ID_SPEED))
#        self.Bind(wx.EVT_SCROLL,   self.OnPitch,  ci(self,wdr.ID_PITCH))
#        self.Bind(wx.EVT_SCROLL,   self.OnVolSx,  ci(self,wdr.ID_VOLSX))
#        self.Bind(wx.EVT_SCROLL,   self.OnVolDx,  ci(self,wdr.ID_VOLDX))
#        
#        self.Bind(wx.EVT_BUTTON,   self.OnSave,   ci(self,wdr.ID_OK))
#        self.Bind(wx.EVT_BUTTON,   self.OnTest,   ci(self,wdr.ID_SPEAK))
#        
#        self.LoadValues()
#        
#        voice = self.values['Voice'][0]
#        self.SetVoice(voice)
#        self.SetParams()
#        self.EnableControls()
#    
#    def SetParams(self):
#        for key, (val, cid) in self.values.iteritems():
#            if key == 'Voice':
#                val -= 1 #le voci hanno offset 1
#            ci(self, cid).SetValue(val)
#            if key in ('Speed', 'Pitch', 'VolSx', 'VolDx'):
#                getattr(self.talker, 'set%s' % key)(val)
#    
#    def OnEnable(self, event):
#        self.EnableControls()
#        event.Skip()
#    
#    def OnVoice(self, event):
#        self.SetVoice(event.GetSelection()+1)
#        event.Skip()
#    
#    def OnSpeed(self, event):
#        self.talker.setSpeed(event.GetPosition())
#        self.UpdateCurrent()
#        event.Skip()
#    
#    def OnPitch(self, event):
#        self.talker.setPitch(event.GetPosition())
#        self.UpdateCurrent()
#        event.Skip()
#    
#    def OnVolSx(self, event):
#        self.talker.setVolumeLeft(event.GetPosition())
#        self.UpdateCurrent()
#        event.Skip()
#    
#    def OnVolDx(self, event):
#        self.talker.setVolumeRight(event.GetPosition())
#        self.UpdateCurrent()
#        event.Skip()
#    
#    def OnTest(self, event):
#        self.talker.speak(ci(self, wdr.ID_TEST).GetValue())
#        event.Skip()
#    
#    def EnableControls(self):
#        enab = ci(self, wdr.ID_ENABLE).GetValue() == 1
#        for ctr in awu.GetAllChildrens(self):
#            if ctr.GetId() not in (wdr.ID_ENABLE, wdr.ID_OK, wdr.ID_CANCEL):
#                ctr.Enable(enab)
#    
#    def UpdateCurrent(self):
#        t = self.talker
#        for ccur, cci, cmin, cmax in (
#            (wdr.ID_CURSPEED, wdr.ID_SPEED, t.MinSpeed,       t.MaxSpeed),
#            (wdr.ID_CURPITCH, wdr.ID_PITCH, t.MinPitch,       t.MaxPitch),
#            (wdr.ID_CURVOLSX, wdr.ID_VOLSX, t.MinVolumeLeft,  t.MaxVolumeLeft),
#            (wdr.ID_CURVOLDX, wdr.ID_VOLDX, t.MinVolumeRight, t.MaxVolumeRight),
#            ):
#            cur = ci(self, cci).GetValue()
#            ci(self, ccur).SetLabel("%d%%" % int((float(cur)/float(cmax))*100))
#    
#    def SetVoice(self, voice):
#        t = self.talker
#        t.setVoice(voice)
#        for key, cmin, cmax in (('Speed', t.MinSpeed,       t.MaxSpeed),
#                                ('Pitch', t.MinPitch,       t.MaxPitch),
#                                ('VolSx', t.MinVolumeLeft,  t.MaxVolumeLeft),
#                                ('VolDx', t.MinVolumeRight, t.MaxVolumeRight),
#                                ):
#            ccur, cid = self.values[key]
#            if not cmin <= ccur <= cmax:
#                ccur = int((cmax+cmin)/2)
#            ci(self, cid).SetRange(cmin, cmax)
#            ci(self, cid).SetValue(ccur)
#            getattr(self.talker, 'set%s' % key)(ccur)
#        self.UpdateCurrent()
#    
#    def LoadValues(self):
#        t = self.talker
#        t.readConfig()
#        for key, val in (('Enabled', tts._vs_enabled),
#                         ('Voice',   t.voice_no),
#                         ('Speed',   t.Speed),
#                         ('Pitch',   t.Pitch),
#                         ('VolSx',   t.VolumeLeft),
#                         ('VolDx',   t.VolumeRight)):
#            self.values[key][0] = val
#    
#    def SaveValues(self):
#        tts._vs_enabled = ci(self, wdr.ID_ENABLE).GetValue()
#        self.talker.writeConfig()
#        return True
#    
#    def OnSave(self, event):
#        if self.SaveValues():
#            event.Skip()
#
#
## ------------------------------------------------------------------------------
#
#
#class VoiceSyntFrame(aw.Frame):
#    """
#    Frame Impostazione sintetizzatore vocale.
#    """
#    def __init__(self, *args, **kwargs):
#        if not kwargs.has_key('title') and len(args) < 3:
#            kwargs['title'] = FRAME_TITLE
#        aw.Frame.__init__(self, *args, **kwargs)
#        self.AddSizedPanel(VoiceSyntPanel(self, -1))
#        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_OK)
#        self.Bind(wx.EVT_BUTTON, self.OnClose, id=wdr.ID_CANCEL)
#
#    def OnClose(self, event):
#        self.Close()
#
#
## ------------------------------------------------------------------------------
#
#
#def runTest(frame, nb, log):
#    Env.Azienda.Colours.SetDefaults()
#    win = VoiceSyntFrame()
#    win.Show()
#    return win
#
#
## ------------------------------------------------------------------------------
#
#
#if __name__ == '__main__':
#    import sys,os
#    import runtest
#    db = adb.DB()
#    db.Connect()
#    runtest.main(['', os.path.basename(sys.argv[0])] + sys.argv[1:])
