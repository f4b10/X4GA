#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         comm/comsmtp.py
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

import smtplib

import email
import email.mime.text
import email.mime.base
import email.mime.multipart
import email.iterators
import email.generator
import email.utils

from email.utils import COMMASPACE, formatdate

from email.mime import text as MIMEText
from email.mime import base as MIMEBase
from email.mime import multipart as MIMEMultipart
from email import iterators as Iterators
from email import generator as Generator
from email import utils as Utils

email.MIMEText = MIMEText.MIMEText
email.MIMEBase = MIMEBase.MIMEBase
email.MIMEMultipart = MIMEMultipart.MIMEMultipart
email.Iterators = Iterators
email.Generator = Generator
email.Utils = Utils

MIMEText = MIMEText.MIMEText
MIMEBase = MIMEBase.MIMEBase
MIMEMultipart = MIMEMultipart.MIMEMultipart

import email.encoders as Encoders 

import os

SMTP_ADDR = ""
def SetSMTP_Addr(x):
    global SMTP_ADDR
    SMTP_ADDR = x

SMTP_PORT = 0
def SetSMTP_Port(x):
    global SMTP_PORT
    SMTP_PORT = x

AUTH_USER = ""
def SetAUTH_User(x):
    global AUTH_USER
    AUTH_USER = x

AUTH_PSWD = ""
def SetAUTH_Pswd(x):
    global AUTH_PSWD
    AUTH_PSWD = x

AUTH_TLS = False
def SetAUTH_TLS(x):
    global AUTH_TLS
    AUTH_TLS = x

SENDER = ""
def SetSender(x):
    global SENDER
    SENDER = x


class AuthFailedException(Exception):
    pass


# ------------------------------------------------------------------------------


class SendMail(object):
    
    """Sends an email to the recipient using the extended MAPI interface
    Subject and Message are strings
    Send{To,CC,BCC} are comma-separated address lists
    MAPIProfile is the name of the MAPI profile"""
    
    SmtpAddress = None  #Nome server SMTP
    SmtpPort =    None  #Numero porta SMTP
    
    SendTo =      None  #Indirizzo destinatario
    Subject =     None  #Oggetto del messaggio
    Message =     None  #Corpo del messaggio
    SendCC =      None  #Indirizzo destinatario in copia
    SendBCC =     None  #Indirizzo destinatario in copia nascosta
    Attachments = None  #Lista nomi file da allegare
    
    AuthUser =    None  #Nome utente per autenticazione server
    AuthPswd =    None  #Password per autenticazione server
    AuthTLS =     None  #Flag autenticazione con TLS
    msg =         None  #Oggetto smtp
    error =       None  #Specifiche errore invio
    
    def __init__(self, smtpServer=None, smtpPort=None, authUser=None, authPswd=None, authTLS=None, sendFrom=None):
        object.__init__(self)
        self.smtpServer = smtpServer or SMTP_ADDR
        self.SmtpPort = smtpPort or SMTP_PORT
        if authUser:
            self.AuthUser = authUser
            self.AuthPswd = authPswd
        else:
            self.AuthUser = AUTH_USER
            self.AuthPswd = AUTH_PSWD
        if self.AuthUser:
            self.AuthTLS = authTLS or AUTH_TLS
        else:
            self.AuthTLS = False
        self.SendFrom = sendFrom
    
    def set_auth(self, user=None, pswd=None, tls=False):
        self.AuthUser = user
        self.AuthPswd = pswd
        self.AuthTLS = tls
    
    def send(self, 
             SendFrom=None, 
             Subject="", 
             Message="", 
             SendTo=None, 
             SendCC=None, 
             SendBCC=None, 
             Attachments=None):
        
        SendFrom = SendFrom or SENDER
        if isinstance(SendTo, basestring):
            SendTo = [SendTo]
        
        self.SendFrom =    SendFrom
        self.SendTo =      SendTo
        self.Subject =     Subject
        self.Message =     Message
        self.SendCC =      SendCC
        self.SendCCN =     SendBCC
        self.Attachments = []+(Attachments or [])
        
        self.msg = MIMEMultipart()
        self.msg['From'] = self.SendFrom or ''
        self.msg['To'] = COMMASPACE.join(SendTo)
        self.msg['Date'] = formatdate(localtime=True)
        self.msg['Subject'] = Subject
        
        self.msg.attach(MIMEText(Message, _charset='utf-8'))
        
        for attach in self.Attachments:
            f = open(attach, 'rb')
            part = MIMEBase('application', "octet-stream")
            part.set_payload(f.read())
            Encoders.encode_base64(part)
            part.add_header('Content-Disposition', 'attachment; filename="%s"'
                            % os.path.basename(attach))
            f.close()
            self.msg.attach(part)
        
        try:
            smtp = smtplib.SMTP(self.smtpServer, int(self.SmtpPort or 0))
            if self.AuthUser:
                if self.AuthTLS:
                    smtp.ehlo()
                    smtp.starttls()
                    smtp.ehlo()
                if not smtp.login(self.AuthUser, self.AuthPswd):
                    raise AuthFailedException, 'Autenticazione fallita'
            smtp.sendmail(self.SendFrom, self.SendTo, self.msg.as_string() )
            smtp.close()
        except Exception, e:
            self.error = repr(e.args)
            return False
        
        return True
    
    def get_error(self):
        return self.error


# ------------------------------------------------------------------------------


class SendDocumentMail(SendMail):
    
    def storicizza(self, tipologia="Documento", id_pdc=None, id_doc=None):
        if self.msg is None:
            raise Exception, "Impossibile storicizzare una mail non inizializzata"
        import Env
        bt = Env.Azienda.BaseTab
        adb = Env.adb
        from mx.DateTime import now
        s = adb.DbTable(bt.TABNAME_DOCSEMAIL, 'docsemail')
        s.CreateNewRow()
        s.datcoda = now()
        s.datsend = now()
        s.id_pdc = id_pdc
        s.id_doc = id_doc
        s.tipologia = tipologia
        s.mittente = self.SendFrom
        s.destinat = ', '.join(self.SendTo)
        s.oggetto = self.Subject
        s.testo = self.Message
        stream = None
        if self.Attachments:
            try:
                f = open(self.Attachments[0], 'rb')
                stream = f.read()
                f.close()
            except:
                pass
        if stream:
            s.documento = stream
        if not s.Save():
            raise Exception, repr(s.GetError())
