#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/prodvencli.py
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

import magazz.stat.stat_wdr as wdr

import magazz.dbtables as dbm
import magazz.stat.dbtables as dbs
bt = dbm.Env.Azienda.BaseTab

import magazz.maglib as maglib

from awc.controls.linktable import EVT_LINKTABCHANGED

import report as rpt


FRAME_TITLE = "Sintesi prodotti fatturati per cliente"


class ProdVenCliGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbfat, **kwargs):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        self.dbfat = dbfat
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _QTA = bt.GetMagQtaMaskInfo()
        _PRZ = bt.GetMagPreMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 50, (cn(dbfat, "pdc_codice"),   "Cod.",         _STR, True)),
            (220, (cn(dbfat, "pdc_descriz"),  "Cliente",      _STR, True)),
            ( 80, (cn(dbfat, "prod_codice"),  "Codice",       _STR, True)),
            (220, (cn(dbfat, "prod_descriz"), "Prodotto",     _STR, True)),
            ( 60, (cn(dbfat, "totqta"),       "Tot.Qta",      _QTA, True)),
            ( 80, (cn(dbfat, "lastdat"),      "Ultima vend.", _DAT, True)),
            ( 60, (cn(dbfat, 'lastqta'),      "Quantità",     _QTA, True)),
            ( 70, (cn(dbfat, 'lastprz'),      "Prezzo",       _PRZ, True)),
            ( 40, (cn(dbfat, 'lastsco'),      "Sc.%",         _SCO, True)),
            ( 70, (cn(dbfat, 'lastscmq'),     "Sc.Mce",       _QTA, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        self.SetData(dbfat.GetRecordset(), colmap, canedit, canins)
        
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


# ------------------------------------------------------------------------------


class ProdVenCliPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.PdcFtProdFunc(self)
        
        tipana = dbm.dba.PdcTip()
        tipana.Retrieve()
        tipi = [str(t.id) for t in tipana if t.tipo == 'C']
        if tipi:
            for cid in (wdr.ID_PDC1, wdr.ID_PDC2):
                self.FindWindowById(cid).SetFilter('pdc.id_tipo IN (%s)'\
                                                   % ','.join(tipi))
        else:
            aw.awu.MsgDialog(self, 'Nessun tipo anagrafico per i clienti')
        
        self.dbfat = dbs.SintesiProVenCli()
        
        ci = lambda x: self.FindWindowById(x)
        for cid in (wdr.ID_PDC1, wdr.ID_PDC2):
            ci(cid).tipo = 'descriz'
        
        ci(wdr.ID_ORDER).SetSelection(dbm.Env.Azienda.GetAutom('magordfta', 0))
        
        self.gridfta = ProdVenCliGrid(ci(wdr.ID_PANGRIDSINT), self.dbfat)
        
        self.Bind(EVT_LINKTABCHANGED, self.OnLinkTabChanged)
        for cid, func in ((wdr.ID_UPDATE, self.OnUpdateFilters),
                          (wdr.ID_PRINT, self.OnPrint)):
            self.Bind(wx.EVT_BUTTON, func, id=cid)
    
    def OnPrint(self, event):
        self.Print()
        event.Skip()
    
    def Print(self):
        rpt.Report(self, self.dbfat, 'Scheda vendite cliente')
    
    def OnLinkTabChanged(self, event):
        if hasattr(self, '_tabchanging'):
            return
        self._tabchanging = True
        ctr = event.GetEventObject()
        if hasattr(ctr, 'tipo'):
            field = ctr.tipo
            if field == 'descriz':
                val = ctr.GetValueDes()
            else:
                val = ctr.GetValue()
        else:
            field = 'codice'
            val = ctr.GetValueCod()
        name = ctr.GetName()
        if name.endswith('1'):
            ctr2 = self.FindWindowByName(name[:-1]+'2')
            if ctr2:
                v2 = ctr2.GetValue()
                ctr2.SetValue(None)
                if val:
                    ctr2.SetFilter("%s>='%s'" % (field, val))
                else:
                    ctr2.SetFilter('1')
                ctr2.SetValue(v2)
        elif name.endswith('2'):
            ctr1 = self.FindWindowByName(name[:-1]+'1')
            if ctr1:
                if val:
                    ctr1.SetFilter("%s<='%s'" % (field, val))
                else:
                    ctr1.SetFilter('1')
        def delvar():
            del self._tabchanging
        wx.CallAfter(delvar)
        event.Skip()
    
    def OnUpdateFilters(self, event):
        cn = lambda x: self.FindWindowByName(x)
        #filtri relativi ai clienti
        filter = {'anag': [],
                  'prod': [],
                  'mov':  []}
        for key, names in (('anag', ('pdc', 'age', 'zona')),
                           ('prod', ('tipart', 'catart', 'gruart', 'marart', 'fornit'))):
            for name in names:
                filt = filter[key]
                c1, c2 = cn(name+'1'), cn(name+'2')
                if hasattr(c1, 'tipo'):
                    tipo = c1.tipo
                else:
                    tipo = 'codice'
                if tipo == 'codice':
                    v1 = c1.GetValueCod()
                    v2 = c2.GetValueCod()
                else:
                    v1 = cn(name+'1').GetValueDes()
                    v2 = cn(name+'2').GetValueDes()
                if v1 or v2:
                    if v1 == v2:
                        filt.append("%s.%s='%s'" % (name, tipo, v1))
                    else:
                        if v1:
                            filt.append("%s.%s>='%s'" % (name, tipo, v1))
                        if v2:
                            filt.append("%s.%s<='%s'" % (name, tipo, v2))
        for name, op in (('data1', '>='),
                         ('data2', '<=')):
            v = cn(name).GetValue()
            if v:
                filter['mov'].append("doc.datdoc%s'%s'"\
                                 % (op, v.Format('%Y%m%d')))
        order = "PD"[cn('order').GetSelection()]
        wait = aw.awu.WaitDialog(self)
        af = lambda x: " AND ".join(x)
        self.dbfat.Retrieve(af(filter['anag']), 
                            af(filter['prod']),
                            af(filter['mov']), order)
        wait.Destroy()
        self.gridfta.ChangeData(self.dbfat.GetRecordset())
        event.Skip()


# ------------------------------------------------------------------------------


class ProdVenCliFrame(aw.Frame):
    """
    Frame Interrogazione documenti magazzino.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ProdVenCliPanel(self, -1))
        self.CenterOnScreen()
