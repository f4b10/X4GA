#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         custcontab/comunicazione.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

import os
import sys    
import datetime
import time
import zipfile
#import locale    
import tempfile
from xml.dom import minidom  
import subprocess 
import Env
import wx
from awc.util import MsgDialog            


class SendByCmail():
    
    def __init__(self, sendFrom=None, sendTo=None, subject=None, message=None, attachments=[]):
        
        self.sendFrom    = sendFrom
        self.sendTo      = sendTo
        self.subject     = subject
        self.message     = message
        self.attachments = attachments
        self.exe, self.cfg = self.GetCmailParameter()
       
    def GetCmailParameter(self): 
        self.db_conn = Env.Azienda.DB.connection
        self.db_curs = self.db_conn.cursor() 
        codAzi = Env.Azienda.codice
        cmailexe = cmailcfg = None
        try: 
            cmd ='select cmailexe, cmailcfg from x4.cfgmail where azienda="%s"' % codAzi
            self.db_curs.execute(cmd)
            rs = self.db_curs.fetchone()
            if rs:
                cmailexe = rs[0]
                cmailcfg = rs[1]
        except:
            pass
        return [cmailexe, cmailcfg]
           
    def Send(self):
        cmd = '%s' % self.exe
        cmd = '%s -config:"%s"' % (cmd, self.cfg)
        for to in self.sendTo:
            cmd = '%s -to:%s' % (cmd, to)
        cmd = '%s -subject:"%s"' % (cmd, self.subject)
        self.message=self.message.replace('\n', '\\n')
        cmd = '%s -body:"%s"' % (cmd, self.message)
        for a in self.attachments:
            cmd ='%s -a:"%s"' % (cmd, a)
        logDir = 'c:/cmail.log'
        if not os.path.exists(logDir):
            os.mkdir(logDir)
        logFile = os.path.join(logDir, 'log.txt')
        if os.path.exists(logFile):
            os.remove(logFile)
        cmd = '%s -results:"%s"' % (cmd, logFile)
        
        FNULL = open(os.devnull, 'w')
        process =subprocess.Popen(cmd, stdout=FNULL, stderr=FNULL, shell=True)
        while process.poll()==None:
            wx.Sleep(1)
        FNULL.close()
        if not process.returncode==0:
            msg = "Mail non inviata.\nErrore n.%s" % process.returncode
            if os.path.exists(logFile):
                msg="%s\nnVedi file %s." % (msg, logFile)
            MsgDialog(None, msg)
