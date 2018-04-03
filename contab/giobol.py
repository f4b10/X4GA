#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/giobol.py
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

import contab.giobol_wdr as wdr

import contab
import contab.dbtables as dbc
import cfg.dbtables as dbp

import awc
import awc.controls.windows as aw
import awc.controls.linktable as lt

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLE = "Giornale generale"


class GiornaleGrid(dbglib.DbGridColoriAlternati):
    
    def __init__(self, parent, dbmov, **kwargs):
        
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size,
                                              idGrid='giornale')
        
        self.dbmov = dbmov
        self.dbmov.ShowDialog(self)
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        mov = self.dbmov
        pdc = mov.pdc
        reg = mov.reg
        cau = reg.config
        riv = reg.regiva
        #riv = cau.regiva
        
        _NUM = gl.GRID_VALUE_NUMBER+":7"
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 60, (cn(mov, "nrigiobol"), "Riga",       _NUM, True)),
            ( 80, (cn(reg, "datreg"),    "Data reg.",  _DAT, True)),
            ( 35, (cn(cau, "codice"),    "Cod.",       _STR, True)),
            (120, (cn(cau, "descriz"),   "Causale",    _STR, True)),
            ( 80, (cn(reg, "datdoc"),    "Data doc.",  _DAT, True)),
            ( 50, (cn(reg, "numdoc"),    "Num.",       _STR, True)),
            ( 35, (cn(riv, "codice"),    "Reg.",       _STR, True)),
            ( 50, (cn(reg, "numiva"),    "Prot.",      _NUM, True)),
            ( 50, (cn(pdc, "codice"),    "Cod.",       _STR, True)),
            (240, (cn(pdc, "descriz"),   "Sottoconto", _STR, True)),
            (110, (cn(mov, "dare"),      "Dare",       _IMP, True)),
            (110, (cn(mov, "avere"),     "Avere",      _IMP, True)),
            ( 40, (cn(reg, "esercizio"), "Es.",        _STR, True)),
            (360, (cn(mov, "note"),      "Note",       _STR, True)),
            (  1, (cn(cau, "id"),        "#cau",       _STR, True)),
            (  1, (cn(pdc, "id"),        "#pdc",       _STR, True)),
            (  1, (cn(mov, "id"),        "#mov",       _STR, True)),
            (  1, (cn(reg, "id"),        "#reg",       _STR, True)),
        )                            
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        
        rs = mov.GetRecordset()
        
        self.SetData( rs, colmap, canedit, canins)
        
        self._fgcold, self._fgcola = contab.GetColorsDA()
        self._colsegno = cn(mov, 'segno')
        self._colcaues = cn(cau, 'esercizio')
        self.SetCellDynAttr(self.GetAttr)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(9)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        rsmov = self.dbmov.GetRecordset()
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
        attr.SetReadOnly()
        return attr


# ------------------------------------------------------------------------------


class GiornalePanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        def ci(x):
            return self.FindWindowById(x)
        def cn(x):
            return self.FindWindowByName(x)
        
        self.dbprg = dbp.Progressivi()
        self.dbmov = dbc.GiornaleGenerale()
        self.dbese = dbp.ProgrEsercizio()
        
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.GiornaleFunc(self)
        
        cn('warningsquad').Hide()
        ci(wdr.ID_TIPOSTA).SetDataLink('tiposta', 'PDR')
        
        self.values = {}
        
        self.gridreg = GiornaleGrid(ci(wdr.ID_PANGRIDMOV), self.dbmov)
        self.pdcid = None
        
        for evt, func, cid in ((wx.EVT_BUTTON,   self.OnUpdate,  wdr.ID_UPDATE),
                               (wx.EVT_BUTTON,   self.OnPrint,   wdr.ID_PRINT),
                               (wx.EVT_RADIOBOX, self.OnTipoSta, wdr.ID_TIPOSTA),
                               (wx.EVT_CHECKBOX, self.OnIntesta, wdr.ID_INTATT),
                               ):
            self.Bind(evt, func, id=cid)
        
        self.SetValues()
        self.TestSel()
        self.TestIntest()
    
    def ReadProgr(self):
        
        p = self.dbprg
        v = self.values
        v.clear()
        
        vx = p.ReadKey('ccg_giobol', '0')
        #if vx is None:
            #raise Exception, "Progressivi contabili mancanti"
        v['lastdat'] = p.progrdate
        v['lastnum'] = p.progrnum
        
        def cn(x):
            return self.FindWindowByName(x)
        
        cn('intatt').SetValue(bool(p.progrdesc))
        cn('intdes').SetValue(p.progrdesc)
        cn('intanno').SetValue(p.progrimp1 or Env.Azienda.Login.dataElab.year)
        cn('intpag').SetValue((p.progrimp2 or 0)+1)
        
        vx = p.ReadKey('ccg_giobol_ec', '0')
        #if vx is None:
            #raise Exception, "Progressivi contabili mancanti per l'esercizio in corso"
        v['progrlastecd'] = p.progrimp1
        v['progrlasteca'] = p.progrimp2
        
        vx = p.ReadKey('ccg_giobol_ep', '0')
        #if vx is None:
            #raise Exception, "Progressivi contabili mancanti per l'esercizio precedente"
        v['progrlastepd'] = p.progrimp1
        v['progrlastepa'] = p.progrimp2
    
    def OnTipoSta(self, event):
        self.SetValues()
        self.TestSel()
        event.Skip()
    
    def SetValues(self):
        self.ReadProgr()
        def cn(x):
            return self.FindWindowByName(x)
        tiposta = cn('tiposta').GetValue()
        names = 'lastdat lastnum progrlastecd progrlasteca progrlastepd progrlastepa'.split()
        if tiposta == "R":
            cn('esercizio').ReadEserciziSiStampaGiornale()
            values = (None, 0, 0, 0, 0, 0)
        else:
            cn('esercizio').ReadEserciziNoStampaGiornale()
            values = map(lambda n: self.values[names[n]], range(6))
        cn('esercizio').Enable(tiposta == 'R')
        for n, name in enumerate(names):
            self.FindWindowByName(name).SetValue(values[n])
        names = 'nextdat nextnum progrnextecd progrnexteca progrnextepd progrnextepa'.split()
        for name in names:
            cn(name).SetValue(None)
        self.dbmov.Reset()
        self.gridreg.ResetView()
    
    def TestSel(self):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        tiposta = cn('tiposta').GetValue()
        
        v = {\
            "P": ("Stampa provvisoria",
                  """La stampa non aggiorna alcun dato sulle """
                  """registrazioni e può essere effettuata quando """
                  """si vuole.""",
                  'data'),
            "D": ("Stampa definitiva",
                  """La stampa definitiva aggiorna le registrazioni """
                  """rendendole non più modificabili.  L'elaborazione può """
                  """essere fatta solo una volta per il periodo selezionato.""",
                  'data'),
            "R": ("Ristampa",
                  """La ristampa considera solo le registrazioni già stampate """
                  """in modo definitivo.  Occorre specificare l'intero periodo """
                  """da ristampare e i progressivi da riprendere.""",
                  'lastdat')
        }
        cn('tipotit').SetLabel(v[tiposta][0])
        cn('tipodes').SetLabel(v[tiposta][1])
        f = cn('data')
        #cn(v[tiposta][2]).SetFocus()
        
        if tiposta == "R":
            l = "Inizio periodo da ristampare"
            e = True
            f = cn('lastdat')
        else:
            l = "Ultima registrazione stampata sul giornale"
            e = False
        cn('label_lastprt').SetLabel(l)
        for name in 'lastdat lastnum progrlastecd progrlasteca progrlastepd progrlastepa'.split():
            cn(name).Enable(e)
        for name in 'nextdat nextnum progrnextecd progrnexteca progrnextepd progrnextepa'.split():
            cn(name).Enable(False)
        f.SetFocus()
    
    def OnIntesta(self, event):
        self.TestIntest(setfocus=True)
        event.Skip()
    
    def TestIntest(self, setfocus=False):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        i = cn('intatt').GetValue()
        for name in 'intdes,intanno,intpag'.split(','):
            cn(name).Enable(i)
        
        if i and setfocus:
            cn('intdes').SetFocus()
    
    def OnPrint(self, event):
        self.Stampa()
        event.Skip()
    
    def Stampa(self):
        def cn(x):
            return self.FindWindowByName(x)
        dec, aec, dep, aep = map(lambda x: cn(x).GetValue() or 0, 
                  'progrlastecd progrlasteca progrlastepd progrlastepa'.split())
        i = self.dbmov._info
        i.ripdare_ec, i.ripavere_ec = dec, aec
        i.ripdare_ep, i.ripavere_ep = dep, aep
#        i.anno_ec = self.dbese.GetEsercizioInCorso()
        i.anno_ec = cn('esercizio').GetValue()
        i.anno_ep = i.anno_ec-1
        dec, aec, dep, aep = map(lambda x: cn(x).GetValue() or 0, 
                  'progrnextecd progrnexteca progrnextepd progrnextepa'.split())
        i.esepre = (dep != 0 or aep != 0)
        for c in 'tiposta intatt intdes intanno intpag'.split():
            setattr(i, c, cn(c).GetValue())
        s = rpt.Report(self, self.dbmov, 'Giornale Generale')
        if cn('tiposta').GetValue() == 'D':
            aw.awu.MsgDialog(self, "Stampa giornale terminata.")
            if aw.awu.MsgDialog(self,\
                                """Confermando questa scelta, la stampa ottenuta diverrà definitiva, ovvero:\n"""
                                """- le registrazioni coinvolte verrnno numerate definitivamente come sulla stampa;\n"""
                                """- saranno nuovamente stampabili sul giornale, se necessario, solo mediante funzione di ristampa;\n"""
                                """- i progressivi dare/avere verranno memorizzati in modo da essere ripresi alla stampa successiva.\n\n"""
                                """Confermi l'elaborazione definitiva dei movimenti?""",
                                style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                self.RendiStampaDefinitiva()
                prg = self.dbprg
                prg.ReadKey('ccg_giobol', '0')
                if prg.OneRow():
                    p = s.usedReport.oCanvas.userVariableList['intpag']
                    prg.progrimp1 = cn('intanno').GetValue()
                    prg.progrimp2 = p.valore
                    prg.Save()
                self.Close()
            self.SetValues()
    
    def RendiStampaDefinitiva(self):
        def cn(x):
            return self.FindWindowByName(x)
        wx.BeginBusyCursor()
        try:
            if self.dbmov.Save():
                dat, num, dec, aec, dep, aep = map(lambda x: cn(x).GetValue(), 
                          'nextdat nextnum progrnextecd progrnexteca progrnextepd progrnextepa'.split())
                p = self.dbprg
                p.SaveKey('ccg_giobol', '0',
                          fields='progrdate,progrnum',
                          values=(dat,num))
                e = self.dbese.GetEsercizioInCorso()
                p.SaveKey('ccg_giobol_ec', '0', 
                          fields='progrimp1,progrimp2',
                          values=(dec,aec))
                p.SaveKey('ccg_giobol_ep', '0', 
                          fields='progrimp1,progrimp2',
                          values=(dep,aep))
            else:
                aw.awu.MsgDialog(self, repr(self.dbmov.GetError()))
        finally:
            wx.EndBusyCursor()
    
    def OnUpdate(self, event):
        self.UpdateData()
        event.Skip()
    
    def UpdateData(self):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        mov = self.dbmov
        mov.ClearFilters()
        
        tipelab = cn('tiposta').GetValue()
        mov.SetModoStampa(tipelab)
        
#        e = self.dbese.GetEsercizioInCorso()
        e = cn('esercizio').GetValue()
        dmin, dmax = self.dbese.GetEsercizioDates(e)
        
        err = None
        if e is None:
            err = 'Esercizio nullo'
        if err is None:
            if tipelab in 'PD':
                r = dbc.adb.DbTable(bt.TABNAME_CONTAB_H, 'reg')
                r.AddFilter("(reg.st_giobol IS NULL or reg.st_giobol<>1) AND reg.tipreg<>'E'")
                if self.dbese.GetSovrapposizione():
                    r.AddFilter('reg.esercizio<%s AND reg.datreg<%s', e, dmin)
                else:
                    r.AddFilter('reg.esercizio<%s', e)
                r.AddLimit(1)
                r.Retrieve()
                if not r.IsEmpty():
                    err = 'Sono presenti registrazioni di esercizi precedenti ancora da stampare'
                del r
        if err is None:
            d1, d2 = map(lambda x: cn(x).GetValue(), 'lastdat data'.split())
            if d1 is None:
                if tipelab in 'PD':
                    err = 'Manca la data iniziale, controllare i progressivi contabili'
            if err is None and d2 is None:
                err = 'Manca la data limite di stampa'
            if err is None and tipelab == 'R' and d1 is not None and d1<dmin:
                err = 'La data di inizio stampa è precedente l\'inizio dell\'esercizio indicato'
            if err is None and tipelab != 'R' and d1 is not None and d2<d1:
                err = 'La data limite di stampa è antecedente l\'ultima data stampata'
            if err is None and d2>dmax:
                err = 'La data limite di stampa è successiva la fine dell\'esercizio indicato'
        if err:
            aw.awu.MsgDialog(self, message=err, style=wx.ICON_ERROR)
            return
        
        if tipelab in 'PD':
            #stampa provv. o defin., prendo solo registrazioni non stampate
            mov.AddFilter('reg.st_giobol IS NULL OR reg.st_giobol=0')
        else:
            #ristampa, prendo solo registrazioni già stampate
            mov.AddFilter('reg.st_giobol=1')
        datstart = cn('lastdat').GetValue()
        if tipelab == 'R':
            numstart = cn('lastnum').GetValue()
            if numstart:
                mov.AddFilter('body.nrigiobol>=%s', numstart)
        if datstart is not None:
            mov.AddFilter('reg.datreg>=%s', datstart)
        mov.AddFilter('reg.datreg<=%s', cn('data').GetValue())
        mov.AddFilter("reg.tipreg<>'E'")
        
        if not mov.Retrieve():
            awc.util.MsgDialog(self, message=repr(mov.GetError()))
        
        self.gridreg.ChangeData(mov.GetRecordset())
        self.UpdateTotals()

    def UpdateTotals(self):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        mov = self.dbmov
        
        rinum = cn('tiposta').GetValue() != 'R'
        nr = cn('lastnum').GetValue()+1
        
        ec = cn('esercizio').GetValue()
        ep = ec-1
        wx.BeginBusyCursor()
        try:
            tecd, teca, tepd, tepa = mov.NumeraRighe(nr, ec, ep, rinum)#, func=lambda n: w.SetValue(n))
        finally:
            wx.EndBusyCursor()
        self.gridreg.ResetView()
        cn('progrnextecd').SetValue(cn('progrlastecd').GetValue()+tecd)
        cn('progrnexteca').SetValue(cn('progrlasteca').GetValue()+teca)
        cn('progrnextepd').SetValue(cn('progrlastepd').GetValue()+tepd)
        cn('progrnextepa').SetValue(cn('progrlastepa').GetValue()+tepa)
        mov.MoveLast()
        cn('nextdat').SetValue(mov.reg.datreg)
        cn('nextnum').SetValue(mov.nrigiobol)
        sf = dbc.adb.DbTable.samefloat
        cn('warningsquad').Show(not sf(tecd, teca) or not sf(tepd, tepa))


# ------------------------------------------------------------------------------


class GiornaleFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GiornalePanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class GiornaleDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GiornalePanel(self, -1))
        self.CenterOnScreen()
