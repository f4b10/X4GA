#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/caucontab.py
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

import MySQLdb

import awc.layout.gestanag as ga
import cfg.caucontab_wdr as wdr

import awc
import awc.util as awu

from Env import Azienda
bt = Azienda.BaseTab
bc = Azienda.Colours

import awc.controls.windows as aw

import awc.controls.dbgrid as dbglib

import stormdb as adb

from cfg.regiva import RegIvaDialog


MAGREGIVA_ID =          0
MAGREGIVA_MAGAZZ_ID =   1
MAGREGIVA_MAGAZZ_cod =  2
MAGREGIVA_MAGAZZ_desc = 3
MAGREGIVA_REGIVA_ID =   4
MAGREGIVA_REGIVA_cod =  5
MAGREGIVA_REGIVA_desc = 6


FRAME_TITLE = "Causali contabili"


class MagRegIvaGrid(dbglib.DbGrid):
    """
    Griglia definizione registro iva della causale in base al magazzino
    (x dataentry magazzino; x dataentry contab non è contemplata la codifica
    del magazzino, quindi in presenza di causale con registro dinamico viene
    semplicemente attivato il controllo di selezione del registro iva in
    testata registrazione.
    """
    def __init__(self, parent, rsrim):
        """
        Passare:
        parent della griglia
        recordset da gestire: 7-list, vedi costanti MAGREGIVA_*
        """
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), 
                               style=wx.SUNKEN_BORDER)
        
        _STR = gl.GRID_VALUE_STRING
        
        coldef = (\
            ( 50, (MAGREGIVA_MAGAZZ_cod,  "Cod.",         _STR, False)),
            (150, (MAGREGIVA_MAGAZZ_desc, "Magazzino",    _STR, False)),
            ( 50, (MAGREGIVA_REGIVA_cod,  "Cod.",         _STR, False)),
            (150, (MAGREGIVA_REGIVA_desc, "Registro IVA", _STR, False)),
        )
        
        sizes =  [c[0] for c in coldef]
        colmap = [c[1] for c in coldef]
        
        canedit = True
        canins = False
        
        links = []
        lta = dbglib.LinkTabAttr( bt.TABNAME_REGIVA,     #table
                                  2,                     #grid col
                                  MAGREGIVA_REGIVA_ID,   #rs col id
                                  MAGREGIVA_REGIVA_cod,  #rs col cod
                                  MAGREGIVA_REGIVA_desc, #rs col des
                                  RegIvaDialog,          #card class
                                  refresh = True)        #refresh flag
        links.append(lta)
        
        afteredit = ( (dbglib.CELLEDIT_AFTER_UPDATE, -1, self.TestValues), )
        
        self.SetData( rsrim, colmap, canedit, canins, links, afteredit)
        
        self.SetCellDynAttr(self.GetAttr)
        for c,s in enumerate(sizes):
            self.SetColumnDefaultSize(c,s)
        self.SetFitColumn(-1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)

    def TestValues(self, row, gridcol, col, value):
        return True

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        readonly = rscol != MAGREGIVA_REGIVA_cod
        attr.SetReadOnly(readonly)
        #impostazione colori
        fgcol = bc.NORMAL_FOREGROUND
        bgcol = bc.NORMAL_BACKGROUND
        if row % 2 == 1:
            bgcol = bc.GetColour("LIGHT GREY")
        attr.SetTextColour(fgcol)
        attr.SetBackgroundColour(bgcol)
        return attr

    
# ------------------------------------------------------------------------------


def ValidateRsRim(rs):
    err = None
    rp = []
    for r in rs:
        ri = r[MAGREGIVA_REGIVA_ID]
        if not ri:
            err = "Ogni magazzino deve avere un corrispondente registro IVA"
            break
        elif ri in rp:
            err = "I Registri IVA devono essere univoci"
            break
        rp.append(ri)
    if err:
        awu.MsgDialog(None, message=err, style=wx.ICON_ERROR)
        out = False
    else:
        out = True
    return out
    

class MagRegIvaPanel(aw.Panel):
    def __init__(self, *args, **kwargs):
        rs = kwargs.pop('rsrim')
        aw.Panel.__init__(self, *args, **kwargs)
        ci = lambda x: self.FindWindowById(x)
        wdr.MagRegIvaFunc(self)
        grid = MagRegIvaGrid(ci(wdr.ID_PANGRIDMAG), rs)
        self.rs = rs
        self.Bind(wx.EVT_BUTTON, self.OnSave, id=wdr.ID_BTN_MAGRIV_OK)
    
    def OnSave(self, event):
        if self.Validate():
            event.Skip()
    
    def Validate(self):
        assert self.rs is not None
        return ValidateRsRim(self.rs)


# ------------------------------------------------------------------------------


class MagRegIvaDialog(aw.Dialog):
    """
    Dialog Gestione Registri IVA x magazzino.
    """
    def __init__(self, *args, **kwargs):
        assert 'rsrim' in kwargs
        rsrim = kwargs.pop('rsrim')
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = "Registri IVA per magazzino"
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(MagRegIvaPanel(self, -1, rsrim=rsrim))
        ci = lambda x: self.FindWindowById(x)
        for cid, func in ((wdr.ID_BTN_MAGRIV_OK, self.OnOk),):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
    
    def OnOk(self, event):
        self.EndModal(1)
    
    def OnQuit(self, event):
        self.EndModal(0)


# ------------------------------------------------------------------------------


class CauContabSearchResultsTable(ga.dbglib.DbGridTable):
    
    def GetValue(self, row, col):
        value = ga.dbglib.DbGridTable.GetValue(self, row, col)
        if col == self.grid.COL_PRALCF:
            if value == 1:
                value = "+ SOMMA"
            elif value == -1:
                value = "- sottrae"
            else:
                value = ''
        return value


class CauContabSearchResultsGrid(ga.SearchResultsGrid):
    
    tableClass = CauContabSearchResultsTable
    
    def GetDbColumns(self):
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRC = bt.GetPerGenMaskInfo()
        cn = lambda x: self.db._GetFieldIndex(x)
        
        self.COL_PRALCF = 4
        
        return (( 35, (cn('cfgcontab_codice'),  "Cod.",          _STR, True)),
                (240, (cn('cfgcontab_descriz'), "Causale",       _STR, True)),
                ( 35, (cn('regiva_codice'),     "Cod.",          _STR, True)),
                (240, (cn('regiva_descriz'),    "Registro IVA",  _STR, True)),
                (150, (cn('cfgcontab_pralcf'),  "Segno Spesom.", _STR, True)),
                (  1, (cn('cfgcontab_id'),      "#cau",          _STR, True)),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class CauContabPanel(ga.AnagPanel):
    """
    Gestione tabella Causali contabilità.
    """
    def __init__(self, *args, **kwargs):
        
        ga.AnagPanel.__init__(self, *args, **kwargs)
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_CFGCONTAB ] )
        
        self._sqlrelcol += ', regiva.id, regiva.codice, regiva.descriz'
        
        self._sqlrelfrm =\
            " LEFT JOIN %s AS regiva ON regiva.id=cfgcontab.id_regiva" % bt.TABNAME_REGIVA
        
        mag = adb.DbTable(bt.TABNAME_MAGAZZ, 'magazz', writable=False)
        mag.AddOrder('magazz.codice')
        mag.Retrieve()
        self.dbmag = mag
        self.dbrim = adb.DbTable(bt.TABNAME_CFGMAGRIV, 'rim', writable=True)
        self.dbrim.AddJoin(bt.TABNAME_REGIVA, 'regiva')
        self.rsrim = None #recordset x i/o cfgmagriv

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.CauContabCardFunc( p, True )
        cn = lambda x: self.FindWindowByName(x)
        self._pdcpref = cn('panpref')
        for name, val in (("tipo",      "SCIE"),
                          ("datdoc",    " 01"),
                          ("numdoc",    " 01"),
                          ("numiva",    " 01"),
                          ("esercizio", "01"),
                          ("pcfsgn",    "+-"),
                          ("pcfimp",    " 12"),
                          ("pcfabb",    " AP")):
            cn(name).SetDataLink(name, val)
        
        for name, val in (("regivadyn", (0,1)),
                          ("pcf",       {True: '1', False: '0'}),
                          ("pcfscon",   {True: '1', False: '0'}),
                          ("pcfspe",    {True: '1', False: '0'}),
                          ("pcfins",    {True: '1', False: '0'}),
                          ("camsegr1",  {True:   1, False:   0}),
                          ("quaivanob", {True:   1, False:   0}),
                          ):
            cn(name).SetDataLink(name, val)
        
        cn('tipo').Bind(wx.EVT_RADIOBOX, self.OnTipoChanged)
        cn('regivadyn').Bind(wx.EVT_RADIOBOX, self.OnRegIvaDyn)
        cn('_regiva_detmag').Bind(wx.EVT_BUTTON, self.OnDetMag)
        
        cn('pralcf').SetDataLink(values=(0, 1, -1))
        
        return p
    
    def GetSearchResultsGrid(self, parent):
        grid = CauContabSearchResultsGrid(parent, ga.ID_SEARCHGRID, 
                                          self.db_tabname, self.GetSqlColumns())
        return grid
    
    def OnTipoChanged(self, event):
        self.TestRegIva()
        event.Skip()
    
    def OnRegIvaDyn(self, event):
        self.TestRegIva()
        event.Skip()
    
    def OnDetMag(self, event):
        dlg = MagRegIvaDialog(self, rsrim=self.rsrim)
        if dlg.ShowModal() == 1:
            self.SetDataChanged()
        event.Skip()
    
    def TestRegIva(self):
        tipo = self.FindWindowByName('tipo').GetValue()
        rdyn = self.FindWindowByName('regivadyn').GetValue()
        rivctrls = [x for x in awu.GetAllChildrens(self)
                    if 'regiva' in x.GetName()]
        riva = self.FindWindowByName('id_regiva')
        doiva = tipo in "IE"
        if not doiva:
            riva.SetValue(None)
        for c in rivctrls:
            if c.GetName().startswith('id_regiva'):
                enab = doiva and rdyn == 0
            elif c.GetName().startswith('_regiva_detmag'):
                enab = doiva and rdyn == 1 and self.db_recid is not None
            else:
                enab = doiva
            c.Enable(enab)
        riva.SetObligatory(doiva and not rdyn)

    def UpdateButtonsState(self):
        ga.AnagPanel.UpdateButtonsState(self)
        self._pdcpref.UpdateMoveButtonsState()

    def UpdateDataControls( self, recno ):
        ga.AnagPanel.UpdateDataControls( self, recno )
        self.TestRegIva()
        self._pdcpref.UpdateDataControls(self.db_recid)
        self.ReadMagRegIva()
    
    def ReadMagRegIva(self):
        mag = self.dbmag
        rim = self.dbrim
        rsrim = []
        for m in mag:
            rim.Retrieve('rim.id_caus=%s AND rim.id_magazz=%s', 
                         self.db_recid, m.id)
            rsrim.append([rim.id,              #MAGREGIVA_ID
                          m.id,                #MAGREGIVA_MAGAZZ_ID
                          m.codice,            #MAGREGIVA_MAGAZZ_cod
                          m.descriz,           #MAGREGIVA_MAGAZZ_desc
                          rim.regiva.id,       #MAGREGIVA_REGIVA_ID
                          rim.regiva.codice,   #MAGREGIVA_REGIVA_cod
                          rim.regiva.descriz]) #MAGREGIVA_REGIVA_desc
        self.rsrim = rsrim
    
    def TransferDataFromWindow( self ):
        out = self.Validate()
        if out: out = ga.AnagPanel.TransferDataFromWindow(self)
        if out: out = self._pdcpref.TransferDataFromWindow(self.db_recid)
        if out: out = self.WriteMagRegIva()
        return out
    
    def Validate(self):
        out = True
        if self.FindWindowByName('regivadyn').GetValue() == 1:
            #reg.iva dinamici x magazzino, controllo conformita recordset
            out = ValidateRsRim(self.rsrim)
        return out
    
    def WriteMagRegIva(self):
        if self.FindWindowByName('regivadyn').GetValue() == 0:
            return True
        rim = self.dbrim
        rim.Get(-1)
        for r in self.rsrim:
            rimid = r[MAGREGIVA_ID]
            if rimid is None or not rim.Locate(lambda x: x.id == rimid):
                rim.CreateNewRow()
                rim.id_caus = self.db_recid
            rim.id = rimid
            rim.id_magazz = r[MAGREGIVA_MAGAZZ_ID]
            rim.id_regiva = r[MAGREGIVA_REGIVA_ID]
        out = rim.Save()
        if not out:
            awu.MsgDialog(self, message=repr(rim.GetError()))
        return out

    def DeleteMagRegIva(self):
        out = False
        rim = self.dbrim
        if rim.Retrieve('rim.id_caus=%s', self.db_recid):
            for r in rim:
                r.Delete()
            out = rim.Save()
            if not out:
                awu.MsgDialog(self, message=repr(rim.GetError()))
        return out
    
    def DeleteDataRecord(self, *args, **kwargs):
        out = self.DeleteMagRegIva()
        if out: out = ga.AnagPanel.DeleteDataRecord(self, *args, **kwargs)
        return out


# ------------------------------------------------------------------------------


class CauContabFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Causali contabili.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(CauContabPanel(self, -1))


# ------------------------------------------------------------------------------


class CauContabDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Causali contabili.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(CauContabPanel(self, -1))
