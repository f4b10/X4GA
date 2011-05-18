#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/sottosc.py
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

import magazz.dbtables as dbm

import magazz.invent_wdr as wdr

import report as rpt
import magazz.barcodes as bcode

Env = dbm.Env
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

import magazz
import magazz.invent as inv

RSINV_ID =   0
RSINV_COD =  1
RSINV_DES =  2
RSINV_GIA =  3
RSINV_SCO =  4
RSINV_FAB =  5


FRAME_TITLE = "Prodotti sottoscorta"


class SottoscortaGrid(inv.GridInv):
    """
    Grid Prodotti sottoscorta.
    """
    def CreateGrid(self):
        
        if self.gridinv is not None:
            self.gridinv.Destroy()
        
        size = self.parent.GetClientSizeTuple()
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        
        qw = 100 # qta col width
        
        cols = [
            ( 80, (RSINV_COD, "Cod.",     _STR, True)),
            (180, (RSINV_DES, "Prodotto", _STR, True))
        ]
        
        if True:#self.modo == RSINV_MODE_BYPROGR:
            cols += [\
                ( qw, (RSINV_GIA, "Giacenza",    _QTA, True)),
                ( qw, (RSINV_SCO, "Scorta min.", _QTA, True)),
                ( qw, (RSINV_FAB, "Fabbisogno",  _QTA, True)),
                (  1, (RSINV_ID,  "#pro",        _STR, True)),
            ]                                      
        
        #else:
            #for col, mag in enumerate(self.dbmags):
                #cols.append((qw, (col+4, mag.descriz, _QTA, True)))
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        afteredit = None
        
        grid = dbglib.DbGrid(self.parent, -1, size=size, style=0)
        grid.SetData(self.rsinv, colmap, canedit, canins)
        
        #def GridAttr(row, col, rscol, attr):
            #if col%2 == 0:
                #attr.SetBackgroundColour(stdcolor.GetColour("gainsboro"))
            #else:
                #attr.SetBackgroundColour(stdcolor.NORMAL_BACKGROUND)
            #return attr
        #grid.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.SetFitColumn(1)
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        self.parent.SetSizer(sz)
        sz.SetSizeHints(self.parent)
        self.gridinv = grid
    
    def Update(self, dlg, dbinv, parms):
        
        wait = aw.awu.WaitDialog(dlg,
                                 message="Estrazione dati inventario in corso",\
                                 maximum=dbinv.RowsCount())
        
        self.rsinv = []
        self.ResetTotals()
        
        #tipoval = int(parms['tipoval'])
        #tiplist = parms['id_tiplist']
        
        for i in dbinv:
            #vu = i.Valore(tipoval, tiplist)
            #val = i.total_giac*vu
            do = True
            #if   i.total_giac < 0  and not parms['incgianeg']:
                #do = False
            #elif i.total_giac == 0 and not parms['incgianul']:
                #do = False
            #elif i.total_giac > 0  and not parms['incgiapos']:
                #do = False
            #elif val <= 0 and not parms['incvalnul']:
                #do = False
            #else:
                #v1 = parms['valinf']
                #v2 = parms['valsup']
                #if v1 or v2:
                    #if v1 and val<v1 or v2 and val>v2:
                        #do = False
            if do:
                if True:#self.modo == RSINV_MODE_BYPROGR:
                    gia = i.total_giac or 0
                    sco = i.scomin or 0
                    if sco>0 and gia<sco:
                        self.rsinv.append([i.id,      #RSINV_ID
                                           i.codice,  #RSINV_COD
                                           i.descriz, #RSINV_DES
                                           gia,       #RSINV_GIA
                                           sco,       #RSINV_SCO
                                           sco-gia])  #RSINV_VAL
                    #for t in ('ini', 'car', 'sca'):
                        #for tipo in ('', 'v'):
                            #name = "%s%s" % (t, tipo)
                            #self.totals[name] +=\
                                #i.__getattr__("total_%s" % name)
                    #self.totals['giac'] +=  i.total_giac
                    #self.totals['giacv'] += val
                    
                #else:
                    #p = [i.id,                       #RSINV_ID
                         #i.codice,                   #RSINV_COD
                         #i.descriz,                  #RSINV_DES
                         #i.barcode]                  #RSINV_BCD
                    #for magid in self.magsid:
                        #gm = 0
                        #if self.invdata:
                            #if i.mov.Locate(lambda x: x.doc.id_magazz == magid):
                                #gm = i.mov.total_giac
                        #else:
                            #if i.pp.Locate(lambda x: x.id_magazz == magid):
                                #gm = i.pp.total_giac
                        #p.append(gm)
                    #self.rsinv.append(p)
            
            if not wait.SetValue(i.RowNumber()):
                break
        
        wait.Destroy()
        
        self.CreateGrid()
    

# ------------------------------------------------------------------------------


class SottoscortaPanel(inv.InventPanel):
    """
    Panel Prodotti sottoscorta.
    """
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.dbinvdat = dbm.InventarioDaMovim(flatmag=True)
        self.dbinvdat.ShowDialog(self)
        self.dbinvsch = dbm.InventarioDaScheda(flatmag=True)
        self.dbinvsch.ShowDialog(self)
        self.dbinv = None
        
        wdr.SottoscortaFunc(self)
        dm = magazz.GetDefaultMagazz()
        if dm:
            lm = self.FindWindowByName('magazzini')
            if dm in lm.magid:
                lm.Check(lm.magid.index(dm), True)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        cn('datinv').SetValue(Env.Azienda.Login.dataElab)
        
        self.gridinv = SottoscortaGrid(self.FindWindowById(wdr.ID_PANGRIDINV))
        
        self.SetTipoInv()
        
        for cid, func in ((wdr.ID_UPDATE, self.OnUpdate),
                          (wdr.ID_PRINT,  self.OnPrint),
                          (wdr.ID_LABELS, self.OnLabels)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeTipoInv, id=wdr.ID_TIPOINV)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeTipoVal, id=wdr.ID_TIPOVAL)
        self.Bind(wx.EVT_CHECKBOX, self.OnChangeView, id=wdr.ID_CHGVIEW)
    
    def SetMagFilter(self):
        mag = self.FindWindowByName("magazzini")
        mags = []
        for n, mid in enumerate(mag.magid):
            if mag.IsChecked(n):
                mags.append(mid)
        if len(mags) == 0:
            aw.awu.MsgDialog(self, "Selezionare almeno un magazzino")
            return False
        self.dbinv.SetMagazz(mags)
        return True
    
    def EnableList(self):
        pass
    
    def PrintInventario(self):
        wait = aw.awu.WaitDialog(self.GetParent(), 
                                 message='Preparazione dei dati in corso...')
        try:
            db = dbm.SottoscortaPrint()
            db.ShowDialog(self.GetParent())
            for n, rs in enumerate(self.gridinv.rsinv):
                db.CreateNewRow()
                db.codice = rs[RSINV_COD]
                db.descriz = rs[RSINV_DES]
                db.gia = rs[RSINV_GIA]
                db.sco = rs[RSINV_SCO]
                db.fab = rs[RSINV_FAB]
                wait.SetValue(n)
        finally:
            wait.Destroy()
        db._info.valivati = self.dbinv._info.valivati
        rpt.Report(self, db, 'Prodotti sottoscorta')


# ------------------------------------------------------------------------------


class SottoscortaFrame(aw.Frame):
    """
    Frame Prodotti sottoscorta.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = SottoscortaPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
