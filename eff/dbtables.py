#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         eff/dbtables.py
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

from contab import dbtables as dbc
bt = dbc.Env.Azienda.BaseTab

adb = dbc.adb


class Eff(dbc.Pcf):
    """
    DbTable Effetti.
    Deriva da contab.dbtables.Pcf, ma filtra le partite con flag effetto.
    pcf
      +-> pdc
      +-> tipana (pdctip)
      +-> modpag (modpag)
      +-> caus   (cfgcontab)
      !      +-> regiva
      +-> pdcban (banche)
      +-> bap    (bancf)
      +==>> rif (contab_s)
              +-> reg (contab_h)
                    +-> cau (cfgcontab)
    """
    def __init__(self, *args, **kwargs):
        
        dbc.Pcf.__init__(self, *args, **kwargs)
        
        self.pdc.AddJoin(\
            dbc.bt.TABNAME_CLIENTI, "anag", idLeft="id", idRight="id",\
            join=adb.JOIN_LEFT)
        
        pdcban = self.AddJoin(\
            dbc.bt.TABNAME_PDC,     "pdcban", idLeft="id_effban", idRight="id",\
            join=adb.JOIN_LEFT)
        
        pdcban.AddJoin(\
            dbc.bt.TABNAME_BANCHE,  "ban", idLeft="id", idRight="id",\
            join=adb.JOIN_LEFT)
        
        self.AddJoin(\
            dbc.bt.TABNAME_BANCF,   "bap", idLeft="id_effbap", idRight="id",\
            join=adb.JOIN_LEFT)
        
        #la seguente dbtable è slegata dai dati di questa classe
        #viene usata in fase di stampa effetti per accedere ai dati della
        #banca emittente (pdcban e seguenti hanno senso solo *dopo* l'emissione)
        pdcbanem = adb.DbTable(bt.TABNAME_PDC, 'pdc', writable=False)
        pdcbanem.AddJoin(bt.TABNAME_BANCHE, 'banem', idLeft='id', idRight='id')
        pdcbanem.Get(-1)
        self._info.pdcbanem = pdcbanem
        
        self.ClearOrders()
        self.AddOrder("pcf.datdoc")
        self.AddOrder("pcf.numdoc")
        self.AddOrder("pcf.datscad")
        
        self.ClearFilters()
        
        self.AddField('0.0', 'saldato')
        
        self.Get(-1)
    
    def Retrieve(self, *args, **kwargs):
        """
        Modifico il saldo di ogni partita per gestire l'emissione di:
        - partite aperte: viene emesso il saldo della partita
        - partite chiuse: viene emesso l'importo originale della partita
        """
        out = dbc.Pcf.Retrieve(self, *args, **kwargs)
        cn = lambda col: self._GetFieldIndex(col, inline=True)
        colimp, colpar, colsal, coleff, colflag =\
              map(cn, ('imptot', 'imppar', 'saldo', 'impeff', 'saldato'))
        rse = self.GetRecordset()
        for row in range(len(rse)):
            #se la partita ha un saldo, emetto quello
            saldo = rse[row][colsal]
            rse[row][colflag] = int(saldo == 0)
            if saldo == 0:
                #altrimenti, vuol dire che riemetto la riba visto che la partita
                #risulta saldata; quindo emetto l'importo originale
                saldo = rse[row][colimp]
            rse[row][coleff] = saldo
        return out
    
    def ClearFilters(self):
        dbc.Pcf.ClearFilters(self)
        self.AddFilter("tipana.tipo='C'")
    
    def rifdoc(self):
        if False:#eff.desriba1:
            out = self.desriba1+self.desriba2
        else:
            if self.rif.RowsCount() <= 1:
                if self.numdoc and self.datdoc:
                    #non trovo riferimenti (partita manuale?) o solo uno
                    #quindi la partita si riferisce ad una unica fattura
                    #descrivo con i dati della partita
                    out = "Rif.to Fattura n. %s del %s"\
                        % (self.numdoc, self.datdoc.Format().split()[0])
                else:
                    #no riferimenti, no numdoc/datdoc: non posso descrivere
                    out = ''
            else:
                #trovo i riferimenti, compongo la descrizione sommando
                #tutti i riferimenti che trovo
                out = ''
                n = 0
                regids = [scad.id_reg for scad in self.rif]
                reg = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg', writable=False)
                if reg.Retrieve("reg.id_regiva IS NOT NULL AND reg.id IN (%s)" % ','.join(map(str, regids))):
                    for reg in reg:
                        if out:
                            out += ', '
                        out += reg.numdoc
                        if reg.datdoc:
                            out += "/%s" % reg.datdoc.year
                        n += 1
                    if out:
                        if n == 1:
                            out = 'Rif.to fattura n. '+out
                        else:
                            out = 'Rif.to documenti: '+out
            #impeff = (self.imptot or 0) - (self.imppar or 0)
            #out += " Totale Euro %.2f" % impeff
        return (out or '').ljust(80)


# ------------------------------------------------------------------------------


class RIBA(Eff):
    
    def ClearFilters(self):
        dbc.Pcf.ClearFilters(self)
        self.AddFilter("tipana.tipo='C'")
        self.AddFilter("pcf.riba=1")


# ------------------------------------------------------------------------------


class RID(Eff):
    
    def ClearFilters(self):
        dbc.Pcf.ClearFilters(self)
        self.AddFilter("tipana.tipo='C'")
        self.AddFilter("modpag.tipo='I'")


# ------------------------------------------------------------------------------


def GetEffConfig(tipo="R", banca=None):
    """
    Legge configurazione x generazione file effetti.
    Parametri:
    tipo def. R tipo configurazione
    banca def. None banca del tracciato
    Restituisce un dizionario di tre chiavi (H=head,B=body,F=foot)
    i valori sono le liste di mascro da generare, una per ogni riga del file
    """
    ec = dbc.Env.Azienda.BaseTab.TABNAME_CFGEFF
    cfg = adb.DbTable(ec, "cfg", writable=False)
    cfg.AddFilter("cfg.tipo=%s", tipo)
    cfg.StoreFilters()
    cfg.AddFilter("cfg.id_banca=%s", banca)
    cfg.Retrieve()
    if cfg.RowsCount() == 0:
        cfg.ResumeFilters()
        cfg.Retrieve()
    if cfg.RowsCount() == 0:
        raise Exception, "Manca la configurazione del file effetti"
    tr = {"H": [],\
          "B": [],\
          "F": []}
    cfgb = []
    cfgf = []
    for c in cfg:
        if c.zona in "HBF":
            tr[c.zona].append(c.macro)
    del cfg
    return tr
    
    
if __name__ == "__main__":
    db = adb.DB()
    db.Connect()
    eff = Eff()
    eff.Retrieve()
    print eff
    for e in eff:
        print e.id, e.datscad, e.numdoc, e.pdc.descriz, e.pdc.cli.indirizzo
