#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry_i_s.py
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

from contab.dataentry_i_o import ContabPanelTipo_I_O, ctb, ctbi, ctbw, MySQLdb, MsgDialogDbError, ListSearch, FRAME_TITLE, gl, dbglib, PdcDialog, AliqIvaDialog, stdcolor, dbgred, lib

import Env
from contab.dataentry import RSDET_PDCPA_ID, RSDET_PDCPA_cod, RSDET_PDCPA_des

bt = Env.Azienda.BaseTab

l = ctb.RSDET_last_col

RSDIS_IMPONIB =    l+1
RSDIS_IMPOSTA =    l+2
RSDIS_INDEDUC =    l+3
RSDIS_IMPORTO =    l+4
RSDIS_pdciva_id  = l+5
RSDIS_pdciva_cod = l+6
RSDIS_pdciva_des = l+7
RSDIS_pdcind_id =  l+8
RSDIS_pdcind_cod = l+9
RSDIS_pdcind_des = l+10
RSDIS_ISOMAGG =    l+11



class ContabPanelTipo_I_S(ContabPanelTipo_I_O):
    """
    Panel Dataentry registrazioni iva per contabilità semplif.
    """
    
    def __init__(self, *args, **kwargs):
        
        self._grid_iva = None
        self.regrsi = []
        
        ctbi.ContabPanelTipo_I.__init__(self, *args, **kwargs)
        
        self.totimpon = 0
        self.totimpst = 0
        self.totivato = 0
        self.totinded = 0
        
        self.SetName('regconiva_s_panel')
        self.HelpBuilder_SetDir('contab.dataentry.RegConIva_S')
    
    def InitPanelBody( self ):
        ctbi.ContabPanelTipo_I.InitPanelBody(self)
        ctbw.BodyFuncTipo_I_S(self.panbody, True)
        self._GridEdit_Dav__Init__()
        return self
    
    def OnCauChanged(self, event):
        ctbi.ContabPanelTipo_I.OnCauChanged(self, event)
    
    def CheckQuadraturaIVA_DA(self):
        return True
    
    def UpdateTotIva(self):
        self.totimpon = 0
        self.totimpst = 0
        self.totivato = 0
        self.totinded = 0
        for rec in self.regrsb:
            if rec[ctb.RSDET_TIPRIGA] in "IO":
                self.totimpon += rec[RSDIS_IMPONIB]
                self.totimpst += rec[RSDIS_IMPOSTA]
                self.totivato += rec[RSDIS_IMPORTO]
                self.totinded += rec[RSDIS_INDEDUC]
        self.controls["totimpon"].SetValue(self.totimpon)
        self.controls["totimpst"].SetValue(self.totimpst)
        self.controls["totivato"].SetValue(self.totivato)
        self.controls["totinded"].SetValue(self.totinded)
    
    def UpdateDavFromIVA(self):
        #determinazione righe contabili iva
        rigiva = []
        for rec in self.regrsb:
            if rec[ctb.RSDET_TIPRIGA] in "IO":
                for colimp, ivaid, ivacod, ivades, forcerow in (\
                    (RSDIS_IMPOSTA, RSDIS_pdciva_id, RSDIS_pdciva_cod, RSDIS_pdciva_des, True),
                    (RSDIS_INDEDUC, RSDIS_pdcind_id, RSDIS_pdcind_cod, RSDIS_pdcind_des, False)):
                    
                    if not self.dbese.samefloat(rec[colimp], 0):# or forcerow:
                        
                        if rec[ivaid] is None:
                            #no sottoconto iva definito, prendo il sottoconto della riga
                            ivaid = ctb.RSDET_PDCPA_ID
                            ivacod = ctb.RSDET_PDCPA_cod
                            ivades = ctb.RSDET_PDCPA_des
                        
                        try:
                            n = ListSearch(rigiva,\
                                   lambda x: x[ctb.RSDET_PDCPA_ID] == rec[ivaid])
                        except IndexError:
                            rigiva.append([None,        #RSDET_NUMRIGA
                                           "A",         #RSDET_TIPRIGA
                                           rec[ivaid],  #RSDET_PDCPA_ID
                                           rec[ivacod], #RSDET_PDCPA_cod
                                           rec[ivades], #RSDET_PDCPA_des
                                           0,           #RSDET_IMPDARE
                                           0,           #RSDET_IMPAVERE
                                           None,        #RSDET_ALIQ_ID
                                           None,        #RSDET_ALIQ_cod
                                           None,        #RSDET_ALIQ_des
                                           None,        #RSDET_ALIQ_TOT
                                           "",          #RSDET_NOTE
                                           0,           #RSDET_RIGAPI    
                                           0,           #RSDET_SOLOCONT
                                           None,        #RSDIS_IMPONIB
                                           None,        #RSDIS_IMPOSTA
                                           None,        #RSDIS_INDEDUC
                                           None,        #RSDIS_IMPORTO
                                           None,        #RSDIS_pdciva_id
                                           None,        #RSDIS_pdciva_cod
                                           None,        #RSDIS_pdciva_des
                                           None,        #RSDIS_pdcind_id
                                           None,        #RSDIS_pdcind_cod
                                           None,        #RSDIS_pdcind_des
                                           None])       #RSDIS_ISOMAGG
                            n = len(rigiva)-1             
                        
                        if self._cfg_pasegno == "D":
                            rigiva[n][ctb.RSDET_IMPAVERE] += rec[colimp]
                            
                        elif self._cfg_pasegno == "A":
                            rigiva[n][ctb.RSDET_IMPDARE] += rec[colimp]
        
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
    
    def UpdateIvaFromDav(self):
        pass
    
    def UpdateButtons(self, enable=True):
        ctbi.ContabPanelTipo_I.UpdateButtons(self, enable)
        c = self.controls["button_end"]
        if c.IsEnabled():
            tip = None
            nie = self.CheckTotaliIVA()
            if nie>=0:
                tip = 'Totali IVA non congruenti su riga #%d' % (nie+1)
            else:
                for nda, r in enumerate(self.regrsb):
                    if r[ctb.RSDET_TIPRIGA] in "CI" and not r[ctb.RSDET_IMPDARE] and not r[ctb.RSDET_IMPAVERE]:
                        if nda>0 or bool(self.totdoc):
                            tip = 'Manca Dare/Avere su riga #%d' % (nda+1)
                            break
            if tip:
                c.Enable(False)
                c.SetToolTipString(tip)
    
    def CheckTotaliIVA(self):
        for n, r in enumerate(self.regrsb):
            if r[ctb.RSDET_TIPRIGA] in "IO":
                if not r[RSDIS_IMPONIB]:
                    return n
                t1 = r[RSDIS_IMPORTO]
                t2 = 0
                if True:#not r[RSDIS_ISOMAGG]:
                    t2 += (r[RSDIS_IMPONIB] or 0)
                t2 += (r[RSDIS_IMPOSTA] or 0)+(r[RSDIS_INDEDUC] or 0)
                if not self.dbese.samefloat(t1, t2):
                    return n
        return -1
    
    def AddDefaultRow(self, row):
        #nel dataentry di classe superiore, i sottoconti predefiniti vengono aggiunti come righe "C"
        #e con struttura priva dei dati iva; ricorro quindi al metodo di inserimento della griglia,
        #che setta correttamente numero e tipo riga, quindi inizializzo i dati del sottoconto con quelli
        #in arrivo nella matrice dati della riga in aggiunta dal metodo della classe superiore
        self._GridEdit_Dav_NewRow()
        r = self.regrsb[-1]
        for col in (ctb.RSDET_PDCPA_ID,
                    ctb.RSDET_PDCPA_cod,
                    ctb.RSDET_PDCPA_des,):
            r[col] = row[col]
    
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
#                if n>0 and rb[ctb.RSDET_TIPRIGA] == "I" and rb[ctb.RSDET_ALIQ_ID] is None:
#                    rb[ctb.RSDET_ALIQ_ID] = self.aliqdef_id
#                    rb[ctb.RSDET_ALIQ_cod] = self.aliqdef_cod
#                    rb[ctb.RSDET_ALIQ_des] = self.aliqdef_des
    
    def _GridEdit_Dav__Init__(self):
        
        parent = self.FindWindowById(ctbw.ID_PANGRID_DAV)
        parent.SetSize((0,0))
        
        _STR = gl.GRID_VALUE_STRING
        _NUM = gl.GRID_VALUE_NUMBER+":4"
        _FLT = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_CHOICE+":1,0"
        
        cols = (\
            ( 30, (ctb.RSDET_NUMRIGA,   "Riga",                     _NUM, False)),
            ( 50, (ctb.RSDET_PDCPA_cod, "Cod.",                     _STR, False)),
            (190, (ctb.RSDET_PDCPA_des, "Sottoconto",               _STR, False)),
            (110, (ctb.RSDET_IMPDARE,   "Dare",                     _FLT, True )),
            (110, (ctb.RSDET_IMPAVERE,  "Avere",                    _FLT, True )),
            ( 35, (ctb.RSDET_SOLOCONT,  "SC",                       _CHK, True )),
            ( 35, (ctb.RSDET_ALIQ_cod,  "Cod.",                     _STR, True )),
            (120, (ctb.RSDET_ALIQ_des,  "Aliquota IVA",             _STR, True )),
            ( 35, (RSDIS_ISOMAGG,       "Omg",                      _CHK, False)),
            (110, (RSDIS_IMPONIB,       "Imponibile",               _FLT, False)),
            (110, (RSDIS_IMPOSTA,       "Imposta",                  _FLT, False)),
            (110, (RSDIS_INDEDUC,       "Indeducibile",             _FLT, False)),
            (110, (RSDIS_IMPORTO,       "Totale",                   _FLT, False)),
            ( 50, (RSDIS_pdciva_cod,    "Cod.",                     _STR, False)),
            (140, (RSDIS_pdciva_des,    "Sottoconto IVA",           _STR, False)),
            ( 50, (RSDIS_pdcind_cod,    "Cod.",                     _STR, False)),
            (140, (RSDIS_pdcind_des,    "S.conto IVA indeducibile", _STR, False)),
            (200, (ctb.RSDET_NOTE,      "Note",                     _STR, False)),
        )
        
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
                                 6,
                                 ctb.RSDET_ALIQ_ID,
                                 ctb.RSDET_ALIQ_cod,
                                 ctb.RSDET_ALIQ_des,
                                 AliqIvaDialog, refresh=True)
        links.append(lti)
        
        def SetPdcTipIva(lt, *args):
            lt.SetPdcTipCods(self._auto_cod_tippdc_pdciva)
        lta = lib.LinkTabPdcAttr(bt.TABNAME_PDC,
                                 13, #colonna cod.sottoconto iva
                                 RSDIS_pdciva_id,
                                 RSDIS_pdciva_cod,
                                 RSDIS_pdciva_des,
                                 PdcDialog, 
                                 refresh=True,
                                 oncreate=SetPdcTipIva)
        links.append(lta)
        
        def SetPdcTipIvaInd(lt, *args):
            lt.SetPdcTipCods(self._auto_cod_tippdc_pdciva+\
                             self._cfg_pdctipcp_cod)
        lta = lib.LinkTabPdcAttr(bt.TABNAME_PDC,
                                 15, #colonna cod.sottoconto iva indeduc.
                                 RSDIS_pdcind_id,
                                 RSDIS_pdcind_cod,
                                 RSDIS_pdcind_des,
                                 PdcDialog, 
                                 refresh=True,
                                 oncreate=SetPdcTipIvaInd)
        links.append(lta)
        
        TestValues = self._GridEdit_Dav_TestValues
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1, TestValues), )
        
        grid.SetData(self.regrsb, colmap, canedit, canins,\
                     links, afteredit, self._GridEdit_Dav_NewRow)
        grid.SetRowLabelSize(80)
        grid.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        
        def GetRowLabel(row):
            if row<len(self.regrsb) and self.regrsb[row][ctb.RSDET_TIPRIGA] == "O":
                return "Omaggi"
            return ContabPanelTipo_I_O._GridEdit_Dav_GetRowLabel(self, row)
        
        grid.SetRowDynLabel(GetRowLabel)
        grid.SetCellDynAttr(self._GridEdit_Dav_GetAttr)
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        grid.SetFitColumn(16) #note
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
                if self.regrsb[row][ctb.RSDET_TIPRIGA] in "IO":
                    def _NoCalcIva(*args):#_self=self, row=None):
                        self.regrsb[row][ctb.RSDET_RIGAPI] = 1-(self.regrsb[row][ctb.RSDET_RIGAPI] or 0)
                        self._grid_dav.ResetView()
                    if self.regrsb[row][ctb.RSDET_RIGAPI]:
                        nocalcDes = "Abilita"
                    else:
                        nocalcDes = "Disabilita"
                    nocalcDes += " calcolo IVA"
                    nocalcId = wx.NewId()
                    menu.Append(nocalcId, nocalcDes)
                    self.Bind(wx.EVT_MENU, _NoCalcIva, id=nocalcId)
                menu.Append(deleteId, "Elimina riga")
                self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
                xo, yo = event.GetPosition()
                self._grid_dav.PopupMenu(menu, (xo, yo))
                menu.Destroy()
                
            event.Skip()
        
        def _OnLeftClick(event, self=self):
            self._GridEdit_Dav_CheckBoxChanged(event.GetRow(), event.GetCol(), changeContent=True)
            event.Skip()
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if row >= 0 and self.status == ctb.STATUS_EDITING:
                MenuPopup(row, event)
        
        for event, func in (
            (gl.EVT_GRID_CELL_LEFT_CLICK,    _OnLeftClick),
            (gl.EVT_GRID_CELL_RIGHT_CLICK,   _OnRightClick),
            (gl.EVT_GRID_CMD_EDITOR_CREATED, self._GridEdit_Dav_OnEditorShown),
            (gl.EVT_GRID_CMD_EDITOR_SHOWN,   self._GridEdit_Dav_OnEditorShown),):
            grid.Bind(event, func)
        
        grid.Bind(wx.EVT_CHAR, self._GridEdit_Dav_OnChar)
        
        self._grid_dav = grid
    
    def _GridEdit_Dav_OnChar(self, event):
        if event.GetKeyCode() == 32:
            def Update(*args):
                self._GridEdit_Dav_CheckBoxChanged(self._grid_dav.GetGridCursorRow(),
                                                   self._grid_dav.GetGridCursorCol(),
                                                   changeContent=False)
            wx.CallAfter(Update)
        event.Skip()
    
    def _GridEdit_Dav_CheckBoxChanged(self, row, col, changeContent):
        if self.status == ctb.STATUS_EDITING and 1<=row<len(self.regrsb):
            r = self.regrsb[row]
            t = self._grid_dav.GetTable()
            rscol = t.rsColumns[col]
            change = False
            if rscol == ctb.RSDET_SOLOCONT and r[ctb.RSDET_TIPRIGA] in "CIO":
                #click su cella SC solo contab
                sc = (r[rscol] or 0)
                if changeContent:
                    sc = r[rscol] = 1-sc
                om = r[RSDIS_ISOMAGG] = 0
                if not sc:
                    r[RSDIS_IMPONIB] = 0
                    r[RSDIS_IMPOSTA] = 0
                    r[RSDIS_INDEDUC] = 0
                    r[RSDIS_IMPORTO] = 0
                change = True
            elif rscol == RSDIS_ISOMAGG and r[ctb.RSDET_TIPRIGA] in "IO" and not r[ctb.RSDET_SOLOCONT]:
                #click su cella Omg omaggi
                om = (r[rscol] or 0)
                if changeContent:
                    om = r[rscol] = 1-om
                sc = r[ctb.RSDET_SOLOCONT] or 0
                change = True
            if change:
                if sc:
                    r[ctb.RSDET_TIPRIGA] = "C"
                    r[ctb.RSDET_ALIQ_ID] = None
                    r[ctb.RSDET_ALIQ_cod] = None
                    r[ctb.RSDET_ALIQ_des] = None
                    r[RSDIS_IMPONIB] = None
                    r[RSDIS_IMPOSTA] = None
                    r[RSDIS_INDEDUC] = None
                    r[RSDIS_IMPORTO] = None
                else:
                    if om:
                        r[ctb.RSDET_TIPRIGA] = "O"
                        r[ctb.RSDET_IMPDARE] = None
                        r[ctb.RSDET_IMPAVERE] = None
                    else:
                        r[ctb.RSDET_TIPRIGA] = "I"
                self.UpdateDavFromIVA()
                self.CheckQuadraturaIVA_DA()
                self.UpdatePanelBody()
                self._grid_dav.ResetView()
                self.UpdateButtons()
    
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
                                             ctb.RSDET_ALIQ_des,
                                             RSDIS_pdciva_des,
                                             RSDIS_pdcind_des)
            if not readonly and rscol in (ctb.RSDET_ALIQ_cod,
                                          ctb.RSDET_ALIQ_des):
                readonly = (self.regrsb[row][ctb.RSDET_SOLOCONT] or 0)
            if not readonly and rscol in (ctb.RSDET_IMPDARE,
                                          ctb.RSDET_IMPAVERE,) and self.regrsb[row][RSDIS_ISOMAGG]:
                readonly = True 
            if rscol == RSDIS_ISOMAGG and self.regrsb[row][ctb.RSDET_TIPRIGA] == "C":
                readonly = True
        attr.SetReadOnly(readonly)
        
        rs = self.regrsb
        if col in (3,4) and row<len(rs):
            if rs[row][ctb.RSDET_TIPRIGA] in "CI" and not rs[row][ctb.RSDET_IMPDARE] and not rs[row][ctb.RSDET_IMPAVERE]:
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
        if rscol in (ctb.RSDET_ALIQ_cod,
                     ctb.RSDET_ALIQ_des,
                     RSDIS_IMPONIB,
                     RSDIS_pdciva_cod,
                     RSDIS_pdciva_des) and row<len(rs):
            if rs[row][ctb.RSDET_TIPRIGA] in "IO" and not rs[row][rscol]:
                bgcol = stdcolor.VALMISS_BACKGROUND
        if rscol in (RSDIS_IMPONIB, RSDIS_IMPOSTA, RSDIS_IMPORTO) and row<len(rs):
            if rs[row][ctb.RSDET_RIGAPI]:
                bgcol = stdcolor.NOCALC_BACKGROUND
        
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
        self.regrsb.append([nrig,                  #RSDET_NUMRIGA
                            "I",                   #RSDET_TIPRIGA
                            None,                  #RSDET_PDCPA_ID
                            None,                  #RSDET_PDCPA_cod
                            None,                  #RSDET_PDCPA_des
                            None,                  #RSDET_IMPDARE
                            None,                  #RSDET_IMPAVERE
                            self.aliqdef_id,       #RSDET_ALIQ_ID
                            self.aliqdef_cod,      #RSDET_ALIQ_cod
                            self.aliqdef_des,      #RSDET_ALIQ_des
                            None,                  #RSDET_ALIQ_TOT
                            None,                  #RSDET_NOTE
                            0,                     #RSDET_RIGAPI
                            0,                     #RSDET_SOLOCONT
                            0,                     #RSDIS_IMPONIB
                            0,                     #RSDIS_IMPOSTA
                            0,                     #RSDIS_INDEDUC
                            0,                     #RSDIS_IMPORTO
                            self._auto_pdciva_id,  #RSIVA_ID_PDCIVA
                            self._auto_pdciva_cod, #RSIVA_pdciva_cod
                            self._auto_pdciva_des, #RSIVA_pdciva_des
                            None,                  #RSIVA_pdcind_id
                            None,                  #RSIVA_pdcind_cod
                            None,                  #RSIVA_pdcind_des
                            None,                  #RSIVA_NOTE
                            0])                    #RSIVA_ISOMAGG
        return True               
    
    def _GridEdit_Dav_TestValues(self, row, gridcol, col, value):
        
        r = self.regrsb[row]
        
        if col == ctb.RSDET_IMPDARE:    #digitato dare, lo aggiorno e ann.avere
            r[ctb.RSDET_IMPDARE] = value
            r[ctb.RSDET_IMPAVERE] = None
            
        elif col == ctb.RSDET_IMPAVERE: #digitato avere, lo aggiorno e ann.dare
            r[ctb.RSDET_IMPDARE] = None
            r[ctb.RSDET_IMPAVERE] = value
            
        elif col == ctb.RSDET_NOTE:
            note = self.regrsb[row][col]
            if note[0:1] == "*":
                note = note[1:]
                for r in range(len(self.regrsb)):
                    self.regrsb[r][col] = note
        
        if col in (ctb.RSDET_IMPDARE,
                   ctb.RSDET_IMPAVERE,
                   ctb.RSDET_ALIQ_cod,
                   ctb.RSDET_PDCPA_cod,
                   RSDIS_pdciva_cod,
                   RSDIS_pdcind_cod,
                   RSDIS_IMPONIB,
                   RSDIS_IMPOSTA,
                   RSDIS_INDEDUC,
                   RSDIS_IMPORTO,):
            
            ppaid = r[ctb.RSDET_PDCPA_ID]
            if ppaid:
                row_from_end = len(self.regrsb)-row
                def Posiz(row_from_end, col):
                    def Posiz2(row, col):
                        self._grid_dav.SetGridCursor(len(self.regrsb)-row_from_end, col)
                        def SetFocus():
                            #setfocus sul grid non funge :(
                            #sull'ultimo dei suoi figli invece si (misteri gui)
                            list(self._grid_dav.GetChildren())[-1].SetFocus()
                        wx.CallAfter(SetFocus)
                    wx.CallAfter(Posiz2, row, col)
                wx.CallAfter(Posiz, row_from_end, gridcol)
            
            r = self.regrsb[row]
            
            id_aliq = r[ctb.RSDET_ALIQ_ID]
            nocalc = r[ctb.RSDET_RIGAPI]
            
            if col in (ctb.RSDET_IMPDARE,
                       ctb.RSDET_IMPAVERE,):
                imponib = (r[ctb.RSDET_IMPDARE] or 0)-(r[ctb.RSDET_IMPAVERE] or 0)
                if self._cfg_pasegno == "D":
                    imponib *= -1
            else:
                imponib = r[RSDIS_IMPONIB]
            
            imposta = r[RSDIS_IMPOSTA]
            indeduc = r[RSDIS_INDEDUC]
            ttivato = r[RSDIS_IMPORTO]
            isomagg = r[RSDIS_ISOMAGG] or 0
            
            def R(n):
                return round(n, bt.VALINT_DECIMALS)
            
            if col == ctb.RSDET_PDCPA_cod:
                
                id1,cod1,des1,id2,cod2,des2 = self.GetSottocontiIva(tipaliq=None)
                
                #sottoconto iva
                r[RSDIS_pdciva_id] = id1
                r[RSDIS_pdciva_cod] = cod1
                r[RSDIS_pdciva_des] = des1
                
                if self._cfg_regiva_tipo == "A":
                    #sottoconto iva indeducibile, se presente
                    if id2 is None:
                        for n, rsb in enumerate(self.regrsb):
                            if n>0 and rsb[ctb.RSDET_TIPRIGA] == 'I':
                                id2 =  rsb[ctb.RSDET_PDCPA_ID]
                                cod2 = rsb[ctb.RSDET_PDCPA_cod]
                                des2 = rsb[ctb.RSDET_PDCPA_des]
                    r[RSDIS_pdcind_id] = id2
                    r[RSDIS_pdcind_cod] = cod2
                    r[RSDIS_pdcind_des] = des2
                
            elif col == ctb.RSDET_ALIQ_cod:
                
                if not r[RSDIS_IMPONIB]:
                    #digitata aliquota ad imponibile vuoto, lo recupero dal dare/avere
                    imponib = (r[ctb.RSDET_IMPDARE] or 0)-(r[ctb.RSDET_IMPAVERE] or 0)
                    if self._cfg_pasegno == "D":
                        imponib *= -1
                
                if nocalc:
                    ttivato = R(imponib+imposta)
                else:
                    imponib, imposta, ttivato, indeduc =\
                           self.CalcolaIva_DaImponibile(id_aliq, imponib, indeduc)
                
            elif col in (ctb.RSDET_IMPDARE,
                         ctb.RSDET_IMPAVERE,
                         RSDIS_IMPONIB,):
                #digitato imponibile
                if nocalc:
                    ttivato = R(imponib+imposta+indeduc)
                else:
                    imponib, imposta, ttivato, indeduc =\
                           self.CalcolaIva_DaImponibile(id_aliq, imponib, indeduc)
                
            elif col == RSDIS_IMPOSTA:
                #digitata imposta
                if nocalc:
                    ttivato = R(imponib+imposta+indeduc)
                else:
                    digiva = value
                    imponib, imposta, ttivato, indeduc =\
                      self.CalcolaIva_DaImposta(id_aliq, value, indeduc)
                    if not imponib:
                        imponib = imposta = indeduc = ttivato = digiva = 0
                    value = digiva
                
            elif col == RSDIS_INDEDUC:
                #digitato parte indeducibile dell'imposta
                ttivato = R(imponib+imposta+indeduc)
                
            elif col == RSDIS_IMPORTO:
                #digitato tot.ivato
                if nocalc:
                    imposta = R(ttivato-imponib-indeduc)
                else:
                    imponib, imposta, ttivato, indeduc =\
                      self.CalcolaIva_DaIvato(id_aliq, value, indeduc)
                
            elif col == ctb.RSDET_ALIQ_cod:
                #modificata aliquota iva, ricalcolo tutto dall'imponibile
                #se il calcolo è disattivato lo riattivo
                imponib, imposta, ttivato, indeduc =\
                  self.CalcolaIVA(id_aliq,
                                  imponib = imponib,
                                  imposta = imposta,
                                  ivato = ttivato,
                                  indeduc = indeduc)
            
            if isomagg:
                ttivato -= imponib
            
            r[RSDIS_IMPONIB] = imponib
            r[RSDIS_IMPOSTA] = imposta
            r[RSDIS_INDEDUC] = indeduc
            r[RSDIS_IMPORTO] = ttivato
            
            if col in (RSDIS_IMPONIB,
                       RSDIS_IMPOSTA,
                       RSDIS_IMPORTO,) and r[ctb.RSDET_TIPRIGA] == "I":
                #digitato imponibile o imposta o totale, adeguo il dare/avere della riga = imponibile
                if imponib>=0:
                    r[ctb.RSDET_IMPDARE] = imponib
                    r[ctb.RSDET_IMPAVERE] = None
                else:
                    r[ctb.RSDET_IMPDARE] = None
                    r[ctb.RSDET_IMPAVERE] = abs(imponib)
                if self._cfg_pasegno == "D":
                    r[ctb.RSDET_IMPDARE], r[ctb.RSDET_IMPAVERE] = r[ctb.RSDET_IMPAVERE], r[ctb.RSDET_IMPDARE]
            
            self._grid_dav.ForceResetView()
            
            oldtot = self.totdoc
            self.UpdateTotIva()
            if self.totdoc != oldtot:
                self.ScadCalc()
                self.UpdatePanelScad()
            
            self.UpdateDavFromIVA()
            self.UpdatePanelDav()
        
        self._grid_dav.ForceResetView()
        self.UpdateTotDav()
        
        return True
    
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
          if(row.segno="D", if(row.tipriga="O",NULL,row.importo), NULL),
          if(row.segno="A", if(row.tipriga="O",NULL,row.importo), NULL), 
          row.id_aliqiva,
          iva.codice,
          iva.descriz,
          NULL,
          row.note, 
          row.ivaman, 
          row.solocont,
          if(row.tipriga IN ("I","O"), row.imponib, 0),
          if(row.tipriga IN ("I","O"), row.imposta, 0),
          if(row.tipriga IN ("I","O"), row.indeduc, 0),
          if(row.tipriga IN ("I","O"), row.imposta+IF(row.tipriga="I",row.imponib,0), 0),
          row.id_pdciva,
          pdi.codice,
          pdi.descriz,
          row.id_pdcind,
          pdn.codice,
          pdn.descriz,
          IF(row.tipriga='O',1,0)
          
     FROM %s AS row
     JOIN %s AS pdc ON row.id_pdcpa=pdc.id
LEFT JOIN %s AS iva ON row.id_aliqiva=iva.id
LEFT JOIN %s AS pdi ON row.id_pdciva=pdi.id
LEFT JOIN %s AS pdn ON row.id_pdcind=pdn.id
    WHERE row.id_reg=%%s and row.tipriga IN ('S','C','I','O','A')""" % (bt.TABNAME_CONTAB_B,
                                                                        bt.TABNAME_PDC,
                                                                        bt.TABNAME_ALIQIVA,
                                                                        bt.TABNAME_PDC,
                                                                        bt.TABNAME_PDC)
            self.db_curs.execute(cmd, idreg)
            rsb = self.db_curs.fetchall()
            
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
                    if not self.totdoc:
                        self.totdoc = -(r[ctb.RSDET_IMPAVERE] or 0)
                else:
                    self.totdoc = r[ctb.RSDET_IMPAVERE]
                    if not self.totdoc:
                        self.totdoc = -(r[ctb.RSDET_IMPDARE] or 0)
            
            if hasattr(self, '_griddav'):
                self._grid_dav.SetGridCursorNewRowCol()
        
        return out

    def RegWriteBody(self, addRows=None):
        """
        Scrittura dettaglio registrazione su db.
        """
        out = False
        self.TestPagImm()
        rows = []
        rsb = self.regrsb
        rmax = 0
        for n in range(len(rsb)):
            if rsb[n][ctb.RSDET_IMPDARE] > 0:
                impdav = rsb[n][ctb.RSDET_IMPDARE]
                segno = "D"
            else:
                impdav = rsb[n][ctb.RSDET_IMPAVERE]
                segno = "A"
            regid = self.reg_id
            numriga =  rsb[n][ctb.RSDET_NUMRIGA]
            tipriga =  rsb[n][ctb.RSDET_TIPRIGA]
            pdcpaid =  rsb[n][ctb.RSDET_PDCPA_ID]
            pdccpid =  rsb[n][ctb.RSDET_PDCPA_ID]
            note =     rsb[n][ctb.RSDET_NOTE]
            davscorp = rsb[n][ctb.RSDET_ALIQ_TOT]
            solocont = rsb[n][ctb.RSDET_SOLOCONT]
            ivaman =   rsb[n][ctb.RSDET_RIGAPI]
            if rsb[n][ctb.RSDET_TIPRIGA] in "IO":
                imponib =  rsb[n][RSDIS_IMPONIB]
                imposta =  rsb[n][RSDIS_IMPOSTA]
                indeduc =  rsb[n][RSDIS_INDEDUC]
                pdciva =   rsb[n][RSDIS_pdciva_id]
                pdcind =   rsb[n][RSDIS_pdcind_id]
            else:
                imponib = None
                imposta = None
                indeduc = None
                pdciva =  None
                pdcind =  None
            #riga c/partita
            pdccpid = None
            if n == 0:
                #c/p della prima riga
                for r in rsb[1:]:
                    if r[ctb.RSDET_TIPRIGA] != "A":
                        pdccpid = r[ctb.RSDET_PDCPA_ID]
                        break
                aliqivaid = None
            else:
                #c/p delle righe oltre la prima
                if pdcpaid == rsb[0][ctb.RSDET_PDCPA_ID]:
                    #pdc=pdc prima riga (pag.imm?)
                    if n<(len(self.regrsb)-1):
                        #c/p = pdc della riga successiva
                        pdccpid = rsb[n+1][ctb.RSDET_PDCPA_ID]
                else:
                    #pdc della prima riga
                    pdccpid = rsb[0][ctb.RSDET_PDCPA_ID]
                aliqivaid = rsb[n][ctb.RSDET_ALIQ_ID]
            if pdccpid is None: 
                pdccpid = self.id_pdcpa
            rows.append((regid,     #id_reg
                         numriga,   #numriga
                         tipriga,   #tipriga
                         imponib,   #imponib
                         imposta,   #imposta
                         impdav,    #importo
                         indeduc,   #indeduc
                         ivaman,    #ivaman
                         segno,     #segno
                         aliqivaid, #id_aliqiva
                         davscorp,  #davscorp
                         solocont,  #solocont
                         pdcpaid,   #id_pdcpa
                         pdccpid,   #id_pdccp
                         pdciva,    #id_pdciva
                         pdcind,    #id_pdcind
                         note))     #note
            #rmax += 1
            rmax = max(rmax, rsb[n][ctb.RSDET_NUMRIGA])
        
        if addRows is not None:
            #se dalle sottoclassi arriva la chiamata con righe aggiuntive da
            #memorizzare, esse vengono aggiunte in coda alle righe contabili
            #presenti
            for n in range(len(addRows)):
                rmax += 1
                addRows[n][0] = self.reg_id
                addRows[n][1] = rmax
                rows.append(addRows[n])
        
        try:
            cmd =\
"""DELETE FROM %s WHERE id_reg=%%s""" % bt.TABNAME_CONTAB_B
            self.db_curs.execute(cmd, self.reg_id)
            cmd =\
"""INSERT INTO %s ("""\
"""id_reg, numriga, tipriga, imponib, imposta, importo, indeduc, ivaman, segno, """\
"""id_aliqiva, davscorp, solocont, id_pdcpa, id_pdccp, id_pdciva, id_pdcind, note) """\
"""VALUES (%s)""" % ( bt.TABNAME_CONTAB_B,\
                      (r"%s, " * 17)[:-2] )
            self.db_curs.executemany(cmd, rows)
            out = True
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        return out


# ------------------------------------------------------------------------------


class ContabFrameTipo_I_S(ctb.ContabFrame):
    """
    Frame Dataentry registrazioni iva per contabilità semplif.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabFrame.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_I_S(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ContabDialogTipo_I_S(ctb.ContabDialog):
    """
    Dialog Dataentry registrazioni iva per contabilità semplif.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabDialog.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_I_S(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        self.Layout()
        self.CenterOnScreen()
