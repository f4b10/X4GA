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
    Restituisce un dizionario di tre chiavi o più chiavi (H=head,B=body,F=foot)
    i valori sono le liste di mascro da generare, una per ogni riga del file
    """
    ec = dbc.Env.Azienda.BaseTab.TABNAME_CFGEFF
    cfg = adb.DbTable(ec, "cfg", writable=False)
    cfg.AddFilter("cfg.tipo=%s", tipo)
    cfg.StoreFilters()
    cfg.AddFilter("cfg.id_banca=%s", banca)
    cfg.AddOrder('riga')
    cfg.Retrieve()
    if cfg.RowsCount() == 0:
        cfg.ResumeFilters()
        cfg.Retrieve()
    if cfg.RowsCount() == 0:
        InitConfig(tipo)
        cfg.Retrieve()
    if cfg.RowsCount() == 0:
        raise Exception, "Manca la configurazione del file effetti"
    tr = {"H": [],\
          "B": [],\
          "H1": [],\
          "B1": [],\
          "F1": [],\
          "F": []}
    cfgb = []
    cfgf = []
    for c in cfg:
        if c.zona in "H|B|F|H1|B1|F1":
            tr[c.zona].append(c.macro)
    del cfg
    return tr


def InitConfig(tipo='R'):
    # utilizzati da peidaigo
    print 'inizializza configurazione effetti di tipo %s' % tipo
    cfg=[]
    if tipo=='S':
        cfg.append(['H ',  0, "'<?xml version=" + '"1.0" encoding="UTF-8"?>' +"'"])
        cfg.append(['H ',  1, "'<CBIBdySDDReq xmlns=" +'"urn:CBI:xsd:CBIBdySDDReq.00.01.01" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'+"'"])
        cfg.append(['H ',  2, "'              xsi:schemaLocation=" +'"urn:CBI:xsd:CBIBdySDDReq.00.01.01 CBIBdySDDReq.00.01.01.xsd">' + "'"])
        cfg.append(['H ',  3, "'  <PhyMsgInf>'"])
        cfg.append(['H ',  4, "'    <PhyMsgTpCd>' + info.PhyMsgTpCd +'</PhyMsgTpCd>'"])
        cfg.append(['H ',  5, "'    <NbOfLogMsg>1</NbOfLogMsg>'"])
        cfg.append(['H ',  6, "'  </PhyMsgInf>'"])
        cfg.append(['H ',  7, "'  <CBIEnvelSDDReqLogMsg>'"])
        cfg.append(['H ',  8, "'    <CBISDDReqLogMsg>'"])
        cfg.append(['H ',  9, "'      <GrpHdr xmlns=" + '"urn:CBI:xsd:CBISDDReqLogMsg.00.01.01">' +"'"])
        cfg.append(['H ', 10, "'        <MsgId>'+ info.MsgId + '</MsgId>'",                            '<!-- Identificativo univoco messaggio -->'])
        cfg.append(['H ', 11, "'        <CreDtTm>'+ info.CreDtTm + '</CreDtTm>'",                      '<!-- Data e Ora di Creazione -->'])
        cfg.append(['H ', 12, "'        <NbOfTxs>' + str(info.NbOfTxs) +'</NbOfTxs>'",                 '<!-- Numero totale disposizioni -->'])
        cfg.append(['H ', 13, "'        <CtrlSum>' + ('% 8.2f' % info.CtrlSum).strip() +'</CtrlSum>'", '<!-- Totale complessivo delle disposizioni presenti nella distinta -->'])
        cfg.append(['H ', 14, "'        <InitgPty>'"])
        cfg.append(['H ', 15, "'          <Nm>'+ info.InitgPty_Nm + '</Nm>'",                          '<!-- Nome Azienda Creditrice -->'])
        cfg.append(['H ', 16, "'          <Id>'"])
        cfg.append(['H ', 17, "'            <OrgId>'"])
        cfg.append(['H ', 18, "'              <Othr>'"])
        cfg.append(['H ', 19, "'                <Id>' + info.InitgPty_Id + '</Id>'",                  '<!-- Identificativo Azienda Creditrice (Cod. CUC) -->'])
        cfg.append(['H ', 20, "'                <Issr>CBI</Issr>'"])
        cfg.append(['H ', 21, "'              </Othr>'"])
        cfg.append(['H ', 22, "'            </OrgId>'"])
        cfg.append(['H ', 23, "'          </Id>'"])
        cfg.append(['H ', 24, "'        </InitgPty>'"])
        cfg.append(['H ', 25, "'      </GrpHdr>'"])
        cfg.append(['H1',  0, "'      <PmtInf xmlns=" +'"urn:CBI:xsd:CBISDDReqLogMsg.00.01.01">' "'"])
        cfg.append(['H1',  1, "'        <PmtInfId>' + info.PmtInfId + '</PmtInfId>'",                 '<!-- Identificativo Univoco della Sottodistinta -->'])
        cfg.append(['H1',  2, "'        <PmtMtd>DD</PmtMtd>'"])
        cfg.append(['H1',  3, "'        <PmtTpInf>'"])
        cfg.append(['H1',  4, "'          <SvcLvl>'"])
        cfg.append(['H1',  5, "'            <Cd>SEPA</Cd>'"])
        cfg.append(['H1',  6, "'          </SvcLvl>'"])
        cfg.append(['H1',  7, "'          <LclInstrm>'"])
        cfg.append(['H1',  8, "'            <Cd>CORE</Cd>'"])
        cfg.append(['H1',  9, "'          </LclInstrm>'"])
        cfg.append(['H1', 10, "'          <SeqTp>' + info.SeqTp + '</SeqTp>'",                        '<!-- Tipo  sequenza di incasso -->'])
        cfg.append(['H1', 11, "'        </PmtTpInf>'"])
        cfg.append(['H1', 12, "'        <ReqdColltnDt>' + info.ReqdColltnDt +'</ReqdColltnDt>'",      '<!-- Data Scadenza -->' ])
        cfg.append(['H1', 13, "'        <Cdtr>'"])
        cfg.append(['H1', 14, "'          <Nm>' + info.Cdtr_Nm + '</Nm>'",                            '<!-- Nome Azienda Creditrice -->'])
        cfg.append(['H1', 15, "'        </Cdtr>'"])
        cfg.append(['H1', 16, "'        <CdtrAcct>'"])
        cfg.append(['H1', 17, "'          <Id>'"])
        cfg.append(['H1', 18, "'            <IBAN>' + info.CdtrAcct_IBAN + '</IBAN>'",                '<!-- IBAN Banca Creditrice -->'])
        cfg.append(['H1', 19, "'          </Id>'"])
        cfg.append(['H1', 20, "'        </CdtrAcct>'"])
        cfg.append(['H1', 21, "'        <CdtrAgt>'"])
        cfg.append(['H1', 22, "'          <FinInstnId>'"])
        cfg.append(['H1', 23, "'            <ClrSysMmbId>'"])
        cfg.append(['H1', 24, "'              <MmbId>' + info.CdtrAgt_MmbId + '</MmbId>'",            '<!-- ABI Banca creditore -->'])
        cfg.append(['H1', 25, "'            </ClrSysMmbId>'"])
        cfg.append(['H1', 26, "'          </FinInstnId>'"])
        cfg.append(['H1', 27, "'        </CdtrAgt>'"])
        cfg.append(['H1', 28, "'        <CdtrSchmeId>'"])
        cfg.append(['H1', 29, "'          <Nm>' + info.CdtrSchmedId_Nm + '</Nm>'",                    '<!-- Ragione Sociale Creditore -->'])
        cfg.append(['H1', 30, "'          <Id>'"])
        cfg.append(['H1', 31, "'            <PrvtId>'"])
        cfg.append(['H1', 32, "'              <Othr>'"])
        cfg.append(['H1', 33, "'                <Id>' + info.CdtrSchmedId_Id + '</Id>'",              '<!-- Numero Identificativo Creditore -->' ])
        cfg.append(['H1', 34, "'              </Othr>'"])
        cfg.append(['H1', 35, "'            </PrvtId>'"])
        cfg.append(['H1', 36, "'          </Id>'"])
        cfg.append(['H1', 37, "'        </CdtrSchmeId>'"])
        cfg.append(['B1',  0, "'        <DrctDbtTxInf>'"])
        cfg.append(['B1',  1, "'          <PmtId>'"])
        cfg.append(['B1',  2, "'            <InstrId>' + info.InstrId + '</InstrId>'",                '<!-- Numero Progressivo effetto nella sottodistinta -->'])
        cfg.append(['B1',  3, "'            <EndToEndId>' + info.EndToEndId +'</EndToEndId>'",        '<!-- Identificativo univoco effetto nella sottodistinta -->' ])
        cfg.append(['B1',  4, "'          </PmtId>'"])
        cfg.append(['B1',  5, "'          <InstdAmt Ccy=" +'"EUR">' + "' + info.InstdAmt + '</InstdAmt>'", '<!-- Importo effetto -->' ])
        cfg.append(['B1',  6, "'          <DrctDbtTx>'"])
        cfg.append(['B1',  7, "'            <MndtRltdInf>'"])
        cfg.append(['B1',  8, "'              <MndtId>' + info.MndtId + '</MndtId>'", '<!-- Identificativo Univoco autorizzazione addebito -->' ])
        cfg.append(['B1',  9, "'              <DtOfSgntr>' + info.DtOfSgntr +'</DtOfSgntr>'", '<!-- Data autorizzazione addebito -->' ])
        cfg.append(['B1', 10, "'              <AmdmntInd>false</AmdmntInd>'"])
        cfg.append(['B1', 11, "'            </MndtRltdInf>'"])
        cfg.append(['B1', 12, "'          </DrctDbtTx>'"])
        cfg.append(['B1', 18, "'          <Dbtr>'"])
        cfg.append(['B1', 19, "'            <Nm>' + info.Dbtr_Nm + '</Nm>'", '<!-- Ragione Sociale Cliente Debitore -->' ])
        cfg.append(['B1', 20, "'          </Dbtr>'"])
        cfg.append(['B1', 21, "'          <DbtrAcct>'"])
        cfg.append(['B1', 22, "'            <Id>'"])
        cfg.append(['B1', 23, "'              <IBAN>' + info.DbtrAcct_IBAN + '</IBAN>'", '<!-- IBAN Cliente Debitore -->' ])
        cfg.append(['B1', 24, "'            </Id>'"])
        cfg.append(['B1', 25, "'          </DbtrAcct>'"])
        cfg.append(['B1', 26, "'          <Purp>'"])
        cfg.append(['B1', 27, "'            <Cd>GDSV</Cd>'"])
        cfg.append(['B1', 28, "'          </Purp>'"])
        cfg.append(['B1', 29, "'          <RgltryRptg>'"])
        cfg.append(['B1', 30, "'            <DbtCdtRptgInd>CRED</DbtCdtRptgInd>'"])
        cfg.append(['B1', 31, "'          </RgltryRptg>'"])
        cfg.append(['B1', 32, "'          <RmtInf>'"])
        cfg.append(['B1', 33, "'            <Ustrd>' + info.RmtInf_Ustrd +'</Ustrd>'", '<!-- Causale Descrittiva effetto -->' ])
        cfg.append(['B1', 34, "'          </RmtInf>'"])
        cfg.append(['B1', 35, "'        </DrctDbtTxInf>'"])
        cfg.append(['B2', 13, "'          <DbtrAgt>'"])
        cfg.append(['B2', 14, "'            <FinInstnId>'"])
        cfg.append(['B2', 15, "'              <BIC>NDEASESS</BIC>'"])
        cfg.append(['B2', 16, "'            </FinInstnId>'"])
        cfg.append(['B2', 17, "'          </DbtrAgt>'"])
        cfg.append(['F1', 1 , "'      </PmtInf>'"])
        cfg.append(['F ', 0 , "'    </CBISDDReqLogMsg>'"])
        cfg.append(['F ', 1 , "'  </CBIEnvelSDDReqLogMsg>'"])
        cfg.append(['F ', 2 , "'</CBIBdySDDReq>'"])

    if len(cfg)>0:
        ec = dbc.Env.Azienda.BaseTab.TABNAME_CFGEFF
        cfgTable = adb.DbTable(ec, "cfg")
        for r in cfg:
            cfgTable.CreateNewRow()
            cfgTable.tipo=tipo
            cfgTable.zona=r[0]
            cfgTable.riga=r[1]
            try:
                cfgTable.macro=r[2]+'+"'+r[3]+'"'
            except:
                cfgTable.macro=r[2]

            cfgTable.Save()



if __name__ == "__main__":
    db = adb.DB()
    db.Connect()
    eff = Eff()
    eff.Retrieve()
    print eff
    for e in eff:
        print e.id, e.datscad, e.numdoc, e.pdc.descriz, e.pdc.cli.indirizzo
