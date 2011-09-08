#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         anag/lib.py
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
import wx.grid as gridlib

import awc.controls.dbgrid as dbg
import awc.controls.dbgrideditors as gred
from awc.controls.linktable import LinkTable, AndApp, OrApp,\
     INITFOCUS_CODICE, INITFOCUS_DESCRIZ

import anag
import anag.util as autil

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb
import anag.dbtables as dba

from awc.util import TimedPopupMessageFrame


class LinkTableHideSearchMixin(object):
    
    filter_to_hide = None
    
    def SetFilterToHide(self, f):
        self.filter_to_hide = f
        self.SetDisplayHidden()
    
    display_hidden = False
    def SetDisplayHidden(self, dh=None, popup=False):
        if dh is not None:
            self.display_hidden = dh
        if self.display_hidden:
            self.basefilter = None
            msg = "Visualizza anche elementi nascosti"
            color = 'red'
        else:
            self.basefilter = self.filter_to_hide
            msg = "Gli elementi nascosti non saranno visualizzati"
            color = 'blue'
        if popup:
            f = self.FindFocus()
            self.HideFilterLinksTitle()
            TimedPopupMessageFrame(self, message=msg, seconds=1, text_color=color)
            if f:
                wx.CallAfter(lambda: f.SetFocus())
                self.HideFilterLinksTitle()
    
    def ToggleDisplayHidden(self):
        old = self.display_hidden
        self.SetDisplayHidden(not self.display_hidden, popup=True)
        return old
    
    def OnChar(self, event):
        if not self._ctrcod.IsEditable() or not self.IsShown(): return
        if event.GetKeyCode() == wx.WXK_F2:
            self.ToggleDisplayHidden()
            event.Skip()
            return
        LinkTable.OnChar(self, event)
    
    def GetExtraToolTip(self):
        return "\n(F2) Visualizza/nasconde elementi nascosti"


# ------------------------------------------------------------------------------


class LinkTableProd(LinkTable, LinkTableHideSearchMixin):
    """
    LinkTable su prodotti; ricerca il codice non solo come codice interno,
    ma anche (se non trovato) come codice a barre e codice fornitore.
    """
    ppmag = None
    barcode_readed = False
    tabsearch_oncode = True
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.digitsearch_oncode = Env.Azienda.BaseTab.MAGDIGSEARCH
        self.tabsearch_oncode = not self.digitsearch_ondescriz
        if bt.MAGEXCSEARCH:
            self.SetCodExclusive(True)
        LinkTableHideSearchMixin.__init__(self)
        self.SetFilterToHide("status.hidesearch IS NULL or status.hidesearch<>1")
        if name:
            self.SetName(name)
        self.SetCodeWidth(80)
        w = 560
        if bt.MAGVISPRE:
            w += 110
        if bt.MAGVISCOS:
            w += 110
        if bt.MAGVISGIA:
            w += 120
        self.SetMinWidth(w)
        from anag.prod import ProdDialog
        self.cardclass = ProdDialog
        aut = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGAUTOM, 'aut', writable=False)
        self.db_name = Env.Azienda.BaseTab.TABNAME_PROD
        self.db_alias = 'prod'
        if aut.Retrieve("codice LIKE 'magfil%'"):
            fl = []
            if aut.Locate(lambda a: a.codice == 'magfiltip' and aut.aut_id):
                from anag.tipart import TipArtDialog
                fl.append(("Tipo articolo",
                          Env.Azienda.BaseTab.TABNAME_TIPART,
                          "id_tipart",
                          TipArtDialog,
                          None,
                          None))
            if aut.Locate(lambda a: a.codice == 'magfilcat' and aut.aut_id):
                from anag.catart import CatArtDialog
                fl.append(("Categoria",
                           Env.Azienda.BaseTab.TABNAME_CATART,
                           "id_catart",
                           CatArtDialog,
                           None,
                           None))
            if aut.Locate(lambda a: a.codice == 'magfilfor' and aut.aut_id):
                from anag.fornit import FornitDialog
                fl.append(("Fornitore",
                           Env.Azienda.BaseTab.TABNAME_PDC,
                           "id_fornit",
                           FornitDialog,
                           "id_tipo=%d" % dba.GetPdcTipForCodice('F'),
                           None))
            if aut.Locate(lambda a: a.codice == 'magfilmar' and aut.aut_id):
                from anag.marart import MarArtDialog
                fl.append(("Marca",
                           Env.Azienda.BaseTab.TABNAME_MARART,
                           "id_marart",
                           MarArtDialog,
                           None,
                           None))
            if fl:
                self.SetFilterLinks(fl)
    
    def GetExtraToolTip(self):
        return LinkTableHideSearchMixin.GetExtraToolTip(self)
    
    def OnChar(self, event):
        LinkTableHideSearchMixin.OnChar(self, event)
    
    def GetSql(self, count=False):
        if count:
            cmd = 'SELECT COUNT(*)'
        else:
            cmd = self.GetSqlSelect()
        return cmd+self.GetSqlFrom()
    
    def GetSqlSelect(self):
        
        out = """SELECT prod.id, 
                        prod.codice, 
                        prod.descriz, 
                        prod.codfor AS codfor,
                        prod.barcode AS barcode, 
                        prod.costo,
                        prod.prezzo"""
                    
        if bt.MAGVISGIA:
            tabprogr = bt.TABNAME_PRODPRO
            if self.ppmag:
                testmag = ' AND pp.id_magazz=%d' % self.ppmag
            else:
                testmag = ''
            out += ',\n'
            out += ("""(SELECT SUM(IF(pp.ini IS NULL,0,pp.ini)+IF(pp.car IS NULL,0,pp.car)-IF(pp.sca IS NULL,0,pp.sca)) 
                          FROM %(tabprogr)s pp
                         WHERE pp.id_prod=prod.id %(testmag)s) 'giac', 
                        NULL AS magid""" % locals()).replace('\n', ' ')        
        return out
    
    def GetSqlFrom(self):
        
        out = """
        FROM %s prod
        LEFT JOIN %s status ON prod.id_status=status.id"""\
            % (self.db_name, bt.TABNAME_STATART)
        
#        if bt.MAGVISGIA:
#            out += """
#        LEFT JOIN %s pp ON pp.id_prod=prod.id"""\
#            % Env.Azienda.BaseTab.TABNAME_PRODPRO
        
        return out
    
#    def GetSqlGroup(self):
#        if bt.MAGVISGIA:
#            out = "GROUP BY prod.id"
#        else:
#            out = ""
#        return out
#    
#    def GetSqlHaving(self):
#        cmd = ''
#        par = []
#        if bt.MAGVISGIA:
#            if self.ppmag:
#                cmd += r" AND pp.id_magazz=%s"
#                par.append(self.ppmag)
#            if cmd:
#                cmd = " HAVING "+cmd[5:]
#        return cmd, par
#    
    def GetDataGridStructure(self):
        
        _STR = gridlib.GRID_VALUE_STRING
        _QTA = bt.GetMagQtaMaskInfo()
        _PRE = bt.GetMagPreMaskInfo()
        
        out = [( -1, ( 1, "Cod.",        _STR, False)),
               (200, ( 2, "Descrizione", _STR, False)),]
        
        if bt.MAGVISCPF:
            out.append((110, ( 3, "Cod.Forn.", _STR, False)))
        
        if bt.MAGVISBCD:
            out.append((110, ( 4, "Barcode",   _STR, False)))
        
        if bt.MAGVISCOS:
            out.append((110, ( 5, "Costo",     _PRE, False)))
        
        if bt.MAGVISPRE:
            out.append((110, ( 6, "Prezzo",    _PRE, False)))
        
        if bt.MAGVISGIA:
            out.append((120, ( 7, "Giacenza",  _QTA, False)))
        
        return out
    
    def GetDataGridColumns(self):
        cols = self.GetDataGridStructure()
        return [c[1] for c in cols]
    
    def AdjustColumnsSize(self, grid):
        cols = self.GetDataGridStructure()
        colsize = [c[0] for c in cols]
        for n, w in enumerate(colsize):
            if w>=0:
                grid.SetColumnDefaultSize(n, w)
                #grid.SetColSize(n, w)
    
    def GetSqlTextSearch(self, obj, forceAll, exact):
        cmd, par = LinkTable.GetSqlTextSearch(self, obj, forceAll, exact)
        fltv = obj.GetValue()
        if obj == self._ctrcod and len(fltv)>=3:
            if cmd:
                cmd += " OR "
            #cmd += "%s.codfor=%%s" % self.db_alias
            #par.append(fltv.rstrip())
            cmd += "%s.codfor LIKE %%s" % self.db_alias
            par.append('%s%%' % fltv.rstrip())
            if cmd:
                cmd += " OR "
            #cmd += "%s.barcode=%%s" % self.db_alias
            #par.append(fltv.rstrip())
            cmd += "%s.barcode LIKE %%s" % self.db_alias
            par.append('%s%%' % fltv.rstrip())
        return cmd, par
    
    def SetValue(self, id, txt=None, **kw):
        LinkTable.SetValue(self, id, txt, **kw)
        if txt and self._rs:
            self.barcode_readed = (txt == str(self._rs[4]).upper())
        else:
            self.barcode_readed = False


# ------------------------------------------------------------------------------


class LinkTableTipList(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_TIPLIST
        self.db_alias = 'tiplist'
        from anag.tiplist import TipListDialog
        self.cardclass = TipListDialog


# ------------------------------------------------------------------------------


class LinkTableTipArt(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_TIPART
        self.db_alias = 'tipart'
        from anag.tipart import TipArtDialog
        self.cardclass = TipArtDialog


# ------------------------------------------------------------------------------


class LinkTableCatArt(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_CATART
        self.db_alias = 'catart'
        from anag.catart import CatArtDialog
        self.cardclass = CatArtDialog


# ------------------------------------------------------------------------------


class LinkTableCatCli(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_CATCLI
        self.db_alias = 'catcli'
        from anag.catcli import CatCliDialog
        self.cardclass = CatCliDialog


# ------------------------------------------------------------------------------


class LinkTableCatFor(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_CATFOR
        self.db_alias = 'catfor'
        from anag.catfor import CatForDialog
        self.cardclass = CatForDialog


# ------------------------------------------------------------------------------


class LinkTableGruArt(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_GRUART
        self.db_alias = 'gruart'
        from anag.gruart import GruArtDialog
        self.cardclass = GruArtDialog


# ------------------------------------------------------------------------------


class LinkTableMarArt(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_MARART
        self.db_alias = 'marart'
        from anag.marart import MarArtDialog
        self.cardclass = MarArtDialog


# ------------------------------------------------------------------------------


class LinkTableStatArt(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_STATART
        self.db_alias = 'statart'
        from anag.statart import StatArtDialog
        self.cardclass = StatArtDialog


# ------------------------------------------------------------------------------


class LinkTableStatCli(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_STATCLI
        self.db_alias = 'statcli'
        from anag.statcli import StatCliDialog
        self.cardclass = StatCliDialog


# ------------------------------------------------------------------------------


class LinkTableStatFor(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_STATFOR
        self.db_alias = 'statfor'
        from anag.statfor import StatForDialog
        self.cardclass = StatForDialog


# ------------------------------------------------------------------------------


class LinkTableStatPdc(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.db_name = Env.Azienda.BaseTab.TABNAME_STATPDC
        self.db_alias = 'statpdc'
        from anag.statpdc import StatPdcDialog
        self.cardclass = StatPdcDialog


# ------------------------------------------------------------------------------


class LinkTableGruPrez(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        from anag.gruprez import GruPrezDialog
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_GRUPREZ, name, GruPrezDialog)


# ------------------------------------------------------------------------------


class DataLinkGruPrezEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableGruPrez


# ------------------------------------------------------------------------------


class LinkTabGruPrezAttr(dbg.LinkTabAttr):
    editorclass = DataLinkGruPrezEditor


# ------------------------------------------------------------------------------


class DataLinkProdCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableProd


# ------------------------------------------------------------------------------


class LinkTabProdAttr(dbg.LinkTabAttr):
    editorclass = DataLinkProdCellEditor


# ------------------------------------------------------------------------------


class _LinkTablePdcMixin(LinkTable):
    
    _codewidth = 50
    
    tipanacods = ''
    filter_by_descriz = True
    
    def __init__(self, parent, id, name=None, **kwargs):
        fromgrid = kwargs.pop('fromgrid', False)
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetFilterLinks(("Tipo di sottoconto",
                             Env.Azienda.BaseTab.TABNAME_PDCTIP,
                             "id_tipo",
                             None,
                             None,
                             None))
        self.SetDynCard(self.GetDialogClass)
        self.SetInitFocusCD(fromgrid)
        self.db_name = self.db_alias = Env.Azienda.BaseTab.TABNAME_PDC
        self.dbtip = dba.PdcTip()
        if self.tipanacods:
            self.SetPdcTipCods(self.tipanacods)
    
    def SetInitFocusCD(self, fromgrid):
        if fromgrid:
            f = bt.OPTLNKGRDPDC
            if f is None:
                f = INITFOCUS_CODICE
        else:
            f = bt.OPTLNKGRDPDC
            if f is None:
                f = INITFOCUS_DESCRIZ
        self.SetInitFocus(f)
    
    def SetPdcTipCods(self, tipanacods):
        out = False
        dbtip = self.dbtip
        if tipanacods:
            filt = "codice IN (%s)" \
                 % ','.join(map(lambda x: "'%s'" % x, list(tipanacods)))
        else:
            filt = '1'
        if dbtip.Retrieve(filt) and dbtip.RowsCount()>0:
            self.SetFilterValue(dbtip.id)
            self.SetFilterFilter(filt)
            self.tipanacods = tipanacods
            out = True
        return out
    
    def GetDialogClass(self):
        return autil.GetPdcDialogClass(self.filtervalues[0][1])
    
    def GetSql(self, count=False):
        bt = Env.Azienda.BaseTab
        if count:
            fields = 'COUNT(*)'
        else:
            fields = """pdc.id         'id',
                        pdc.codice     'codice',
                        pdc.descriz    'descriz',
                        tipana.id      'id_tipo',
                        tipana.tipo    'tipo',
                        bilmas.id      'bilmas_id',
                        bilmas.codice  'bilmas_codice',
                        bilmas.descriz 'bilmas_descriz',
                        bilcon.id      'bilcon_id',
                        bilcon.codice  'bilcon_codice',
                        bilcon.descriz 'bilcon_descriz'"""
        pdc = bt.TABNAME_PDC
        tipana = bt.TABNAME_PDCTIP
        bilmas = bt.TABNAME_BILMAS
        bilcon = bt.TABNAME_BILCON
        cmd = """
        SELECT %(fields)s
          FROM %(pdc)s    pdc
          JOIN %(tipana)s tipana ON tipana.id=pdc.id_tipo
          JOIN %(bilmas)s bilmas ON pdc.id_bilmas=bilmas.id
          JOIN %(bilcon)s bilcon ON pdc.id_bilcon=bilcon.id
          """ % locals()
        return cmd
    
    def GetValueSearchSqlJoins(self):
        tipanaid = self.filtervalues[0][1]
        tipo = autil.GetPdcTipo(tipanaid)
        bt = Env.Azienda.BaseTab
        j = ''
        if tipo == 'C':
            j = 'JOIN %s clienti ON pdc.id=clienti.id' % bt.TABNAME_CLIENTI
        elif tipo == 'F':
            j = 'JOIN %s fornit ON pdc.id=fornit.id' % bt.TABNAME_FORNIT
        if tipo == 'A':
            j = 'JOIN %s cassa ON pdc.id=cassa.id' % bt.TABNAME_CASSE
        if tipo == 'B':
            j = 'JOIN %s banche ON pdc.id=banche.id' % bt.TABNAME_BANCHE
        if tipo == 'D':
            j = 'JOIN %s effetti ON pdc.id=effetti.id' % bt.TABNAME_EFFETTI
        return j


# ------------------------------------------------------------------------------


class LinkTablePdc(_LinkTablePdcMixin, LinkTableHideSearchMixin):
    """
    LinkTable su pdc x selezionare un sottoconto.
    """
    
    def __init__(self, *args, **kwargs):
        _LinkTablePdcMixin.__init__(self, *args, **kwargs)
        LinkTableHideSearchMixin.__init__(self)
        self.SetFilterToHide("(statpdc.hidesearch IS NULL or statpdc.hidesearch<>1)")
        self.SetMinWidth(300)
    
    def GetExtraToolTip(self):
        return LinkTableHideSearchMixin.GetExtraToolTip(self)
    
    def OnChar(self, event):
        LinkTableHideSearchMixin.OnChar(self, event)
    
    def GetSql(self, count=False):
        bt = Env.Azienda.BaseTab
        if count:
            fields = 'COUNT(*)'
        else:
            fields = """pdc.id      'id',
                        pdc.codice  'codice',
                        pdc.descriz 'descriz'
            """
        pdc = bt.TABNAME_PDC
        statpdc = bt.TABNAME_STATPDC
        cmd = """
        SELECT %(fields)s
          FROM      %(pdc)s    pdc
          LEFT JOIN %(statpdc)s statpdc ON statpdc.id=pdc.id_statpdc
          """ % locals()
        return cmd


# ------------------------------------------------------------------------------


class _LinkTablePdcCostiRicavi(_LinkTablePdcMixin):
    """
    LinkTable su pdc x selezionare un sottoconto.
    """
    tipo_cr = None
    def __init__(self, parent, id, name):
        assert self.tipo_cr is not None
        _LinkTablePdcMixin.__init__(self, parent, id)
        self.SetName(name)
        auto = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGAUTOM, 'auto', writable=False)
        if auto.Retrieve('auto.codice=%s', 
                         'pdctip_%s' % self.tipo_cr) and auto.OneRow():
            self.SetFilterValue(auto.aut_id)
            self.SetFilterFilter('1')


# ------------------------------------------------------------------------------


class LinkTablePdcCosti(_LinkTablePdcCostiRicavi):
    tipo_cr = 'costi'


# ------------------------------------------------------------------------------


class LinkTablePdcRicavi(_LinkTablePdcCostiRicavi):
    tipo_cr = 'ricavi'


# ------------------------------------------------------------------------------


class LinkTableCassa(_LinkTablePdcMixin):
    tipanacods = "A"


# ------------------------------------------------------------------------------


class LinkTableBanca(_LinkTablePdcMixin):
    tipanacods = "B"


# ------------------------------------------------------------------------------


class LinkTableCassaBanca(_LinkTablePdcMixin):
    tipanacods = "AB"


# ------------------------------------------------------------------------------


class LinkTableCliFor(_LinkTablePdcMixin, LinkTableHideSearchMixin):
    """
    LinkTable su pdc x selezionare clienti o fornitori.
    """
    
    tipanacods = "CF"
    
    def __init__(self, *args, **kwargs):
        _LinkTablePdcMixin.__init__(self, *args, **kwargs)
        LinkTableHideSearchMixin.__init__(self)
        self.SetFilterToHide("(statcli.hidesearch IS NULL or statcli.hidesearch<>1) AND (statfor.hidesearch IS NULL or statfor.hidesearch<>1)")
        self.SetMinWidth(900)
        self.SetGridMaxDescWidth(300)
    
    def SetInitFocusCD(self, fromgrid):
        if fromgrid:
            f = bt.OPTLNKGRDCLI
            if f is None:
                f = INITFOCUS_DESCRIZ
        else:
            f = bt.OPTLNKGRDCLI
            if f is None:
                f = INITFOCUS_DESCRIZ
        self.SetInitFocus(f)
    
    def GetExtraToolTip(self):
        return LinkTableHideSearchMixin.GetExtraToolTip(self)
    
    def OnChar(self, event):
        LinkTableHideSearchMixin.OnChar(self, event)
    
    def GetSql(self, count=False):
        bt = Env.Azienda.BaseTab
        if count:
            fields = 'COUNT(*)'
        else:
            fields = """pdc.id      'id',
                        pdc.codice  'codice',
                        pdc.descriz 'descriz',
                        tipana.id   'id_tipo',
                        tipana.tipo 'tipo',
                        IF(tipana.tipo='C', anacli.indirizzo, anafor.indirizzo) 'indirizzo',
                        IF(tipana.tipo='C', anacli.cap,       anafor.cap)       'cap',
                        IF(tipana.tipo='C', anacli.citta,     anafor.citta)     'citta',
                        IF(tipana.tipo='C', anacli.prov,      anafor.prov)      'prov',
                        IF(tipana.tipo='C', anacli.piva,      anafor.piva)      'piva',
                        IF(tipana.tipo='C', anacli.codfisc,   anafor.codfisc)   'codfisc'
            """
        pdc = bt.TABNAME_PDC
        tipana = bt.TABNAME_PDCTIP
        clienti = bt.TABNAME_CLIENTI
        statcli = bt.TABNAME_STATCLI
        fornit = bt.TABNAME_FORNIT
        statfor = bt.TABNAME_STATFOR
        cmd = """
        SELECT %(fields)s
          FROM      %(pdc)s    pdc
               JOIN %(tipana)s  tipana  ON tipana.id=pdc.id_tipo
          LEFT JOIN %(clienti)s anacli  ON anacli.id=pdc.id
          LEFT JOIN %(statcli)s statcli ON anacli.id_status=statcli.id
          LEFT JOIN %(fornit)s  anafor  ON anafor.id=pdc.id
          LEFT JOIN %(statfor)s statfor ON anafor.id_status=statfor.id
          """ % locals()
        return cmd
    
    def SetDataGrid(self, grid, rs):
        _STR = gridlib.GRID_VALUE_STRING
        cols = (( -1, ( 1, "Cod.",        _STR, False)),
                ( -1, ( 2, "Descrizione", _STR, False)),
                (200, ( 5, "Indirizzo",   _STR, False)),
                ( 50, ( 6, "CAP",         _STR, False)),
                (160, ( 7, "Città",       _STR, False)),
                ( 30, ( 8, "Pr.",         _STR, False)),
                ( 90, ( 9, "P.IVA",       _STR, False)),
                (130, (10, "Cod.Fiscale", _STR, False)),
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        for n, w in enumerate(colsize):
            if w>=0:
                grid.SetColumnDefaultSize(n, w)
        grid.SetAnchorColumns(5, 1)
        grid.SetData(rs, colmap)

    def GetSqlTextSearch(self, obj, forceAll, exact):
        cmd, par = LinkTable.GetSqlTextSearch(self, obj, forceAll, exact)
        fltv = obj.GetValue()
        if obj == self._ctrdes:
            val = self._ctrdes.GetValue()
            if len(val) == 11 and val.isdigit():
                cmd = OrApp(cmd, "(anacli.piva=%s OR anacli.codfisc=%s)")
                cmd = OrApp(cmd, "(anafor.piva=%s OR anafor.codfisc=%s)")
                par.append(fltv)
                par.append(fltv)
                par.append(fltv)
                par.append(fltv)
            elif len(val) == 16:
                cmd = OrApp(cmd, "(anacli.codfisc=%s OR anafor.codfisc=%s)")
                par.append(fltv)
                par.append(fltv)
        return cmd, par
    
    def HelpChoice(self, obj, *args, **kwargs):
        if obj is self._ctrdes:
            val = obj.GetValue()
            unsel = (len(val) == 11 and val.isdigit()) or len(val) == 16
        out = LinkTable.HelpChoice(self, obj, *args, **kwargs)
        if self._rs and obj == self._ctrdes:
            val = obj.GetValue()
            if unsel:
                wx.CallAfter(lambda: obj.SetSelection(0,len(val)))
        return out


# ------------------------------------------------------------------------------


class LinkTableCliente(LinkTableCliFor):
    
    tipanacods = "C"
    
    def SetInitFocusCD(self, fromgrid):
        if fromgrid:
            f = bt.OPTLNKGRDCLI
            if f is None:
                f = INITFOCUS_DESCRIZ
        else:
            f = bt.OPTLNKGRDCLI
            if f is None:
                f = INITFOCUS_DESCRIZ
        self.SetInitFocus(f)


# ------------------------------------------------------------------------------


class LinkTableFornit(LinkTableCliFor):
    
    tipanacods = "F"
    
    def SetInitFocusCD(self, fromgrid):
        if fromgrid:
            f = bt.OPTLNKGRDFOR
            if f is None:
                f = INITFOCUS_DESCRIZ
        else:
            f = bt.OPTLNKGRDFOR
            if f is None:
                f = INITFOCUS_DESCRIZ
        self.SetInitFocus(f)


# ------------------------------------------------------------------------------


class LinkTableEffetto(_LinkTablePdcMixin):
    
    tipanacods = "D"
    
    def __init__(self, *args, **kwargs):
        _LinkTablePdcMixin.__init__(self, *args, **kwargs)
        self.SetInitFocus(INITFOCUS_DESCRIZ)
        self.SetMinWidth(400)
    
    def GetSql(self, count=False):
        bt = Env.Azienda.BaseTab
        if count:
            fields = "COUNT(*)"
        else:
            fields = """pdc.id      'id',
                        pdc.codice  'codice',
                        pdc.descriz 'descriz',
                        IF(eff.tipo="R", "RIBA", IF(eff.tipo="I","RID",eff.tipo)) 'tipeff',
                        tipana.tipo 'tipo'
            """
        pdc = bt.TABNAME_PDC
        tipana = bt.TABNAME_PDCTIP
        effetti = bt.TABNAME_EFFETTI
        cmd = """
        SELECT %(fields)s
          FROM      %(pdc)s    pdc
               JOIN %(tipana)s  tipana ON tipana.id=pdc.id_tipo
          LEFT JOIN %(effetti)s eff ON eff.id=pdc.id
          """ % locals()
        return cmd
    
    def SetDataGrid(self, grid, rs):
        _STR = gridlib.GRID_VALUE_STRING
        cols = (( -1, ( 1, "Cod.",        _STR, False)),
                ( -1, ( 2, "Descrizione", _STR, False)),
                ( 40, ( 3, "Tipo",        _STR, False)),
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        grid.SetData(rs, colmap)
        for n, w in enumerate(colsize):
            if w>=0:
                grid.SetColumnDefaultSize(n, w)
                #grid.SetColSize(n, w)


# ------------------------------------------------------------------------------


class LinkTableContoIva(_LinkTablePdcMixin):
    tipanacods = "I"


# ------------------------------------------------------------------------------


class LinkTableAliqIva(LinkTable):
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        from anag.aliqiva import AliqIvaDialog
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_ALIQIVA, name, AliqIvaDialog)


# ------------------------------------------------------------------------------


class LinkTableRegIva(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        from cfg.regiva import RegIvaDialog
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_REGIVA, name, RegIvaDialog)
        self.canins = False
    
    def GetSql(self, count=False):
        if count:
            fields = 'COUNT(*)'
        else:
            fields = 'regiva.id, regiva.codice, regiva.descriz, regiva.tipo'
        table = self.db_name
        alias = 'regiva'
        return\
        """SELECT %(fields)s """\
        """FROM %(table)s AS %(alias)s""" % locals()


# ------------------------------------------------------------------------------


class LinkTableRegIvaNoScheda(LinkTable):
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_REGIVA, name, None)
        self.canins = False


# ------------------------------------------------------------------------------


class LinkTableCauContab(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_CFGCONTAB, name, None)
        self.SetMinWidth(400)
    
    def GetSql(self, count=False):
        if count:
            fields = 'COUNT(*)'
        else:
            fields = 'id, codice, descriz, IF(esercizio=1,"Es.Precedente","")'
        table = self.db_name
        alias = self.db_alias
        return """SELECT %(fields)s
                  FROM %(table)s %(alias)s""" % locals()
    
    def SetDataGrid(self, grid, rs):
        _STR = gridlib.GRID_VALUE_STRING
        cols = (( -1, ( 1, "Cod.",      _STR, False)),
                (200, ( 2, "Causale",   _STR, False)),
                (110, ( 3, "Esercizio", _STR, False)),
                (  1, ( 0, "#cau",      _STR, False)),
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        grid.SetData(rs, colmap)
        for n, w in enumerate(colsize):
            if w>=0:
                grid.SetColumnDefaultSize(n, w)
                #grid.SetColSize(n, w)
        grid.SetFitColumn(1)


# ------------------------------------------------------------------------------


class LinkTableDocMagazz(LinkTable):
    dbdoc = None
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_CFGMAGDOC, name, None)
        self.dbdoc = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGMAGDOC, 'tipdoc', writable=False)
        self.dbdoc.AddJoin(Env.Azienda.BaseTab.TABNAME_PDCTIP, 'tipana', idLeft='id_pdctip')
    def SetValue(self, idtpd, *a, **kw):
        LinkTable.SetValue(self, idtpd, *a, **kw)
        self.dbdoc.Get(idtpd)


# ------------------------------------------------------------------------------


class LinkTableMovMagazz(LinkTable):
    
    tipdoc = None
    
    def __init__(self, parent, id, name=None, docfather=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_CFGMAGMOV, name, None)
        self.SetMinWidth(500)
        if docfather:
            self.SetDocFather(docfather)
    
    def SetTipoDoc(self, td):
        self.tipdoc = td
        if td is None:
            flt = "1"
        else:
            flt = "id_tipdoc=%d" % td
        self.SetFilter(flt)
    
    def GetSql(self, count=False):
        tabmov = Env.Azienda.BaseTab.TABNAME_CFGMAGMOV
        tabdoc = Env.Azienda.BaseTab.TABNAME_CFGMAGDOC
        self.db_alias = """tm"""
        if count:
            fields = 'COUNT(*)'
        else:
            fields = """tm.id, tm.codice, tm.descriz, 
                        td.id      AS 'tipdoc_id', 
                        td.codice  AS 'tipdoc_codice', 
                        td.descriz AS 'tipdoc_descriz' 
               """
        return """SELECT %(fields)s
                  FROM %(tabmov)s tm
                  JOIN %(tabdoc)s td ON tm.id_tipdoc=td.id""" % locals()
    
    def GetSqlOrder(self, field):
        return """td.%s, tm.%s""" % (field, field)
    
    def SetDataGrid(self, grid, rs):
        _STR = gridlib.GRID_VALUE_STRING
        cols = (( -1, ( 1, "Cod.",      _STR, False)),
                (200, ( 2, "Movimento", _STR, False)),
                ( 35, ( 4, "Cod.",      _STR, False)),
                (200, ( 5, "Documento", _STR, False)),
                )
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        grid.SetData(rs, colmap)
        for n, w in enumerate(colsize):
            if w>=0:
                grid.SetColumnDefaultSize(n, w)
                #grid.SetColSize(n, w)
    
    def SetDocFather(self, ctrdoc):
        assert isinstance(ctrdoc, LinkTableDocMagazz)
        from awc.controls.linktable import EVT_LINKTABCHANGED
        self.GetParent().Bind(EVT_LINKTABCHANGED, self.OnDocChanged, ctrdoc)
    
    def OnDocChanged(self, event):
        self.SetTipoDoc(event.GetEventObject().GetValue())
        event.Skip()


# ------------------------------------------------------------------------------


class LinkTableModPag(LinkTable):
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        from anag.modpag import ModPagDialog
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_MODPAG, name, ModPagDialog)


# ------------------------------------------------------------------------------


class LinkTableMagazz(LinkTable):
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_MAGAZZ, name, None)


# ------------------------------------------------------------------------------


class LinkTableAgente(LinkTable):
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        from anag.agenti import AgentiDialog
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_AGENTI, name, AgentiDialog)


# ------------------------------------------------------------------------------


class LinkTableTipoEvento(LinkTable):
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        from cfg.eventi import TipiEventoDialog
        self.SetDataLink(Env.Azienda.BaseTab.TABNAME_TIPEVENT, name, TipiEventoDialog)


# ------------------------------------------------------------------------------


class DataLinkPdcCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTablePdc


# ------------------------------------------------------------------------------


class LinkTabPdcAttr(dbg.LinkTabAttr):
    editorclass = DataLinkPdcCellEditor


# ------------------------------------------------------------------------------


class DataLinkCassaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableCassa


# ------------------------------------------------------------------------------


class LinkTabCassaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkCassaCellEditor


# ------------------------------------------------------------------------------


class DataLinkBancaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableBanca


# ------------------------------------------------------------------------------


class LinkTabBancaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkBancaCellEditor


# ------------------------------------------------------------------------------


class DataLinkCassaBancaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableCassaBanca


# ------------------------------------------------------------------------------


class LinkTabCassaBancaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkCassaBancaCellEditor


# ------------------------------------------------------------------------------


class DataLinkClienteCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableCliente


# ------------------------------------------------------------------------------


class LinkTabClienteAttr(dbg.LinkTabAttr):
    editorclass = DataLinkClienteCellEditor


# ------------------------------------------------------------------------------


class DataLinkFornitCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableFornit


# ------------------------------------------------------------------------------


class LinkTabFornitAttr(dbg.LinkTabAttr):
    editorclass = DataLinkFornitCellEditor


# ------------------------------------------------------------------------------


class DataLinkCliForCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableCliFor


# ------------------------------------------------------------------------------


class LinkTabCliForAttr(dbg.LinkTabAttr):
    editorclass = DataLinkCliForCellEditor


# ------------------------------------------------------------------------------


class DataLinkEffettoCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableEffetto


# ------------------------------------------------------------------------------


class LinkTabEffettoAttr(dbg.LinkTabAttr):
    editorclass = DataLinkEffettoCellEditor


# ------------------------------------------------------------------------------


class DataLinkContoIvaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableContoIva


# ------------------------------------------------------------------------------


class LinkTabContoIvaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkContoIvaCellEditor


# ------------------------------------------------------------------------------


class DataLinkAliqIvaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableAliqIva


# ------------------------------------------------------------------------------


class DataLinkRegIvaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableRegIva


# ------------------------------------------------------------------------------


class DataLinkDocMagazzEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableDocMagazz


# ------------------------------------------------------------------------------


class LinkTabAliqIvaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkAliqIvaCellEditor


# ------------------------------------------------------------------------------


class LinkTabRegIvaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkRegIvaCellEditor


# ------------------------------------------------------------------------------


class LinkTabDocMagazzAttr(dbg.LinkTabAttr):
    editorclass = DataLinkDocMagazzEditor


# ------------------------------------------------------------------------------


class DataLinkTipoEventoEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTipoEvento


# ------------------------------------------------------------------------------


class LinkTabTipoEventoAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTipoEventoEditor


# ------------------------------------------------------------------------------


class LinkTableBilCee(LinkTable):
    
    def __init__(self, parent, id, name, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        self.digitsearch_oncode = False
        self.tabsearch_oncode = True
        from cfg.bilcee import BilCeeDialog
        self.SetDataLink('x4.bilcee', name, BilCeeDialog)
        self.db_alias = 'bilcee'
        self.SetFilter('bilcee.selectable=1')
        self.SetCodeWidth(80)
        self.SetMinWidth(640)
    
    def GetSql(self, count=False):
        if count:
            fields = 'COUNT(*)'
        else:
            fields = """bilcee.id, bilcee.codice, bilcee.descriz, 
                        bilcee.sezione, bilcee.voce, bilcee.capitolo, 
                        bilcee.dettaglio, bilcee.subdett
            """
        return """SELECT %(fields)s
                  FROM x4.bilcee AS bilcee""" % locals()
    
    def GetDataGridColumns(self):
        cols = self.GetDataGridStructure()
        return [c[1] for c in cols]
    
    def _GetColMap(self):
        _STR = gridlib.GRID_VALUE_STRING
        return (( 35, ( 3, "Sez.",        _STR, False)),
                ( 35, ( 4, "Voce",        _STR, False)),
                ( 35, ( 5, "Cap.",        _STR, False)),
                ( 35, ( 6, "Det.",        _STR, False)),
                ( 35, ( 7, "Sub",         _STR, False)),
                (300, ( 2, "Descrizione", _STR, False)),
            )
    
    def SetDataGrid(self, grid, rs):
        cols = self._GetColMap()
        colmap  = [c[1] for c in cols]
        grid.SetData(rs, colmap)
    
    def GetGridColumnSizes(self):
        cols = self._GetColMap()
        colsize = [c[0] for c in cols]
        return colsize
    
    def GetGridColumn2Fit(self):
        return 5


# ------------------------------------------------------------------------------


class LinkTableOperatori(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
#        self.digitsearch_oncode = Env.Azienda.BaseTab.MAGDIGSEARCH
#        self.tabsearch_oncode = not self.digitsearch_ondescriz
        if name:
            self.SetName(name)
        self.cardclass = None
        self.SetNameAlias()
    
    def SetDataLink(self, *args, **kwargs):
        LinkTable.SetDataLink(self, *args, **kwargs)
        self.SetNameAlias()
    
    def SetNameAlias(self):
        self.db_name = 'x4.utenti'
        self.db_alias = 'utenti'
        
    def GetSql(self, count=False):
        table = self.db_name
        alias = self.db_alias
        if count:
            fields = 'COUNT(*)'
        else:
            fields = 'utenti.id, utenti.codice, utenti.descriz'
        return """SELECT %(fields)s 
                    FROM %(table)s AS %(alias)s""" % locals()


# ------------------------------------------------------------------------------


class DataLinkOperatoriCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableOperatori


# ------------------------------------------------------------------------------


class LinkTabOperatoriAttr(dbg.LinkTabAttr):
    editorclass = DataLinkOperatoriCellEditor


# ------------------------------------------------------------------------------


class LinkTableStati(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from cfg.stati import StatiDialog
        self.cardclass = StatiDialog
    
    def SetNameAlias(self):
        self.db_name = 'x4.stati'
        self.db_alias = 'stati'
        
    def GetSql(self, count=False):
        table = self.db_name
        alias = self.db_alias
        if count:
            fields = 'COUNT(*)'
        else:
            fields = 'stati.id, stati.codice, stati.descriz, stati.is_cee, stati.is_blacklisted, stati.vatprefix'
        return """SELECT %(fields)s """\
               """FROM %(table)s AS %(alias)s""" % locals()
    
    def IsCee(self):
        if self._rs:
            return self._rs[3] == 1
        return False
    
    def IsBlacklisted(self):
        if self._rs:
            return self._rs[4] == 1
        return False
    
    def GetVatPrefix(self):
        if self._rs:
            return self._rs[5]
        return None
    
    def SetValueHome(self):
        db = adb.db.__database__
        cmd = self.GetSql()+' WHERE stati.codice="IT"'
        if db.Retrieve(cmd):
            if len(db.rs) == 1:
                self.SetValue(db.rs[0][0])
                return True
        return False
        


# ------------------------------------------------------------------------------


class DataLinkStatiCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableStati


# ------------------------------------------------------------------------------


class LinkTabStatiAttr(dbg.LinkTabAttr):
    editorclass = DataLinkStatiCellEditor


# ------------------------------------------------------------------------------


class LinkTableTraCau(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.trasp import TraCauDialog
        self.cardclass = TraCauDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_TRACAU
        self.db_alias = 'tracau'


# ------------------------------------------------------------------------------


class DataLinkTraCauCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTraCau


# ------------------------------------------------------------------------------


class LinkTabTraCauAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTraCauCellEditor


# ------------------------------------------------------------------------------


class LinkTableTraCur(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.trasp import TraCurDialog
        self.cardclass = TraCurDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_TRACUR
        self.db_alias = 'tracur'


# ------------------------------------------------------------------------------


class DataLinkTraCurCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTraCur


# ------------------------------------------------------------------------------


class LinkTabTraCurAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTraCurCellEditor


# ------------------------------------------------------------------------------


class LinkTableTraPor(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.trasp import TraPorDialog
        self.cardclass = TraPorDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_TRAPOR
        self.db_alias = 'trapor'


# ------------------------------------------------------------------------------


class DataLinkTraPorCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTraPor


# ------------------------------------------------------------------------------


class LinkTabTraPorAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTraPorCellEditor


# ------------------------------------------------------------------------------


class LinkTableTraAsp(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.trasp import TraAspDialog
        self.cardclass = TraAspDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_TRAASP
        self.db_alias = 'traasp'


# ------------------------------------------------------------------------------


class DataLinkTraAspCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTraAsp


# ------------------------------------------------------------------------------


class LinkTabTraAspAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTraAspCellEditor


# ------------------------------------------------------------------------------


class LinkTableTraVet(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.trasp import TraVetDialog
        self.cardclass = TraVetDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_TRAVET
        self.db_alias = 'travet'
        
    def GetSql(self, count=False):
        table = self.db_name
        alias = self.db_alias
        if count:
            fields = 'COUNT(*)'
        else:
            fields = 'travet.id, travet.codice, travet.descriz, travet.indirizzo, travet.cap, travet.citta, travet.prov'
        return """SELECT %(fields)s 
                    FROM %(table)s AS %(alias)s""" % locals()
    
    def GetFullDescription(self):
        if self._rs:
            _, _, des, ind, cap, cit, prv, stt = self._rs 
            out = des
            if ind: out += (' %' % ind)
            if cap: out += (' %' % cap)
            if cit: out += (' %' % cit)
            if prv: out += (' %' % prv)
            return out
        return None


# ------------------------------------------------------------------------------


class DataLinkTraVetCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTraVet


# ------------------------------------------------------------------------------


class LinkTabTraVetAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTraVetCellEditor


# ------------------------------------------------------------------------------


class LinkTableTraCon(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.trasp import TraConDialog
        self.cardclass = TraConDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_TRACON
        self.db_alias = 'tracon'


# ------------------------------------------------------------------------------


class DataLinkTraConCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableTraCon


# ------------------------------------------------------------------------------


class LinkTabTraConAttr(dbg.LinkTabAttr):
    editorclass = DataLinkTraConCellEditor


# ------------------------------------------------------------------------------


class LinkTableZona(LinkTable):
    
    def __init__(self, parent, id, name=None, **kwargs):
        LinkTable.__init__(self, parent, id, **kwargs)
        if name:
            self.SetName(name)
        self.SetNameAlias()
        from anag.zone import ZoneDialog
        self.cardclass = ZoneDialog
    
    def SetNameAlias(self):
        self.db_name = bt.TABNAME_ZONE
        self.db_alias = 'zona'


# ------------------------------------------------------------------------------


class DataLinkZonaCellEditor(gred.DataLinkCellEditor):
    baseclass = LinkTableZona


# ------------------------------------------------------------------------------


class LinkTabZonaAttr(dbg.LinkTabAttr):
    editorclass = DataLinkZonaCellEditor
