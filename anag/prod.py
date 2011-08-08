#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/prod.py
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

import MySQLdb
import stormdb as adb

import awc.layout.gestanag as ga
import anag.prod_wdr as wdr

import awc.util as awu
import awc.controls.linktable as lt
import awc.controls.windows as aw

import Env
from awc.controls.linktable import EVT_LINKTABCHANGED
stdcolor = Env.Azienda.Colours

from Env import Azienda
bt = Azienda.BaseTab

import stormdb as adb
import report as rpt

import magazz.dbtables as dbm
dba = dbm.dba

import anag.lib as alib


FRAME_TITLE = "Prodotti"


RSGIAC_CODMAG = 0
RSGIAC_DESMAG = 1
RSGIAC_QTA =    2
RSGIAC_COSTOU = 3
RSGIAC_COSTOM = 4
RSGIAC_TOTCSU = 5
RSGIAC_TOTCSM = 6

class GiacMagGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia giacenze x magazzino
    """
    def __init__(self, parent):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable progressivi x mag. (magazz.dbtables.ProdProgrDaMovimByMag)
        """
        
        size = parent.GetClientSizeTuple()
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        
        cols = (( 40, (RSGIAC_CODMAG, "Cod.",            _STR, True)),
                (180, (RSGIAC_DESMAG, "Magazzino",       _STR, True)),
                (120, (RSGIAC_QTA,    "Giacenza",        _QTA, True)),
                ( 90, (RSGIAC_COSTOM, "Costo Medio",     _PRZ, True)),
                (120, (RSGIAC_TOTCSM, "Tot.CostoMedio",  _PRZ, True)),
                (120, (RSGIAC_TOTCSU, "Tot.CostoUltimo", _PRZ, True)),)
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=size, style=0)
        
        links = None
        afteredit = None
        
        self.SetData([], colmap, canedit, canins, links, afteredit,
                     newRowFunc=None)
        
        self.AddTotalsRow(1, 'Totali', (RSGIAC_QTA, 
                                        RSGIAC_TOTCSU,
                                        RSGIAC_TOTCSM))
        
        #background colors
        self._bgcol0 = stdcolor.GetColour("lemonchiffon")  #prodotto
        self._bgcol1 = stdcolor.GetColour("paleturquoise") #giac.
        self._bgcol2 = stdcolor.GetColour("darkseagreen")  #costo m.
        self._bgcol3 = stdcolor.GetColour("palegreen")     #valori
        #foreground colors
        self._fggneg = stdcolor.GetColour("red")           #giacenza negativa
        self._fggpos = stdcolor.NORMAL_FOREGROUND          #giacenza 0/positiva
        
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(2, 1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

    def GetAttr(self, row, col, rscol, attr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        #if col < 2:
            #bgcol = self._bgcol0
        #elif col == 2:
            #bgcol = self._bgcol1
        #elif col == 3:
            #bgcol = self._bgcol2
        #else:
            #bgcol = self._bgcol3
        if col == RSGIAC_QTA and self.GetTable().GetDataValue(row, col) < 0:
            fgcol = self._fggneg
        else:
            fgcol = self._fggpos
        attr.SetTextColour(fgcol)
        #attr.SetBackgroundColour(bgcol)
        attr.SetReadOnly()
        return attr
    

# ------------------------------------------------------------------------------


class GrigliaPrezziCliForGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia prezzi.
    """
    
    LinkTabAttr = None
    LinkTabDialog = None
    LinkTabDescriz = None
    clifor = None
    idprod = None
    
    def __init__(self, parent, dbgri):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable grigila prezzi
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple(), 
                                              style=0)
        self.dbgri = dbgri
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL
        _PRE = bt.GetMagPreMaskInfo()
        _PRC = bt.GetMagScoMaskInfo()
        _PZC = bt.GetMagPzcMaskInfo()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        gri = dbgri
        pdc = gri.pdc
        
        cols = []
        self.edcols = []
        
        def a(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                self.edcols.append(n)
            return n
        def b(x):
            return a(x, True)
        
        self.COL_anacod =  b(( 50, (cn(pdc, 'codice'),  "Codice",         _STR, True)))
        self.COL_anades =  a((200, (cn(pdc, 'descriz'), "Anagrafica",     _STR, True)))
        self.COL_DATA =    b(( 80, (cn(gri, 'data'),    "Data",           _DAT, True)))
        
        if self.clifor == "C":
            cde = bt.MAGCDEGRIP
        elif self.clifor == "F":
            cde = bt.MAGCDEGRIF
        else:
            raise Exception, "Impossibile determinare se la griglia è per i clienti o per i fornitori"
        if cde:
            self.COL_EXTCOD = b(( 80, (cn(gri, "ext_codice"),  "Codice Ext.",      _STR, False)))
            self.COL_EXTDES = b((200, (cn(gri, "ext_descriz"), "Descrizione Ext.", _STR, False)))
        
        if bt.MAGPZGRIP:
            self.COL_PZCONF = b((70,(cn(gri,'pzconf'),  "Pz.Conf.",       _PZC, True)))
        
        self.COL_PREZZO =  b((110, (cn(gri, 'prezzo'),  "Prezzo griglia", _PRE, True)))
        self.COL_SCONTO1 = b(( 50, (cn(gri, 'sconto1'), "Sc.%1",          _PRC, True)))
        self.COL_SCONTO2 = b(( 50, (cn(gri, 'sconto2'), "Sc.%2",          _PRC, True)))
        self.COL_SCONTO3 = b(( 50, (cn(gri, 'sconto3'), "Sc.%3",          _PRC, True)))
        self.COL_ID_GRIP = a((  1, (cn(gri, 'id'),      "#gri",           _STR, True)))
        self.COL_ID_PDC =  a((  1, (cn(pdc, 'id'),      "#pdc",           _STR, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = canins = True
        
        links = []
        ltpdc = self.LinkTabAttr(bt.TABNAME_PDC,     #table
                                 self.COL_anacod,    #grid col
                                 cn(gri, 'id_pdc'),  #rs col id
                                 cn(pdc, 'codice'),  #rs col cod
                                 cn(pdc, 'descriz'), #rs col des
                                 self.LinkTabDialog, #card class
                                 refresh=True)       #refresh flag
        links.append(ltpdc)
        
        afteredit = ((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.EditedValues),)
        
        self.SetData([], colmap, canedit, canins, links, afteredit, self.CreateNewRow)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnRightClick)
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnDblClick)
    
    def EditedValues(self, row, gridcol, col, value):
        dbgrip = self.dbgri
        if 0 <= row < dbgrip.RowsCount():
            dbgrip.MoveRow(row)
            dbgrip.data = dbgrip.data #forza la scrittura della riga
        return True
    
    def OnRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < self.dbgri.RowsCount():
            self.MenuPopup(event)
            event.Skip()
    
    def OnDblClick(self, event):
        gri = self.dbgri
        sr = self.GetSelectedRows()
        row = sr[0]
        if 0 <= row < gri.RowsCount():
            gri.MoveRow(row)
            self.ApriSchedaPdc()
        event.Skip()
    
    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        if not 0 <= row < self.dbgri.RowsCount():
            return
        self.dbgri.MoveRow(row)
        self.SetGridCursor(row, col)
        self.SelectRow(row)
        gri = self.dbgri
        pdcok = gri.id_pdc is not None
        voci = []
        voci.append(("Apri la scheda del %s" % self.LinkTabDescriz, 
                     self.OnSchedaPdc, pdcok))
        voci.append(("Elimina il %s dalla griglia" % self.LinkTabDescriz.lower(),
                     self.OnDeleteRow,  True))
        menu = wx.Menu()
        for text, func, enab in voci:
            id = wx.NewId()
            menu.Append(id, text)
            menu.Enable(id, enab)
            self.Bind(wx.EVT_MENU, func, id=id)
        xo, yo = event.GetPosition()
        self.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()
    
    def OnSchedaPdc(self, event):
        self.ApriSchedaPdc()
        event.Skip()
    
    def ApriSchedaPdc(self):
        pdcid = self.dbgri.id_pdc
        f = None
        try:
            wx.BeginBusyCursor()
            f = self.LinkTabDialog(self, onecodeonly=pdcid)
            f.OneCardOnly(pdcid)
            f.CenterOnScreen()
        finally:
            wx.EndBusyCursor()
        f.ShowModal()
        if f is not None:
            f.Destroy()
    
    def OnDeleteRow(self, event):
        sr = self.GetSelectedRows()
        if sr:
            row = sr[-1]
            gri = self.dbgri
            if 0 <= row < gri.RowsCount():
                gri.MoveRow(row)
                if gri.id is not None:
                    if not gri.id in gri._info.deletedRecords:
                        #riga già esistente, marco per cancellazione da db
                        gri._info.deletedRecords.append(gri.id)
                #elimino riga da dbgrid
                self.DeleteRows(row)
                gri._info.recordCount -= 1
                if gri._info.recordNumber >= gri._info.recordCount:
                    gri._info.recordNumber -= 1
                    gri._UpdateTableVars()
                #after deletion, record cursor is on the following one
                #so for iterations we decrement iteration index and count
                gri._info.iterIndex -= 1
                gri._info.iterCount -= 1
                self.Refresh()
        event.Skip()
    
    def SetProdId(self, idprod):
        self.idprod = idprod
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly(not col in self.edcols)
        return attr

    def GridListTestValues(self, row, gridcol, col, value):
        out = True
        return out
    
    def CreateNewRow(self):
        g = self.dbgri
        g.CreateNewRow()
        g.id_prod = self.idprod
        if bt.MAGDATGRIP:
            g.data = Env.Azienda.Login.dataElab
        return True


# ------------------------------------------------------------------------------


class GrigliaPrezziClientiGrid(GrigliaPrezziCliForGrid):
    from anag.clienti import ClientiDialog
    LinkTabAttr = alib.LinkTabClienteAttr
    LinkTabDialog = ClientiDialog
    LinkTabDescriz = "Cliente"
    clifor = "C"


# ------------------------------------------------------------------------------


class GrigliaPrezziFornitoriGrid(GrigliaPrezziCliForGrid):
    from anag.fornit import FornitDialog
    LinkTabAttr = alib.LinkTabFornitAttr
    LinkTabDialog = FornitDialog
    LinkTabDescriz = "Fornitore"
    clifor = "F"


# ------------------------------------------------------------------------------


#colonne da listini attuail magazz.dbtables.ListiniAttuail
RSLISTATT_LISTID =     0
RSLISTATT_LISTCOD =    1
RSLISTATT_LISTDES =    2
RSLISTATT_IMPONIBILE = 3
RSLISTATT_IVATO =      4
RSLISTATT_SCONTOPREP = 5
RSLISTATT_RICARICA =   6
RSLISTATT_SCONTOLIS1 = 7
RSLISTATT_GUADAGNO =   8


class ListAttGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia listini in vigore
    """
    def __init__(self, parent):
        """
        Parametri:
        parent griglia  (wx.Panel)
        """
        
        self.dblistatt = dbm.ListiniAttuali()
        
        size = parent.GetClientSizeTuple()
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL
        _PRZ = bt.GetMagPreMaskInfo()
        _PRC = bt.GetMagScoMaskInfo()
        
        cols = (#(30, (RSLISTATT_LISTCOD,    "Cod.",    _STR, True)),
                (100, (RSLISTATT_LISTDES,    "Listino", _STR, True)),
                (110, (RSLISTATT_IMPONIBILE, "Prezzo",  _PRZ, True)),
                (110, (RSLISTATT_IVATO,      "Ivato",   _PRZ, True)),
                ( 50, (RSLISTATT_SCONTOPREP, "Sc.PP%",  _PRC, True)),
                ( 50, (RSLISTATT_SCONTOLIS1, "Sc.L1%",  _PRC, True)),
                ( 50, (RSLISTATT_RICARICA,   "Ri.CA%",  _PRC, True)),
                ( 50, (RSLISTATT_GUADAGNO,   "Gu.CA%",  _PRC, True)),
                )
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=size, style=0)
        
        links = None
        afteredit = None
        
        self.SetData([], colmap, canedit, canins, links, afteredit,
                     newRowFunc=None)
        
        #background colors
        self._bgcols = (stdcolor.GetColour("lightcyan3"),
                        stdcolor.GetColour("wheat3"))
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(2, 0)
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

    def GetAttr(self, row, col, rscol, attr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        #bgcol = self._bgcols[row%2]
        #attr.SetTextColour(fgcol)
        #attr.SetBackgroundColour(bgcol)
        attr.SetReadOnly()
        return attr
    
    def Update(self, idprod):
        lisatt = self.dblistatt
        if bt.MAGDATLIS:
            data = Env.Azienda.Login.dataElab
        else:
            data = None
        lisatt.Determina(idprod, data)
        self.ChangeData(lisatt.GetRecordset())


# ------------------------------------------------------------------------------


class ProdSearchResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRZ = bt.GetMagPreMaskInfo()
        _QTA = bt.GetMagQtaMaskInfo()
        
        def cn(col):
            return self.db._GetFieldIndex(col)
        tab = self.tabalias
        
        cols = [(100, (cn('prod_codice'),    "Cod.",         _STR, True)),
                ( 40, (cn('tipart_codice'),  "Tipo",         _STR, True)),
                (270, (cn('prod_descriz'),   "Descrizione",  _STR, True)),]
        
        cols.append(( 50, (cn('pdc_codice'),  "Cod.",        _STR, True)))
        cols.append((210, (cn('pdc_descriz'), "Fornitore",   _STR, True)))
        
        if bt.MAGVISCPF:
            cols.append((115, (cn('prod_codfor'),  "Cod.Fornit.", _STR, True)))
        
        if bt.MAGVISBCD:
            cols.append((115, (cn('prod_barcode'), "Barcode",     _STR, True)))
        
        if bt.MAGVISCOS:
            cols.append((100, (cn('prod_costo'),   "Costo",       _PRZ, True)))
        
        if bt.MAGVISPRE:
            cols.append((100, (cn('prod_prezzo'),  "Prezzo",      _PRZ, True)))
        
        if bt.MAGVISGIA:
            cols.append((100, (cn('prod_totgiac'), "Giacenza",    _QTA, True)))
        
        cols += [( 40, (cn('catart_codice'),  "Cod.",        _STR, True)),
                 (120, (cn('catart_descriz'), "Categoria",   _STR, True)),
                 ( 40, (cn('gruart_codice'),  "Cod.",        _STR, True)),
                 (120, (cn('gruart_descriz'), "Gruppo",      _STR, True)),
                 ( 40, (cn('marart_codice'),  "Cod.",        _STR, True)),
                 (200, (cn('marart_descriz'), "Marca",       _STR, True)),]
        
        cols += [(1, (cn('prod_id'),   "#pro", _STR, True)),
                 (1, (cn('tipart_id'), "#tip", _STR, True)),
                 (1, (cn('catart_id'), "#cat", _STR, True)),
                 (1, (cn('gruart_id'), "#gru", _STR, True)),
                 (1, (cn('pdc_id'),    "#for", _STR, True)),
                 (1, (cn('marart_id'), "#mar", _STR, True)),]
        
        return cols
    
    def SetColumn2Fit(self):
        self.SetFitColumn(2)


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        
        id_prod = kwargs.pop('id_prod')
        tipana = kwargs.pop('tipana')
        if tipana == "C":
            self._desana = "Cliente"
        else:
            self._desana = "Fornitore"
        
        wx.Panel.__init__(self, *args, **kwargs)
        
        import magazz.listini_wdr as liswdr
        liswdr.VediPrezziInVigoreFunc(self)
        
        import magazz.stagrip as stagrip
        self.dbgrip = stagrip.dba.TabProdGrigliaPrezziAttualiProdTable()
        self.dbgrip.SetParam(Env.Azienda.Login.dataElab, id_prod, tipana)
        self.dbgrip.Retrieve()
        
        def cn(x):
            return self.FindWindowByName(x)
        
        self.gridlis = stagrip.GrigliaPrezziAttualiProdottoGrid(cn('pangridlist'), 
                                                                self.dbgrip)
        
        self.Bind(wx.EVT_BUTTON, self.OnPrint, cn('butprint'))
    
    def OnPrint(self, event):
        self.dbgrip._datlis = Env.Azienda.Login.dataElab
        self.dbgrip._desana = self._desana
        rpt.Report(self, self.dbgrip, "Griglia prezzi in vigore del prodotto")
        event.Skip()


# ------------------------------------------------------------------------------


class GrigliaPrezziAttualiDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        id_prod = kwargs.pop('id_prod')
        tipana = kwargs.pop('tipana')
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GrigliaPrezziAttualiPanel(self, id_prod=id_prod,
                                                     tipana=tipana))


# ------------------------------------------------------------------------------


class DatiPromoPanel(wx.Panel):
    
    id_promo = None
    
    def __init__(self, *args, **kwargs):
        assert 'id_promo' in kwargs
        self.id_promo = kwargs.pop('id_promo')
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.DatiPromoFunc(self)
        def cn(x):
            return self.FindWindowByName(x)
        self.dbpromo = prm = dba.ProdPromo()
        if self.id_promo is None:
            prm.Reset()
        else:
            prm.Get(self.id_promo)
        for name in prm.GetFieldNames():
            c = cn(name)
            if c:
                c.SetValue(getattr(prm, name))
        for name, func in (('butsavepromo', self.OnSavePromo),
                           ('butcancpromo', self.OnDeletePromo)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnDeletePromo(self, event):
        if awu.MsgDialog(self, "Confermi la cancellazione di questa promozione?",
                         style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
            if self.DeletePromo():
                event.Skip()
    
    def DeletePromo(self):
        prm = self.dbpromo
        prm.Delete()
        if not prm.Save():
            aw.awu.MsgDialog(self, repr(prm.GetError()))
            return False
        return True

    def OnSavePromo(self, event):
        if self.Validate():
            if self.SavePromo():
                event.Skip()
    
    def Validate(self):
        out = False
        def cn(x):
            return self.FindWindowByName(x)
        prm = self.dbpromo
        if prm.id is None:
            awu.MsgDialog(self, "Promo non definita")
        elif prm.id_prod is None:
            awu.MsgDialog(self, "Prodotto non definito")
        else:
            if cn('prezzo').GetValue():
                out = True
            else:
                awu.MsgDialog(self, "Definire il prezzo promo")
        return out
    
    def SavePromo(self):
        out = False
        def cn(x):
            return self.FindWindowByName(x)
        prm = self.dbpromo
        prm.prezzo = cn('prezzo').GetValue()
        for name in 'sconto1 sconto2 sconto3'.split():
            setattr(prm, name, cn(name).GetValue())
        if prm.Save():
            out = True
        else:
            aw.awu.MsgDialog(self, repr(prm.GetError()))
        return out

    
# ------------------------------------------------------------------------------


class DatiPromoDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        assert 'id_promo' in kwargs
        id_promo = kwargs.pop('id_promo')
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(DatiPromoPanel(self, id_promo=id_promo))
        self.CenterOnParent()
        def cn(x):
            return self.FindWindowByName(x)
        for name, func in (('butsavepromo', self.OnClose),
                           ('butcancpromo', self.OnClose)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnClose(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class ProdPanel(ga.AnagPanel):
    """
    Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( Azienda.BaseTab.tabelle[
                         Azienda.BaseTab.TABSETUP_TABLE_PROD ] )
        
        self.flt_catart = None
        self.flt_gruart = None
        self.flt_tipart = None
        self.flt_marart = None
        self.flt_fornit = None
        
        self.SetDbOrderColumns((
            ("Codice",              ('prod.codice',)),
            ("Tipo/Descrizione",    ('tipart.codice', 'prod.descriz',)),
            ("Categoria/Gruppo",    ('catart.codice', 'gruart.codice', 'prod.codice',)),
            ("Fornitore/Cod.Forn.", ('pdc.descriz',   'prod.codfor',   'prod.codice',)),
            ("Fornitore/Barcode",   ('pdc.descriz',   'prod.barcode',  'prod.codice',)),
            ("Marca",               ('marart.codice', 'prod.codice',)),
            ("Marca/Cod.Forn.",     ('marart.codice', 'prod.codfor',   'prod.codice',)),
            ("Marca/Barcode",       ('marart.codice', 'prod.barcode',  'prod.codice',)),
            ("Cod.Forn.",           ('prod.codfor',   'prod.codice',)),
            ("Barcode",             ('prod.barcode',  'prod.codice',)),
        ))
        
        #self._sqlrelcol += ', prod.codfor AS "prod_codfor", prod.barcode  AS "prod_barcode"'
        self._sqlrelcol += ', catart.id, catart.codice, catart.descriz'
        self._sqlrelcol += ', gruart.id, gruart.codice, gruart.descriz'
        self._sqlrelcol += ', tipart.id, tipart.codice, tipart.descriz'
        self._sqlrelcol += ', marart.id, marart.codice, marart.descriz'
        self._sqlrelcol += ', pdc.id, pdc.codice, pdc.descriz'
        
        self._sqlrelfrm =\
            " LEFT JOIN %s AS tipart ON %s.id_tipart=tipart.id"\
            " LEFT JOIN %s AS catart ON %s.id_catart=catart.id"\
            " LEFT JOIN %s AS gruart ON %s.id_gruart=gruart.id"\
            " LEFT JOIN %s AS pdc    ON %s.id_fornit=pdc.id"\
            " LEFT JOIN %s AS marart ON %s.id_marart=marart.id"\
            " LEFT JOIN %s AS status ON %s.id_status=status.id"\
            % (bt.TABNAME_TIPART,  bt.TABNAME_PROD,
               bt.TABNAME_CATART,  bt.TABNAME_PROD,
               bt.TABNAME_GRUART,  bt.TABNAME_PROD,
               bt.TABNAME_PDC,     bt.TABNAME_PROD,
               bt.TABNAME_MARART,  bt.TABNAME_PROD,
               bt.TABNAME_STATART, bt.TABNAME_PROD,)
        
        self.db_tabprefix = "%s." % bt.TABNAME_PROD
        
        self._valfilters['tipart'] =  ['tipart.codice', None, None]
        self._valfilters['catart'] =  ['catart.codice', None, None]
        self._valfilters['gruart'] =  ['gruart.codice', None, None]
        self._valfilters['fornit'] =  ['pdc.descriz',   None, None]
        self._valfilters['marart'] =  ['marart.codice', None, None]
        self._valfilters['statart'] = ['status.codice', None, None]
        self._hasfilters = True
        
        self.dblis = adb.DbTable("listini", "list", writable=True)
        self.dblis.AddOrder("list.data", orderType=adb.ORDER_DESCENDING)
        self.gridlist = None
        self._glist_rsdel = []
        
        if bt.MAGPPROMO:
            self.dbpromo = dba.ProdPromo()
        else:
            self.dbpromo = None
        
        self.loadrelated = None
        
        self.dbmag = dba.TabMagazz()
        self.dbmag.Retrieve()
        
        self.dbppm = dbm.ProdProgrDaMovimByMag()
        self.dbpro = dbm.Prodotti()
        
        self.giacmaggrid = None
        self.listattgrid = None
        
        self.ricar = 0
        
        self.dbgrc = None
        self.dbgrf = None
        for n in range(2):
            gri = adb.DbTable(bt.TABNAME_GRIGLIE, 'gri')
            pdc = gri.AddJoin(bt.TABNAME_PDC,     'pdc')
            tip = pdc.AddJoin(bt.TABNAME_PDCTIP,  'tipo')
            gri.AddOrder('pdc.descriz')
            gri.AddOrder('gri.data', adb.ORDER_DESCENDING)
            gri.Get(-1)
            if n == 0:
                self.dbgrc = gri
            else:
                self.dbgrf = gri
        
        self.gridgrc = None
        self.gridgrf = None
        
        setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')
        if setup.Retrieve('chiave=%s', 'magricpre') and setup.OneRow():
            self.ricar = setup.importo or 0
        
        self.db_report = "Prodotti"
        
        self.Bind(lt.EVT_LINKTABCHANGED, self.OnGruPrezChanged, id=wdr.ID_GRUPREZ)
        
        self.HelpBuilder_SetDir('anag.prod')
    
    def GetLinkTableClass(self):
        return alib.LinkTableProd
    
    def InitAnagToolbar(self, parent):
        if bt.MAGVISGIA:
            p = wx.Panel(parent)        
            tb = ga.AnagToolbar(p, wdr.ID_PROD_TOOLBAR, hide_ssv=False)
            ltmag = alib.LinkTableMagazz(p, wdr.ID_GIAC_SELMAG, 'giacmag')
#            import magazz
#            ltmag.SetValue(magazz.GetDefaultMagazz())
            wdr.ProdToolBarFunc(p)#, False, False)
            self.Bind(EVT_LINKTABCHANGED, self.OnUpdateSearch, ltmag)
            self.Bind(wx.EVT_CHECKBOX, self.OnUpdateSearch, self.FindWindowByName('sologiac'))
        else:
            p = ga.AnagToolbar(parent, wdr.ID_PROD_TOOLBAR, hide_ssv=False)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnSSV)
        return p
    
    def OnSSV(self, event):
        self.UpdateSearch()
        event.Skip()
    
    def GetSqlSearch(self):
        _sqlrelfrm = self._sqlrelfrm
        cmd = "SELECT %s FROM %s%s%s"\
              % (self.GetSqlColumns().replace('~',''), self.db_schema, self.db_tabname, _sqlrelfrm)
        par = []
        return cmd, par
    
    def GetSqlColumns(self):
        fields = ''
        for col,ctr in self.db_datalink:
            fields += '%s.%s AS "%s_%s", ' % (self.db_tabname, col, 
                                              self.db_tabname, col)
        fields = fields[:-2]
        fields += self._sqlrelcol
        if bt.MAGVISGIA:
            fields += ', (%s) ~AS prod_totgiac' % self.GetGiacQuery()
        else:
            fields += ', NULL ~AS prod_totgiac'
        return fields
    
    def GetGiacQuery(self):
        ppfilt = ""
        c = self.FindWindowByName('giacmag')
        if c:
            magid = c.GetValue()
            if magid is not None:
                ppfilt = " AND pp.id_magazz=%s" % magid
        giac_query =\
        """SELECT SUM(pp.ini+pp.car-pp.sca)
             FROM %s pp
            WHERE pp.id_prod=%s.id %s""" % (bt.TABNAME_PRODPRO,
                                            self.db_tabname,
                                            ppfilt)
        return giac_query
    
    def OnGruPrezChanged(self, event):
        self.UpdateButtonRicalcCP()
        event.Skip()
    
    def UpdateButtonRicalcCP(self):
        
        pro = self.dbpro
        gpr = pro.gruprez
        
        pro.Reset()
        pro.CreateNewRow()
        pro.id_gruprez = self.FindWindowById(wdr.ID_GRUPREZ).GetValue()
        
        def cascade_perc(p, v):
            if v:
                if p:
                    p += '+'
                p += str(v)
            return p
        
        cn = self.FindWindowByName
        def cnv(x):
            return cn(x).GetValue()
        
        p_cst, p_prz, p_sc1, p_sc2, p_sc3, p_rc1, p_rc2, p_rc3 =\
        map(cnv, 'costo prezzo sconto1 sconto2 sconto3 ricar1 ricar2 ricar3'.split())
        
        def cpv(x):
            return getattr(gpr, x)
        
        g_sc1, g_sc2, g_sc3, g_rc1, g_rc2, g_rc3 =\
        map(cpv, 'prcpresco1 prcpresco2 prcpresco3 prccosric1 prccosric2 prccosric3'.split())
        
        if gpr.calcpc == 'C' or (p_sc1 or p_sc2 or p_sc3):
            label = 'Ric.Costo'
            s_prezzo = pro.sepnpr(p_prz)
            s_sconti = ''
            if p_sc1 or p_sc2 or p_sc3:
                s_sconti = cascade_perc(s_sconti, p_sc1)
                s_sconti = cascade_perc(s_sconti, p_sc2)
                s_sconti = cascade_perc(s_sconti, p_sc3)
                s_qualisconti = 'prodotto'
            else:
                s_sconti = cascade_perc(s_sconti, g_sc1)
                s_sconti = cascade_perc(s_sconti, g_sc2)
                s_sconti = cascade_perc(s_sconti, g_sc3)
                s_qualisconti = 'gruppo prezzi'
            tt = 'Ricalcola il costo, applicando al prezzo di %(s_prezzo)s lo sconto del %(s_sconti)s%% come indicato sul %(s_qualisconti)s' % locals()
            
        elif gpr.calcpc == 'P' or (p_rc1 or p_rc2 or p_rc3):
            label = 'Ric.Prezzo'
            s_costo = pro.sepnpr(p_cst)
            s_ricar = ''
            if p_rc1 or p_rc2 or p_rc3:
                s_ricar = cascade_perc(s_ricar, p_rc1)
                s_ricar = cascade_perc(s_ricar, p_rc2)
                s_ricar = cascade_perc(s_ricar, p_rc3)
                s_qualiricar = 'prodotto'
            else:
                s_ricar = cascade_perc(s_ricar, g_rc1)
                s_ricar = cascade_perc(s_ricar, g_rc2)
                s_ricar = cascade_perc(s_ricar, g_rc3)
                s_qualiricar = 'gruppo prezzi'
            tt = 'Ricalcola il prezzo al pubblico, applicando al costo di %(s_costo)s la ricarica del %(s_ricar)s%% come indicato sul %(s_qualiricar)s' % locals()
        else:
            label = ''
            tt = ''
        
        b = self.FindWindowById(wdr.ID_BTNRICALC)
        b.SetLabel(label)
        b.Enable(bool(label))
        b.SetToolTipString(tt)
    
    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.ProdCardFunc( p, True )
        def cn(x):
            return self.FindWindowByName(x)
        if bt.MAGNUMLIS == 0:
            cn('btnriclis').Hide()
#            if not bt.MAGATTGRIP and not bt.MAGATTGRIF:
#                cn('workzone').RemovePage(1)
        cn('_btnattach').SetAutoScan()
        self.Bind(wx.EVT_BUTTON, self.OnGeneraBarcode, id=wdr.ID_GENBC)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnTestImmagine, id=wdr.ID_NOTEFOTOZONE)
#        for name, func in (('_calcprezzo', self.OnRicalcPrezzo),
#                           ('_calccosto',  self.OnRicalcCosto)):
#            self.Bind(wx.EVT_BUTTON, func, cn(name))
        for name in 'costo prezzo sconto1 sconto2 sconto3 ricar1 ricar2 ricar3'.split():
            self.Bind(wx.EVT_TEXT, self.OnUpdateButtonRicalcCP, cn(name))
        return p
    
    def OnUpdateButtonRicalcCP(self, event):
        self.UpdateButtonRicalcCP()
        event.Skip()
    
#    def OnRicalcPrezzo(self, event):
#        self.RicalcolaPC('prezzo')
#        event.Skip()
#    
#    def OnRicalcCosto(self, event):
#        self.RicalcolaPC('costo')
#        event.Skip()
#    
#    def RicalcolaPC(self, elemento):
#        
#        #ricalcola costo/prezzo mediante dati da scheda (prezzo,costo,sconti,ricariche)
#        #in maniera indipendente dal gruppo prezzi
#        
#        cn = self.FindWindowByName
#        ND = Env.Azienda.BaseTab.MAGPRE_DECIMALS
#        
#        if elemento == 'prezzo':
#            cs, r1, r2, r3 = map(lambda x: cn(x).GetValue() or 0,
#                                 'costo ricar1 ricar2 ricar3'.split())
#            pr = round(cs*(100+r1)/100*(100+r2)/100*(100+r3)/100, ND)
#            cn('prezzo').SetValue(pr)
#            
#        elif elemento == 'costo':
#            pr, s1, s2, s3 = map(lambda x: cn(x).GetValue() or 0,
#                                 'prezzo sconto1 sconto2 sconto3'.split())
#            cs = round(pr*(100-s1)/100*(100-s2)/100*(100-s3)/100, ND)
#            cn('costo').SetValue(cs)
#            
#        else:
#            raise Exception, "Tipo di ricalcolo non riconosciuto"
#    
    def OnTestImmagine(self, event):
        self.TestImmagine()
        event.Skip()
    
    def OnGeneraBarcode(self, event):
        self.GeneraBarcode()
        event.Skip()
    
    def GeneraBarcode(self):
        if bt.MAGEAN_PREFIX is None or len(bt.MAGEAN_PREFIX)<1:
            awu.MsgDialog(self, message=\
                          """Prefisso EAN (Country Code) errato.\nVerificare """
                          """il setup dell'azienda.""")
            return
        def cn(x):
            return self.FindWindowByName(x)
        bc = cn('barcode')
        if bc.GetValue():
            awu.MsgDialog(self, message=\
                          """Il barcode è già presente, il calcolo di un """
                          """nuovo codice a barre avviene solo in assenza di """
                          """un valore codificato.""")
            return
        bc.SetValue(self.dbpro.GetNewEAN13code('barcode', bt.MAGEAN_PREFIX))
    
    def PrintEtichette(self):
        import magazz.invent as inv
        dlg = inv.bcode.SelQtaDialog(self)
        do = dlg.ShowModal() == wx.ID_OK
        dlg.Destroy()
        if not do:
            return
        db = dbm.ProdEticList()
        db.CreateNewRow()
        db.id = self.db_recid
        db.qtaetic = dlg.GetQta(self.dbppm.total_giac)
        dlg.Destroy()
        if db.qtaetic>0:
            def GetPrintTable(rptdef, _rpt):
                rows = cols = 1
                if '(' in rptdef:
                    x = rptdef[rptdef.rindex('(')+1:]
                    if x.endswith(')'):
                        x = x[:-1]
                    if 'x' in x:
                        rows, cols = map(int,x.split('x'))
                row0 = _rpt.GetLabelOffsetRow()
                col0 = _rpt.GetLabelOffsetCol()
                return db.GetPrintTable(rptdef, rows, cols, row0, col0)
            rpt.ReportLabels(self, None, 'Etichette prodotti', 
                             dbfunc=GetPrintTable)
    
    def GetSearchResultsGrid(self, parent):
        grid = ProdSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                     self.db_tabname, self.GetSqlColumns())
        return grid
    
    def InitControls(self, *args, **kwargs):
        self.loadrelated = False
        ga.AnagPanel.InitControls(self, *args, **kwargs)
        self.loadrelated = True
        
        ci = lambda x: self.FindWindowById(x)
        ci(wdr.ID_STETIC).SetDataLink('stetic', {True: 1, False: 0})
        self.giacmaggrid = GiacMagGrid(ci(wdr.ID_PANGRIDGIAC))
        if bt.MAGNUMLIS>0:
            self.listattgrid = ListAttGrid(ci(wdr.ID_PANGRIDLATT))
        if bt.MAGATTGRIP:
            self.gridgrc = GrigliaPrezziClientiGrid(ci(wdr.ID_PANGRIDGRC), self.dbgrc)
            self.Bind(wx.EVT_BUTTON, self.OnPrintGriglieAttualiCli, ci(wdr.ID_BUTVEDIPREVIGCLI))
        if bt.MAGATTGRIF:
            self.gridgrf = GrigliaPrezziFornitoriGrid(ci(wdr.ID_PANGRIDGRF), self.dbgrf)
            self.Bind(wx.EVT_BUTTON, self.OnPrintGriglieAttualiFor, ci(wdr.ID_BUTVEDIPREVIGFOR))
        self.GridList_Init()
        
        tip = adb.DbTable(bt.TABNAME_PDCTIP, 'tipana')
        tip.Retrieve('tipana.tipo="F"')
        ci(wdr.ID_CTRFORNIT).SetFilter('id_tipo IN (%s)' \
                                       % ','.join([str(x.id) for x in tip]))
        
        self.UpdateDataControls()
        
        self.Bind(wx.EVT_CHECKBOX, self.OnStEtic, id=wdr.ID_STETIC)
        
        self.Bind(wx.EVT_BUTTON, self.OnRicalc, id=wdr.ID_BTNRICALC)
        self.Bind(wx.EVT_BUTTON, self.OnRicalcListini, id=wdr.ID_BTNRICLIS)
        
        self.Bind(ga.linktable.EVT_LINKTABCHANGED, self.OnCatArtChanged,
                  id=wdr.ID_CTRCATART)
        
        self.Bind(wx.EVT_BUTTON, self.OnPrintEtic, id=wdr.ID_PRINTBC)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        if bt.MAGPPROMO:
            self.Bind(wx.EVT_BUTTON, self.OnPromoChange, cn('_promobutton'))
    
    def OnPrintGriglieAttualiCli(self, event):
        self.VediGriglieAttualiCli()
        event.Skip()
    
    def OnPrintGriglieAttualiFor(self, event):
        self.VediGriglieAttualiFor()
        event.Skip()
    
    def VediGriglieAttualiCli(self):
        self.VediGriglieAttuali(tipana="C")
    
    def VediGriglieAttualiFor(self):
        self.VediGriglieAttuali(tipana="F")
    
    def VediGriglieAttuali(self, tipana):
        def cn(x):
            return self.FindWindowByName(x)
        title = "Griglia prezzi in vigore del prodotto %s" % cn('codice').GetValue()
        d = GrigliaPrezziAttualiDialog(self, title=title, id_prod=self.db_recid, tipana=tipana)
        c = d.FindWindowByName('elencotitle')
        if tipana == "C":
            c.SetLabel("Elenco Clienti")
        elif tipana == "F":
            c.SetLabel("Elenco Fornitori")
        d.CenterOnScreen()
        d.ShowModal()
        d.Destroy()
    
    def GetSqlFilter(self):
        fltexp, fltpar = ga.AnagPanel.GetSqlFilter(self)
        if bt.MAGVISGIA:
            m = self.FindWindowByName('giacmag')
            if m:
                c = self.FindWindowByName('sologiac')
                if c:
                    if c.IsChecked():
                        if fltexp:
                            fltexp += ' AND '
                        fltexp += '(%s)<>0' % self.GetGiacQuery()
        return fltexp, fltpar
    
    def GetSqlFilterSearch(self):
        cn = self.FindWindowByName
        #filtro di base, non visuale e impostato dalla sottoclasse
        filter = self.db_searchfilter or ''
        #filtro per inclusione/esclusione elementi con status nascosto
        if cn('_ssv').GetValue():
            flt = "status.hidesearch IS NULL or status.hidesearch<>1"
            if filter:
                filter = "(%s) AND " % filter
            filter += "(%s)" % flt
        par = []
        val = cn('_searchval').GetValue()
        #filtro in base al valore digitato
        if val:
            #valore digitato nel box di ricerca
            val = val.replace('..', '%')
            tab = self.db_tabname
            #test su codice (inizia con)
            flt = "%s.codice LIKE %%s" % tab
            par.append(val)
            #test su descrizione (inizia con)
            flt += " OR %s.descriz LIKE %%s" % tab
            vx = val
            if not vx.endswith(r'%'):
                vx = vx.rstrip()+r'%'
            par.append(vx)
            if not '%' in val:
                v2 = '%s%%' % val
                flt += " OR %s.codfor LIKE %%s" % tab
                par.append(v2)
                flt += " OR %s.barcode LIKE %%s" % tab
                par.append(v2)
            if filter:
                filter = "(%s) AND " % filter
            filter += "(%s)" % flt
        return filter, par
    
    def OnRicalc(self, event):
        cn = self.FindWindowByName
        pro = self.dbpro
        pro.Reset()
        pro.CreateNewRow()
        gpr = pro.gruprez
        pro.id_gruprez = self.FindWindowById(wdr.ID_GRUPREZ).GetValue()
        for name in 'costo prezzo id_gruprez sconto1 sconto2 sconto3 ricar1 ricar2 ricar3'.split():
            setattr(pro, name, cn(name).GetValue())
        if gpr.calcpc == "C" or (pro.sconto1 or pro.sconto2 or pro.sconto3):
            pro.RicalcolaCosto()
            cn('costo').SetValue(pro.costo)
        elif gpr.calcpc == 'P' or (pro.ricar1 or pro.ricar2 or pro.ricar3):
            pro.RicalcolaPrezzo()
            cn('prezzo').SetValue(pro.prezzo)
        if bt.MAGNUMLIS>0:
            if aw.awu.MsgDialog(self, "Vuoi ricalcolare automaticamente i listini?", style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                self.RicalcolaListini()
        event.Skip()
    
    def OnRicalcListini(self, event):
        self.RicalcolaListini()
        event.Skip()
    
    def RicalcolaListini(self):
        cn = self.FindWindowByName
        pro = self.dbpro
        pro.Reset()
        pro.CreateNewRow()
        for name in 'costo prezzo id_gruprez sconto1 sconto2 sconto3 ricar1 ricar2 ricar3'.split():
            setattr(pro, name, cn(name).GetValue())
        lis = self.dblis
        new = lis.IsEmpty()
        dat = None
        if bt.MAGDATLIS and not new:
            if lis.data != Env.Azienda.Login.dataElab:
                x = aw.awu.MsgDialog(self, "Vuoi ricalcolare il listino più recente (alla data del %s)?\n(Se rispondi 'No', verrà creato un nuovo listino in data odierna)" % pro.dita(lis.data), style=wx.ICON_QUESTION|wx.YES_NO|wx.CANCEL|wx.NO_DEFAULT)
                if x == wx.ID_CANCEL:
                    return
                elif x == wx.ID_NO:
                    new = True
                    dat = Env.Azienda.Login.dataElab
                else:
                    lis.MoveFirst()
            else:
                lis.MoveFirst()
        if new:
            lis.CreateNewRow()
            if dat:
                lis.data = dat
        pro.RicalcolaListini(lis)
        self.gridlist.ResetView()
        self.SetDataChanged()
    
    def OnStEtic(self, event):
        self.TestEnable()
        event.Skip()
    
    def OnPrintEtic(self, event):
        self.PrintEtichette()
        event.Skip()
    
    def OnCatArtChanged( self, event ):
        cat = event.GetEventObject()
        gru = self.FindWindowByName('id_gruart')
        if cat.GetValue() == None:
            gru.SetFilter('1')
            gru.Enable(False)
        else:
            gru.SetFilter('id_catart=%d' % cat.GetValue())
            gru.Enable(True)
        event.Skip()

    def UpdateDataControls(self, *args, **kwargs):
        #tolgo il filtro dal conto di bilancio
        #poiché il filtro presente è stato impostato *prima* di aggiornare i
        #controlli con i valori di questo record, quindi se il mastro del
        #record attuale differisce da quello del record precedente, il filtro
        #impostato sul conto è *errato*
        self.FindWindowByName('id_gruart').SetFilter(None)
        ga.AnagPanel.UpdateDataControls(self, *args, **kwargs)
        if self.giacmaggrid:
            dbmag, dbppm = self.dbmag, self.dbppm
            dbppm.Get(self.db_recid)
            gpm = []
            for mag in dbmag:
                if dbppm.Locate(lambda x: x.mov.doc.mag.codice == mag.codice):
                    g = dbppm.total_giac
                    u = dbppm.Valore(dbm.VALINV_COSTOULTIMO)
                    m = dbppm.Valore(dbm.VALINV_COSTOMEDIO)
                else:
                    g = u = m = 0
                gpm.append((mag.codice,  #RSGIAC_CODMAG
                            mag.descriz, #RSGIAC_DESMAG
                            g,           #RSGIAC_QTA
                            u,           #RSGIAC_COSTOU
                            m,           #RSGIAC_COSTOM
                            g*u,         #RSGIAC_TOTCSU
                            g*m))        #RSGIAC_TOTCSM
            self.giacmaggrid.ChangeData(gpm)
        if bt.MAGPPROMO:
            self.UpdatePromo()
        if self.listattgrid:
            self.listattgrid.Update(self.db_recid)
        if self.loadrelated:
            self.GridListLoad()
            self.gridlist.SetGridCursor(0,0)
            self.GridGriglieLoad()
        self.TestImmagine()
        self.TestEnable()
    
    def UpdatePromo(self):
        prm = self.dbpromo
        r = prm.Retrieve
        p = self.db_recid
        d = Env.Azienda.Login.dataElab
        r("promo.id_prod=%s AND promo.datmin<=%s AND promo.datmax>=%s", p, d, d)
        for name in prm.GetFieldNames():
            c = self.FindWindowByName('_promo_%s' % name)
            if c:
                c.SetValue(getattr(prm, name))
        for name in 'label button'.split():
            self.FindWindowByName('_promo%s' % name).Show(prm.id is not None)
    
    def OnPromoChange(self, event):
        self.PromoChange()
        event.Skip()
    
    def PromoChange(self):
        prm = self.dbpromo
        if prm.id is not None:
            cod = self.FindWindowByName('codice').GetValue()
            dp = DatiPromoDialog(self, title="Promo %s" % cod, id_promo=prm.id)
            if dp.ShowModal() == wx.ID_OK:
                self.UpdatePromo()
            dp.Destroy()
            self.RemoveChild(dp)
    
    def TestImmagine(self):
        def cn(x):
            return self.FindWindowByName(x)
        nb = self.FindWindowById(wdr.ID_NOTEFOTOZONE)
        if nb.GetPageText(nb.GetSelection()) == 'Immagine':
            ba = cn('_btnattach')
            imgpreview = cn('_imagepreview')
            imgpreview.undisplay_image()
            img = ba.GetDefaultImageName()
            if img:
                imgpreview.display_image(img)
    
    def TestEnable(self):
        cid = lambda x: self.FindWindowById(x)
        stetic = cid(wdr.ID_STETIC).GetValue() == 1
        cid(wdr.ID_DESCETIC).Enable(stetic)
        if stetic and not cid(wdr.ID_DESCETIC).GetValue():
            des = cid(wdr.ID_TXT_DESCRIZ).GetValue() or ''
            if len(des)>24:
                des = des[:24]
            cid(wdr.ID_DESCETIC).SetValue(des)
    
    def GridGriglieLoad(self):
        for n, (tipo, gri, ctr) in enumerate((("C", self.dbgrc, self.gridgrc),
                                              ("F", self.dbgrf, self.gridgrf))):
            if ctr is not None:
                if self.db_recid is None:
                    gri.Get(-1)
                else:
                    gri.Retrieve(r'tipo.tipo=%s AND gri.id_prod=%s',
                                 tipo, self.db_recid)
                ctr.ChangeData(gri.GetRecordset())
                ctr.SetProdId(self.db_recid)
    
    def GridGriglieWrite(self):
        for gri, tip in ((self.dbgrc, 'Clienti'),
                         (self.dbgrf, 'Fornitori')):
            if not gri.Save():
                awu.MsgDialog(self, 'Problema in scrittura griglia %s:\n%s'\
                              % (tip, repr(gri.GetError())))
    
    def UpdateDataRecord( self ):
        self.loadrelated = False
        written = ga.AnagPanel.UpdateDataRecord(self)
        self.loadrelated = True
        if written:
            #self.GridListWrite(); self.GridListLoad()
            #self.GridGriglieWrite(); self.GridGriglieLoad()
            self.GridListWrite()
            self.GridGriglieWrite()
            self.LoadFieldsValues()
        return written
    
    def DeleteDataRecord(self):
        recid = self.db_recid
        out = ga.AnagPanel.DeleteDataRecord(self)
        if out and recid is not None:
            cmd = "DELETE FROM %s WHERE id_prod=%%s" % bt.TABNAME_LISTINI
            try:
                self.db_curs.execute(cmd, recid)
            except MySQLdb.Error, e:
                awu.MsgDialogDbError(self, e)
        return out
    
    def GetDb2Print(self, rptdef, *args):
        db = dbm.dba.TabProdotti()
        if bt.MAGVISGIA:
            db.AddField('(%s)' % self.GetGiacQuery(), 'totgiacmag')
            db.Reset()
            d = 'Giac.Tot.'
            c = self.FindWindowByName('giacmag')
            if c:
                if c.GetValue() is not None:
                    d = 'Giac.M.%s' % c.GetValueCod()
            db.SetPrintValue('giacdes', d)
        if self.db_filter:
            db.AddFilter(self.db_filter, *self.db_parms)
        if self.db_filtersexpr:
            db.AddFilter(self.db_filtersexpr, *self.db_filterspars)
        if self.db_orderdirection == 1:
            ot = adb.ORDER_DESCENDING
        else:
            ot = adb.ORDER_ASCENDING
        if 'struttura' in rptdef.lower():
            db.AddOrder('catart.codice', ot)
            db.AddOrder('gruart.codice', ot)
        n = self.GetOrderNumber()
        for of in self.db_ordercolumns[n][1]:
            db.AddOrder(of, ot)
        if not db.Retrieve():
            awu.MsgDialog(self, repr(db.GetError()))
        return db
    
    def PrintLista(self):
        if self.db_report is None: return
        rpt.Report(self, None, self.db_report, dbfunc=self.GetDb2Print)
    
    def GetSpecializedSearchPanel(self, parent):
        p = wx.Panel(parent, -1)
        wdr.ProdSpecSearchFunc(p)
        return p

    def GridList_Init(self):
        #costruzione griglia listini
        parent = self.FindWindowById(wdr.ID_PANGRIDLIS)
        size = parent.GetClientSizeTuple()
        
        _DAT = gl.GRID_VALUE_DATETIME
        _FLT = bt.GetMagPreMaskInfo()
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        
        cols = []
        self.edcols = []
        def a(x, e=False):
            cols.append(x)
            n = len(cols)-1
            if e:
                self.edcols.append(n)
            return n
        def b(x):
            return a(x, True)
        
        def cn(x):
            return self.dblis._GetFieldIndex(x)
        
        if bt.MAGDATLIS:
            self.COL_DATA = b(( 80, (cn('data'),    "Data",        _DAT, True)))
        
        pw = 90
        
        if bt.MAGNUMLIS >= 1:
            self.COL_PRZ1 = b(( pw, (cn('prezzo1'), "Listino #1",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 2:
            self.COL_PRZ2 = b(( pw, (cn('prezzo2'), "Listino #2",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 3:
            self.COL_PRZ3 = b(( pw, (cn('prezzo3'), "Listino #3",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 4:
            self.COL_PRZ4 = b(( pw, (cn('prezzo4'), "Listino #4",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 5:
            self.COL_PRZ5 = b(( pw, (cn('prezzo5'), "Listino #5",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 6:
            self.COL_PRZ6 = b(( pw, (cn('prezzo6'), "Listino #6",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 7:
            self.COL_PRZ7 = b(( pw, (cn('prezzo7'), "Listino #7",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 8:
            self.COL_PRZ8 = b(( pw, (cn('prezzo8'), "Listino #8",  _FLT, True)))
        
        if bt.MAGNUMLIS >= 9:
            self.COL_PRZ9 = b(( pw, (cn('prezzo9'), "Listino #9",  _FLT, True)))
        
        if not bt.MAGDATLIS:
            self.COL_DATA = b(( 80, (cn('data'),    "Data",        _DAT, True)))
        
        self.COL_NOTE = b((200, (cn('note'), "Note", _STR, False)))
        
        self.COL_ID = a((  1, (cn('id'),   "#lis", _STR, False)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = True
        
        links = None
        afteredit = ((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.GridListTestValues),)
        
        grid = dbglib.DbGrid(parent, -1, size=size, style=0)
        grid.SetData( self.dblis._info.rs, colmap, canedit, canins,\
                      links, afteredit, self.GridListAddNewRow )
        grid.SetCellDynAttr(self.GridListGetAttr)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.SetFitColumn(len(cols)-2)
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.gridlist = grid
        
        grid.Bind(gl.EVT_GRID_CELL_CHANGE, self.GridListOnChanged)
        if bt.MAGDATLIS:
            grid.Bind(gl.EVT_GRID_SELECT_CELL, self.GridListOnSelected)
            self.Bind(wx.EVT_BUTTON, self.GridListOnCreate, id=wdr.ID_BTNLISTNEW)
            self.Bind(wx.EVT_BUTTON, self.GridListOnDelete, id=wdr.ID_BTNLISTDEL)

    def GridListGetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        #blocco editazione su cella ID
        lis = self.dblis
        attr.SetReadOnly(not col in self.edcols)
        
        #impostazione colori
        fgcol = stdcolor.NORMAL_FOREGROUND
        bgcol = stdcolor.NORMAL_BACKGROUND
        if 0 <= row < lis.RowsCount():
            lis.MoveRow(row)
            if lis.id in self._glist_rsdel:
                fgcol = stdcolor.DELETED_FOREGROUND
                bgcol = stdcolor.DELETED_BACKGROUND
            #elif not self.GridBodyIsRowOK(row):
                #bgcol = stdcolor.VALERR_BACKGROUND
            elif lis.id is None:
                bgcol = stdcolor.ADDED_BACKGROUND
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        return attr

    def GridListTestValues(self, row, gridcol, col, value):
        out = True
        lis = self.dblis
        lis.MoveRow(row)
        #lis.data = Env.Azienda.Login.dataElab
        lis._UpdateTableVars()
        #if col in (RSLIS_PREZZO1, RSLIS_PREZZO2, RSLIS_PREZZO3,\
                   #RSLIS_PREZZO4, RSLIS_PREZZO5, RSLIS_PREZZO6,\
                   #RSLIS_PREZZO7, RSLIS_PREZZO8, RSLIS_PREZZO9):
            #out = value >= 0
        return out
    
    #def GridListIsRowOK(self, row):
        #valok = True
        #if 0 <= row < self.dbmov.RowsCount():
            #if not self.CfgMovimentoIsValid():
                #return False
            #dbmov = self.dbmov
            #dbmov.MoveRow(row)
            #if dbmov.descriz is None or len(dbmov.descriz.strip()) == 0:
                #return False
            #if self.cfgmov.askvalori in "QT" and dbmov.qta == 0:
                #return False
            #if self.cfgmov.askvalori in "TV" and dbmov.importo == 0:
                #return False
        #return True
    
    def GridListAddNewRow(self):
        if not bt.MAGDATLIS and self.dblis.RowsCount()>0:
            return False
        lis = self.dblis
        lis.MoveNewRow()
        lis.AppendNewRow()
        map(lis._ResetTableVar,\
            'prezzo1,prezzo2,prezzo3,prezzo4,prezzo5,prezzo6,prezzo7,prezzo8,prezzo9'.split(','))
        if bt.MAGDATLIS:
            lis.data = Env.Azienda.Login.dataElab
    
    def GridListOnSelected(self, event):
        row = event.GetRow()
        enable = (0 <= row < self.dblis.RowsCount())
        ctr = self.FindWindowById(wdr.ID_BTNLISTDEL)
        ctr.Enable(enable)
        event.Skip()
    
    def GridListOnChanged(self, event):
        self.SetDataChanged()
    
    def GridListOnCreate(self, event):
        self.GridListAddNewRow()
        self.gridlist.ResetView()
        self.gridlist.SetGridCursor(self.dblis.RowsCount()-1,1)

    def GridListOnDelete(self, event):
        sr = self.gridlist.GetSelectedRows()
        if sr:
            row = sr[-1]
            dblis = self.dblis
            dblis.MoveRow(row)
            if dblis.id is None:
                self.gridlist.DeleteRows(row)
                dblis._info.recordCount -= 1
                if dblis._info.recordNumber >= dblis._info.recordCount:
                    dblis._info.recordNumber -= 1
                dblis._UpdateTableVars()
                #after deletion, record cursor is on the following one
                #so for iterations we decrement iteration index and count
                dblis._info.iterIndex -= 1
                dblis._info.iterCount -= 1
            else:
                if dblis.id in self._glist_rsdel:
                    self._glist_rsdel.remove(dblis.id)
                else:
                    self._glist_rsdel.append(dblis.id)
                self.gridlist.ResetView()
                self.SetDataChanged()
        event.Skip()
    
    def GridListLoad(self):
        self.dblis.ClearFilters()
        self.dblis.AddFilter("id_prod=%s", self.db_recid)
        self.dblis.Retrieve()
        for lis in self.dblis:
            for i in range(9):
                var = 'prezzo%d' % (i+1)
                if getattr(lis, var) is None:
                    setattr(lis, var, 0)
        self.gridlist.ResetView()
        del self._glist_rsdel[:]

    def GridListWrite(self):
        out = False
        dblis = self.dblis
        for recno in range(len(dblis.GetRecordset())):
            dblis.MoveRow(recno)
            dblis.id_prod = self.db_recid
        if dblis.SaveAll():
            cmd = "DELETE FROM %s WHERE id=%%s" % bt.TABNAME_LISTINI
            try:
                self.db_curs.executemany(cmd, self._glist_rsdel)
                out = True
            except MySQLdb.Error, e:
                awu.MsgDialogDbError(self, e)
        return out


# ------------------------------------------------------------------------------


class ProdFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ProdPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_CLOSE, self.OnClose)


# ------------------------------------------------------------------------------


class ProdDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Prodotti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(ProdPanel(self, -1))
        self.CenterOnScreen()
