#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/util.py
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

import stormdb as adb


def GetPdcFrameClass(id_tipo):
    return _GetPdcClass(id_tipo, 0)


# ------------------------------------------------------------------------------


def GetPdcDialogClass(id_tipo):
    return _GetPdcClass(id_tipo, 1)


# ------------------------------------------------------------------------------


def _GetPdcClass(id_tipo, w_tipo):
    """
    Ritorna il Frame (se w_tipo=0) o il Dialog (se w_tipo=1) di gestione
    anagrafica congruente con il tipo di sottoconto passato.
    Il Frame/Dialog è da instaziare.
    """
    cls = None
    tipibase = "ABDCF"
    tipo = adb.DbTable("pdctip", "tipo", writable=False)
    from anag.pdc     import PdcFrame,     PdcDialog
    clss = [PdcFrame, PdcDialog]
    if tipo.Get(id_tipo) and tipo.RowsCount() == 1:
        from anag.casse   import CasseFrame,   CasseDialog
        from anag.banche  import BancheFrame,  BancheDialog
        from anag.effetti import EffettiFrame, EffettiDialog
        from anag.clienti import ClientiFrame, ClientiDialog
        from anag.fornit  import FornitFrame,  FornitDialog
        if tipo.tipo in tipibase:
            clss = ((CasseFrame,   CasseDialog),\
                    (BancheFrame,  BancheDialog),\
                    (EffettiFrame, EffettiDialog),\
                    (ClientiFrame, ClientiDialog),\
                    (FornitFrame,  FornitDialog))[tipibase.index(tipo.tipo)]
    cls = clss[w_tipo]
    del tipo
    return cls


# ------------------------------------------------------------------------------


def GetPdcTipo(id_tipo):
    ctip = None
    tipibase = "ABDCF"
    tipo = adb.DbTable("pdctip", "tipo", writable=False)
    if tipo.Get(id_tipo) and tipo.RowsCount() == 1:
        if tipo.tipo in tipibase:
            ctip = tipo.tipo
    return ctip
