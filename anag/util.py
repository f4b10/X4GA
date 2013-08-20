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


def GetPdcPanelClass(id_tipo, **kwargs):
    return _GetPdcClass(id_tipo, 0, **kwargs)


# ------------------------------------------------------------------------------


def GetPdcFrameClass(id_tipo, **kwargs):
    return _GetPdcClass(id_tipo, 1, **kwargs)


# ------------------------------------------------------------------------------


def GetPdcDialogClass(id_tipo, **kwargs):
    return _GetPdcClass(id_tipo, 2, **kwargs)


# ------------------------------------------------------------------------------


def _GetPdcClass(id_tipo, w_tipo, **kwargs):
    """
    Ritorna la classe Panel, Frame o Dialog di gestione del sottoconto, in base al suo tipo.
    La classe viene cercata in base all'id_tipo e può riferirsi al Frame, Dialog o Panel a seconda
    di quanto passato in w_tipo (0,1,2)
    """
    cls = None
    tipibase = "ABDCF"
    tipo = None
    if 'tipo' in kwargs:
        tipo = kwargs['tipo']
    else:
        dbtip = adb.DbTable("pdctip", "tipo", writable=False)
        if dbtip.Get(id_tipo) and dbtip.RowsCount() == 1:
            tipo = dbtip.tipo
    from contab.pdcint import PdcInterrPanel, PdcInterrFrame, PdcInterrDialog
    if tipo is not None:
        from contab.pdcint import CasseInterrPanel, CasseInterrFrame, CasseInterrDialog, BancheInterrPanel, BancheInterrFrame, BancheInterrDialog, EffettiInterrPanel, EffettiInterrFrame, EffettiInterrDialog, ClientiInterrPanel, ClientiInterrFrame, ClientiInterrDialog, FornitInterrPanel, FornitInterrFrame, FornitInterrDialog
        clss = [PdcInterrPanel, PdcInterrFrame, PdcInterrDialog]
        if tipo in tipibase:
            clss = ((CasseInterrPanel,   CasseInterrFrame,   CasseInterrDialog),\
                    (BancheInterrPanel,  BancheInterrFrame,  BancheInterrDialog),\
                    (EffettiInterrPanel, EffettiInterrFrame, EffettiInterrDialog),\
                    (ClientiInterrPanel, ClientiInterrFrame, ClientiInterrDialog),\
                    (FornitInterrPanel,  FornitInterrFrame,  FornitInterrDialog))[tipibase.index(tipo)]
        cls = clss[w_tipo]
    if cls is None:
        cls = [PdcInterrPanel, PdcInterrFrame, PdcInterrDialog][w_tipo]
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
