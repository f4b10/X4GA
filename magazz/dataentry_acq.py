#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/dataentry_acq.py
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

import locale
import magazz.acquis_wdr as wdr

from awc.util import MsgDialog, GetParentFrame

import wx
import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw

import magazz
from magazz import dbtables as dbm

import wx.lib.evtmgr as em
QtaAcqChangedEvent, EVT_QTAACQCHANGED = wx.lib.newevent.NewEvent()

Env = magazz.Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours


class SelDocGrid(dbglib.DbGrid):
    """
    Griglia ricerca documenti da acquisire
    """
    def __init__(self, parent, dbacq, *args, **kwargs):
        """
        Parametri:
        - parent della griglia
        - istanza di RiepDocAcquis da usare per estrarre i documenti
        """
        size = parent.GetClientSizeTuple()
        
        self.dbacq = dbacq
        doc = self.dbacq.mov.doc
        pdc = doc.pdc
        des = doc.dest
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        ncdatreg = cn(dbacq, 'doc_datreg')
        ncnumdoc = cn(dbacq, 'doc_numdoc')
        ncdatdoc = cn(dbacq, 'doc_datdoc')
        nccodana = cn(dbacq, 'pdc_codice')
        ncdesana = cn(dbacq, 'pdc_descriz')
        nccoddes = cn(dbacq, 'dest_codice')
        ncdesdes = cn(dbacq, 'dest_descriz')
        
        cols = (\
        ( 80, (ncdatreg, "Data reg.",      _DAT, True )),\
        ( 60, (ncnumdoc, "Num.",           _NUM, True )),\
        ( 80, (ncdatdoc, "Data doc.",      _DAT, True )),\
        ( 60, (nccodana, "Cod.",           _STR, True )),\
        (180, (ncdesana, "Anagrafica",     _STR, True )),\
        ( 60, (nccoddes, "Cod.",           _STR, True )),\
        (180, (ncdesdes, "Destinazione",   _STR, True )),\
        (100, (-1,       "Stato evasione", _STR, True )),\
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        class GridTable(dbglib.DbGridTable):
            def GetValue(self, row, col):
                rscol = self.rsColumns[col]
                if rscol == -1: #stato evasione
                    doc = self.grid.dbacq
                    if row<doc.RowsCount():
                        doc.MoveRow(row)
                        if (doc.total_qtaevas or 0) == (doc.total_qtaorig or 0):
                            out = "Chiuso"
                        elif (doc.total_qtaevas or 0) == 0:
                            out = "Mai evaso"
                        else:
                            try:
                                pe = ((float(doc.total_qtaevas) or 0.0)/\
                                      (doc.total_qtaorig or 0))*100
                            except ZeroDivisionError:
                                pe = 0
                            out = "Evaso al %.2f%%" % pe
                    else:
                        out = ''
                else:
                    out = dbglib.DbGridTable.GetValue(self, row, col)
                return out
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size,\
                               tableClass=GridTable)
        
        self.SetData([], colmap, canedit, canins)
        
        #def GridAttr(row, col, rscol, attr):
            #if row<self.dbsal.RowsCount():
                #if row != self.dbsal.RowNumber():
                    #self.dbsal.MoveRow(row)
                #if self.dbsal.total_progr_avere>self.dbsal.total_progr_dare:
                    #fgcol = stdcolor.GetColour("red")
                #else:
                    #fgcol = stdcolor.NORMAL_FOREGROUND
                #attr.SetTextColour(fgcol)
            #return attr
        #self.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class SelDocDialog(wx.Dialog):
    """
    Dialog di selezione del documento da acquisire
    """
    def __init__(self, parent, pdc_id, dest_id, docs_id):
        
        wx.Dialog.__init__(self, parent, -1, title="Acquisizione documento",\
                           style=wx.DEFAULT_FRAME_STYLE)
        
        self.docs_id = docs_id
        self.struacq = None
        
        wdr.AcqDocSearchFunc(self)
        
        ctrtdoc = self.FindWindowById(wdr.ID_ACQTIPDOC)
        ctrtdoc.SetFilter("id IN (%s)" %\
                          ','.join(map(str,[d[0] for d in docs_id])))
        self.dbacq =   dbm.RiepDocAcquis()
        self.pdc_id =  pdc_id
        self.dest_id = dest_id
        self.gridsel = SelDocGrid(self.FindWindowById(wdr.ID_ACQPANGRID),\
                                  self.dbacq)
        
        self.Fit()
        
        self.gridsel.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDocSelected)
        self.Bind(wx.EVT_BUTTON, self.OnUpdateGrid, id=wdr.ID_ACQBUTSRC)
        self.Bind(wx.EVT_BUTTON, self.OnDocSelected, id=wdr.ID_ACQBUTSEL)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnUpdateGrid(self, event):
        
        cn = self.FindWindowById
        
        tipdocacq = cn(wdr.ID_ACQTIPDOC).GetValue()
        n = aw.awu.ListSearch(self.docs_id, lambda d: d[0] == tipdocacq)
        self.struacq = self.docs_id[n]
        
        docs = self.dbacq
        doc = docs.mov.doc
        doc.ClearFilters()
        doc.AddFilter(r"doc.id_tipdoc=%s", tipdocacq)
        doc.AddFilter(r"doc.id_pdc=%s", self.pdc_id)
        if self.dest_id is not None:
            doc.AddFilter(r"doc.id_dest=%s", self.dest_id)
        
        for fltid, fltname in ( (wdr.ID_ACQDATDOC1,r'doc_datdoc>=%s'),\
                                (wdr.ID_ACQDATDOC2,r'doc_datdoc<=%s') ):
            fltval = cn(fltid).GetValue()
            if fltval:
                docs.AddFilter(fltname, fltval)
        
        aper, parz, chiu = map(lambda x: cn(x).GetValue(), (wdr.ID_ACQAPERTI,\
                                                            wdr.ID_ACQPARZ,\
                                                            wdr.ID_ACQCHIUSI) )
        docs.SetAcqStatus(aper, parz, chiu)
        docs.Retrieve()
        self.gridsel.ChangeData(docs.GetRecordset())
        
        event.Skip()

    def OnDocSelected(self, event):
        sr = self.gridsel.GetSelectedRows()
        if len(sr)>0 and 0 <= sr[-1] < self.dbacq.RowsCount():
            self.dbacq.MoveRow(sr[-1])
            acqdocid = self.dbacq.mov.doc.id
            n = [x[0] for x in self.docs_id].index(self.dbacq.mov.doc.id_tipdoc)
            self.modoacq = self.docs_id[n][1]
            self.annacq = self.docs_id[n][2]
            self.EndModal(acqdocid)
        event.Skip()
    
    def OnClose(self, event):
        self.EndModal(-1)


# ------------------------------------------------------------------------------


class AcqDocGrid(dbglib.DbGrid):
    """
    Griglia acquisizione documento
    """
    def __init__(self, parent, dbacq, modoacq):
        
        size = parent.GetClientSizeTuple()
        
        self.dbacq = dbacq
        self.modoacq = modoacq
        
        self.colors = {'normal': (stdcolor.NORMAL_FOREGROUND,
                                  stdcolor.NORMAL_BACKGROUND),
                       'closed': (stdcolor.NORMAL_FOREGROUND,
                                  stdcolor.GetColour('yellow')),
                       'acquis': (stdcolor.ADDED_FOREGROUND,
                                  stdcolor.ADDED_BACKGROUND)
                   }
        
        mov = self.dbacq
        doc = mov.doc
        pdc = doc.pdc
        des = doc.dest
        pro = mov.prod
        iva = mov.iva
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER+":4"
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        
        colcodart = pro._GetFieldIndex("codice", inline=True)
        
        cols = (\
            ( 40, (cn(mov, 'numriga'),      "Riga",        _NUM, True )),\
            ( 80, (colcodart,               "Codice",      _STR, True )),\
            (140, (cn(mov, 'descriz'),      "Descrizione", _STR, True )),\
            ( 30, (cn(mov, 'um'),           "U.M.",        _STR, True )),\
            ( -1, (cn(mov, 'qta'),          "Qta orig.",   _QTA, True )),\
            ( -1, (cn(mov, 'total_qtaeva'), "Evaso",       _QTA, True )),\
            ( -1, (   -1,                   "Residuo",     _QTA, True )),\
            ( -1, (cn(mov, 'qtaacq'),       "Quantità",    _QTA, True )),\
            ( -1, (cn(mov, 'prezzo'),       "Prezzo",      _PRE, True )),\
            ( -1, (cn(mov, 'sconto1'),      "Sc.%1",       _SCO, True )),\
            ( -1, (cn(mov, 'sconto2'),      "Sc.%2",       _SCO, True )),\
            ( -1, (cn(mov, 'sconto3'),      "Sc.%3",       _SCO, True )),\
            ( -1, (cn(mov, 'impacq'),       "Importo",     _IMP, True )),\
            ( -1, (cn(mov, 'annacq'),       "Annulla",     _CHK, True )),\
            ( -1, (cn(mov, 'importo'),      "Imp.Orig.",   _IMP, True )),\
            ( 80, (cn(iva, 'descriz'),      "Aliq.IVA",    _STR, True )),\
            )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False
        
        colqta = mov._GetFieldIndex("qta")
        coleva = mov._GetFieldIndex("total_qtaeva")
        class GridTable(dbglib.DbGridTable):
            def GetValue(self, row, col):
                rscol = self.rsColumns[col]
                if rscol == -1: #qta residua
                    qta = self.data[row][colqta] or 0
                    eva = self.data[row][coleva] or 0
                    p = r"%." + "%d" % bt.MAGQTA_DECIMALS + "f"
                    out = locale.format(p, qta-eva, 1)
                else:
                    out = dbglib.DbGridTable.GetValue(self, row, col)
                return out
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0,\
                               tableClass=GridTable)
        
        links = None
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE,  -1,\
                       self.TestEditedValues), )
        
        self.SetData( self.dbacq._info.rs, colmap, canedit, canins,\
                      links, afteredit)
        
        self.AddTotalsRow(2,'Totali:',(cn(mov, 'qta'),
                                       cn(mov, 'total_qtaeva'),
                                       cn(mov, "qtaacq"),
                                       cn(mov, "impacq"),
                                       cn(mov, 'importo')))
        #self.SetRowLabelSize(100)
        #self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        #self.SetRowDynLabel(self.GetRowLabel)
        self.SetCellDynAttr(self.GetAttr)
        #grid.Bind(gl.EVT_GRID_CELL_CHANGE, self.GridBodyOnChanged)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        #def MenuPopup(self, event, row):
            #def _DeleteRow(*args):
                #self.GridBodyOnDelete(event)
            #def _SchedaProd(*args):
                #pass
            #def _MastroMov(*args):
                #pass
            #self.gridbody.SelectRow(row)
            #deleteId = wx.NewId()
            #schedaId = wx.NewId()
            #mastroId = wx.NewId()
            #menu = wx.Menu()
            #if self.dbdoc.mov._info.rs[row][m.RSMOV_ID] is None:
                #desc = "Elimina riga"
            #else:
                #desc = "Marca la riga per la cancellazione"
            #menu.Append(deleteId, desc)
            #menu.Append(schedaId, "Apri la scheda del prodotto")
            #menu.Append(mastroId, "Visualizza il mastro del prodotto")
            #prodok = self.dbdoc.mov.id_prod is not None
            #menu.Enable(schedaId, prodok)
            #menu.Enable(mastroId, prodok)
            #self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
            #xo, yo = event.GetPosition()
            #self.gridbody.PopupMenu(menu, (xo, yo))
            #menu.Destroy()
            #event.Skip()
        
        #def _OnLabelRightClick(event, self=self):
            #row = event.GetRow()
            #if 0 <= row < self.dbdoc.mov.RowsCount():
                #self.gridbody.SelectRow(row)
                #MenuPopup(self, event, row)
        
        #grid.Bind(gl.EVT_GRID_LABEL_RIGHT_CLICK, _OnLabelRightClick)
        #grid.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, _OnLabelRightClick)
    
    def GetRowLabel(self, row):
        desc = ""
        mov = self.dbacq
        if 0 <= row < mov.RowsCount():
            mov.MoveRow(row)
            desc = mov.tipmov.descriz
        return desc
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        #blocco editazione su cella ID
        askvcol = self.dbacq.tipmov._GetFieldIndex("askvalori", inline=True)
        askv = self.dbacq.GetRecordset()[row][askvcol]
        if   askv == "T": cols = [7,8,9,10,11,13]
        elif askv == "Q": cols = [7,13]
        elif askv == "V": cols = [12,13]
        elif askv == "D": cols = [2,13]
        else:             cols = []
        readonly = not col in cols
        acqcol = self.dbacq._GetFieldIndex("acquis", inline=True)
        clscol = self.dbacq._GetFieldIndex("closed", inline=True)
        rs = self.dbacq.GetRecordset()
        acq = rs[row][acqcol]
        cls = rs[row][clscol]
        if acq:
            fgcol, bgcol = self.colors['acquis']
        elif cls:
            fgcol, bgcol = self.colors['closed']
            readonly = True
        else:
            fgcol, bgcol = self.colors['normal']
        if not readonly and col in (7,13) and self.modoacq == "A":
            readonly = True
        attr.SetReadOnly(readonly)
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        return attr

    def TestEditedValues(self, row, col, rscol, value):
        valid = True
        msg = None
        mov = self.dbacq
        mov.MoveRow(row)
        field = self.dbacq.GetFieldName(rscol)
        if field == "qtaacq":
            qta = mov.qta or 0
            eva = mov.total_qtaeva or 0
            res = qta-eva
            valid = 0 <= value <= res
            if valid:
                event = QtaAcqChangedEvent()
                event.SetEventObject( self )
                event.m_id = self.GetId()
                event.SetId( event.m_id )
                wx.PostEvent(GetParentFrame(self), event)
            else:
                msg = """Quantità non valida"""
            mov.acquis = value>0
            
        elif field == 'prezzo':
            valid = value > 0
            
        elif field in ('sconto1', 'sconto2', 'sconto3'):
            valid = 0 <= value <= 100
            if not valid: msg = """Sconto non valido"""
            
        elif field == 'importo':
            valid = value >= 0
            if valid:
                mov.acquis = value > 0
            else:
                msg = """Importo non valido"""
        
        if valid:
            mov.__setattr__(field, value)
            self.dbacq.CalcImpAcq()
            self.ForceRefresh()
        else:
            MsgDialog(self, msg, style = wx.ICON_ERROR)
        
        return valid

    
# ------------------------------------------------------------------------------


class AcqDocDialog(wx.Dialog):
    """
    Dialog di selezione del documento da acquisire
    """
    def __init__(self, parent, docid, modoacq, annacq):
        
        wx.Dialog.__init__(self, parent, -1, title="Acquisizione documento",\
                           style=wx.DEFAULT_FRAME_STYLE)
        wdr.AcqDocFunc(self)
        
        ci = self.FindWindowById
        cn = self.FindWindowByName
        
        self.modoacq = modoacq
        self.annacq = annacq
        
        self.dbacq =  dbm.RiepMovAcquis(writable=True)
        mov = self.dbacq
        doc = mov.doc
        mov.AddFilter("mov.id_doc=%s", docid)
        mov.Retrieve()
        for m in mov:
            m.qtaacq = 0
            m.impacq = 0
            if m.tipmov.askvalori in 'QT':
                m.closed = (m.total_qtaeva or 0) >= (m.qta or 0)
            else:
                m.closed = (m.count_numovi > 0)
        
        self.gridacq = AcqDocGrid(self.FindWindowById(wdr.ID_ACQPANGRID),\
                                  self.dbacq, modoacq)
        
        for ctrid, ctrval in ((wdr.ID_ACQDESTIPDOC, doc.tipdoc.descriz),\
                              (wdr.ID_ACQDESNUMDOC, str(doc.numdoc)),\
                              (wdr.ID_ACQDESDATDOC, doc.datdoc.Format().split()[0])):
            ci(ctrid).SetLabel(ctrval)
        for name in 'int doc'.split():
            c = parent.FindWindowByName('note%s' % name)
            if not c.GetValue():
                c.SetValue(getattr(mov.doc, 'note%s' % name))
        
        self.Fit()
        
        self.TestButtons(0)
        
        self.Bind(wx.EVT_BUTTON, self.OnEvadiRiga,  id=wdr.ID_ACQBUTROW)
        self.Bind(wx.EVT_BUTTON, self.OnEvadiTutto, id=wdr.ID_ACQBUTALL)
        self.Bind(wx.EVT_BUTTON, self.OnConferma,   id=wdr.ID_ACQBUTOK)
        self.Bind(EVT_QTAACQCHANGED, self.OnTestButtons)
        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnSelected, self.gridacq)
    
    def OnSelected(self, event):
        self.TestButtons(event.GetRow())
        event.Skip()
    
    def CanEvas(self, row):
        acq = self.dbacq
        acq.MoveRow(row)
        canevas = False
        if row<acq.RowsCount():
            if acq.f_ann or acq.doc.f_ann:
                canevas = False
            elif acq.tipmov.askvalori in "QT":
                canevas = (acq.total_qtaeva or 0)<(acq.qta or 0)
            else:
                canevas = not acq.count_numovi
        return canevas
    
    def OnEvadiRiga(self, event):
        self.EvadiRighe(self.gridacq.GetSelectedRows())
        event.Skip()

    def OnEvadiTutto(self, event):
        self.EvadiRighe(range(self.dbacq.RowsCount()))
        event.Skip()

    def EvadiRighe(self, rows):
        mov = self.dbacq
        for row in rows:
            if self.CanEvas(row):
                mov.MoveRow(row)
                mov.CalcQtaAcq()
                mov.acquis = True
        self.TestButtons()
        self.gridacq.Refresh()
    
    def OnTestButtons(self, event):
        self.TestButtons()
        event.Skip()
    
    def TestButtons(self, row=None):
        def ci(x):
            return self.FindWindowById(x)
        if row is not None:
            ci(wdr.ID_ACQBUTROW).Enable(self.modoacq != "A" and self.CanEvas(row))
        ci(wdr.ID_ACQBUTOK).Enable(\
            self.dbacq.Locate(lambda mov: mov.acquis) )
    
    def OnConferma(self, event):
        self.EndModal(1)
        event.Skip()
