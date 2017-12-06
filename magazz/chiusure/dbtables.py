#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         magazz/chiusure/dbtables.py
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

import Env
bt = Env.Azienda.BaseTab

import stormdb as adb
import anag.dbtables as dba

from magazz.dbtables import InventarioDaMovim as Inventario

import cfg.dbtables as dbcfg

import magazz.dbtables as dbm


MAXRIGHE_PER_DOC = 444


class ConsolidaCosti(adb.DbTable):
    
    def __init__(self):
        
        adb.DbTable.__init__(self, bt.TABNAME_PROCOS, 'procos')
        self.Reset()
        
        i = self._info
        i.dbmag = dba.TabMagazz()
        i.dbpro = adb.DbTable(bt.TABNAME_PROD, 'prod', fields='id,codice,costo,prezzo')
        i.dbpro.AddOrder('prod.codice')
        i.dbinv = Inventario(flatmag=True)
        i.dbgia = adb.DbTable(bt.TABNAME_PROGIA)
        i.dbgia.Reset()
    
    def EsistonoCostiAnno(self, anno):
        i = self._info
        db = i.db
        db.Retrieve("SELECT COUNT(*) FROM %s WHERE anno=%%s" % bt.TABNAME_PROCOS, (anno,))
        return db.rs[0][0] or 0
    
    def EliminaCostiConsolidatiAnno(self, anno):
        db = self._info.db
        db.Execute("DELETE FROM %s WHERE anno=%%s" % bt.TABNAME_PROCOS, (anno,))
    
    def ConsolidaCostiAnno(self, anno, func0=None, func1=None):
        self.EliminaCostiConsolidatiAnno(anno)
        pro = self._info.dbpro
        pro.Retrieve()
        inv = self._info.dbinv
        fa = Env.DateTime.Date(anno, 12, 31)
        inv.SetDataInv(fa)
        inv.Retrieve()
        rsi = inv.GetRecordset()
        if func0:
            func0(pro)
        self.Reset()
        def cc(db, x):
            return db._GetFieldIndex(x, inline=True)
        col_idp = cc(inv, 'id')
        col_cos = cc(inv, 'costo')
        col_ini = cc(inv, 'total_ini')
        col_iniv = cc(inv, 'total_iniv')
        col_car = cc(inv, 'total_car')
        col_carv = cc(inv, 'total_carv')
        for p, pro in enumerate(pro):
            self.CreateNewRow()
            self.id_prod = pro.id
            self.anno = anno
            self.costou = pro.costo
            self.prezzop = pro.prezzo
            n = inv.LocateRS(lambda x: x[col_idp] == pro.id)
            if n is not None:
                r = rsi[n]
                iniv = r[col_iniv] or 0
                carv = r[col_carv] or 0
                ini = r[col_ini] or 0
                car = r[col_car] or 0
                try:
                    cm = (iniv+carv)/(ini+car)
                except ZeroDivisionError:
                    cm = 0
                self.costom = cm
            if func1:
                func1(p)
        if not self.Save():
            raise Exception, repr(self.GetError())
        return True
    
    def EliminaGiacenzeAnno(self, anno):
        db = self._info.db
        db.Execute("DELETE FROM %s WHERE anno=%%s" % bt.TABNAME_PROGIA, (anno,))
    
    def CreaGiacenzeAnno(self, anno, datgiac, func0=None, func1=None, func2=None):
        i = self._info
        db = i.db
        db.Execute("DELETE FROM %s WHERE anno=%%s" % bt.TABNAME_PROGIA, anno)
        mag = i.dbmag
        mag.Retrieve()
        inv = i.dbinv
        gia = i.dbgia
        def cc(db, x):
            return db._GetFieldIndex(x, inline=True)
        col_id = cc(inv, 'id')
        col_gia = cc(inv, 'total_giac')
        for mag in mag:
            if func0:
                func0(mag)
            inv.ClearFilters()
            inv.SetMagazz(mag.id)
            inv.SetDataInv(datgiac)
            inv.Retrieve()
            if func1:
                func1(mag, inv)
            for n in range(inv.RowsCount()):
                r = inv.GetRecordset()[n]
                gia.Reset()
                gia.CreateNewRow()
                gia.id_prod = r[col_id]
                gia.id_magazz = mag.id
                gia.anno = anno
                gia.datgia = datgiac
                gia.giacon = r[col_gia]
                if not gia.Save():
                    raise Exception, repr(gia.GetError())
                if func2:
                    func2(mag, inv, n)
        return True


# ------------------------------------------------------------------------------


class EditGiacenzeTable(adb.DbTable):
    
    _tipval = None
    
    def __init__(self, **kwargs):
        
        if 'tipval' in kwargs:
            self.SetTipVal(kwargs.pop('tipval'))
        
        adb.DbTable.__init__(self, bt.TABNAME_PROD, 'prod')
        cos = self.AddJoin(bt.TABNAME_PROCOS, 'procos', idLeft='id', idRight='id_prod', join=adb.JOIN_LEFT)
        gia = self.AddJoin(bt.TABNAME_PROGIA, 'progia', idLeft='id', idRight='id_prod', join=adb.JOIN_LEFT)
        mag = gia.AddJoin(bt.TABNAME_MAGAZZ,  'magazz', join=adb.JOIN_LEFT)
        
        cat = self.AddJoin(bt.TABNAME_CATART, 'catart', idLeft='id_catart', idRight='id', join=adb.JOIN_LEFT)
        
        self.Reset()
        self.AddOrder('prod.codice')
    
    def SetTipVal(self, tv):
        self._tipval = tv
    
    def GetTipVal(self):
        return self._tipval
    
    def GetValDes(self):
        out = '?'
        if self._tipval == "U":
            out = "Costo Ultimo"
        elif self._tipval == "M":
            out = "Costo Medio"
        return out
    
    def GetValUni(self):
        if self._tipval == "U":
            col = 'costou'
        elif self._tipval == "M":
            col = 'costom'
        else:
            return None
        return getattr(self.procos, col)
    
    def GetValore(self):
        return round((self.progia.giafis or 0)*(self.GetValUni() or 0), 
                     bt.VALINT_DECIMALS)


# ------------------------------------------------------------------------------


class ChiusAutomTable(dbcfg.Automat):
    
    def GetDocumento(self):
        return self.GetAutomat('maginidoc')
    
    def GetMovimento(self):
        return self.GetAutomat('maginimov')


# ------------------------------------------------------------------------------


class RiepilogoGiacenzeTable(adb.DbTable):
    
    def __init__(self, anno=None, tipval="U"):
        adb.DbTable.__init__(self, bt.TABNAME_PROGIA, 'progia', fields=None)
        self.anno = anno
        self.tipval = tipval
        self.AddJoin(bt.TABNAME_PROD,   'prod', fields=None)
        self.AddJoin(bt.TABNAME_MAGAZZ, 'magazz', fields=None)
        gcre = "procos.id_prod=progia.id_prod AND procos.anno=progia.anno"
        self.AddJoin(bt.TABNAME_PROCOS, "procos", relexpr=gcre, fields=None)
        self.AddFilter("progia.anno=%s", anno)
        self.AddFilter("progia.movgen IS NULL OR progia.movgen<>1")
        self.AddOrder("magazz.codice")
        if tipval == "U":
            c = 'costou'
        elif tipval == "M":
            c = 'costom'
        else:
            raise Exception, "Tipo valorizzazione sconosciuto"
        self.AddGroupOn('progia.id_magazz', 
                        """mag_id""")
        self.AddGroupOn('magazz.codice', 
                        """mag_codice""")
        self.AddGroupOn('magazz.descriz', 
                        """mag_descriz""")
        self.AddCountOf('IF(progia.giafis>0,1,NULL)',
                        """prodotti""")
        self.AddCountOf('IF(progia.giafis>0 AND (procos.%s IS NULL OR procos.%s=0),1,NULL)' % (c, c), 
                        """prod_noval""")
        self.AddTotalOf('progia.giafis', 
                        """qtagia""")
        self.AddTotalOf('progia.giafis*procos.%s' % c, 
                        """valgia""")
        self.Retrieve()
    
    def TestMagazzini(self):
        """
        Verifica che tutti i magazzini esistenti abbiano il legame con il 
        relativo sottoconto magazzino.
        """
        mag = adb.DbTable(bt.TABNAME_MAGAZZ, 'magazz')
        pdc = mag.AddJoin(bt.TABNAME_PDC, 'pdc', join=adb.JOIN_LEFT)
        mag.AddOrder('magazz.codice')
        mag.Retrieve()
        for mag in mag:
            if mag.pdc.id is None:
                return False
        return True
        
    def GeneraMovimenti(self, tipdoc, tipmov, datdoc, numdoc, tipval, 
                        func=None, func0=None):
        if tipval == "U":
            cc = 'costou'
        elif tipval == "M":
            cc = 'costom'
        else:
            raise Exception, "Tipo valorizzazione sconosciuto"
        doc = adb.DbTable(bt.TABNAME_MOVMAG_H, 'doc')
        doc.AddFilter("id_tipdoc=%s", tipdoc)
        doc.AddFilter("YEAR(datdoc)=%s", datdoc.year)
        doc.AddFilter("numdoc>=%s", numdoc)
        doc.AddLimit(1)
        doc.Retrieve()
        if not doc.IsEmpty():
            raise Exception, "Esistono documenti successivi"
        doc = dbm.DocMag()
        mov = doc.mov
        pro = EditGiacenzeTable()
        mag = dba.TabMagazz()
        n = 0
        for r in self:
            mag.Get(r.mag_id)
            if callable(func0):
                func0(mag)
            pro.ClearFilters()
            pro.AddFilter("progia.id_magazz=%s", r.mag_id)
            pro.AddFilter("progia.giafis IS NOT NULL AND progia.giafis<>0")
            pro.procos.SetRelation("procos.id_prod=prod.id AND procos.anno=%d" % self.anno)
            pro.progia.SetRelation("progia.id_prod=prod.id AND progia.anno=%d AND progia.id_magazz=%d" % (self.anno, r.mag_id))
            pro.Retrieve()
            for p in pro:
                if doc.IsEmpty():
                    doc.CreateNewRow()
                    doc.datreg = datdoc
                    doc.datdoc = datdoc
                    doc.numdoc = numdoc
                    doc.id_tipdoc = tipdoc
                    doc.id_magazz = r.mag_id
                    doc.id_pdc = mag.id_pdc
                    doc.f_ann = 0
                    doc.f_acq = 0
                    doc.f_genrag = 0
                    doc.f_printed = 0
                    doc.f_emailed = 0
                    nr = 1
                    numdoc += 1
                mov.CreateNewRow()
                mov.id_tipmov = tipmov
                mov.numriga = nr
                mov.id_prod = p.id
                mov.descriz = p.descriz
                mov.um = p.um
                mov.pzconf = p.pzconf
                mov.qta = p.progia.giafis
                mov.prezzo = getattr(p.procos, cc)
                mov.importo = round((mov.qta or 0)*(mov.prezzo or 0), bt.VALINT_DECIMALS)
                mov.id_aliqiva = p.id_aliqiva
                mov.f_ann = 0
                mov.f_acq = 0
                nr += 1
                if nr>MAXRIGHE_PER_DOC:
                    doc.MakeTotals()
                    if not doc.Save():
                        raise Exception, repr(doc.GetError())
                    doc.Reset()
                n += 1
                if callable(func):
                    func(n)
            if not doc.mov.IsEmpty():
                doc.MakeTotals()
                if not doc.Save():
                    raise Exception, repr(doc.GetError())
                doc.Reset()
            db = doc._info.db
            cmd = "UPDATE %s SET movgen=1 WHERE anno=%%s AND id_magazz=%%s"\
                % bt.TABNAME_PROGIA
            db.Execute(cmd, (self.anno, r.mag_id))
        s = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')
        s.Retrieve("chiave=%s", "magdatchi")
        if s.IsEmpty():
            s.CreateNewRow()
            s.chiave = "magdatchi"
        s.data = datdoc-1
        s.Save()
        return True
