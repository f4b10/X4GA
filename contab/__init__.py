#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/__init__.py
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
import stormdb as adb

import Env
bt = Env.Azienda.BaseTab
bc = Env.Azienda.Colours

def GetColorsDA():
    return [bc.GetColour(x) for x in ("blue3",      #dare
                                      "darkgreen")] #avere

_evtREGCHANGED = wx.NewEventType()
EVT_REGCHANGED = wx.PyEventBinder(_evtREGCHANGED, 1)
class RegChangedEvent(wx.PyCommandEvent): pass

_evtPCFCHANGED = wx.NewEventType()
EVT_PCFCHANGED = wx.PyEventBinder(_evtPCFCHANGED, 1)
class PcfChangedEvent(wx.PyCommandEvent): pass

#frame,dialog x reg.iva in ordinaria
from contab.dataentry_i_o  import ContabFrameTipo_I_O,  ContabDialogTipo_I_O

#frame,dialog x reg.iva in semplificata
from contab.dataentry_i_s  import ContabFrameTipo_I_S,  ContabDialogTipo_I_S

#frame,dialog x reg.sola iva
from contab.dataentry_i_si import ContabFrameTipo_I_SI, ContabDialogTipo_I_SI

#frame,dialog x reg.semplici/composte
from contab.dataentry_c    import ContabFrameTipo_C,    ContabDialogTipo_C

#frame,dialog x reg.saldaconto
from contab.dataentry_sc   import ContabFrameTipo_SC,   ContabDialogTipo_SC


#costanti per recordset scadenze
RSSCA_ID      =  0
RSSCA_IDREG   =  1
RSSCA_IDPCF   =  2
RSSCA_DATSCAD =  3
RSSCA_IMPORTO =  4
RSSCA_IMPORVE =  5
RSSCA_NOTE    =  6
RSSCA_ABBUONO =  7
RSSCA_SPESA   =  8
RSSCA_ISRIBA  =  9


#campi della tabella scadenze
scafields = ["id", "id_reg", "id_pcf", "datscad", "importo", "importo_ve",\
             "note", "abbuono", "tipabb", "spesa", "f_riba"]


def RegConFrameClass(id_reg):
    return _GetRegConClass(id_reg, 0)


# ------------------------------------------------------------------------------


def RegConDialogClass(id_reg):
    return _GetRegConClass(id_reg, 1)


# ------------------------------------------------------------------------------


def _GetRegConClass(id_reg, w_tipo):
    """
    Ritorna il Frame (se w_tipo=0) o il Dialog (se w_tipo=1) della registrazione
    contabile congruente con la registrazione passata mediante id.
    Il Frame/Dialog è da instaziare.
    """
    cls = None
    reg = adb.DbTable(bt.TABNAME_CONTAB_H,  'reg', writable=False)
    cau = reg.AddJoin(bt.TABNAME_CFGCONTAB, 'cau', idLeft="id_caus",
                      join=adb.JOIN_LEFT)
    if reg.Get(id_reg) and reg.OneRow():
        tipcontab = bt.TIPO_CONTAB
        if   cau.tipo == "S" and cau.pcf == '1' and cau.pcfscon == '1':
            #saldaconto
            clss = (ContabFrameTipo_SC,   ContabDialogTipo_SC)
        elif cau.tipo == "I" and tipcontab == "O":
            #reg.iva in ordinaria
            clss = (ContabFrameTipo_I_O,  ContabDialogTipo_I_O)
        elif cau.tipo == "I" and tipcontab == "S":
            #reg.iva in semplificata
            clss = (ContabFrameTipo_I_S,  ContabDialogTipo_I_S)
        elif cau.tipo == "E":
            #reg.sola iva
            clss = (ContabFrameTipo_I_SI, ContabDialogTipo_I_SI)
        elif cau.tipo in "SC":
            #reg.semplici/composte
            clss = (ContabFrameTipo_C, ContabDialogTipo_C)
        cls = clss[w_tipo]
    return cls


# ------------------------------------------------------------------------------


def GetInterrPdcFrameClass(id_tipo):
    return _GetInterrPdcClass(id_tipo, 0)


# ------------------------------------------------------------------------------


def GetInterrPdcDialogClass(id_tipo):
    return _GetInterrPdcClass(id_tipo, 1)


# ------------------------------------------------------------------------------


def _GetInterrPdcClass(id_tipo, w_tipo):
    """
    Ritorna il Frame (se w_tipo=0) o il Dialog (se w_tipo=1) di interrogazione
    anagrafica congruente con il tipo di sottoconto passato.
    Il Frame/Dialog è da instaziare.
    """
    cls = None
    tipibase = "ABCFD"
    tipo = adb.DbTable("pdctip", "tipo", writable=False)
    if tipo.Get(id_tipo) and tipo.RowsCount() == 1:
        from contab.pdcint import PdcInterrDialog, PdcInterrFrame
        from contab.pdcint import CasseInterrDialog, CasseInterrFrame
        from contab.pdcint import BancheInterrDialog, BancheInterrFrame
        from contab.pdcint import ClientiInterrDialog, ClientiInterrFrame
        from contab.pdcint import FornitInterrDialog, FornitInterrFrame
        from contab.pdcint import EffettiInterrDialog, EffettiInterrFrame
        if tipo.tipo in tipibase:
            clss = ((CasseInterrFrame,   CasseInterrDialog),\
                    (BancheInterrFrame,  BancheInterrDialog),\
                    (ClientiInterrFrame, ClientiInterrDialog),\
                    (FornitInterrFrame,  FornitInterrDialog),\
                    (EffettiInterrFrame, EffettiInterrDialog))[tipibase.index(tipo.tipo)]
        else:
            clss = [PdcInterrFrame, PdcInterrDialog]
        cls = clss[w_tipo]
    del tipo
    return cls
