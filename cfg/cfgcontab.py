#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/cfgcontab.py
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

import MySQLdb

from awc.util import MsgDialog, MsgDialogDbError

from Env import Azienda, DateTime
bt = Azienda.BaseTab

import stormdb as adb


class CfgContab(adb.DbTable):
    
    def __init__(self):
        adb.DbTable.__init__(self, bt.TABNAME_CFGSETUP, 'setup')
    
    def _get_daymonth(self):
        k = {'gg': None,
             'mm': None}
        for key in k.keys():
            if self.Retrieve("setup.chiave='esercizio_start%s'" % key)\
               and self.OneRow():
                v = self.importo or 1
                if key == 'gg' and 1 <= v <= 31 or\
                   key == 'mm' and 1 <= v <= 12:
                    k[key] = int(v)
        gg = k['gg']
        mm = k['mm']
        return gg, mm
    
    def SetEsercizio(self, dataelab):
        yy = dataelab.year
        gg, mm = self._get_daymonth()
        if gg and mm:
            e = Azienda.Esercizio
            while True:
                d1 = DateTime.Date(yy, mm, gg)
                d2 = DateTime.Date(yy+1, mm, gg)-DateTime.DateTimeDelta(1)
                if dataelab < d1:
                    yy -= 1
                    continue
                e.start = d1
                e.end = d2
                e.year = yy
                e.dataElab = dataelab
                from awc.controls.datectrl import SetYearDefault
                SetYearDefault(dataelab.year)
                break
            return True
        return False
    
    def GetEsercizio(self, d, esepre=False):
        e = None
        gg, mm = self._get_daymonth()
        if gg and mm:
            e = Azienda.Esercizio
            if e.start <= d <= e.end:
                e = e.year
            elif d < e.start:
                yy = e.year-1
                d1 = DateTime.Date(yy, mm, gg)
                d2 = DateTime.Date(yy+1, mm, gg)-DateTime.DateTimeDelta(1)
                if d1 <= d <= d2:
                    e = yy
            if e and esepre:
                e -= 1
        return e
    
    def GetEsercizioDates(self, e):
        assert type(e) is int
        d1 = d2 = None
        gg, mm = self._get_daymonth()
        if gg and mm:
            d1 = DateTime.Date(e, mm, gg)
            d2 = DateTime.Date(e+1, mm, gg)-DateTime.DateTimeDelta(1)
        return d1, d2


# ------------------------------------------------------------------------------


class CfgCausale(object):
    """
    Configurazione causale contabile.
    """
    def __init__(self, curs):
        """
        Costruttore.
        C{CfgCausale.__init__(self, curs)}
        
        @param curs: cursore db
        @type curs: L{MySQLdb.Cursor}
        """
        self.db_curs = curs
        self.keys = ("id",           #Id causale
                     "codice",       #Codice causale
                     "descriz",      #Descrizione causale
                     "esercizio",    #Esercizio
                     "tipo",         #Tipologia
                     "datdoc",       #Data documento
                     "numdoc",       #Numero documento
                     "regiva_id",    #Id registro IVA
                     "regiva_cod",   #Codice registro IVA
                     "regiva_des",   #Descrizione registro IVA
                     "regiva_tipo",  #Tipo registro IVA
                     "regiva_dyn",   #Reg.IVA dinamico
                     "numiva",       #Numero registro IVA
                     "modpag",       #Modalità di pagamento
                     "pcf",          #Gestione partite clienti/fornitori
                     "pcfscon",      #Gestione saldaconto
                     "pcfimp",       #Importo/paregg. per saldaconto
                     "pcfsgn",       #Segno per saldaconto
                     "pcfabb",       #Gestione abbuono
                     "pcfspe",       #Gestione spese
                     "pcfins",       #Attiva flag insoluto
                     "pades",        #Descrizione partit
                     "pdctippa_id",  #Id sottoconto partita
                     "pdctippa_cod", #Codice sottoconto partita
                     "pdctippa_des", #Descrizione sottoconto partita
                     "pasegno",      #Segno contabile partita
                     "cpdes",        #Descrizione c/partit
                     "pdctipcp_id",  #Id sottoconto c/partita
                     "pdctipcp_cod", #Codice sottoconto c/partita
                     "pdctipcp_des", #Descrizione sottoconto c/partita
                     "id_pdcrow1",   #Sottoconto fisso riga 1
                     "camsegr1",     #Flag permesso cambio segno su riga 1
                     "quaivanob",    #Flag quadr. iva/dare-avere non bloccante
                     "davscorp",     #Flag colonna scorporo su dare/avere
                     "id_tipevent",  #ID Tipo evento
                     "event_msg",)   #Messaggio evento
        self.ResetConfig()

    def ResetConfig(self):
        """
        Reset configurazione.
        C{CfgCausale.ResetConfig(self)}
        """
        for key in self.keys:
            self.__setattr__("_cfg_%s" % key,  None)
        self._cfg_pdcpref = []
        self._cfg_pdcpref_da = {}

    def CfgCausale_Read(self, idcau):
        #lettura configurazione causale
        cmd =\
"""SELECT cau.id, cau.codice, cau.descriz, cau.esercizio, cau.tipo, """\
"""cau.datdoc, cau.numdoc, cau.id_regiva, riv.codice, riv.descriz, """\
"""riv.tipo, cau.regivadyn, cau.numiva, cau.modpag, cau.pcf, cau.pcfscon, cau.pcfimp, """\
"""cau.pcfsgn, cau.pcfabb, cau.pcfspe, cau.pcfins, cau.pades, """\
"""cau.id_pdctippa, pdcpa.codice, pdcpa.descriz, cau.pasegno, cau.cpdes, """\
"""cau.id_pdctipcp, pdccp.codice, pdccp.descriz, cau.id_pdcrow1, """\
"""cau.camsegr1, cau.quaivanob, cau.davscorp, cau.id_tipevent, cau.event_msg """\
"""FROM %s AS cau """\
"""LEFT JOIN %s AS riv ON cau.id_regiva=riv.id """\
"""LEFT JOIN %s AS pdcpa ON cau.id_pdctippa=pdcpa.id """\
"""LEFT JOIN %s AS pdccp ON cau.id_pdctipcp=pdccp.id """\
"""WHERE cau.id=%%s;""" % ( bt.TABNAME_CFGCONTAB,\
                            bt.TABNAME_REGIVA,\
                            bt.TABNAME_PDCTIP,\
                            bt.TABNAME_PDCTIP )
        try:
            self.db_curs.execute(cmd, idcau)
            rs = self.db_curs.fetchone()
        except MySQLdb.Error, e:
            MsgDialogDbError(None, e)
            self.ResetConfig()
        else:
            nkey = 0
            for key in self.keys:
                self.__setattr__("_cfg_%s" % key,  rs[nkey])
                nkey += 1
            del key, nkey
        #lettura sottoconti preferiti
        self._cfg_pdcpref = []
        self._cfg_pdcpref_da = {}
        cmd =\
"""SELECT id_pdc, segno """\
"""FROM %s AS pdcpref """\
"""WHERE ambito=1 AND key_id=%%s """\
"""ORDER BY pdcord""" % (bt.TABNAME_CFGPDCP,)
        try:
            self.db_curs.execute(cmd, idcau)
            rs = self.db_curs.fetchall()
        except MySQLdb.Error, e:
            MsgDialogDbError(None, e)
            self.ResetConfig()
        else:
            for r in rs:
                self._cfg_pdcpref.append(r[0])
                self._cfg_pdcpref_da[r[0]] = r[1] #segno


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    
    class _testApp(wx.App):
        
        def OnInit(self):
            wx.InitAllImageHandlers()
            Azienda.DB.testdb()
            return True
    
    app = _testApp(True)
    app.MainLoop()
    con = Azienda.DB.connection
    cur = con.cursor()
    cfg = CfgCausale(cur)
    cfg.CfgCausale_Read(14)
    for key,val in cfg.__dict__.iteritems():
        if key.startswith("_cfg_"):
            print "%s=%s" % (key, repr(val))
