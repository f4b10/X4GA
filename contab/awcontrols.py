#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/awcontrols.py
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
import awc.controls.choice as awch
import stormdb as adb
import Env
bt = Env.Azienda.BaseTab

from cfg.dbtables import ProgrEsercizio


class SelEsercizioChoice(awch.Choice):
    
    esercizi = None
    allow_empty_esercizio = True
    
    def __init__(self, *args, **kwargs):
        k = 'allow_empty_esercizio'
        if k in kwargs:
            self.allow_empty_esercizio = kwargs.pop(k)
        awch.Choice.__init__(self, *args, **kwargs)
        reg = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg', fields=None)
        reg.Synthetize()
        reg.AddGroupOn('esercizio')
        reg.AddOrder('esercizio')#, adb.ORDER_DESCENDING)
        reg.Retrieve()
        self.dbreg = reg
        self.dbprg = adb.DbTable(bt.TABNAME_CFGPROGR, 'progr')
        self.dbese = ProgrEsercizio()
        self.esercizi = list()
        self.ReadEsercizi()
    
    def ReadEsercizi(self, regfilter=None):
        prg = self.dbprg
        if prg.Retrieve('codice=%s', 'ccg_esercizio') and prg.OneRow():
            ec = prg.progrnum
        else:
            ec = 0
        sov = self.dbese.GetSovrapposizione()
        self.Clear()
        reg = self.dbreg
        reg.Retrieve(regfilter)
        e = self.esercizi
        del e[:]
        if self.allow_empty_esercizio and regfilter is None:
            self.Append('Tutti')
            e.append(None)
        for reg in reg:
            d = str(reg.esercizio).zfill(4)
            if reg.esercizio == ec-1 and sov:
                d += ' (da chiud.)'
            elif reg.esercizio < ec:
                d += ' (chiuso)'
            elif reg.esercizio == ec:
                d += ' (in corso)'
            self.Append(d)
            e.append(int(reg.esercizio))
        if self.GetCount():
            self.SetSelection(0)
    
    def ReadEserciziNoStampaGiornale(self):
        self.ReadEsercizi("(reg.st_giobol IS NULL or reg.st_giobol<>1) AND reg.tipreg<>'E'")
        if self.GetCount():
            self.SetValue(self.dbese.GetEsercizioInCorso())
    
    def ReadEserciziSiStampaGiornale(self):
        self.ReadEsercizi("(reg.st_giobol=1) AND reg.tipreg<>'E'")
        if self.GetCount():
            self.SetSelection(self.GetCount()-1)
    
    def SetValue(self, val):
        if val is None and not self.allow_empty_esercizio:
            raise Exception, "Esercizio nullo non consentito"
        if val is None:
            n = 0
        else:
            try:
                n = self.esercizi.index(int(val))
            except ValueError, e:
                n = len(self.esercizi)-1
        self.SetSelection(n)
    
    def GetValue(self):
        n = self.GetSelection()
        try:
            return self.esercizi[n]
        except:
            return None


# ------------------------------------------------------------------------------


class SelEsercizioExChoice(SelEsercizioChoice):
    
    allow_empty_esercizio = False
