#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/dbtables.py
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

import re
import socket
import base64


class Progressivi(adb.DbTable):
    fields = None
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr', writable=True)
        self.fields = ()
    
    def ReadKey(self, key, dif=None, fields=None):
        """
        Legge i progressivi della chiave specificata key.
        fields contiene l'elenco delle colonne da leggere, per default:
        'progrnum,progrdate,progrimp1,progrimp2'
        """
        assert type(key) in (str, unicode), 'Tipo chiave errato'
        assert len(key)>0, 'Chiave nulla'
        if fields is None:
            fields = 'progrnum,progrdate,progrimp1,progrimp2,progrdesc'.split(',')
        if type(fields) in (str, unicode):
            fields = fields.split(',')
        if dif is None:
            dif = Env.Azienda.Esercizio.year
        out = None
        if self.Retrieve('progr.codice=%s AND progr.keydiff=%s', key, dif)\
           and self.RowsCount() == 1:
            out = []
            for field in fields:
                out.append(getattr(self, field))
        self.fields = fields
        return out
    
    def GetFields(self):
        return self.fields
    
    def ReadKeyNumero(self, key):
        return self.ReadKey(key, 'progrnum')
    
    def ReadKeyData(self, key):
        return self.ReadKey(key, 'progdate')
    
    def ReadKeyValore1(self, key):
        return self.ReadKey(key, 'progrimp1')
    
    def ReadKeyValore2(self, key):
        return self.ReadKey(key, 'progrimp2')
    
    def SaveKey(self, key, dif=None, fields=None, values=None):
        assert fields is not None
        assert values is not None
        if type(fields) in (str, unicode):
            fields = fields.split(',')
        if dif is None:
            dif = Env.Azienda.Esercizio.year
        self.Reset()
        self.Retrieve('progr.codice=%s AND progr.keydiff=%s', key, dif)
        if self.RowsCount() == 0:
            self.CreateNewRow()
            self.codice = key
            self.keydiff = dif
        for field, value in zip(fields, values):
            setattr(self, field, value)
        return self.Save()


# ------------------------------------------------------------------------------


class ProgrEsercizio(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr', writable=True)
        self.AddBaseFilter('progr.codice=%s', 'ccg_esercizio')
        self.Reset()
        self.dbsetup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')
    
    def GetEsercizioInCorso(self):
        self.Retrieve()
        return int(self.progrnum or 0)
    
    def GetSovrapposizione(self):
        self.Retrieve()
        return bool(self.progrimp1 or 0)
    
    def GetMovimentiGenerati(self):
        self.Retrieve()
        return bool(self.progrimp2 or 0)
    
    def SetEsercizioInCorso(self, ec, sovrapp=None, movim=None):
        return self._SetParam(esercizio=ec, sovrapp=sovrapp)
    
    def SetSovrapposizione(self, sa, esercizio=None, movim=None):
        return self._SetParam(esercizio=esercizio, sovrapp=sa, movimenti=movim)
    
    def SetMovimentiGenerati(self, mg, esercizio=None, sovrapp=None):
        return self._SetParam(esercizio=esercizio, sovrapp=sovrapp, movimenti=mg)
    
    def _SetParam(self, esercizio=None, sovrapp=None, movimenti=None):
        self.Retrieve()
        if self.IsEmpty():
            self.CreateNewRow()
            self.codice = 'ccg_esercizio'
            self.descriz = 'Esercizio in corso e sovrapposizione attivata'
        if esercizio is not None:
            self.progrnum = int(esercizio)
        if sovrapp is not None:
            self.progrimp1 = int(sovrapp)
        if movimenti is not None:
            self.progrimp2 = int(movimenti)
        return self.Save()
    
    def _get_daymonth(self):
        k = {'gg': None,
             'mm': None}
        s = self.dbsetup
        for key in k.keys():
            if s.Retrieve("setup.chiave='esercizio_start%s'" % key)\
               and s.OneRow():
                v = s.importo or 1
                if key == 'gg' and 1 <= v <= 31 or\
                   key == 'mm' and 1 <= v <= 12:
                    k[key] = int(v)
        gg = k['gg']
        mm = k['mm']
        return gg, mm
    
    def GetEsercizioDates(self, e=None):
        if e is None:
            e = self.GetEsercizioInCorso()
        assert type(e) is int
        d1 = d2 = None
        gg, mm = self._get_daymonth()
        if gg and mm:
            d1 = Env.DateTime.Date(e, mm, gg)
            d2 = Env.DateTime.Date(e+1, mm, gg)-Env.DateTime.DateTimeDelta(1)
        return d1, d2
    
    def GetEsercizioDaData(self, data):
        e = None
        gg, mm = self._get_daymonth()
        if gg and mm:
            datini = Env.DateTime.Date(data.year, mm, gg)
            e = data.year
            if data<datini:
                e -= 1
        return e
    
    def SetDataChiusura(self):
        p = adb.DbTable(bt.TABNAME_CFGPROGR, 'progr')
        p.Retrieve('progr.codice=%s', 'ccg_chiusura')
        dc = p.progrdate
        p.Retrieve('progr.codice=%s', 'ccg_aggcon')
        if p.IsEmpty():
            p.CreateNewRow()
            p.codice = 'ccg_aggcon'
            p.descriz = 'Ultima chiusura contabile'
        p.progrdate = dc
        return p.Save()


# ------------------------------------------------------------------------------


class ProgrGiornaleDareAvere(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr', writable=True)
        self.AddBaseFilter("progr.codice IN ('ccg_giobol_ec', 'ccg_giobol_ep')")
        self.AddOrder('progr.codice')
        self.Reset()
    
    def AttivaSovrapposizione(self):
        self.Retrieve()
        t = {'ec': [0, 0, None],
             'ep': [0, 0, None]}
        for e in 'ec ep'.split():
            if self.Locate(lambda x: x.codice == ('ccg_giobol_%s' % e)):
                t[e][0] = self.progrimp1 or 0
                t[e][1] = self.progrimp2 or 0
                t[e][2] = self.RowNumber()
        if t['ec'][0] == 0 and t['ec'][1] == 0:
            raise Exception,\
                  "I progressivi dell'esercizio in corso sono vuoti"
        if t['ep'][0] or t['ep'][1]:
            raise Exception,\
                  "I progressivi dell'esercizio precedente non sono vuoti"
        if t['ep'][2] is None:
            self.CreateNewRow()
            self.codice = 'ccg_giobol_ep'
            self.descriz = 'Progressivi giornale bollato esercizio precedente'
            self.keydiff = '0'
        else:
            self.MoveRow(t['ep'][2])
        self.progrimp1 = t['ec'][0]
        self.progrimp2 = t['ec'][1]
        self.MoveRow(t['ec'][2])
        self.progrimp1 = 0
        self.progrimp2 = 0
        if self.Save():
            aggsta = adb.DbTable(bt.TABNAME_CFGPROGR, 'progr')
            aggsta.AddBaseFilter('codice="ccg_giobol"')
            aggsta.Retrieve()
            if aggsta.IsEmpty():
                aggsta.CreateNewRow()
                aggsta.codice = 'ccg_giobol'
                aggsta.descriz = 'Data e numero riga ultima stampa giornale'
            aggsta.progrnum = 0
            return aggsta.Save()
        return False
    
    def ChiudiSovrapposizione(self):
        return self.AzzeraProgressiviPrecedente()
    
    def AzzeraProgressiviPrecedente(self):
        return self._AzzeraProgressivi('ep')
    
    def AzzeraProgressiviInCorso(self):
        return self._AzzeraProgressivi('ec')
    
    def _AzzeraProgressivi(self, ecep):
        if self.Retrieve('codice=%s', 'ccg_giobol_%s' % ecep) and self.OneRow():
            self.progrimp1 = self.progrimp2 = 0
            return self.Save()
        return False


# ------------------------------------------------------------------------------


class ProgrStampaGiornale(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr', writable=True)
        self.AddBaseFilter("progr.codice=%s", 'ccg_giobol')
        self.AddOrder('progr.codice')
        self.Reset()
    
    def GetDataGiornale(self):
        dsg = None
        if self.Retrieve():
            dsg = self.progrdate
        return dsg
    
    def AzzeraProgressivi(self):
        self.Retrieve()
        if self.IsEmpty():
            self.CreateNewRow()
            self.codice = 'ccg_giobol'
            self.descriz = 'Progressivi Giornale Bollato'
            self.keydiff = '0'
        self.progrnum = None
        self.progrimp1 = None
        self.progrimp2 = None
        return self.Save()
    

# ------------------------------------------------------------------------------


class ProgrStampaMastri(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr', writable=True)
        self.AddBaseFilter('progr.codice=%s', 'ccg_giobol_stm')
        self.AddOrder('progr.keydiff', adb.ORDER_DESCENDING)
        self.Reset()
    
    def GetDataMastri(self, e):
        dsm = None
        if self.Retrieve('progr.keydiff=%s', e):
            dsm = self.progrdate
        return dsm
    
    def CreaEserciziMancanti(self):
        r = adb.DbTable(bt.TABNAME_CONTAB_H, 'reg', fields=None)
        r.Synthetize()
        r.AddGroupOn('reg.esercizio')
        r.AddOrder('reg.esercizio')
        r.Retrieve()
        self.Retrieve()
        a = False
        for r in r:
            if not self.Locate(lambda x: x.keydiff == str(r.esercizio).zfill(4)):
                self.CreateNewRow()
                self.codice = 'ccg_giobol_stm'
                self.descriz = 'Data stampa mastri per l\'esercizio %s' % r.esercizio
                self.keydiff = str(r.esercizio).zfill(4)
                a = True
        if a:
            rs = self.GetRecordset()
            c = self._GetFieldIndex('keydiff')
            rs2 = [[r[c], r ] for r in rs]
            rs2.sort(reverse=True)
            self.SetRecordset([r[1] for r in rs2])
            pass


# ------------------------------------------------------------------------------


class ProgrLiqIVA(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPROGR, 'progr', writable=True)
        self.Reset()
        self.dbsetup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')
    
    def GetUltimaLiquidazione(self, year=None):
        if year is None:
            year = Env.Azienda.Login.dataElab.year
        if not self.Retrieve('progr.codice="iva_debcred" AND progr.keydiff=%s', year) or self.IsEmpty():
            raise Exception, "Progressivi IVA non definiti per l'anno %d" % year
        c, d = self.progrimp1, 0
        if self.progrimp2<0:
            c, d = d, c
        return {'data':    self.progrdate,
                'credito': c,
                'debito':  d}
    
    def CreaProgressiviAnno(self, year):
        uliq = self.GetUltimaLiquidazione(year-1)
        d = uliq['data']
        if d is None:
            raise Exception, "Data ultima liquidazione non definita per l'anno %d" % (year-1)
        if d.month != 12 or d.day != 31:
            raise Exception, "Ultima liquidazione non al 31/12"
        #creo record per dati ultima liquidazione, vuoti
        cod = 'iva_debcred'
        self.Retrieve('progr.codice=%s AND progr.keydiff=%s', cod, year)
        if self.IsEmpty():
            self.CreateNewRow()
            self.codice = cod
            self.keydiff = year
            self.Save()
        #creo i 2 records per dati credito iva compensabile (inizio, disponibile)
        cred = uliq['credito']
        for name in 'start disp'.split():
            cod = 'iva_cricom%s' % name
            self.Retrieve('progr.codice=%s AND progr.keydiff=%s', cod, year)
            if self.IsEmpty():
                self.CreateNewRow()
                self.codice = cod
                self.keydiff = year
            self.progrimp1 = cred
            self.Save()


# ------------------------------------------------------------------------------


class Automat(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGAUTOM, 'aut')
    
    def GetAutomat(self, cod):
        self.Retrieve("aut.codice=%s", cod)
        return self.aut_id


# ------------------------------------------------------------------------------


class PermessiUtenti(adb.DbTable):
    
    _ambito = None
    _idrel = None
    
    def __init__(self, *args, **kwargs):
        if 'ambito' in kwargs:
            self.SetAmbito(kwargs.pop('ambito'))
        if 'idrel' in kwargs:
            self.SetIdRel(kwargs.pop('idrel'))
        adb.DbTable.__init__(self, bt.TABNAME_CFGPERM, 'perm')
    
    def CreateNewRow(self):
        out = adb.DbTable.CreateNewRow(self)
        if out:
            self.ambito = self._ambito
            self.id_rel = self._idrel
        return out
    
    def SetAmbito(self, ambito):
        self._ambito = ambito
    
    def GetAmbito(self):
        return self._ambito
    
    def SetIdRel(self, idrel):
        self._idrel = idrel
    
    def GetIdRel(self):
        return self._idrel
    
    def CheckRead(self, ambito=None, idrel=None):
        return self._CheckRW(ambito, idrel, 'leggi')
    
    def CheckWrite(self, ambito=None, idrel=None):
        return self._CheckRW(ambito, idrel, 'scrivi')
    
    def _CheckRW(self, ambito=None, idrel=None, tipo=None):
        if ambito is None: ambito = self._ambito
        if idrel is None: idrel = self._idrel
        assert ambito is not None
        assert idrel is not None
        assert tipo in 'leggi scrivi'.split()
        self.Retrieve("perm.ambito=%s AND perm.id_rel=%s AND perm.id_utente=%s",
                      ambito, idrel, Env.Azienda.Login.userid)
        return getattr(self, tipo) == 1


# ------------------------------------------------------------------------------


class PdcPrefTable(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGPDCP, 'pcp')
        self.AddJoin(bt.TABNAME_PDC)
        self.AddOrder("pcp.pdcord")
        self.Reset()


# ------------------------------------------------------------------------------


class EventiStdCallbacks:
    
    def __init__(*x):
        pass
    
    def start(*x):
        pass
    
    def stop(*x): 
        pass


# ------------------------------------------------------------------------------


class EventiTable(adb.DbTable):
    
    _notified_email = False
    _notified_xmpp = False
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_EVENTI, 'eventi')
        tip = self.AddJoin(  bt.TABNAME_TIPEVENT,     'tipevent')
        self.AddOrder('eventi.data_evento')
        self.Reset()
    
    def CreateNewRow(self):
        out = adb.DbTable.CreateNewRow(self)
        if out:
            name = socket.getfqdn()
            name, alias, addr = socket.gethostbyname_ex(name)
            self.wksname = name
            self.wksaddr = ', '.join(addr or [])
            self.notified_email = 0
            self.notified_xmpp = 0
        return out
    
    def ParseContent(self, s2p, dbt, wc='RS'):
        ps = s2p
        if ps and dbt:
            if not wc.endswith('.'):
                wc += '.'
            while True:
                #m = re.search("{([A-Za-z0-9.]+)}", ps)
                m = re.search("{(.+)}", ps)
                if m:
                    g = m.groups()
                    if g:
                        exp = g[0].replace(wc, 'dbt.')
                        try:
                            val = eval(exp)
                        except Exception, e:
                            val = repr(e.args)
                        n1, n2 = m.start(), m.end()
                        ps = ps[:n1] + str(val) + ps[n2:]
                else:
                    break
        return ps
    
    def Notify(self, callbacks=None, owner=None, byemail=True, byxmpp=True, plusmsg=""):
        
        if not bt.OPTNOTIFICHE:
            return True
        
        if callbacks is None: 
            callbacks = {}
        
        out = False
        
        if byemail and self.tipevent.notify_emailto:
            n = callbacks.get('mail', EventiStdCallbacks)(owner)
            n.start('Invio email di notifica in corso')
            out |= self.NotifyByEmail(plusmsg=plusmsg)
            n.stop()
        
        if byxmpp and self.tipevent.notify_xmppto:
            n = callbacks.get('xmpp', EventiStdCallbacks)(owner)
            n.start('Invio messaggio istantaneo di notifica in corso')
            out |= self.NotifyByXmpp(plusmsg=plusmsg)
            n.stop()
        
        return out
    
    def GetNotifyStatus(self):
        return {'mail': self._notified_email,
                'xmpp': self._notified_xmpp}
    
    def NotifyByEmail(self, plusmsg=""):
        if not bt.OPTNOTIFICHE: 
            return True
        from comm.comsmtp import SendMail
        self.notified_email = 0
        self.notifieddemail = None
        s = SendMail()
        subj = "Notifica evento X4: %s%s" % (self.tipevent.descriz, plusmsg)
        if s.send(Subject=subj,
                  Message=self.dettaglio,
                  SendTo=self.tipevent.notify_emailto.split(";")):
            self.notified_email = 1
            self.notifieddemail = Env.DateTime.now()
            return True
        raise Exception, repr(s.get_error())
    
    def NotifyByXmpp(self, plusmsg=""):
        if not bt.OPTNOTIFICHE: 
            return True
        from comm.comxmpp import NotifyClient
        self.notified_xmpp = 0
        self.notifieddxmpp = None
        s = NotifyClient()
        msg = "Notifica evento X4: %s%s\n\n%s" % (self.tipevent.descriz, plusmsg, self.dettaglio)
        if s.connect_and_sendto(self.tipevent.notify_xmppto, msg):
            self.notified_xmpp = 1
            self.notifieddxmpp = Env.DateTime.now()
            return True
        if s.get_error():
            raise Exception, repr(s.get_error())
        del s
        return False


# ------------------------------------------------------------------------------


class EmailConfigTable(adb.DbTable):
    
    _tabname = 'x4.cfgmail'
    
    def __init__(self):
        adb.DbTable.__init__(self, self._tabname, 'setup')
        self.AddBaseFilter('setup.azienda=%s', Env.Azienda.codice)
        self.Retrieve()
    
    def GetAuthPassword(self):
        return base64.b64decode(self.authpswd or '')


# ------------------------------------------------------------------------------


class XmppConfigTable(EmailConfigTable):
    _tabname = 'x4.cfgxmpp'


# ------------------------------------------------------------------------------


class BilancioCeeTable(adb.DbTable):
    
    def __init__(self, *args, **kwargs):
        adb.DbTable.__init__(self, 'x4.bilcee', 'bilcee')
        self.AddOrder('bilcee.sezione')
        self.AddOrder('bilcee.voce')
        self.AddOrder('bilcee.capitolo')
        self.AddOrder('bilcee.dettaglio')
        self.AddOrder('bilcee.subdett')
        self.Reset()
        self._info.dbcee = adb.DbTable(self.GetTableName(),
                                       self.GetTableAlias())
    
    def GetDescrizOf(self, field, codcee=None):
        out = ''
        if codcee is None:
            codcee = self.codice
        if codcee is None:
            codcee = ''
        parts = {'sezione':   1,
                 'voce':      2,
                 'capitolo':  6,
                 'dettaglio': 8,
                 'subdett':   9}
        assert field in parts
        key = str((codcee or '')).ljust(9)[:parts[field]]
        cee = self._info.dbcee
        if cee.Retrieve('bilcee.codice=%s', key) and cee.OneRow():
            out = cee.descriz
            if field == 'sezione':
                if key in '123':
                    out = 'STATO PATRIMONIALE - %s' % out
                elif key == '4':
                    out = 'CONTO ECONOMICO - %s' % self.GetDescrizOf('voce', codcee)
        return out
    
    def GetRaggrKey(self, codcee=None):
        if codcee is None:
            codcee = self.codice
        if codcee is None:
            codcee = ''
        sez = codcee[0] or ' '
        if sez in '123':
            key = sez
        elif sez == '4':
            key = codcee[:2]
        else:
            key = '?'
        return key


# ------------------------------------------------------------------------------


class StatiTable(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, 'x4.stati', 'stati')
        self.AddOrder('stati.codice')
        self.Reset()
