#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/bil.py
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

import contab.dbtables as dbc
import contab.bil_wdr as wdr

import locale

from lib import SameFloat

from anag.pdc import PdcDialog
import contab
from contab.pdcint import PdcInterrDialog

import report as rpt

from cfg.cfgcontab import CfgContab

bt = dbc.Env.Azienda.BaseTab
bc = dbc.Env.Azienda.Colours
DateTime = dbc.adb.DateTime
today = dbc.Env.Azienda.Esercizio.dataElab

MsgWait = aw.awu.WaitDialog


FRAME_TITLE_BILVER = "Bilancio di verifica"
FRAME_TITLE_BILGES = "Bilancio gestionale"
FRAME_TITLE_BILCON = "Bilancio contrapposto"
FRAME_TITLE_BILCEE = "Bilancio Riclassificato CEE"


GRIDCOL_TIPBIL =  0 #tipo bilancio (0=Patr, 1=Econ, 2=Ord)
GRIDCOL_CODMAS =  1 #cod. mastro
GRIDCOL_CODCON =  2 #cod. conto
GRIDCOL_IDTIP =   3 #id tipo anagrafico
GRIDCOL_CODTIP =  4 #cod. tipo anagrafico
GRIDCOL_IDPDC =   5 #id sottoconto
GRIDCOL_CODPDC =  6 #cod. sottoconto
GRIDCOL_DESC =    7 #descrizione
GRIDCOL_PROGRD =  8 #progr. dare
GRIDCOL_PROGRA =  9 #progr. avere
GRIDCOL_SALDOD = 10 #saldo se dare
GRIDCOL_SALDOA = 11 #saldo se avere
GRIDCOL_CEECOD = 12 #classificazione cee: codice
GRIDCOL_CEESEZ = 13 #classificazione cee: sezione
GRIDCOL_CEEVOC = 14 #classificazione cee: voce
GRIDCOL_CEECAP = 15 #classificazione cee: capitolo
GRIDCOL_CEEDET = 16 #classificazione cee: dettaglio
GRIDCOL_CEESUB = 17 #classificazione cee: sub-dettaglio
GRIDCOL_CEEVAL = 18 #valore (Dare - Avere)
GRIDCOL_SALGAD = 12 #saldo G.Apertura se dare
GRIDCOL_SALGAA = 13 #saldo G.Apertura se avere


class DbMemBil(dbc.adb.DbMem):
    
    def __init__(self, win, fields):
        dbc.adb.DbMem.__init__(self, fields)
        self._info.win = win
    
    def GetQuadratura(self):
        return self._info.win.FindWindowByName('warning').GetLabel()
    
    def GetPeriodo(self):
        try:
            return self._info.win.GetPeriodo()
        except:
            return ''


# ------------------------------------------------------------------------------


class _BilGrid(dbglib.DbGridColoriAlternati):
    
    coloratip = True
    
    def __init__(self, dbbil, pp, tableClass=None):
        
        dbglib.DbGridColoriAlternati.__init__(self, pp, -1, 
                                              size=pp.GetClientSizeTuple(), 
                                              style=0, tableClass=tableClass,
                                              idGrid='bilancioverifica')
        
        self.SetDefaultRowSize(20)
        
        self.dbbil =   dbbil
        self.rsbil =   []
        self.colors =  False
        self.intesta = True
        self.totali =  {}
        self.totd =    None
        self.tota =    None
        
        cols, anchorcol, resizecol, fitcol = self.GetGridColumns()
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        
        canedit = True
        canins = False
        links = None
        afteredit = None
        
        self.SetData(self.rsbil, colmap, canedit, canins, links, afteredit)
        self.GetTable().rsbil = self.rsbil
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetAnchorColumns(anchorcol, resizecol)
        self.SetFitColumn(fitcol)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        pp.SetSizer(sz)
        sz.SetSizeHints(pp)
        
        self.Bind(gl.EVT_GRID_CELL_RIGHT_CLICK, self.OnCellRightClick)
    
    def OnPdcScheda(self, event):
        self.ApriPdcScheda(False)
        event.Skip()
    
    def OnPdcMastro(self, event):
        self.ApriPdcScheda(True)
        event.Skip()
    
    def ApriPdcScheda(self, mas):
        rs = self.rsbil
        row = self.GetSelectedRows()[0]
        if not 0 <= row < len(rs):
            return
        tipid = rs[row][GRIDCOL_IDTIP]
        pdcid = rs[row][GRIDCOL_IDPDC]
        pdccod = rs[row][GRIDCOL_CODPDC]
        pdcdes = rs[row][GRIDCOL_DESC]
        if pdcid is None:
            return
        wx.BeginBusyCursor()
        fc = contab.GetInterrPdcDialogClass(tipid)
        if fc is None:
            return
        f = fc(self, onecodeonly=pdcid)
        f.OneCardOnly(pdcid)
        wx.EndBusyCursor()
        win = self
        while not isinstance(win, (wx.Frame, wx.Dialog)):
            win = win.GetParent()
        if mas:
            f.DisplayTab('mastro')
            cn = lambda w, x: w.FindWindowByName(x)
            for cnbil, cnmas in (('datreg1', 'masdatini'),
                                 ('datreg2', 'masdatmov')):
                d = cn(win, cnbil).GetValue()
                if d: cn(f, cnmas).SetValue(d)
            e = cn(win, 'eserc').GetValue()
            if e is not None:
                cn(f, 'masesercizio').SetValue(e)
            f.panel.TestForUpdates()
        f.CenterOnScreen()
        f.ShowModal()
        f.Destroy()
    
    def MenuPopup(self, event):
        row, col = event.GetRow(), event.GetCol()
        rsb = self.rsbil
        if not rsb[row][GRIDCOL_CODPDC]:
            return
        self.SetGridCursor(row, col)
        self.SelectRow(row)
        menu = wx.Menu()
        schedaId = wx.NewId()
        menu.Append(schedaId, "Apri la scheda anagrafica del sottoconto")
        self.Bind(wx.EVT_MENU, self.OnPdcScheda, id=schedaId)
        mastroId = wx.NewId()
        menu.Append(mastroId, "Visualizza il mastro del sottoconto")
        self.Bind(wx.EVT_MENU, self.OnPdcMastro, id=mastroId)
        xo, yo = event.GetPosition()
        self.PopupMenu(menu, (xo, yo))
        menu.Destroy()
        event.Skip()
    
    def OnCellRightClick(self, event):
        row = event.GetRow()
        if 0 <= row < len(self.rsbil):
            self.MenuPopup(event)
    
    def GetAttr(self, row, col, rscol, attr=gl.GridCellAttr):
        attr = dbglib.DbGridColoriAlternati.GetAttr(self, row, col, rscol, attr)
        if not 0 <= row < len(self.rsbil):
            return attr
        rsb = self.rsbil[row]
        if not self.colors:
            color = bc.GetColour("linen")
        elif rscol in (GRIDCOL_PROGRD, GRIDCOL_PROGRA):
            color = bc.GetColour("gainsboro")
        elif rscol in (GRIDCOL_SALGAD, GRIDCOL_SALGAA):
            color = bc.GetColour("lightyellow")
        elif rsb[GRIDCOL_TIPBIL] == 0:
            color = bc.GetColour("lightblue")
        elif rsb[GRIDCOL_TIPBIL] == 1:
            color = bc.GetColour("darkseagreen2")
        elif rsb[GRIDCOL_TIPBIL] == 2:
            color = bc.GetColour("wheat1")
        else:
            color = bc.GetColour("thistle3")
        attr.SetBackgroundColour(color)
        try:
            f = attr.GetFont()
        except:
            f = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD)
            attr.SetFont(f)
        f = attr.GetFont()
        w = wx.FONTWEIGHT_BOLD
        if rsb[GRIDCOL_CODPDC]:
            w = wx.FONTWEIGHT_NORMAL
        elif rsb[GRIDCOL_CODMAS]:
            w = wx.FONTWEIGHT_MAX
        try:
            f.SetWeight(w)
            attr.SetFont(f)
        except:
            pass
        attr.SetReadOnly(True)
        return attr
    
    def GetGridColumns(self):
        raise Exception,\
              """Questa classe non è istanziabile"""
    
#    def AppendRow(self, *args, **kwargs):
#        raise Exception,\
#              """Questa classe non è istanziabile"""
#    
    def UpdateGrid(self, pbar, **parms):
        for name, val in (('tipdet',    'S'),\
                          ('detcf',     True),\
                          ('globaltot', False),\
                          ('pbper',     0),\
                          ('pbmax',     1)):
            if not parms.has_key(name):
                parms[name] = val
        
        b = self.dbbil
        ci = lambda tab, col: tab._GetFieldIndex(col, inline=True)
        nctip = ci(b, 'tipobil')
        ncmas = ci(b, 'mastro')
        nccon = ci(b, 'conto')
        ncpid = ci(b.pdc, 'id')
        ncpdc = ci(b.pdc, 'codice')
        nctpi = ci(b.pdc.tipana, 'id')
        nctpa = ci(b.pdc.tipana, 'codice')
        nctpt = ci(b.pdc.tipana, 'tipo')
        ncttd = ci(b, 'total_dare')
        nctta = ci(b, 'total_avere')
        ncdma = ci(b.pdc.bilmas, 'descriz')
        ncdco = ci(b.pdc.bilcon, 'descriz')
        ncdsc = ci(b.pdc, 'descriz')
        nctgd = ci(b,            'total_darega')
        nctga = ci(b,            'total_averega')

        
        b.SetVar('pbar', pbar)
        
#        def AddTot(totdict, key, dare, avere):
        def AddTot(totdict, key, dare, avere, darega, averega):
            if not totdict.has_key(key):
#                totdict[key] = [0, 0]
                totdict[key] = [0, 0, 0, 0]
            totdict[key][0] += dare or 0
            totdict[key][1] += avere or 0
            totdict[key][2] += darega or 0
            totdict[key][3] += averega or 0
        
        totpatd = 0; totpata = 0
        totecod = 0; totecoa = 0
        totordd = 0; totorda = 0
        
        rs = b.GetRecordset()
        self.totali = {}
        tt = self.totali
        
        for row in range(b.RowsCount()):
            rowd = rs[row][ncttd]
            rowa = rs[row][nctta]
            rgad = rs[row][nctgd]
            rgaa = rs[row][nctga]

            if self.Filter(rs[row][nctip], rs[row][ncttd]>=rs[row][nctta]):
                for tipo, col in (('t', nctip),\
                                  ('m', ncmas),\
                                  ('c', nccon)):
                    AddTot(tt, "%s%s" % (tipo, rs[row][col]), rowd, rowa, rgad, rgaa)
#                    AddTot(tt, "%s%s" % (tipo, rs[row][col]), rowd, rowa)
       
        dototmas = parms['tipdet'] in "MCS"
        dototcon = parms['tipdet'] in "CS"
        dototpdc = parms['tipdet'] in "S"
        
        self.rsbil = []
        rs =    self.rsbil
        ltip =  None
        lmas =  None
        lcon =  None
        trec =  b.RowsCount()
        tord =  b.GetVar('ordin')
        
        pbcur = trec*parms['pbper']
        trec *= parms['pbmax']
        
        self.totd = 0
        self.tota = 0
        
        self.tgad = 0
        self.tgaa = 0
        
        self.pbar = pbar
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(1000)
        self.pbcur = pbcur
        
        try:
            
            for row in range(b.RowsCount()):
                
                self.pbcur += 1
                try:
                    wx.YieldIfNeeded()
                except:
                    pass
                
                r = b.GetRecordset()[row]
                
                tip = r[nctip]
                
                if not self.Filter(tip, r[ncttd]>=r[nctta]):
                    continue
                
                mas = r[ncmas]
                con = r[nccon]
                des = r[ncdsc]
                pid = r[ncpid]
                pdc = r[ncpdc]
                tpi = r[nctpi]
                tpa = r[nctpa]
                
                rowd = r[ncttd] or 0
                rowa = r[nctta] or 0
                
                self.totd += rowd
                self.tota += rowa

                rgad = r[nctgd] or 0
                rgaa = r[nctga] or 0

                self.tgad += rgad
                self.tgaa += rgaa
                
                def TestZero(d,a):
                    return (not parms['detnozero'] or not SameFloat(d,a))
                
                if tord == dbc.BILORD_BIL:
                    
                    if tip != ltip:
                        if self.intesta:
                            try:
                                dsb = ('Stato Patrimoniale',\
                                       'Conto Economico',\
                                       'Conti d\'Ordine')[tip]
                                prd, pra, gad, gaa = tt['t%s' % tip]
#                                prd, pra = tt['t%s' % tip]
                            except IndexError:
                                dsb = 'Tipo di bilancio sconosciuto'
                                prd, pra, gad, gaa = 0, 0, 0, 0
#                                prd, pra = 0, 0
                            if len(rs)>0:
                                for x in range(2):
                                    self.AppendRow(tip=-1)
                            self.AppendRow(tip, mas=dsb, prd=prd, pra=pra, gad=gad, gaa=gaa)
                        ltip = tip
                    
                    if dototmas and mas != lmas:
                        prd, pra, gad, gaa = tt['m%s' % mas]
                        if TestZero(prd, pra):
                            if (dototcon or dototpdc) and len(self.rsbil)>0:
                                self.AppendRow(tip)
                            self.AppendRow(tip, mas=mas, des=r[ncdma],\
                                           prd=prd, pra=pra, gad=gad, gaa=gaa)
                        lmas = mas
                    
                    if dototcon and con != lcon:
                        prd, pra, gad, gaa = tt['c%s' % con]
                        if TestZero(prd, pra):
                            self.AppendRow(tip, con=con, des=r[ncdco],\
                                           prd=prd, pra=pra, gad=gad, gaa=gaa)
                        lcon = con
                    
                    if dototpdc and\
                       ((not r[nctpt] in "CF" or parms['detcf']) and\
                        TestZero(rowd, rowa)):
                        self.AppendRow(tip,\
                                       pid=pid, pdc=pdc, tpi=tpi, tpa=tpa, des=des,\
                                       prd=rowd, pra=rowa,\
                                       gad=rgad, gaa=rgaa)
#                        self.AppendRow(tip,\
#                                       pid=pid, pdc=pdc, tpi=tpi, tpa=tpa, des=des,\
#                                       prd=rowd, pra=rowa)
                    
                    if dototpdc and r[nctpt] in "CF" and not parms['detcf'] and\
                        TestZero(rowd, rowa):
                        self.AppendRow(tip,\
                                       pid=pid, pdc="***", tpi=tpi, tpa=tpa, des="SOTTOCONTI ACCORPATI",\
                                       prd=rowd, pra=rowa, accorpa=r[nctpt],\
                                       gad=rgad, gaa=rgaa)
#                        self.AppendRow(tip,\
#                                       pid=pid, pdc="***", tpi=tpi, tpa=tpa, des="SOTTOCONTI ACCORPATI",\
#                                       prd=rowd, pra=rowa, accorpa=r[nctpt])
                    
                elif not r[nctpt] in "CF" or parms['detcf'] and\
                     TestZero(rowd, rowa):
                    self.AppendRow(tip, mas=mas, con=con,\
                                   pid=pid, pdc=pdc, tpi=tpi, tpa=tpa, des=des,\
                                   prd=rowd, pra=rowa, gad=rgad, gaa=rgaa)
#                    self.AppendRow(tip, mas=mas, con=con,\
#                                   pid=pid, pdc=pdc, tpi=tpi, tpa=tpa, des=des,\
#                                   prd=rowd, pra=rowa)
            
            if parms['globaltot']:
                self.AppendRow(-1, mas="-", con="-",\
                               pdc="-", tpa="-", des="TOTALI",\
                               prd=self.totd, pra=self.tota,\
                               gad=self.tgad, gaa=self.tgaa)
#                self.AppendRow(-1, mas="-", con="-",\
#                               pdc="-", tpa="-", des="TOTALI",\
#                               prd=self.totd, pra=self.tota)
            
            self.Freeze()
            try:
                self.ChangeData(self.rsbil)
                self.AnchorColumn()
            finally:
                self.Thaw()
        
        finally:
            del self.timer
    
    def OnTimer(self, event):
        self.pbar.SetValue(self.pbcur)
    
    def Filter(self, *args):
        return True
    
#    def AppendRow(self, tip,\
#                  mas=None, con=None, pid=None, pdc=None, tpi=None, tpa=None, des=None,\
#                  prd=None, pra=None, accorpa=None):
    def AppendRow(self, tip,\
                  mas=None, con=None, pid=None, pdc=None, tpi=None, tpa=None, des=None,\
                  prd=None, pra=None, accorpa=None, gad=None, gaa=None):
        
        if prd is None or pra is None:
            sld, sla = None, None
        else:
            sld, sla = prd-pra, 0
            if sld < 0:
                sld, sla = sla, -sld
        
        if prd == 0: prd = None
        if pra == 0: pra = None
        if sld == 0: sld = None
        if sla == 0: sla = None

        if gad == 0: gad = None
        if gaa == 0: gaa = None
        
        app = True
        if accorpa is not None:
            try:
                if self.rsbil[-1][6] == "***":
                    lr = self.rsbil[-1]
                    lr[8] = (self.rsbil[-1][8] or 0)+(prd or 0)
                    lr[9] = (self.rsbil[-1][9] or 0)+(pra or 0)
                    if lr[8] >= lr[9]:
                        lr[10], lr[11] = lr[8]-lr[9], None
                    else:
                        lr[10], lr[11] = None, lr[9]-lr[8]
                    app = False
                    lr[12] = (self.rsbil[-1][12] or 0)+(gad or 0)
                    lr[13] = (self.rsbil[-1][13] or 0)+(gaa or 0)
            except:
                pass
        if app:
            if accorpa == "C":
                des = "*** CLIENTI VARI ***"
            elif accorpa == "F":
                des = "*** FORNITORI VARI ***"
            self.rsbil.append([tip,  #GRIDCOL_TIPBIL
                               mas,  #GRIDCOL_CODMAS
                               con,  #GRIDCOL_CODCON
                               tpi,  #GRIDCOL_IDTIP
                               tpa,  #GRIDCOL_CODTIP
                               pid,  #GRIDCOL_IDPDC
                               pdc,  #GRIDCOL_CODPDC
                               des,  #GRIDCOL_DESC
                               prd,  #GRIDCOL_PROGRD
                               pra,  #GRIDCOL_PROGRA
                               sld,  #GRIDCOL_SALDOD
                               sla,  #GRIDCOL_SALDOA
                               gad,  #GRIDCOL_SALGAD
                               gaa]) #GRIDCOL_SALGAA
        return self.rsbil[-1]
    

# ------------------------------------------------------------------------------


class BilGestGridsPool(object):
    
    def __init__(self, dbbil, panels):
        object.__init__(self)
        self.grids = [ BilGestGrid(dbbil, p) for p in panels ]
        for n, tipo in enumerate((0,1,2)):
            self.grids[n].tipo =  tipo
    
    def UpdateGrid(self, pbar, **kwargs):
        kwargs['pbmax'] = len(self.grids)
        for gnum, grid in enumerate(self.grids):
            kwargs['pbper'] = gnum
            grid.UpdateGrid(pbar, **kwargs)
    
    def __setattr__(self, name, val):
        if name in ('colors', 'intesta'):
            for grid in self.grids:
                grid.colors = val
        else:
            object.__setattr__(self, name, val)
    
    
# ------------------------------------------------------------------------------


class BilGestGrid(_BilGrid):
    
    def __init__(self, dbbil, pp):
        
        class _BilContrGridTable(dbglib.DbGridTable):
            def GetDataValue(self, row, col):
                if self.rsColumns[col] == -1:
                    rd = self.data[row]
                    out = abs((rd[GRIDCOL_PROGRD] or 0)-\
                              (rd[GRIDCOL_PROGRA] or 0))
                else:
                    out = dbglib.DbGridTable.GetDataValue(self, row, col)
                return out
        
        _BilGrid.__init__(self, dbbil, pp, tableClass=_BilContrGridTable)
    
    def GetGridColumns(self):
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        iw = 110 # val col width
        
        mov = self.dbbil
        pdc = mov.pdc
        mas = pdc.bilmas
        con = pdc.bilcon
        
        #colonna contenuto (solo per intestazione/piede se ordin=bil)
        # 0      tipo di bilancio, solo sull'intestazione
        # 1      codice del mastro
        # 2      codice del conto
        # 3      codice del sottoconto
        #
        #colonna contenuto
        # 4      descrizione (tipo bil, mastro, conto, sottoconto)
        # 5      progr. dare
        # 6      progr. avere
        # 7      saldo se dare
        # 8      saldo se avere
        
        cols = (
            ( 50, (GRIDCOL_CODMAS, "Mastro",      _STR, False )),
            ( 50, (GRIDCOL_CODCON, "Conto",       _STR, False )),
            ( 50, (GRIDCOL_CODPDC, "Cod.",        _STR, False )),
            ( 50, (GRIDCOL_CODTIP, "Tipo",        _STR, False )),
            (260, (GRIDCOL_DESC,   "Sottoconto",  _STR, False )),
            ( iw, (GRIDCOL_SALDOD, "Saldo Dare",  _IMP, True  )),
            ( iw, (GRIDCOL_SALDOA, "Saldo Avere", _IMP, True  )),
            ( iw, (GRIDCOL_PROGRD, "Progr.Dare",  _IMP, True  )),
            ( iw, (GRIDCOL_PROGRA, "Progr.Avere", _IMP, True  )),
            ( iw, (GRIDCOL_SALGAD, "G.Ap.Dare",   _IMP, True  )),
            ( iw, (GRIDCOL_SALGAA, "G.Ap.Avere",  _IMP, True  )),
        )
        anchorcol = 6
        resizecol = 4
        fitcol = 4
        return cols, anchorcol, resizecol, fitcol
    
    def Filter(self, tipo, *args, **kwargs):
        return self.tipo == tipo
    

# ------------------------------------------------------------------------------


class _BilPanel(aw.Panel):
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        self.InitWdr()
        
        import cfg.dbtables as dbx
        self.dbbil =     self.GetTabBilancio()
        self.dbese =     dbx.ProgrEsercizio()
        self.gridbil =   None
        self.pmulti =    1
        self.globaltot = False
        self.report =    None
        self.bilese =    True
        self.salep =     [0,0]  #saldi pat/eco es.precedenti se bil.esercizio
        self.descperiodo = ''
        self.pdcparz =   False
        
        a = dbc.adb.DbTable(bt.TABNAME_CFGAUTOM, 'aut')
        a.Retrieve('codice=%s', 'regapecau')
        self.cauape = a.aut_id
        a.Retrieve('codice=%s', 'regchicau')
        self.cauchi = a.aut_id
        
        self.dbcfg = CfgContab()
        self.dbcfg.SetEsercizio(dbc.Env.Azienda.Login.dataElab)
        
        self.InitPanelBilancio()
        wdr.BilancioFunc(self)
        
        cn = lambda x: self.FindWindowByName(x)
        
        #inizializzazione valori controlli radio
        for name, val, init in (('tipord',  'CDB', 'B'),\
                                ('inclape', 'IES', 'I'),\
                                ('inclchi', 'IES', 'I')):
            cn(name).SetDataLink(name, val)
            cn(name).SetValue(init)
        cn('tipdet').SetValue("S")
        
        e = dbc.Env.Azienda.Esercizio
        for name, val in (('datreg1', e.start),
                          ('datreg2', e.dataElab),
                          ('eserc',   e.year)):
            cn(name).SetValue(val)
        
        self.EnableControls()
        
        for evt, func, cid in \
            ((wx.EVT_RADIOBOX, self.OnUpdate,    wdr.ID_TIPORD),
             (wx.EVT_RADIOBOX, self.OnUpdate,    wdr.ID_INCLAPE),
             (wx.EVT_RADIOBOX, self.OnUpdate,    wdr.ID_INCLCHI),
             (wx.EVT_RADIOBOX, self.OnRiTot,     wdr.ID_TIPDET),
             (wx.EVT_CHECKBOX, self.OnRiTot,     wdr.ID_DETCLIFOR),
             (wx.EVT_CHECKBOX, self.OnRiTot,     wdr.ID_DETNOZERO),
             (wx.EVT_CHECKBOX, self.OnPeriodo,   wdr.ID_PERIODO),
             (wx.EVT_BUTTON,   self.OnUpdate,    wdr.ID_BTNUPD),
             (wx.EVT_BUTTON,   self.OnPrint,     wdr.ID_BTNPRINT),
             (wx.EVT_CHOICE,   self.OnEsercizio, wdr.ID_ESERC),
             ):
            self.Bind(evt, func, id=cid)
    
    def GetTabBilancio(self):
        return dbc.Bilancio()
    
    def InitWdr(self):
        wdr.bilmas_table = bt.TABNAME_BILMAS
        wdr.bilcon_table = bt.TABNAME_BILCON
        wdr.bilmas_dialog = wdr.BilMasDialog
        wdr.bilcon_dialog = wdr.BilConDialog
    
    def GetPeriodo(self):
        return self.descperiodo
    
    def OnEsercizio(self, event):
        if self.bilese:
            e = dbc.Env.Azienda.Esercizio
            es = event.GetEventObject().GetValue()
            #for cid, val in ((wdr.ID_DATREG1, DateTime.Date(es, e.start.month, e.start.day)),
                             #(wdr.ID_DATREG2, DateTime.Date(es, e.end.month, e.end.day))):
                #self.FindWindowById(cid).SetValue(val)
            di = DateTime.Date(es, e.start.month, e.start.day)
            self.FindWindowById(wdr.ID_DATREG1).SetValue(di)
        event.Skip()
    
    def EnableControls(self):
        
        def ci(x):
            return self.FindWindowById(x)
        
        d1, d2 = map(lambda x: ci(x), (wdr.ID_DATREG1,
                                       wdr.ID_DATREG2))
        d1.Enable(not self.bilese)
        e, l, s = map(lambda x: ci(x), (wdr.ID_ESERC,
                                        wdr.ID_ESERCLABEL,
                                        wdr.ID_SALEP))
        for c in (e, l, s):
            c.Enable(self.bilese)
        if self.bilese:
            c = e
        else:
            c = d1
        ci(wdr.ID_DATREG1).Enable(not self.bilese)
        c.SetFocus()
        self.UpdateTitle()
    
    def OnPeriodo(self, event):
        self.SetBilEse(not event.GetEventObject().GetValue())
        event.Skip()
    
    def SetBilEse(self, bilese):
        self.bilese = bilese
        self.EnableControls()
    
    def UpdateTitle(self):
        def ci(x): return self.FindWindowById(x)
        lab = 'Bilancio '
        if self.bilese:
            lab += 'di esercizio'
        else:
            lab += 'di periodo'
        ci(wdr.ID_TITLE).SetLabel(lab)
    
    def OnPrint(self, event):
        if self.dbbil.RowsCount() == 0:
            aw.awu.MsgDialog(self, message='Nessun dato da stampare')
            return
        self.PrintBil()
        event.Skip()
    
    def PrintBil(self):
        raise Exception, "Classe non istanziabile"
    
    def InitPanelBilancio(self):
        raise Exception,\
              """Questa classe non è istanziabile"""

    def OnUpdate(self, event):
        self.UpdateBil()
        event.Skip()
    
    def OnRiTot(self, event):
        if self.dbbil.RowsCount()>0:
            self.UpdateGrid()
        event.Skip()
    
    def UpdateBil(self):
        
        def cn(x):
            return self.FindWindowByName(x)
        
        b = self.dbbil
        
        #impostazione filtri
        ese, d1, d2 = map(lambda x:\
                          self.FindWindowById(x).GetValue(), (wdr.ID_ESERC,
                                                              wdr.ID_DATREG1,
                                                              wdr.ID_DATREG2))
        
        if ese is None:
            aw.awu.MsgDialog(self, "Nessun esercizio presente", style=wx.ICON_ERROR)
            return
        
        if self.bilese:
            t = 'ESERCIZIO %d  ' % ese
            if cn('salep').GetValue():
                c = 2
            else:
                c = 1
        else:
            t = 'Periodo: '
            c = 1
        dita = dbc.adb.DbTable.dita
        self.descperiodo = t+('%s - %s' % tuple(map(dita, (d1, d2))))
        
        self.salep[0] = self.salep[1] = 0
        self.pdcparz = False
        b.ResetPrintFilterValues()
        
        pe = dbc.ProgrEsercizio()
        eco = pe.GetEsercizioInCorso()
        
        for n in range(c, 0, -1):
            
            b.ClearFilters()
            
            if n == 2:
                #bilancio di esercizio
                #estraz. x saldo patrimoniali esercizi precedenti
#                f = "(bilmas.tipo='P' AND reg.esercizio<%s)"
#                b.AddFilter(f, ese)
                if ese == eco:
                    #bilancio su esercizio in corso: nessun riporto
                    b.AddFilter('0')
                elif ese > eco:
                    #bilancio su esercizio successivo a quello in corso: riporto da esercizio in corso
                    b.AddFilter("(bilmas.tipo='P' AND reg.esercizio>=%s AND reg.esercizio<%s)", eco, ese)
                else:
                    #bilancio precedente a esercizio in corso: riporto da tutti gli esercizi presenti precedenti quello in corso
#                    b.AddFilter("(bilmas.tipo='P' AND reg.esercizio<%s)", ese)
                    #bilancio precedente a esercizio in corso: nessun riporto
                    b.AddFilter("0")
            else:
                #estraz. bilancio
                if self.bilese:
                    #di esercizio
                    if cn('salep').GetValue():
#                        f = "(bilmas.tipo='P' AND reg.esercizio<=%s) OR (bilmas.tipo<>'P' AND reg.esercizio=%s)"
#                        b.AddFilter(f, ese, ese)
                        if ese == eco:
                            #bilancio su esercizio in corso: solo registrazioni esercizio in corso
                            b.AddFilter("reg.esercizio=%s", eco)
                        elif ese > eco:
                            #bilancio su esercizio successivo a quello in corso: riporto da esercizio in corso, registrazioni esercizio desiderato
                            b.AddFilter("(bilmas.tipo='P' AND reg.esercizio>=%s AND reg.esercizio<=%s) OR (bilmas.tipo<>'P' AND reg.esercizio=%s)", eco, ese, ese)
                        else:
#                            #bilancio precedente a esercizio in corso: riporto da tutti gli esercizi presenti precedenti quello in corso, registrazioni esercizio desiderato
#                            b.AddFilter("(bilmas.tipo='P' AND reg.esercizio<=%s) OR (bilmas.tipo<>'P' AND reg.esercizio=%s)", ese, ese)
                            #bilancio precedente a esercizio in corso: nessun riporto
                            b.AddFilter("reg.esercizio=%s", ese)
                    else:
                        f = "reg.esercizio=%s"
                        b.AddFilter(f, ese)
                    val = cn('datreg2').GetValue()
                    if val:
                        b.AddFilter('reg.datreg<=%s', val)
                else:
                    #di periodo
                    for name, expr in (('datreg1', 'reg.datreg>=%s'),
                                       ('datreg2', 'reg.datreg<=%s')):
                        val = cn(name).GetValue()
                        if val:
                            b.AddFilter(expr, val)
            
            for name, expr in (('mas1',    'pdc.id_bilmas>=%s'),
                               ('mas2',    'pdc.id_bilmas<=%s'),
                               ('con1',    'pdc.id_bilcon>=%s'),
                               ('con2',    'pdc.id_bilcon<=%s'),
                               ('tip1',    'pdc.id_tipo>=%s'),
                               ('tip2',    'pdc.id_tipo<=%s'),
                               ('pdc1',    'pdc.codice<=%s'),
                               ('pdc2',    'pdc.codice<=%s')):
                val = cn(name).GetValue()
                if val is not None:
                    b.AddFilter(expr, val)
                    if n != 2:
                        b.SetPrintFilterValue('%scod'%name, cn(name).GetValueCod())
                        b.SetPrintFilterValue('%sdes'%name, cn(name).GetValueDes())
                        self.pdcparz = True
            
            ia = cn('inclape').GetValue()
            if ia == "E":
                b.AddFilter("reg.esercizio=%s AND reg.id_caus<>%s", ese, self.cauape)
            elif ia == "S":
                b.AddFilter("reg.esercizio=%s AND reg.id_caus=%s", ese, self.cauape)
            
            ic = cn('inclchi').GetValue()
            if ic == "E":
                b.AddFilter("reg.esercizio=%s AND reg.id_caus<>%s", ese, self.cauchi)
            elif ic == "S":
                b.AddFilter("reg.esercizio=%s AND reg.id_caus=%s", ese, self.cauchi)
            
            if n == 2:
                wait = MsgWait(self, message=\
                               "Estrazione dati esercizi precedenti in corso")
                b.Retrieve()
                tots = {0: 0, #pat
                        1: 0} #eco
                ND = bt.VALINT_DECIMALS
                for b in b:
                    if b.tipobil == 0:   #pat
                        s = 1
                    elif b.tipobil == 1: #eco
                        s = -1
                    else:
                        s = None
                    if s is not None:
                        tots[b.tipobil] += round(((b.total_dare or 0)-\
                                                  (b.total_avere or 0))*s, ND)
                self.salep[0] = tots[0]
                self.salep[1] = tots[1]
                wait.Destroy()
        
        #impostazione ordinamento
        ord = self.FindWindowByName('tipord').GetValue()
        if   ord == 'C':
            b.SetOrdinamento(dbc.BILORD_COD)
            self.gridbil.colors = False
            
        elif ord == 'D':
            b.SetOrdinamento(dbc.BILORD_DES)
            self.gridbil.colors = False
            
        elif ord == 'B':
            b.SetOrdinamento(dbc.BILORD_BIL)
            self.gridbil.colors = True
        
        wait = MsgWait(self, message="Estrazione dati in corso")
        
        b.Retrieve()
        
        wait.Destroy()
        
        self.UpdateGrid()
    
    def UpdateGrid(self):
        
        parms = {}
        for name in ('tipdet', 'detcf', 'detnozero'):
            val = self.FindWindowByName(name).GetValue()
            if val is not None:
                parms[name] = val
        parms['globaltot'] = self.globaltot
        
        wait = MsgWait(self,\
                       message="Totalizzazione bilancio in corso",\
                       maximum=self.dbbil.RowsCount()*self.pmulti)
        
        self.gridbil.UpdateGrid(wait, **parms)
        
        wait.Destroy()
    
    def UpdateQuadratura(self, totd, tota, salep=False, utiper=None, ripep=True, quadonly=False):
        sepn = dbc.adb.DbTable.sepn
        ND = bt.VALINT_DECIMALS
        val = ''
        if self.bilese:
            totd = round(totd-self.salep[0], ND)
        if utiper is None:
            utiper = totd-tota
        if self.pdcparz:
            val = '(Estratto parziale del Piano dei Conti)'
            color = 'darkgreen'
        else:
            if SameFloat(totd, tota):
                if quadonly:
                    val = "Nessuna squadratura rilevata"
                else:
                    riepese = self.bilese and salep and self.salep[0]
                    if (self.bilese and ripep) or not salep:
                        if utiper>=0:
                            val = 'Utile'
                            if riepese:
                                val += ' rilevato'
                            elif self.bilese:
                                val += ' di esercizio'
                        else:
                            val = 'Perdita'
                            if riepese:
                                val += ' rilevata'
                            elif self.bilese:
                                val += ' di esercizio'
                        if not self.bilese:
                            val += ' del periodo'
                        val += ': %s' % sepn(abs(utiper), ND)
                    if riepese and ripep:
                        if self.salep[0]>0:
                            up = 'utile'
                        else:
                            up = 'perdita'
                        val += ' (%s da esercizi precedenti: %s)  '\
                            % (up, sepn(abs(self.salep[0]), ND))
                    if riepese:
                        s = utiper-self.salep[0]
                        if s>0:
                            up = 'Utile'
                        else:
                            up = 'Perdita'
                        val += '%s di esercizio: %s' % (up, sepn(abs(s), ND))
                color = 'blue'
            else:
                val = 'Attenzione: rilevata squadratura di %s in %s'\
                    % (sepn(abs(totd-tota), ND), ("DARE", "AVERE")[int(totd>tota)])
                color = 'red'
        c = self.FindWindowByName('warning')
        c.SetLabel('')
        c.SetForegroundColour(color)
        c.SetLabel(val)


# ------------------------------------------------------------------------------


class BilGestPanel(_BilPanel):
    
    def __init__(self, *args, **kwargs):
        
        wdr.BilancioTipoLivelloFunc = None
        _BilPanel.__init__(self, *args, **kwargs)
        self.report = 'Bilancio Gestionale'
        self.pmulti = 3
    
    def InitPanelBilancio(self):
        p = wx.Panel(self, wdr.ID_PANGRIDS)
        wdr.BilGestFunc(p)
        self.gridbil = BilGestGridsPool(self.dbbil,\
                                        [self.FindWindowById(x)\
                                         for x in (wdr.ID_PANGESPAT,
                                                   wdr.ID_PANGESECO,
                                                   wdr.ID_PANGESORD)])
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSezChanged, 
                  id=wdr.ID_BILGESTZONE)
    
    def OnSezChanged(self, event):
        self.UpdateTotals()
        event.Skip()
    
    def UpdateGrid(self):
        _BilPanel.UpdateGrid(self)
        self.UpdateTotals()
    
    def UpdateTotals(self):
        grids = self.gridbil.grids
#        gridpat, grideco = grids[:2]
        gridpat, grideco = grids[:2]
        ND = bt.VALINT_DECIMALS
        totd = round(gridpat.totd-gridpat.tota, ND)
        tota = round(grideco.tota-grideco.totd, ND)
        try:
            up = (gridpat.rsbil[0][10] or 0)-(gridpat.rsbil[0][11] or 0)
        except:
            up = 0
        self.UpdateQuadratura(totd, tota, salep=self.bilese, utiper=up)
    
    def UpdateQuadratura(self, totd, tota, salep=False, utiper=None):
        def ci(x):
            return self.FindWindowById(x)
        sezno = ci(wdr.ID_BILGESTZONE).GetSelection()
        return _BilPanel.UpdateQuadratura(self, totd, tota, 
                                          salep=self.bilese, utiper=utiper,
                                          ripep=(sezno == 0))
    
    def PrintBil(self):
#        bil = DbMemBil(self, 'tip,mas,con,tpi,tpa,pid,pdc,des,prd,pra,sld,sla')
        bil = DbMemBil(self, 'tip,mas,con,tpi,tpa,pid,pdc,des,prd,pra,sld,sla,gad,gaa')
        bil.SetRecordset(self.gridbil.grids[0].rsbil
                         +self.gridbil.grids[1].rsbil
                         +self.gridbil.grids[2].rsbil)
        bil._info.printfilters = self.dbbil._info.printfilters
        def adegua(rptname, report):
            dbt = bil
            if 'strutt' in rptname.lower():
#                bil2 = DbMemBil(self, 'tip,mas,con,tpi,tpa,pid,pdc,des,prd,pra,sld,sla,dmas,dcon')
                bil2 = DbMemBil(self, 'tip,mas,con,tpi,tpa,pid,pdc,des,prd,pra,sld,sla,dmas,dcon,gad,gaa')
                l_tip = l_mas = l_con = None
                ldmas = ldcon = None
                for b in bil:
                    if b.con is not None:
                        l_con = b.con
                        ldcon = b.des
                    if b.mas is not None:
                        l_mas = b.mas
                        ldmas = b.des
                        l_con = None
                    if b.tip is not None and b.pdc is not None and b.mas is None and b.con is None:
                        l_tip = b.tip
                    if b.pdc is not None:
                        bil2.CreateNewRow()
                        bil2.tip = bil.tip
                        bil2.mas = l_mas
                        bil2.con = l_con
                        bil2.tpi = b.tpi
                        bil2.tpa = b.tpa
                        bil2.pid = b.pid
                        bil2.pdc = b.pdc
                        bil2.des = b.des
                        bil2.prd = b.prd
                        bil2.pra = b.pra
                        bil2.sld = b.sld
                        bil2.sla = b.sla
                        bil2.dmas = ldmas
                        bil2.dcon = ldcon
                        bil2.gad = b.gad
                        bil2.gaa = b.gaa
                dbt = bil2
            return dbt
        rpt.Report(self, bil, self.report, dbfunc=adegua)


# ------------------------------------------------------------------------------


class BilGestFrame(aw.Frame):
    """
    Frame Bilancio gestionale.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILGES
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilGestPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilGestDialog(aw.Dialog):
    """
    Dialog Bilancio gestionale.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILGES
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilGestPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilVerifPanel(_BilPanel):
    
    def __init__(self, *args, **kwargs):
        
        wdr.BilancioTipoLivelloFunc = None
        _BilPanel.__init__(self, *args, **kwargs)
        self.report = 'Bilancio di Verifica'
        self.globaltot = True
        
        #inizializzazione valori controlli radio
        for name, init in (('tipord', 'C'),):
            self.FindWindowByName(name).SetValue(init)

    def InitPanelBilancio(self):
        p = wx.Panel(self, wdr.ID_PANGRIDS, size=(-1, 360))
        self.gridbil = BilVerifGrid(self.dbbil, p)
    
    def UpdateGrid(self):
        _BilPanel.UpdateGrid(self)
        self.UpdateQuadratura(self.gridbil.totd, self.gridbil.tota, salep=True, quadonly=True)

    def PrintBil(self):
#        bil = DbMemBil(self, 'tip,mas,con,tpi,tpa,pid,pdc,des,prd,pra,sld,sla')
        bil = DbMemBil(self, 'tip,mas,con,tpi,tpa,pid,pdc,des,prd,pra,sld,sla,gad,gaa')
        bil.SetRecordset(self.gridbil.rsbil)
        rpt.Report(self, bil, self.report)


# ------------------------------------------------------------------------------


class BilVerifFrame(aw.Frame):
    """
    Frame Bilancio di verifica.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILVER
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilVerifPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilVerifGrid(BilGestGrid):
    def Filter(self, *args, **kwargs):
        return True


# ------------------------------------------------------------------------------


class BilVerifDialog(aw.Dialog):
    """
    Dialog Bilancio di verifica.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILVER
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilVerifPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilContrGridsPool(object):
    
    def __init__(self, dbbil, panels):
        object.__init__(self)
        self.grids = [ BilContrGrid(dbbil, p) for p in panels ]
        for n, (tipo, isdare) in enumerate(((0, True ),\
                                            (0, False),\
                                            (1, True ),\
                                            (1, False),
                                            (2, True ),\
                                            (2, False),)):
            self.grids[n].tipo =  tipo
            self.grids[n].isdare = isdare
    
    def UpdateGrid(self, pbar, **kwargs):
        kwargs['pbmax'] = 6
        for gnum, grid in enumerate(self.grids):
            kwargs['pbper'] = gnum
            grid.UpdateGrid(pbar, **kwargs)
    
    def __setattr__(self, name, val):
        if name in ('colors', 'intesta'):
            for grid in self.grids:
                grid.colors = val
        else:
            object.__setattr__(self, name, val)
    
    
# ------------------------------------------------------------------------------


class BilContrGrid(_BilGrid):
    
    def __init__(self, dbbil, pp):
        
        class _BilContrGridTable(dbglib.DbGridTable):
            def GetDataValue(self, row, col):
                if self.rsColumns[col] == -1:
                    rd = self.data[row]
                    out = abs((rd[GRIDCOL_PROGRD] or 0)-\
                              (rd[GRIDCOL_PROGRA] or 0))
                else:
                    out = dbglib.DbGridTable.GetDataValue(self, row, col)
                return out
        
        _BilGrid.__init__(self, dbbil, pp, tableClass=_BilContrGridTable)
        
        self.intesta = False
        self.tipo =    None
        self.isdare =  None
    
    def GetGridColumns(self):
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        iw = 110 # val col width
        
        mov = self.dbbil
        pdc = mov.pdc
        mas = pdc.bilmas
        con = pdc.bilcon
        
        #colonna contenuto (solo per intestazione/piede se ordin=bil)
        # 0      tipo di bilancio, solo sull'intestazione
        # 1      codice del mastro
        # 2      codice del conto
        # 3      codice del sottoconto
        #
        #colonna contenuto
        # 4      descrizione (tipo bil, mastro, conto, sottoconto)
        # 5      progr. dare
        # 6      progr. avere
        # 7      saldo se dare
        # 8      saldo se avere
        
        cols = (
            ( 35, (GRIDCOL_CODMAS, "Mastro",      _STR, False )),
            ( 35, (GRIDCOL_CODCON, "Conto",       _STR, False )),
            ( 50, (GRIDCOL_CODPDC, "Cod.",        _STR, False )),
            ( 35, (GRIDCOL_CODTIP, "Tipo",        _STR, False )),
            (160, (GRIDCOL_DESC,   "Sottoconto",  _STR, False )),
            ( iw, (-1,             "Saldo",       _IMP, True  )),
        )
        anchorcol = resizecol = None
        fitcol = 4
        return cols, anchorcol, resizecol, fitcol
    
    def Filter(self, tipo, isdare):
        return self.tipo == tipo and self.isdare == isdare
    

# ------------------------------------------------------------------------------


class BilContrPanel(_BilPanel):
    
    def __init__(self, *args, **kwargs):
        
        wdr.BilancioTipoLivelloFunc = None
        _BilPanel.__init__(self, *args, **kwargs)
        self.report = 'Bilancio Contrapposto'
        self.pmulti = 6
        for name in 'pupa pupp eupc eupr oupd oupa'.split():
            self.FindWindowByName("lab%s" % name).Show(False)
            self.FindWindowByName("tot%s" % name).Enable(False)
        self.adjustsize = True
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnSezChanged, 
                  id=wdr.ID_BILCONTRZONE)
    
    def OnSezChanged(self, event):
        self.UpdateTotals()
        event.Skip()
    
    def InitPanelBilancio(self):
        
        def ci(x):
            return self.FindWindowById(x)
        
        p = wx.Panel(self, wdr.ID_PANGRIDS)
        wdr.BilContrFunc(p)
        
        for cid in (wdr.ID_UTIESP,  wdr.ID_LABUTIESP,
                    wdr.ID_PERESP,  wdr.ID_LABPERESP,
                    wdr.ID_TOTPUPA, wdr.ID_LABPUPA,
                    wdr.ID_TOTPUPP, wdr.ID_LABPUPP,
                    wdr.ID_TOTEUPC, wdr.ID_LABEUPC,
                    wdr.ID_TOTEUPR, wdr.ID_LABEUPR,
                    wdr.ID_TOTOUPD, wdr.ID_LABOUPD,
                    wdr.ID_TOTOUPA, wdr.ID_LABOUPA,):
            ci(cid).Show(False)
        
        for splitid, sizeIndex in ((wdr.ID_BILPATRZONE, 0),\
                                   (wdr.ID_BILECONZONE, 0),\
                                   (wdr.ID_BILORDZONE,  0),):
            split = ci(splitid)
            split.SetSashPosition(split.GetSize()[sizeIndex]/2)
            split.SetSashGravity(0.5)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,\
                  self.OnSashPatSizeChanged, ci(wdr.ID_BILPATRZONE))
        
        self.gridbil = BilContrGridsPool(self.dbbil,\
                                         [ci(x) for x in (wdr.ID_PANPATATT,\
                                                          wdr.ID_PANPATPAS,\
                                                          wdr.ID_PANECOCOS,\
                                                          wdr.ID_PANECORIC,\
                                                          wdr.ID_PANORDDAR,\
                                                          wdr.ID_PANORDAVE,)])
    
    def OnSashPatSizeChanged(self, event):
        def ci(x):
            return self.FindWindowById(x)
        split = event.GetEventObject()
        def AdjustSizeEco():
            pos = ci(wdr.ID_BILPATRZONE).GetSashPosition()
            ci(wdr.ID_BILECONZONE).SetSashPosition(pos)
            ci(wdr.ID_BILORDZONE).SetSashPosition(pos)
        wx.CallAfter(AdjustSizeEco)
        event.Skip()
    
    def ChangeSashPosition(self, split, pos):
        self.FindWindowById(split).SetSashPosition(pos)
    
    def UpdateBil(self):
        _BilPanel.UpdateBil(self)
        self.UpdateTotals()
    
    def UpdateTotals(self):
        
        cn = self.FindWindowByName
        
        def Cval(name, val):
            cn(name).SetValue(val)
        
        def Cshow(name, show):
            cn(name).Show(show)
        
        def Cenab(name, enab):
            cn(name).Enable(enab)
        
        #determinazione totali di sezione
        totali = {}
        for n, totname in enumerate(('totpatt',\
                                     'totppas',\
                                     'totecos',\
                                     'toteric',\
                                     'totodar',\
                                     'totoave')):
            totali[totname] = abs((self.gridbil.grids[n].totd or 0)-\
                                  (self.gridbil.grids[n].tota or 0))
            Cval(totname, totali[totname])
        
        t = totali
        #determinazione utile/perdita e tot. a pareggio
        for tipo in 'peo':
            if tipo == 'p':
                tsx = 'totpatt'; ssx = 'totpupa'; lsx = 'labpupa'
                tdx = 'totppas'; sdx = 'totpupp'; ldx = 'labpupp'
            elif tipo == 'e':
                tsx = 'totecos'; ssx = 'toteupc'; lsx = 'labeupc'
                tdx = 'toteric'; sdx = 'toteupr'; ldx = 'labeupr'
            else:
                tsx = 'totodar'; ssx = 'totoupd'; lsx = 'laboupd'
                tdx = 'totoave'; sdx = 'totoupa'; ldx = 'laboupa'
            if t[tsx] >= t[tdx]:              
                totsx = abs(t[tsx]-t[tdx])
                if tipo == 'p':
                    totsx -= self.salep[0]
                totdx = None
                #labsx = True
                #labdx = False
                #enabsx = True
                #enabdx = False
            else:
                totsx = None
                totdx = abs(t[tsx]-t[tdx])
                if tipo == 'p':
                    totdx -= self.salep[0]
                #labsx = False
                #labdx = True
                #enabsx = False
                #enabdx = True
            if totsx and totsx<0:
                totdx = -totsx
                totsx = None
            elif totdx and totdx<0:
                totsx = -totdx
                totdx = None
            labsx = enabsx = totsx>=0
            labdx = enabdx = totsx<0
            #aggiornamento totali di sezione
            for name, val in ((tsx, t[tsx]),\
                              (tdx, t[tdx])):
                Cval(name, val)
            #aggiornamento labels utile/perdita
            for name, val in ((lsx, labsx),\
                              (ldx, labdx )):
                Cshow(name, val)
            #aggiornamento valori utile/perdita
            for name, val, en in ((ssx, totsx, enabsx),\
                                  (sdx, totdx, enabdx)):
                Cval(name, val)
                Cshow(name, en)
        for name, show in (('utiesp', self.salep[0]>0),
                           ('peresp', self.salep[0]<0)):
            if show:
                val = abs(self.salep[0])
            else:
                val = 0
            Cval(name, val)
            Cshow(name, show)
            Cshow('lab%s' % name, show)
        
        #determinazione quadratura bilancio
        totpat = t['totpatt'] - t['totppas']
        toteco = t['toteric'] - t['totecos']
        totord = t['totodar'] - t['totoave']
        self.totpatatt = tpa = t['totpatt']
        self.totpatpas = tpp = t['totppas']
        self.totecocos = tec = t['totecos']
        self.totecoric = ter = t['toteric']
        self.totorddar = tod = t['totodar']
        self.totordave = toa = t['totoave']
        sezno = self.FindWindowById(wdr.ID_BILCONTRZONE).GetSelection()
        self.UpdateQuadratura(totpat, toteco, salep=self.bilese, utiper=tpa-tpp,
                              ripep=(sezno == 0))
        
        self._Layout()

    def PrintBil(self):
        grids = self.gridbil.grids
        def GetRighe(n, rs1, rs2):
            try: r1 = rs1[n]
            except IndexError: r1 = [None]*14
            try: r2 = rs2[n]
            except IndexError: r2 = [None]*14
            return tuple(r1)+tuple(r2)
        def GetSezione(sez, rs1, rs2):
            sezrs = []
            for row in range(max(len(rs1),len(rs2))):
                sezr = [sez]
                sezr += GetRighe(row, rs1, rs2)
                sezrs.append(sezr)
            return sezrs
        rs = []
        rs += GetSezione('P', grids[0].rsbil, grids[1].rsbil)
        rs += GetSezione('E', grids[2].rsbil, grids[3].rsbil)
        rs += GetSezione('O', grids[4].rsbil, grids[5].rsbil)
        bil = DbMemBil(self,
            'sez,tip1,mas1,con1,tpi1,tpa1,pid1,pdc1,des1,prd1,pra1,sld1,sla1,tgio11,tgio12,'+
            ''+ 'tip2,mas2,con2,tpi2,tpa2,pid2,pdc2,des2,prd2,pra2,sld2,sla2,tgio21,tgio22 ')
        bil.SetRecordset(rs)
        bil.salep = self.salep
        for name in 'totpatatt totpatpas totecocos totecoric totorddar totordave'.split():
            setattr(bil, name, getattr(self, name))
        bil.tots = {'P': (self.totpatatt, self.totpatpas),
                    'E': (self.totecocos, self.totecoric),
                    'O': (self.totorddar, self.totordave)}
        rpt.Report(self, bil, self.report)


        #=======================================================================
        # nctip = ci(b, 'tipobil')
        # ncmas = ci(b, 'mastro')
        # nccon = ci(b, 'conto')
        # ncpid = ci(b.pdc, 'id')
        # ncpdc = ci(b.pdc, 'codice')
        # nctpi = ci(b.pdc.tipana, 'id')
        # nctpa = ci(b.pdc.tipana, 'codice')
        # nctpt = ci(b.pdc.tipana, 'tipo')
        # ncttd = ci(b, 'total_dare')
        # nctta = ci(b, 'total_avere')
        # ncdma = ci(b.pdc.bilmas, 'descriz')
        # ncdco = ci(b.pdc.bilcon, 'descriz')
        # ncdsc = ci(b.pdc, 'descriz')
        # nctgd = ci(b,            'total_darega')
        # nctga = ci(b,            'total_averega')
        #=======================================================================



# ------------------------------------------------------------------------------


class BilContrFrame(aw.Frame):
    """
    Frame Bilancio contrapposto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILCON
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilContrPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilContrDialog(aw.Dialog):
    """
    Dialog Bilancio contrapposto.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILGES
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilContrPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilCeeGrid(_BilGrid):
    
    def GetGridColumns(self):
        
        _STR = gl.GRID_VALUE_STRING
        _IMP = bt.GetValIntMaskInfo()
        
        iw = 110 # val col width
        
        mov = self.dbbil
        pdc = mov.pdc
        cee = pdc.bilcee
        
        #colonna contenuto (solo per intestazione/piede se ordin=bil)
        #  0      tipo di bilancio, solo sull'intestazione
        #  1      codice sezione
        #  2      codice voce
        #  3      codice capitolo
        #  4      codice dettaglio
        #  5      codice sub-dettaglio
        #  6      codice del sottoconto
        #
        #colonna contenuto
        #  7      descrizione (tipo bil, sezione, voce, capitolo, dettaglio, sub-dettaglio, sottoconto)
        #  8      saldo se dare
        #  9      saldo se avere
        # 10      valore algebrico (sempre Dare - Avere)
        
        cols = (
            ( 40, (GRIDCOL_CEESEZ, "Sez.",        _STR, False)),
            ( 40, (GRIDCOL_CEEVOC, "Voce",        _STR, False)),
            ( 60, (GRIDCOL_CEECAP, "Cap.",        _STR, False)),
            ( 50, (GRIDCOL_CEEDET, "Dett.",       _STR, False)),
            ( 40, (GRIDCOL_CEESUB, "Sub",         _STR, False)),
            ( 60, (GRIDCOL_CODPDC, "Cod.",        _STR, False)),
            (300, (GRIDCOL_DESC,   "Sottoconto",  _STR, False)),
            ( iw, (GRIDCOL_SALDOD, "Saldo Dare",  _IMP, True )),
            ( iw, (GRIDCOL_SALDOA, "Saldo Avere", _IMP, True )),
            #( iw, (GRIDCOL_CEEVAL, "Valore",      _IMP, True )),
        )
        anchorcol = 8
        resizecol = 6
        fitcol = 6
        return cols, anchorcol, resizecol, fitcol
    
    def UpdateGrid(self, pbar, **parms):
        for name, val in (('tipdet',    'S'),\
                          ('detcf',     True),\
                          ('globaltot', False),\
                          ('pbper',     0),\
                          ('pbmax',     1)):
            if not parms.has_key(name):
                parms[name] = val
        
        b = self.dbbil
        p = b.pdc
        c = p.bilcee
        def ci(tab, col):
            return tab._GetFieldIndex(col, inline=True)
        
        nctip = ci(b,            'tipobil')
        nccee = ci(b.pdc.bilcee, 'codice')
        ncsez = ci(b.pdc.bilcee, 'sezione')
        ncvoc = ci(b.pdc.bilcee, 'voce')
        nccap = ci(b.pdc.bilcee, 'capitolo')
        ncdet = ci(b.pdc.bilcee, 'dettaglio')
        ncsub = ci(b.pdc.bilcee, 'subdett')
        ncpid = ci(b.pdc,        'id')
        ncpdc = ci(b.pdc,        'codice')
        nctpi = ci(b.pdc.tipana, 'id')
        nctpa = ci(b.pdc.tipana, 'codice')
        nctpt = ci(b.pdc.tipana, 'tipo')
        ncttd = ci(b,            'total_dare')
        nctta = ci(b,            'total_avere')
        ncdsc = ci(b.pdc,        'descriz')
        
        b.SetVar('pbar', pbar)
        
        def AddTot(totdict, key, dare, avere):
            if not totdict.has_key(key):
                totdict[key] = [0, 0]
            totdict[key][0] += dare or 0
            totdict[key][1] += avere or 0
        
        totpatd = 0; totpata = 0
        totecod = 0; totecoa = 0
        totordd = 0; totorda = 0
        
        rs = b.GetRecordset()
        self.totali = {}
        tt = self.totali
        
        for row in range(b.RowsCount()):
            rowd = rs[row][ncttd]
            rowa = rs[row][nctta]
            if self.Filter(rs[row][nctip], rs[row][ncttd]>=rs[row][nctta]):
                for tipo, lun in (('s', 1),
                                  ('v', 2),
                                  ('c', 6),
                                  ('d', 8),
                                  ('u', 9),):
                    AddTot(tt, "%s%s" % (tipo, str(rs[row][nccee] or '').ljust(lun)[:lun]), rowd, rowa)
       
        dototsez = parms['tipdet'] in "ZVCDUS"
        dototvoc = parms['tipdet'] in "VCDUS"
        dototcap = parms['tipdet'] in "CDUS"
        dototdet = parms['tipdet'] in "DUS"
        dototsub = parms['tipdet'] in "US"
        dototpdc = parms['tipdet'] in "S"
        
        self.rsbil = []
        rs =    self.rsbil
        lcee =  None
        ltip =  None
        lsez =  None
        lvoc =  None
        lcap =  None
        ldet =  None
        lsub =  None
        trec =  b.RowsCount()
        tord =  b.GetVar('ordin')
        
        pbcur = trec*parms['pbper']
        trec *= parms['pbmax']
        
        self.totd = 0
        self.tota = 0
        
        class DbMemCee(DbMemBil):
            def GetTotale(mself, group, codcee, da):
                out = None
                parts = {'s': 1,
                         'v': 2,
                         'c': 6,
                         'd': 8,
                         'u': 9}
                l = parts[group]
                key = group+((codcee or '')[:l]).ljust(l)
                d,a = mself._info.win.totali[key]
                if da == 'D' and d>=a:
                    #richiesto saldo, se in dare
                    out = d-a
                elif da == 'A' and a>=d:
                    #richiesto saldo, se in avere
                    out = a-d
                elif da == 'V':
                    #richiesto valore: sempre dare-avere
                    out = d-a
                return out
        self.dbprint = dbprt = DbMemCee(self, 'grx,gry,cee,cod,des,sld,sla,val,prt')
        
        grx = 0
        #usato come finto raggruppamento per aggiungere nelle posizioni
        #strategiche le righe di differenza costi/ricavi e riepilogo utile
        #pre/post tasse
        #grx parte a 0
        #aumenta di 1 sulla riga aggiunta di differenza costi/ricavi
        #aumenta di 1 sulla riga aggiunta di risultato prima delle tasse
        
        gry = 0
        #usato come discriminante per la stampa del raggruppamento.
        #sulle righe aggiunte di cui sopra, devono essere stampato solo il piede
        #in maniera apposita, quindi testa e piede normale a qualsiasi livello 
        #non devono esaminare le righe con gry=1
        
        addif = addpt = True
        
        for row in range(b.RowsCount()):
            
            pbcur += 1
            pbar.SetValue(pbcur)
            
            r = b.GetRecordset()[row]
            
            tip = r[nctip]
            
            if not self.Filter(tip, r[ncttd]>=r[nctta]):
                continue
            
            cee = (r[nccee] or '').ljust(9)
            sez = cee[:1]
            voc = cee[:2]
            cap = cee[:6]
            det = cee[:8]
            sub = cee[:9]
            des = r[ncdsc]
            pid = r[ncpid]
            pdc = r[ncpdc]
            tpi = r[nctpi]
            tpa = r[nctpa]
            tpt = r[nctpt]
            
            csez = (sez or '').ljust(9)[0:1].strip()
            cvoc = (voc or '').ljust(9)[1:2].strip()
            ccap = (cap or '').ljust(9)[2:6].strip()
            cdet = (det or '').ljust(9)[6:8].strip()
            csub = (sub or '').ljust(9)[8:9].strip()
            
            rowd = r[ncttd] or 0
            rowa = r[nctta] or 0
            
            self.totd += rowd
            self.tota += rowa
            
            def TestZero(d,a):
                return (not parms['detnozero'] or not SameFloat(d,a))
            
            if tord == dbc.BILORD_BIL:
                
                def Decod(b, cosa):
                    return b.pdc.bilcee.GetDescrizOf(cosa, codcee=cee)
                
                if tip != ltip:
                    ltip = tip
                
                if addif and cee[0] == '4' and cee[1] > 'B':
                    #sono su sezione '4' e voce successiva alla 'B';
                    #aggiungo la riga di differenza tra costi e ricavi
                    #prima di continuare con il resto del bilancio
                    #(su cui sono già posizionato, oneri o altro)
                    #differenza = A-B
                    if 'v4A' in tt and 'v4B' in tt:
                        _trd, _tra = tt['v4A']
                        _tcd, _tca = tt['v4B']
                        _tr = _trd-_tra #tot.ricavi = dare-avere
                        _tc = _tca-_tcd #tot.costi  = avere-dare
                        if _tr>=_tc:
                            _dcra = _tr-_tc
                            _dcrd = 0
                        else:
                            _dcrd = _tr-_tc
                            _dcra = 0
                        _dcrv = '4B'.ljust(9)
                        _dcrx = "DIFFERENZA FRA VALORE E COSTO DELLA PRODUZIONE"
                        self.AppendRow(des=_dcrx, prd=_dcrd, pra=_dcra)
                        #aggiungo riga diff.costi/ricavi su tab. per la stampa
                        dbprt.CreateNewRow()
                        dbprt.grx = grx
                        dbprt.gry = 1
                        dbprt.cee = str(_dcrv).ljust(9)
                        dbprt.cod = None
                        dbprt.des = _dcrx
                        dbprt.sld = _dcrd
                        dbprt.sla = _dcra
                        dbprt.val = dbprt.sld-dbprt.sla
                        dbprt.prt = False #riga da non stampare insieme alle altre
                        addif = False
                        grx += 1
                
                if addpt and cee[0] == '4' and cee[1] >= 'E' and cee[6:8] > '21':
                    #sono su sezione '4' e dettaglio successivo al '21';
                    #aggiungo la riga di risultato d'esercizio prima delle tasse
                    #prima di continuare con il resto del bilancio
                    #(su cui sono già posizionato, tasse o altro)
                    #risultato pretasse = (A-B)+C+D+E, al quale sottraggo 
                    #l'ammontare delle tasse (sub-dett. '4E    24 ')
                    dav_a = tt.get('v4A', (0,0))
                    dav_b = tt.get('v4B', (0,0))
                    dav_c = tt.get('v4C', (0,0))
                    dav_d = tt.get('v4D', (0,0))
                    dav_e = tt.get('v4E', (0,0))
                    dav_x = tt.get('u4E    22 ', (0,0))
                    def gs(dav): #get saldo
                        return dav[1]-dav[0] #economico, avere-dare
                    davpt = gs(dav_a)+gs(dav_b)+gs(dav_c)+gs(dav_d)+gs(dav_e)-gs(dav_x)
                    if davpt >= 0:
                        _pta = davpt
                        _ptd = 0
                    else:
                        _ptd = -davpt
                        _pta = 0
                    _dcrv = '4E'.ljust(9)
                    _dcrx = "RISULTATO PRIMA DELLE IMPOSTE"
                    self.AppendRow(des=_dcrx, prd=_ptd, pra=_pta)
                    #aggiungo riga diff.costi/ricavi su tab. per la stampa
                    dbprt.CreateNewRow()
                    dbprt.grx = grx
                    dbprt.gry = 1
                    dbprt.cee = str(_dcrv).ljust(9)
                    dbprt.cod = None
                    dbprt.des = _dcrx
                    dbprt.sld = _ptd
                    dbprt.sla = _pta
                    dbprt.val = dbprt.sld-dbprt.sla
                    dbprt.prt = False #riga da non stampare insieme alle altre
                    addpt = False
                    grx += 1
                
                if dototsez and sez != lsez:
                    prd, pra = tt['s%s' % sez]
                    if TestZero(prd, pra):
                        self.AppendRow(sez=csez, des=Decod(b, 'sezione'),
                                       prd=prd, pra=pra)
                    lsez = sez
                
                if dototvoc and voc != lvoc and cvoc:
                    prd, pra = tt['v%s' % voc]
                    if TestZero(prd, pra):
                        self.AppendRow(voc=cvoc, des=Decod(b, 'voce'),
                                       prd=prd, pra=pra)
                    lvoc = voc
                
                if dototcap and cap != lcap and ccap:
                    prd, pra = tt['c%s' % cap]
                    if TestZero(prd, pra):
                        self.AppendRow(cap=ccap, des=Decod(b, 'capitolo'),
                                       prd=prd, pra=pra)
                    lcap = cap
                
                if dototdet and det != ldet and cdet:
                    prd, pra = tt['d%s' % det]
                    if TestZero(prd, pra):
                        self.AppendRow(det=cdet, des=Decod(b, 'dettaglio'),
                                       prd=prd, pra=pra)
                    ldet = det
                
                if dototsub and sub != lsub and csub:
                    prd, pra = tt['u%s' % sub]
                    if TestZero(prd, pra):
                        self.AppendRow(sub=csub, des=Decod(b, 'subdett'),
                                       prd=prd, pra=pra)
                    lsub = sub
                
                if dototpdc and\
                   ((not r[nctpt] in "CF" or parms['detcf']) and\
                    TestZero(rowd, rowa)):
                    self.AppendRow(cee=cee, 
                                   pid=pid, pdc=pdc, tpi=tpi, tpa=tpa, des=des,\
                                   prd=rowd, pra=rowa)
                
                lcee = cee
                
            elif (not r[nctpt] in "CF" or parms['detcf']) and TestZero(rowd, rowa):
                self.AppendRow(cee=cee, sez=csez, voc=cvoc, cap=ccap, det=cdet, sub=csub,
                               pid=pid, pdc=pdc, tpi=tpi, tpa=tpa, des=des,
                               prd=rowd, pra=rowa)
            
            dbprt.CreateNewRow()
            dbprt.grx = grx
            dbprt.gry = 0
            dbprt.cee = r[nccee]
            dbprt.cod = r[ncpdc]
            dbprt.des = r[ncdsc]
            dbprt.sld = r[ncttd] or 0
            dbprt.sla = r[nctta] or 0
            dbprt.val = dbprt.sld-dbprt.sla
            dbprt.prt = bool(not r[nctpt] in "CF" or parms['detcf'] and TestZero(rowd, rowa))
        
        if not addpt:
            #sono a fine bilancio;
            #aggiungo la riga di risultato d'esercizio dopo le tasse
            #prima di continuare con il resto del bilancio
            #(su cui sono già posizionato, tasse o altro)
            #risultato pretasse = (A-B)+C+D+E
            dav_a = tt.get('v4A', (0,0))
            dav_b = tt.get('v4B', (0,0))
            dav_c = tt.get('v4C', (0,0))
            dav_d = tt.get('v4D', (0,0))
            dav_e = tt.get('v4E', (0,0))
            def gs(dav): #get saldo
                return dav[1]-dav[0] #economico, avere-dare
            davpt = gs(dav_a)+gs(dav_b)+gs(dav_c)+gs(dav_d)+gs(dav_e)
            if davpt >= 0:
                _pta = davpt
                _ptd = 0
            else:
                _ptd = -davpt
                _pta = 0
            _dcrv = '4E'.ljust(9)
            _dcrx = "UTILE/PERDITA DELL'ESERCIZIO"
            self.AppendRow(des=_dcrx, prd=_ptd, pra=_pta)
            #aggiungo riga diff.costi/ricavi su tab. per la stampa
            dbprt.CreateNewRow()
            dbprt.grx = grx
            dbprt.gry = 1
            dbprt.cee = str(_dcrv).ljust(9)
            dbprt.cod = None
            dbprt.des = _dcrx
            dbprt.sld = _ptd
            dbprt.sla = _pta
            dbprt.val = dbprt.sld-dbprt.sla
            dbprt.prt = False #riga da non stampare insieme alle altre
            addpt = False
            grx += 1
        
        self.ChangeData(self.rsbil)
    
    def Filter(self, *args):
        return True
    
    def AppendRow(self, 
                  cee=None, sez=None, voc=None, cap=None, det=None, sub=None,
                  pid=None, pdc=None, tpi=None, tpa=None, des=None,\
                  prd=None, pra=None):
        
        if prd is None or pra is None:
            sld = sla = sal = None
        else:
            sld, sla = prd-pra, 0
            if sld < 0:
                sld, sla = sla, -sld
            sal = sld-sla
        
        if prd == 0: prd = None
        if pra == 0: pra = None
        if sld == 0: sld = None
        if sla == 0: sla = None
        
        self.rsbil.append((None, #GRIDCOL_TIPBIL
                           None, #GRIDCOL_CODMAS
                           None, #GRIDCOL_CODCON
                           tpi,  #GRIDCOL_IDTIP
                           tpa,  #GRIDCOL_CODTIP
                           pid,  #GRIDCOL_IDPDC
                           pdc,  #GRIDCOL_CODPDC
                           des,  #GRIDCOL_DESC
                           prd,  #GRIDCOL_PROGRD
                           pra,  #GRIDCOL_PROGRA
                           sld,  #GRIDCOL_SALDOD
                           sla,  #GRIDCOL_SALDOA
                           cee,  #GRIDCOL_CEECOD
                           sez,  #GRIDCOL_CEESEZ
                           voc,  #GRIDCOL_CEEVOC
                           cap,  #GRIDCOL_CEECAP
                           det,  #GRIDCOL_CEEDET
                           sub,  #GRIDCOL_CEESUB
                           sal)) #GRIDCOL_CEEVAL
        return self.rsbil[-1]


# ------------------------------------------------------------------------------


class BilCeePanel(_BilPanel):
    
    def __init__(self, *args, **kwargs):
        
        wdr.BilancioTipoLivelloFunc = wdr.BilancioTipoLivelloCeeFunc
        _BilPanel.__init__(self, *args, **kwargs)
        self.report = 'Bilancio CEE'
        self.rptflat = 'Bilancio CEE (flat)'
        self.globaltot = True
        
        #inizializzazione valori controlli radio
        for name, init in (('tipord', 'B'),):
            self.FindWindowByName(name).SetValue(init)

    def GetTabBilancio(self):
        return dbc.BilancioCee()
    
    def InitPanelBilancio(self):
        p = wx.Panel(self, wdr.ID_PANGRIDS, size=(-1, 360))
        self.gridbil = BilCeeGrid(self.dbbil, p)
    
    def UpdateBil(self):
        _BilPanel.UpdateBil(self)
        self.gridbil.colors = False
    
    def UpdateGrid(self):
        _BilPanel.UpdateGrid(self)
        self.UpdateQuadratura(self.gridbil.totd, self.gridbil.tota, salep=True, quadonly=True)

    def PrintBil(self):
        tord = self.dbbil.GetVar('ordin')
        if tord == 2:
            stbil = self.gridbil.dbprint
            stbil._info.dbcee = self.dbbil._info.dbcee # x decodifiche
            msg = "Stampo il dettaglio dei sottoconti?"
            s = wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT
            stbil._info.stadet = (aw.awu.MsgDialog(self, msg, style=s) == wx.ID_YES)
            rptname = self.report
            def GetPeriodo(*x):
                return self.GetPeriodo()
            stbil.GetPeriodo = GetPeriodo
        else:
            stbil = self.dbbil
            rptname = self.rptflat
        rpt.Report(self, stbil, rptname)


# ------------------------------------------------------------------------------


class BilCeeFrame(aw.Frame):
    """
    Frame Bilancio Cee.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILCEE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilCeePanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class BilCeeDialog(aw.Dialog):
    """
    Dialog Bilancio Cee.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE_BILCEE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(BilCeePanel(self, -1))
        self.CenterOnScreen()
