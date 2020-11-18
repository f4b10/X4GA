#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/ftdif.py
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
import wx.grid as gl
import awc.controls.dbgrid as dbglib
import awc.controls.windows as aw

import magazz.dbftd as ftd
dbm = ftd.dbm
Env = dbm.Env
bt = dbm.bt
adb = dbm.adb
dt = dbm.mx.DateTime

import magazz
import magazz.ftdif_wdr as wdr

from awc.controls.datectrl import EVT_DATECHANGED

import report as rpt
import stormdb as adb


stdcolor = dbm.Env.Azienda.Colours


FRAME_TITLE = "Fatturazione differita"

LISTEFOLDER = "Liste di controllo Operazioni Differite"

import sys
_DEBUG = True and not hasattr(sys, 'frozen')

class GridDocRag(dbglib.DbGridColoriAlternati):
    """
    Griglia documenti estratti
    """
    def __init__(self, parent, dbdoc, idGrid=None):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable documenti (derivati da magazz.dbtables.DocAll)
        """

        size = parent.GetClientSizeTuple()

        self.dbdoc = dbdoc

        cols = self.GetDbColumns()

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False

        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size, style=0, idGrid=idGrid)

        links = None

        afteredit = None
        self.SetData( self.dbdoc.GetRecordset(), colmap, canedit, canins,\
                      links, afteredit)

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

        self.inclescl = True

        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnDocRagInclEscl)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc)


    def GetDbColumns(self):
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        doc = self.dbdoc
        mag = doc.magazz
        tpd = doc.tipdoc
        pdc = doc.pdc
        des = doc.dest
        mpa = doc.modpag
        cat = doc.tracau
        tot = doc.tot

        self.col_p0 = cn(tot, 'total_prezzizero')

        _NUM = gl.GRID_VALUE_NUMBER
        _FLT = bt.GetValIntMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":True,False"

        cols = (
            ( 30, (cn(doc, 'raggruppa'),     "Rag.",           _CHK, True)),
            ( 35, (cn(mag, 'codice'),        "Mag.",           _STR, True)),
            ( 30, (cn(doc, 'f_acq'),         "Acq.",           _CHK, True)),
            ( 30, (cn(doc, 'f_ann'),         "Ann.",           _CHK, True)),
            ( 35, (cn(tpd, 'codice'),        "Cod.",           _STR, True)),
            ( 95, (cn(tpd, 'descriz'),       "Documento",      _STR, True)),
            ( 70, (cn(cat, 'descriz'),       "Caus.Trasp.",    _STR, True)),
            ( 50, (cn(doc, 'numdoc'),        "Num.",           _NUM, True)),
            ( 80, (cn(doc, 'datdoc'),        "Data Doc.",      _DAT, True)),
            ( 80, (cn(doc, 'datreg'),        "Data reg.",      _DAT, True)),
            ( 50, (cn(pdc, 'codice'),        "Cod.",           _STR, True)),
            (190, (cn(pdc, 'descriz'),       "Anagrafica",     _STR, True)),
            (100, (cn(tot, 'total_imponib'), "Tot.Imponibile", _FLT, True)),
            ( 40, (cn(mpa, 'codice'),        "Cod.",           _STR, True)),
            (120, (cn(mpa, 'descriz'),       "Mod.Pagamento",  _STR, True)),
            ( 40, (cn(des, 'codice'),        "Cod.",           _STR, True)),
            (250, (cn(des, 'descriz'),       "Destinazione",   _STR, True)),
            (  1, (cn(doc, 'id'),            "#id",            _STR, True)),
            (  1, (cn(doc, 'changed'),       "#flg",           _CHK, True)),
            )

        return cols




    def GetFieldColInGrid(self, fieldName, ):
        idx=self.dbdoc.GetAllColumnsNames().index(fieldName)
        item= [item for item in self.GetDbColumns() if item[1][0]==idx]
        return item[0][1][0]



    def OnCallDoc(self, event):
        # richiamo documento dai documenti estratti
        assert isinstance(self, dbglib.DbGrid)
        row = event.GetRow()
        dbdoc = self.dbdoc
        if 0 <= row < dbdoc.RowsCount():
            dbdoc.MoveRow(row)
            if magazz.CheckPermUte(dbdoc.id_tipdoc, 'leggi'):
                wx.BeginBusyCursor()
                try:
                    Dialog = magazz.GetDataentryDialogClass()
                    dlg = Dialog(aw.awu.GetParentFrame(self))
                    dlg.SetOneDocOnly(dbdoc.id)
                    dlg.CenterOnScreen()
                finally:
                    wx.EndBusyCursor()
                r = dlg.ShowModal()
                if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                    self.UpdateGrid()
                    if r == magazz.DOC_MODIFIED:
                        wx.CallAfter(lambda: self.SelectRow(row))
                dlg.Destroy()
        event.Skip()

    def UpdateGrid(self):
        self.SetStatus(True)

    def GetAttr(self, row, col, rscol, attr=dbglib.gridlib.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        if 0 <= row < self.dbdoc.RowsCount():
            rs = self.dbdoc.GetRecordset()
            if (rs[row][self.col_p0] or 0) > 0:
                attr.SetTextColour(Env.Azienda.Colours.VALERR_FOREGROUND)
                attr.SetBackgroundColour(Env.Azienda.Colours.VALERR_BACKGROUND)
            elif rs[row][self.GetFieldColInGrid('changed')] and col==12:                 
                #attr.SetTextColour(Env.Azienda.Colours.VALERR_BACKGROUND)
                attr.SetTextColour(Env.Azienda.Colours.VALERR_FOREGROUND)
                attr.SetBackgroundColour(Env.Azienda.Colours.VALERR_BACKGROUND)
        return attr


    #===========================================================================
    # def DrawLines(self, focused=False):
    #     if focused:
    #         tx = self._textcolor_sel_on
    #         row=self.GridCursorRow
    #         rs = self.dbdoc.GetRecordset()            
    #         if rs[row-1][self.GetFieldColInGrid('changed')]:
    #             tx = Env.Azienda.Colours.VALERR_BACKGROUND
    #             
    #         cb = self._gridcolor_sel_on
    #         cl = self._gridcolor_on
    #     else:
    #         tx = 'white'#self._textcolor_sel_off #pare che senza focus la riga di selezione abbia sempre background grigio
    #         cb = self._gridcolor_sel_off
    #         cl = self._gridcolor_off
    #     self.SetSelectionForeground(tx)
    #     self.SetSelectionBackground(cb)
    #     self.SetGridLineColour(cl)
    #===========================================================================



    def OnDocRagInclEscl(self, event):
        if event.GetCol() == 0 and self.inclescl:
            col = self.dbdoc._GetFieldIndex('raggruppa', inline=True)
            row = event.GetRow()
            rs = self.dbdoc.GetRecordset()
            if row < len(rs):
                rs[row][col] = not rs[row][col]
                #self.ForceRefresh()
        event.Skip()


# ------------------------------------------------------------------------------


class GridDocGen(dbglib.DbGrid):
    """
    Griglia documenti generati
    """
    def __init__(self, parent, dbdoc, idGrid=None):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable documenti (derivati da magazz.dbtables.DocAll)
        """

        size = parent.GetClientSizeTuple()

        self.dbdoc = dbdoc
        doc = self.dbdoc
        mag = doc.magazz
        cau = doc.tipdoc
        pdc = doc.pdc
        des = doc.dest
        mpa = doc.modpag
        spe = doc.speinc
        ban = doc.bancf
        tot = doc.tot

        cn = lambda db, col: db._GetFieldIndex(col, inline=True)

        _NUM = gl.GRID_VALUE_NUMBER
        _FLT = bt.GetValIntMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL

        cols = (
            ( 35, (cn(mag, 'codice'),          "Mag.",           _STR, True)),
            ( 35, (cn(cau, 'codice'),          "Cod.",           _STR, True)),
            (120, (cn(cau, 'descriz'),         "Documento",      _STR, True)),
            ( 50, (cn(doc, 'numdoc'),          "Num.",           _NUM, True)),
            ( 80, (cn(doc, 'datdoc'),          "Data Doc.",      _DAT, True)),
            ( 80, (cn(doc, 'datreg'),          "Data reg.",      _DAT, True)),
            ( 50, (cn(pdc, 'codice'),          "Cod.",           _STR, True)),
            (250, (cn(pdc, 'descriz'),         "Anagrafica",     _STR, True)),
            (120, (cn(tot, 'total_imponib'),   "Tot.Imponibile", _FLT, True)),
            ( 40, (cn(mpa, 'codice'),          "Cod.",           _STR, True)),
            (120, (cn(mpa, 'descriz'),         "Mod.Pagamento",  _STR, True)),
            ( 35, (cn(spe, 'codice'),          "Cod.",           _STR, True)),
            (120, (cn(spe, 'descriz'),         "Spese incasso",  _STR, True)),
            ( 35, (cn(ban, 'codice'),          "Cod.",           _STR, True)),
            (160, (cn(ban, 'descriz'),         "Banca appoggio", _STR, True)),
            ( 35, (cn(des, 'codice'),          "Cod.",           _STR, True)),
            (250, (cn(des, 'descriz'),         "Destinazione",   _STR, True)),
            (  1, (cn(doc, 'original_id_doc'), "#idDoc",         _STR, True)),
        )

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False

        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0, idGrid=idGrid)

        links = None

        afteredit = None
        self.SetData( self.dbdoc.GetRecordset(), colmap, canedit, canins,\
                      links, afteredit)

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


class GridMovRag(dbglib.DbGrid):
    """
    Griglia dettaglio movimenti
    """
    def __init__(self, parent, dbmov, gridFather=None, idGrid=None):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable movimenti (derivati da magazz.dbftd.MovAll)
        """

        size = parent.GetClientSizeTuple()

        self.dbmov = dbmov
        self.gridFather=gridFather

        cols = self.GetDbColumns()

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False

#===============================================================================
#         def BeforeEdit(row, gridcol, col, value):
#             print 'before'
#             return True
#
#         def AfterEdit(row, gridcol, col, value):
#             print 'after'
#             return True
#
#         afterEdit = ((dbglib.CELLEDI
#                       T_BEFORE_UPDATE, 1, BeforeEdit,),
#                      (dbglib.CELLEDIT_AFTER_UPDATE, 1, AfterEdit,),)
#===============================================================================

        afterEdit = ( (dbglib.CELLEDIT_BEFORE_UPDATE, -1, self.OnBeforeValueChanged),
                      (dbglib.CELLEDIT_AFTER_UPDATE, -1,  self.OnAfterValueChanged),)

        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0, idGrid=idGrid)

        links = None

        #afteredit = None
        self.SetData( self.dbmov.GetRecordset(), colmap, canedit, canins,\
                      links, afterEdit)

        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))

        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallDoc)

    def OnCallDoc(self, event):
        # richiamo documento dai movimenti estratti
        assert isinstance(self, dbglib.DbGrid)
        row = event.GetRow()
        dbmov = self.dbmov
        if 0 <= row < dbmov.RowsCount():
            dbmov.MoveRow(row)
            print 'id doc: %s' % dbmov.id_doc
            if self.CheckPermUte(dbmov.id_doc, 'leggi'):
                wx.BeginBusyCursor()
                try:
                    Dialog = magazz.GetDataentryDialogClass()
                    dlg = Dialog(aw.awu.GetParentFrame(self))
                    dlg.SetOneDocOnly(dbmov.id_doc)
                    dlg.CenterOnScreen()
                finally:
                    wx.EndBusyCursor()
                r = dlg.ShowModal()
                if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                    self.UpdateGrid()
                    if r == magazz.DOC_MODIFIED:
                        wx.CallAfter(lambda: self.SelectRow(row))
                dlg.Destroy()
        event.Skip()

    def UpdateGrid(self):
        self.SetStatus(True)

    def CheckPermUte(self, idDoc, perm):
        dbDoc=adb.DbTable(bt.TABNAME_MOVMAG_H)
        dbDoc.Get(idDoc)
        return magazz.CheckPermUte(dbDoc.id_tipdoc, perm)

    def GetDbColumns(self):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)

        _NUM = gl.GRID_VALUE_NUMBER
        _FLT = bt.GetValIntMaskInfo()
        _FLQ = bt.GetMagQtaMaskInfo()
        _FLP = bt.GetMagPreMaskInfo()
        _FLS = bt.GetMagScoMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":True,False"

        mov = self.dbmov
        tpm = mov.tipmov
        pro = mov.prod
        iva = mov.iva

        cols = []
        a = cols.append
        a(( 30, (cn(tpm, 'codice'),  "M.",           _STR, False)))
        a(( 90, (cn(pro, 'codice'),  "Cod.",         _STR, False)))
        a((280, (cn(mov, 'descriz'), "Descrizione",  _STR, False)))
        a(( 20, (cn(mov, 'um'),      "U.M.",         _STR, False)))
        a(( 90, (cn(mov, 'qta'),     "Qtà",          _FLQ, True)))
        a((100, (cn(mov, 'prezzo'),  "Prezzo",       _FLP, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 40, (cn(mov, 'sconto1'), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _FLS, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 40, (cn(mov, 'sconto2'), "Sc.%2",    _FLS, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 40, (cn(mov, 'sconto3'), "Sc.%3",    _FLS, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 40, (cn(mov, 'sconto4'), "Sc.%4",    _FLS, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 40, (cn(mov, 'sconto5'), "Sc.%5",    _FLS, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 40, (cn(mov, 'sconto6'), "Sc.%6",    _FLS, True)))
        a((110, (cn(mov, 'importo'), "Importo",      _FLT, False)))
        a(( 30, (cn(iva, 'codice'),  "Cod.",         _STR, False)))
        a(( 90, (cn(iva, 'descriz'), "Aliquota IVA", _STR, False)))
        a(( 90, (cn(tpm, 'descriz'), "Movimento",    _STR, False)))
        a((200, (cn(mov, 'note'),    "Note",         _STR, False)))

        a((  1, (cn(mov, 'id_doc'),  "#idDoc",        _STR, False)))
        a((  1, (cn(mov, 'id'),      "#id",           _STR, False)))
        return cols


    def GetFieldColInGrid(self, fieldName):
        idx=self.dbmov.GetAllColumnsNames().index(fieldName)
        item= [item for item in self.GetDbColumns() if item[1][0]==idx]
        return item[0][1][0]

    def OnBeforeValueChanged(self, row, gridcol, col, value):
        changed = False
        table = self.GetTable()
        data = table.data
        newData=[]
        for r in data:
            newData.append(list(r))
        self.GetTable().data=newData
        data = self.GetTable().data

        return True

    def OnAfterValueChanged(self, row, gridcol, col, value):
        table = self.GetTable()
        data = table.data
        sconto={}
        for n in ['sconto1', 'sconto2', 'sconto3', 'sconto4', 'sconto5', 'sconto6']:
            try:
                sconto[n]=data[row][self.GetFieldColInGrid(n)]
            except:
                sconto[n]=0
        data[row][self.GetFieldColInGrid('importo')]=round(
                                                           data[row][self.GetFieldColInGrid('qta')]*data[row][self.GetFieldColInGrid('prezzo')]\
                                                            *(100-sconto['sconto1'])/100\
                                                            *(100-sconto['sconto2'])/100\
                                                            *(100-sconto['sconto3'])/100\
                                                            *(100-sconto['sconto4'])/100\
                                                            *(100-sconto['sconto5'])/100\
                                                            *(100-sconto['sconto6'])/100, bt.VALINT_DECIMALS)
        id=data[row][self.GetFieldColInGrid('id')]
        idDoc=data[row][self.GetFieldColInGrid('id_doc')]
        self.UpdateMovDoc(id,
                          idDoc,
                          qta=data[row][self.GetFieldColInGrid('qta')],
                          prezzo=data[row][self.GetFieldColInGrid('prezzo')],
                          sconto1=sconto['sconto1'],
                          sconto2=sconto['sconto2'],
                          sconto3=sconto['sconto3'],
                          sconto4=sconto['sconto4'],
                          sconto5=sconto['sconto5'],
                          sconto6=sconto['sconto6'],
                          importo=data[row][self.GetFieldColInGrid('importo')])
        self.gridFather.Refresh()
        self.SetStatus(True)

    def UpdateMovDoc(self, id, idDoc, qta=0, prezzo=0, sconto1=0, sconto2=0, sconto3=0, sconto4=0, sconto5=0, sconto6=0, importo=0):
        dbWork=adb.DbTable(bt.TABNAME_MOVMAG_B)
        if dbWork.Get(id):
            dbWork.qta     = qta
            dbWork.prezzo  = prezzo
            dbWork.sconto1 = sconto1
            dbWork.sconto2 = sconto2
            dbWork.sconto3 = sconto3
            dbWork.sconto4 = sconto4
            dbWork.sconto5 = sconto5
            dbWork.sconto6 = sconto6
            dbWork.importo = importo
            if dbWork.Save():
                obj=Env.GetAncestorByName(self, 'pgedoc').GetChildren()[0]
                row=None
                for i, r in enumerate(obj.GetTable().data):
                    if r[0]==idDoc:
                        row=i
                        break
                obj.GetTable().data[row][obj.GetFieldColInGrid('changed')] = True
                pass

# ------------------------------------------------------------------------------


class GridMovGen(GridMovRag):
    def GetDbColumns(self):
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)

        _NUM = gl.GRID_VALUE_NUMBER
        _FLT = bt.GetValIntMaskInfo()
        _FLQ = bt.GetMagQtaMaskInfo()
        _FLP = bt.GetMagPreMaskInfo()
        _FLS = bt.GetMagScoMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":True,False"

        mov = self.dbmov
        tpm = mov.tipmov
        pro = mov.prod
        iva = mov.iva

        cols = []
        a = cols.append
        a(( 30, (cn(tpm, 'codice'),  "M.",           _STR, True)))
        a(( 90, (cn(pro, 'codice'),  "Cod.",         _STR, True)))
        a((280, (cn(mov, 'descriz'), "Descrizione",  _STR, True)))
        a(( 20, (cn(mov, 'um'),      "U.M.",         _STR, True)))
        a(( 90, (cn(mov, 'qta'),     "Qtà",          _FLQ, True)))
        a((100, (cn(mov, 'prezzo'),  "Prezzo",       _FLP, True)))
        if bt.MAGNUMSCO >= 1:
            a(( 40, (cn(mov, 'sconto1'), "Sc.%"+'1'*int(bt.MAGNUMSCO>1), _FLS, True)))
        if bt.MAGNUMSCO >= 2:
            a(( 40, (cn(mov, 'sconto2'), "Sc.%2",    _FLS, True)))
        if bt.MAGNUMSCO >= 3:
            a(( 40, (cn(mov, 'sconto3'), "Sc.%3",    _FLS, True)))
        if bt.MAGNUMSCO >= 4:
            a(( 40, (cn(mov, 'sconto4'), "Sc.%4",    _FLS, True)))
        if bt.MAGNUMSCO >= 5:
            a(( 40, (cn(mov, 'sconto5'), "Sc.%5",    _FLS, True)))
        if bt.MAGNUMSCO >= 6:
            a(( 40, (cn(mov, 'sconto6'), "Sc.%6",    _FLS, True)))
        a((110, (cn(mov, 'importo'), "Importo",      _FLT, True)))
        a(( 30, (cn(iva, 'codice'),  "Cod.",         _STR, True)))
        a(( 90, (cn(iva, 'descriz'), "Aliquota IVA", _STR, True)))
        a(( 90, (cn(tpm, 'descriz'), "Movimento",    _STR, True)))
        a((200, (cn(mov, 'note'),    "Note",         _STR, True)))


        a((  1, (cn(mov, 'id_doc'),           "#numDoc",    _STR, True)))
        a((  1, (cn(mov, 'original_id'),      "#id",        _STR, True)))
        a((  1, (cn(mov, 'original_id_doc'),  "#idDoc",     _STR, True)))
        return cols



    def OnCallDoc(self, event):
        # richiamno documento dai movimenti generati
        assert isinstance(self, dbglib.DbGrid)
        row = event.GetRow()
        dbmov = self.dbmov

        idx_id    = self.dbmov.GetAllColumnsNames().index('original_id')
        idx_iddoc = self.dbmov.GetAllColumnsNames().index('original_id_doc')

        if 0 <= row < len(self.GetTable().data):
            r=self.GetTable().data[row]
            id=r[idx_id]
            idDoc=r[idx_iddoc]
            if self.CheckPermUte(idDoc, 'leggi'):
                wx.BeginBusyCursor()
                try:
                    Dialog = magazz.GetDataentryDialogClass()
                    dlg = Dialog(aw.awu.GetParentFrame(self))
                    dlg.SetOneDocOnly(idDoc)
                    dlg.CenterOnScreen()
                finally:
                    wx.EndBusyCursor()
                r = dlg.ShowModal()
                if r in (magazz.DOC_MODIFIED, magazz.DOC_DELETED):
                    self.UpdateGrid()
                    if r == magazz.DOC_MODIFIED:
                        wx.CallAfter(lambda: self.SelectRow(row))
                dlg.Destroy()
        event.Skip()

    def UpdateGrid(self):
        self.SetStatus(True)

    def CheckPermUte(self, idDoc, perm):
        dbDoc=adb.DbTable(bt.TABNAME_MOVMAG_H)
        dbDoc.Get(idDoc)
        return magazz.CheckPermUte(dbDoc.id_tipdoc, perm)




# ------------------------------------------------------------------------------


class FtDifPanel(aw.Panel):

    needRecalc=None


    def __init__(self, *args, **kwargs):

        aw.Panel.__init__(self, *args, **kwargs)
        wdr.FtdSelFunc(self)
        cn = self.FindWindowByName


        self.SetStatus()

        #fatturazione differita
        self.ftd = ftd.FtDif()
        self.ftd.docrag.ShowDialog(self)

        self.dbdoc = dbm.DocMag()

        #inizializzazione controlli
        today = Env.Azienda.Esercizio.dataElab

        d1 = today
        if d1.day < 15:
            d1 -= 10
            d1 = dt.DateTime(d1.year, d1.month, 1)
            d2 = dt.DateTime(d1.year, d1.month, d1.GetDaysInMonth())
        else:
            d1 = dt.DateTime(d1.year, d1.month, 1)
            d2 = today

        if _DEBUG:
            d1 = dt.DateTime(2020, 7, 1)
            d2 = dt.DateTime(2020, 7, 5)



        for name, val in (('datmin', d1),
                          ('datmax', d2),
                          ('datdoc', d2)):
            cn(name).SetValue(val)

        cn('datlast').Disable()
        cn('numlast').Disable()



        #griglie doc/mov estratti
        self.gridocrag = GridDocRag(cn('pgedoc'), self.ftd.docrag, idGrid='ftd_docestratti')
        self.gridocrag.SetStatus = self.SetStatus

        self.grimovrag = GridMovRag(cn('pgemov'), self.ftd.movrag, gridFather=self.gridocrag, idGrid='ftd_movestratti')
        self.grimovrag.SetStatus = self.SetStatus

        #def MenuPopup(self, event, row):
            #def _DeleteRow(*args):
                #self.OnDocRagDel(event)
            #self.gridocrag.SelectRow(row)
            #deleteId = wx.NewId()
            #menu = wx.Menu()
            #desc = "Escludi dal raggruppamento"
            #menu.Append(deleteId, desc)
            #self.Bind(wx.EVT_MENU, _DeleteRow, id=deleteId)
            #xo, yo = event.GetPosition()
            #self.gridocrag.PopupMenu(menu, (xo, yo))
            #menu.Destroy()
            #event.Skip()

        #def _OnLabelRightClick(event, self=self):
            #row = event.GetRow()
            #if 0 <= row < self.ftd.docrag.RowsCount():
                #self.gridocrag.SelectRow(row)
                #MenuPopup(self, event, row)

        #self.gridocrag.Bind(gl.EVT_GRID_LABEL_RIGHT_CLICK, _OnLabelRightClick)
        #self.gridocrag.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, _OnLabelRightClick)

        self.gridocrag.Bind(gl.EVT_GRID_SELECT_CELL, self.OnDocRagSelected)

        #griglie doc/mov generati
        self.gridocgen = GridDocGen(cn('pggdoc'), self.ftd.docgen, idGrid='ftd_docgen')
        self.grimovgen = GridMovGen(cn('pggmov'), self.ftd.movgen, idGrid='ftd_movgen')

        self.grimovgen.SetStatus=self.SetStatus


        self.gridocgen.Bind(gl.EVT_GRID_SELECT_CELL, self.OnDocGenSelected)

        #artifizio: x evidenziare con colori alternati insiemi di documenti
        #diversi raggruppati nello stesso documento generato, viene aggiunta
        #una colonna fittizia 'docset' nel corpo dei movimenti generati, che
        #parte da 1 per il primo documento raggruppato e si incrementa per
        #ogni diverso documento raggruppato
        msc = self.ftd.movgen._GetFieldIndex('docset', inline=True)
        if msc >= 0:
            colors = [wx.TheColourDatabase.Find(x)
                      for x in ('oldlace', 'azure')]
            def MovGenGetAttr(row, col, rscol, attr=gl.GridCellAttr):
                rs = self.grimovgen.GetTable().data
                if row < len(rs):
                    rowrs = rs[row]
                    attr.SetBackgroundColour(colors[rowrs[msc] % 2])
                return attr
            self.grimovgen.SetCellDynAttr(MovGenGetAttr)

        for evt, cbf, name in (
            (EVT_DATECHANGED, self.OnDatDocChanged, 'datdoc'),
            (wx.EVT_BUTTON,   self.OnEstrai,        'butest'),
            (wx.EVT_BUTTON,   self.OnRaggr,         'butrag'),
            (wx.EVT_BUTTON,   self.OnListaRag,      'listrag'),
            (wx.EVT_BUTTON,   self.OnGenera,        'butconf'),
            (wx.EVT_BUTTON,   self.OnListaGen,      'listgen'),
            (wx.EVT_BUTTON,   self.OnHistory,       'story'),
            ):
            self.Bind(evt, cbf, cn(name))

        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnDocRagInclEscl)


    def SetStatus(self, needRecalc=False):
        self.needRecalc = needRecalc
        for n in ['msgEstratti', 'msgGenerati', 'listrag', 'butrag', 'listgen', 'butconf']:
            obj=self.FindWindowByName(n)
            if obj:
                if isinstance(obj, wx.StaticText):
                    if self.needRecalc:
                        obj.SetLabel("ATTENZIONE PROVVEDERE A RIESEGUIRE L'ESTRAZIONE")
                    else:
                        obj.SetLabel("")
                elif isinstance(obj, wx.Button):
                    obj.Enable(not needRecalc)

    def OnListaRag(self, event):
        docids = [str(d.id) for d in self.ftd.docrag if d.raggruppa == 1]
        docs = dbm.DocMag()
        docs.ShowDialog(self)
        msg = "Vuoi ordinare i documenti raggruppati per numero?"
        x = aw.awu.MsgDialog(self, msg,
                             style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if x == wx.ID_NO:
            docs.ClearOrders()
            docs.AddOrder("pdc.descriz")
            docs.AddOrder("doc.datdoc")
            docs.AddOrder("doc.numdoc")
        if not docs.Retrieve('doc.id IN (%s)' % ','.join(docids)):
            aw.awu.MsgDialog(self, message=repr(docs.GetError()))
            return
        self.Stampa(docs, LISTEFOLDER, "Lista documenti da raggruppare")
        event.Skip()

    def Stampa(self, dbt, rptname, rpttitle, **kwargs):
        dbt._info.titleprint = rpttitle
        rpt.Report(self, dbt, rptname, **kwargs)

    def OnListaGen(self, event):
        #caricamento dbm.DocMag x stampa di tutti i documenti generati
        dg = self.ftd.docgen
        wait = aw.awu.WaitDialog(self,
                                 message='Preparazione dei dati per la stampa',
                                 maximum = dg.RowsCount())
        docs = dbm.DocMag()
        docs.AddField('0.0', 'allinea')
        docs.Get(-1)
        mov = self.ftd.movgen
        docs._info.updateMChildrens = False
        for n, dg in enumerate(dg):
            docs.CreateNewRow()
            for field in dg.GetFieldNames():
                setattr(docs, field, getattr(dg, field))
            wait.SetValue(n)
        wait.Destroy()
        #aggiornamento dettaglio documento in stampa
        #ad ogni iterazione sui documenti, la funzione provvede a caricare
        #i movimenti generati
        def LoadMovs(report, dbt):
            if not dbt.allinea == 1:
                dbt.totimponib = 0
                dbt.mov.Reset()
                if mov.Locate(lambda row: row.id_doc == -dbt.numdoc):
                    while mov.id_doc == -dbt.numdoc:
                        dbt.mov.CreateNewRow()
                        for field in mov.GetFieldNames():
                            setattr(dbt.mov, field, getattr(mov, field))
                        if not mov.tipmov.tipologia in 'EO':
                            impriga = mov.importo or 0
                            if mov.tipmov.tipologia == 'I':
                                impriga *= -1
                            dbt.totimponib += impriga
                        if not mov.MoveNext():
                            break
                    
                dbt.mov.MoveFirst()
                nr = dbt._info.recordNumber
                try:
                    dbt.MoveRow(0)
                    dbt.MoveRow(nr)
                except:
                    pass
                report.StoreRecordPosition = dbt.SavePosition()
                dbt.allinea = 1
        self.Stampa(docs, LISTEFOLDER, "Lista documenti generati", rowFunc=LoadMovs)
        event.Skip()

    def OnHistory(self, event):
        frame = FtDifHistoryFrame(self)
        frame.Show()
        event.Skip()

    def OnDocRagInclEscl(self, event):
        self.UpdateDocRag()
        event.Skip()

    #def OnDocRagDel(self, event):
        #row = event.GetRow()
        #self.gridocrag.DeleteRows(row)
        #dr = self.ftd.docrag
        #dr._info.recordCount -= 1
        #if dr._info.recordNumber >= dr._info.recordCount:
            #dr._info.recordNumber -= 1
        #dr._info.iterIndex -= 1
        #dr._info.iterCount -= 1
        #self.UpdateDocRag()
        #event.Skip()

    def OnDocRagSelected(self, event):
        row = event.GetRow()
        if 0 <= row < self.ftd.docrag.RowsCount():
            self.ftd.docrag.MoveRow(row)
            if self.ftd.movrag.Retrieve("movrag.id_doc=%s", self.ftd.docrag.id):
                self.grimovrag.ChangeData(self.ftd.movrag.GetRecordset())
            else:
                aw.awu.MsgDialog(self, repr(self.ftd.movrag.GetError()))
            event.Skip()

    def OnDocGenSelected(self, event):
        dg = self.ftd.docgen
        mg = self.ftd.movgen
        row = event.GetRow()
        movrs = []
        if row < dg.RowsCount():
            dg.MoveRow(row)
            numdoc = dg.numdoc
            col = mg._GetFieldIndex('id_doc', inline=True)
            if mg.LocateRow(lambda movrs: movrs[col] == -numdoc):
                while mg.id_doc == -numdoc:
                    movrs.append(mg.GetRecordset()[mg.RowNumber()])
                    if not mg.MoveNext():
                        break
        self.grimovgen.ChangeData(movrs)
        event.Skip()

    def OnEstrai(self, event):
        if self.Validate():
            self.Estrai()
            self.SetStatus(False)
            event.Skip()

    def OnRaggr(self, event):
        self.Raggruppa()
        event.Skip()

    def Validate(self):
        cn = self.FindWindowByName
        ddoc, dmin, dmax = map(lambda x: cn(x).GetValue(), 'datdoc datmin datmax'.split())
        ndoc, nmin, nmax = map(lambda x: cn(x).GetValue(), 'numdoc nummin nummax'.split())
        err = False
        cando = False
        if not err:
            for val, msg in ((ddoc, 'la data del documento'),
                             (ndoc, 'il numero del primo documento')):
                if not val:
                    err = 'Indicare %s da generare' % msg
                    break
        if not err:
            for val, msg in ((ddoc, 'la data del documento'),
                             (dmin, 'la data minima dei documenti'),
                             (dmax, 'la data massima dei documenti')):
                if not val:
                    err = 'Indicare %s da generare' % msg
                    break
        if not err:
            if dmin>dmax:
                err = 'Le date dei documenti da raggruppare sono incongruenti'
            elif nmin>nmax:
                err = 'I numeri dei documenti da raggruppare sono incongruenti'
            elif ddoc<dmin:
                err = 'Il documento da generare non può essere antecedente a quelli da raggruppare'
        if not err:
            cando = True
            if ddoc.year != dmax.year:
                err = 'L\'anno dei documenti da generare e non coincide con l\'anno dei documenti da raggruppare'
            elif ddoc.month != dmax.month:
                err = 'Il mese dei documenti da generare e non coincide con il mese dei documenti da raggruppare'
            elif dmin.year != dmax.year or dmin.month != dmax.month:
                err = 'Le date dei documenti da raggruppare non appartengono allo stesso mese'
        if err:
            msg = err
            if cando:
                msg += '.\n\nProcedo ugualmente?'
                style = wx.ICON_INFORMATION|wx.YES_NO|wx.NO_DEFAULT
            else:
                style = wx.ICON_ERROR
            do = aw.awu.MsgDialog(self, message=msg, style=style) == wx.ID_YES
        else:
            do = True
        return do

    def Estrai(self):

        ftd = self.ftd
        cn = self.FindWindowByName

        dr = ftd.docrag
        dg = ftd.docgen

        for d, uname, tname in ((dg, 'sepall',  None),
                                (dg, 'sepmp',   None),
                                (dg, 'sepdest', None),
                                (dr, 'datmin',  None),
                                (dr, 'datmax',  None),
                                (dr, 'nummin',  None),
                                (dr, 'nummax',  None),
                                (dr, 'esclacq', None),
                                (dr, 'esclann', None),
                                (dr, 'solosta', None),
                                (dr, 'magazz',  'solomag'),
                                (dr, 'pdc',     'solopdc'),
                                (dr, 'agente',  'soloage'),
                                (dr, 'zona',    'solozona'),
                                (dr, 'catcli',  'solocateg'),
                                (dr, 'modpag',  'solomp'),):

            c = cn(uname)
            if c:
                v = c.GetValue()
            else:
                v = getattr(self, uname, None)

            name = tname
            if name is None:
                name = uname

            setattr(d, '_%s' % name, v)

        ftd.docrag._tipidoc = [int(ddr.id_docrag)
                               for n, ddr in enumerate(ftd.ddr)
                               if cn('docs').IsChecked(n)]

        ctrct = cn('cautra')
        if ctrct:
            ftd.docrag._cautras = [ct.id for n, ct in enumerate(self.dbtracau)
                                   if ctrct.IsChecked(n)]
            if ctrct.IsChecked(ctrct.GetCount()-1):
                ftd.docrag._cautras.append(None)
        else:
            ftd.docrag._cautras = [None]

        #azzero contenuto griglie
        for grid in (self.gridocrag, self.grimovrag,
                     self.gridocgen, self.grimovgen):
            grid.ChangeData(())

        try:
            ftd.Estrai()
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args))

        p0 = False
        dr = self.ftd.docrag
        cp0 = dr.tot._GetFieldIndex('total_prezzizero', inline=True)
        if dr.LocateRS(lambda r: r[cp0]>0) is not None:
            p0 = True
        if p0:
            wx.CallAfter(lambda: aw.awu.MsgDialog(self, "Ci sono documenti con prezzo nullo.\nImpossibile procedere.", style=wx.ICON_ERROR))
        for name in 'butrag butconf'.split():
            c = cn(name)
            if c:
                c.Enable(not p0)

        self.UpdateDocRag()

        if ftd.docrag.RowsCount() == 0:
            aw.awu.MsgDialog(self, "Nessun documento da raggruppare")
        else:
            self.gridocrag.inclescl = False
            self.gridocrag.ChangeData(ftd.docrag.GetRecordset())
            self.gridocrag.inclescl = True
            cn('workzone').SetSelection(1)

    def UpdateDocRag(self):
        dr = self.ftd.docrag
        tot = {0: [0, 0], 1: [0, 0]}
        colrag = dr._GetFieldIndex('raggruppa')
        coltot = dr.tot._GetFieldIndex('total_imponib', inline=True)
        for docrs in dr.GetRecordset():
            tot[docrs[colrag]][0] += 1
            tot[docrs[colrag]][1] += docrs[coltot]
        cn = self.FindWindowByName
        for name, rag, col in (('docinclnum', 1, 0),
                               ('docincltot', 1, 1),
                               ('docesclnum', 0, 0),
                               ('docescltot', 0, 1)):
            cn(name).SetValue(tot[rag][col])

    def UpdateDocGen(self):
        cn = self.FindWindowByName
        dg = self.ftd.docgen
        cn('docgennum').SetValue(dg.RowsCount())
        if dg.RowsCount() == 0:
            n1 = n2 = None
        else:
            col = self.ftd.docgen._GetFieldIndex('numdoc', inline=True)
            n1, n2 = [dg._info.rs[row][col] for row in (0, dg.LastRow())]
        cn('docgenmin').SetValue(n1)
        cn('docgenmax').SetValue(n2)

    def Raggruppa(self):

        if self.ftd.docrag.RowsCount() == 0:
            aw.awu.MsgDialog(self, "Nessun documento estratto")
            return

        cn = self.FindWindowByName
        self.ftd.docgen._firstdat = cn('datdoc').GetValue()
        self.ftd.docgen._firstnum = cn('numdoc').GetValue()

        wait = aw.awu.WaitDialog(
            self, message="Raggruppamento documenti in corso...",
            maximum=self.ftd.docrag.RowsCount())
        try:
            def WaitUpdate(n):
                wait.SetValue(n)
                wx.SafeYield(onlyIfNeeded=True)
            self.ftd.Raggruppa(WaitUpdate)
        except Exception, e:
            wait.Destroy()
            aw.awu.MsgDialog(self, repr(e.args))
            return
        wait.Destroy()
        self.UpdateDocGen()
        self.gridocgen.ChangeData(self.ftd.docgen.GetRecordset())
        cn('workzone').SetSelection(2)

    def OnDatDocChanged(self, event):
        cn = self.FindWindowByName
        if event.GetValue() is not None:
            self.ftd.SetYear(event.GetValue().year)
            cn('datlast').SetValue(self.ftd.docgen._lastdat)
            cn('numlast').SetValue(self.ftd.docgen._lastnum)
            cn('numdoc').SetValue((self.ftd.docgen._lastnum or 0)+1)

    def SetRaggr(self, fdid):

        cn = self.FindWindowByName

        ftd = self.ftd
        try:
            ftd.SetRaggr(fdid)
            enab = True
        except Exception, e:
            aw.awu.MsgDialog(self, repr(e.args))
            enab = False
        for name in 'butest butrag'.split():
            cn(name).Enable(enab)

        cn('desdoc').SetLabel(ftd.tipdoc.descriz)

        l = cn('docs')
        for ddr in ftd.ddr:
            l.Append(ddr.tipdoc.descriz)
            l.Check(l.GetCount()-1)

        for name, value in (('sepall',  ftd.f_sepall == 1),
                            ('sepmp',   ftd.f_sepmp == 1),
                            ('sepdest', ftd.f_sepdest == 1),
                            ('solosta', ftd.f_solosta == 1)):
            c = cn(name)
            if c:
                c.SetValue(value)
            else:
                setattr(self, name, value)

        ct = adb.DbTable(bt.TABNAME_TRACAU, 'tracau', writable=True)
        ct.AddOrder('esclftd')
        ct.AddOrder('codice')
        ct.Retrieve()
        ct.CreateNewRow()
        ct.descriz = 'non definito'
        ct.esclftd = 0
        l = cn('cautra')
        if l:
            for ct in ct:
                l.Append(ct.descriz)
                if ct.esclftd != 1:
                    l.Check(l.GetCount()-1)
        self.dbtracau = ct

        cn('pdc').SetFilter("id_tipo=%d" % ftd.tipdoc.id_pdctip)

    def OnGenera(self, event):
        if self.Genera():
            event.Skip()

    def Genera(self):
        out = False
        if aw.awu.MsgDialog(self, "Confermi la generazione dei documenti?",
                            style=wx.ICON_QUESTION|\
                            wx.YES_NO|wx.NO_DEFAULT) != wx.ID_YES:
            return
        wait = aw.awu.WaitDialog(self, message=
                                 '''Conferma dei documenti generati '''
                                 '''in corso''',
                                 maximum=self.ftd.docgen.RowsCount())
        WaitUpdate = lambda *x: wait.SetValue(self.ftd.docgen.RowNumber())

        wx.BeginBusyCursor()
        try:
            self.ftd.Genera(WaitUpdate)
            wait.Destroy()
            wx.EndBusyCursor()
            aw.awu.MsgDialog(self, 'Raggruppamento terminato', style=wx.ICON_INFORMATION)
            out = True
        except Exception, e:
            wait.Destroy()
            wx.EndBusyCursor()
            aw.awu.MsgDialog(self, repr(e.args))
        return out


# ------------------------------------------------------------------------------


class _FtDif_Mixin:
    def SetRaggr(self, *args, **kwargs):
        self.ftdifpanel.SetRaggr(*args, **kwargs)


# ------------------------------------------------------------------------------


class FtDifFrame(aw.Frame, _FtDif_Mixin):
    """
    Frame Fatturazione differita.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        cn = self.FindWindowByName
        self.ftdifpanel = FtDifPanel(self, -1)
        self.AddSizedPanel(self.ftdifpanel)
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnClose, cn('butconf'))

    def OnClose(self, event):
        self.Close()
        event.Skip()


# ------------------------------------------------------------------------------


class FtDifHistoryGrid(dbglib.DbGrid):
    """
    Griglia documenti elaborazioni precedenti
    """
    def __init__(self, parent, dbdocs):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable documenti (derivati da magazz.dbftd.FtDifHistory)
        """

        size = parent.GetClientSizeTuple()

        self.dbdocs = dbdocs
        d = dbdocs
        d.docrag = d
        g = d.docgen
        g.docgen = g

        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)

        _NUM = gl.GRID_VALUE_NUMBER
        _FLT = bt.GetValIntMaskInfo()
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":True,False"

        cols = (\
            ( 30, (cn(d.cfgrag, 'codice'),  "Cod.",            _STR, True )),\
            (130, (cn(d.cfgrag, 'descriz'), "Doc.Raggruppato", _STR, True )),\
            ( 60, (cn(d.docrag, 'numdoc'),  "Num.",            _NUM, True )),\
            ( 80, (cn(d.docrag, 'datdoc'),  "Data",            _DAT, True )),\
            ( 30, (cn(g.cfggen, 'codice'),  "Cod.",            _STR, True )),\
            (130, (cn(g.cfggen, 'descriz'), "Doc.Generato",    _STR, True )),\
            ( 60, (cn(g.docgen, 'numdoc'),  "Num.",            _NUM, True )),\
            ( 80, (cn(g.docgen, 'datdoc'),  "Data",            _DAT, True )),\
            )

        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False

        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)

        links = None

        afteredit = None
        self.SetData(self.dbdocs.GetRecordset(), colmap, canedit, canins,\
                     links, afteredit)

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


class FtDifHistoryPanel(aw.Panel):

    def __init__(self, *args, **kwargs):

        aw.Panel.__init__(self, *args, **kwargs)
        wdr.FtDifHistoryFunc(self)
        cn = self.FindWindowByName

        self.dbdocs = ftd.FtDifHistory()
        self.dbdocs.ShowDialog(self)

        self.grid = FtDifHistoryGrid(cn('storypangrid'), self.dbdocs)

        self.UpdateGrid()

        self.Bind(wx.EVT_BUTTON, self.OnUpdate, cn('storyupd'))
        self.Bind(wx.EVT_RADIOBOX, self.OnOrder, cn('storyorder'))

    def OnOrder(self, event):
        docs = self.dbdocs
        sel = event.GetEventObject().GetSelection()
        if sel:
            docs.SetOrderGen()
        else:
            docs.SetOrderRag()
        self.UpdateGrid()
        event.Skip()

    def OnUpdate(self, event):
        self.UpdateGrid()
        event.Skip()

    def UpdateGrid(self):
        cn = self.FindWindowByName
        dat1, dat2 = [cn(x).GetValue() for x in 'storydat1 storydat2'.split()]
        docs = self.dbdocs
        docs.ClearFilters()
        if dat1: docs.AddFilter('docrag.datdoc>=%s', dat1)
        if dat2: docs.AddFilter('docrag.datdoc<=%s', dat2)
        if not docs.Retrieve():
            aw.awu.MsgDialog(self, message=repr(docs.GetError()))
            return
        self.grid.ChangeData(docs.GetRecordset())


# ------------------------------------------------------------------------------


class FtDifHistoryFrame(aw.Frame):
    """
    Frame elaborazioni precedenti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Elaborazioni precedenti"
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(FtDifHistoryPanel(self, -1))
        self.CenterOnScreen()
