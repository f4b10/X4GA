#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/tts/__init__.py
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

#"""
#Messaggistica tramite sintesi vocale, basata su MS SAPI4
#"""
#    
#import win32com.client
#import win32clipboard
#import win32con,re
#from win32gui import *
#import win32api
#import pythoncom
#import time
#
#import Env
#adb = Env.adb
#bt = Env.Azienda.BaseTab
#
#import ConfigParser
#
#
#_vs_enabled = False
#def SetVoiceEnabled(ve):
#    global _vs_enabled
#    _vs_enabled = ve
#def GetVoiceEnabled():
#    return _vs_enabled
#
#    
#class Sapi4:
#
#    voice_list = []
#
#    def __init__(self):
#        
#        try:
#            self.directss = win32com.client.Dispatch(
#                "{EEE78591-FE22-11D0-8BEF-0060081841DE}")
#            
#            voice_no = self.directss.Find(0)
#            self.voice = self.directss.Select(voice_no)			
#            voice_name = self.directss.ModeName(voice_no)
#            self.sapi_compliant = 1
#            
#            if len(self.voice_list) < 1:
#                self.getVoiceList()
#            self.selectVoice(voice_name)
#            
#            self.readConfig()
#            
#        except Exception, e:
#            SetVoiceEnabled(False)
#        
#        return None
#    
#    def setVoice(self, voice_no):
#        if 1 <= voice_no <= len(self.voice_list):
#            self.selectVoice(self.voice_list[voice_no-1])
#    
#    def selectVoice(self, voice_name=''):
#        #select voice
#        voice_index = 0
#        voice_no = 0
#        found = 0
#        for voice_compare in self.voice_list:
#            voice_no = voice_no + 1						
#            if voice_compare == voice_name:
#                found = 1
#                break	
#        if found == 0:
#            voice_no = 1
#        self.directss.AudioReset() 		
#        
#        try:
#            self.directss.Select(voice_no)		
#            self.sapi_compliant = 1
#        except:	
#            self.sapi_compliant = 0
#            
#        self.directss.Speak(' ')
#        self.voice_no = voice_no
#        self.voice_index = voice_no - 1
#        self.voice_name = self.directss.ModeName(voice_no)	
#        
#        self.MinSpeed = self.directss.MinSpeed
#        self.MaxSpeed = self.directss.MaxSpeed
#        self.Speed = self.directss.Speed	
#        if self.MinSpeed > self.MaxSpeed: self.sapi_compliant = 0
#        
#        self.MinPitch = self.directss.MinPitch
#        self.MaxPitch = self.directss.MaxPitch
#        self.Pitch = self.directss.Pitch
#        if self.MinPitch > self.MaxPitch: self.sapi_compliant = 0
#        
#        self.MinVolumeLeft = self.directss.MinVolumeLeft
#        self.MaxVolumeLeft = self.directss.MaxVolumeLeft
#        self.VolumeLeft = self.directss.VolumeLeft
#        if self.MinVolumeLeft > self.MaxVolumeLeft: self.sapi_compliant = 0
#        
#        self.MinVolumeRight = self.directss.MinVolumeRight
#        self.MaxVolumeRight = self.directss.MaxVolumeRight	
#        self.VolumeRight = self.directss.VolumeRight
#        if self.MinVolumeRight > self.MinVolumeRight: self.sapi_compliant = 0		
#        
#        return voice_no
#
#    def getVoiceList(self):
#        #fill list of avaliable voices
#        voice_count = self.directss.CountEngines
#        voice_no = 1
#        self.voice_list=[]
#        while voice_no < voice_count + 1:
#            voice_name = self.directss.ModeName(voice_no)
#            #print 'adding voice' + voice_name
#            self.voice_list.append(voice_name)
#            voice_no = voice_no + 1	
#        return self.voice_list
#
#    def setSpeed(self, speed):
#        #set voice speed
#        try:
#            self.directss.Speed = int(speed)
#            self.Speed = speed
#        except:
#            pass
#        return None  
#    
#    def setPitch(self, pitch):
#        #set voice pitch
#        try:
#            self.directss.Pitch = int(pitch)
#            self.Pitch = pitch
#        except:
#            pass
#        return None
#
#    def setVolumeLeft(self, volume):
#        #set voice volume left
#        try:
#            self.directss.VolumeLeft = int(volume)
#            self.VolumeLeft = volume
#        except:
#            pass
#        return None        
#
#    def setVolumeRight(self, volume):
#        #set voice volume right
#        try:
#            self.directss.VolumeRight = int(volume)
#            self.VolumeRight = volume
#        except:
#            pass
#        return None
#    
#    def setVolSx(self, *args, **kwargs):
#        return self.setVolumeLeft(*args, **kwargs)
#    
#    def setVolDx(self, *args, **kwargs):
#        return self.setVolumeRight(*args, **kwargs)
#    
#    def speak(self, msg):
#        try:
#            self.directss.AudioReset()
#            self.directss.Speak(msg)
#        except:
#            pass
#    
#    def readConfig(self, cfgfile='.\\voice.ini'):
#        defaults = {'Enabled':     GetVoiceEnabled(),
#                    'Voice':       self.voice_no,
#                    'Speed':       self.Speed,
#                    'Pitch':       self.Pitch,
#                    'VolumeLeft':  self.VolumeLeft,
#                    'VolumeRight': self.VolumeLeft}
#        cfg = ConfigParser.ConfigParser()
#        cfg.read(cfgfile)
#        s = 'Voice'
#        create = False
#        try:
#            for par in defaults:
#                value = eval(cfg.get(s, par))
#                if par == "Enabled":
#                    SetVoiceEnabled(bool(value))
#                else:
#                    getattr(self, 'set%s' % par)(value)
#        except:
#            create = True
#        if create:
#            if not cfg.has_section(s):
#                cfg.add_section(s)
#            for par, val in defaults.iteritems():
#                cfg.set(s, par, val)
#            cfg.write(open(cfgfile,'w'))
#
#    def writeConfig(self, cfgfile='.\\voice.ini'):
#        values = {'Enabled':     GetVoiceEnabled(),
#                  'Voice':       self.voice_no,
#                  'Speed':       self.Speed,
#                  'Pitch':       self.Pitch,
#                  'VolumeLeft':  self.VolumeLeft,
#                  'VolumeRight': self.VolumeLeft}
#        cfg = ConfigParser.ConfigParser()
#        cfg.read(cfgfile)
#        s = 'Voice'
#        if not cfg.has_section(s):
#            cfg.add_section(s)
#        for par, val in values.iteritems():
#            cfg.set(s, par, val)
#        cfg.write(open(cfgfile,'w'))
#
#
#tts = None
#
#def Parla(msg, stopcurrent=False):
#    
#    global tts
#    if tts is None:
#        tts = Sapi4()
#    
#    if not GetVoiceEnabled():
#        return False
#    
#    if stopcurrent:
#        tts.directss.AudioReset()
#    
#    tts.directss.Speak(msg)
#
#    return True
#
#
#
#def StaZitto():
#    if not GetVoiceEnabled() or not tts: return False
#    tts.directss.AudioReset()
#    Parla("")
#    return True
