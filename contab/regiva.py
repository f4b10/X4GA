#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/regiva.py
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
import awc.util as awu

import awc.controls.windows as aw
from awc.controls.linktable import EVT_LINKTABCHANGED
from awc.controls.datectrl import EVT_DATECHANGED

import Env
import contab.dbtables as dbc

from contab import regiva_wdr as wdr

import report as rpt

_evtREGSEL = wx.NewEventType()
EVT_REGSEL = wx.PyEventBinder(_evtREGSEL, 1)


class RegSelEvent(wx.PyCommandEvent):
    def __init__(self, evtType):
        wx.PyCommandEvent.__init__(self, evtType)
        self._selection = None

    def SetSelection(self, val):
        self._selection = val

    def GetSelection(self):
        return self._selection


# ------------------------------------------------------------------------------


FRAME_TITLE = "Registro IVA"


adb = dbc.adb
bt = Env.Azienda.BaseTab
stdcolor = Env.Azienda.Colours

colprot = None
coldata = None
colrimp = None
colriva = None
colaimp = None
colaiva = None
colaind = None


class GridReg(dbglib.DbGridColoriAlternati):
    """
    Griglia registrazioni
    """
    def __init__(self, parent, dbreg):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable registro iva (derivati da contab.dbtables.RegIva)
        """
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, 
                                              size=parent.GetClientSizeTuple())
        
        self.dbreg = dbreg
        reg = self.dbreg
        cau = reg.cau
        pdc = reg.pdc
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER+":6"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        
        #colcodart = pro._GetFieldIndex("codice", inline=True)
        
        global colprot, coldata, colrimp, colriva
        colprot = cn(reg, 'numiva')
        coldata = cn(reg, 'datreg')
        colrimp = cn(reg, 'total_imponib')
        colriva = cn(reg, 'total_imposta')
        colrind = cn(reg, 'total_indeduc')
        
        if reg.tipana == "C":
            desanag = "Cliente"
        else:
            desanag = "Fornitore"
        
        cols = (\
            ( 60, (cn(reg, 'numiva'),  "Prot.",     _NUM, True )),\
            ( 80, (cn(reg, 'datreg'),  "Data reg.", _DAT, True )),\
            (100, (cn(cau, 'descriz'), "Causale",   _STR, True )),\
            ( 80, (cn(reg, 'datdoc'),  "Data Doc.", _DAT, True )),\
            ( 80, (cn(reg, 'numdoc'),  "Num.",      _STR, True )),\
            ( 50, (cn(pdc, 'codice'),  "Cod.",      _STR, True )),\
            (200, (cn(pdc, 'descriz'), desanag,     _STR, True )),\
            (120, (           colrimp, "Imponib.",  _IMP, True )),\
            (120, (           colriva, "Imposta",   _IMP, True )),\
            (120, (           colrind, "Indeduc.",  _IMP, True )),\
            )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        links = None
        
        afteredit = None
        self.SetData( self.dbreg._info.rs, colmap, canedit, canins,\
                      links, afteredit)
        #self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(6)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_SELECT_CELL, self.OnSelected)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        readonly = True
        if not self.dbreg.rei.noprot:
            rowreg = self.dbreg.GetRecordset()[row]
            fgcol = stdcolor.NORMAL_FOREGROUND
            bgcol = stdcolor.NORMAL_BACKGROUND
            if rscol == colprot and row>0:
                pv = lambda r: self.dbreg.GetRecordset()[r][colprot] or 0
                ppre = pv(row-1)
                patt = pv(row)
                if patt != ppre+1:
                    bgcol = wx.RED
            elif rscol == coldata and row>0:
                pv = lambda r: self.dbreg.GetRecordset()[r][coldata]
                dpre = pv(row-1)
                datt = pv(row)
                if datt < dpre:
                    bgcol = wx.RED
            if rscol in (colrimp, colriva) and rowreg[rscol]<0:
                fgcol = wx.RED
            attr.SetTextColour(fgcol)
            attr.SetBackgroundColour(bgcol)
        attr.SetReadOnly(readonly)
        return attr

    def OnSelected(self, event):
        row = event.GetRow()
        self.dbreg.MoveRow(row)
        evt = RegSelEvent(_evtREGSEL)
        evt.SetEventObject(self)
        evt.SetId(self.GetId())
        evt.SetSelection(self.dbreg.id)
        #self.GetEventHandler().ProcessEvent(evt)
        self.GetEventHandler().AddPendingEvent(evt)
        event.Skip()


# ------------------------------------------------------------------------------


class GridAliq(dbglib.DbGridColoriAlternati):
    """
    Griglia aliquote registrazione
    """
    def __init__(self, parent, dbreg):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable registro iva (derivati da contab.dbtables.RegIva)
        """
        
        size = parent.GetClientSizeTuple()
        
        self.dbreg = dbreg
        reg = self.dbreg
        mov = reg.mov
        iva = mov.iva
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        global colaimp, colaiva
        colaimp = cn(mov, 'total_imponib')
        colaiva = cn(mov, 'total_imposta')
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRC = bt.GetPerGenMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = [
            ( 40, (cn(iva, 'codice'),  "Cod.",      _STR, True )),
            (130, (cn(iva, 'descriz'), "Aliquota",  _STR, True )),
            ( 60, (cn(iva, 'perciva'), "%IVA",      _PRC, True )),
            ( 60, (cn(iva, 'percind'), "%Ind.",     _PRC, True )),]
        if bt.TIPO_CONTAB == "S":
            pdc = mov.pdcpa
            cols.append(( 50, (cn(pdc, 'codice'),  "Cod.",       _STR, True)))
            cols.append((180, (cn(pdc, 'descriz'), "Sottoconto", _STR, True)))
        cols += [
            (130, (           colaimp, "Imponib.",  _IMP, True )),
            (130, (           colaiva, "Imposta",   _IMP, True )),]
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData( self.dbreg.mov._info.rs, colmap, canedit, canins,\
                      links, afteredit)
        #self.SetRowLabelSize(100)
        #self.SetRowLabelAlignment(wx.ALIGN_RIGHT, wx.ALIGN_BOTTOM)
        #self.SetRowDynLabel(self.GetRowLabel)
        #self.SetCellDynAttr(self.GetAttr)
        
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

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        try:
            readonly = True
            rowmov = self.dbreg.mov.GetRecordset()[row]
            fgcol = stdcolor.NORMAL_FOREGROUND
            if rscol in (colaimp, colaiva) and rowmov[rscol]<0:
                fgcol = wx.RED
            attr.SetReadOnly(readonly)
            attr.SetTextColour(fgcol)
        except:
            pass
        return attr


# ------------------------------------------------------------------------------


class GridTotAliq(dbglib.DbGridColoriAlternati):
    """
    Griglia totali aliquote
    """
    def __init__(self, parent, dbreg):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable totali aliquote (DbMem)
        """
        
        size = parent.GetClientSizeTuple()
        
        self.dbriep = dbreg._riepaliq
        mov = self.dbriep
        iva = mov.iva
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        global colaimp, colaiva
        colaimp = cn(mov, 'total_imponib')
        colaiva = cn(mov, 'total_imposta')
        colaind = cn(mov, 'total_indeduc')
        
        _STR = gl.GRID_VALUE_STRING
        _PRC = bt.GetPerGenMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 50, (cn(iva, 'codice'),  "Cod.",      _STR, True )),\
            (180, (cn(iva, 'descriz'), "Aliquota",  _STR, True )),\
            ( 30, (cn(iva, 'tipo'),    "Tipo",      _STR, True )),\
            ( 60, (cn(iva, 'perciva'), "%IVA",      _PRC, True )),\
            ( 60, (cn(iva, 'percind'), "%Ind.",     _PRC, True )),\
            (130, (           colaimp, "Imponib.",  _IMP, True )),\
            (130, (           colaiva, "Imposta",   _IMP, True )),\
            (130, (           colaind, "Indeduc.",  _IMP, True )),\
            )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData( self.dbriep.GetRecordset(), colmap, canedit, canins,\
                      links, afteredit)
        #self.SetCellDynAttr(self.GetAttr)
        
        coltipo = cn(iva, 'tipo')
        for label, cbfilt in (\
            ("Totali:",
             lambda rs, row: not rs[row][coltipo]),
            ("Acquisti CEE:",
             lambda rs, row: rs[row][coltipo] == "C"),
            ("Vendite in split payment:",
             lambda rs, row: rs[row][coltipo] == "S")):
            self.AddTotalsRow(1, label, (colaimp, colaiva, colaind), cbfilt)
        
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
        
        self.ResetView()

    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        try:
            readonly = True
            if self.IsOnTotalRow(row):
                if self.CurrentTotalRow(row) == 0:
                    fgcol = 'blue'
                else:
                    fgcol = 'blueviolet'
            else:
                fgcol = stdcolor.NORMAL_FOREGROUND
            attr.SetReadOnly(readonly)
            attr.SetTextColour(fgcol)
        except:
            pass
        return attr


# ------------------------------------------------------------------------------


class RegIvaPanel(aw.Panel):
    
    gridreg = None
    gridaliq = None
    gridriep = None
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        
        self.dbreg = None
        
        wdr.RegIvaFunc(self)
        
        ci = self.FindWindowById
        
        tipi = {'P': ("Stampa Provvisoria",\
                      """Vengono estratte solo le registrazioni IVA non """
                      """ancora stampate in modo definitivo.\nLa stampa può """
                      """essere fatta in qualsiasi momento."""),\
                'D': ("Stampa Definitiva",\
                      """Vengono estratte solo le registrazioni IVA mai """
                      """stampate sul registro o stampate in modo """
                      """provvisorio.\nLa stampa può essere eseguita solo """
                      """una volta"""),\
                'R': ("Ristampa",\
                      """Vengono estratte solo le registrazioni IVA già """
                      """stampate in modo definitivo""")}
        self.tipista = tipi
        
        ci(wdr.ID_TIPOSTA).SetDataLink('tiposta', 'PDR')
        self.SetTipoSta('P')
        
        ci(wdr.ID_SPLITREG).SetSashPosition(ci(wdr.ID_SPLITREG).GetSize()[1]-100)
        ci(wdr.ID_SPLITREG).SetSashGravity(1)
        
        self.EnableIntestaz()
        
        NPC = wx.EVT_NOTEBOOK_PAGE_CHANGED
        for evt, func, cid in (\
            (wx.EVT_RADIOBOX,    self.OnTipoStaChanged, wdr.ID_TIPOSTA),
            (wx.EVT_BUTTON,      self.OnStampa,         wdr.ID_BUTSTA),
            (wx.EVT_BUTTON,      self.OnUpdateGridReg,  wdr.ID_BUTUPD),
            (NPC,                self.OnZoneChanged,    wdr.ID_GRIDZONE),
            (EVT_LINKTABCHANGED, self.OnRegIvaChanged,  wdr.ID_REGIVA),
            (EVT_DATECHANGED,    self.OnDateChanged,    wdr.ID_DATMIN),
            (wx.EVT_CHECKBOX,    self.OnIntestaz,       wdr.ID_INTATT)):
            self.Bind(evt, func, id=cid)
        
        cn = self.FindWindowByName
        cn('regiva').SetFocus()
        
        self.Bind(wx.EVT_RADIOBOX, self.OnEnableButtonUpdate, cn('tiposta'))
        self.Bind(EVT_LINKTABCHANGED, self.OnEnableButtonUpdate, cn('regiva'))
        for name in 'datmin datmax radate'.split():
            self.Bind(EVT_DATECHANGED, self.OnEnableButtonUpdate, cn(name))
        self.Bind(EVT_REGSEL, self.OnUpdateGridAliq)
    
    def OnEnableButtonUpdate(self, event):
        self.EnableButtonUpdate()
        event.Skip()
    
    def OnIntestaz(self, event):
        self.EnableIntestaz(setfocus=True)
        event.Skip()
    
    def CreateGrids(self):
        
        cn = self.FindWindowById
        
        if self.gridreg:
#            self.gridreg.Destroy()
            wx.CallAfter(self.gridreg.Destroy)
        self.gridreg = GridReg(cn(wdr.ID_PANGRIDREG), self.dbreg)
        
        if self.gridaliq:
#            self.gridaliq.Destroy()
            wx.CallAfter(self.gridaliq.Destroy)
        self.gridaliq = GridAliq(cn(wdr.ID_PANGRIDALIQ), self.dbreg)

    def CreateGridTotAliq(self):
        
        cn = lambda x: self.FindWindowById(x)
        
        if self.gridriep:
#            self.gridriep.Destroy()
            wx.CallAfter(self.gridriep.Destroy)
        self.gridriep = GridTotAliq(cn(wdr.ID_PANGRIDRIEP), self.dbreg)
    
    def OnTipoStaChanged(self, event):
        self.SetTipoSta(event.GetEventObject().GetValue())
        cn = self.FindWindowByName
        def setfocus():
            cn('regiva').SetFocus()
        wx.CallAfter(setfocus)
        event.Skip()
    
    def SetTipoSta(self, tiposta):
        """
        Imposta tipo stampa:
            "P" stampa provvisoria
            "D" stampa definitiva
            "R" ristampa
        """
        if not tiposta in "PDR":
            raise Exception, "Tipo stampa errato (%s)" % tiposta
        self.tiposta = tiposta
        cn = lambda x: self.FindWindowById(x)
        cn(wdr.ID_TIPOTIT).SetLabel(self.tipista[self.tiposta][0])
        cn(wdr.ID_TIPODES).SetLabel(self.tipista[self.tiposta][1])
        self.UpdateLastDatNum()
    
    def OnStampa(self, event):
        self.Stampa()
        event.Skip()
    
    def Stampa(self):
        reg = self.dbreg
        r = reg._riepaliq
        #per compatilibità alias tabelle con riep.iva fatto x lista mov.
        r.reg.regiva = r.reg.rei
        r.aliqiva = r.iva
        if self.FindWindowById(wdr.ID_GRIDZONE).GetSelection() == 2:
            name = 'Riepilogo IVA'
            db = r
        else:
            name = 'Registro IVA'
            db = reg
        def cn(x):
            return self.FindWindowByName(x)
        for c in 'tiposta intatt intdes intanno intpag'.split():
            for o in (reg, r):
                setattr(o._info, c, cn(c).GetValue())
        r._info.noperiodo = True #evita di stampare il periodo su riep. iva
        s = rpt.Report(self, db, name)
        if reg._tipostampa == "D":
            q = awu.MsgDialog(self, message=\
                              "Confermi l'aggiornamento del database con le "\
                              "informazioni stampate?",
                              style=wx.YES_NO|wx.YES_DEFAULT|wx.ICON_QUESTION)
            if q == wx.ID_YES:
                wait = awu.WaitDialog(self, message=\
                                      "Aggiornamento dati in corso",
                                      maximum=reg.RowsCount())
                try:
                    e = self.dbreg.ElaboraDefin(lambda n,reg: wait.SetValue(n))
                    ri = adb.DbTable(bt.TABNAME_REGIVA, 'rei')
                    if ri.Get(reg._rivid):
                        p = s.usedReport.oCanvas.userVariableList['intpag']
                        ri.intanno = cn('intanno').GetValue()
                        ri.intpag = p.valore
                        reg.MoveLast()
                        ri.lastprtnum = reg.numiva
                        ri.lastprtdat = reg._datmax
                        ri.Save()
                finally:
                    wait.Destroy()
                if e:
                    awu.MsgDialog(self, "Aggiornamento correttamente effettuato")
                    self.GetParent().Close()
    
    def OnRegIvaChanged(self, event):
        rivid = event.GetEventObject().GetValue()
        if rivid is not None:
            self.dbreg = dbc.RegIva(rivid)
            self.dbreg.ShowDialog(self)
            self.UpdateLastDatNum()
            self.CreateGrids()
            self.UpdateIntestaz()
            #awu.MsgDialog(self, message=\
                          #"""Controllare il numero di pagina proposto, """
                          #"""confrontando con l'ultima pagina esistente """
                          #"""della stampa cartacea del registro""",
                          #style=wx.ICON_WARNING)
        event.Skip()
    
    def UpdateIntestaz(self):
        def cn(x):
            return self.FindWindowByName(x)
        r = self.dbreg
        cn('intatt').SetValue(bool(r._intestaz))
        cn('intdes').SetValue(r._intestaz)
        cn('intanno').SetValue(r._intanno)
        cn('intpag').SetValue((r._intpag or 0)+1)
        self.EnableIntestaz()
    
    def EnableIntestaz(self, setfocus=False):
        def cn(x):
            return self.FindWindowByName(x)
        e = cn('intatt').GetValue()
        for name in 'intdes intanno intpag'.split():
            cn(name).Enable(e)
        if e and setfocus:
            cn('intdes').SetFocus()
    
    def OnDateChanged(self, event):
        if self.dbreg is not None:
            self.UpdateLastDatNum()
        event.Skip()

    def OnZoneChanged(self, event):
        b = self.FindWindowById(wdr.ID_BUTSTA)
        t = event.GetSelection()
        e = self.dbreg is not None and not self.dbreg.IsEmpty()
        if t == 0:   #tab. selezioni
            b.Disable()
        elif t == 1: #tab. registrazioni
            b.Enable(e)
            b.SetLabel("&Stampa Registro IVA")
            b.Fit()
        elif t == 2: #tab. riepilogo aliquote
            b.Enable(e)
            b.SetLabel("&Stampa riepilogo")
            b.Fit()
        event.Skip()
    
    def UpdateLastDatNum(self):
        cn = self.FindWindowByName
        if self.dbreg is not None:
            d = cn('datmin').GetValue()
            if d is not None:
                self.dbreg.SetYear(d.year)
            cn('datlast').SetValue(self.dbreg._lastdate)
            cn('numlast').SetValue(self.dbreg._lastprot)
        tiposta = cn('tiposta').GetValue()
        cn('datmin').Enable(tiposta in "PR")
        cn('datmax').Enable()
        cn('nummin').Enable(tiposta == "R")
        cn('nummax').Enable(tiposta == "R")
        cn('radate').Enable(tiposta == "R")
        cn('raprot').Enable(tiposta == "R")
        if tiposta == "D":
            d = cn('datlast').GetValue()
            if d is not None:
                d += 1
            cn('datmin').SetValue(d)
    
    def EnableButtonUpdate(self):
        cn = self.FindWindowByName
        ts, ri, d1, d2, dr = map(lambda x: cn(x).GetValue(), 
                                 'tiposta regiva datmin datmax radate'.split())
        e = ri is not None and d1 is not None and d2 is not None and d2>=d1
        if e and ts == "R":
            e = dr is not None
        cn('butupd').Enable(e)
    
    def OnUpdateGridReg(self, event):
        self.UpdateGridReg()
        event.Skip()

    def UpdateGridReg(self, msg=True):
        cn = lambda x: self.FindWindowById(x)
        cv = lambda x: cn(x).GetValue()
        reg = self.dbreg
        reg.SetTipoStampa(self.tiposta)
        reg.SetLimits(cv(wdr.ID_DATMIN), cv(wdr.ID_DATMAX),\
                      protini=cv(wdr.ID_NUMMIN),\
                      radate= cv(wdr.ID_RADATE),\
                      raprot= cv(wdr.ID_RAPROT))
        if reg.Retrieve():
            self.gridreg.ResetView()
            self.CreateGridTotAliq()
            if reg.RowsCount() == 0 and msg:
                awu.MsgDialog(self, "Nessuna registrazione trovata")
            else:
                cn(wdr.ID_GRIDZONE).SetSelection(1)
                smsg, snum, sdat = reg.CtrSeq()
                if smsg:
                    awu.MsgDialog(self, message=\
                                  """Attenzione!\n\n"""
                                  """Problema sul protocollo n.%d: %s"""\
                                  % (snum, smsg),
                                  style=wx.ICON_WARNING)
        else:
            awu.MsgDialog(self, repr(reg.GetError()))
    
    def OnUpdateGridAliq(self, event):
        self.gridaliq.GetTable().data = self.dbreg.mov.GetRecordset()
        self.gridaliq.ResetView()
        event.Skip()


# ------------------------------------------------------------------------------


class RegIvaFrame(aw.Frame):
    """
    Frame Gestione Registri IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        if not kwargs.has_key('size') and len(args) < 5:
            kwargs['size'] = (970,600)
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(RegIvaPanel(self, -1))


# ------------------------------------------------------------------------------


class RegIvaDialog(aw.Dialog):
    """
    Dialog Gestione Registri IVA.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        if not kwargs.has_key('size') and len(args) < 5:
            kwargs['size'] = (970,600)
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(RegIvaPanel(self, -1))


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    
    class _testApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            Env.Azienda.DB.testdb()
            db = adb.DB()
            db.Connect()
            return True
    
    app = _testApp(True)
    app.MainLoop()
    Env.InitSettings()
    test = RegIvaDialog()
    test.CenterOnScreen()
    test.ShowModal()
