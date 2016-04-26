#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/azisetup.py
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
import Env
bt = Env.Azienda.BaseTab

import awc.controls.windows as aw
import awc.controls.radiobox as awradio
import awc.controls.checkbox as awcheck
import awc.controls.linktable as lt
from awc.controls.numctrl import NumCtrl
from awc.controls.datectrl import DateCtrl

import cfg.azisetup_wdr as wdr
import stormdb as adb

from cfg.cfgcontab import CfgContab

import os
import lib
import os
import shutil
import stat



import crypt, base64


def _mkdir_recursive(path):
    sub_path = os.path.dirname(path)
    if not os.path.exists(sub_path):
        _mkdir_recursive(sub_path)
    if not os.path.exists(path):
        os.mkdir(path)


FRAME_TITLE = "Setup azienda"


class _SetupPanel(aw.Panel):

    def __init__(self, *args, **kwargs):
        aw.Panel.__init__(self, *args, **kwargs)
        self.dbsetup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup')

    def EncodeValue(self, value, name, is_pswd=False):
        if is_pswd:
            c = crypt.encrypt_data(str(value))
            enc = base64.b64encode(c)
            return enc
        return value

    def DecodeValue(self, value, name, is_pswd=False):
        if is_pswd:
            try:
                dec = base64.b64decode(value)
                d = crypt.decrypt_data(dec)
                return d
            except:
                pass
        return value

    def SetupRead(self):
        db = self.dbsetup
        cn = self.FindWindowByName
        for ctr in aw.awu.GetAllChildrens(self):
            if ctr.GetName()[:6] == 'setup_':
                name = ctr.GetName()[6:]
                if db.Retrieve('setup.chiave=%s', name) and db.RowsCount() == 1:
                    if isinstance(ctr, (awradio.RadioBox, awcheck.CheckBox)):
                        val = db.flag
                    elif isinstance(ctr, (int, long, lt.LinkTable, NumCtrl, wx.Choice)):
                        val = db.importo
                    elif isinstance(ctr, DateCtrl):
                        val = db.data
                    else:
                        val = self.DecodeValue(db.descriz, name, ctr.GetWindowStyle() & wx.TE_PASSWORD == wx.TE_PASSWORD)
                    ctr.SetValue(val)

    def SetupWrite(self):

        out = True
        db = self.dbsetup
        cn = self.FindWindowByName

        for ctr in aw.awu.GetAllChildrens(self):
            name = ctr.GetName()
            if name[:6] == 'setup_':
                val = cn(name).GetValue()
                name = ctr.GetName()[6:]
                if db.Retrieve('setup.chiave=%s', name):
                    if db.RowsCount() == 0:
                        db.CreateNewRow()
                        db.chiave = name
                    if isinstance(ctr, (awradio.RadioBox, awcheck.CheckBox)):
                        db.flag = val
                    elif isinstance(ctr, (int, long, lt.LinkTable, NumCtrl, wx.Choice)):
                        db.importo = val
                    elif isinstance(ctr, DateCtrl):
                        db.data = val
                    else:
                        db.descriz = self.EncodeValue(val, name, ctr.GetWindowStyle() & wx.TE_PASSWORD == wx.TE_PASSWORD)
                    if not db.Save():
                        aw.awu.MsgDialog(self, message="Problema in aggiornamento setup:\n%s" % repr(db.GetError()))
                        out = False
                        break
                else:
                    aw.awu.MsgDialog(self, message="Problema in lettura setup:\n%s" % db.GetError())
                    out = False
                    break

        import lib
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)

        return out

    def OnConfirm(self, event):
        if self.Validate():
            if self.SetupWrite():
                if bt.SYNCFLAG==1 and bt.SYNCTIPOSERVER=='M':
                    self.UpdateDirStru()
                event.Skip()


    def UpdateDirStru(self):
        import shutil
        def del_rw(action, name, exc):
            os.chmod(name, stat.S_IWRITE)
            os.remove(name)
        newDestinatari=self.FindWindowByName('setup_syncDestinatari').GetValue().split('|')
        oldDestinatari=self.oldDestinatari.split('|')
        userPath=os.path.join(self.FindWindowByName('setup_syncWrkDir').GetValue(), 'DA_SEDE', 'USERSYNC')
        if not os.path.exists(userPath):
            self._mkdir_recursive(userPath)
        if os.path.exists(userPath):
            L=[os.path.join(userPath,o) for o in os.listdir(userPath) if os.path.isdir(os.path.join(userPath,o))]
            for d in L:
                u='%s' % int(os.path.split(d)[1].strip())
                if not u in newDestinatari:
                    shutil.rmtree(d, onerror=del_rw)
            for r in newDestinatari:
                if len(r)>0:
                    wrkPath=os.path.join(userPath, '%03d' % int(r))
                    if not os.path.exists(wrkPath):
                        self._mkdir_recursive(wrkPath)

    def _mkdir_recursive(self, path):
        sub_path = os.path.dirname(path)
        if not os.path.exists(sub_path):
            self._mkdir_recursive(sub_path)
        if not os.path.exists(path):
            os.mkdir(path)

    def Validate(self):
        raise Exception, 'Classe non istanziabile'


# ------------------------------------------------------------------------------


class AziendaSetupPanel(_SetupPanel):
    """
    Impostazione setup azienda.
    """

    def __init__(self, *args, **kwargs):

        _SetupPanel.__init__(self, *args, **kwargs)
        wdr.AziendaSetup(self)
        cn = lambda x: self.FindWindowByName(x)
        for name, vals in (('tipo_contab',     'OS'),
                           ('liqiva_periodic', 'MT'),
                           ('syncTipoServer', 'MS'),):
            name = 'setup_'+name
            cn(name).SetDataLink(name, list(vals))
        self.SetupRead()


        self.oldDestinatari=cn('setup_syncDestinatari').GetValue()

        self.AttivaSyncCtrl(cn('setup_syncflag').GetValue())
        self.AttivaServerCtrl(cn('setup_syncTipoServer').GetValue()=='M')

        self.Bind(wx.EVT_BUTTON, self.OnConfirm, id=wdr.ID_BTNOK)
        cn('setup_syncflag').Bind(wx.EVT_CHECKBOX, self.OnAttivaSync)
        cn('setup_syncTipoServer').Bind(wx.EVT_RADIOBOX , self.OnAttivaServer)


    def OnAttivaServer(self, evt):
        self.AttivaServerCtrl(self.FindWindowByName('setup_syncTipoServer').GetValue()=='M')
        evt.Skip()

    def AttivaServerCtrl(self, value=None):
        for n in [ 'setup_syncDestinatari', 'setup_syncTabelle']:
            self.FindWindowByName(n).Enable(value)

    def OnAttivaSync(self, evt):
        self.AttivaSyncCtrl(evt.IsChecked())
        evt.Skip()

    def AttivaSyncCtrl(self, value=None):
        for ctr in aw.awu.GetAllChildrens(self):
            name=ctr.GetName()
            if name[:6] == 'setup_':
                if ctr.GetName()[6:10] and not name=='setup_syncflag':
                    ctr.Enable(value)



    def SetupRead(self):
        out = _SetupPanel.SetupRead(self)
        cn = self.FindWindowByName
        cn('setup_consovges').SetValue(bt.CONSOVGES) #il flag è numerico, ma memorizzato in setup.flag che è carattere
        logo = os.path.join(self.GetLogoPath(), self.GetLogoFileName())
        if os.path.isfile(logo):
            cn('azienda_logo').display_image(logo)
        return out

    def SetupWrite(self):

        cn = self.FindWindowByName
        out = _SetupPanel.SetupWrite(self)

        if out:
            #aggiornamento ragione sociale su db aziende
            out = False
            cod = Env.Azienda.codice
            host = Env.Azienda.DB.servername
            user = Env.Azienda.DB.username
            pswd = Env.Azienda.DB.password
            dba = adb.db.DB(dbType=getattr(adb.db.__database__, '_dbType'), globalConnection=False)
            if dba.Connect(host=host, user=user, passwd=pswd, db='x4'):
                dbz = adb.DbTable('aziende', 'azi', db=dba)
                if dbz.Retrieve('azi.codice=%s', cod):
                    if dbz.RowsCount() == 1:
                        dbz.codice = Env.Azienda.codice = cn('setup_azienda_codice').GetValue()
                        dbz.azienda = Env.Azienda.descrizione = cn('setup_azienda_ragsoc').GetValue()
                        if dbz.Save():
                            out = True
                        else:
                            aw.awu.MsgDialog(self, message="Problema in fase di aggiornamento della tabella aziende:\n%s" % repr(dbz.GetError()))
                    else:
                        aw.awu.MsgDialog(self, message="Codice '%s' non trovato su tabella aziende" % cod)
                else:
                    aw.awu.MsgDialog(self, message="Problema in fase di aggiornamento della tabella aziende:\n%s" % repr(dbz.GetError()))
            else:
                aw.awu.MsgDialog(self, message="Problema di connessione al database delle aziende:\n%s" % dba._Error_MySQLdb)
            dba.Close()

            if out:

                img = cn('azienda_logo')
                if img.is_changed():
                    fns = img.get_image_filename()
                    if fns:
                        d = self.GetLogoPath(azienda_codice=cn('setup_azienda_codice').GetValue())
                        if d:
                            if not os.path.isdir(d):
                                os.makedirs(d)
                            try:
                                fnt = os.path.join(d, self.GetLogoFileName())
                                hs = open(fns, 'rb')
                                buf = hs.read()
                                hs.close()
                                ht = open(fnt, 'wb')
                                ht.write(buf)
                                ht.close()
                                cfg = Env.Azienda.config
                                p = cfg.get('Site', 'folder')
                                if os.path.isdir(p):
                                    if aw.awu.MsgDialog(self, 'Aggiorno anche il logo aziendale su X4?', style=wx.ICON_QUESTION|wx.YES_NO|wx.NO_DEFAULT) == wx.ID_YES:
                                        fnt = os.path.join(p, self.GetLogoFileName())
                                        hs = open(fns, 'rb')
                                        buf = hs.read()
                                        hs.close()
                                        ht = open(fnt, 'wb')
                                        ht.write(buf)
                                        ht.close()
                            except Exception, e:
                                aw.awu.MsgDialog(self, repr(e.args))

                bt.ReadAziendaSetup()
                Env.Azienda.read_dati_azienda()

        return out

    def GetLogoPath(self, azienda_codice=None):
        import report
        d = report.pathsub
        if d:
            d = os.path.join(d, 'immagini')
        return d

    def GetLogoFileName(self):
        return 'logo_aziendale.jpg'

    def Validate(self):
        reindex=False
        out = True
        cn = self.FindWindowByName
        ci = self.FindWindowById
        for name in ('codice', 'ragsoc', 'indirizzo', 'cap', 'citta', 'prov'):
            ctr = cn('setup_azienda_'+name)
            if ctr.GetValue():
                ctr.SetBackgroundColour(None)
            else:
                ctr.SetBackgroundColour(Env.Azienda.Colours.VALERR_BACKGROUND)
                out = False
        if out and not self.TestEsercizio():
            aw.awu.MsgDialog(self, message="Giorno/Mese errati x l'esercizio", style=wx.ICON_ERROR)
            out = False
        if out and cn('setup_contab_valcon').GetValue() is None:
            aw.awu.MsgDialog(self, message="Definire la valuta di conto", style=wx.ICON_ERROR)
            out = False
        if out and ci(wdr.ID_MAGDEFAULT).GetValue() is None:
            aw.awu.MsgDialog(self, message="Definire il magazzino di default", style=wx.ICON_ERROR)
            out = False

        if out and cn('setup_syncflag').GetValue()==1:
            if len(cn('setup_syncWrkDir').GetValue().strip())==0:
                aw.awu.MsgDialog(self, message="Specificare Cartella di Sincronizzazione", style=wx.ICON_ERROR)
                out = False
            if out and not os.path.exists(cn('setup_syncWrkDir').GetValue().strip()):
                aw.awu.MsgDialog(self, message="La Cartella di Sincronizzazione non esiste", style=wx.ICON_ERROR)
                out = False
            if out:
                newDestinatari=cn('setup_syncDestinatari').GetValue().split('|')
                oldDestinatari=self.oldDestinatari.split('|')
                for d in oldDestinatari:
                    if not d in newDestinatari:
                        msg="""
            ATTENZIONE! Si stanno rimuovendo alcuni destinatari.\n
            Proseguendo con la memorizzazione per tali utenti
            cesserà la sincronizzazione delle tabelle indicate\n
            Si conferma la memorizzazione?"""
                        if aw.awu.MsgDialog(self, message=msg, style=wx.ICON_QUESTION|wx.YES_NO)==wx.ID_NO:
                            out = False
                        break

        #=======================================================================
        # if len(self.wrkDir.GetValue().strip())==0:
        #     msg="La cartella di lavoro deve essere specificata"
        #     lEsito=False
        # elif not os.path.exists(self.wrkDir.GetValue().strip()):
        #     msg="La cartella di lavoro specificata non esiste"
        #     lEsito=False
        # return msg
        #=======================================================================








        self.Refresh()
        if out:
            old = (bt.TIPO_CONTAB,
                   bt.CONBILRICL,
                   bt.CONBILRCEE,
                   bt.CONATTRITACC,
                   bt.CONPERRITACC,
                   bt.CONCOMRITACC,
                   bt.MAGPRE_DECIMALS,
                   bt.MAGQTA_DECIMALS,
                   bt.VALINT_DECIMALS,
                   bt.MAGEAN_PREFIX,
                   bt.MAGSCOCAT,
                   bt.MAGSCORPCOS,
                   bt.MAGSCORPPRE,
                   bt.GESFIDICLI,
                   bt.MAGIMGPROD,
                   bt.MAGDIGSEARCH,
                   bt.MAGRETSEARCH,
                   bt.MAGEXCSEARCH,
                   bt.OPTLINKINDEX,
                   bt.OPTDIGSEARCH,
                   bt.OPTTABSEARCH,
                   bt.OPTRETSEARCH,
                   bt.OPTSPASEARCH,
                   bt.OPTLNKCRDPDC,
                   bt.OPTLNKGRDPDC,
                   bt.OPTLNKCRDCLI,
                   bt.OPTLNKGRDCLI,
                   bt.OPTLNKCRDFOR,
                   bt.OPTLNKGRDFOR,
                   bt.OPTNOTIFICHE,
                   bt.OPTBACKUPDIR,
                   bt.OPT_GC_PRINT,
                   bt.OPT_GCP_USER,
                   bt.OPT_GCP_PSWD,
                   bt.MAGATTGRIP,
                   bt.MAGATTGRIF,
                   bt.MAGCDEGRIP,
                   bt.MAGCDEGRIF,
                   bt.MAGDATGRIP,
                   bt.MAGAGGGRIP,
                   bt.MAGALWGRIP,
                   bt.MAGPZCONF,
                   bt.MAGPZGRIP,
                   bt.MAGPPROMO,
                   bt.MAGVISGIA,
                   bt.MAGVISPRE,
                   bt.MAGVISCOS,
                   bt.MAGVISCPF,
                   bt.MAGVISBCD,
                   bt.MAGGESACC,
                   bt.MAGPROVATT,
                   bt.MAGPROVCLI,
                   bt.MAGPROVPRO,
                   bt.MAGPROVMOV,
                   bt.MAGPROVSEQ,
                   bt.MAGNOCODEDES,
                   bt.MAGNOCODEVET,
                   bt.MAGNOCDEFDES,
                   bt.MAGNOCDEFVET,
                   bt.MAGEXTRAVET,
                   bt.MAGNUMSCO,
                   bt.MAGNUMRIC,
                   bt.MAGNUMLIS,
                   bt.MAGRICLIS,
                   bt.MAGSCOLIS,
                   bt.MAGROWLIS,
                   bt.MAGVLIFOR,
                   bt.MAGVLIMAR,
                   bt.MAGVLICAT,
                   bt.MAGVLIGRU,
                   bt.MAGDATLIS,
                   bt.MAGFORLIS,
                   bt.MAGBCOLIS,
                   bt.MAGERPLIS,
                   bt.MAGESPLIS,
                   bt.MAGVRGLIS,
                   bt.MAGVSGLIS,
                   bt.MAGREPLIS,
                   bt.MAGSEPLIS,
                   bt.MAGRELLIS,
                   bt.MAGSELLIS,
                   bt.SYNCFLAG,
                   bt.SYNCTIPOSERVER,
                   bt.SYNCWRKDIR,
                   bt.SYNCDESTINATARI,
                   bt.SYNCTABELLE,
                   )


            if not bt.OPTLINKINDEX == bool(cn('setup_optlinkindex').GetValue()):
                reindex=True
            bt.TIPO_CONTAB = cn('setup_tipo_contab').GetValue()
            bt.CONSOVGES = cn('setup_consovges').GetValue()
            bt.CONBILRICL = cn('setup_conbilricl').GetValue()
            bt.CONBILRCEE = cn('setup_conbilrcee').GetValue()
            bt.CONATTRITACC = cn('setup_conattritacc').GetValue()
            bt.CONPERRITACC = cn('setup_conperritacc').GetValue()
            bt.CONCOMRITACC = cn('setup_concomritacc').GetValue()
            bt.MAGPRE_DECIMALS = cn('setup_magdec_prez').GetValue()
            bt.MAGQTA_DECIMALS = cn('setup_magdec_qta').GetValue()
            bt.VALINT_DECIMALS = cn('setup_contab_decimp').GetValue()
            bt.MAGEAN_PREFIX = cn('setup_mageanprefix').GetValue()
            bt.MAGSCOCAT = int(cn('setup_magscocat').GetValue())
            bt.MAGSCORPCOS = cn('setup_magscorpcos').GetValue()
            bt.MAGSCORPPRE = cn('setup_magscorppre').GetValue()
            bt.GESFIDICLI = cn('setup_gesfidicli').GetValue()
            bt.MAGIMGPROD = cn('setup_magimgprod').GetValue()
            bt.MAGDIGSEARCH = bool(cn('setup_magdigsearch').GetValue())
            bt.MAGRETSEARCH = bool(cn('setup_magretsearch').GetValue())
            bt.MAGEXCSEARCH = bool(cn('setup_magexcsearch').GetValue())
            bt.OPTLINKINDEX = bool(cn('setup_optlinkindex').GetValue())
            bt.OPTDIGSEARCH = bool(cn('setup_optdigsearch').GetValue())
            bt.OPTTABSEARCH = bool(cn('setup_opttabsearch').GetValue())
            bt.OPTRETSEARCH = bool(cn('setup_optretsearch').GetValue())
            bt.OPTSPASEARCH = bool(cn('setup_optspasearch').GetValue())
            bt.OPTLNKCRDPDC = bool(cn('setup_optlnkcrdpdc').GetValue())
            bt.OPTLNKGRDPDC = bool(cn('setup_optlnkgrdpdc').GetValue())
            bt.OPTLNKCRDCLI = bool(cn('setup_optlnkcrdcli').GetValue())
            bt.OPTLNKGRDCLI = bool(cn('setup_optlnkgrdcli').GetValue())
            bt.OPTLNKCRDFOR = bool(cn('setup_optlnkcrdfor').GetValue())
            bt.OPTLNKGRDFOR = bool(cn('setup_optlnkgrdfor').GetValue())
            bt.OPTNOTIFICHE = bool(cn('setup_optnotifiche').GetValue())
            bt.OPTBACKUPDIR = cn('setup_optbackupdir').GetValue()
            bt.OPT_GC_PRINT = cn('setup_opt_gc_print').GetValue()
            bt.OPT_GCP_USER = cn('setup_opt_gcp_user').GetValue()
            bt.OPT_GCP_PSWD = cn('setup_opt_gcp_pswd').GetValue()

            bt.SYNCFLAG       = cn('setup_syncflag').GetValue()
            bt.SYNCTIPOSERVER = cn('setup_syncTipoServer').GetValue()
            bt.SYNCWRKDIR     = cn('setup_syncWrkDir').GetValue()
            bt.SYNCDESTINATARI= cn('setup_syncDestinatari').GetValue()
            bt.SYNCTABELLE    = cn('setup_syncTabelle').GetValue()

            bt.MAGATTGRIP = bool(cn('setup_magattgrip').GetValue())
            bt.MAGATTGRIF = bool(cn('setup_magattgrif').GetValue())
            bt.MAGCDEGRIP = bool(cn('setup_magcdegrip').GetValue())
            bt.MAGCDEGRIF = bool(cn('setup_magcdegrif').GetValue())
            bt.MAGDATGRIP = bool(cn('setup_magdatgrip').GetValue())
            bt.MAGAGGGRIP = bool(cn('setup_magagggrip').GetValue())
            bt.MAGALWGRIP = bool(cn('setup_magalwgrip').GetValue())
            bt.MAGPZCONF = bool(cn('setup_magpzconf').GetValue())
            bt.MAGPZGRIP = bool(cn('setup_magpzgrip').GetValue())
            bt.MAGPPROMO = bool(cn('setup_magppromo').GetValue())
            bt.MAGVISGIA = bool(cn('setup_magvisgia').GetValue())
            bt.MAGVISPRE = bool(cn('setup_magvispre').GetValue())
            bt.MAGVISCOS = bool(cn('setup_magviscos').GetValue())
            bt.MAGVISCPF = bool(cn('setup_magviscpf').GetValue())
            bt.MAGVISBCD = bool(cn('setup_magvisbcd').GetValue())
            bt.MAGGESACC = bool(cn('setup_maggesacc').GetValue())
            bt.MAGPROVATT = bool(cn('setup_magprovatt').GetValue())
            bt.MAGPROVCLI = bool(cn('setup_magprovcli').GetValue())
            bt.MAGPROVPRO = bool(cn('setup_magprovpro').GetValue())
            bt.MAGPROVMOV = cn('setup_magprovmov').GetValue()
            bt.MAGPROVSEQ = cn('setup_magprovseq').GetValue()
            bt.MAGNOCODEDES = cn('setup_magnocodedes').GetValue()
            bt.MAGNOCODEVET = cn('setup_magnocodevet').GetValue()
            bt.MAGNOCDEFDES = cn('setup_magnocdefdes').GetValue()
            bt.MAGNOCDEFVET = cn('setup_magnocdefvet').GetValue()
            bt.MAGEXTRAVET = cn('setup_magextravet').GetValue()
            bt.MAGNUMSCO = int(cn('setup_magnumsco').GetValue())
            bt.MAGNUMRIC = int(cn('setup_magnumric').GetValue())
            bt.MAGNUMLIS = int(cn('setup_magnumlis').GetValue())
            bt.MAGRICLIS = int(cn('setup_magriclis').GetValue())
            bt.MAGSCOLIS = int(cn('setup_magscolis').GetValue())
            bt.MAGROWLIS = int(cn('setup_magrowlis').GetValue())
            bt.MAGVLIFOR = int(cn('setup_magvlifor').GetValue())
            bt.MAGVLIMAR = int(cn('setup_magvlimar').GetValue())
            bt.MAGVLICAT = int(cn('setup_magvlicat').GetValue())
            bt.MAGVLIGRU = int(cn('setup_magvligru').GetValue())
            bt.MAGDATLIS = int(cn('setup_magdatlis').GetValue())
            bt.MAGFORLIS = int(cn('setup_magforlis').GetValue())
            bt.MAGBCOLIS = int(cn('setup_magbcolis').GetValue())
            bt.MAGERPLIS = cn('setup_magerplis').GetValue()
            bt.MAGESPLIS = cn('setup_magesplis').GetValue()
            bt.MAGVRGLIS = cn('setup_magvrglis').GetValue()
            bt.MAGVSGLIS = cn('setup_magvsglis').GetValue()
            bt.MAGREPLIS = cn('setup_magreplis').GetValue()
            bt.MAGSEPLIS = cn('setup_magseplis').GetValue()
            bt.MAGRELLIS = cn('setup_magrellis').GetValue()
            bt.MAGSELLIS = cn('setup_magsellis').GetValue()
            bt.defstru()
            out = wx.GetApp().TestDBVers(force=True, reindex=reindex)
            if not out:
                bt.TIPO_CONTAB,
                bt.CONSOVGES,
                bt.CONBILRICL,
                bt.CONBILRCEE,
                bt.CONATTRITACC,
                bt.CONPERRITACC,
                bt.CONCOMRITACC,
                bt.MAGPRE_DECIMALS,
                bt.MAGQTA_DECIMALS,
                bt.VALINT_DECIMALS,
                bt.MAGEAN_PREFIX,
                bt.MAGSCOCAT,
                bt.MAGSCORPCOS,
                bt.MAGSCORPPRE,
                bt.GESFIDICLI,
                bt.MAGIMGPROD,
                bt.MAGDIGSEARCH,
                bt.MAGRETSEARCH,
                bt.MAGEXCSEARCH,
                bt.OPTLINKINDEX,
                bt.OPTDIGSEARCH,
                bt.OPTTABSEARCH,
                bt.OPTRETSEARCH,
                bt.OPTSPASEARCH,
                bt.OPTLNKCRDPDC,
                bt.OPTLNKGRDPDC,
                bt.OPTLNKCRDCLI,
                bt.OPTLNKGRDCLI,
                bt.OPTLNKCRDFOR,
                bt.OPTLNKGRDFOR,
                bt.OPTNOTIFICHE,
                bt.OPTBACKUPDIR,
                bt.OPT_GC_PRINT,
                bt.OPT_GCP_USER,
                bt.OPT_GCP_PSWD,
                bt.MAGATTGRIP,
                bt.MAGATTGRIF,
                bt.MAGCDEGRIP,
                bt.MAGCDEGRIF,
                bt.MAGDATGRIP,
                bt.MAGAGGGRIP,
                bt.MAGALWGRIP,
                bt.MAGPZCONF,
                bt.MAGPZGRIP,
                bt.MAGPPROMO,
                bt.MAGVISGIA,
                bt.MAGVISPRE,
                bt.MAGVISCOS,
                bt.MAGVISCPF,
                bt.MAGVISBCD,
                bt.MAGGESACC,
                bt.MAGPROVATT,
                bt.MAGPROVCLI,
                bt.MAGPROVPRO,
                bt.MAGPROVMOV,
                bt.MAGPROVSEQ,
                bt.MAGNOCODEDES,
                bt.MAGNOCODEVET,
                bt.MAGNOCDEFDES,
                bt.MAGNOCDEFVET,
                bt.MAGEXTRAVET,
                bt.MAGNUMSCO,
                bt.MAGNUMRIC,
                bt.MAGNUMLIS,
                bt.MAGRICLIS,
                bt.MAGSCOLIS,
                bt.MAGROWLIS,
                bt.MAGVLIFOR,
                bt.MAGVLIMAR,
                bt.MAGVLICAT,
                bt.MAGVLIGRU,
                bt.MAGDATLIS,
                bt.MAGFORLIS,
                bt.MAGBCOLIS,
                bt.MAGERPLIS,
                bt.MAGESPLIS,
                bt.MAGVRGLIS,
                bt.MAGVSGLIS,
                bt.MAGREPLIS,
                bt.MAGSEPLIS,
                bt.MAGRELLIS,
                bt.MAGSELLIS,
                bt.SYNCFLAG,
                bt.SYNCTIPOSERVER,
                bt.SYNCWRKDIR,
                bt.SYNCDESTINATARI,
                bt.SYNCTABELLE, = old
        if out:
            cfg = CfgContab()
            cfg.SetEsercizio(Env.Azienda.Login.dataElab)

        return out

    def TestEsercizio(self):
        out = True
        cnv = lambda x: self.FindWindowByName('setup_'+x).GetValue()
        try:
            data = adb.DateTime.DateTime(Env.Azienda.Esercizio.dataElab.year,
                                         cnv('esercizio_startmm'),
                                         cnv('esercizio_startgg'))
        except:
            out = False
        return out


# ------------------------------------------------------------------------------


class AziendaSetupDialog(aw.Dialog):
    """
    Dialog impostazione setup azienda
    """
    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('title') and len(args) < 3:
            kwargs['title'] = FRAME_TITLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = AziendaSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
        for cid, func in ((wdr.ID_BTNOK, self.OnSave),):
            self.Bind(wx.EVT_BUTTON, func, id=cid)

    def OnSave(self, event):
        evt = wx.PyCommandEvent(lib._evtCHANGEMENU)
        wx.GetApp().GetTopWindow().AddPendingEvent(evt)
        self.EndModal(1)
