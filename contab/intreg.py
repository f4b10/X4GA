#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/intreg.py
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

import contab.pdcint_wdr as wdr

import contab
import contab.dataentry as ctb
import contab.dbtables as dbc

import awc
import awc.controls.windows as aw
import awc.controls.linktable as lt

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLE_REGCON = "Registrazioni Contabili"


class _IntRegGridMixin(object):
    
    def OnApriReg(self, event):
        reg = self.dbreg
        row = event.GetRow()
        if 0 <= row < reg.RowsCount():
            reg.MoveRow(row)
            try:
                cls = contab.RegConDialogClass(reg.id)
                if cls:
                    wx.BeginBusyCursor()
                    dlg = cls(aw.awu.GetParentFrame(self))
                    dlg.SetOneRegOnly(reg.id)
                    wx.EndBusyCursor()
                    if dlg.ShowModal() in (ctb.REG_MODIFIED, ctb.REG_DELETED):
                        evt = contab.RegChangedEvent(contab._evtREGCHANGED, 
                                                     self.GetId())
                        evt.SetEventObject(self)
                        evt.SetId(self.GetId())
                        self.GetEventHandler().AddPendingEvent(evt)
                    dlg.Destroy()
                    event.Skip()
            except:
                pass


# ------------------------------------------------------------------------------


class IntRegConGrid(dbglib.DbGridColoriAlternati, _IntRegGridMixin):
    
    def __init__(self, parent, **kwargs):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        _IntRegGridMixin.__init__(self)
        
        self.dbreg = dbc.RiepRegCon(writable=False)
        mov = self.dbreg.AddMultiJoin(bt.TABNAME_CONTAB_B, 'mov', 
                                      idLeft='id', idRight='id_reg')
        mov.AddOrder('IF(mov.tipriga="I",0,1)')
        mov.AddOrder('mov.numriga')
        self.dbreg.ShowDialog(self)
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        reg = self.dbreg
        cau = reg.config
        mov = reg.body
        riv = reg.regiva
        pdc = mov.pdc
        
        cfit, cols = self.MakeColumns()
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = mov.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        self._fgcold, self._fgcola = contab.GetColorsDA()
        self._colsegno = cn(mov, 'segno')
        self._colcaues = cn(self.dbreg.config, 'esercizio')
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(cfit)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnApriReg)
    
    def MakeColumns(self):
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        reg = self.dbreg
        cau = reg.config
        mov = reg.body
        riv = reg.regiva
        pdc = mov.pdc
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        
        cols = [( 80, (cn(reg, "datreg"),    "Data reg.",  _DAT, True)),
                ( 35, (cn(cau, "codice"),    "Cod.",       _STR, True)),
                (120, (cn(cau, "descriz"),   "Causale",    _STR, True)),
                ( 80, (cn(reg, "datdoc"),    "Data doc.",  _DAT, True)),
                ( 50, (cn(reg, "numdoc"),    "Num.",       _STR, True)),
                ( 50, (cn(reg, "numiva"),    "Prot.",      _NUM, True)),
                ( 40, (cn(riv, "codice"),    "R.IVA",      _STR, True)),
                ( 50, (cn(pdc, "codice"),    "Cod.",       _STR, True)),
                (240, (cn(pdc, "descriz"),   "Sottoconto", _STR, True)),
                (110, (cn(mov, "dare"),      "Dare",       _IMP, True)),
                (110, (cn(mov, "avere"),     "Avere",      _IMP, True)),
                ( 30, (cn(reg, "st_giobol"), "G.B.",       _CHK, True)),
                ( 30, (cn(reg, "st_regiva"), "R.I.",       _CHK, True)),
                ( 40, (cn(reg, "esercizio"), "Es.",        _STR, True)),
                (  1, (cn(reg, "id"),        "#reg",       _STR, True)),
                (  1, (cn(pdc, "id"),        "#pdc",       _STR, True)),]
        
        self.SetAnchorColumns(10, 2)
        return 8, cols
        
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        rsmov = self.dbreg.GetRecordset()
        if row<len(rsmov):
            if rsmov[row][self._colsegno] == 'D':
                fgcol = self._fgcold
            else:
                fgcol = self._fgcola
            attr.SetTextColour(fgcol)
            try:
                f = attr.GetFont()
                if rsmov[row][self._colcaues] == '1':
                    f.SetStyle(wx.FONTSTYLE_ITALIC)
                else:
                    f.SetStyle(wx.FONTSTYLE_NORMAL)
                attr.SetFont(f)
            except:
                pass
        return attr
    
    def UpdateGrid(self):
        self.ChangeData(self.dbreg.GetRecordset())


# ------------------------------------------------------------------------------


class IntRegConPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.IntRegConFunc(self)
        self.FindWindowByName('limsegno').SetSelection(0)
        pp = self.FindWindowById(wdr.ID_PANGRIDREG)
        self.gridreg = IntRegConGrid(pp)
        self.pdcid = None
        
        self.SetRegIvaFilter()
        self.CauRivEnable()
        
        for cid, col in ((wdr.ID_PANCOLMASD, self.gridreg._fgcold),
                         (wdr.ID_PANCOLMASA, self.gridreg._fgcola)):
            self.FindWindowById(cid).SetBackgroundColour(col)
        
        for evt, func, cid in (\
            (wx.EVT_BUTTON,         self.OnUpdateFilters, wdr.ID_BUTUPD),
            (lt.EVT_LINKTABCHANGED, self.OnCauChanged,    wdr.ID_CAUS),
            (lt.EVT_LINKTABCHANGED, self.OnRivChanged,    wdr.ID_RIV),
            (wx.EVT_BUTTON,         self.OnStampa,        wdr.ID_BUTPRT),
            (wx.EVT_CHECKBOX,       self.OnIncRegIva,     wdr.ID_INCREGIVA),
            (wx.EVT_CHECKBOX,       self.OnIncRegIva,     wdr.ID_INCREGSIV),):
            self.Bind(evt, func, id=cid)
        
        self.Bind(contab.EVT_REGCHANGED, self.OnUpdateFilters)
        
        self.SetName('IntRegCon')
    
    def OnIncRegIva(self, event):
        self.SetRegIvaFilter()
        event.Skip()
    
    def SetRegIvaFilter(self):
        def cn(x): return self.FindWindowByName(x)
        riv, siv = map(lambda x: cn(x).GetValue(), 
                       'incregiva incregsiv'.split())
        tr = "'S','C','A'"
        if riv:
            tr += ",'I'"
        if siv:
            tr += ",'E'"
        cn('id_caus').SetFilter("tipo IN (%s)" % tr)
        self.CauRivEnable()
        
    def OnStampa(self, event):
        self.Stampa()
        event.Skip()
    
    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        self.UpdateGrid()
        event.Skip()
    
    def OnCauChanged(self, event):
        self.CauRivEnable('id_caus')
        event.Skip()
    
    def OnRivChanged(self, event):
        self.CauRivEnable('id_regiva')
        event.Skip()
    
    def CauRivEnable(self, digname='id_caus'):
        cn = self.FindWindowByName
        if digname == 'id_caus':
            othname = 'id_regiva'
        else:
            othname = 'id_caus'
        dig, oth = map(cn, (digname, othname))
        digval = dig.GetValue()
        if dig.GetValue():
            oth.SetValueSilent(None)
        if othname == 'id_regiva' \
           and not cn('incregiva').GetValue()\
           and not cn('incregsiv').GetValue():
            oth.Disable()
        else:
            oth.Enable(not bool(digval))
        cn('id_aliqiva').Enable(cn('incregiva').IsChecked() or cn('incregsiv').IsChecked())

    def UpdateFilters(self):
        
        reg = self.gridreg.dbreg
        reg.ClearFilters()
        
        gcv = lambda ctr: self.FindWindowByName(ctr).GetValue()
        
        e = gcv('esercizio')
        if e:
            reg.AddFilter('reg.esercizio=%s', e)
        
        for col, op, name in (("reg.id",        ">=", "numreg1"),
                              ("reg.id",        "<=", "numreg2"),
                              ("reg.datreg",    ">=", "datreg1"),
                              ("reg.datreg",    "<=", "datreg2"),
                              ("reg.numdoc",    ">=", "numdoc1"),
                              ("reg.numdoc",    "<=", "numdoc2"),
                              ("reg.datdoc",    ">=", "datdoc1"),
                              ("reg.datdoc",    "<=", "datdoc2"),
                              ("reg.id_caus",   "=",  "id_caus"),
                              ("reg.id_regiva", "=",  "id_regiva")):
            val = gcv(name)
            if val:
                reg.AddFilter("%s%s%%s" % (col, op), val)
        
        val = gcv('id_aliqiva')
        if val:
            reg.AddFilter("(SELECT COUNT(testiva.id) FROM %s testiva WHERE testiva.id_reg=body.id_reg AND testiva.id_aliqiva=%%s)>0" % bt.TABNAME_CONTAB_B, val)
        
        if not gcv('incregiva'):
            reg.AddFilter("reg.tipreg IS NULL OR reg.tipreg<>'I'")
        if not gcv('incregsiv'):
            reg.AddFilter("reg.tipreg IS NULL OR reg.tipreg<>'E'")
        
        val = gcv('id_pdc')
        if val:
            reg.AddFilter("(SELECT COUNT(testmov.id) FROM %s testmov WHERE testmov.id_reg=body.id_reg AND testmov.id_pdcpa=%%s)>0" % bt.TABNAME_CONTAB_B, val)
        
        sg = gcv('stampagio')
        if sg == "S":
            reg.AddFilter("reg.st_giobol=1")
        elif sg == "N":
            reg.AddFilter("reg.st_giobol IS NULL OR reg.st_giobol<>1")
        
        i1, i2 = map(lambda x: gcv(x), 'limimp1 limimp2'.split())
        if i1 and i2:
            if i1 == i2:
                reg.AddFilter('body.importo=%s', i1)
            else:
                reg.AddFilter('body.importo>=%s AND body.importo<=%s', i1, i2)
        elif i1:
            reg.AddFilter('body.importo>=%s', i1)
        elif i2:
            reg.AddFilter('body.importo<=%s', i2)
        s = self.FindWindowByName('limsegno').GetSelection()
        if s>0:
            reg.AddFilter('body.segno=%s', " DA"[s])
        
        #reg.AddFilter('(reg.tipreg="E" AND body.numriga>1) OR (reg.tipreg<>"E" AND body.numriga=1)')
    
    def UpdateGrid(self):
        db = self.gridreg.dbreg
        if not db.Retrieve():
            awc.util.MsgDialog(self, message="Problema in lettura dati:\n\n%s"\
                               % repr(db.GetError()))
        self.gridreg.UpdateGrid()
        self.UpdateTotals()

    def UpdateTotals(self):
        reg = self.gridreg.dbreg
        
        wx.BeginBusyCursor()
        
        try:
            td = ta = 0
            cd = reg.body._GetFieldIndex("dare", inline=True)
            ca = reg.body._GetFieldIndex("avere", inline=True)
            for r in range(reg.RowsCount()):
                td += reg.GetRecordset()[r][cd] or 0
                ta += reg.GetRecordset()[r][ca] or 0
        finally:
            wx.EndBusyCursor()
        
        scv = lambda x, y: self.FindWindowByName(x).SetValue(y)
        
        if td>=ta: sd = td-ta; sa = 0
        else:      sa = ta-td; sd = 0
        
        scv("totpro_d", td)
        scv("totpro_a", ta)
        scv("totsal_d", sd)
        scv("totsal_a", sa)
        scv("totnumreg", reg.RowsCount())
    
    def Stampa(self):
        mov = dbc.RiepMovCon()
        mov.ShowDialog(self)
        mov._info.filters = self.gridreg.dbreg._info.filters
        mov.Retrieve()
        mov._info.righe_i = False
        def VediRighe_I(vedi):
            mov._info.righe_i = vedi
        mov.VediRighe_I = VediRighe_I
        tot = dbc.RiepMovCon()
        tot.ShowDialog(self)
        tot._info.filters = self.gridreg.dbreg._info.filters
        tot.AddGroupOn('regiva.tipo')
        tot.AddGroupOn('aliqiva.id')
        persegno = 'IF(regiva.tipo IN ("V", "C") AND body.segno="A" OR regiva.tipo="A" AND body.segno="D", 1, -1)'
        tot.AddTotalOf('body.imponib*%s' % persegno, 'imponib')
        tot.AddTotalOf('body.imposta*%s' % persegno, 'imposta')
        tot.AddTotalOf('body.indeduc*%s' % persegno, 'indeduc')
        tot.AddCountOf('1.0', 'righe')
        tot.AddBaseFilter('body.tipriga="I"')
        tot.ClearOrders()
        tot.AddOrder('IF(regiva.tipo="A",0,IF(regiva.tipo="V",1,2))')
        tot.AddOrder('aliqiva.codice')
        tot.Retrieve()
        mov._info.riepiva = tot
        mov._info.id_pdc_hilite = self.FindWindowByName('id_pdc').GetValue()
        rpt.Report(self, mov, "Lista registrazioni contabili", 
                   rowFilter=lambda m: m.tipriga != 'I' or m._info.righe_i)


# ------------------------------------------------------------------------------


class IntRegConFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_REGCON
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(IntRegConPanel(self, -1))


# ------------------------------------------------------------------------------


class IntRegConDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_REGCON
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(IntRegConPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLE_REGIVA = "Registrazioni IVA"


class IntRegIvaGrid(dbglib.DbGridColoriAlternati, _IntRegGridMixin):
    
    def __init__(self, parent, **kwargs):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1,
                                              size=parent.GetClientSizeTuple())
        _IntRegGridMixin.__init__(self)
        
        self.dbreg = dbc.RiepRegIva(writable=False)
        self.dbreg.ShowDialog(self)
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        reg = self.dbreg
        riv = reg.regiva
        cau = reg.config
        mov = reg.body
        pdc = mov.pdc
        
        ncimponib = cn(reg, "total_imponib")
        ncimposta = cn(reg, "total_imposta")
        ncindeduc = cn(reg, "total_indeduc")
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (cn(reg, "datreg"),    "Data reg.",    _DAT, True)),
            ( 35, (cn(cau, "codice"),    "Cod.",         _STR, True)),
            (120, (cn(cau, "descriz"),   "Causale",      _STR, True)),
            ( 50, (cn(pdc, "codice"),    "Cod.",         _STR, True)),
            (220, (cn(pdc, "descriz"),   "Sottoconto",   _STR, True)),
            ( 50, (cn(reg, "numdoc"),    "Num.doc.",     _STR, True)),
            ( 80, (cn(reg, "datdoc"),    "Data doc.",    _DAT, True)),
            ( 60, (cn(reg, "numiva"),    "Prot.",        _NUM, True)),
            ( 40, (cn(riv, "codice"),    "R.IVA",        _STR, True)),
            (110, (ncimponib,            "Imponibile",   _IMP, True)),
            (110, (ncimposta,            "Imposta",      _IMP, True)),
            (110, (ncindeduc,            "Indeducibile", _IMP, True)),
            ( 35, (cn(reg, 'st_regiva'), "St.",          _CHK, True)),
            (  1, (cn(reg, 'id'),        "#reg",         _STR, True)),
            (  1, (cn(cau, 'id'),        "#cau",         _STR, True)),
            (  1, (cn(pdc, 'id'),        "#pdc",         _STR, True)),
            (  1, (cn(riv, 'id'),        "#riv",         _STR, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = mov.GetRecordset()
        
        self.SetData( rs, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(4)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnApriReg)
    
    def UpdateGrid(self):
        self.ChangeData(self.dbreg.GetRecordset())


# ------------------------------------------------------------------------------


class IntRegIvaPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.IntRegIvaFunc(self)
        
        pp = self.FindWindowById(wdr.ID_PANGRIDREG)
        self.gridreg = IntRegIvaGrid(pp)
        self.pdcid = None
        
        for evt, func, cid in (\
            (wx.EVT_BUTTON, self.OnUpdateFilters, wdr.ID_BUTUPD),\
            (wx.EVT_BUTTON, self.OnStampa,        wdr.ID_BUTPRT)):
            self.Bind(evt, func, id=cid)
        
        self.Bind(contab.EVT_REGCHANGED, self.OnUpdateFilters)
        
        self.SetName('IntRegIva')
    
    def OnStampa(self, event):
        db = self.gridreg.dbreg
        cn = self.FindWindowByName
        def SPV(key, value=None):
            if value is None:
                value = cn(key).GetValue()
            db._info.SetPrintValue(key, value)
        #valori di stampa per i filtri
        ri = cn('id_regiva')
        SPV('regivacod', ri.GetValueCod())
        SPV('regivades', ri.GetValueDes())
        cc = cn('id_caus')
        SPV('causalecod', cc.GetValueCod())
        SPV('causaledes', cc.GetValueDes())
        for name in 'datreg1 datreg2 numreg1 numreg2 datdoc1 datdoc2 numdoc1 numdoc2 numpro1 numpro2'.split():
            SPV(name)
        #valori di stampa per totali
        for tipo in 'AVC':
            SPV('totimponib_%s' % tipo.lower())
            SPV('totimposta_%s' % tipo.lower())
            SPV('totindeduc_%s' % tipo.lower())
            SPV('totnumreg_%s' % tipo.lower())
        rpt.Report(self, db, 'Lista Registrazioni IVA')
    
    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        self.UpdateGrid()
        event.Skip()
    
    def UpdateFilters(self):
        
        reg = self.gridreg.dbreg
        reg.ClearFilters()
        
        def gcv(ctr):
            return self.FindWindowByName(ctr).GetValue()
        
        for col, op, name in (("reg.id",     ">=%s", "numreg1"),\
                              ("reg.id",     "<=%s", "numreg2"),\
                              ("reg.datreg", ">=%s", "datreg1"),\
                              ("reg.datreg", "<=%s", "datreg2"),\
                              ("reg.datdoc", ">=%s", "datdoc1"),\
                              ("reg.datdoc", "<=%s", "datdoc2"),\
                              ("reg.numdoc", ">=%s", "numdoc1"),\
                              ("reg.numdoc", "<=%s", "numdoc2"),\
                              ("reg.numiva", ">=%s", "numpro1"),\
                              ("reg.numiva", "<=%s", "numpro2")):
            val = gcv(name)
            if val: reg.AddFilter("%s%s" % (col, op), val)
        
        for col in ("id_caus", "id_regiva"):
            val = gcv(col)
            if val: reg.AddFilter("reg.%s=%%s" % col, val)
            else:
                if col == "id_regiva":
                    reg.AddFilter("reg.%s IS NOT NULL" % col)
        
        for name, flag in (('stampareg', 'st_regiva'),
                           ('stampagio', 'st_giobol')):
            sr = gcv(name)
            if sr == "S":
                reg.AddFilter("reg.%s=1" % flag)
            elif sr == "N":
                reg.AddFilter("reg.%s IS NULL OR reg.%s<>1" % (flag, flag))
    
    def UpdateGrid(self):
        db = self.gridreg.dbreg
        if not db.Retrieve():
            awc.util.MsgDialog("Problema in lettura dati:\n\n%s"\
                               % db.GetError())
        self.gridreg.UpdateGrid()
        self.UpdateTotals()
    
    def UpdateTotals(self):
        
        reg = self.gridreg.dbreg
        
        totali = {"A": [0,0,0,0],\
                  "V": [0,0,0,0],\
                  "C": [0,0,0,0]}
        cimponib, cimposta, cindeduc =\
                map(lambda x: reg._GetFieldIndex("total_%s" % x, inline=True),\
                    ("imponib", "imposta", "indeduc"))
        ctipriv = reg.regiva._GetFieldIndex("tipo", inline=True)
                
        rs = reg.GetRecordset()
        
        wx.BeginBusyCursor()
        try:
            for r in range(reg.RowsCount()):
                tipriv = rs[r][ctipriv]
                totali[tipriv][0] += rs[r][cimponib] or 0
                totali[tipriv][1] += rs[r][cimposta] or 0
                totali[tipriv][2] += rs[r][cindeduc] or 0
                totali[tipriv][3] += 1
        finally:
            wx.EndBusyCursor()
        
        scv = lambda x, y: self.FindWindowByName(x).SetValue(y)
        
        for tipriv in "AVC":
            for n, col in enumerate(("imponib", "imposta", "indeduc", "numreg")):
                scv("tot%s_%s" % (col, tipriv.lower()), totali[tipriv][n])
    
    #def StampaMastrino(self):
        #db = self.gridreg.dbmas
        #rpt.Report(self, db, "Mastrino")


# ------------------------------------------------------------------------------


class IntRegIvaDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_REGIVA
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(IntRegIvaPanel(self, -1))


# ------------------------------------------------------------------------------


class IntRegIvaFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_REGIVA
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(IntRegIvaPanel(self, -1))


# ------------------------------------------------------------------------------


FRAME_TITLE_UTIIVA = "Utilizzo Aliquote IVA"


class IntAliqIvaGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbmov):
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbmov = dbmov
        self.dbmov.ShowDialog(self)
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        mov = self.dbmov
        reg = mov.reg
        riv = reg.regiva
        cau = reg.config
        pdc = mov.pdc
        alq = mov.aliqiva
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _CHK = gl.GRID_VALUE_BOOL+":1,0"
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 80, (cn(reg, "datreg"),     "Data reg.",    _DAT, True)),
            ( 35, (cn(cau, "codice"),     "Cod.",         _STR, True)),
            (120, (cn(cau, "descriz"),    "Causale",      _STR, True)),
            ( 50, (cn(pdc, "codice"),     "Cod.",         _STR, True)),
            (220, (cn(pdc, "descriz"),    "Sottoconto",   _STR, True)),
            ( 50, (cn(reg, "numdoc"),     "Num.doc.",     _STR, True)),
            ( 80, (cn(reg, "datdoc"),     "Data doc.",    _DAT, True)),
            ( 60, (cn(reg, "numiva"),     "Prot.",        _NUM, True)),
            ( 40, (cn(riv, "codice"),     "R.IVA",        _STR, True)),
            ( 40, (cn(alq, "codice"),     "Aliq.",        _STR, True)),
            (110, (cn(mov, "valimponib"), "Imponibile",   _IMP, True)),
            (110, (cn(mov, "valimposta"), "Imposta",      _IMP, True)),
            (110, (cn(mov, "valindeduc"), "Indeducibile", _IMP, True)),
            ( 35, (cn(reg, 'st_regiva'),  "St.",          _CHK, True)),
            (  1, (cn(reg, 'id'),         "#reg",         _STR, True)),
            (  1, (cn(cau, 'id'),         "#cau",         _STR, True)),
            (  1, (cn(pdc, 'id'),         "#pdc",         _STR, True)),
            (  1, (cn(riv, 'id'),         "#riv",         _STR, True)),
        )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = mov.GetRecordset()
        
        self.SetData( rs, colmap, canedit, canins)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(4)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnApriReg)
    
    def OnApriReg(self, event):
        mov = self.dbmov
        row = event.GetRow()
        if 0 <= row < mov.RowsCount():
            mov.MoveRow(row)
            try:
                cls = contab.RegConDialogClass(mov.reg.id)
                if cls:
                    wx.BeginBusyCursor()
                    dlg = cls(self)
                    dlg.SetOneRegOnly(mov.reg.id)
                    wx.EndBusyCursor()
                    if dlg.ShowModal() in (ctb.REG_MODIFIED, ctb.REG_DELETED):
                        evt = contab.RegChangedEvent(contab._evtREGCHANGED, 
                                                     self.GetId())
                        evt.SetEventObject(self)
                        evt.SetId(self.GetId())
                        self.GetEventHandler().AddPendingEvent(evt)
                    dlg.Destroy()
                    event.Skip()
            except:
                pass


# ------------------------------------------------------------------------------


class IntAliqIvaPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.IntAliqIvaFunc(self)
        
        self.dbmov = dbc.MovAliqIvaTable()
        self.dbmov.AddBaseFilter("body.tipriga IN ('I', 'E', 'O')")
        def cn(x):
            return self.FindWindowByName(x)
        self.gridreg = IntAliqIvaGrid(cn('pangridmov'), self.dbmov)
        self.pdcid = None
        
        for evt, func, cid in (\
            (wx.EVT_BUTTON, self.OnUpdateFilters, wdr.ID_BUTUPD),\
            (wx.EVT_BUTTON, self.OnStampa,        wdr.ID_BUTPRT)):
            self.Bind(evt, func, id=cid)
        
        self.Bind(contab.EVT_REGCHANGED, self.OnUpdateFilters)
        
        self.SetName('IntUsoAliq')
    
    def OnStampa(self, event):
        db = self.dbmov
        cn = self.FindWindowByName
        def SPV(key, value=None):
            if value is None:
                value = cn(key).GetValue()
            db._info.SetPrintValue(key, value)
        #valori di stampa per i filtri
        al = cn('id_aliqiva')
        SPV('aliqivacod', al.GetValueCod())
        SPV('aliqivades', al.GetValueDes())
        ri = cn('id_regiva')
        SPV('regivacod', ri.GetValueCod())
        SPV('regivades', ri.GetValueDes())
        cc = cn('id_caus')
        SPV('causalecod', cc.GetValueCod())
        SPV('causaledes', cc.GetValueDes())
        for name in 'datreg1 datreg2 numreg1 numreg2 datdoc1 datdoc2 numdoc1 numdoc2 numpro1 numpro2'.split():
            SPV(name)
        #valori di stampa per totali
        for tipo in 'AVC':
            SPV('totimponib_%s' % tipo.lower())
            SPV('totimposta_%s' % tipo.lower())
            SPV('totindeduc_%s' % tipo.lower())
            SPV('totnumreg_%s' % tipo.lower())
        rpt.Report(self, db, 'Utilizzo Aliquote IVA')
        event.Skip()
    
    def OnUpdateFilters(self, event):
        self.UpdateFilters()
        self.UpdateGrid()
        event.Skip()
    
    def UpdateFilters(self):
        
        mov = self.dbmov
        mov.ClearFilters()
        reg = mov.reg
        
        def gcv(ctr):
            return self.FindWindowByName(ctr).GetValue()
        
        for col, op, name in (("reg.id",     ">=%s", "numreg1"),\
                              ("reg.id",     "<=%s", "numreg2"),\
                              ("reg.datreg", ">=%s", "datreg1"),\
                              ("reg.datreg", "<=%s", "datreg2"),\
                              ("reg.numdoc", ">=%s", "numdoc1"),\
                              ("reg.numdoc", "<=%s", "numdoc2"),\
                              ("reg.numiva", ">=%s", "numpro1"),\
                              ("reg.numiva", "<=%s", "numpro2")):
            val = gcv(name)
            if val: mov.AddFilter("%s%s" % (col, op), val)
        
        for col in "id_caus id_regiva".split():
            val = gcv(col)
            if val: mov.AddFilter("reg.%s=%%s" % col, val)
            else:
                if col == "id_regiva":
                    mov.AddFilter("reg.%s IS NOT NULL" % col)
        
        val = gcv('id_aliqiva')
        if val:
            mov.AddFilter("body.id_aliqiva=%s", val)
        else:
            mov.AddFilter("body.id_aliqiva IS NOT NULL")
        
        for name, flag in (('stampareg', 'st_regiva'),
                           ('stampagio', 'st_giobol')):
            sr = gcv(name)
            if sr == "S":
                mov.AddFilter("reg.%s=1" % flag)
            elif sr == "N":
                mov.AddFilter("reg.%s IS NULL OR reg.%s<>1" % (flag, flag))
    
    def UpdateGrid(self):
        db = self.dbmov
        if not db.Retrieve():
            awc.util.MsgDialog("Problema in lettura dati:\n\n%s"\
                               % db.GetError())
        self.gridreg.ResetView()
        self.UpdateTotals()

    def UpdateTotals(self):
        def gc(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        mov = self.dbmov
        coltipriva = gc(mov.reg.regiva, 'tipo')
        colimponib = gc(mov, 'valimponib')
        colimposta = gc(mov, 'valimposta')
        colindeduc = gc(mov, 'valindeduc')
        colidreg = gc(mov.reg, 'id')
        totali = [0, #imponibile,
                  0, #imposta,
                  0, #indeducibile
                  0] #numero operazioni
        def _totali():
            return []+totali
        tot = {'A': _totali(),
               'V': _totali(),
               'C': _totali(),}
        rs = mov.GetRecordset()
        wx.BeginBusyCursor()
        try:
            for n in range(mov.RowsCount()):
                tipreg = rs[n][coltipriva]
                if (tipreg or ' ') in 'AVC':
                    tot[tipreg][0] += rs[n][colimponib]
                    tot[tipreg][1] += rs[n][colimposta]
                    tot[tipreg][2] += rs[n][colindeduc]
                    tot[tipreg][3] += 1
                else:
                    aw.awu.MsgDialog(self, "Registro iva non valido: registrazione #%d"%colidreg, style=wx.ICON_ERROR)
                    break
        finally:
            wx.EndBusyCursor()
        
        cn = self.FindWindowByName
        for tipo in 'AVC':
            t = tot[tipo]
            cn('totimponib_%s' % tipo.lower()).SetValue(t[0])
            cn('totimposta_%s' % tipo.lower()).SetValue(t[1])
            cn('totindeduc_%s' % tipo.lower()).SetValue(t[2])
            cn('totnumreg_%s' % tipo.lower()).SetValue(t[3])
    
    #def StampaMastrino(self):
        #db = self.gridreg.dbmas
        #rpt.Report(self, db, "Mastrino")


# ------------------------------------------------------------------------------


class IntAliqIvaDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_UTIIVA
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(IntAliqIvaPanel(self, -1))


# ------------------------------------------------------------------------------


class IntAliqIvaFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_UTIIVA
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(IntAliqIvaPanel(self, -1))
