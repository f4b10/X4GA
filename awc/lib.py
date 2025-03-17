#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         awc/lib.py
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
import re
import urllib2

from awc.checkvat.checkvat import check_vat


class ControllaPIVA(object):
    
    PIVA_OK = 0
    PIVA_MANCA = 1
    PIVA_ERROR = 2
    
    piva = None
    stato = 'IT'
    
    def __init__(self, piva=None):
        object.__init__(self)
        self.piva = piva
    
    def SetPIva(self, piva, stato=None):
        self.piva = piva
        print 'SetPIva %s %s' % (piva, stato)
        if stato is not None:
            self.stato = stato
    
    def Controlla(self):
        return self.stato != 'IT' or self.Analizza() == self.PIVA_OK
    
    def GetStatus(self):
        return "Partita IVA %s" % ["formalmente corretta",
                                   "mancante",
                                   "errata",
                                   "estera"][self.Analizza()]
    
    def Analizza(self):
        
        out = self.PIVA_ERROR
        
        pi = self.piva
        st = self.stato or 'IT'
        
        if not pi:
            out = self.PIVA_MANCA
            
        elif check_vat(st, pi):
            out = self.PIVA_OK
        
        return out
    
#    def GetPIvaDateURL(self):
#        return """http://www1.agenziaentrate.it/servizi/vies/vies.htm?"""\
#               """act=piva&stato=%(stato)s&piva=%(piva)s""" % {'stato': self.stato or 'IT',
#                                                               'piva':  self.piva}
    
    def GetPIvaDateURL(self):
        #=======================================================================
        # return """http://www1.agenziaentrate.it/servizi/vies/transazione.htm?"""\
        #        """s=%(stato)s&p=%(piva)s""" % {'stato': self.stato or 'IT',
        #                                        'piva':  self.piva}
        #=======================================================================
        return """https://ec.europa.eu/taxation_customs/vies/#/vat-validation"""
        #return """http://www1.agenziaentrate.it/servizi/vies"""
    
    def GetPIvaDateOpenWebPage(self):
        os.startfile(self.GetPIvaDateURL())
    
    def CheckVies(self, full=False):
        
        from awc.checkvat.wsdl.checkVatService_client import checkVatServiceLocator, checkVatRequest

        ws = checkVatServiceLocator()
        
        portType = ws.getcheckVatPort()
        
        request = checkVatRequest()
        request._countryCode = self.stato or 'IT'
        request._vatNumber = self.piva
        
        response = portType.checkVat(request)
        if not full:
            ret = response._valid
        else:
            name=''
            address = ''
            if response._valid:
                name    =  response.Name
                address = response.Address
            ret = [response._valid, name, address ]
        #print ret
        return ret


# ------------------------------------------------------------------------------


class ControllaCodFisc(object):
    
    CFISC_OK = 0
    CFISC_MANCA = 1
    CFISC_ERROR = 2
    
    cfisc = None
    
    def __init__(self, cfisc=None):
        object.__init__(self)
        self.cfisc = cfisc
    
    def SetCodFisc(self, cfisc):
        self.cfisc = cfisc
    
    def Controlla(self):
        return self.Analizza() == self.CFISC_OK
    
    def GetStatus(self):
        return "Codice Fiscale %s" % ["formalmente corretto",
                                      "mancante",
                                      "errato"][self.Analizza()]
    
    def Analizza(self):
        
        out = self.CFISC_OK
        cf = self.cfisc
        
        if not cf:
            out = self.CFISC_MANCA
            
        elif (len(cf) == 11) and re.match('^[0-9]+$', cf):
            #è una partita iva
            ctrpi = ControllaPIVA(cf)
            out = ctrpi.Analizza()
            
        elif len(cf) != 16 or not re.match('^[A-Za-z0-9]+$', cf):
            out = self.CFISC_ERROR
            
        else:
            cf = cf.upper()
            s = 0
            for i in range(1, 14, 2):
                c = cf[i]
                if c.isdigit():
                    s += ord(c)-ord('0')
                else:
                    s += ord(c)-ord('A')
            chk = {'0':  1,
                   '1':  0,
                   '2':  5,
                   '3':  7,
                   '4':  9,
                   '5': 13,
                   '6': 15,
                   '7': 17,
                   '8': 19,
                   '9': 21,
                   'A':  1,
                   'B':  0,
                   'C':  5,
                   'D':  7,
                   'E':  9,
                   'F': 13,
                   'G': 15,
                   'H': 17,
                   'I': 19,
                   'J': 21,
                   'K':  2,
                   'L':  4,
                   'M': 18,
                   'N': 20,
                   'O': 11,
                   'P':  3,
                   'Q':  6,
                   'R':  8,
                   'S': 12,
                   'T': 14,
                   'U': 16,
                   'V': 10,
                   'W': 22,
                   'X': 25,
                   'Y': 24,
                   'Z': 23}
            for i in range(0, 15, 2):
                s += chk[cf[i]]
            if chr(s%26+ord('A')) != cf[15]:
                out = self.CFISC_ERROR
        return out


# ------------------------------------------------------------------------------


def codeblock_eval(cb, *parms):
    if type(cb) not in (str, unicode):
        raise Exception, "Tipo errato"
    cb = cb.strip()
    if not cb.startswith('{') or not cb.endswith('}'):
        raise Exception, "Formato errato"
    cb = cb[1:]
    cb = cb[:-1]
    cb = cb.strip()
    if not cb.startswith('|'):
        raise Exception, "Formato errato"
    cb = cb[1:]
    parts = cb.split('|')
    if len(parts) != 2:
        raise Exception, "Formato errato"
    vars, expr = [x.strip() for x in parts]
    vars = vars.split(',')
    if len(vars) != len(parms):
        raise Exception, "Parametri errati (%d occorrenti, %d passati)" % (len(vars), len(parms))
    d = {}
    for name, val in zip(vars, parms):
        d[name] = val
    return eval(expr, None, d)
