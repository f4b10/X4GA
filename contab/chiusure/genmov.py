#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/chiusure/genmov.py
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

import contab.chiusure.chiusure_wdr as wdr

import contab
import contab.dbtables as dbc
import cfg.dbtables as dbx

import awc
import awc.controls.windows as aw
import awc.controls.linktable as lt

import Env
bt = Env.Azienda.BaseTab

import report as rpt


FRAME_TITLE = "Generazione movimenti di Apertura/Chiusura"


class GeneraMovimentiGrid(dbglib.DbGridColoriAlternati):
    
    esercizio = None
    
    def __init__(self, parent, dbsal, **kwargs):
        
        size = parent.GetClientSizeTuple()
        
        dbglib.DbGridColoriAlternati.__init__(self, parent, -1, size=size)
        
        self.dbsal = dbsal
        self.dbsal.ShowDialog(self)
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        sal = self.dbsal
        pdc = sal.pdc
        mas = pdc.bilmas
        con = pdc.bilcon
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        cols = (\
            ( 50, (cn(mas, "codice"),      "Mastro",      _STR, True)),
            ( 50, (cn(con, "codice"),      "Conto",       _STR, True)),
            ( 60, (cn(pdc, "codice"),      "Cod.",        _STR, True)),
            (240, (cn(pdc, "descriz"),     "Sottoconto",  _STR, True)),
            (110, (cn(sal, "total_dare"),  "Saldo Dare",  _IMP, True)),
            (110, (cn(sal, "total_avere"), "Saldo Avere", _IMP, True)),
            (  1, (cn(pdc, "id"),          "#pdc",        _STR, True)),
        )                            
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = False
        canins = False
        
        rs = pdc.GetRecordset()
        
        self.SetData(rs, colmap, canedit, canins)
        
        self.AddTotalsRow(3, 'Totali:', (cn(sal, 'total_dare'),
                                         cn(sal, 'total_avere')))
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(3)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)
        
        self.Bind(gl.EVT_GRID_CELL_LEFT_DCLICK, self.OnCallMastro)
    
    def OnCallMastro(self, event):
        self.CallMastro()
        event.Skip()
    
    def CallMastro(self):
        s = self.dbsal
        rs = s.GetRecordset()
        row = self.GetSelectedRows()[0]
        if not 0 <= row < len(rs):
            return
        s.MoveRow(row)
        tipid = s.pdc.id_tipo
        pdcid = s.pdc.id
        if pdcid is None:
            return
        wx.BeginBusyCursor()
        fc = contab.GetInterrPdcDialogClass(tipid)
        if fc is None:
            return
        f = fc(self, onecodeonly=pdcid)
        f.OneCardOnly(pdcid)
        wx.EndBusyCursor()
        f.DisplayTab('mastro')
        def cn(w, x):
            return w.FindWindowByName(x)
        #for cnbil, cnmas in (('datreg1', 'masdatini'),
                             #('datreg2', 'masdatmov')):
            #d = cn(win, cnbil).GetValue()
            #if d: cn(f, cnmas).SetValue(d)
        cn(f, 'masesercizio').SetValue(self.esercizio)
        f.panel.TestForUpdates()#mastroaddfilter=self.mastrofilter)
        f.CenterOnScreen()
        f.ShowModal()
        f.Destroy()
    
    def SetEsercizio(self, e):
        self.esercizio = e


# ------------------------------------------------------------------------------


class GeneraMovimentiPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        self.dbaut = dbx.Automat()
        self.dbese = dbx.ProgrEsercizio()
        self.dbslp = dbc.Bilancio()
        self.dbsle = dbc.Bilancio()
        self.dbreg = dbc.DbRegCon()
        
        self.esercizio = self.dbese.GetEsercizioInCorso()
        if self.dbese.GetSovrapposizione():
            self.esercizio -= 1
        
        self.risultato = None     #descrizione risultato per stampa
        self.risultato_tot = None #importo risultato, x registrazione finale
        self.risultato_tip = None #tipo U/P utile/perdita, x registrazione finale
        
        for s in self.dbslp, self.dbsle:
            s.AddHaving("total_dare<>total_avere")
            s.SetOrdinamento(dbc.BILORD_BIL)
            s.Reset()
        
        wx.Panel.__init__(self, *args, **kwargs)
        wdr.GeneraMovimentiFunc(self)
        
        def cn(x):
            return self.FindWindowByName(x)
        
        for name in 'chi ape'.split():
            cn('pancal%s'%name).Hide()
        
        self.gridslp = GeneraMovimentiGrid(cn('pangridsalpat'), self.dbslp)
        self.gridsle = GeneraMovimentiGrid(cn('pangridsaleco'), self.dbsle)
        
        e = cn('esercizio')
        e.SetLabel(str(self.esercizio))
        
        a = self.dbaut
        for prefix in 'regchi regape'.split():
            for key in 'cau bil upe prp'.split():
                name = prefix+key
                c = cn(name)
                if c:
                    c.SetValue(a.GetAutomat(name))
        
        for name, func in (('update', self.OnUpdateData),
                           ('printpat', self.OnPrintPat),
                           ('printeco', self.OnPrintEco),
                           ('genera', self.OnGeneraMovimenti)):
            self.Bind(wx.EVT_BUTTON, func, cn(name))
    
    def OnUpdateData(self, event):
        self.UpdateData()
    
    def OnPrintPat(self, event):
        self.PrintReport(self.dbslp)
    
    def OnPrintEco(self, event):
        self.PrintReport(self.dbsle)
    
    def OnGeneraMovimenti(self, event):
        if self.GeneraMovimenti():
            event.Skip()
    
    def UpdateData(self):
        def cn(x):
            return self.FindWindowByName(x)
        p = self.workzone.GetPage(0).FindWindowByName('pancalc')
        p.Disable()
        e = self.esercizio
        if not e:
            aw.awu.MsgDialog(self, "Impostare l'esercizio per la determinazione dei saldi")
            return
        if self.dbese.GetMovimentiGenerati():
            aw.awu.MsgDialog(self, "Movimenti di chiusura/apertura già generati")
            return
        sg = None
        err = False
        s = self.dbslp
        #test #1: esistenza esercizi precedenti
        ef = "reg.esercizio<%s" % e
        gf = "(reg.st_giobol IS NULL or reg.st_giobol<>1) AND reg.tipreg<>'E'"
        s.AddFilter(ef)
        s.AddFilter(gf)
        s.Retrieve()
        if not s.IsEmpty():
            msg = 'Sono presenti esercizi precedenti non stampati sul giornale'
            err = True
        if not err:
            ef = "reg.esercizio=%s" % e
            #test #1: esistenza registrazioni non stampate sul giornale
            s.ClearFilters()
            s.AddFilter(ef)
            s.AddFilter(gf)
            s.Retrieve()
            if not s.IsEmpty():
                msg = 'Sono presenti registrazioni non stampate sul giornale'
                err = True
        tots = {'P': [0,0],
                'E': [0,0]}
        for s, t, g in ((self.dbslp, 'P', self.gridslp),
                        (self.dbsle, 'E', self.gridsle)):
            s.ClearFilters()
            s.AddFilter("bilmas.tipo=%s", t)
            s.AddFilter(ef)
            if not s.Retrieve():
                aw.awu.MsgDialog(self, repr(s.GetError()))
                return
            w = aw.awu.WaitDialog(self, maximum=s.RowsCount())
            try:
                for n, mov in enumerate(s):
                    if (mov.total_dare or 0) > (mov.total_avere or 0):
                        mov.total_dare = mov.total_dare-mov.total_avere
                        mov.total_avere = None
                    else:
                        mov.total_avere = mov.total_avere-mov.total_dare
                        mov.total_dare = None
                    w.SetValue(n)
            finally:
                w.Destroy()
            g.ChangeData(s.GetRecordset())
            g.SetEsercizio(e)
            tx = g.GetTotalsRows()[0][3]
            tots[t][0] = tx[0]
            tots[t][1] = tx[1]
        tpa = tpp = tec = ter = 0
        ris = ''
        sq = False
        if not err:
            if self.dbslp.IsEmpty() and self.dbsle.IsEmpty():
                msg = "Non è stato trovato alcun sottoconto da chiudere"
                err = True
        if not err:
            tpa, tpp = tots['P']
            tec, ter = tots['E']
            sf = dbc.adb.DbTable.samefloat
            fn = dbc.adb.DbTable.sepnvi
            ris = ''
            if tpa >= tpp:
                up = tpa-tpp
                pp = None
                ue = ter-tec
                pe = None
                if sf(up, ue):
                    msg = 'Utile rilevato: %s' % fn(up)
                    ris = 'UTILE'
                    self.risultato_tot = up
                    self.risultato_tip = "U"
                else:
                    sq = True
            else:
                pp = tpp-tpa
                up = None
                pe = tec-ter
                ue = None
                if sf(pp, pe):
                    msg = 'Perdita rilevata: %s' % fn(pp)
                    ris = 'PERDITA'
                    self.risultato_tot = pp
                    self.risultato_tip = "P"
                else:
                    sq = True
            cn('salchiupe').SetValue(pp or up)
            cn('salapeupe').SetValue(pp or up)
            if sq:
                msg = 'Squadratura Patrimoniale-Economico'
                err = True
        cn('salchibil').Show(sq)
        cn('salchiprp').Show(sq)
        cn('salchiupe').Show(not sq)
        cn('pancalchi').Show(True)
        cn('salapebil').Show(sq)
        cn('salapeupe').Show(not sq)
        cn('pancalape').Show(True)
        self.risultato = msg # per stampa
        c = cn('warning')
        if err:
            c.SetForegroundColour('red')
            cn('esercizio').SetFocus()
        else:
            c.SetForegroundColour('blue')
            p.Enable()
            cn('regchidat').SetFocus()
        c.SetLabel(msg)
        cn('salchibil').SetValue(abs(tpa-tpp))
        cn('salchiprp').SetValue(abs(ter-tec))
        cn('salapebil').SetValue(abs(tpa-tpp))
        for name in 'chi ape'.split():
            cn('%sris' % name).SetLabel(ris)
        self._Layout()
    
    def PrintReport(self, dbsal):
        def GetSezione(tipo):
            out = ''
            if tipo in "PEO":
                out = ['STATO PATRIMONIALE', 
                       'CONTO ECONOMICO', 
                       'CONTI D\'ORDINE']["PEO".index(tipo)]
            return out
        dbsal.GetSezione = GetSezione
        def GetRisultato():
            return self.risultato
        dbsal.GetRisultato = GetRisultato
        def GetEsercizio():
            return self.esercizio
        dbsal.GetEsercizio = GetEsercizio
        rpt.Report(self, dbsal, "Saldi sottoconti per chiusura bilancio")
    
    def GeneraMovimenti(self):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        err = None
        d1, d2 = map(lambda x: cn(x).GetValue(), 'regchidat regapedat'.split())
        if not d1:
            err = "Definire la data di chiusura"
        elif not d2:
            err = "Definire la data di apertura"
        if not err and d2 <= d1:
            err = "La data di apertura deve essere successiva alla data di chiusura"
        if not err:
            e = self.esercizio
            if self.dbese.GetSovrapposizione():
                dmin, dmax = self.dbese.GetEsercizioDates(e+1)
                if not dmin <= d1 <= dmax:
                    err = "La data di chiusura deve appartenere all'esercizio in corso"
                elif not dmin <= d1 <= dmax:
                    err = "La data di apertura deve appartenere all'esercizio in corso"
            else:
                dmin, dmax = self.dbese.GetEsercizioDates(e)
                if not dmin <= d1 <= dmax:
                    err = "La data di chiusura deve appartenere all'esercizio di chiusura"
        
        if err:
            aw.awu.MsgDialog(self, message=err, style=wx.ICON_ERROR)
            return
        
        r = aw.awu.MsgDialog(self,\
                             """ATTENZIONE\n\nL'elaborazione è irreversibile, è """
                             """consigliabile effettuare una copia di backup del database """
                             """prima di procedere.\n\n"""
                             """Confermi l'elaborazione?""",
                             style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT)
        if r != wx.ID_YES:
            return
        
        w = aw.awu.WaitDialog(self, message="Generazione registrazioni in corso...",
                              maximum=self.dbslp.RowsCount()+self.dbsle.RowsCount())
        
        err = None
        try:
            n = 0
            def gv(x):
                return cn('reg'+x).GetValue()
            e = self.esercizio
            for s, t, cc, pc, ca, pa in\
                ((self.dbslp, 'P', 'chicau', 'chibil', 'apecau', 'apebil'),
                 (self.dbsle, 'E', 'chicau', 'chiprp', None,     None    )):
                for x in s:
                    #creazione chiusura
                    err = not self._GenReg(e, x, gv(cc), gv(pc), gv('chidat'), 'A', 'D')
                    if not err and ca:
                        #creazione apertura
                        err = not self._GenReg(e+1, x, gv(ca), gv(pa), gv('apedat'), 'D', 'A')
                    w.SetValue(n)
                    n += 1
                    if err:
                        break
                if err:
                    break
            if err:
                aw.awu.MsgDialog(self, err, style=wx.ICON_ERROR)
        finally:
            w.Destroy()
        
        if not err:
            #scritture finali
            pdc1 = gv('chiprp')
            pdc2 = gv('chiupe')
            impr = self.risultato_tot
            if self.risultato_tip == "U":
                s1 = "D"
                s2 = "A"
            else:
                s1 = "A"
                s2 = "D"
            #CHIUSURA: profitti/perdite -> risultato di esercizio
            err = not self._GenRegFinale(e, pdc1, gv('chicau'), pdc2, gv('chidat'), impr, s1, s2)
            if not err:
                pdc1 = gv('chiupe')
                pdc2 = gv('chibil')
                #CHIUSURA: risultato di esercizio -> bilancio di chiusura
                err = not self._GenRegFinale(e, pdc1, gv('chicau'), pdc2, gv('chidat'), impr, s1, s2)
                if not err:
                    #APERTURA: bilancio di apertura -> risultato di esercizio
                    pdc1 = gv('apebil')
                    pdc2 = gv('chiupe')
                    err = not self._GenRegFinale(e+1, pdc1, gv('apecau'), pdc2, gv('apedat'), impr, s1, s2)
        
        if err:
            msg = repr(self.dbreg.GetError())
            icon = wx.ICON_ERROR
        else:
            dbpro = dbc.adb.DbTable(bt.TABNAME_CFGPROGR, 'progr')
            for key, des, col, val in (('chiusura',  'Movimenti chiusura esercizio', 'progrdate', gv('chidat')),
                                       ('apertura',  'Movimenti apertura esercizio', 'progrdate', gv('apedat')),
                                       ('esercizio', 'Flags esercizio',              'progrimp2', 1),
                                       ):
                dbpro.Retrieve('progr.codice="ccg_%s"' % key)
                if dbpro.IsEmpty():
                    dbpro.CreateNewRow()
                    dbpro.codice = 'progr.codice="ccg_%s"' % key
                    dbpro.descriz = des
                setattr(dbpro, col, val)
                dbpro.Save()
            msg = "Generazione movimenti terminata"
            icon = wx.ICON_INFORMATION
        aw.awu.MsgDialog(self, msg, style=icon)
        
        return True
    
    def _GenReg(self, e, sal, cau, pdc, dat, s1, s2):
        
        reg = self.dbreg
        reg.Reset()
        
        #testata registrazione
        reg.CreateNewRow()
        reg.esercizio = e
        reg.id_caus = cau
        reg.tipreg = reg.config.tipo
        reg.datreg = dat
        b = reg.body
        
        #riga 1 - sottoconto elaborato
        b.CreateNewRow()
        b.numriga = 1
        b.tipriga = reg.tipreg
        if sal.total_dare:
            b.importo = sal.total_dare
            b.segno = s1
        else:
            b.importo = sal.total_avere
            b.segno = s2
        b.id_pdcpa = sal.pdc.id
        b.id_pdccp = pdc
        
        #riga 2 - sottoconto bilancio
        b.CreateNewRow()
        b.numriga = 2
        b.tipriga = reg.tipreg
        if sal.total_dare:
            b.importo = sal.total_dare
            b.segno = s2
        else:
            b.importo = sal.total_avere
            b.segno = s1
        b.id_pdcpa = pdc
        b.id_pdccp = sal.pdc.id
        return reg.Save()
    
    def _GenRegFinale(self, e, pdc1, cau, pdc2, dat, imp, s1, s2):
        
        assert s1 in ("D", "A"), "Segno non riconosciuto"
        assert s2 in ("D", "A"), "Segno non riconosciuto"
        
        reg = self.dbreg
        reg.Reset()
        
        #testata registrazione
        reg.CreateNewRow()
        reg.esercizio = e
        reg.id_caus = cau
        reg.tipreg = reg.config.tipo
        reg.datreg = dat
        b = reg.body
        
        #riga 1 - sottoconto elaborato
        b.CreateNewRow()
        b.numriga = 1
        b.tipriga = reg.tipreg
        b.importo = imp
        b.segno = s1
        b.id_pdcpa = pdc1
        b.id_pdccp = pdc2
        
        #riga 2 - sottoconto bilancio
        b.CreateNewRow()
        b.numriga = 2
        b.tipriga = reg.tipreg
        b.importo = imp
        b.segno = s2
        b.id_pdcpa = pdc2
        b.id_pdccp = pdc1
        
        return reg.Save()


# ------------------------------------------------------------------------------


class GeneraMovimentiFrame(aw.Frame):
    
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(GeneraMovimentiPanel(self, -1))
        self.CenterOnScreen()
        self.Bind(wx.EVT_BUTTON, self.OnGeneraMovimenti, self.FindWindowByName('genera'))
    
    def OnGeneraMovimenti(self, event):
        import lib
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        self.Close()
