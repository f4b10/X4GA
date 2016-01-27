#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         contab/scad.py
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

import lib
dt = lib.DateTime

import MySQLdb

import Env
bt = Env.Azienda.BaseTab

import awc.util as util


class Scadenze(object):
    """
    Calcoli per scadenzari.
    """
    def __init__(self, db_curs):
        """
        @param db_curs: Cursore di database
        @type db_curs: MySQLdb.Cursor
        """
        self.db_curs = db_curs
        self.mp_id = None
        self.mp_codice = None
        self.mp_descriz = None
        self.mp_tipo = None
        self.mp_contrass = None
        self.mp_modocalc = None
        self.mp_finemese0 = None
        self.mp_finemese = None
        self.mp_numscad = None
        self.mp_mesi1 = None
        self.mp_mesitra = None
        self.mp_id_pdcpi = None
        self.mp_sc1noeff = None
        self.mp_sc1iva = None
        self.mp_sc1perc = None
        self.mp_gg = None
        self.mp_pdcpi_cod = None
        self.mp_pdcpi_des = None

    def SetupModPag(self, id_modpag):
        """
        Calcola le scadenze di pagamento.

        @param datestart: data di partenza (data documento)
        @type datestart: date
        @param id_modpag: id modalità di pagamento
        @type id_modpag: int
        @param impot: importo totale (tot. documento)

        @return: elenco scadenze con data e importo
        @rtype: nscad-tuple di 2-tuple (data scadenza, importo)
        """
        self.mp_id = None
        self.mp_codice = None
        self.mp_descriz = None
        self.mp_tipo = None
        self.mp_contrass = None
        self.mp_modocalc = None
        self.mp_finemese0 = None
        self.mp_finemese = None
        self.mp_numscad = None
        self.mp_mesi1 = None
        self.mp_mesitra = None
        self.mp_id_pdcpi = None
        self.mp_sc1noeff = None
        self.mp_sc1iva = None
        self.mp_sc1perc = None
        self.mp_ggextra = None
        self.mp_gg = None
        self.mp_gem = None

        if id_modpag is None:
            return
        cmd =\
"""SELECT mp.codice, mp.descriz, mp.tipo, mp.contrass, mp.modocalc, """\
"""mp.tipoper, mp.finemese0, mp.finemese, mp.numscad, mp.mesi1, mp.mesitra, mp.id_pdcpi, """\
"""mp.sc1noeff, mp.sc1iva, mp.sc1perc, mp.ggextra, """\
"""mp.gg01, mp.gg02, mp.gg03, mp.gg04, mp.gg05, mp.gg06, mp.gg07, mp.gg08, mp.gg09, mp.gg10, mp.gg11, mp.gg12,"""\
"""mp.gg13, mp.gg14, mp.gg15, mp.gg16, mp.gg17, mp.gg18, mp.gg19, mp.gg20, mp.gg21, mp.gg22, mp.gg23, mp.gg24,"""\
"""mp.gg25, mp.gg26, mp.gg27, mp.gg28, mp.gg29, mp.gg30, mp.gg31, mp.gg32, mp.gg33, mp.gg34, mp.gg35, mp.gg36,"""\
"""mp.gem01, mp.gem02, mp.gem03, mp.gem04, mp.gem05, mp.gem06, mp.gem07, mp.gem08, mp.gem09, mp.gem10, mp.gem11, mp.gem12 """\
"""FROM %s AS mp """\
"""WHERE mp.id=%%s""" % bt.TABNAME_MODPAG
        try:
            self.db_curs.execute(cmd, id_modpag)
            rsmp = self.db_curs.fetchone()
        except MySQLdb.Error, e:
            util.MsgDialogDbError(None, e)
        else:
            self.mp_id = id_modpag
            self.mp_codice,\
            self.mp_descriz,\
            self.mp_tipo,\
            self.mp_contrass,\
            self.mp_modocalc,\
            self.mp_tipoper,\
            self.mp_finemese0,\
            self.mp_finemese,\
            self.mp_numscad,\
            self.mp_mesi1,\
            self.mp_mesitra,\
            self.mp_id_pdcpi,\
            self.mp_sc1noeff,\
            self.mp_sc1iva,\
            self.mp_sc1perc,\
            self.mp_ggextra = rsmp[:16]
            self.mp_finemese0 = self.mp_finemese0 or False
            self.mp_finemese = self.mp_finemese or False
            self.mp_sc1noeff = self.mp_sc1noeff or False
            if self.mp_numscad is None: self.mp_numscad = 0
            if self.mp_mesi1 is None:   self.mp_mesi1 = 0
            if self.mp_mesitra is None: self.mp_mesitra = 0
            self.mp_gg = []
            mp_gg = rsmp[16:53]
            for gg in mp_gg:
                self.mp_gg.append(gg or 0)
            self.mp_gem = []
            mp_gem = rsmp[52:65]
            for gem in mp_gem:
                self.mp_gem.append(gem or 0)
        if self.mp_id_pdcpi:
            cmd = \
                """SELECT pdc.codice, pdc.descriz """\
                """FROM %s AS pdc """\
                """WHERE pdc.id=%%s""" % bt.TABNAME_PDC
            try:
                self.db_curs.execute(cmd, self.mp_id_pdcpi)
                rs = self.db_curs.fetchone()
            except:
                rs = (None, None)
            self.mp_pdcpi_cod = rs[0]
            self.mp_pdcpi_des = rs[1]
        else:
            self.mp_pdcpi_cod = None
            self.mp_pdcpi_des = None

    def CalcolaScadenze(self, datestart, id_modpag, imptot = 0, impiva = 0):
        """
        Calcola le scadenze di pagamento.

        @param datestart: data di partenza (data documento)
        @type datestart: date
        @param id_modpag: id modalità di pagamento
        @type id_modpag: int
        @param imptot: importo totale (tot. documento)
        @type imptot: float
        @param impiva: importo iva
        @type imptot: float

        @return: elenco scadenze con data e importo
        @rtype: nscad-tuple di 4-tuple (data scadenza, importo, isriba, iscontrass)
        """
        scad = []

        if id_modpag != self.mp_id:
            self.SetupModPag(id_modpag)

        NDEC = bt.VALINT_DECIMALS

        if id_modpag and datestart and self.mp_id_pdcpi is None:

            dscad = datestart
            if self.mp_finemese0:
                dscad += dscad.GetDaysInMonth() - dscad.day

            for numsca in range(self.mp_numscad):

                riba = 0
                cass = 0

                #determino il periodo da aggiungere alla data precedente
                if self.mp_modocalc == "S":
                    if numsca == 0:
                        periodi = self.mp_mesi1
                    else:
                        periodi = self.mp_mesitra
                elif self.mp_modocalc == "D":
                    periodi = self.mp_gg[numsca]

                #aggiungo il periodo alla data precedente
                if self.mp_tipoper == "M":
                    dscad = lib.AddMonths(dscad, periodi)
                elif self.mp_tipoper == "G":
                    dscad += dt.DateTimeDelta(days = periodi)
                if self.mp_finemese == 1:
                    dscad += dscad.GetDaysInMonth() - dscad.day

                #determino se la mp è una riba
                if self.mp_tipo == "R":
                    riba = 1

                #determino se la mp è un contrassegno
                if self.mp_contrass:
                    cass = 1

                #determino importo ed esclusione effetto su prima scadenza
                imp = 0
                if numsca == 0:
                    if self.mp_sc1iva:
                        imp = round(impiva, NDEC)
                    elif self.mp_sc1perc:
                        imp = round(imptot/100*self.mp_sc1perc, NDEC)
                    if self.mp_sc1noeff:
                        riba = 0
                ggextra = self.mp_gem[dscad.month-1] or self.mp_ggextra or 0
                scad.append([dscad+ggextra, imp, riba, cass])

            if scad:
                ripn = 0
                ripv = imptot
                for s in scad:
                    if s[1]:
                        ripv -= s[1]
                    else:
                        ripn += 1
                ripr = round(ripv/ripn, NDEC)
                total = 0
                for s in scad:
                    if not s[1]: s[1] = ripr
                    total = round(total+s[1], NDEC)
                if total != imptot:
                    scad[len(scad)-1][1] =\
                        round(scad[len(scad)-1][1]+(imptot-total), NDEC)

        elif id_modpag is None:
            #se la mod.pag. è vuota, genera cmq una scadenza in data documento
            #o data elaborazione se data doc. vuota (che non dovrebbe accadere)
            dscad = datestart
            if dscad is None:
                dscad = Env.Azienda.Login.dataElab
            scad.append([dscad, imptot, 0, 0])

        return scad


# ------------------------------------------------------------------------------


import stormdb as adb

class Scadenze_Table(adb.DbTable):
    """
    Calcoli per scadenzari.
    """
    def __init__(self, **kwargs):
        adb.DbTable.__init__(self, bt.TABNAME_MODPAG, 'modpag', **kwargs)
        self.mp_id = None
        self.mp_codice = None
        self.mp_descriz = None
        self.mp_tipo = None
        self.mp_contrass = None
        self.mp_modocalc = None
        self.mp_finemese0 = None
        self.mp_finemese = None
        self.mp_numscad = None
        self.mp_mesi1 = None
        self.mp_mesitra = None
        self.mp_id_pdcpi = None
        self.mp_sc1noeff = None
        self.mp_sc1iva = None
        self.mp_sc1perc = None
        self.mp_gg = None
        self.mp_pdcpi_cod = None
        self.mp_pdcpi_des = None

    def SetupModPag(self, id_modpag):
        """
        Calcola le scadenze di pagamento.

        @param datestart: data di partenza (data documento)
        @type datestart: date
        @param id_modpag: id modalità di pagamento
        @type id_modpag: int
        @param impot: importo totale (tot. documento)

        @return: elenco scadenze con data e importo
        @rtype: nscad-tuple di 2-tuple (data scadenza, importo)
        """
        self.mp_id = None
        self.mp_codice = None
        self.mp_descriz = None
        self.mp_tipo = None
        self.mp_contrass = None
        self.mp_modocalc = None
        self.mp_finemese0 = None
        self.mp_finemese = None
        self.mp_numscad = None
        self.mp_mesi1 = None
        self.mp_mesitra = None
        self.mp_id_pdcpi = None
        self.mp_sc1noeff = None
        self.mp_sc1iva = None
        self.mp_sc1perc = None
        self.mp_ggextra = None
        self.mp_gg = None
        self.mp_gem = None

        if id_modpag is None:
            return
        cmd =\
"""SELECT mp.codice, mp.descriz, mp.tipo, mp.contrass, mp.modocalc, """\
"""mp.tipoper, mp.finemese0, mp.finemese, mp.numscad, mp.mesi1, mp.mesitra, mp.id_pdcpi, """\
"""mp.sc1noeff, mp.sc1iva, mp.sc1perc, mp.ggextra, """\
"""mp.gg01, mp.gg02, mp.gg03, mp.gg04, mp.gg05, mp.gg06, mp.gg07, mp.gg08, mp.gg09, mp.gg10, mp.gg11, mp.gg12,"""\
"""mp.gg13, mp.gg14, mp.gg15, mp.gg16, mp.gg17, mp.gg18, mp.gg19, mp.gg20, mp.gg21, mp.gg22, mp.gg23, mp.gg24,"""\
"""mp.gg25, mp.gg26, mp.gg27, mp.gg28, mp.gg29, mp.gg30, mp.gg31, mp.gg32, mp.gg33, mp.gg34, mp.gg35, mp.gg36,"""\
"""mp.gem01, mp.gem02, mp.gem03, mp.gem04, mp.gem05, mp.gem06, mp.gem07, mp.gem08, mp.gem09, mp.gem10, mp.gem11, mp.gem12 """\
"""FROM %s AS mp """\
"""WHERE mp.id=%%s""" % bt.TABNAME_MODPAG
        try:
            self._info.db.Retrieve(cmd, (id_modpag,))
            rsmp = self._info.db.rs[0]
        except MySQLdb.Error, e:
            util.MsgDialogDbError(None, e)
        else:
            self.mp_id = id_modpag
            self.mp_codice,\
            self.mp_descriz,\
            self.mp_tipo,\
            self.mp_contrass,\
            self.mp_modocalc,\
            self.mp_tipoper,\
            self.mp_finemese0,\
            self.mp_finemese,\
            self.mp_numscad,\
            self.mp_mesi1,\
            self.mp_mesitra,\
            self.mp_id_pdcpi,\
            self.mp_sc1noeff,\
            self.mp_sc1iva,\
            self.mp_sc1perc,\
            self.mp_ggextra = rsmp[:16]
            self.mp_finemese0 = self.mp_finemese0 or False
            self.mp_finemese = self.mp_finemese or False
            self.mp_sc1noeff = self.mp_sc1noeff or False
            if self.mp_numscad is None: self.mp_numscad = 0
            if self.mp_mesi1 is None:   self.mp_mesi1 = 0
            if self.mp_mesitra is None: self.mp_mesitra = 0
            self.mp_gg = []
            mp_gg = rsmp[16:53]
            for gg in mp_gg:
                self.mp_gg.append(gg or 0)
            self.mp_gem = []
            mp_gem = rsmp[52:65]
            for gem in mp_gem:
                self.mp_gem.append(gem or 0)
        self.mp_pdcpi_cod = None
        self.mp_pdcpi_des = None
        if self.mp_id_pdcpi:
            cmd = \
                """SELECT pdc.codice, pdc.descriz """\
                """FROM %s AS pdc """\
                """WHERE pdc.id=%%s""" % bt.TABNAME_PDC
            try:
                pdc = adb.DbTable(bt.TABNAME_PDC, 'pdc')
                pdc.Get(self.mp_id_pdcpi)
                self.mp_pdcpi_cod = pdc.codice
                self.mp_pdcpi_des = pdc.descriz
            except:
                pass

    def CalcolaScadenze(self, datestart, id_modpag, imptot = 0, impiva = 0):
        """
        Calcola le scadenze di pagamento.

        @param datestart: data di partenza (data documento)
        @type datestart: date
        @param id_modpag: id modalità di pagamento
        @type id_modpag: int
        @param imptot: importo totale (tot. documento)
        @type imptot: float
        @param impiva: importo iva
        @type imptot: float

        @return: elenco scadenze con data e importo
        @rtype: nscad-tuple di 4-tuple (data scadenza, importo, isriba, iscontrass)
        """
        scad = []

        if id_modpag != self.mp_id:
            self.SetupModPag(id_modpag)

        NDEC = bt.VALINT_DECIMALS

        if id_modpag and datestart and self.mp_id_pdcpi is None:

            dscad = datestart
            if self.mp_finemese0:
                dscad += dscad.GetDaysInMonth() - dscad.day

            for numsca in range(self.mp_numscad):

                riba = 0
                cass = 0

                #determino il periodo da aggiungere alla data precedente
                if self.mp_modocalc == "S":
                    if numsca == 0:
                        periodi = self.mp_mesi1
                    else:
                        periodi = self.mp_mesitra
                elif self.mp_modocalc == "D":
                    periodi = self.mp_gg[numsca]

                #aggiungo il periodo alla data precedente
                if self.mp_tipoper == "M":
                    dscad = lib.AddMonths(dscad, periodi)
                elif self.mp_tipoper == "G":
                    dscad += dt.DateTimeDelta(days = periodi)
                if self.mp_finemese == 1:
                    dscad += dscad.GetDaysInMonth() - dscad.day

                #determino se la mp è una riba
                if self.mp_tipo == "R":
                    riba = 1
                #determino se la mp è un SDD
                elif self.mp_tipo == 'S':
                    riba = 2
                #determino se la mp è un contrassegno
                if self.mp_contrass:
                    cass = 1

                #determino importo ed esclusione effetto su prima scadenza
                imp = 0
                if numsca == 0:
                    if self.mp_sc1iva:
                        imp = round(impiva, NDEC)
                    elif self.mp_sc1perc:
                        imp = round(imptot/100*self.mp_sc1perc, NDEC)
                    if self.mp_sc1noeff:
                        riba = 0
                ggextra = self.mp_gem[dscad.month-1] or self.mp_ggextra or 0
                scad.append([dscad+ggextra, imp, riba, cass])

            if scad:
                ripn = 0
                ripv = imptot
                for s in scad:
                    if s[1]:
                        ripv -= s[1]
                    else:
                        ripn += 1
                ripr = round(ripv/ripn, NDEC)
                total = 0
                for s in scad:
                    if not s[1]: s[1] = ripr
                    total = round(total+s[1], NDEC)
                if total != imptot:
                    scad[len(scad)-1][1] =\
                        round(scad[len(scad)-1][1]+(imptot-total), NDEC)

        elif id_modpag is None:
            #se la mod.pag. è vuota, genera cmq una scadenza in data documento
            #o data elaborazione se data doc. vuota (che non dovrebbe accadere)
            dscad = datestart
            if dscad is None:
                dscad = Env.Azienda.Login.dataElab
            scad.append([dscad, imptot, 0, 0])

        return scad


# ------------------------------------------------------------------------------


if __name__ == "__main__":
    import locale
    locale.setlocale(locale.LC_ALL, 'it')
    date = lib.DateTime.today()
    Env.Azienda.DB.testdb()
    con = Env.Azienda.DB.connection
    cur = con.cursor()
    try:
        cur.execute("SELECT id, codice, descriz FROM modpag ORDER BY codice")
        rsmp = cur.fetchall()
    except MySQLdb.Error, e:
        print "Errore %d - %s" % (e.args[0], e.args[1])
    else:
        space = lambda x: " "*x
        scad = Scadenze(cur)
        for mp in rsmp:
            scad.SetupModPag(mp[0])
            x = scad.CalcolaScadenze(date, mp[0], 1000.00)
            row = ("%s %s:" % (mp[1], mp[2]) + space(20))[:21]
            if x:
                row += "%d\t" % x[0][1]
            for d,i in x:
                row += (d.Format().split()[0]+space(12))[:13]
            print row
