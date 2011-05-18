#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/stat/valcosacq.py
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

import magazz.stat.valpreapp as preapp
bt = preapp.bt
wdr = preapp.wdr
dbms = preapp.dbms
rpt = preapp.rpt


COSTI_FRAME_TITLE = "Valutazione costi di acquisto"


class MovimentiCostiGrid(preapp.MovimentiPrezziGrid):
    
    def DefColumns(self):
        
        mov = self.dbmov
        tpm = mov.tipmov
        doc = mov.doc
        tpd = doc.tipdoc
        pdc = doc.pdc
        age = doc.agente
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        _PRZ = bt.GetMagPreMaskInfo()
        _QTA = bt.GetMagQtaMaskInfo()
        _SCO = bt.GetMagScoMaskInfo()
        _IMP = bt.GetValIntMaskInfo()
        wp = wdr.PREZZOWIDTH
        wi = wp+20
        
        cols = []
        self.edcols = []
        def c(col, ed=False):
            n = len(cols)
            cols.append(col)
            if ed:
                self.edcols.append(n)
            return n
        def C(col):
            return c(col, ed=True)
        
        self.COL_DATDOC = c(( 80, (cn(doc, "datdoc"),  "Data doc.",  _DAT, True )))
        self.COL_TPDCOD = c(( 35, (cn(tpd, "codice"),  "Cod.",       _STR, True )))
        self.COL_TPDDES = c((120, (cn(tpd, "descriz"), "Documento",  _STR, True )))
        self.COL_TPMCOD = c(( 35, (cn(tpm, "codice"),  "Mov.",       _STR, True )))
        self.COL_NUMDOC = c(( 50, (cn(doc, "numdoc"),  "Num.",       _STR, True )))
        self.COL_PDCCOD = c(( 50, (cn(pdc, "codice"),  "Cod.",       _STR, True )))
        self.COL_PDCDES = c((230, (cn(pdc, "descriz"), "Fornitore",  _STR, True )))
        self.COL_PREZUN = c(( wp, (cn(mov, "prezzo"),  "Prezzo Un.", _PRZ, True )))
        self.COL_PREZSC = c(( wp, (cn(mov, "presco"),  "Prezzo Sc.", _PRZ, True )))
        self.COL_TOTQTA = c(( wp, (cn(mov, "qta"),     "Qta",        _QTA, True )))
        self.COL_SCONT1 = c(( 50, (cn(mov, "sconto1"), "Sc.%1",      _SCO, True )))
        self.COL_SCONT2 = c(( 50, (cn(mov, "sconto2"), "Sc.%2",      _SCO, True )))
        self.COL_SCONT3 = c(( 50, (cn(mov, "sconto3"), "Sc.%3",      _SCO, True )))
        self.COL_IMPORT = c(( wi, (cn(mov, "importo"), "Importo",    _IMP, True )))
        c((  1, (cn(tpd, "id"),   "#tpd", _STR, True )))
        c((  1, (cn(tpm, "id"),   "#tpm", _STR, True )))
        c((  1, (cn(pdc, "id"),   "#pdc", _STR, True )))
        
        return cols


# ------------------------------------------------------------------------------


class MovimentiCostiPanel(preapp.MovimentiPrezziPanel):
    """
    Panel Movimenti che determinano le valutazioni del costo.
    """
    
    statftcol = 'statftfor'
    GridClass = MovimentiCostiGrid


# ------------------------------------------------------------------------------


COSTI_FRAME_TITLE_DETT = 'Prezzi applicati'

class MovimentiCostiFrame(preapp.MovimentiPrezziFrame):
    """
    Frame Movimenti che determinano le valutazioni del costo.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = COSTI_FRAME_TITLE_DETT
        aw.Frame.__init__(self, *args, **kwargs)
        self.panel = MovimentiCostiPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class MovimentiCostiDialog(preapp.MovimentiPrezziDialog):
    """
    Dialog Movimenti che determinano le valutazioni del costo.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = COSTI_FRAME_TITLE_DETT
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = MovimentiCostiPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ValutaCostiGrid(preapp.ValutaPrezziGrid):
    
    def DefColumns(self):
        
        def cn(db, col):
            return db._GetFieldIndex(col, inline=True)
        
        vpv = self.dbvpv
        pro = vpv.prod
        
        _STR = gl.GRID_VALUE_STRING
        _PRZ = bt.GetMagPreMaskInfo()
        wp = wdr.PREZZOWIDTH
        
        cols = []
        self.edcols = []
        def c(col, ed=False):
            n = len(cols)
            cols.append(col)
            if ed:
                self.edcols.append(n)
            return n
        def C(col):
            return c(col, ed=True)
        
        self.COL_CODICE =  C(( 80, (cn(vpv, "prod_codice"),        "Codice",        _STR, True )))
        self.COL_DESCRIZ = C((170, (cn(vpv, "prod_descriz"),       "Prodotto",      _STR, True )))
        
        if bt.MAGFORLIS:
            self.COL_CODFOR = c(( 90, (cn(vpv, "prod_codfor"),     "Cod.Fornit.",   _STR, True )))
        
        self.COL_COSTO =   C(( wp, (cn(vpv, "prod_costo"),         "Costo scheda",  _PRZ, False)))
        
        #minimo, massimo, media su prezzo unitario
        self.COL_PREAPPUN_MIN =  C(( wp, (cn(vpv, "min_prezzoun"), "Min.Un.",       _PRZ, False)))
        self.COL_PREAPPUN_MAX =  C(( wp, (cn(vpv, "max_prezzoun"), "Max.Un.",       _PRZ, False)))
        self.COL_PREAPPUN_AVG =  C(( wp, (cn(vpv, "avg_prezzoun"), "Media.Un.",     _PRZ, False)))
        
        #minimo, massimo, media su prezzo scontato
        self.COL_PREAPPSC_MIN =  C(( wp, (cn(vpv, "min_prezzosc"), "Min.Sc.",       _PRZ, False)))
        self.COL_PREAPPSC_MAX =  C(( wp, (cn(vpv, "max_prezzosc"), "Max.Sc.",       _PRZ, False)))
        self.COL_PREAPPSC_AVG =  C(( wp, (cn(vpv, "avg_prezzosc"), "Media.Sc.",     _PRZ, False)))
        
        c((  1, (cn(vpv, "prod_id"),   "#pro", _STR, True )))
        
        return cols


# ------------------------------------------------------------------------------


class ValutaCostiPanel(preapp.ValutaPrezziPanel):
    """
    Panel Valutazione costi di acquisto applicati.
    """
    
    ValutaCostiPrezziTable = dbms.ValutaCostiAcquisto
    WdrFiller = wdr.ValutaCostiAcquistoFunc
    GridClass = ValutaCostiGrid
    
    def DefALS(self):
        ALS = self.AddLimitiFiltersSequence
        vpv = self.dbvpv
        pro = vpv.prod
        doc = vpv.doc
        ALS(pro, 'prod',    'codice')
        ALS(pro, 'prod',    'descriz')
        ALS(pro, 'status',  'id_status')
        ALS(pro, 'catart',  'id_catart')
        ALS(pro, 'gruart',  'id_gruart')
        ALS(pro, 'tipart',  'id_tipart')
        ALS(pro, 'fornit',  'id_fornit')
        ALS(doc, 'doc',     'datreg')
        ALS(doc, 'pdc',     'id_anag')
    
    def VediPrezzi(self, id_prod):
        vpv = self.dbvpv
        filters = []
        for tab in (vpv.doc, vpv.doc.pdc):
            if tab._info.filters:
                filters += ([]+tab._info.filters)
        dlg = MovimentiCostiDialog(self)
        dlg.SetParam(id_prod, filters)
        dlg.ShowModal()
        dlg.Destroy()
    
    def PrintData(self):
        rpt.Report(self, self.dbvpv, 'Valutazione Costi Acquisto')


# ------------------------------------------------------------------------------


class ValutaCostiFrame(aw.Frame):
    """
    Frame Valutazione costi di acquisto presenti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = COSTI_FRAME_TITLE
        aw.Frame.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ValutaCostiPanel(self, -1))
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


class ValutaCostiDialog(aw.Dialog):
    """
    Dialog Valutazione costi di acquisto presenti.
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = COSTI_FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.AddSizedPanel(ValutaCostiPanel(self, -1))
        self.CenterOnScreen()
