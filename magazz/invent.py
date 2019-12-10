#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/invent.py
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


RSINV_MODE_BYPROGR = 0
RSINV_MODE_BYMAGAZ = 1

RSINV_ID =        0
RSINV_COD =       1
RSINV_DES =       2
RSINV_BCD =       3
RSINV_CTCOD =     4
RSINV_CTDES =     5
RSINV_FORN_ID =   6
RSINV_forn_cod =  7
RSINV_forn_des =  8
RSINV_INI =       9
RSINV_INIV =     10
RSINV_CAR =      11
RSINV_CARV =     12
RSINV_SCA =      13
RSINV_SCAV =     14
RSINV_GIA =      15
RSINV_VAL =      16
RSINV_GIAV =     17


FRAME_TITLE = "Inventario magazzino"


class GridInv(object):
    
    def __init__(self, pp):
        
        object.__init__(self)
        
        self.parent =  pp
        self.rsinv =   ()
        self.gridinv = None
        self.totals =  {}
        self.modo =    RSINV_MODE_BYPROGR
        self.invdata = False
        
        self.dbmags =  dbm.adb.DbTable(dbm.bt.TABNAME_MAGAZZ, "mag")
        self.dbmags.AddOrder("codice")
        self.dbmags.Retrieve()
        
        self.magsid = [mag.id for mag in self.dbmags]
        
        self.CreateGrid()
    
    def CreateGrid(self):
        
        if self.gridinv is not None:
#            self.gridinv.Destroy()
            wx.CallAfter(self.gridinv.Destroy)
        
        size = self.parent.GetClientSizeTuple()
        
        _STR = gl.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _VAL = bt.GetValIntMaskInfo()
        
        qw = 80  # qta col width
        iw = 110 # val col width
        
        cols = [
            (  1, (RSINV_CTCOD, "cod.",      _STR, True )),
            (  1, (RSINV_CTDES, "Categoria", _STR, True )),
            ( 80, (RSINV_COD,   "Cod.",      _STR, True )),
            (180, (RSINV_DES,   "Prodotto",  _STR, True ))
        ]
        
        if self.modo == RSINV_MODE_BYPROGR:
            cols += [\
                ( qw, (RSINV_GIA,      "Giacenza",   _QTA, True)),
                ( iw, (RSINV_GIAV,     "Valore",     _VAL, True)),
                ( qw, (RSINV_INI,      "Giac.Iniz.", _QTA, True)),
                ( iw, (RSINV_INIV,     "Valore",     _VAL, True)),
                ( qw, (RSINV_CAR,      "Carichi",    _QTA, True)),
                ( iw, (RSINV_CARV,     "Valore",     _VAL, True)),
                ( qw, (RSINV_SCA,      "Scarichi",   _QTA, True)),
                ( iw, (RSINV_SCAV,     "Valore",     _VAL, True)),
                ( 50, (RSINV_forn_cod, "Cod.",       _STR, True)),
                (220, (RSINV_forn_des, "Fornitore",  _STR, True)),
            ]                                      
        
        else:
            for col, mag in enumerate(self.dbmags):
                cols.append((qw, (col+4, mag.descriz, _QTA, True)))
        
        cols.append((1, (RSINV_ID,      "#pro", _STR, True)))
        cols.append((1, (RSINV_FORN_ID, "#for", _STR, True)))
        
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        afteredit = None
        
        grid = dbglib.DbGrid(self.parent, -1, size=size, style=0,
                             idGrid='inter_inventario')
        grid.SetData(self.rsinv, colmap, canedit, canins)
        grid._cols=cols
        
        
        
        def GridAttr(row, col, rscol, attr):
            if col%2 == 0:
                attr.SetBackgroundColour(stdcolor.GetColour("gainsboro"))
            else:
                attr.SetBackgroundColour(stdcolor.NORMAL_BACKGROUND)
            return attr
        grid.SetCellDynAttr(GridAttr)
        
        map(lambda c:\
            grid.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        grid.SetFitColumn(3)
        grid.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(grid, 0, wx.GROW|wx.ALL, 0)
        self.parent.SetSizer(sz)
        sz.SetSizeHints(self.parent)
        self.gridinv = grid

    def ResetTotals(self):
        for t in ('ini', 'car', 'sca', 'giac'):
            for tipo in ('', 'v'):
                name = "%s%s" % (t, tipo)
                self.totals[name] = 0
    
    def Update(self, dlg, dbinv, parms):
        
        wait = aw.awu.WaitDialog(dlg,
                                 message="Estrazione dati inventario in corso",\
                                 maximum=dbinv.RowsCount())
        
        self.rsinv = []
        self.ResetTotals()
        
        tipoval = int(parms['tipoval'])
        tiplist = parms['id_tiplist']
        
        for i in dbinv:
            vu = i.Valore(tipoval, tiplist)
            qta = i.total_giac or 0
            val = qta*vu
            do = True
            #print 'prodotto nascosto:%s  includi nascosti:%s' % (i.status.hidesearch, parms['inchidden'])
            if i.status.hidesearch and not parms['inchidden']:
                do = False
            #if   i.total_giac < 0  and not parms['incgianeg']:
            elif   i.total_giac < 0  and not parms['incgianeg']:
                do = False
            elif i.total_giac == 0 and not parms['incgianul']:
                do = False
            elif i.total_giac > 0  and not parms['incgiapos']:
                do = False
            elif val <= 0 and not parms['incvalnul']:
                do = False
            else:
                v1 = parms['valinf']
                v2 = parms['valsup']
                if v1 or v2:
                    if v1 and val<v1 or v2 and val>v2:
                        do = False
            if do:
                q1 = parms['qtainf']
                q2 = parms['qtasup']
                if q1 or q2:
                    if q1 and qta<q1 or q2 and qta>q2:
                        do = False
            if do:
                c = i.catart
                if self.modo == RSINV_MODE_BYPROGR:
                    self.rsinv.append([i.id,              #RSINV_ID
                                       i.codice,          #RSINV_COD
                                       i.descriz,         #RSINV_DES
                                       i.barcode,         #RSINV_BCD
                                       c.codice,          #RSINV_CTCOD
                                       c.descriz,         #RSINV_CTDES
                                       i.pdcforn.id,      #RSINV_FORN_ID
                                       i.pdcforn.codice,  #RSINV_forn_cod
                                       i.pdcforn.descriz, #RSINV_forn_des
                                       i.total_ini,       #RSINV_INI
                                       i.total_iniv,      #RSINV_INIV
                                       i.total_car,       #RSINV_CAR
                                       i.total_carv,      #RSINV_CARV
                                       i.total_sca,       #RSINV_SCA
                                       i.total_scav,      #RSINV_SCAV
                                       i.total_giac,      #RSINV_GIA
                                       vu,                #RSINV_VAL
                                       val])              #RSINV_GIAV
                    for t in ('ini', 'car', 'sca'):
                        for tipo in ('', 'v'):
                            name = "%s%s" % (t, tipo)
                            self.totals[name] +=\
                                i.__getattr__("total_%s" % name)
                    self.totals['giac'] +=  i.total_giac
                    self.totals['giacv'] += val
                    
                else:
                    p = [i.id,      #RSINV_ID
                         i.codice,  #RSINV_COD
                         i.descriz, #RSINV_DES
                         i.barcode, #RSINV_BCD
                         c.codice,  #RSINV_CTCOD
                         c.descriz] #RSINV_CTDES
                    for magid in self.magsid:
                        gm = 0
                        if self.invdata:
                            if i.mov.Locate(lambda x: x.doc.id_magazz == magid):
                                gm = i.mov.total_giac
                        else:
                            if i.pp.Locate(lambda x: x.id_magazz == magid):
                                gm = i.pp.total_giac
                        p.append(gm)
                    self.rsinv.append(p)
            
            if not wait.SetValue(i.RowNumber()):
                break
        
        wait.Destroy()
        
        self.CreateGrid()
    
    def ChangeMode(self):
        if self.modo == RSINV_MODE_BYPROGR:
            self.modo = RSINV_MODE_BYMAGAZ
        else:
            self.modo = RSINV_MODE_BYPROGR


# ------------------------------------------------------------------------------


class InventPanel(aw.Panel):
    
    rptname = 'Inventario magazzino'
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        #self.dbinvdat = dbm.InventarioDaMovim(flatmag=True)
        self.dbinvdat = dbm.InventarioDaMovim(flatmag=True, fields='id,codice,descriz,id_catart,id_gruart,id_status,id_gruprez,costo,prezzo,barcode')
        self.dbinvdat.ShowDialog(self)
        self.dbinvsch = dbm.InventarioDaScheda(flatmag=True)
        self.dbinvsch.ShowDialog(self)
        self.dbinv = None
        
        wdr.QI = bt.MAGQTA_INTEGERS
        wdr.QD = bt.MAGQTA_DECIMALS
        wdr.VI = bt.VALINT_INTEGERS
        wdr.VD = bt.VALINT_DECIMALS
        
        wdr.InventFunc(self)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        cn('tipoval').SetDataLink('tipoval', (dbm.VALINV_COSTOULTIMO,
                                              dbm.VALINV_COSTOMEDIO,
                                              dbm.VALINV_PREZZOUFF,
                                              dbm.VALINV_PREZZOLIST))
        cn('datinv').SetValue(Env.Azienda.Login.dataElab)
        
        self.CreateGrid()
        
        self.SetTipoInv()
        self.EnableList()
        
        wx.CallAfter(lambda: cn('id_magazz').SetFocus())
        
        for cid, func in ((wdr.ID_UPDATE, self.OnUpdate),
                          (wdr.ID_PRINT,  self.OnPrint),
                          (wdr.ID_LABELS, self.OnLabels)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
        
        self.Bind(wx.EVT_CHECKBOX, self.OnChangeTipoInv, id=wdr.ID_INVDATA)
        self.Bind(wx.EVT_RADIOBOX, self.OnChangeTipoVal, id=wdr.ID_TIPOVAL)
        self.Bind(wx.EVT_CHECKBOX, self.OnChangeView, id=wdr.ID_CHGVIEW)
    
    def GetPanelDataSource(self):
        return self.dbinvdat
    
    def CreateGrid(self):
        self.gridinv = GridInv(self.FindWindowById(wdr.ID_PANGRIDINV))
    
    def OnChangeTipoInv(self, event):
        self.SetTipoInv()
        event.Skip()
    
    def SetTipoInv(self):
        ci = self.FindWindowById
        try:
            invdata = ci(wdr.ID_INVDATA).IsChecked()
        except:
            invdata = True
        if invdata:
            self.dbinv = self.dbinvdat
            s = True
        else:
            self.dbinv = self.dbinvsch
            s = False
        ci(wdr.ID_DATINV).Enable(s)
        if s:
            ci(wdr.ID_DATINV).SetFocus()
        self.gridinv.invdata = s
    
    def OnChangeTipoVal(self, event):
        self.EnableList()
        event.Skip()
    
    def EnableList(self):
        def cn(x):
            return self.FindWindowByName(x)
        c = cn('id_tiplist')
        e = (cn('tipoval').GetValue() == dbm.VALINV_PREZZOLIST)
        c.Enable(e)
        if e:
            c.SetFocus()
    
    def OnUpdate(self, event):
        self.UpdateInv()
    
    def OnPrint(self, event):
        self.PrintInventario()
        event.Skip()
    
    def OnLabels(self, event):
        self.PrintEtichette()
        event.Skip()
    
    def PrintInventario(self):
        if self.dbinv._info.raggrcat:
            r = aw.awu.MsgDialog(self, "Includo il dettaglio dei prodotti?",
                                 style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
            sd = (r == wx.ID_YES)
        else:
            r = None
            sd = True
        if sd:
            r = aw.awu.MsgDialog(self, "Stampo anche il fornitore?",
                                 style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
            sf = (r == wx.ID_YES)
        else:
            sf = False
        wait = aw.awu.WaitDialog(self.GetParent(), 
                                 message='Preparazione dei dati in corso...')
        try:
            db = dbm.InventarioPrint()
            db._info.stampadet = sd
            db._info.stampaforn = sf
            db.ShowDialog(self.GetParent())
            for n, rs in enumerate(self.gridinv.rsinv):
                db.CreateNewRow()
                db.codice = rs[RSINV_COD]
                db.descriz = rs[RSINV_DES]
                db.codcat = rs[RSINV_CTCOD]
                db.descat = rs[RSINV_CTDES]
                db.forncod = rs[RSINV_forn_cod]
                db.forndes = rs[RSINV_forn_des]
                db.ini = rs[RSINV_INI]
                db.iniv = rs[RSINV_INIV]
                db.car = rs[RSINV_CAR]
                db.carv = rs[RSINV_CARV]
                db.sca = rs[RSINV_SCA]
                db.scav = rs[RSINV_SCAV]
                db.gia = rs[RSINV_GIA]
                db.val = rs[RSINV_VAL]
                db.giav = rs[RSINV_GIAV]
                wait.SetValue(n)
        finally:
            wait.Destroy()
        db._info.valivati = self.dbinv._info.calciva
        db._info.raggrcat = self.dbinv._info.raggrcat
        cn = self.FindWindowByName
        db.SetPrintValue('codmag', cn('id_magazz').GetValueCod())
        db.SetPrintValue('desmag', cn('id_magazz').GetValueDes())
        db.SetPrintValue('datinv', cn('datinv').GetValue())
        def AdaptHeadings(report, dbt):
            if dbt._info.raggrcat and not dbt._info.stampadet:
                groups = report.lGroup
                for g in groups:
                    if groups[g].name == 'catart':
                        groups[g].oGroupHeader.altezza = 0
        rpt.Report(self, db, self.rptname, startFunc=AdaptHeadings)
    
    def PrintEtichette(self):
        dlg = bcode.SelQtaDialog(self)
        do = dlg.ShowModal() == wx.ID_OK
        dlg.Destroy()
        if not do:
            return
        wait = aw.awu.WaitDialog(self.GetParent(), 
                                 message='Preparazione dei dati in corso...')
        try:
            db = dbm.ProdEticList()
            db.ShowDialog(self.GetParent())
            for n, rs in enumerate(self.gridinv.rsinv):
                do = True
                if dlg.GetSoloInterni():
                    do = False
                    bc = rs[RSINV_BCD]
                    if bc is not None:
                        if bc.startswith(bt.MAGEAN_PREFIX):
                            do = True
                if do:
                    db.CreateNewRow()
                    db.id = rs[RSINV_ID]
                    db.qtaetic = dlg.GetQta(rs[RSINV_GIA])
                    wait.SetValue(n)
        finally:
            wait.Destroy()
        #def GetPrintTable(rptdef, _rpt):
            #rows = cols = 1
            #if '(' in rptdef:
                #x = rptdef[rptdef.rindex('(')+1:]
                #if x.endswith(')'):
                    #x = x[:-1]
                #if 'x' in x:
                    #rows, cols = map(int,x.split('x'))
            #row0 = _rpt.GetLabelOffsetRow()
            #col0 = _rpt.GetLabelOffsetCol()
            #return db.GetPrintTable(rptdef, rows, cols, row0, col0)
        #rpt.ReportLabels(self, None, 'Etichette prodotti', dbfunc=GetPrintTable)
        if db.RowsCount() == 0:
            aw.awu.MsgDialog(self, message="Nessuna etichetta da stampare.")
            return
        SelDialog = bcode.EtichetteProdottiDialog
        dlg = SelDialog(self, title='Etichette prodotti da inventario')
        dlg.SetProdEticList(db)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnChangeView(self, event):
        self.gridinv.ChangeMode()
        self.UpdateInv()
    
    def SetMagFilter(self):
        val = self.FindWindowByName("id_magazz").GetValue()
        if True:#val is not None:
            self.dbinv.SetMagazz(val)
    
    def UpdateInv(self):
        
        wx.BeginBusyCursor()
        
        
        i = self.dbinv
        i.ClearFilters()
        
        def cn(x):
            return self.FindWindowByName(x)
        
        val = cn("datinv").GetValue()
        if val is not None:
            i.SetDataInv(val)
            
        
        self.SetMagFilter()
        
        v1 = cn('codice1').GetValue()
        v2 = cn('codice2').GetValue()
        if v1 or v2:
            if v1: i.AddFilter(r"prod.codice>=%s", v1)
            if v2: i.AddFilter(r"prod.codice<=%s", v2.rstrip()+'Z')
        
        for name in 'tipart,catart,gruart,pdcforn'.split(','):
            c1 = cn(name+'1')
            c2 = cn(name+'2')
            if hasattr(c1, 'GetValueCod'):
                v1 = cn(name+'1').GetValueCod()
                v2 = cn(name+'2').GetValueCod()
            else:
                v1 = cn(name+'1').GetValue()
                v2 = cn(name+'2').GetValue()
            if v1 or v2:
                if v1 == v2:
                    i.AddFilter("%s.codice=%%s" % name, v1)
                else:
                    if v1:
                        i.AddFilter("%s.codice>=%%s" % name, v1)
                    if v2:
                        i.AddFilter("%s.codice<=%%s" % name, v2.rstrip()+'Z')

        if self.FindWindowByName('invdata').IsChecked() and i.tabinfo('cfgautom', 'maginidoc', 'aut_id', 'codice'):
            v_idmagaz=i._info.g_magazz
            v_datinv =i._info.g_data
            v_tipdoc =i.tabinfo('cfgautom', 'maginidoc', 'aut_id', 'codice')
            v_tipmov =i.tabinfo('cfgautom', 'maginimov', 'aut_id', 'codice')
            #===================================================================
            # print 'aggiungere filtro su inizializzazione giacenze'
            # print '        id_magazz: %s' % v_idmagaz
            # print '  data inventario: %s' % v_datinv 
            # print 'id tipo documento: %s' % v_tipmov 
            # print 'id tipo movimento: %s' % v_tipdoc 
            # print '-'*80
            #===================================================================
            filter = """(
(select g.dtGiaIni from SearchGiacIniziale g 
    where (g.id_prod=prod.id and g.id_tipmov=%s and g.dtGiaIni<%s and g.id_magazz=%s) 
    order by g.dtGiaIni desc  limit 1 ) is null or
(select g.dtGiaIni  from SearchGiacIniziale g 
    where (g.id_prod=prod.id and g.id_tipmov=%s and g.dtGiaIni<%s and g.id_magazz=%s)
    order by g.dtGiaIni desc  limit 1 ) <=doc.datdoc
)""" % (v_tipmov, '"%s"'% v_datinv, v_idmagaz, v_tipmov, '"%s"' % v_datinv, v_idmagaz)
            #===================================================================
            # print filter
            #===================================================================

            i.AddFilter(filter)
        #=======================================================================
        # i.SetDebug()
        #=======================================================================
        i.ClearOrders()
        i._info.raggrcat = False
        s1 = 1
        s2 = 1
        c = cn('raggrcat')
        if c:
            if c.GetValue():
                i.AddOrder('catart.codice')
                i._info.raggrcat = True
                s1 = 35
                s2 = 120
        i.AddOrder('prod.codice')
        
        i.Retrieve()
        
        parms = {}
        for name in ("incgianeg", "incgianul", "incgiapos", "incvalnul",
                     "tipoval", "id_tiplist",
                     "inchidden",
                     "qtainf", "qtasup", "valinf", "valsup", ):
            c = cn(name)
            if c is None:
                parms[name] = None
            else:
                parms[name] = c.GetValue()
        
        c = cn('calciva')
        if c is not None:
            self.dbinv.SetCalcIva(cn('calciva').GetSelection() == 1)
        wx.EndBusyCursor()        
        
        self.gridinv.Update(self, self.dbinv, parms)
        
        for key, val in self.gridinv.totals.iteritems():
            c = cn("tot%s" % key)
            if c:
                c.SetValue(val)
        
        ctr = self.FindWindowById(wdr.ID_LABGRIDINV)
        if ctr:
            if self.gridinv.modo == RSINV_MODE_BYPROGR:
                ctr.SetLabel("Giacenze e progressivi")
            else:
                ctr.SetLabel("Giacenze per magazzino")
        
        g = self.gridinv.gridinv
        sw = g.SetColumnDefaultSize
        sw(0, s1)
        sw(1, s2)
        g.AutoSizeColumns()


# ------------------------------------------------------------------------------


class InventFrame(aw.Frame):
    """
    Frame Inventario magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = InventPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class InventDialog(aw.Dialog):
    """
    Dialog Inventario magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(InventPanel(self, -1))
        self.CenterOnScreen()
