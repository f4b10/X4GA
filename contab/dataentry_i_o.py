#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry_i_o.py
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
import wx.lib
import wx.grid as gl

import MySQLdb

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import contab.dataentry     as ctb
import contab.dataentry_i   as ctbi
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

import wx.lib.newevent
(GridSelectedEvent, EVT_GRIDSELECTED) = wx.lib.newevent.NewEvent()

import anag.lib as lib

from stormdb.dbtable import DbTable
samefloat = DbTable.samefloat


#costanti per recordset iva
RSIVA_ID_ALIQIVA =  0
RSIVA_iva_cod =     1
RSIVA_iva_des =     2
RSIVA_IMPONIB =     3
RSIVA_IMPOSTA =     4
RSIVA_TTIVATO =     5
RSIVA_INDEDUC =     6
RSIVA_NOCALC =      7
RSIVA_ID_PDCIVA =   8
RSIVA_pdciva_cod =  9
RSIVA_pdciva_des = 10
RSIVA_pdcind_id =  11
RSIVA_pdcind_cod = 12
RSIVA_pdcind_des = 13
RSIVA_NOTE =       14
RSIVA_ISOMAGG =    15



FRAME_TITLE = "Registrazione IVA"


class ContabPanelTipo_I_O(ctbi.ContabPanelTipo_I):
    """
    Panel Dataentry registrazioni iva per contabilità ordinaria.
    """
    
    def __init__(self, *args, **kwargs):
        
        self.regrsi = []     # recordset iva
        self._grid_iva = None
        
        ctbi.ContabPanelTipo_I.__init__(self, *args, **kwargs)
        
        cn = self.FindWindowByName
        
        c = cn('enableseziva')
        if c:
            c.Show()
            self.Bind(wx.EVT_BUTTON, self.OnEnableSezIva, c)
        
        if self.__class__ == ContabPanelTipo_I_O:
            self.Bind(wx.EVT_BUTTON, self.OnParity, cn('butparity'))
        
        self.SetName('regconiva_o_panel')
        self.HelpBuilder_SetDir('contab.dataentry.RegConIva_O')
    
    def OnEnableSezIva(self, event):
        if self.reg_nocalciva:
            msg =\
                """Disabilitando la sezione IVA, questa sarà nuovamente pilotata in modo automatico\n"""\
                """dalla sezione contabile.  Inoltre, eventuali differenze di arrotondamento dell'imposta\n"""\
                """rispetto al documento cartaceo ricevuto non saranno modificabili, se non riattivando la\n"""\
                """sezione IVA stessa."""
        else:
            msg =\
                """Abilitando la sezione IVA essa sarà indipendente dalla sezione contabile;\n"""\
                """ogni cambiamento in questa effettuato non avrà ripercussione nella sezione IVA stessa."""
        msg += """\n\nConfermi l'operazione?"""
        if aw.awu.MsgDialog(self, msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            self.reg_nocalciva = 1 - (self.reg_nocalciva or 0)
            #if self.reg_nocalciva:
                #for r in self.regrsb:
                    #r[ctb.RSDET_ALIQ_ID] = None
                    #r[ctb.RSDET_ALIQ_cod] = None
                    #r[ctb.RSDET_ALIQ_des] = None
                    #r[ctb.RSDET_ALIQ_TOT] = None
            for g in (self._grid_dav,
                      self._grid_iva):
                g.ResetView()
            self.EnableBodyControls()
            event.Skip()
    
    def EnableBodyControls(self, enable=True):
        ctb.ContabPanel.EnableBodyControls(self, enable)
        b = self.FindWindowByName('enableseziva')
        if b:
            if self.reg_nocalciva:
                l = 'Disab.'
            else:
                l = 'Abilita'
            b.SetLabel('%s sez.IVA' % l)
        if self._grid_iva:
            self._grid_iva.EnableEditing(enable and bool(self.reg_nocalciva))
        
    def OnCauChanged(self, event):
        ctbi.ContabPanelTipo_I.OnCauChanged(self, event)
        if self._cfg_davscorp == 1:
            s = 110
        else:
            s = 1
        g = self._grid_dav
        g.SetColSize(7, s) #colonna importo da scorp.
        g.SetColumnDefaultSize(7, s) #colonna importo da scorp.
        g.ResetView()
    
    def OnParity(self, event):
        ctbi.ContabPanelTipo_I.OnParity(self, event)
        row = len(self.regrsb)-1
        if self.regrsb[row][ctb.RSDET_ALIQ_ID]:
            self.UpdateIvaFromDav()
    
    def InitPanelBody( self ):
        ctbi.ContabPanelTipo_I.InitPanelBody(self)
        ctbw.BodyFuncTipo_I_O(self.panbody, True)
        self._GridEdit_Dav__Init__()
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
            self.controls["totdare"].SetValue(None)
            self.controls["totavere"].SetValue(None)
            self.controls["totquadr"].SetValue(None)

    def UpdatePanelIva(self):
        if self._grid_iva is not None:
            self._grid_iva.ResetView()
            self._grid_iva.AutoSizeColumns()
        self.UpdateTotIva()

    def UpdateDavFromIVA(self):
        #determinazione righe contabili iva
        rigiva = []
        for reciva in self.regrsi:
            for colimp, ivaid, ivacod, ivades, forcerow in (\
                (RSIVA_IMPOSTA, RSIVA_ID_PDCIVA, RSIVA_pdciva_cod, RSIVA_pdciva_des, True),
                (RSIVA_INDEDUC, RSIVA_pdcind_id, RSIVA_pdcind_cod, RSIVA_pdcind_des, False)):
                
                #if reciva[colimp]:# or forcerow:
                if not self.dbese.samefloat(reciva[colimp], 0):# or forcerow:
                    
                    try:
                        n = ListSearch(rigiva,\
                               lambda x: x[ctb.RSDET_PDCPA_ID] == reciva[ivaid])
                    except IndexError:
                        rigiva.append([None,           #RSDET_NUMRIGA
                                       "A",            #RSDET_TIPRIGA
                                       reciva[ivaid],  #RSDET_PDCPA_ID
                                       reciva[ivacod], #RSDET_PDCPA_cod
                                       reciva[ivades], #RSDET_PDCPA_des
                                       0,              #RSDET_IMPDARE
                                       0,              #RSDET_IMPAVERE
                                       None,           #RSDET_ALIQ_ID
                                       None,           #RSDET_ALIQ_cod
                                       None,           #RSDET_ALIQ_des
                                       None,           #RSDET_ALIQ_TOT
                                       "",             #RSDET_NOTE
                                       0,              #RSDET_RIGAPI    
                                       0])             #RSDET_SOLOCONT
                        n = len(rigiva)-1             
                    
                    if self._cfg_pasegno == "D":
                        rigiva[n][ctb.RSDET_IMPAVERE] += reciva[colimp]
                        
                    elif self._cfg_pasegno == "A":
                        rigiva[n][ctb.RSDET_IMPDARE] += reciva[colimp]
        
        #controllo segno imposta, se negativo inverto segno contabile
        for r in rigiva:
            if r[ctb.RSDET_IMPDARE]<0:
                r[ctb.RSDET_IMPAVERE] = -r[ctb.RSDET_IMPDARE]
                r[ctb.RSDET_IMPDARE] = 0
            elif r[ctb.RSDET_IMPAVERE]<0:
                r[ctb.RSDET_IMPDARE] = -r[ctb.RSDET_IMPAVERE]
                r[ctb.RSDET_IMPAVERE] = 0
        
        #ricostruzione lista dettaglio
        rs1 = []
        rs2 = []
        for rec in self.regrsb:
            rs1.append(rec)
        
        s = self._cfg_pasegno
        if self.totdoc<0:
            s = "DA"["AD".index(s)]
        td = abs(self.totdoc)
        for rec in rs1:
            if rec[ctb.RSDET_TIPRIGA] != "A": #esclude righe iva
                rs2.append(rec)
                if rec[ctb.RSDET_NUMRIGA] == 1: #riga 1: d/a da self.totdoc
                    if s == "D":
                        rs2[len(rs2)-1][ctb.RSDET_IMPDARE] = td
                        rs2[len(rs2)-1][ctb.RSDET_IMPAVERE] = 0
                    elif s == "A":
                        rs2[len(rs2)-1][ctb.RSDET_IMPDARE] = 0
                        rs2[len(rs2)-1][ctb.RSDET_IMPAVERE] = td
                    for rig in rigiva: #aggiunta righe iva
                        rs2.append(rig)
        
        for nrig in range(len(rs2)): #rinumerazione
            rs2[nrig][0] = nrig+1
        
        del self.regrsb[:]
        for rec in rs2:
            self.regrsb.append(rec)
        
        
        #self._grid_dav.SetGridCursorNewRowCol()

    def IsIvaOK(self):
        return len(self.regrsi)>0
    
    def UpdateTotIva(self):
        self.totimpon = 0
        self.totimpst = 0
        self.totivato = 0
        self.totinded = 0
        for rec in self.regrsi:
            if not rec[RSIVA_ISOMAGG]:
                self.totimpon += rec[RSIVA_IMPONIB]
            self.totimpst += rec[RSIVA_IMPOSTA]
            self.totivato += rec[RSIVA_TTIVATO]
            self.totinded += rec[RSIVA_INDEDUC]
        self.controls["totimpon"].SetValue(self.totimpon)
        self.controls["totimpst"].SetValue(self.totimpst)
        self.controls["totivato"].SetValue(self.totivato)
        self.controls["totinded"].SetValue(self.totinded)

    def UpdateTotDav(self):
        self.CheckQuadraturaIVA_DA()
        return ctbi.ContabPanelTipo_I.UpdateTotDav(self)
    
    def CheckTotaliIVA(self):
        for n, r in enumerate(self.regrsi):
            t1 = r[RSIVA_TTIVATO]
            t2 = 0
            if not r[RSIVA_ISOMAGG]:
                t2 += (r[RSIVA_IMPONIB] or 0)
            t2 += (r[RSIVA_IMPOSTA] or 0)+(r[RSIVA_INDEDUC] or 0)
            if not self.dbese.samefloat(t1, t2):
                return n
        return -1
    
    def CheckQuadraturaIVA_DA(self):
        out = True
        msg = ''
        rsi = self.regrsi
        rsb = self.regrsb
        if self._cfg_pasegno == 'D':
            col = ctb.RSDET_IMPAVERE
        else:
            col = ctb.RSDET_IMPDARE
        if rsi and rsb:
            tot1 = 0
            for r in rsi:
                tot1 += r[RSIVA_TTIVATO]
            tot2 = 0
            for n, r in enumerate(rsb):
                if n>0 and not r[ctb.RSDET_SOLOCONT]:
                    imp = (r[ctb.RSDET_IMPDARE] or 0)-(r[ctb.RSDET_IMPAVERE] or 0)
                    if self._cfg_pasegno == "D":
                        imp *= -1
                    tot2 += imp
            if not Env.adb.DbTable.samefloat(tot1, tot2):
                msg = "ATTENZIONE! Squadratura tra sezione IVA e sezione Dare/Avere."
                out = False
        self.FindWindowByName('ivaquad').SetLabel(msg)
        return out
    
    def RegReadBody(self, idreg):
        out = True
        try:
            #recordset righe contabili
            cmd = """
   SELECT row.numriga, 
          row.tipriga, 
          row.id_pdcpa, 
          pdc.codice, 
          pdc.descriz, 
          if(row.segno="D", row.importo, NULL),
          if(row.segno="A", row.importo, NULL), 
          row.id_aliqiva,
          iva.codice,
          iva.descriz,
          row.davscorp,
          row.note, 
          row.ivaman, 
          row.solocont 
     FROM %s AS row
     JOIN %s AS pdc ON row.id_pdcpa=pdc.id
LEFT JOIN %s AS iva ON row.id_aliqiva=iva.id
    WHERE row.id_reg=%%s and row.tipriga IN ('S','C','A')""" % (bt.TABNAME_CONTAB_B,
                                                                bt.TABNAME_PDC,
                                                                bt.TABNAME_ALIQIVA,)
            self.db_curs.execute(cmd, idreg)
            rsb = self.db_curs.fetchall()
            
            #recordset righe iva
            cmd =\
"""SELECT row.id_aliqiva, iva.codice, iva.descriz, """\
"""row.imponib, row.imposta, row.importo, row.indeduc, """\
"""row.ivaman, row.id_pdciva, pcv.codice, pcv.descriz, """\
"""row.id_pdcind, pcn.codice, pcn.descriz, row.note, """\
"""IF(row.tipriga='I',0,1) """\
"""FROM %s AS row """\
"""JOIN %s AS iva ON row.id_aliqiva=iva.id """\
"""LEFT JOIN %s AS pcv ON row.id_pdciva=pcv.id """\
"""LEFT JOIN %s AS pcn ON row.id_pdcind=pcn.id """\
"""WHERE row.id_reg=%%s and row.tipriga IN ('I', 'O')""" % ( bt.TABNAME_CONTAB_B,\
                                                             bt.TABNAME_ALIQIVA,\
                                                             bt.TABNAME_PDC,\
                                                             bt.TABNAME_PDC )
            self.db_curs.execute(cmd, idreg)
            rsi = self.db_curs.fetchall()
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            out = False
            
        else:
            del self.regrsb[:]
            for b in rsb:
                self.regrsb.append(list(b))
            try:
                n = ListSearch(self.regrsb,\
                               lambda x: x[ctb.RSDET_NUMRIGA] == 1)
            except:
                self.id_pdcpa = None
                self.totdoc = 0
            else:
                r = self.regrsb[n]
                self.id_pdcpa = r[ctb.RSDET_PDCPA_ID]
                if self._cfg_pasegno == "D":
                    self.totdoc = r[ctb.RSDET_IMPDARE]
                    if self.totdoc is None:
                        self.totdoc = -(r[ctb.RSDET_IMPAVERE] or 0)
                else:
                    self.totdoc = r[ctb.RSDET_IMPAVERE]
                    if self.totdoc is None:
                        self.totdoc = -(r[ctb.RSDET_IMPDARE] or 0)
            
            del self.regrsi[:]
            for i in rsi:
                self.regrsi.append(list(i))
            
            self._grid_iva.SetGridCursorNewRowCol()
            if hasattr(self, '_griddav'):
                self._grid_dav.SetGridCursorNewRowCol()
        
        return out

    def RegWriteBody(self):
        #righe iva
        rows = []
        #rmax = len(self.regrsb)
        if self._cfg_pasegno == "D":
            segno = "A"
        else:
            segno = "D"
        rsi = self.regrsi
        for n in range(len(rsi)):
            tr = "I"
            if rsi[n][RSIVA_ISOMAGG]:
                tr = "O"
            rows.append([ self.reg_id,                  #id_reg
                          0,                            #numriga
                          tr,                           #tipriga
                          rsi[n][RSIVA_IMPONIB],        #imponib
                          rsi[n][RSIVA_IMPOSTA],        #imposta
                          rsi[n][RSIVA_TTIVATO],        #importo
                          rsi[n][RSIVA_INDEDUC],        #indeduc
                          rsi[n][RSIVA_NOCALC],         #ivaman
                          segno,                        #segno
                          rsi[n][RSIVA_ID_ALIQIVA],     #id_aliqiva
                          None,                         #davscorp
                          None,                         #solocont
                          self.id_pdcpa,                #id_pdcpa
                          rsi[n][RSIVA_ID_PDCIVA],      #id_pdccp
                          rsi[n][RSIVA_ID_PDCIVA],      #id_pdciva
                          rsi[n][RSIVA_pdcind_id],      #id_pdcind
                          rsi[n][RSIVA_NOTE] ])         #note
        return ctbi.ContabPanelTipo_I.RegWriteBody(self, rows)
    
    def RegReset(self):
        ctbi.ContabPanelTipo_I.RegReset(self)
        del self.regrsi[:]

    def _GridEdit_Iva__Init__(self):
        parent = self.FindWindowById(ctbw.ID_PANGRID_IVA)
        parent.SetSize((0,0))
        size = parent.GetClientSizeTuple()
        
        _STR = gl.GRID_VALUE_STRING
        _FLT = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        
        cols = (
            ( 35, (RSIVA_iva_cod,    "Cod.",                     _STR, False)),
            (100, (RSIVA_iva_des,    "Aliquota IVA",             _STR, False)),
            (110, (RSIVA_IMPONIB,    "Imponibile",               _FLT, False)),
            (110, (RSIVA_IMPOSTA,    "Imposta",                  _FLT, False)),
            ( 40, (RSIVA_ISOMAGG,    "Omg",                      _CHK, False)),
            (110, (RSIVA_INDEDUC,    "Indeducibile",             _FLT, False)),
            (110, (RSIVA_TTIVATO,    "Totale",                   _FLT, False)),
            ( 50, (RSIVA_pdciva_cod, "Cod.",                     _STR, False)),
            (200, (RSIVA_pdciva_des, "Sottoconto IVA",           _STR, False)),
            ( 50, (RSIVA_pdcind_cod, "Cod.",                     _STR, False)),
            (200, (RSIVA_pdcind_des, "S.conto IVA indeducibile", _STR, False)),
            (160, (RSIVA_NOTE,       "Note",                     _STR, False)),
        )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = self.canedit
        canins = self.canins
        
        links = []
        lta = lib.LinkTabAliqIvaAttr( bt.TABNAME_ALIQIVA, #table
                                      0,                  #grid col
                                      RSIVA_ID_ALIQIVA,   #rs col id
                                      RSIVA_iva_cod,      #rs col cod
                                      RSIVA_iva_des,      #rs col des
                                      AliqIvaDialog,      #card class
                                      refresh = True)     #refresh flag
        links.append(lta)
        
        def SetPdcTipIva(lt, *args):
            lt.SetPdcTipCods(self._auto_cod_tippdc_pdciva)
        lta = lib.LinkTabPdcAttr(bt.TABNAME_PDC,
                                 7, #colonna cod.sottoconto iva
                                 RSIVA_ID_PDCIVA,
                                 RSIVA_pdciva_cod,
                                 RSIVA_pdciva_des,
                                 PdcDialog, 
                                 refresh=True,
                                 oncreate=SetPdcTipIva)
        links.append(lta)
        
        def SetPdcTipIvaInd(lt, *args):
            lt.SetPdcTipCods(self._auto_cod_tippdc_pdciva+\
                             self._cfg_pdctipcp_cod)
        lta = lib.LinkTabPdcAttr(bt.TABNAME_PDC,
                                 9, #colonna cod.sottoconto iva indeduc.
                                 RSIVA_pdcind_id,
                                 RSIVA_pdcind_cod,
                                 RSIVA_pdcind_des,
                                 PdcDialog, 
                                 refresh=True,
                                 oncreate=SetPdcTipIvaInd)
        links.append(lta)
        
        TestValues = self._GridEdit_Iva_TestValues
        NewRow = self._GridEdit_Iva_NewRow
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1, TestValues), )
        
        grid = dbglib.DbGrid(parent, -1, size=size, style=wx.SUNKEN_BORDER)
        grid.SetData( self.regrsi, colmap, canedit, canins,\
                      links, afteredit, NewRow )
        
        grid.SetRowLabelSize(80)
        grid.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        grid.SetRowDynLabel(self._GridEdit_Iva_GetRowLabel)
        grid.SetCellDynAttr(self._GridEdit_Iva_GetAttr)
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
#        grid.SetAnchorColumns(4, 1)
        grid.AutoSizeColumns()
        
        def MoveColumnAfterEdit(grid, row, col):
            if col == 0:
                col = 2
            return row, col
        grid.SetColumnsFunc(MoveColumnAfterEdit)
        
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        def MenuPopup(row, event):
            if self.reg_nocalciva and row < len(self.regrsi):
                def _NoCalcIva(*args):#_self=self, row=None):
                    self.regrsi[row][RSIVA_NOCALC] = \
                        1 - (self.regrsi[row][RSIVA_NOCALC] or 0)
                    self._grid_iva.ResetView()
                
                def _DeleteRow(*args):
                    self._grid_iva.DeleteRows(row)
                    self.UpdateDavFromIVA()
                    self.UpdatePanelDav()
                
                self._grid_iva.SelectRow(row)
                if self.regrsi[row][RSIVA_NOCALC]:
                    nocalcDes = "Abilita"
                else:
                    nocalcDes = "Disabilita"
                nocalcDes += " calcolo IVA"
                nocalcId = wx.NewId()
                deleteId = wx.NewId()
                menu = wx.Menu()
                menu.Append(deleteId, "Elimina riga")
                menu.Append(nocalcId, nocalcDes)
                self.Bind(wx.EVT_MENU, _NoCalcIva, id=nocalcId)
                self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
                xo, yo = event.GetPosition()
                #x = self._grid_iva.GetRowSize(row)/2
                self._grid_iva.PopupMenu(menu, (xo, yo))
                menu.Destroy()
            event.Skip()
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if row >= 0 and self.status == ctb.STATUS_EDITING:
                MenuPopup(row, event)
        
        grid.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, _OnRightClick)
        grid.Bind(gl.EVT_GRID_CELL_LEFT_CLICK, self._GridEdit_Iva_OnLeftClick)
        
        self._grid_iva = grid
        
        self._db_pdc = DbTable('pdc')
        self._db_pdc.AddJoin('bilmas', idLeft='id_bilmas')
        self._db_pdc.AddJoin('bilcon', idLeft='id_bilcon')
        self._db_pdc.Reset()
    
    def _GridEdit_Iva_OnLeftClick(self, event):
        if self.status != ctb.STATUS_EDITING or not self.reg_nocalciva:
            return
        col = event.GetCol()
        if self._grid_iva.GetTable().rsColumns[col] == RSIVA_ISOMAGG:
            row = event.GetRow()
            r = self.regrsi[row]
            r[RSIVA_ISOMAGG] = 1-(r[RSIVA_ISOMAGG] or 0)
            t = 0
            if not r[RSIVA_ISOMAGG]:
                t += (r[RSIVA_IMPONIB] or 0)
            t += (r[RSIVA_IMPOSTA] or 0)+(r[RSIVA_INDEDUC] or 0)
            r[RSIVA_TTIVATO] = t
            self._grid_iva.Refresh()
            self.UpdateTotIva()
            self.CheckQuadraturaIVA_DA()
            self.UpdateButtons()
        event.Skip()
    
    def _GridEdit_Iva_NewRow(self):
        newrow = [ None,                   #RSIVA_ID_ALIQIVA
                   None,                   #RSIVA_iva_cod
                   None,                   #RSIVA_iva_des
                   0,                      #RSIVA_IMPONIB
                   0,                      #RSIVA_IMPOSTA
                   0,                      #RSIVA_TTIVATO
                   0,                      #RSIVA_INDEDUC
                   0,                      #RSIVA_NOCALC
                   self._auto_pdciva_id,   #RSIVA_ID_PDCIVA
                   self._auto_pdciva_cod,  #RSIVA_pdciva_cod
                   self._auto_pdciva_des,  #RSIVA_pdciva_des
                   None,                   #RSIVA_pdcind_id
                   None,                   #RSIVA_pdcind_cod
                   None,                   #RSIVA_pdcind_des
                   None,                   #RSIVA_NOTE
                   0 ]                     #RSIVA_ISOMAGG
        self.regrsi.append(newrow)
        return True

    def _GridEdit_Iva_TestValues(self, row, gridcol, col, value):
        try:
            id_aliq = self.regrsi[row][RSIVA_ID_ALIQIVA]
            nocalc = self.regrsi[row][RSIVA_NOCALC]
        except IndexError:
            pass
        else:
            imponib = self.regrsi[row][RSIVA_IMPONIB]
            imposta = self.regrsi[row][RSIVA_IMPOSTA]
            ttivato = self.regrsi[row][RSIVA_TTIVATO]
            indeduc = self.regrsi[row][RSIVA_INDEDUC]
            isomagg = self.regrsi[row][RSIVA_ISOMAGG] or 0
            
            rsi = self.regrsi[row]
            
            def R(n):
                return round(n, bt.VALINT_DECIMALS)
            
            if col == RSIVA_iva_cod:
                
                import awc.tables.util as awtu
                perc, pind, tipo =\
                    awtu.GetRecordInfo(self.db_curs, bt.TABNAME_ALIQIVA, value,\
                                       ('perciva', 'percind', 'tipo',))
                id1,cod1,des1,id2,cod2,des2 = self.GetSottocontiIva(tipo)
                
                #sottoconto iva
                rsi[RSIVA_ID_PDCIVA] = id1
                rsi[RSIVA_pdciva_cod] = cod1
                rsi[RSIVA_pdciva_des] = des1
                
                #sottoconto iva indeducibile, se presente
                if id2 is None:
                    for n, rsb in enumerate(self.regrsb):
                        if n>0 and rsb[ctb.RSDET_TIPRIGA] == 'C':
                            self._db_pdc.Get(rsb[ctb.RSDET_PDCPA_ID])
                            if self._db_pdc.bilmas.tipo == "E":
                                #prende il primo sottoconto di tipo economico presente
                                #nel dettaglio della registrazione
                                id2 =  rsb[ctb.RSDET_PDCPA_ID]
                                cod2 = rsb[ctb.RSDET_PDCPA_cod]
                                des2 = rsb[ctb.RSDET_PDCPA_des]
                                break
                rsi[RSIVA_pdcind_id] = id2
                rsi[RSIVA_pdcind_cod] = cod2
                rsi[RSIVA_pdcind_des] = des2
                
                if nocalc:
                    ttivato = R(imponib+imposta)
                else:
                    imponib, imposta, ttivato, indeduc =\
                           self.CalcolaIva_DaImponibile(id_aliq,
                                                        rsi[RSIVA_IMPONIB],
                                                        indeduc)
                
            elif col == RSIVA_IMPONIB:
                #digitato imponibile
                if nocalc:
                    ttivato = R(imponib+imposta+indeduc)
                else:
                    imponib, imposta, ttivato, indeduc =\
                           self.CalcolaIva_DaImponibile(id_aliq,
                                                        value,
                                                        indeduc)
                
            elif col == RSIVA_IMPOSTA:
                #digitata imposta
                if nocalc:
                    ttivato = R(imponib+imposta+indeduc)
                else:
                    digiva = value
                    imponib, imposta, ttivato, indeduc =\
                      self.CalcolaIva_DaImposta(id_aliq, value, indeduc)
                    if not imponib:
                        #aw.awu.MsgDialog(self, "Il calcolo della parte imponibile porta a zero, l'imposta digitata non è accettata")
                        imponib = imposta = indeduc = ttivato = digiva = 0
                    value = digiva
                
            elif col == RSIVA_INDEDUC:
                #digitato parte indeducibile dell'imposta
                ttivato = R(imponib+imposta+indeduc)
                
            elif col == RSIVA_TTIVATO:
                #digitato tot.ivato
                if nocalc:
                    imposta = R(ttivato-imponib-indeduc)
                else:
                    imponib, imposta, ttivato, indeduc =\
                      self.CalcolaIva_DaIvato(id_aliq, value, indeduc)
                
            elif col == RSIVA_iva_cod:
                #modificata aliquota iva, ricalcolo tutto dall'imponibile
                #se il calcolo è disattivato lo riattivo
                imponib, imposta, ttivato, indeduc =\
                  self.CalcolaIVA(id_aliq,\
                                  imponib = imponib,\
                                  imposta = imposta,\
                                  ivato = ttivato,\
                                  indeduc = indeduc)
                rsi[RSIVA_NOCALC] = 0
            
            if isomagg:
                ttivato -= imponib
            
            rsi[RSIVA_IMPONIB] = imponib
            rsi[RSIVA_IMPOSTA] = imposta
            rsi[RSIVA_TTIVATO] = ttivato
            rsi[RSIVA_INDEDUC] = indeduc
            
            self._grid_iva.ForceResetView()
            
            oldtot = self.totdoc
            self.UpdateTotIva()
            if self.totdoc != oldtot:
                self.ScadCalc()
                self.UpdatePanelScad()
            
            self.UpdateDavFromIVA()
            self.UpdatePanelDav()
        
        return True
    
    def SetAliqIvaDefault(self, dbaliq):
        
        a = dbaliq
        
        aliq_id = a.id
        aliq_cod = a.codice
        aliq_des = a.descriz
        
        #aliquota iva predefinita
        self.aliqdef_id = aliq_id
        self.aliqdef_cod = aliq_cod
        self.aliqdef_des = aliq_des
        
#        if self.aliqdef_id:
#            #metto l'aliquota di default sulle eventuali righe di costo già presenti
#            #(eventualmente inserite dalla prescelta dei conti di costo all'atto
#            #della creazione di una nuova regisrtrazione)
#            for n, rb in enumerate(self.regrsb):
#                if n>0 and rb[ctb.RSDET_TIPRIGA] == "C" and rb[ctb.RSDET_ALIQ_ID] is None:
#                    rb[ctb.RSDET_ALIQ_ID] = self.aliqdef_id
#                    rb[ctb.RSDET_ALIQ_cod] = self.aliqdef_cod
#                    rb[ctb.RSDET_ALIQ_des] = self.aliqdef_des
#        
#        id1, cod1, des1, id2, cod2, des2 = self.GetSottocontiIva(dbaliq.tipo)
#        
#        self.regrsi.append([ aliq_id,  #RSIVA_ID_ALIQIVA
#                             aliq_cod, #RSIVA_iva_cod
#                             aliq_des, #RSIVA_iva_des
#                             0,        #RSIVA_IMPONIB
#                             0,        #RSIVA_IMPOSTA
#                             0,        #RSIVA_TTIVATO
#                             0,        #RSIVA_INDEDUC
#                             0,        #RSIVA_NOCALC
#                             id1,      #RSIVA_ID_PDCIVA
#                             cod1,     #RSIVA_pdciva_cod
#                             des1,     #RSIVA_pdciva_des
#                             id2,      #RSIVA_pdcind_id
#                             cod2,     #RSIVA_pdcind_cod
#                             des2,     #RSIVA_pdcind_des
#                             None,     #RSIVA_NOTE
#                             0 ])      #RSIVA_ISOMAGG
    
    def _GridEdit_Iva_GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        try:
            nocalc = self.regrsi[row][RSIVA_NOCALC]
        except IndexError:
            nocalc = 0
        if row<len(self.regrsi):
            readonly = rscol in (RSIVA_iva_des, RSIVA_pdciva_des)
        else:
            readonly = rscol != RSIVA_iva_cod
        attr.SetReadOnly(readonly)
        #impostazione colori
        fgcol = stdcolor.NORMAL_FOREGROUND
        bgcol = stdcolor.NORMAL_BACKGROUND
        if row<len(self.regrsi):
            if self.reg_nocalciva:
                r = self.regrsi[row]
                i = r[RSIVA_IMPONIB]
                if r[RSIVA_ISOMAGG]:
                    i = 0
                sf = self.dbese.samefloat
                if rscol in (RSIVA_IMPONIB, RSIVA_IMPOSTA, RSIVA_TTIVATO)\
                        and nocalc:
                    bgcol = stdcolor.NOCALC_BACKGROUND
                #elif rscol in (RSIVA_INDEDUC, RSIVA_pdcind_cod, RSIVA_pdcind_des):
                    #bgcol = stdcolor.GetColour("grey88")
                elif rscol == RSIVA_TTIVATO and not sf(r[RSIVA_TTIVATO] or 0, (i or 0)+(r[RSIVA_IMPOSTA] or 0)+(r[RSIVA_INDEDUC] or 0)):
                    fgcol = stdcolor.VALERR_FOREGROUND
                    bgcol = stdcolor.VALERR_BACKGROUND
            else:
                bgcol = stdcolor.GetColour('lightgray')
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        return attr

    def _GridEdit_Iva_GetRowLabel(self, row):
        if row < len(self.regrsi):
            label = "Aliq. #%d" % (row+1)
        else:
            label = ""
        return label
    
    def UpdateButtons(self, enable=True):
        ctbi.ContabPanelTipo_I.UpdateButtons(self, enable)
        c = self.controls["button_end"]
        if c.IsEnabled():
            tip = None
            nie = self.CheckTotaliIVA()
            if len(self.regrsi) == 0:
                tip = 'Manca dettaglio aliquote IVA'
            elif nie>=0:
                tip = 'Totali IVA non congruenti su aliquota #%d' % (nie+1)
            elif self._cfg_quaivanob != 1 and not self.CheckQuadraturaIVA_DA():
                tip = 'Squadratura tra sezione IVA e sezione Dare/Avere'
            if tip:
                c.Enable(False)
                c.SetToolTipString(tip)
    
    def Validate(self):
        
        out = ctbi.ContabPanelTipo_I.Validate(self)
        
        if out:
            #test quadratura iva/dare-avere
            if not self.CheckQuadraturaIVA_DA():
                msg = "Rilevata squadratura tra sezione IVA e sezione Dare/Avere.\n"
                if self._cfg_quaivanob == 1:
                    if aw.awu.MsgDialog(self, msg+'Vuoi proseguire comunque anche in presenza di questa differenza?',
                                        style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                        out = False
                else:
                    aw.awu.MsgDialog(self, msg+'Impossibile confermare la registrazione',
                                     style=wx.ICON_ERROR)
                    out = False
        
        return out
    
    def _GridEdit_Dav__Init__(self):
        
        parent = self.FindWindowById(ctbw.ID_PANGRID_DAV)
        parent.SetSize((0,0))
        
        _STR = gl.GRID_VALUE_STRING
        _NUM = gl.GRID_VALUE_NUMBER+":4"
        _FLT = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        
        cols = (\
                ( 35, (ctb.RSDET_NUMRIGA,   "Riga",         _NUM, False)),
                ( 50, (ctb.RSDET_PDCPA_cod, "Cod.",         _STR, False)),
                (200, (ctb.RSDET_PDCPA_des, "Sottoconto",   _STR, False)),
                (110, (ctb.RSDET_IMPDARE,   "Dare",         _FLT, True )),
                (110, (ctb.RSDET_IMPAVERE,  "Avere",        _FLT, True )),
                ( 40, (ctb.RSDET_ALIQ_cod,  "Cod.",         _STR, True )),
                (100, (ctb.RSDET_ALIQ_des,  "Aliquota IVA", _STR, True )),
                (110, (ctb.RSDET_ALIQ_TOT,  "Da scorp.",    _FLT, True )),
                ( 40, (ctb.RSDET_SOLOCONT,  "SC",           _CHK, True )),
                (150, (ctb.RSDET_NOTE,      "Note",         _STR, False)),)
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        grid = dbglib.DbGrid(parent, -1, size=parent.GetClientSizeTuple())
        grid.SetColMaxChar(ctb.RSDET_NOTE, bt.getStdNoteWidth())
        
        canedit = self.canedit
        canins = self.canins
        
        links = []
        
        #linktable per il sottoconto
        from anag.lib import LinkTabPdcAttr
        lta = LinkTabPdcAttr(bt.TABNAME_PDC,
                             1,
                             ctb.RSDET_PDCPA_ID,
                             ctb.RSDET_PDCPA_cod,
                             ctb.RSDET_PDCPA_des,
                             PdcDialog, refresh=True)
        links.append(lta)
        
        #linktable per l'aliquota iva
        from anag.lib import LinkTabAliqIvaAttr
        lti = LinkTabAliqIvaAttr(bt.TABNAME_ALIQIVA,
                                 5,
                                 ctb.RSDET_ALIQ_ID,
                                 ctb.RSDET_ALIQ_cod,
                                 ctb.RSDET_ALIQ_des,
                                 AliqIvaDialog, refresh=True)
        links.append(lti)
        
        TestValues = self._GridEdit_Dav_TestValues
        NewRow = self._GridEdit_Dav_NewRow
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1, TestValues), )
        
        grid.SetData( self.regrsb, colmap, canedit, canins,\
                      links, afteredit, NewRow )
        grid.SetRowLabelSize(80)
        grid.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        grid.SetRowDynLabel(self._GridEdit_Dav_GetRowLabel)
        grid.SetCellDynAttr(self._GridEdit_Dav_GetAttr)
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
#        grid.SetAnchorColumns(5, 2)
        grid.SetFitColumn(9)
        grid.AutoSizeColumns()
        
        grid.SetColDefault(1)
        
        def MoveColumnAfterEdit(grid, row, col):
            if col == 1:
                s = self._cfg_pasegno
                if self.totdoc<0:
                    s = "DA"["AD".index(s)]
                if s == "D":
                    col = 4
                elif s == "A":
                    col = 3
            #elif col == 5: #da aliq, vado su scorporo o note
                #if self._cfg_davscorp == 1:
                    #col = 8 #importo da scorp.
                #else:
                    #col = 6 #descrizione aliquota
            return row, col
        grid.SetColumnsFunc(MoveColumnAfterEdit)
        
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        def MenuPopup(row, event):
            if row > 0 and row < len(self.regrsb)\
                       and self.regrsb[row][ctb.RSDET_TIPRIGA] != "A":
                    
                def _DeleteRow(*args):
                    riciva = self.regrsb[row][ctb.RSDET_ALIQ_ID] is not None
                    self._grid_dav.DeleteRows(row)
                    if riciva:
                        self.UpdateIvaFromDav()
                    self.UpdateTotDav()
                    self.UpdatePanelDav()
                
                self._grid_dav.SelectRow(row)
                deleteId = wx.NewId()
                menu = wx.Menu()
                menu.Append(deleteId, "Elimina riga")
                self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
                xo, yo = event.GetPosition()
                self._grid_dav.PopupMenu(menu, (xo, yo))
                menu.Destroy()
                
            event.Skip()
        
        def _OnLeftClick(event, self=self):
            if self.status == ctb.STATUS_EDITING:
                row = event.GetRow()
                col = event.GetCol()
                t = self._grid_dav.GetTable()
                rs = t.data
                if 1<=row<len(rs) and col in t.rsColumns:
                    if rs[row][ctb.RSDET_TIPRIGA] == "C":
                        rscol = t.rsColumns[col]
                        if rscol == ctb.RSDET_SOLOCONT:
                            sc = rs[row][rscol] = 1-(rs[row][rscol] or 0)
                            if sc:
                                rs[row][ctb.RSDET_ALIQ_ID] = None
                                rs[row][ctb.RSDET_ALIQ_cod] = None
                                rs[row][ctb.RSDET_ALIQ_des] = None
                                self.UpdateIvaFromDav()
                            self._grid_dav.ResetView()
                            self.CheckQuadraturaIVA_DA()
                            self.UpdateButtons()
            event.Skip()
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if row >= 0 and self.status == ctb.STATUS_EDITING:
                MenuPopup(row, event)
        
        for event, func in (
            (gl.EVT_GRID_CELL_LEFT_CLICK,    _OnLeftClick),
            (gl.EVT_GRID_CELL_RIGHT_CLICK,   _OnRightClick),
            (gl.EVT_GRID_CMD_EDITOR_CREATED, self._GridEdit_Dav_OnEditorShown),
            (gl.EVT_GRID_CMD_EDITOR_SHOWN,   self._GridEdit_Dav_OnEditorShown)):
            grid.Bind(event, func)
        
        self._grid_dav = grid

    def _GridEdit_Dav_GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        
        #impostazione colori
        fgcol = stdcolor.NORMAL_FOREGROUND
        bgcol = stdcolor.NORMAL_BACKGROUND
        
        if row >= len(self.regrsb):
            #nuova riga, permesso ins. solo sottoconto (col.codice)
            readonly = (rscol != ctb.RSDET_PDCPA_cod)
        else:
            #su prima riga e righe automatiche (iva) abilito solo col.note
            tiprig = self.regrsb[row][ctb.RSDET_TIPRIGA]
            readonly = ((row == 0 or tiprig == "A") and rscol != ctb.RSDET_NOTE)
            if readonly:
                bgcol = stdcolor.GetColour('lightgray')
            if not readonly and self.reg_nocalciva:
                readonly = rscol in (#ctb.RSDET_ALIQ_cod,
                                     ctb.RSDET_ALIQ_des,
                                     ctb.RSDET_ALIQ_TOT)
            readonly = readonly or rscol in (ctb.RSDET_NUMRIGA, 
                                             ctb.RSDET_PDCPA_des,
                                             ctb.RSDET_ALIQ_des)
            if not readonly and rscol in (ctb.RSDET_ALIQ_cod,
                                          ctb.RSDET_ALIQ_des):
                readonly = (self.regrsb[row][ctb.RSDET_SOLOCONT] or 0)
            if rscol == ctb.RSDET_SOLOCONT:
                readonly = True
        attr.SetReadOnly(readonly)
        
        rs = self.regrsb
        if col in (3,4) and row<len(rs):
            if not rs[row][ctb.RSDET_IMPDARE] and not rs[row][ctb.RSDET_IMPAVERE]:
                miss = True
                if row == 0:
                    s = self._cfg_pasegno
                else:
                    s = None
                    pdcid = rs[row][ctb.RSDET_PDCPA_ID]
                    if pdcid in self._cfg_pdcpref_da:
                        s = self._cfg_pdcpref_da[pdcid]
                    if s is None:
                        if self._cfg_pasegno == 'D':
                            s = 'A'
                        else:
                            s = 'D'
                if s is not None:
                    if self.totdoc<0:
                        s = self.GetSegnoInvertito(s)
                    if s in 'DA':
                        miss = (col == 3 and s == "D" or col == 4 and s == "A")
                if miss:
                    bgcol = stdcolor.VALMISS_BACKGROUND
        elif rscol == ctb.RSDET_ALIQ_TOT and row<len(rs) and row>0 and rs[row][ctb.RSDET_TIPRIGA] == 'C':
            bgcol = stdcolor.GetColour('darkseagreen1')
        
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        
        return attr

    def _GridEdit_Dav_OnEditorShown(self, event):
        row = event.GetRow()
        col = event.GetCol()
        if col == 1:
            editor = self._grid_dav.GetCellEditor(row, col)
            assert isinstance(editor, dbgred.DataLinkCellEditor),\
                   "L'editor della colonna %d non è DataLinkCellEditor" % col
            if editor._tc:
                if row == 0:
                    idtip = self._cfg_pdctippa_id
                else:
                    idtip = self._cfg_pdctipcp_id
                editor._tc.SetFilterValue(idtip)
        event.Skip()
    
    def _GridEdit_Dav_GetRowLabel(self, row):
        label = ""
        if row < len(self.regrsb):
            try:
                if row == 0:                                     #cli/for
                    if self._cfg_regiva_tipo == "A":
                        label = "Fornitore"
                    else:
                        label = "Cliente"
                elif self.regrsb[row][ctb.RSDET_TIPRIGA] == "A": #iva
                    label = "IVA"
                else:                                            #c/partite
                    if self._cfg_regiva_tipo == "A":
                        label = "Costo"
                    else:
                        label = "Ricavo"
            except IndexError:
                pass
        return label
    
    def _GridEdit_Dav_NewRow(self):
        nrig = len(self.regrsb)+1
        self.regrsb.append([nrig,             #RSDET_NUMRIGA
                            "C",              #RSDET_TIPRIGA
                            None,             #RSDET_PDCPA_ID
                            None,             #RSDET_PDCPA_cod
                            None,             #RSDET_PDCPA_des
                            None,             #RSDET_IMPDARE
                            None,             #RSDET_IMPAVERE
                            self.aliqdef_id,  #RSDET_ALIQ_ID
                            self.aliqdef_cod, #RSDET_ALIQ_cod
                            self.aliqdef_des, #RSDET_ALIQ_des
                            None,             #RSDET_ALIQ_TOT
                            None,             #RSDET_NOTE
                            0,                #RSDET_RIGAPI
                            0])               #RSDET_SOLOCONT
        return True               

    def _GridEdit_Dav_TestValues(self, row, gridcol, col, value):
        
        r = self.regrsb[row]
        
        if col == ctb.RSDET_IMPDARE:    #digitato dare, lo aggiorno e ann.avere
            r[ctb.RSDET_IMPDARE] = value
            r[ctb.RSDET_IMPAVERE] = None
            r[ctb.RSDET_ALIQ_TOT] = None
            
        elif col == ctb.RSDET_IMPAVERE: #digitato avere, lo aggiorno e ann.dare
            r[ctb.RSDET_IMPDARE] = None
            r[ctb.RSDET_IMPAVERE] = value
            r[ctb.RSDET_ALIQ_TOT] = None
            
        elif col == ctb.RSDET_NOTE:
            note = self.regrsb[row][col]
            if note[0:1] == "*":
                note = note[1:]
                for r in range(len(self.regrsb)):
                    self.regrsb[r][col] = note
            
        elif col == ctb.RSDET_PDCPA_cod:
            if row == 0:
                self.UpdateModPag()
            else:
                u = self.InitPdcIndeduc(row)
                if u:
                    self.UpdateDavFromIVA()
            
        elif col == ctb.RSDET_ALIQ_cod:
            r[ctb.RSDET_SOLOCONT] = 0
            self.CheckQuadraturaIVA_DA()
            self.UpdateButtons()
        
        if (col in (ctb.RSDET_PDCPA_cod,
                    ctb.RSDET_ALIQ_cod, 
                    ctb.RSDET_ALIQ_TOT,
                    ctb.RSDET_IMPDARE,
                    ctb.RSDET_IMPAVERE,) and r[ctb.RSDET_ALIQ_ID]) or col == ctb.RSDET_ALIQ_cod:
            
            if col == ctb.RSDET_ALIQ_TOT:
                #digitato importo totale, scorporo prima di aggiornare sez.iva
                imponib, _, _, _ =\
                       self.CalcolaIva_DaIvato(r[ctb.RSDET_ALIQ_ID], value)
                pdcid = r[ctb.RSDET_PDCPA_ID]
                s = None
                if pdcid in self._cfg_pdcpref_da:
                    s = self._cfg_pdcpref_da[pdcid]
                if s is None:
                    if self._cfg_pasegno == 'D':
                        s = 'A'
                    else:
                        s = 'D'
                if s == 'D':
                    r[ctb.RSDET_IMPDARE] = imponib
                    r[ctb.RSDET_IMPAVERE] = None
                elif s == 'A':
                    r[ctb.RSDET_IMPAVERE] = imponib
                    r[ctb.RSDET_IMPDARE] = None
            
            rownum = len(self.regrsb)-row
            ppaid = r[ctb.RSDET_PDCPA_ID]
            self.UpdateIvaFromDav()
            if ppaid:
                row = len(self.regrsb)-rownum
                def Posiz(row, col):
                    def Posiz2(row, col):
                        if col == 5:
                            #editata aliq., vado su colonna:
                            if self._cfg_davscorp == 1:
                                #importo da scorporare, se attivata da causale
                                col = 7
                            else:
                                #descrizione aliquota
                                col = 6
                        elif col == 7:
                            #editata cifra da scorp., mi sposto su:
                            if row<len(self.regrsb)-1:
                                #riga successiva, se c'è
                                row += 1
                                if self.regrsb[row][ctb.RSDET_ALIQ_ID]:
                                    #rimango su col. da scorp, l'aliq. è già presente
                                    col = 7
                                else:
                                    #colonna aliquota
                                    col = 5
                        self._grid_dav.SetGridCursor(row, col)
                        def SetFocus():
                            #setfocus sul grid non funge :(
                            #sull'ultimo dei suoi figli invece si (misteri gui)
                            list(self._grid_dav.GetChildren())[-1].SetFocus()
                        wx.CallAfter(SetFocus)
                    wx.CallAfter(Posiz2, row, col)
                wx.CallAfter(Posiz, row, gridcol)
        
        self._grid_dav.ForceResetView()
        self.UpdateTotDav()
        
        return True
    
    def UpdateIvaFromDav(self):
        if self.reg_nocalciva:
            return
        import awc.tables.util as awtu
        #calcola/ricalcola tutta la sezione iva della registrazione
        rsb = self.regrsb
        rsi = self.regrsi
        #elimino recordset iva, poiché lo devo ricostruire da zero
        del rsi[:]
        #ciclo sul recordset d/a
        for row, rb in enumerate(rsb):
            aliqid = rb[ctb.RSDET_ALIQ_ID]
            if aliqid:
                
                perc, pind, tipo =\
                    awtu.GetRecordInfo(self.db_curs, bt.TABNAME_ALIQIVA, aliqid,\
                                       ('perciva', 'percind', 'tipo',))
                pivaid,pivacod,pivades,pindid,pindcod,pinddes = self.GetSottocontiIva(tipo)
                
                pindid = pindcod = pinddes = None
                i1, i2, i3, i4 = self.CalcolaIva_DaImponibile(aliqid, 100)
                if i4:
                    #l'aliquota porta ad una parte indeducibile,
                    #stabilisco il conto di costo/ricavo della parte indeducibile
                    #(o costo di costo, o automatismo iva inded.)
                    pindid = self._auto_pdcind_id
                    pindcod = self._auto_pdcind_cod
                    pinddes = self._auto_pdcind_des
                    if pindid is None:
                        pindid = rb[ctb.RSDET_PDCPA_ID]
                        pindcod = rb[ctb.RSDET_PDCPA_cod]
                        pinddes = rb[ctb.RSDET_PDCPA_des]
                #è specificata l'aliquota sul costo/ricavo, la cerco nell'iva
                found = False
                for n, ri in enumerate(rsi):
                    if ri[RSIVA_ID_ALIQIVA] == aliqid and ri[RSIVA_ID_PDCIVA] == pivaid and ri[RSIVA_pdcind_id] == pindid:
                        found = True
                        break
                if not found:
                    #aliquota non ancora presente nel rs iva, creo riga
                    self._GridEdit_Iva_NewRow()
                    ri = rsi[-1]
                    ri[RSIVA_ID_PDCIVA] = pivaid
                    ri[RSIVA_pdciva_cod] = pivacod
                    ri[RSIVA_pdciva_des] = pivades
                    ri[RSIVA_pdcind_id] = pindid
                    ri[RSIVA_pdcind_cod] = pindcod
                    ri[RSIVA_pdcind_des] = pinddes
                    ri[RSIVA_ID_ALIQIVA] = rsb[row][ctb.RSDET_ALIQ_ID]
                    ri[RSIVA_iva_cod] = rsb[row][ctb.RSDET_ALIQ_cod]
                    ri[RSIVA_iva_des] = rsb[row][ctb.RSDET_ALIQ_des]
                imp = (rb[ctb.RSDET_IMPDARE] or 0)-(rb[ctb.RSDET_IMPAVERE] or 0)
                if self._cfg_pasegno == "D":
                    imp *= -1
                ri[RSIVA_IMPONIB] += imp
        #ho terminato di computare l'imponibile x ogni aliq, ora calcolo il resto
        for ri in rsi:
            aliqid = ri[RSIVA_ID_ALIQIVA]
            imponib = ri[RSIVA_IMPONIB]
            imponib, imposta, ttivato, indeduc =\
                   self.CalcolaIva_DaImponibile(aliqid, imponib, 0)
            ri[RSIVA_IMPONIB] = imponib
            ri[RSIVA_IMPOSTA] = imposta
            ri[RSIVA_INDEDUC] = indeduc
            ri[RSIVA_TTIVATO] = ttivato
            #controllo di quadratura dell'imponibile in caso di scorporo da griglia D/A
            tx = tt = ttn = None
            for n, rb in enumerate(rsb):
                if rb[ctb.RSDET_ALIQ_ID] == ri[RSIVA_ID_ALIQIVA] and rb[ctb.RSDET_ALIQ_TOT] is not None:
                    tx = (tx or 0) + rb[ctb.RSDET_ALIQ_TOT]
                    if rb[ctb.RSDET_ALIQ_TOT] > tt:
                        tt = rb[ctb.RSDET_ALIQ_TOT]
                        ttn = n
            if tx is not None and not samefloat(ri[RSIVA_TTIVATO], tx):
                dif = ri[RSIVA_TTIVATO]-tx
                if abs(dif) <= .01:
                    if rsb[ttn][ctb.RSDET_IMPDARE] is not None:
                        rsb[ttn][ctb.RSDET_IMPDARE] -= dif
                    elif rsb[ttn][ctb.RSDET_IMPAVERE] is not None:
                        rsb[ttn][ctb.RSDET_IMPAVERE] -= dif
                    ri[RSIVA_IMPONIB] -= dif
                    ri[RSIVA_TTIVATO] -= dif
        if self._grid_iva:
            self._grid_iva.ResetView()
        self.UpdateDavFromIVA()
        self._grid_dav.ResetView()
        self.UpdatePanelIva()
    
    def InitPdcIndeduc(self, row):
        u = False
        r = self.regrsb[row]
        u = False
        for i in self.regrsi:
            if i[RSIVA_pdcind_id] is None:
                i[RSIVA_pdcind_id] = r[ctb.RSDET_PDCPA_ID]
                i[RSIVA_pdcind_cod] = r[ctb.RSDET_PDCPA_cod]
                i[RSIVA_pdcind_des] = r[ctb.RSDET_PDCPA_des]
                u = True
        return u


# ------------------------------------------------------------------------------


class ContabFrameTipo_I_O(ctb.ContabFrame):
    """
    Frame Dataentry registrazioni iva per contabilità ordinaria.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabFrame.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_I_O(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ContabDialogTipo_I_O(ctb.ContabDialog):
    """
    Dialog Dataentry registrazioni iva per contabilità ordinaria.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabDialog.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_I_O(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        self.Layout()
        self.CenterOnScreen()
