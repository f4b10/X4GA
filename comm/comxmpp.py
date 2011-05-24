#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         comm/comxmpp.py
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

import time
import xmpp

XMPP_ADDR = ""
def SetXMPP_Addr(x):
    global XMPP_ADDR
    XMPP_ADDR = x

XMPP_PORT = 0
def SetXMPP_Port(x):
    global XMPP_PORT
    XMPP_PORT = x

AUTH_USER = ""
def SetAUTH_User(x):
    global AUTH_USER
    AUTH_USER = x

AUTH_PSWD = ""
def SetAUTH_Pswd(x):
    global AUTH_PSWD
    AUTH_PSWD = x

ONLINE_ONLY = True
def SetOnlineOnly(x):
    global ONLINE_ONLY
    ONLINE_ONLY = x

TIMEOUT = 5
def SetTimeout(x):
    global TIMEOUT
    TIMEOUT = x


class Client(xmpp.Client):
    
    doloop = True
    user2notify = None
    user_status = None
    
    error = None
    
    def __init__(self, jidname=None, pswd=None, server=None, port=None):
        jidname = jidname or AUTH_USER
        pswd    = pswd    or AUTH_PSWD
        server  = server  or XMPP_ADDR
        port    = port    or XMPP_PORT
        self.jid = xmpp.JID(jidname)
        self.jid_pswd = pswd
        self.servername = server
        self.serverport = port
        xmpp.Client.__init__(self, self.jid.getDomain(), debug=[])# ['always', 'nodebuilder'])
    
    def connect_and_sendto(self, user2notify=None, message=':)'):
        user2notify = user2notify or AUTH_USER
        message = unicode(message, 'utf-8', 'replace')
        out = False
        if xmpp.Client.connect(self, server=(self.servername, self.serverport)):
            self.user2notify = user2notify
            if ONLINE_ONLY:
                self.RegisterHandler('presence', self.cb_presence)
            if self.auth(self.jid.getNode(), self.jid_pswd):
                self.sendInitPresence()
            if ONLINE_ONLY:
                t = time.time()
                while self.doloop:
                    self.Process(1)
                    if (time.time()-t) > TIMEOUT:
                        break
                send = (self.user_status == 'available')
            else:
                send = True
            if send:
                msgid = self.send(xmpp.Message(self.user2notify, message))
                out = True
            else:
                self.error = 'Non autorizzato'
        else:
            self.error = 'Connessione impossibile'
        return out
    
    def cb_presence(self, sess, pres):
        f = pres.attrs['from']
        user = '%s@%s' % (f.node, f.domain)
        if user == self.user2notify:
            status = 'available'
            if 'type' in pres.attrs:
                status = pres.attrs['type']
            else:
                for kid in pres.kids:
                    if kid.name == 'status' and len(kid.data)>0:
                        status = kid.data[0]
                        break
                    elif kid.name == 'show' and len(kid.data)>0:
                        status = kid.data[0]
                        break
            self.user_status = status
            if status != 'available':
                self.error = 'Utente non online'
            self.doloop = False
    
    def get_error(self):
        return self.error

NotifyClient = Client
del Client
