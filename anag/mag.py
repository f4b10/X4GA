#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         anag/mag.py
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

import awc.util as awu
import awc.layout.gestanag as ga
import anag.mag_wdr as wdr

from Env import Azienda
bt = Azienda.BaseTab
bc = Azienda.Colours

import awc.controls.dbgrid as dbglib

import stormdb as adb

from cfg.regiva import RegIvaDialog

import report as rpt


MAGREGIVA_ID =          0
MAGREGIVA_CAUCON_ID =   1
MAGREGIVA_CAUCON_cod =  2
MAGREGIVA_CAUCON_desc = 3
MAGREGIVA_REGIVA_ID =   4
MAGREGIVA_REGIVA_cod =  5
MAGREGIVA_REGIVA_desc = 6


FRAME_TITLE = "Magazzini"


class GridCauRegIva(dbglib.DbGrid):
    """
    Griglia definizione registro iva della causale in base al magazzino
    (x dataentry magazzino; x dataentry contab non è contemplata la codifica
    del magazzino, quindi in presenza di causale con registro dinamico viene
    semplicemente attivato il controllo di selezione del registro iva in
    testata registrazione.
    """
    def __init__(self, parent):
        """
        Passare:
        parent della griglia
        recordset da gestire: 7-list, vedi costanti MAGREGIVA_*
        """
        
        dbglib.DbGrid.__init__(self, parent, -1, size=parent.GetSize(), 
                               style=wx.SUNKEN_BORDER)
        
        _STR = gl.GRID_VALUE_STRING
        
        coldef = (\
            ( 50, (MAGREGIVA_CAUCON_cod,  "Cod.",         _STR, False)),
            (150, (MAGREGIVA_CAUCON_desc, "Causale",      _STR, False)),
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
        
        afteredit = ((dbglib.CELLEDIT_AFTER_UPDATE, -1, self.TestValues),)
        
        self.SetData((), colmap, canedit, canins, links, afteredit)
        
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


class MagazzResultsGrid(ga.SearchResultsGrid):
    
    def GetDbColumns(self):
        _STR = gl.GRID_VALUE_STRING
        cn = lambda x: self.db._GetFieldIndex(x, inline=True)
        tab = self.tabalias
        return (( 40, (cn('magazz_codice'),  "Cod.",       _STR, True)),
                (160, (cn('magazz_descriz'), "Magazzino",  _STR, True)),
                ( 60, (cn('pdc_codice'),     "Cod.",       _STR, True)),
                (240, (cn('pdc_descriz'),    "Sottoconto", _STR, True)),
                (  1, (cn('magazz_id'),      "#mag",       _STR, True)),
                (  1, (cn('pdc_id'),         "#pdc",       _STR, True)),
            )
    
    def SetColumn2Fit(self):
        self.SetFitColumn(1)


# ------------------------------------------------------------------------------


class MagazzPanel(ga.AnagPanel):
    """
    Gestione tabella Magazzini.
    """
    def __init__(self, *args, **kwargs):
        
        ga.AnagPanel.__init__(self, *args, **kwargs)
        
        self.SetDbSetup( bt.tabelle[ bt.TABSETUP_TABLE_MAGAZZ ] )
        
        self._sqlrelcol += ", pdc.id, pdc.codice, pdc.descriz"
        self._sqlrelfrm +=\
            " LEFT JOIN %s ON magazz.id_pdc=pdc.id" % bt.TABNAME_PDC
        
        self.db_report = "Magazzini"
        cau = adb.DbTable(bt.TABNAME_CFGCONTAB, 'cau', writable=False)
        cau.AddOrder('cau.codice')
        cau.AddFilter('cau.regivadyn=1')
        cau.Retrieve()
        self.dbcau = cau
        self.dbrim = adb.DbTable(bt.TABNAME_CFGMAGRIV, 'rim', writable=True)
        self.dbrim.AddJoin(bt.TABNAME_REGIVA, 'regiva')
        self.rsrim = None #recordset x i/o cfgmagriv
        self.gridrim = None

    def InitAnagCard(self, parent):
        p = wx.Panel( parent, -1)
        wdr.MagazzCardFunc( p, True )
        self.gridrim = GridCauRegIva(self.FindWindowById(wdr.ID_PANGRIDRIM))
        self.Bind(gl.EVT_GRID_CELL_CHANGE, self.OnDataChanged)
        return p

    def UpdateDataControls( self, recno ):
        ga.AnagPanel.UpdateDataControls( self, recno )
        self.ReadMagRegIva()
        self.gridrim.ChangeData(self.rsrim)
    
    def GetSearchResultsGrid(self, parent):
        grid = MagazzResultsGrid(parent, ga.ID_SEARCHGRID, 
                                 self.db_tabname, self.GetSqlColumns())
        return grid
    
    def ReadMagRegIva(self):
        cau = self.dbcau
        rim = self.dbrim
        rsrim = []
        for c in cau:
            rim.Retrieve('rim.id_magazz=%s AND rim.id_caus=%s', 
                         self.db_recid, c.id)
            rsrim.append([rim.id,              #MAGREGIVA_ID
                          c.id,                #MAGREGIVA_CAUCON_ID
                          c.codice,            #MAGREGIVA_CAUCON_cod
                          c.descriz,           #MAGREGIVA_CAUCON_desc
                          rim.regiva.id,       #MAGREGIVA_REGIVA_ID
                          rim.regiva.codice,   #MAGREGIVA_REGIVA_cod
                          rim.regiva.descriz]) #MAGREGIVA_REGIVA_desc
        self.rsrim = rsrim
    
    def TransferDataFromWindow( self ):
        out = self.Validate()
        if out: out = ga.AnagPanel.TransferDataFromWindow(self)
        if out: out = self.WriteMagRegIva()
        return out
    
    def Validate(self):
        return self.ValidateRsRim()
    
    def ValidateRsRim(self):
        err = None
        diff = False
        rp = []
        for r in self.rsrim:
            ri = r[MAGREGIVA_REGIVA_ID]
            if not ri:
                err = "Ogni magazzino deve avere un corrispondente registro IVA"
                break
            elif rp and not ri in rp:
                diff = True
            rp.append(ri)
        if err:
            awu.MsgDialog(self, message=err, style=wx.ICON_ERROR)
            out = False
        else:
            if diff:
                awu.MsgDialog(self, message=\
                              """Non c'è lo stesso registro su tutte le """\
                              """causali, assicurarsi che sia corretto""", 
                              style=wx.ICON_WARNING)
            out = True
        return out
    
    def WriteMagRegIva(self):
        rim = self.dbrim
        rim.Get(-1)
        for r in self.rsrim:
            rimid = r[MAGREGIVA_ID]
            if rimid is None or not rim.Locate(lambda x: x.id == rimid):
                rim.CreateNewRow()
                rim.id_magazz = self.db_recid
            rim.id = rimid
            rim.id_caus = r[MAGREGIVA_CAUCON_ID]
            rim.id_regiva = r[MAGREGIVA_REGIVA_ID]
        out = rim.Save()
        if not out:
            awu.MsgDialog(self, message=repr(rim.GetError()))
        return out
    
    def DeleteMagRegIva(self):
        out = False
        rim = self.dbrim
        if rim.Retrieve('rim.id_magazz=%s', self.db_recid):
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


class MagazzFrame(ga._AnagFrame):
    """
    Frame Gestione tabella Magazzini.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagFrame.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(MagazzPanel(self, -1))


# ------------------------------------------------------------------------------


class MagazzDialog(ga._AnagDialog):
    """
    Dialog Gestione tabella Magazzini.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        ga._AnagDialog.__init__(self, *args, **kwargs)
        self.LoadAnagPanel(MagazzPanel(self, -1))
