#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/pdflinux.py
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

import os, sys
import subprocess

import awc.util as awu


def PdfPrint(filename, printer, copies=1, cbex=None, usedde=False, cmdprint=False, pdfcmd=None):
    
    out = False
    
    pdfcmd = 'lpr'
    try:
        subprocess.Popen([pdfcmd, '-P', printer, '-#%d'%copies, filename])
        out = True
    except Exception, e:
        awu.MsgDialog(None, repr(e.args), style=awu.wx.ICON_ERROR)
    
    if cbex:
        cbex()
    
    return out

#------------------------------------------------------------------------------

def PdfView(filename, cbex=None, usedde=False, pdfcmd=None):
    
    os.startfile(filename)
    
    if cbex:
        cbex()
    
    return True
