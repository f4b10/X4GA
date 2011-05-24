#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry_i_si.py
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

import sys
from datetime import date

import wx
import wx.grid as gl

import MySQLdb

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import contab.dataentry     as ctb
import contab.dataentry_i   as ctbi
import contab.dataentry_i_o as ctbio
import contab.dataentry_wdr as ctbw

import awc.controls.dbgrid        as dbglib
import awc.controls.dbgrideditors as dbgred
import awc.controls.windows as aw

from awc.controls import CELLEDIT_AFTER_UPDATE, CELLEDIT_BEFORE_UPDATE

from awc.util import MsgDialog, MsgDialogDbError, GetNamedChildrens,\
                     ListSearch

from anag.aliqiva import AliqIvaDialog
from anag.pdc import PdcDialog
from anag.pdctip import PdcTipDialog

(GridSelectedEvent, EVT_GRIDSELECTED) = wx.lib.newevent.NewEvent()


#costanti per recordset iva
RSIVA_ID_ALIQIVA,\
RSIVA_iva_cod,\
RSIVA_iva_des,\
RSIVA_IMPONIB,\
RSIVA_IMPOSTA,\
RSIVA_TTIVATO,\
RSIVA_INDEDUC,\
RSIVA_NOCALC,\
RSIVA_ID_PDCIVA,\
RSIVA_pdciva_cod,\
RSIVA_pdciva_des,\
RSIVA_pdcind_id,\
RSIVA_pdcind_cod,\
RSIVA_pdcind_des = [n for n in range(14)]


FRAME_TITLE = "Registrazione sola IVA"


class SelRowPa_SI(ctbi.SelRowPa):
    
    def FillContent(self):
        ctbi.wdr.SelRowPa_SI_Func(self)
    
    def InitGridPref(self):
        pass
            
    def UpdateGridPref(self):
        pass


# ------------------------------------------------------------------------------


class ContabPanelTipo_I_SI(ctbio.ContabPanelTipo_I_O):
    """
    Panel Dataentry registrazioni sola iva.
    """
    
    def __init__(self, *args, **kwargs):
        
        ctbio.ContabPanelTipo_I_O.__init__(self, *args, **kwargs)
        
        self.SetName('regsolaivapanel')
        self.HelpBuilder_SetDir('contab.dataentry.RegSolaIva')
    
    def InitCausale(self):
        """
        Inizializza il tipo di causale (C{"I"})
        """
        self.cautipo = "E"
        self.caufilt = "tipo='%s'" % self.cautipo
        return ctb.ContabPanel.InitCausale(self)
    
    def OnCauChanged(self, event):
        return ctbi.ContabPanelTipo_I.OnCauChanged(self, event)
    
    def EnableBodyControls(self, enable=True):
        return ctbi.ContabPanelTipo_I.EnableBodyControls(self, enable)
    
    def InitPanelBody(self):
        ctbi.ContabPanelTipo_I.InitPanelBody(self)
        ctbw.BodyFuncTipo_I_SI(self.panbody, True)
        self._GridEdit_Iva__Init__()
        return self

    def UpdatePanelBody(self):
        ctb.ContabPanel.UpdatePanelBody(self)
        self.UpdatePanelIva()
        if not self.status in (ctb.STATUS_DISPLAY, ctb.STATUS_EDITING):
            self.controls["totimpon"].SetValue(None)
            self.controls["totimpst"].SetValue(None)
            self.controls["totivato"].SetValue(None)
            self.controls["totinded"].SetValue(None)
    
    def RegReadBody(self, *args):
        ctbio.ContabPanelTipo_I_O.RegReadBody(self, *args)
        #determinazione id fornitore
        cmd =\
"""SELECT row.id_pdcpa """\
"""FROM %s AS row """\
"""WHERE row.id_reg=%%s and row.tipriga='I'""" % bt.TABNAME_CONTAB_B
        self.db_curs.execute(cmd, self.reg_id)
        rs = self.db_curs.fetchone()
        if rs:
            self.id_pdcpa = rs[0]

    def UpdateDavFromIVA(self):
        pass
    
    def UpdateTotDav(self):
        self.UpdateButtons()
    
    def GetSelRowPaClass(self):
        return SelRowPa_SI
    
    def RegSearchClass( self ):
        """
        Indica la classe da utilizzare per il dialog di ricerca delle
        registrazioni.
        """
        return Reg_SI_SearchDialog


# ------------------------------------------------------------------------------


def AdaptGridHeight(g, h=240):
    s = g.GetSize()
    s = [s[0], max(h, s[1])]


# ------------------------------------------------------------------------------


class ContabFrameTipo_I_SI(ctb.ContabFrame):
    """
    Frame Dataentry registrazioni sola iva.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabFrame.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_I_SI(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        AdaptGridHeight(self.dataentrypanel._grid_iva)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ContabDialogTipo_I_SI(ctb.ContabDialog):
    """
    Dialog Dataentry registrazioni sola iva.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabDialog.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_I_SI(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        AdaptGridHeight(self.dataentrypanel._grid_iva)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class Reg_SI_SearchGrid(ctbi.Reg_I_SearchGrid):
    
    def DefColumns(self):
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        return (( 80, ( 1, "Data reg.",  _DAT, False)),
                ( 30, ( 2, "Reg.",       _STR, False)),
                ( 60, ( 3, "Prot.",      _STR, False)),
                (200, ( 4, "Sottoconto", _STR, False)),
                ( 80, ( 5, "N.Doc.",     _STR, True )),
                ( 80, ( 6, "Data doc.",  _DAT, True )),
                (110, ( 7, "Imponibile", _IMP, True )),
                (110, ( 8, "Imposta",    _IMP, True )),
                (  1, ( 0, "#reg",       _STR, False)))
    
    def GetColumn2Fit(self):
        return 3



# ------------------------------------------------------------------------------


class Reg_SI_SearchPanel(ctbi.Reg_I_SearchPanel):

    GridClass = Reg_SI_SearchGrid
    
    def UpdateSearch(self):
        dmin = self.datmin.GetValue()
        ctb.DATSEARCH1 = dmin
        dmax = self.datmax.GetValue()
        ctb.DATSEARCH2 = dmax
        filter = "reg.id_caus=%d" % self.cauid
        par = []
        if dmin:
            filter += " AND reg.datreg>=%s"
            par.append(dmin)
        if dmax:
            filter += " AND reg.datreg<=%s"
            par.append(dmax)
        try:
            wx.BeginBusyCursor()
            try:
                cmd = \
"""   SELECT reg.id, reg.datreg, riv.codice, reg.numiva, """\
"""          pdc.descriz, reg.numdoc, reg.datdoc, """\
"""          SUM(row.imponib), SUM(row.imposta) """\
"""     FROM ((%s AS reg JOIN %s AS cau ON reg.id_caus=cau.id) """\
"""LEFT JOIN contab_b AS row ON row.id_reg=reg.id) """\
"""LEFT JOIN pdc AS pdc ON row.id_pdcpa=pdc.id """\
"""     JOIN regiva AS riv ON reg.id_regiva=riv.id """\
"""    WHERE %s """\
""" GROUP BY reg.id, reg.datreg, riv.codice, reg.numiva, """\
"""          pdc.descriz, reg.numdoc, reg.datdoc """\
""" ORDER BY reg.datreg, reg.numiva """\
 % (bt.TABNAME_CONTAB_H, bt.TABNAME_CFGCONTAB, filter)
                db_curs = Env.adb.db.__database__._dbCon.cursor()
                db_curs.execute(cmd, par)
                rs = db_curs.fetchall()
                db_curs.close()
                self.gridsrc.ChangeData(rs)
                
            except MySQLdb.Error, e:
                MsgDialogDbError(self, e)
        finally:
            wx.EndBusyCursor()


# ------------------------------------------------------------------------------


class Reg_SI_SearchDialog(ctbi.Reg_I_SearchDialog):
    
    panelClass = Reg_SI_SearchPanel
