#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         contab/bilric.py
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

"""
Bilancio Riclassificato.
"""

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw

import contab.dbtables as dbc
import contab.bil_wdr as wdr

import locale

from lib import SameFloat

from anag.pdc import PdcDialog
import contab
from contab.pdcint import PdcInterrDialog

import report as rpt

from cfg.cfgcontab import CfgContab

import contab.bil as bil

bt = dbc.Env.Azienda.BaseTab
bc = dbc.Env.Azienda.Colours
DateTime = dbc.adb.DateTime
today = dbc.Env.Azienda.Esercizio.dataElab

MsgWait = aw.awu.WaitDialog


FRAME_TITLE_BILVER = "Bilancio di verifica riclassificato"
FRAME_TITLE_BILGES = "Bilancio gestionale riclassificato"
FRAME_TITLE_BILCON = "Bilancio contrapposto riclassificato"


class _BilRicl(object):
    
    def InitWdr(self):
        wdr.bilmas_table = bt.TABNAME_BRIMAS
        wdr.bilcon_table = bt.TABNAME_BRICON
        wdr.bilmas_dialog = wdr.BriMasDialog
        wdr.bilcon_dialog = wdr.BriConDialog
    
    def GetTabBilancio(self):
        return dbc.BilancioRicl()


# ------------------------------------------------------------------------------


class BilGestPanel(_BilRicl, bil.BilGestPanel):
    pass


# ------------------------------------------------------------------------------


class BilGestFrame(aw.Frame):
    """
    Frame Bilancio gestionale.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILGES
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilGestPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilGestDialog(aw.Dialog):
    """
    Dialog Bilancio gestionale.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILGES
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilGestPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilVerifPanel(_BilRicl, bil.BilVerifPanel):
    pass


# ------------------------------------------------------------------------------


class BilVerifFrame(aw.Frame):
    """
    Frame Bilancio di verifica.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILVER
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilVerifPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilVerifDialog(aw.Dialog):
    """
    Dialog Bilancio di verifica.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILVER
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilVerifPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilContrPanel(_BilRicl, bil.BilContrPanel):
    pass


# ------------------------------------------------------------------------------


class BilContrFrame(aw.Frame):
    """
    Frame Bilancio contrapposto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILCON
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilContrPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilContrDialog(aw.Dialog):
    """
    Dialog Bilancio contrapposto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILGES
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilContrPanel(self, -1))
        self.CenterOnScreen()
