#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry_c.py
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

import copy

import wx
import wx.grid as gl

import MySQLdb

from mx import DateTime

import Env
from Env import Azienda
bt = Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import contab.scad          as scad
import contab.dataentry     as ctb
import contab.dataentry_wdr as ctbw

import awc.controls.linktable as lt
from awc.controls.dbgrid import DbGrid

import awc.controls.dbgrid        as dbglib
import awc.controls.dbgrideditors as dbgred
import awc.controls.windows as aw

import awc
from awc.util import MsgDialog, MsgDialogDbError, GetNamedChildrens,\
                     DictNamedChildrens

from awc.tables.util import GetRecordInfo

import cfg.cfgautomat as auto
import cfg.cfgprogr as progr

from anag.pdc import PdcDialog
from anag.pdctip import PdcTipDialog

(GridSelectedEvent, EVT_GRIDSELECTED) = wx.lib.newevent.NewEvent()

from contab.dataentry_i import GeneraPartiteMixin, SelRowPa


FRAME_TITLE = "Registrazioni contabili"


class ContabPanelTipo_C(ctb.ContabPanel,
                        GeneraPartiteMixin):
    """
    Data entry di contabilità: registrazioni composte
    """
    
    def __init__(self, *args, **kwargs):
        
        self.totdoc = 0
        self.regrss = []       #recordset scadenze
        self.regrss_old = []   #recordset scadenze originale x storno modif.
        self._grid_sca = None
        
        ctb.ContabPanel.__init__(self, *args, **kwargs)
        GeneraPartiteMixin.__init__(self, self.db_curs)
        self.Bind(wx.EVT_BUTTON, self.OnParity, self.FindWindowByName('butparity'))
        
        self.SetName('regcompostapanel')
        self.HelpBuilder_SetDir('contab.dataentry.RegComposta')
    
    def InitCausale(self):
        """
        Inizializza il tipo di causale (C{"C"} o C{"S"} senza saldaconto)
        """
        self.cautipo = "C"
        self.caufilt = "tipo='C' or (tipo='S' and pcfscon != 1)"
        return ctb.ContabPanel.InitCausale(self)
    
    def RegReset(self):
        ctb.ContabPanel.RegReset(self)
        self.reg_modpag_id = None
        self.ScadReset()

    def DefaultValues(self):
        ctb.ContabPanel.DefaultValues(self)
        if self._cfg_pcf != '1':
            for pdcid in self._cfg_pdcpref:
                self._GridEdit_Dav_NewRow(pdcid)
            self._grid_dav.SetGridCursor(len(self.regrsb), 1)
    
    def EnableAllControls(self, enable = True):
        ctb.ContabPanel.EnableAllControls(self, enable)
        self.EnableScadControls(enable)
    
    def UpdateAllControls(self):
        ctb.ContabPanel.UpdateAllControls(self)
        self.controls["modpag"].SetValue(self.reg_modpag_id)
        self.UpdatePanelScad()

    def UpdateButtons(self, enable=True):
        ctb.ContabPanel.UpdateButtons(self, enable)
        self.UpdateScadButtons(enable)
    
    def GetSelRowPaClass(self):
        return SelRowPa
    
    def RegNew(self):
        if self.canins:
            if self._cfg_pcf == '1':
                dlgPa = self.GetSelRowPaClass()(self, -1)
                if self._cfg_id_pdcrow1:
                    dlgPa.id = self._cfg_id_pdcrow1
                    dlgPa.controls['pdcpa'].SetValue(self._cfg_id_pdcrow1)
                if dlgPa.ShowModal() > 0:
                    cn = lambda x: self.FindWindowByName(x)
                    ctb.ContabPanel.RegNew(self)
                    self.id_pdcpa = dlgPa.id
                    self.totdoc = dlgPa.doc
                    impd = dlgPa.doc; impa = None
                    if self._cfg_pasegno == "A": impd, impa = impa, impd
                    #crea riga partita
                    self.regrsb.append([1,         #RSDET_NUMRIGA
                                        "C",       #RSDET_TIPRIGA
                                        dlgPa.id,  #RSDET_PDCPA_ID
                                        dlgPa.cod, #RSDET_PDCPA_cod
                                        dlgPa.des, #RSDET_PDCPA_des
                                        impd,      #RSDET_IMPDARE
                                        impa,      #RSDET_IMPAVERE
                                        None,      #RSDET_ALIQ_ID
                                        None,      #RSDET_ALIQ_cod
                                        None,      #RSDET_ALIQ_des
                                        None,      #RSDET_ALIQ_TOT
                                        None,      #RSDET_NOTE
                                        0,         #RSDET_RIGAPI
                                        0])        #RSDET_SOLOCONT
                    nrig = 2
                    for cprow in dlgPa.rspref:
                        #crea righe c/partita da sottoconti preferiti
                        if cprow[0]:
                            self.regrsb.append([nrig,      #RSDET_NUMRIGA
                                                "C",       #RSDET_TIPRIGA
                                                cprow[1],  #RSDET_PDCPA_ID
                                                cprow[2],  #RSDET_PDCPA_cod
                                                cprow[3],  #RSDET_PDCPA_des
                                                None,      #RSDET_IMPDARE
                                                None,      #RSDET_IMPAVERE
                                                None,      #RSDET_ALIQ_ID
                                                None,      #RSDET_ALIQ_cod
                                                None,      #RSDET_ALIQ_des
                                                None,      #RSDET_ALIQ_TOT
                                                None,      #RSDET_NOTE
                                                0,         #RSDET_RIGAPI
                                                0])        #RSDET_SOLOCONT
                            self._cfg_pdcpref_da[cprow[1]] = cprow[4] #segno
                            nrig += 1
                    self.UpdateModPag()
                    self.UpdatePanelCliFor()
                    self.ReadProgr()
                    self.DefaultValues()
                    self.SetRegStatus(ctb.STATUS_EDITING)
                    
                else:
                    self.SetRegStatus(ctb.STATUS_SELCAUS)
                dlgPa.Destroy()
            else:
                ctb.ContabPanel.RegNew(self)
    
    def RegRead(self, *args):
        
        out = ctb.ContabPanel.RegRead(self, *args)
        
        #elimino righe giroc. cli/for-cassa x pag.immediato
        #vengono reinserite in fase di memorizzazione se occorre
        for r in range(len(self.regrsb)-1,0,-1):
            if self.regrsb[r][ctb.RSDET_RIGAPI]:
                self.regrsb.pop(r)
        try:
            n = awc.util.ListSearch(self.regrsb,\
                                    lambda x: x[ctb.RSDET_NUMRIGA] == 1)
        except:
            self.id_pdcpa = None
            self.totdoc = 0
        else:
            self.id_pdcpa = self.regrsb[n][ctb.RSDET_PDCPA_ID]
            if self._cfg_pasegno == "D":
                self.totdoc = self.regrsb[n][ctb.RSDET_IMPDARE]
            else:
                self.totdoc = self.regrsb[n][ctb.RSDET_IMPAVERE]
        if out:
            out = self.ScadRead(self.reg_id)
            self.SetupModPag(self.reg_modpag_id)
        if out:
            self.UpdatePanelCliFor()
        
        if self._cfg_tipo == 'S':
            row = 0
        else:
            row = len(self.regrsb)
        self._grid_dav.SetGridCursor(row, 1)
        
        return out
    
    def RegSave(self):
        """
        Scrittura registrazione su db.  Oltre alla scrittura della
        registrazione, provvede a scrviere le scadenze e ad aggiornare
        le partite clienti/fornitori.
        """
        out = ctb.ContabPanel.RegSave(self)
        if out and self._cfg_pcf == '1':
            out = self.ScadStorno()
            if out:
                out = self.ScadWrite()
        return out
    
    def RegDelete(self):
        out = self.ScadStorno()
        if out:
            out = ctb.ContabPanel.RegDelete(self)
        return out
    
    def RegWriteBody(self, *args):
        self.TestPagImm()
        return ctb.ContabPanel.RegWriteBody(self, *args)
    
    def UpdateModPag(self):
        """
        Aggiorna la modalità di pagamento in base al sottoconto della riga 1
        """
        GeneraPartiteMixin.UpdateModPag(self, totimposta=0)
    
    def InfoCliFor(self, col):
        """
        Recupera informazioni dalla tabella del cliente o fornitore
        """
        out = None
        cmd =\
"""SELECT cli.%s, frn.%s """\
"""FROM %s AS pdc """\
"""LEFT JOIN %s AS cli ON cli.id=pdc.id """\
"""LEFT JOIN %s AS frn ON frn.id=pdc.id """\
"""WHERE pdc.id=%%s;""" % ( col, 
                            col, 
                            bt.TABNAME_PDC,
                            bt.TABNAME_CLIENTI,
                            bt.TABNAME_FORNIT )
        
        try:
            self.db_curs.execute(cmd, self.id_pdcpa)
            rs = self.db_curs.fetchone()
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            if rs[0] is None:
                out = rs[1]
            else:
                out = rs[0]
        return out
    
    def InitPanelHead(self):
        ctb.ContabPanel.InitPanelHead(self)
        for cid, func in ((ctbw.ID_TXT_DATREG, self.OnDatRegChanged),
                          (ctbw.ID_TXT_DATDOC, self.OnDatDocChanged)):
            self.Bind(ctbw.EVT_DATECHANGED, func, id=cid)
        for cid, func in (#(ctbw.ID_TXT_NUMIVA, self.OnNumIvaChanged),
                          (ctbw.ID_TXT_NUMDOC, self.OnNumDocChanged),):
            self.Bind(wx.EVT_TEXT, func, id=cid)
        self.InitPanelScad()

    def OnDatRegChanged(self, event):
        if self.reg_id is None:
            if self.status == ctb.STATUS_EDITING:
                newdd = self.controls["datreg"].GetValue()
                if self.reg_datreg != newdd:
                    self.reg_datreg = newdd
                if self._cfg_datdoc == '1':
                    self.controls['datdoc'].SetValue(newdd)
                self.UpdateButtons()
        event.Skip()
    
    def OnDatDocChanged(self, event):
        newdd = self.controls["datdoc"].GetValue()
        if self.reg_datdoc != newdd:
            self.reg_datdoc = newdd
            self.ScadCalc()
            self.UpdatePanelScad()
            self.UpdatePanelBody()
        self.UpdateButtons()
        event.Skip()
    
    def InitPanelBody(self):
        ctb.ContabPanel.InitPanelBody(self)
        ctbw.BodyDavFunc(self.panbody, True)
        self.InitPdcControls()
        self.InitGridDav()
        return self

    def Validate(self):
        out = ctb.ContabPanel.Validate(self)
        if out:
            self.reg_modpag_id = self.controls["modpag"].GetValue()
        return out
    
    def InitGridDav(self):
        parent = self.FindWindowById(ctbw.ID_PANGRID_DAV)
        parent.SetSize((0,0))
        size = parent.GetClientSizeTuple()
        _NUM = gl.GRID_VALUE_NUMBER+":4"
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (( 40, (ctb.RSDET_NUMRIGA,   "Riga",       _NUM, False)),
                ( 50, (ctb.RSDET_PDCPA_cod, "Cod.",       _STR, False)),
                (220, (ctb.RSDET_PDCPA_des, "Sottoconto", _STR, False)),
                (130, (ctb.RSDET_IMPDARE,   "Dare",       _IMP, True )),
                (130, (ctb.RSDET_IMPAVERE,  "Avere",      _IMP, True )),
                (200, (ctb.RSDET_NOTE,      "Note",       _STR, False)),)                                                  
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        grid = dbglib.DbGrid(parent, -1, size=size, style=wx.SUNKEN_BORDER)
        grid.SetColMaxChar(ctb.RSDET_NOTE, bt.getStdNoteWidth())
        
        canedit = self.canedit
        canins = self.canins
        
        links = []
        from anag.lib import LinkTabPdcAttr
        lta = LinkTabPdcAttr(bt.TABNAME_PDC,
                             1,
                             ctb.RSDET_PDCPA_ID,
                             ctb.RSDET_PDCPA_cod,
                             ctb.RSDET_PDCPA_des,
                             PdcDialog, refresh=True)
        links.append(lta)
        
        TestValues = self._GridEdit_Dav_TestValues
        NewRow = self._GridEdit_Dav_NewRow
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1, TestValues), )
        
        grid.SetData( self.regrsb, colmap, canedit, canins,\
                      links, afteredit, NewRow )
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        grid.SetAnchorColumns(4, 2)
        grid.SetFitColumn(5)
        grid.AutoSizeColumns()
        
        grid.SetRowLabelSize(80)
        grid.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        grid.SetRowDynLabel(self._GridEdit_Dav_GetRowLabel)
        grid.SetCellDynAttr(self._GridEdit_Dav_GetAttr)
        grid.SetColDefault(1)
        
        def MoveColumnAfterEdit(grid, row, col):
            if col == 1:
                if row == 0:
                    if self._cfg_pasegno == "D":
                        col = 3
                    elif self._cfg_pasegno == "A":
                        col = 4
                if row == 1:
                    if self._cfg_pasegno == "D":
                        col = 4
                    elif self._cfg_pasegno == "A":
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
                    self._grid_dav.DeleteRows(row)
                    self.UpdateTotDav()
                
                self._grid_dav.SelectRow(row)
                deleteId = wx.NewId()
                menu = wx.Menu()
                menu.Append(deleteId, "Elimina riga")
                self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
                xo, yo = event.GetPosition()
                self._grid_dav.PopupMenu(menu, (xo, yo))
                menu.Destroy()
                
            event.Skip()
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if row >= 0 and self.status == ctb.STATUS_EDITING:
                MenuPopup(row, event)
        
        grid.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK,   _OnRightClick)
        grid.Bind(gl.EVT_GRID_CMD_EDITOR_CREATED, self._GridEdit_Dav_OnEditorShown)
        grid.Bind(gl.EVT_GRID_CMD_EDITOR_SHOWN,   self._GridEdit_Dav_OnEditorShown)
        
        self._grid_dav = grid
    
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
    
    def _GridEdit_Dav_GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        try:
            tiprig = self.regrsb[row][ctb.RSDET_TIPRIGA]
        except IndexError:
            tiprig = ""
        #blocco editazione su celle diverse da sottoconto, dare,avere, note
        if row == 0 and self._cfg_pcf == '1':
            readonly = col != ctb.RSDET_NOTE
        elif row == 0 and col in (3,4) and not (self._cfg_camsegr1 or 0):
            s = self._cfg_pasegno
            readonly = col == 3 and s == "A" or col == 4 and s == "D"
        else:
            readonly = not rscol in (ctb.RSDET_PDCPA_ID,\
                                     ctb.RSDET_PDCPA_cod,\
                                     ctb.RSDET_IMPDARE,\
                                     ctb.RSDET_IMPAVERE,\
                                     ctb.RSDET_NOTE)
            
        attr.SetReadOnly(readonly)
        
        #impostazione colori
        fgcol = stdcolor.NORMAL_FOREGROUND
        bgcol = stdcolor.NORMAL_BACKGROUND
        
        rs = self.regrsb
        if col in (3,4) and row<len(rs):
            miss = False
            if row == 0 and (self._cfg_pasegno or ' ') in 'DA':
                s = self._cfg_pasegno
                miss = (col == 3 and s == "D" or col == 4 and s == "A")
            else:
                if self._cfg_pdcpref:
                    pdcid = rs[row][ctb.RSDET_PDCPA_ID]
                    if pdcid in self._cfg_pdcpref_da:
                        s = self._cfg_pdcpref_da[pdcid]
                        if s is not None:
                            if s in 'DA':
                                miss = (col == 3 and s == "D" or col == 4 and s == "A")
                else:
                    if (self._cfg_pasegno or ' ') in 'DA':
                        s = "DA"[1-"DA".index(self._cfg_pasegno)]
                        miss = (col == 3 and s == "D" or col == 4 and s == "A")
            if miss:
                bgcol = stdcolor.VALMISS_BACKGROUND
        
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        
        return attr

    def _GridEdit_Dav_GetRowLabel(self, row):
        label = ""
        if row == 0:
            label = self._cfg_pades
        elif row == 1:
            label = self._cfg_cpdes
        else:
            label = ""
        return label
    
    def _GridEdit_Dav_NewRow(self, pdcid=None, impd=None, impa=None):
        pdccod = pdcdes = None
        if pdcid:
            pdccod, pdcdes = GetRecordInfo(self.db_curs, bt.TABNAME_PDC, pdcid,
                                           'codice,descriz'.split(','))
        nrig = len(self.regrsb)+1
        self.regrsb.append([nrig,   #RSDET_NUMRIGA
                            "C",    #RSDET_TIPRIGA
                            pdcid,  #RSDET_PDCPA_ID
                            pdccod, #RSDET_PDCPA_cod
                            pdcdes, #RSDET_PDCPA_des
                            impd,   #RSDET_IMPDARE
                            impa,   #RSDET_IMPAVERE
                            None,   #RSDET_ALIQ_ID
                            None,   #RSDET_ALIQ_cod
                            None,   #RSDET_ALIQ_des
                            None,   #RSDET_ALIQ_TOT
                            None,   #RSDET_NOTE
                            0,      #RSDET_RIGAPI
                            0])     #RSDET_SOLOCONT
        self._GridEdit_Dav_TestSemplice(0)
        return True

    def _GridEdit_Dav_TestValues(self, row, gridcol, col, value):
        
        if col == ctb.RSDET_NOTE:
            note = self.regrsb[row][col]
            if note[0:1] == "*":
                note = note[1:]
                for r in range(len(self.regrsb)):
                    self.regrsb[r][col] = note
        
        if 3 <= gridcol <= 4:
            if gridcol == 3:
                self.regrsb[row][ctb.RSDET_IMPDARE] = value
                self.regrsb[row][ctb.RSDET_IMPAVERE] = None
            else:
                self.regrsb[row][ctb.RSDET_IMPDARE] = None
                self.regrsb[row][ctb.RSDET_IMPAVERE] = value
        
        if self._cfg_tipo in "SC":
            self._GridEdit_Dav_TestSemplice(row, col)
        
        cd, ca = ctb.RSDET_IMPDARE, ctb.RSDET_IMPAVERE
        if self.regrsb[row][cd]:
            self.regrsb[row][ca] = None
        elif self.regrsb[row][ca]:
            self.regrsb[row][cd] = None
        
        self._grid_dav.ForceResetView()
        self.UpdateTotDav()
        
        return True
    
    def _GridEdit_Dav_TestSemplice(self, row, col=None):
        """
        Testa la presenza di due sole righe nella registrazione, nel qual caso
        provvede a mettere sull'altra riga lo stesso importo con segno contabile
        opposto.
        """
        if len(self.regrsb) == 2 and self._cfg_tipo == 'S':
            cd, ca = ctb.RSDET_IMPDARE, ctb.RSDET_IMPAVERE
            if col is None:
                if self.regrsb[row][cd]:
                    col = cd
                else:
                    col = ca
            if col == cd:
                self.regrsb[row][ca] = None
                self.regrsb[1-row][ca] = self.regrsb[row][cd]
                self.regrsb[1-row][cd] = None
            elif col == ca:
                self.regrsb[row][cd] = None
                self.regrsb[1-row][cd] = self.regrsb[row][ca]
                self.regrsb[1-row][ca] = None
            return True
        return False
    
    def RegSearchClass( self ):
        """
        Indica la classe da utilizzare per il dialog di ricerca delle
        registrazioni.
        """
        return Reg_C_SearchDialog


# ---------------------------------------------------------------------------


def AdaptGridHeight(g, h=240):
    s = g.GetSize()
    s = [s[0], max(h, s[1])]


# ------------------------------------------------------------------------------


class ContabFrameTipo_C(ctb.ContabFrame):
    """
    Frame Dataentry registrazioni composte.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabFrame.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_C(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        AdaptGridHeight(self.dataentrypanel._grid_dav)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ContabDialogTipo_C(ctb.ContabDialog):
    """
    Dialog Dataentry registrazioni composte.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabDialog.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_C(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        AdaptGridHeight(self.dataentrypanel._grid_dav)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class Reg_C_SearchGrid(ctb.RegSearchGrid):
    
    def DefColumns(self):
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        return (( 80, ( 1, "Data reg.",  _DAT, False)),
                (200, ( 2, "Sottoconto", _STR, False)),
                ( 80, ( 3, "N.Doc.",     _STR, True )),
                ( 80, ( 4, "Data doc.",  _DAT, True )),
                (110, ( 5, "Dare",       _IMP, True )),
                (110, ( 6, "Avere",      _IMP, True )),
                (  1, ( 0, "#reg",       _STR, False)))
    
    def GetColumn2Fit(self):
        return 1


# ------------------------------------------------------------------------------


class Reg_C_SearchPanel(ctb.RegSearchPanel):
    
    wdrFiller = ctbw.RegSearchFuncTipo_I
    GridClass = Reg_C_SearchGrid


# ------------------------------------------------------------------------------


class Reg_C_SearchDialog(ctb.RegSearchDialog):
    """
    Ricerca registrazioni.
    Dialog per la ricerca di registrazioni della causale selezionata.
    """
    
    panelClass = Reg_C_SearchPanel
