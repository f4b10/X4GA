#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/dataentry_sc.py
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
from anag.util import GetPdcDialogClass
bt = Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import contab.scad          as scad
import contab.dataentry     as ctb
import contab.dataentry_wdr as wdr

import pcf

import awc.controls.linktable as lt
from awc.controls.dbgrid import DbGrid

import awc.controls.dbgrid as dbglib
import awc.controls.dbgrideditors as dbgred

import awc
import awc.controls.windows as aw

import awc.util as awu

from awc.util import MsgDialog, MsgDialogDbError, GetNamedChildrens,\
                     DictNamedChildrens

from awc.tables.util import GetRecordInfo

import cfg.cfgautomat as auto
import cfg.cfgprogr as progr

import anag
import anag.lib as lib
import anag.util as autil
from anag.pdc import PdcDialog
from anag.pdctip import PdcTipDialog

from contab.util import SetWarningPag

import stormdb as adb


(GridSelectedEvent, EVT_GRIDSELECTED) = wx.lib.newevent.NewEvent()


FRAME_TITLE = "Registrazione incassi e pagamenti"


#costanti per accesso a recordset partite del cli/for
RSPCF_ID =          0
RSPCF_DATSCA =      1
RSPCF_DATDOC =      2
RSPCF_NUMDOC =      3
RSPCF_CAUS_ID =     4
RSPCF_CAUS_COD =    5
RSPCF_CAUS_DES =    6
RSPCF_MPAG_ID =     7
RSPCF_MPAG_COD =    8
RSPCF_MPAG_DES =    9
RSPCF_ISRIBA =     10
RSPCF_ISINSOL =    11
RSPCF_IMPTOT =     12
RSPCF_IMPPAR =     13
RSPCF_IMPSALDO =   14
RSPCF_NOTE =       15


#costanti per recordset scadenze
RSSCA_PCF_ID =      0
RSSCA_DATSCA =      1
RSSCA_DATDOC =      2
RSSCA_NUMDOC =      3
RSSCA_CAUS_ID =     4
RSSCA_CAUS_COD =    5
RSSCA_CAUS_DES =    6
RSSCA_MPAG_ID =     7
RSSCA_MPAG_COD =    8
RSSCA_MPAG_DES =    9
RSSCA_ISRIBA =     10
RSSCA_ISINSOL =    11
RSSCA_IMPORTO =    12
RSSCA_ABBUONO =    13
RSSCA_SPESA =      14
RSSCA_NOTE =       15
RSSCA_TIPABB =     16
RSSCA_IMPTOT =     17
RSSCA_IMPPAR =     18
RSSCA_IMPSALDO =   19


class DavGrid(dbglib.DbGrid):
    
    def __init__(self, parent, regrsb, owner):
        
        _STR = gl.GRID_VALUE_STRING
        _NUM = gl.GRID_VALUE_NUMBER+":4"
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (( 40, (ctb.RSDET_NUMRIGA,   "Riga",       _NUM, False)),
                ( 50, (ctb.RSDET_PDCPA_cod, "Cod.",       _STR, False)),
                (200, (ctb.RSDET_PDCPA_des, "Sottoconto", _STR, False)),
                (110, (ctb.RSDET_IMPDARE,   "Dare",       _IMP, True )),
                (110, (ctb.RSDET_IMPAVERE,  "Avere",      _IMP, True )),
                (200, (ctb.RSDET_NOTE,      "Note",       _STR, False)),)
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        parent.SetSize((0,0))
        size = parent.GetClientSizeTuple()
        dbglib.DbGrid.__init__(self, parent, -1, size=size)
        self.SetColMaxChar(ctb.RSDET_NOTE, bt.getStdNoteWidth())
        self.regrsb = regrsb
        self.owner = owner
        
        canedit = True#self.canedit
        canins = True#self.canins
        
        links = []
        from anag.lib import LinkTabPdcAttr
        lta = LinkTabPdcAttr(bt.TABNAME_PDC,
                             1,
                             ctb.RSDET_PDCPA_ID,
                             ctb.RSDET_PDCPA_cod,
                             ctb.RSDET_PDCPA_des,
                             PdcDialog, refresh=True)
        links.append(lta)
        
        self.SetDefaultValueCB(self.GetDefaultValue)
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1, self.TestValues), )
        
        self.SetData(self.regrsb, colmap, canedit, canins,\
                      links, afteredit, self.NewRow)
        self.SetRowLabelSize(80)
        self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        self.SetRowDynLabel(self.GetRowLabel)
        self._bgcol = Env.Azienda.Colours.GetColour('lightgray')
        self.SetCellDynAttr(self.GetAttr)
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
#        self.SetAnchorColumns(4, 2)
        self.SetFitColumn(5)
        self.AutoSizeColumns()
        self.SetColDefault(1)
        
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        def MenuPopup(row, event):
            if row > 1 and row < len(self.regrsb)\
               and self.regrsb[row][ctb.RSDET_TIPRIGA] != "A"\
               and self.owner.status == ctb.STATUS_EDITING:
                    
                def _DeleteRow(*args):
                    self.DeleteRows(row)
                    self.UpdateDav()
                    self.owner.UpdateTotDav()
                
                self.SelectRow(row)
                deleteId = wx.NewId()
                menu = wx.Menu()
                menu.Append(deleteId, "Elimina riga")
                self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
                xo, yo = event.GetPosition()
                self.PopupMenu(menu, (xo, yo))
                menu.Destroy()
                
            event.Skip()
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if row >= 0 and self.owner.status == ctb.STATUS_EDITING:
                MenuPopup(row, event)
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK,   _OnRightClick)
    
    def GetDefaultValue(self, row, col, editor):
        out = None
        o = self.owner
        if col == 1 and row >= 2: #colonna codice sottoconto, no prime 2 righe
            if len(o._cfg_pdcpref) >= row:
                out = o._cfg_pdcpref[row-1]
                #questo serve x azzerare il valore di partenza memorizzato
                #nell'editor della cella, altrimenti l'uscita dalla cella
                #mantenendo il sottoconto qui inizializzato senza modifica
                #fa in modo che l'editor interpreti erroneamente la cosa come
                #valore non modificato e non prosegue nella memorizzazione
                #della riga
                def ResetStartValue(*args):
                    editor.startValue = None
                    #imposto il tipo anagrafico di filtro del sottoconto
                    #uguale a quello del sottoconto qui inizializzato
                    id_tipo = GetRecordInfo(
                        o.db_curs, bt.TABNAME_PDC, out, ('id_tipo',))[0]
                    editor._tc.SetFilterValue(id_tipo)
                wx.CallAfter(ResetStartValue)
        return out
    
    def GetAttr(self, row, col, rscol, attr):
        if len(self.regrsb) == 0 or\
           (not self.regrsb[0][ctb.RSDET_IMPDARE] and\
            not self.regrsb[0][ctb.RSDET_IMPAVERE]):
            readonly = True
        else:
            if row == 1 and rscol == ctb.RSDET_PDCPA_cod:
                readonly = False
            elif 0 <= row < len(self.regrsb):
                r = self.regrsb[row]
                if r[ctb.RSDET_TIPRIGA] == "A" and rscol == ctb.RSDET_PDCPA_cod and r[ctb.RSDET_RIGAPI] == 1:
                    readonly = False
                else:
                    readonly = (row <= 1 or r[ctb.RSDET_TIPRIGA] in "AS")\
                             and rscol != ctb.RSDET_NOTE
            else:
                readonly = rscol != ctb.RSDET_PDCPA_cod
        attr.SetReadOnly(readonly)
        if readonly and row<len(self.regrsb):
            bgcol = self._bgcol
        else:
            bgcol = stdcolor.NORMAL_BACKGROUND
        attr.SetBackgroundColour(bgcol)
        return attr
    
    def NewRow(self):
        pdc_id = None
        row = len(self.regrsb)
        nrig = row+1
        if row >= 2: #per le righe successive alle prime 2, cerco pdc preferito
            if len(self.owner._cfg_pdcpref) >= row:
                pdc_id = self.owner._cfg_pdcpref[row-1]
        self.regrsb.append([nrig,   #RSDET_NUMRIGA
                            "C",    #RSDET_TIPRIGA
                            pdc_id, #RSDET_PDCPA_ID
                            None,   #RSDET_PDCPA_cod
                            None,   #RSDET_PDCPA_des
                            None,   #RSDET_IMPDARE
                            None,   #RSDET_IMPAVERE
                            None,   #RSDET_ALIQ_ID
                            None,   #RSDET_ALIQ_cod
                            None,   #RSDET_ALIQ_des
                            None,   #RSDET_ALIQ_TOT
                            None,   #RSDET_NOTE
                            0,      #RSDET_RIGAPI
                            None])  #RSDET_SOLOCONT

    def TestValues(self, row, gridcol, col, value):
        if col == ctb.RSDET_IMPDARE:           #digitato dare, annullo avere
            self.regrsb[row][ctb.RSDET_IMPAVERE] = None
            
        elif col == ctb.RSDET_IMPAVERE:        #digitato avere, annullo dare
            self.regrsb[row][ctb.RSDET_IMPDARE] = None
            
        elif col == ctb.RSDET_NOTE:
            note = self.regrsb[row][col]
            if note[0:1] == "*":
                note = note[1:]
                for r in range(len(self.regrsb)):
                    self.regrsb[r][col] = note
        
        self.UpdateDav()
        self.owner.UpdatePanelDav(sizeDavCols=False)
        
        return True

    def GetRowLabel(self, row):
        if len(self.regrsb) == 0:
            label = ''
        elif row == 0:
            label = self.owner._cfg_pades
        elif row == 1:
            label = self.owner._cfg_cpdes
        else:
            label = 'Altro'
        if label is None: label = ''
        return label
    
    def UpdateDav(self):
        
        #determino totale importi, abbuoni e spese
        o = self.owner
        timp = tabb = tspe = 0
        for sca in o.regrss:
            imp = sca[RSSCA_IMPORTO] or 0
            abb = sca[RSSCA_ABBUONO] or 0
            spe = sca[RSSCA_SPESA] or 0
            try:
                if o._cfg_pasegno+sca[RSSCA_TIPABB] in ("AA", "DP"):
                    abb = -abb
            except TypeError:
                pass
            timp += imp
            tabb += abb
            tspe += spe
        col1, col2 = ctb.RSDET_IMPDARE, ctb.RSDET_IMPAVERE
        if o._cfg_pasegno == "A":
            col1, col2 = col2, col1
        
        #riga cli/for
        self.regrsb[0][col1] = timp
        self.regrsb[0][col2] = None
        
        #riga cassa/banca
        self.regrsb[1][col1] = None
        self.regrsb[1][col2] = timp-tabb
        
        #gestione riga abbuono
        try:
            nabb = awc.util.ListSearch(self.regrsb, lambda x: 
                                       x[ctb.RSDET_TIPRIGA] == 'A' and 
                                       x[ctb.RSDET_PDCPA_ID] in (o._auto_abbatt_id,
                                                                 o._auto_abbpas_id))
        except:
            if tabb:
                self.NewRow()
                nabb = len(self.regrsb)-1
            else:
                nabb = None
        #attribuzione tipologia e importo su riga abbuoni
        if nabb is not None:
            if tabb:
                if tabb>0 and o._cfg_pasegno == "A" or\
                   tabb<0 and o._cfg_pasegno == "D":
                    abbid =  o._auto_abbpas_id
                    abbcod = o._auto_abbpas_cod
                    abbdes = o._auto_abbpas_des
                else:
                    abbid =  o._auto_abbatt_id
                    abbcod = o._auto_abbatt_cod
                    abbdes = o._auto_abbatt_des
                cola1, cola2 = col1, col2
                if self.regrsb[1][col2] < self.regrsb[0][col1]:
                    cola1, cola2 = cola2, cola1
                self.regrsb[nabb][ctb.RSDET_PDCPA_ID] =  abbid
                self.regrsb[nabb][ctb.RSDET_PDCPA_cod] = abbcod
                self.regrsb[nabb][ctb.RSDET_PDCPA_des] = abbdes
                self.regrsb[nabb][cola1] = abs(tabb)
                self.regrsb[nabb][cola2] = None
                self.regrsb[nabb][ctb.RSDET_TIPRIGA] = "A"
            else:
                del self.regrsb[nabb]
        
        #gestione riga spese
        try:
            nspe = awc.util.ListSearch(self.regrsb, lambda x: x[ctb.RSDET_RIGAPI] == 1)
        except:
            if tspe:
                self.NewRow()
                nspe = len(self.regrsb)-1
            else:
                nspe = None
        #attribuzione importo su riga spese
        if nspe is not None:
            if tspe:
                if self.regrsb[nspe][ctb.RSDET_PDCPA_ID] is None:
                    self.regrsb[nspe][ctb.RSDET_PDCPA_ID] =  o._auto_speinc_id
                    self.regrsb[nspe][ctb.RSDET_PDCPA_cod] = o._auto_speinc_cod
                    self.regrsb[nspe][ctb.RSDET_PDCPA_des] = o._auto_speinc_des
                cols1, cols2 = col1, col2
                if o._cfg_pasegno == "A":
                    cols1, cols2 = cols2, cols1
                self.regrsb[nspe][cols1] = abs(tspe)
                self.regrsb[nspe][cols2] = None
                self.regrsb[nspe][ctb.RSDET_TIPRIGA] = "A"
                self.regrsb[nspe][ctb.RSDET_RIGAPI] = 1
                td = ta = 0
                for nr,rig in enumerate(self.regrsb):
                    if rig != nspe:
                        td += rig[ctb.RSDET_IMPDARE] or 0
                        ta += rig[ctb.RSDET_IMPAVERE] or 0
                if abs(td-ta)>0.000001:
                    rsc = self.regrsb[1]
                    if rsc[ctb.RSDET_IMPDARE]:
                        if rsc[ctb.RSDET_IMPDARE]<tspe:
                            rsc[ctb.RSDET_IMPAVERE] = tspe-rsc[ctb.RSDET_IMPDARE]
                            rsc[ctb.RSDET_IMPDARE] = None
                        else:
                            rsc[ctb.RSDET_IMPDARE] -= tspe
                    else:
                        if rsc[ctb.RSDET_IMPAVERE]<tspe:
                            rsc[ctb.RSDET_IMPDARE] = tspe-rsc[ctb.RSDET_IMPAVERE]
                            rsc[ctb.RSDET_IMPAVERE] = None
                        else:
                            rsc[ctb.RSDET_IMPAVERE] += tspe
            else:
                del self.regrsb[nspe]
        
        #totalizzazione righe contabili aggiunte manualmente
        td = ta = 0
        for nr,rig in enumerate(self.regrsb):
            if nr > 1 and rig[ctb.RSDET_TIPRIGA] != "A":
                td += rig[ctb.RSDET_IMPDARE] or 0
                ta += rig[ctb.RSDET_IMPAVERE] or 0
        
        #adeguamento importo riga cassa/banca
        if td >= ta:
            imp = td-ta
            sgn = "D"
        else:
            imp = ta-td
            sgn = "A"
        if o._cfg_pasegno != sgn: imp *= -1
        self.regrsb[1][col2] = (self.regrsb[1][col2] or 0) + imp
        
        #verifico righe negative, se le trovo 
        #metto valore assoluto e inverto segno contabile
        for r in self.regrsb:
            if (r[ctb.RSDET_IMPDARE] or 0) < 0:
                r[ctb.RSDET_IMPAVERE] = abs(r[ctb.RSDET_IMPDARE])
                r[ctb.RSDET_IMPDARE] = None
            elif (r[ctb.RSDET_IMPAVERE] or 0) < 0:
                r[ctb.RSDET_IMPDARE] = abs(r[ctb.RSDET_IMPAVERE])
                r[ctb.RSDET_IMPAVERE] = None
        self.owner._grid_dav.SetGridCursorNewRowCol()


# ------------------------------------------------------------------------------


class ScaGrid(dbglib.DbGrid):
    def __init__(self, parent, regrss, owner):
        """
        Inizializza il grid delle scadenze dell'incasso/pagamento.
        """
        parent.SetSize((0,0))
        self.pansca = parent
        size = parent.GetClientSizeTuple()
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        _ABB = bt.GetValIntMaskInfo(numint=8)
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        
        cols = (( 80, (RSSCA_DATSCA,     "Data scad.",   _DAT, False)),
                (110, (RSSCA_IMPORTO,    "Importo",      _IMP, True )),
                (110, (RSSCA_ABBUONO,    "Abbuono",      _ABB, True )),
                ( 40, (RSSCA_TIPABB,     "Tipo",         _STR, True )),
                (110, (RSSCA_SPESA,      "Spesa",        _ABB, True )),
                (200, (RSSCA_NOTE,       "Note",         _STR, False)),
                ( 40, (RSSCA_CAUS_COD,   "Cod.",         _STR, False)),
                (120, (RSSCA_CAUS_DES,   "Causale",      _STR, False)),
                ( 50, (RSSCA_NUMDOC,     "Num.Doc.",     _STR, False)),
                ( 80, (RSSCA_DATDOC,     "Data Doc.",    _DAT, False)),
                ( 40, (RSSCA_ISRIBA,     "Ri.Ba.",       _CHK, True )),
                ( 40, (RSSCA_ISINSOL,    "Insol.",       _CHK, True )),
                (110, (RSSCA_IMPTOT,     "Importo att.", _ABB, True )),
                (110, (RSSCA_IMPPAR,     "Paregg. att.", _ABB, True )),
                (110, (RSSCA_IMPSALDO,   "Saldo att.",   _ABB, True )),)
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        NewRow = None
        links = None
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE, -1, self.TestValues), )
        
        class GridScaTable(dbglib.DbGridTable):
            def GetValue(self, row, col):
                if self.rsColumns[col] == RSSCA_TIPABB:
                    # visualizza tipo abbuono descrittivo
                    ta = self.data[row][RSSCA_TIPABB]
                    if   ta == "A": out = "Attivo"
                    elif ta == "P": out = "Passivo"
                    else:           out = "???"
                else:
                    out = dbglib.DbGridTable.GetValue(self, row, col)
                return out
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, 
                               tableClass=GridScaTable)
        self.SetColMaxChar(RSSCA_TIPABB, 1)
        self.SetColMaxChar(RSSCA_NOTE, bt.getStdNoteWidth())
        
        self.regrss = regrss
        self.owner = owner
        
        self.SetData(self.regrss, colmap, canedit, canins,\
                     links, afteredit, NewRow)
        
        self._bgcol = Env.Azienda.Colours.GetColour('lightgrey')
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
#        self.SetAnchorColumns(5, 5)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        def MenuPopup(self, event, row):
            def _DeleteRow(*args):
                self.OnDeleteRow(event, rowNum=row)
            def _SchedaPcf(*args):
                pass
            def _MastroPcf(*args):
                pass
            def _CalcolaAbbuono(*args):
                r = self.regrss[row]
                x = ["A", "P"]
                if self.owner._cfg_pasegno == "D":
                    x = ["P", "A"]
                d = r[RSSCA_IMPSALDO]-r[RSSCA_IMPORTO]
                r[RSSCA_ABBUONO] = abs(d)
                r[RSSCA_TIPABB] = x[int(d>0)]
                r[RSSCA_IMPORTO] += d
                self.UpdateSaldi(row)
                self.owner._grid_sca.ResetView()
                self.owner._grid_dav.UpdateDav()
                self.owner.UpdatePanelDav()
            self.SelectRow(row)
            deleteId = wx.NewId()
            schedaId = wx.NewId()
            mastroId = wx.NewId()
            calcabId = wx.NewId()
            menu = wx.Menu()
            menu.Append(deleteId, "Elimina riga")
            menu.Append(schedaId, "Apri la scheda della partita")
            menu.Append(mastroId, "Visualizza il mastro della partita")
            menu.Append(calcabId, "Calcola abbuono")
            menu.Enable(schedaId, False)
            menu.Enable(mastroId, False)
            self.pansca.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
            self.pansca.Bind(wx.EVT_MENU, _CalcolaAbbuono, id=calcabId)
            xo, yo = event.GetPosition()
            self.pansca.PopupMenu(menu, (xo, yo))
            menu.Destroy()
            event.Skip()
        
        def _OnRightClick(event, self=self):
            row = event.GetRow()
            if 0 <= row < len(self.regrss) and self.owner.status == ctb.STATUS_EDITING:
                self.SelectRow(row)
                MenuPopup(self, event, row)
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, _OnRightClick)
        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnCellSelected)
    
    def AddRow(self):
        tipabb = self.owner._cfg_pcfabb
        self.regrss.append([ None,  #RSSCA_PCF_ID
                             None,  #RSSCA_DATSCA
                             None,  #RSSCA_DATDOC
                             None,  #RSSCA_NUMDOC
                             None,  #RSSCA_CAUS_ID
                             None,  #RSSCA_CAUS_COD
                             None,  #RSSCA_CAUS_DES
                             None,  #RSSCA_MPAG_ID
                             None,  #RSSCA_MPAG_COD
                             None,  #RSSCA_MPAG_DES
                             0,     #RSSCA_ISRIBA
                             0,     #RSSCA_ISINSOL
                             0,     #RSSCA_IMPORTO
                             0,     #RSSCA_ABBUONO
                             0,     #RSSCA_SPESA
                             None,  #RSSCA_NOTE
                             tipabb,#RSSCA_TIPABB
                             0,     #RSSCA_IMPTOT
                             0,     #RSSCA_IMPPAR
                             0 ])   #RSSCA_IMPSALDO

    def OnDeleteRow(self, event, rowNum):
        self.DeleteRow(rowNum)
        self.Refresh()
    
    def DeleteRow(self, rowNum):
        self.regrss.pop(rowNum)
        self.owner.UpdateSca_Ids()
        self.owner.UpdatePanelSca()
        self.UpdateSaldi()
        self.owner._grid_dav.UpdateDav()
        self.owner._grid_dav.ResetView()
        self.owner.UpdatePanelDav()
        self.owner._grid_pcf.Refresh()
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        readonly = not rscol in (RSSCA_IMPORTO, RSSCA_ABBUONO, RSSCA_TIPABB,
                                 RSSCA_SPESA, RSSCA_NOTE)
        attr.SetReadOnly(readonly)
        if readonly:
            bgcol = self._bgcol
        else:
            bgcol = Env.Azienda.Colours.NORMAL_BACKGROUND
        attr.SetBackgroundColour(bgcol)
        return attr

    def TestValues(self, row, gridcol, col, value):
        r = self.regrss[row]
        if col == RSSCA_ABBUONO and value<0:
            if r[RSSCA_TIPABB] == "A": r[RSSCA_TIPABB] = "P"
            else:                      r[RSSCA_TIPABB] = "A"
            r[RSSCA_ABBUONO] = abs(value)
        elif col == RSSCA_TIPABB:
            value = value.upper()
            if not value in "AP":
                value = self.owner._cfg_pcfabb or "P"
            if value in "AP":
                r[RSSCA_TIPABB] = value
        self.UpdateSaldi(row)
        self.owner._grid_dav.UpdateDav()
        self.owner.UpdatePanelDav()

    def OnCellSelected(self, event):
        self.UpdateSaldi(event.GetRow())
        event.Skip()
    
    def UpdateSaldi(self, row = None):
        if row is None:
            row = self.GetGridCursorRow()
        # aggiorno i saldi attuale/dopo operazione della partita
        pcfid = None
        if 0 <= row < len(self.regrss):
            pcfid = self.regrss[row][RSSCA_PCF_ID]
        diff = 0
        o = self.owner
        if pcfid is None:
            salatt = diff = 0
        else:
            imp,par = GetRecordInfo(o.db_curs, bt.TABNAME_PCF,\
                                    pcfid, ("imptot","imppar"))
            salatt = imp-par
            try:
                n = awc.util.ListSearch(o.regrss_old,\
                                        lambda s: s[RSSCA_PCF_ID] == pcfid)
                diff = o.regrss_old[n][RSSCA_IMPORTO]
            except IndexError:
                pass
            
            salope = self.regrss[row][RSSCA_IMPORTO]
            if   (o._cfg_pcfimp == '2' and o._cfg_pcfsgn == '+') or\
                 (o._cfg_pcfimp == '1' and o._cfg_pcfsgn == '-'):
                diff = diff-salope
            elif (o._cfg_pcfimp == '1' and o._cfg_pcfsgn == '+') or\
                 (o._cfg_pcfimp == '2' and o._cfg_pcfsgn == '-'):
                diff = salope-diff
            else:
                diff = 0
        
        o.controls["pcfsalatt"].SetValue(salatt)
        o.controls["pcfsalaft"].SetValue(salatt+diff)
        # aggiorno i totali importo/abbuono/spese
        imp = 0
        abb = 0
        spe = 0
        for sca in self.regrss:
            imp += sca[RSSCA_IMPORTO]
            abb += sca[RSSCA_ABBUONO] or 0
            spe += sca[RSSCA_SPESA] or 0
        o.controls["totimp"].SetValue(imp)
        o.controls["totabb"].SetValue(abb)
        o.controls["totspe"].SetValue(spe)
    

# ------------------------------------------------------------------------------


class PcfGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, regrsp, owner):
        """
        Inizializza il grid delle partite del cliente/fornitore.
        """
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        
        cols =(( 80, (RSPCF_DATSCA,     "Data scad.",    _DAT, False)),
               (110, (RSPCF_IMPSALDO,   "Saldo",         _IMP, True )),
               ( 40, (RSPCF_CAUS_COD,   "Cod.",          _STR, False)),
               (120, (RSPCF_CAUS_DES,   "Causale",       _STR, False)),
               ( 50, (RSPCF_NUMDOC,     "Num.Doc.",      _STR, False)),
               ( 80, (RSPCF_DATDOC,     "Data Doc.",     _DAT, False)),
               (110, (RSPCF_IMPTOT,     "Importo",       _IMP, True )),
               (110, (RSPCF_IMPPAR,     "Pareggiamento", _IMP, True )),
               ( 40, (RSPCF_ISRIBA,     "Ri.Ba.",        _CHK, True )),
               ( 40, (RSPCF_ISINSOL,    "Insol.",        _CHK, True )),
               (200, (RSPCF_NOTE,       "Note",          _STR, False)),)
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        parent.SetSize((0,0))
        size = parent.GetClientSizeTuple()
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size)
        self.regrsp = regrsp
        self.owner = owner
        
        c1 = lt.awc.controls.SEARCH_COLORS1
        c2 = lt.awc.controls.SEARCH_COLORS2
        c3 = lt.COLORS_LABEL
        self.SetColors1(*c1)
        self.SetColors2(*c2)
        self.SetBackgroundColour(c1[1])
        self.SetLabelTextColour(c3[0])
        self.SetLabelBackgroundColour(c3[1])
        
        self.SetData(self.regrsp, colmap, canEdit=False, canIns=False)
        c = Env.Azienda.Colours.GetColour('lightgrey')
        self._bgcol = c
        self.SetBackgroundColour(c)
        self.SetCellDynAttr(self.GetAttr)
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
#        self.SetAnchorColumns(6, 3)
        self.SetFitColumn(-1)
        self.AutoSizeColumns()
        
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        if 0 <= row < len(self.regrsp):
            if self.regrsp[row][RSPCF_ID] in self.owner.sca_ids:
                fgcol = stdcolor.GetColour("blue")
            else:
                fgcol = stdcolor.NORMAL_FOREGROUND
            attr.SetTextColour(fgcol)
        attr.SetReadOnly()
        return attr


# ------------------------------------------------------------------------------


class ContabPanelTipo_SC(ctb.ContabPanel):
    """
    Panel Registrazioni saldaconto
    """
    
    def __init__(self, *args, **kwargs):
        """
        Costruttore standard.
        """
        self._auto_abbatt_id = None
        self._auto_abbatt_cod = None
        self._auto_abbatt_des = None
        self._auto_abbpas_id = None
        self._auto_abbpas_cod = None
        self._auto_abbpas_des = None
        
        self.id_pdccp = None   #id pdc c/partita (tipicamente cassa/banca)
        
        self.regrsp = []       #recordset partite del cli/for
        self.regrss = []       #recordset scadenze dell'inc/pag
        self.regrss_old = []   #recordset scadenze per storno
        self.sca_ids = []      #elenco id partite toccate dalla reg.
        self.panpcf = None     #pannello che ospita il grid partite
        self.pansca = None     #pannello che ospita il grid scadenze
        self._grid_pcf = None  #grid partite del cli/for
        self._grid_sca = None  #grid scadenze dell'inc/pag
        
        ctb.ContabPanel.__init__(self, *args, **kwargs)
        
        self._Auto_AddKeysContabTipo_SC()
        
        self._auto_abbatt_id =  self._auto_abbatt
        self._auto_abbatt_cod,\
        self._auto_abbatt_des = GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                                  self._auto_abbatt_id, ("codice","descriz"))
        
        self._auto_abbpas_id =  self._auto_abbpas
        self._auto_abbpas_cod,\
        self._auto_abbpas_des = GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                                  self._auto_abbpas_id, ("codice","descriz"))
        
        self._auto_speinc_id =  self._auto_speinc
        self._auto_speinc_cod,\
        self._auto_speinc_des = GetRecordInfo(self.db_curs, bt.TABNAME_PDC,\
                                  self._auto_speinc_id, ("codice","descriz"))
        
        self.SetName('saldacontopanel')
        self.HelpBuilder_SetDir('contab.dataentry.RegSaldaConto')
    
    def Validate(self):
        if len(self.regrss) == 0:
            awu.MsgDialog(self, 
                          "Inserire almeno una scadenza nella registrazione", 
                          style=wx.ICON_INFORMATION)
            return False
        for s in self.regrss:
            if s[RSSCA_PCF_ID] is None:
                awu.MsgDialog(self, "Ci sono scadenze che puntano a partite inesistenti.\nImpossibile proseguire.", style=wx.ICON_ERROR)
                return False
        out = ctb.ContabPanel.Validate(self)
        if out:
            note1 = self.regrsb[0][ctb.RSDET_NOTE]
            note2 = self.regrsb[1][ctb.RSDET_NOTE]
            if note1 and note1 == note2:
                manca = False
                for r in self.regrss:
                    if not r[RSSCA_NOTE]:
                        manca = True
                        break
                if manca:
                    if awu.MsgDialog(self, "Copio le note su ogni scadenza presente?",
                                     style=wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                        for r in self.regrss:
                            if not r[RSSCA_NOTE]:
                                r[RSSCA_NOTE] = note1
        return out
    
    def RegReset(self):
        ctb.ContabPanel.RegReset(self)
        self.id_pdccp = None
        #reset recordset partite del cli/for
        del self.regrsp[:]
        #reset recordset scadenze dell'inc/pag
        del self.regrss[:]
        #reset recordset scadenze x storno dell'inc/pag
        del self.regrss_old[:]
    
    def UpdateAllControls(self):
        ctb.ContabPanel.UpdateAllControls(self)
        self.UpdatePanelPcf()

    def InitPanelHead(self):
        ctb.ContabPanel.InitPanelHead(self)
        self.panpcf = wx.Panel(self, wdr.ID_PANEL_SCAD)
        wdr.PcfPanelFunc(self.panpcf, True)
        self._grid_pcf = PcfGrid(self.FindWindowById(wdr.ID_PANGRID_PCF),
                                 self.regrsp, self)
        for cid, func in ((wdr.ID_BTNPCFSALDA, self.OnSalda),
                          (wdr.ID_BTNPCFCARD, self.OnVediPcf),
                          (wdr.ID_BTNPCFNEW, self.OnCreaPcf)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        self.Bind(wdr.EVT_DATECHANGED, self.OnDatDocChanged, id=wdr.ID_TXT_DATDOC)
        self.Bind(wx.EVT_TEXT, self.OnNumDocChanged, id=wdr.ID_TXT_NUMDOC)
        self._grid_pcf.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnSalda)
        self._grid_pcf.Bind(gl.EVT_GRID_RANGE_SELECT, self.OnPcfSelected)
        self.Bind(wx.EVT_CHECKBOX, self._OnSaldo0, id=wdr.ID_CHKPCFOPEN)
        cn = self.FindWindowByName
        self.Bind(wx.EVT_BUTTON, self.OnSchedaCliFor, cn('butanag'))
    
    def OnSchedaCliFor(self, event):
        if len(self.regrsb) > 0:
            id_pdc = self.regrsb[0][ctb.RSDET_PDCPA_ID]
            pdc = adb.DbTable('pdc')
            pdc.AddJoin('pdctip', 'tipo')
            if pdc.Get(id_pdc) and pdc.OneRow():
                PdcClass = GetPdcDialogClass(pdc.id_tipo)
                if PdcClass:
                    dlg = PdcClass(self, onecodeonly=id_pdc)
                    dlg.OneCardOnly(id_pdc)
                    dlg.ShowModal()
                    dlg.Destroy()
        event.Skip()
    
    def OnDatDocChanged(self, event):
        self.reg_datdoc = self.controls["datdoc"].GetValue()
        self.UpdateButtons()
        event.Skip()
    
    def OnNumDocChanged(self, event):
        self.reg_numdoc = self.controls["numdoc"].GetValue()
        self.UpdateButtons()
        event.Skip()
    
    def OnPcfSelected(self, event):
        wx.CallAfter(self.UpdateTotPcf)

    def _OnSaldo0(self, event):
        self.PcfRead()
        self.UpdatePanelPcf()

    def OnSalda(self, event):
        if self.status == ctb.STATUS_EDITING:
            self.SaldaPcf()

    def SaldaPcf(self):
        rows = self._grid_pcf.GetSelectedRows()
        if len(rows) == 0 or len(self.regrsp) == 0:
            return
        nsca = None
        for row in rows:
            pcf = self.regrsp[row]
            #if ((pcf[RSPCF_IMPTOT] or 0) - (pcf[RSPCF_IMPPAR] or 0)) < 0:
                #aw.awu.MsgDialog(self, message="Partita negativa", 
                                 #style=wx.ICON_ERROR)
                #continue
            pcf_id = pcf[RSPCF_ID]
            try:
                nsca = awc.util.ListSearch(self.regrss,\
                                    lambda x: x[RSSCA_PCF_ID] == pcf_id)
            except:
                self._grid_sca.AddRow()
                nsca = len(self.regrss)-1
                sca = self.regrss[nsca]
                sca[RSSCA_PCF_ID] =   pcf[RSPCF_ID]
                sca[RSSCA_DATSCA] =   pcf[RSPCF_DATSCA]
                sca[RSSCA_DATDOC] =   pcf[RSPCF_DATDOC]
                sca[RSSCA_NUMDOC] =   pcf[RSPCF_NUMDOC]
                sca[RSSCA_CAUS_ID] =  pcf[RSPCF_CAUS_ID]
                sca[RSSCA_CAUS_COD] = pcf[RSPCF_CAUS_COD]
                sca[RSSCA_CAUS_DES] = pcf[RSPCF_CAUS_DES]
                sca[RSSCA_MPAG_ID] =  pcf[RSPCF_MPAG_ID]
                sca[RSSCA_MPAG_COD] = pcf[RSPCF_MPAG_COD]
                sca[RSSCA_MPAG_DES] = pcf[RSPCF_MPAG_DES]
                sca[RSSCA_ISRIBA] =   pcf[RSPCF_ISRIBA]
                sca[RSSCA_ISINSOL] =  pcf[RSPCF_ISINSOL]
                if self._cfg_pcfimp == '2':
                    #la causale lavora sul pareggiamento della partita:
                    if self._cfg_pcfsgn == '+':
                        #è un incasso, prendo il saldo
                        sca[RSSCA_IMPORTO] = pcf[RSPCF_IMPSALDO]
                    elif self._cfg_pcfins == '1':
                        #è un insoluto, prendo l'importo di origine
                        sca[RSSCA_IMPORTO] = pcf[RSPCF_IMPTOT]
                elif self._cfg_pcfimp == '1':
                    #la causale lavora sull'importo della partita:
                    if self._cfg_pcfsgn == '+':
                        #è un pagamento di nota credito, prendo il valore 
                        #assoluto del saldo 
                        sca[RSSCA_IMPORTO] = abs(pcf[RSPCF_IMPSALDO])
                sca[RSSCA_IMPTOT] =   pcf[RSPCF_IMPTOT]
                sca[RSSCA_IMPPAR] =   pcf[RSPCF_IMPPAR]
                sca[RSSCA_IMPSALDO] = pcf[RSPCF_IMPSALDO]
                sca[RSSCA_ABBUONO] = 0
                sca[RSSCA_SPESA] = 0
        
        self.UpdateSca_Ids()
        self.UpdatePanelSca()
        self._grid_sca.UpdateSaldi()
        self._grid_dav.UpdateDav()
        self.UpdatePanelDav()
        
        if nsca is not None:
            self._grid_pcf.Refresh()
            self._grid_sca.SetGridCursor(nsca,1)
            self._grid_sca.SetFocus()

    def OnVediPcf(self, event):
        rows = self._grid_pcf.GetSelectedRows()
        if len(rows) == 0 or len(self.regrsp) == 0:
            return
        row = rows[0]
        pcfid = self.regrsp[row][RSPCF_ID]
        self.SchedaPcf(pcfid)
        event.Skip()
    
    def OnCreaPcf(self, event):
        self.SchedaPcf()
        event.Skip()
    
    def SchedaPcf(self, pcfid=None):
        dlg = pcf.PcfDialog(self)
        if pcfid is None:
            c = dlg.FindWindowByName('id_pdc')
            c.SetValue(self.id_pdcpa)
            c.Disable()
        else:
            dlg.SetPcf(pcfid)
        if dlg.ShowModal() == 1:
            self.PcfRead()
            self.UpdatePanelPcf()
    
    def InitPanelBody( self ):
        ctb.ContabPanel.InitPanelBody(self)
        wdr.BodyFuncTipo_SC(self.panbody, True)
        self._grid_sca = ScaGrid(self.FindWindowById(wdr.ID_PANGRID_SCA),
                                 self.regrss, self)
        self._grid_dav = DavGrid(self.FindWindowById(wdr.ID_PANGRID_DAV), 
                                 self.regrsb, self)
        self.FindWindowByName('butparity').Hide()
        self._grid_dav.Bind(gl.EVT_GRID_CMD_EDITOR_CREATED, self.OnCellEditorShown)
        self._grid_dav.Bind(gl.EVT_GRID_CMD_EDITOR_SHOWN,   self.OnCellEditorShown)
        return self

    def OnCellEditorShown(self, event):
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
    
    def EnableAllControls(self, enable = True):
        ctb.ContabPanel.EnableAllControls(self, enable)
        self.EnablePcfControls(enable)

    def EnablePcfControls(self, enable = True):
        enable = enable and self.status == ctb.STATUS_EDITING
        self._grid_pcf.Enable(enable)
        for c in awu.GetAllChildrens(self.panpcf):
            if isinstance(c, wx.Button):
                c.Enable(enable)

    def UpdatePanelPcf(self):
        """
        Aggiorna i controlli nel pannello partite del cliente/fornitore.
        """
        label = 'Visualizza solo le partite '
        if self._cfg_pcfins == '1':
            label += 'chiuse'
        else:
            label += 'aperte'
        self.FindWindowById(wdr.ID_CHKPCFOPEN).SetLabel(label)
        if self._grid_pcf is not None:
            self._grid_pcf.ResetView()
            self._grid_pcf.AutoSizeColumns()
            self._grid_pcf.ClearSelection()
            self.UpdateTotPcf()
        SetWarningPag(self.FindWindowByName('butattach'), self.id_pdcpa)

    def UpdateTotPcf(self):
        """
        Aggiorna il totale delle partite aperte.
        """
        seltot = 0
        if self.regrsp:
            rows = self._grid_pcf.GetSelectedRows()
            for row in rows:
                seltot += self.regrsp[row][RSPCF_IMPSALDO]
            numsel = len(rows)
        else:
            numsel = 0
        
        self.controls["pcfselnum"].SetValue(numsel)
        self.controls["pcfseltot"].SetValue(seltot)
        
        pcfopen = [ pcf[RSPCF_IMPSALDO] for pcf in self.regrsp ]
        self.controls["pcfopenum"].SetValue(len(pcfopen))
        self.controls["pcfopetot"].SetValue(sum(pcfopen))

    def UpdatePanelSca(self):
        """
        Aggiorna i controlli nel pannello scadenze dell'incasso/pagamento.
        """
        if self._grid_sca is not None:
            self._grid_sca.ResetView()
            self._grid_sca.AutoSizeColumns()
            self.UpdateTotSca()

    def UpdateTotSca(self):
        """
        Aggiorna i totali delle partite del cliente/fornitore.
        """
        pass
        #totimp = sum( [x[RSSCA_IMPORTO] for x in self.regrss] )
        #self.controls["totscad"].SetValue(totimp)

    def PcfRead(self):
        """
        Lettura partite del cli/for
        """
        #estrazione recordset partite del cli/for
        out = True
        filt = r"pcf.id_pdc=%s"
        par = [self.id_pdcpa]
        if self.controls["onlypcfopen"].GetValue():
            if self._cfg_pcfins == '1':
                filt += " and pcf.imptot=pcf.imppar"
            else:
                filt += " and pcf.imptot!=pcf.imppar"
        cmd =\
"""SELECT pcf.id, pcf.datscad, pcf.datdoc, pcf.numdoc, pcf.id_caus, """\
"""cau.codice, cau.descriz, pcf.id_modpag, mpa.codice, mpa.descriz, """\
"""pcf.riba, pcf.insoluto, pcf.imptot, pcf.imppar, """\
"""pcf.imptot-pcf.imppar, pcf.note """\
"""FROM %s AS pcf """\
"""LEFT JOIN %s AS cau ON pcf.id_caus=cau.id """\
"""LEFT JOIN %s AS mpa ON pcf.id_modpag=mpa.id """\
"""WHERE %s """\
"""ORDER BY pcf.datscad, pcf.id""" % ( bt.TABNAME_PCF, bt.TABNAME_CFGCONTAB,\
                                       bt.TABNAME_MODPAG, filt )
        try:
            self.db_curs.execute(cmd, par)
            rsp = self.db_curs.fetchall()
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            del self.regrsp[:]
            for scad in rsp:
                self.regrsp.append(list(scad))
            out = True
        return out

    def RegRead(self, idreg):
        out = ctb.ContabPanel.RegRead(self, idreg)
        if out: out = self.ScadRead(idreg)
        if out: self.PcfRead()
        if out: self.UpdateSca_Ids()
        self.UpdateTotDav()
        return out

    def ScadRead(self, idreg):
        #estrazione recordset scadenze dell'inc/pag
        out = True
        cmd = """
   SELECT pcf.id, pcf.datscad, pcf.datdoc, pcf.numdoc, pcf.id_caus,
          cau.codice, cau.descriz, pcf.id_modpag, mpa.codice, mpa.descriz,
          pcf.riba, pcf.insoluto, sca.importo, sca.abbuono, sca.spesa,
          sca.note, sca.tipabb, pcf.imptot, pcf.imppar, pcf.imptot-pcf.imppar
          
     FROM %s AS sca
LEFT JOIN %s AS pcf ON    sca.id_pcf=pcf.id
LEFT JOIN %s AS cau ON   pcf.id_caus=cau.id
LEFT JOIN %s AS mpa ON pcf.id_modpag=mpa.id

    WHERE sca.id_reg=%%s
 ORDER BY pcf.datscad, pcf.id""" % ( bt.TABNAME_CONTAB_S,\
                                     bt.TABNAME_PCF,\
                                     bt.TABNAME_CFGCONTAB,\
                                     bt.TABNAME_MODPAG )
        par = (idreg,)
        try:
            self.db_curs.execute(cmd, par)
            rss = self.db_curs.fetchall()
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            del self.regrss[:]
            for scad in rss:
                self.regrss.append(list(scad))
            self.regrss_old = copy.deepcopy(self.regrss)
            self.UpdateSca_Ids()
            self._grid_sca.ResetView()
            self._grid_sca.AutoSizeColumns()
            out = True
        return out

    def UpdateSca_Ids(self):
        del self.sca_ids[:]
        for scad in self.regrss:
            self.sca_ids.append(scad[0])
    
    def RegSave(self):
        """
        Scrittura registrazione su db.  Oltre alla scrittura della
        registrazione, provvede a scrviere le scadenze e ad aggiornare
        le partite clienti/fornitori.
        """
        out = ctb.ContabPanel.RegSave(self)
        if out:
            out = self.ScadStorno()
            if out:
                out = self.ScadWrite()
        if out:
            self.ReportFineReg()
        return out
    
    def RegDelete(self):
        self.ScadStorno()
        return ctb.ContabPanel.RegDelete(self)
    
    #def RegRead(self, idreg):
        #out = ctb.ContabPanel.RegRead(self, idreg)
        #try:
            #n = awc.util.ListSearch(self.regrsb,\
                                    #lambda x: x[ctb.RSDET_NUMRIGA] == 1)
        #except:
            #self.totdoc = 0
        #else:
            #self.totdoc = self.regrsb[n][ctb.RSDET_IMPDARE]
            #if self.totdoc == 0:
                #self.totdoc = self.regrsb[n][ctb.RSDET_IMPAVERE]
        #if out:
            #out = self.ScadRead(idreg)
        #return out

    def ScadStorno(self):
        """
        Storno partite.
        """
        out = False
        #storno importi scadenze da partite associate prima della modifica
        cmd1 =\
"""UPDATE %s SET imptot=imptot-%%s, imppar=imppar-%%s """\
"""WHERE id=%%s""" % bt.TABNAME_PCF
        par1 = []
        #elimino i riferimenti alle partite dopo averle stornate
        cmd2 =\
"""DELETE FROM %s WHERE id_reg=%%s""" % bt.TABNAME_CONTAB_S
        par2 = (self.reg_id,)
        for scad in self.regrss_old:
            pcf = scad[RSSCA_PCF_ID]
            imp = scad[RSSCA_IMPORTO]
            imptot = imppar = 0
            if self._cfg_pcfimp == '1':
                if   self._cfg_pcfsgn == '+':
                    imptot = imp
                elif self._cfg_pcfsgn == '-':
                    imptot = -imp
            elif self._cfg_pcfimp == '2':
                if   self._cfg_pcfsgn == '+':
                    imppar = imp
                elif self._cfg_pcfsgn == '-':
                    imppar = -imp
            par1.append((imptot, imppar, scad[RSSCA_PCF_ID]))
            
        try:
            x = self.db_curs.executemany(cmd1, par1)
            z = self.db_curs.execute(cmd2, par2)
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
        else:
            out = True
        
        return True
    
    def ScadWrite(self):
        out = True
        try:
            nsca = 0
            for scad in self.regrss:
                #aggiornamento partite
                pcf = scad[RSSCA_PCF_ID]
                imp = scad[RSSCA_IMPORTO]
                imptot = imppar = 0
                if self._cfg_pcfimp == '1':
                    if   self._cfg_pcfsgn == '+':
                        imptot = imp
                    elif self._cfg_pcfsgn == '-':
                        imptot = -imp
                elif self._cfg_pcfimp == '2':
                    if   self._cfg_pcfsgn == '+':
                        imppar = imp
                    elif self._cfg_pcfsgn == '-':
                        imppar = -imp
                if pcf is not None:
                    #modifica partita esistente
                    cmd = """UPDATE %s 
                    SET imptot=imptot+%%s, imppar=imppar+%%s""" % bt.TABNAME_PCF
                    if self._cfg_pcfins == '1':
                        cmd += """, insoluto=1"""
                    cmd += r""" WHERE id=%s""" 
                    par = [ imptot, imppar, pcf ]
                    self.db_curs.execute(cmd, par)
                    nsca += 1
            
            #scrittura riferimenti
            par = [ [self.reg_id,\
                     scad[RSSCA_PCF_ID],
                     scad[RSSCA_DATSCA],
                     scad[RSSCA_IMPORTO],
                     scad[RSSCA_ABBUONO],
                     scad[RSSCA_TIPABB],
                     scad[RSSCA_SPESA],
                     scad[RSSCA_NOTE],] for scad in self.regrss ]
            cmd = """
            INSERT INTO %s (id_reg, id_pcf, datscad, importo, abbuono, 
                            tipabb, spesa, note)
                 VALUES (%s)""" % (bt.TABNAME_CONTAB_S, 
                                   (r"%s, "*len(par[0]))[:-2])
            self.db_curs.executemany(cmd, par)
            
            #elimino le partite che dopo lo storno sono andate a zero
            cmd = """
            DELETE FROM %s 
            WHERE id=%%s and imptot=0 and imppar=0""" % bt.TABNAME_PCF
            par = []
            for scad in self.regrss_old:
                pcf = scad[RSSCA_PCF_ID]
                par.append((pcf,))
            self.db_curs.executemany(cmd, par)
            
        except MySQLdb.Error, e:
            MsgDialogDbError(self, e)
            out = False
        
        return out

    def InitCausale(self):
        """
        Inizializza il tipo di causale (C{"S"} con saldaconto)
        """
        self.cautipo = "S"
        self.caufilt = "tipo='%s' and pcf=1 and pcfscon=1" % self.cautipo
        return ctb.ContabPanel.InitCausale(self)
    
    def RegSearchClass( self ):
        """
        Indica la classe da utilizzare per il dialog di ricerca delle
        registrazioni.
        """
        return Reg_SC_SearchDialog
    
    def RegNew(self):
        if self.canins:
            dlgPa = SelRowPa(self, -1)
            if dlgPa.ShowModal() > 0:
                ctb.ContabPanel.RegNew(self)
                self.id_pdcpa = dlgPa.paid
                self.id_pdccp = dlgPa.cpid
                #crea riga partita
                self.regrsb.append([1,           #RSDET_NUMRIGA
                                    "S",         #RSDET_TIPRIGA
                                    dlgPa.paid,  #RSDET_PDCPA_ID
                                    dlgPa.pacod, #RSDET_PDCPA_cod
                                    dlgPa.pades, #RSDET_PDCPA_des
                                    None,        #RSDET_IMPDARE
                                    None,        #RSDET_IMPAVERE
                                    None,        #RSDET_ALIQ_ID
                                    None,        #RSDET_ALIQ_cod
                                    None,        #RSDET_ALIQ_des
                                    None,        #RSDET_ALIQ_TOT
                                    None,        #RSDET_NOTE
                                    0,           #RSDET_RIGAPI
                                    None])       #RSDET_SOLOCONT
                #crea riga c/partita
                self.regrsb.append([2,           #RSDET_NUMRIGA
                                    "S",         #RSDET_TIPRIGA
                                    dlgPa.cpid,  #RSDET_PDCPA_ID
                                    dlgPa.cpcod, #RSDET_PDCPA_cod
                                    dlgPa.cpdes, #RSDET_PDCPA_des
                                    None,        #RSDET_IMPDARE
                                    None,        #RSDET_IMPAVERE
                                    None,        #RSDET_ALIQ_ID
                                    None,        #RSDET_ALIQ_cod
                                    None,        #RSDET_ALIQ_des
                                    None,        #RSDET_ALIQ_TOT
                                    None,        #RSDET_NOTE
                                    0,           #RSDET_RIGAPI
                                    None])       #RSDET_SOLOCONT
                self.PcfRead()
                self.UpdateSca_Ids()
                self.UpdatePanelPcf()
                self.UpdatePanelBody()
                self.SetRegStatus(ctb.STATUS_EDITING)
            else:
                self.SetRegStatus(ctb.STATUS_SELCAUS)
            
            dlgPa.Destroy()

    def UpdatePanelBody(self):
        self.UpdatePanelDav()
        self.UpdatePanelSca()
        self._grid_dav.ResetView()
        self._grid_dav.AutoSizeColumns()
    

# ------------------------------------------------------------------------------


class SelRowPa(aw.Dialog):
    """
    Dialog per la selezione del sottoconto di partita, nonché degli
    eventuali sottoconti di contropartita preferiti, definiti nella causale
    e/o nel sottoconto di partita stesso.
    """
    def __init__(self, parent, id=-1, title="Ricerca sottoconto",\
                 pos=wx.DefaultPosition, size=wx.DefaultSize,\
                 style=wx.DEFAULT_FRAME_STYLE):#|wx.RESIZE_BORDER):
        
        aw.Dialog.__init__(self, parent, id, title, pos, size, style)
        
        self.id_cau = parent.cauid
        self.paid = None
        self.pacod = None
        self.pades = None
        self.cpid = None
        self.cpcod = None
        self.cpdes = None
        
        self.db_curs = parent.db_curs
        
        wdr.SelRowPa_SC_Func(self)
        wx.CallAfter(self.SetFirstFocus)
        
        self.Fit()
        
        self.controls = DictNamedChildrens(self)
        
        self.controls["labeltipo1"].SetLabel(parent._cfg_pdctippa_des or '')
        pdcpa = self.controls["pdcpa"]
        #pdcpa.SetFilterLinks((("Tipo sottoconto",\
                               #bt.TABNAME_PDCTIP,\
                               #"id_tipo",\
                               #PdcTipDialog,\
                               #None,\
                               #parent._cfg_pdctippa_id),))
        #pdcpa.SetInitFocus(ctb.linktab.INITFOCUS_DESCRIZ)
        pdcpa.SetFilterValue(parent._cfg_pdctippa_id)
        
        self.controls["labeltipo2"].SetLabel(parent._cfg_pdctipcp_des or '')
        pdccp = self.controls["pdccp"]
        #pdccp.SetFilterLinks((("Tipo sottoconto",\
                               #bt.TABNAME_PDCTIP,\
                               #"id_tipo",\
                               #PdcTipDialog,\
                               #None,\
                               #parent._cfg_pdctipcp_id),))
        #pdccp.SetInitFocus(ctb.linktab.INITFOCUS_DESCRIZ)
        pdccp.SetFilterValue(parent._cfg_pdctipcp_id)
        
        #impostazione sottoconto preferito c/partita, tipicamente cassa/banca
        pp = parent._cfg_pdcpref
        if len(pp)>0:
            pdccp.SetValue(pp[0])
        
        #imposto la classe del dialog x ins/mod mediante funzione che
        #la cerca in base al tipo anagrafico selezionato
        
        def GetPdcPaTipo():
            return autil.GetPdcDialogClass(pdcpa.GetFilterValue())
        pdcpa.SetDynCard(GetPdcPaTipo)
        
        def GetPdcCpTipo():
            return autil.GetPdcDialogClass(pdccp.GetFilterValue())
        pdccp.SetDynCard(GetPdcCpTipo)
        
        #bindings
        
        lt = ctb.linktab
        self.Bind(lt.EVT_LINKTABCHANGED,\
                  self.OnPdcChanged, self.controls["pdcpa"])
        lt = ctb.linktab
        self.Bind(lt.EVT_LINKTABCHANGED,\
                  self.OnPdcChanged, self.controls["pdccp"])
        
        self.Bind( wx.EVT_CLOSE, self.OnClose )
        self.Bind( wx.EVT_BUTTON, self.OnOk, id = wdr.ID_BTNOK )

    def SetFirstFocus(self):
        self.FindWindowByName('pdcpa').SetFocus()
    
    def OnClose(self, event):
        self.EndModal(0)

    def OnOk(self, event):
        if self.Validate():
            self.EndModal(1)

    def Validate(self):
        out = True
        if self.paid is None or self.cpid is None:
            MsgDialog(self,\
                      """Devi selezionare i sottoconti ai quali fa """\
                      """riferimento l'operazione""",\
                      style = wx.ICON_EXCLAMATION)
            out = False
        #elif not self.doc:
            #if MsgDialog(self,\
                    #"""Sei sicuro che il totale documento sia nullo ?""",\
                    #"Richiesta di conferma",\
                    #style = wx.ICON_QUESTION|\
                            #wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
                #out = False
        return out

    def OnPdcChanged(self, event):
        ctr = event.GetEventObject()
        if ctr.GetName() == "pdcpa":
            self.paid =  ctr.GetValue()
            self.pacod = ctr.GetValueCod()
            self.pades = ctr.GetValueDes()
        else:
            self.cpid =  ctr.GetValue()
            self.cpcod = ctr.GetValueCod()
            self.cpdes = ctr.GetValueDes()

    def SetCausale(self, idcau):
        self.id_cau = idcau


# ------------------------------------------------------------------------------


class ContabFrameTipo_SC(ctb.ContabFrame):
    """
    Frame Registrazioni saldaconto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabFrame.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_SC(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ContabDialogTipo_SC(ctb.ContabDialog):
    """
    Dialog Registrazioni saldaconto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ctb.ContabDialog.__init__(self, *args, **kwargs)
        self.dataentrypanel = ContabPanelTipo_SC(self, -1)
        self.AddSizedPanel(self.dataentrypanel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class Reg_SC_SearchGrid(ctb.RegSearchGrid):
    
    def DefColumns(self):
        _DAT = gl.GRID_VALUE_DATETIME
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        return (( 80, ( 1, "Data reg.",   _DAT, False)),
                (200, ( 2, "Sottoconto",  _STR, False)),
                (110, ( 5, "Dare",        _IMP, True )),
                (110, ( 6, "Avere",       _IMP, True )),
                (  1, ( 0, "#reg",        _STR, False)),)
        
    def GetColumn2Fit(self):
        return 1


# ------------------------------------------------------------------------------


class Reg_SC_SearchPanel(ctb.RegSearchPanel):
    
    wdrFiller = wdr.RegSearchFuncTipo_I
    GridClass = Reg_SC_SearchGrid


# ------------------------------------------------------------------------------


class Reg_SC_SearchDialog(ctb.RegSearchDialog):
    """
    Ricerca registrazioni.
    Dialog per la ricerca di registrazioni della causale selezionata.
    """
    
    panelClass = Reg_SC_SearchPanel
