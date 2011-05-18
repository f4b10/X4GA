#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/prodpro.py
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

import copy

import anag.prod_wdr as wdr

import magazz.dbtables as dbm

import Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours


class GridTableForGiac(dbglib.DbGridTable):
    """
    Provvede al calcolo della giacenza
    """
    def __init__(self, *args, **kwargs):
        dbglib.DbGridTable.__init__(self, *args, **kwargs)
        self.dbmov = None
    
    def GetValue(self, row, col):
        rscol = self.rsColumns[col]
        if   rscol == -1:
            if self.dbmov.RowNumber() != row:
                self.dbmov.MoveRow(row)
            out = self.dbmov.total_giac or 0
        else:
            out = dbglib.DbGridTable.GetValue(self, row, col)
        return out


# ------------------------------------------------------------------------------


qw = 80  # qta col width
iw = 110 # val col width

cn = lambda db, col: db._GetFieldIndex(col, inline=True)

def ProdProgrGridColumns(mov):
    _IMPQ = bt.GetMagQtaMaskInfo()
    _IMPV = bt.GetValIntMaskInfo()
    return [\
        ( qw, (cn(mov,"total_ini"),    "Giac.Iniz.",  _IMPQ, True )),\
        ( qw, (cn(mov,"total_car"),    "Carichi",     _IMPQ, True )),\
        ( qw, (cn(mov,"total_sca"),    "Scarichi",    _IMPQ, True )),\
        ( qw, (cn(mov,"total_ordcli"), "Ord.Clienti", _IMPQ, True )),\
        ( qw, (cn(mov,"total_ordfor"), "Ord.Fornit.", _IMPQ, True )),\
        ( iw, (cn(mov,"total_iniv"),   "Val.Iniziale",_IMPV, True )),\
        ( iw, (cn(mov,"total_carv"),   "Val.Car.",    _IMPV, True )),\
        ( iw, (cn(mov,"total_scav"),   "Val.Scar.",   _IMPV, True )),\
        ( iw, (cn(mov,"total_ordcliv"),"Val.Ord.Cli.",_IMPV, True )),\
        ( iw, (cn(mov,"total_ordforv"),"Val.Ord.For.",_IMPV, True )) ]


# ------------------------------------------------------------------------------


class ProdProSchedaGrid(dbglib.DbGridColoriAlternati):
    """
    Griglia progressivi scheda prodotto.
    """
    def __init__(self, parent, dbpro):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable progressivi x mag. (magazz.dbtables.ProdProgrDaMovimByMag)
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbpro = dbpro
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        def cn(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        pro = dbpro
        
        cols = (( 35, (cn(pro.magazz, 
                          'codice'),    "Cod.",      _STR, True)),
                ( 70, (cn(pro.magazz, 
                          'descriz'),   "Magazzino", _STR, True)),
                (110, (cn(pro, 'ini'),  "Giac.In.",  _QTA, True)),
                (110, (cn(pro, 'car'),  "Carichi",   _QTA, True)),
                (110, (cn(pro, 'sca'),  "Scarichi",  _QTA, True)),
                (120, (cn(pro, 'iniv'), "Val.In.",   _IMP, True)),
                (120, (cn(pro, 'carv'), "Val.Car.",  _IMP, True)),
                (120, (cn(pro, 'scav'), "Val.Scar.", _IMP, True)),
                      )
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = True
        canins = False
        
        links = None
        afteredit = None
        
        self.SetData((), colmap, canedit, canins, links, afteredit,
                     newRowFunc=None)
        
        self.AddTotalsRow(1, 'Totali:', (2,3,4,5,6,7,))
        
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
    
    def GetAttr(self, row, col, rscol, attr=dbglib.gridlib.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        attr.SetReadOnly()
        return attr


# ------------------------------------------------------------------------------


class ProdProgrPanel(wx.Panel):
    def __init__(self, parent, dlg):
        wx.Panel.__init__(self, parent)
        self.dlg = dlg
        
        self.dbpromag = dbm.ProdProgrDaMovimByMag()
        self.dbpromov = dbm.ProdProgrDaMovimByMov()
        self.dbproeva = dbm.ProdProgrEvas()
        self.dbprosch = dbm.ProdProgrDaScheda()
        self.proschegrid = None
        
        wdr.ProdProgrFunc(self)
        
        self._bgcol0 = stdcolor.GetColour("lemonchiffon")  #prodotto
        self._bgcol1 = stdcolor.GetColour("paleturquoise") #progr.qta
        self._bgcol2 = stdcolor.GetColour("palegreen")     #progr.valore
        self.GridProMag_Init()
        self.GridProMov_Init()
        self.GridProScheda_Init()
    
    def GridProScheda_Init(self):
        self.proschegrid = ProdProSchedaGrid(
            self.FindWindowById(wdr.ID_PPRPANPROPRO), self.dbprosch)
    
    def GridProMag_Init(self):
        size = self.GetClientSizeTuple()
        parent = self.FindWindowById(wdr.ID_PPRPANPROMAG)
        
        _STR = gl.GRID_VALUE_STRING
        
        self.dbpromag.Reset()
        pro = self.dbpromag
        mov = pro.mov
        doc = mov.doc
        mag = doc.mag
        
        cols = [\
            ( 35, (cn(mag,"codice"),  "Cod.",      _STR, True )),\
            (110, (cn(mag,"descriz"), "Magazzino", _STR, True ))]
        cols += ProdProgrGridColumns(pro)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        afteredit = None
        
        rs = pro.GetRecordset()
        
        grid = dbglib.DbGrid(parent, -1, size=size, style=0,\
                             tableClass=GridTableForGiac)
        grid.SetData( rs, colmap, canedit, canins,\
                      None, afteredit)
        #grid.GetTable().dbmov = self.dbpromag.mov
        grid.AddTotalsRow(1, 'Totali', map(lambda x: x[1][0],
                                           ProdProgrGridColumns(pro)))
        grid.SetCellDynAttr(self.GridProMagGetAttr)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.gridpromag = grid

    def GridProMagGetAttr(self, row, col, rscol, attr):
        if col < 2:
            attr.SetBackgroundColour(self._bgcol0)
        else:
            attr.SetBackgroundColour([self._bgcol1,
                                      self._bgcol2][(col-2)/5])
        attr.SetReadOnly()
        return attr
    
    def GridProSchedaUpdate(self):
        self.proschegrid.ChangeData(self.dbprosch.GetRecordset())
    
    def GridProMagUpdate(self):
        wx.BeginBusyCursor()
        self.gridpromag.ChangeData(self.dbpromag.GetRecordset())
        self.GridProMagUpdateTotali()
        wx.EndBusyCursor()
    
    def GridProMagUpdateTotali(self):
        
        pr = self.dbpromag
        fields = [x[0] for x in pr._info.totdef]
        
        tots = {}
        for field in fields:
            tots[field] = 0
        
        for mag in pr:#.mov:
            for field in fields:
                tots[field] += mag.__getattr__("total_%s" % field) or 0
        
        for field in fields:
            ctr = self.FindWindowByName("pprmag%s" % field)
            if ctr: ctr.SetValue(tots[field])
        
        #calcolo backorders
        wx.BeginBusyCursor()
        pe = self.dbproeva
        pe.Retrieve('mov.id_prod=%s', self.dbpromag.id)
        wx.EndBusyCursor()
        
        cn = lambda x: self.FindWindowByName(x)
        
        for name, col in (('bkocli', 'ordcli'),
                          ('bkofor', 'ordfor')):
            q = tots[col] - (getattr(pe,'total_evas%s' % col) or 0)
            v = tots['%sv'%col] - (getattr(pe,'total_evas%sv' % col) or 0)
            try:
                m = v/q
            except:
                m = 0
            cn("pprmag%s" % name).SetValue(q)
            cn("pprmag%sv" % name).SetValue(v)
            cn("pprmag%sm" % name).SetValue(m)
        
        giac = tots['ini']+tots['car']-tots['sca']
        gpre = giac - (pe.total_evasordcli or 0)
        
        cn("pprmaggia").SetValue(giac)
        cn("pprmaggpr").SetValue(gpre)
        
        mov = pr.mov
        cstu = pr.costo
        try:
            cstm =\
                 (mov.total_iniv+mov.total_carv) /\
                 (mov.total_ini +mov.total_car )
        except:
            cstm = 0
        
        cn("pprmagcsu").SetValue(cstu)
        cn("pprmagcsm").SetValue(cstm)
        
        for name in ('ini', 'car', 'sca'):
            try:
                m = tots['%sv' % name]/tots[name]
            except:
                m = 0
            cn("pprmag%sm" % name).SetValue(m)
    
    # --------------------------------------------------------------------------
    
    def GridProMov_Init(self):
        size = self.GetClientSizeTuple()
        parent = self.FindWindowById(wdr.ID_PROMOVPAN)
        
        _STR = gl.GRID_VALUE_STRING
        
        self.dbpromov.Reset()
        pro = self.dbpromov
        mov = pro.mov
        doc = mov.doc
        mag = doc.mag
        tpd = doc.tipdoc
        tpm = mov.tipmov
        
        cols = [\
            ( 35, (cn(tpd,"codice"),  "Cod.",      _STR, True )),\
            (110, (cn(tpd,"descriz"), "Documento", _STR, True )),\
            ( 35, (cn(tpm,"codice"),  "Cod.",      _STR, True )),\
            (110, (cn(tpm,"descriz"), "Movimento", _STR, True )) ]
        cols += ProdProgrGridColumns(self.dbpromov)
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        afteredit = None
        
        rs = self.dbpromov.GetRecordset()
        
        grid = dbglib.DbGrid(parent, -1, size=size, style=0,\
                             tableClass=GridTableForGiac)
        grid.SetData( rs, colmap, canedit, canins,\
                      None, afteredit)
        #mov = self.dbpromov.mov
        #grid.GetTable().dbmov = mov
        grid.AddTotalsRow(3, 'Totali', map(lambda x: x[1][0],
                                           ProdProgrGridColumns(self.dbpromov)))
        grid.SetCellDynAttr(self.GridProMovGetAttr)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        self.gridpromov = grid
        
        self.Bind(wx.EVT_BUTTON, self.GridProMovOnUpdate,\
                  id=wdr.ID_PROMOVBUTUPD)

    def GridProMovGetAttr(self, row, col, rscol, attr):
        if col < 4:
            attr.SetBackgroundColour(self._bgcol0)
        else:
            attr.SetBackgroundColour([self._bgcol1,
                                      self._bgcol2][(col-4)/5])
        attr.SetReadOnly()
        return attr
    
    def GridProMovOnUpdate(self, event):
        self.GridProMovUpdate()

    def GridProMovUpdate(self):
        
        mov = self.dbpromov.mov
        mov.ClearFilters()
        
        par = self.FindWindowByName("promovmag").GetValue()
        if par: 
            mov.AddFilter("doc.id_magazz=%s", par)
        
        par = self.FindWindowByName("promovdat1").GetValue()
        if par: 
            mov.AddFilter("doc.datreg>=%s", par)
        
        par = self.FindWindowByName("promovdat2").GetValue()
        if par: 
            mov.AddFilter("doc.datreg<=%s", par)
        
        wx.BeginBusyCursor()
        pm = self.dbpromov
        pm.Get(pm.id)
        self.gridpromov.ChangeData(pm.GetRecordset())
        wx.EndBusyCursor()

    def GridUpdate(self, prod=None):
        if prod is not None:
            self.dbpromag.Get(prod)
            self.dbpromov.Get(prod)
            self.dbprosch.Retrieve("id_prod=%s", prod)
        self.GridProSchedaUpdate()
        self.GridProMagUpdate()
        self.GridProMovUpdate()
