#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/util.py
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

from awc.controls.attachbutton import AttachmentButton

from anag.dbtables import Pdc, Clienti, Fornit

def GetWarningPagNotes(id_pdc):
    msg = None
    pdc = Pdc()
    pdc.Get(id_pdc)
    if pdc.OneRow():
        if pdc.tipana.tipo == 'C':
            anag = Clienti()
        elif pdc.tipana.tipo == 'F':
            anag = Fornit()
        else:
            anag = None
        if anag is not None:
            anag.Get(id_pdc)
            msg = anag.anag.notepag
    return msg


def SetWarningPag(button, id_pdc):
    assert isinstance(button, AttachmentButton)
    button.SetAutotextPS(prefix=GetWarningPagNotes(id_pdc))
    button.UpdateElements()
