#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         xframe.py
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

import sys
import wx
import lib
import stormdb as adb
import rss
import strumenti

appl = wx.GetApp()
__app__ = (appl is not None)

import xml.dom.minidom

if __app__:
    def up():
        if appl.splash:
            appl.splash.UpdateProgress()
            wx.SafeYield(onlyIfNeeded=True)
    def setjob(x):
        if appl:
            if appl.splash:
                appl.splash.SetJob(x)
else:
    def up():
        pass
    def setjob(x):
        pass

#setjob("Caricamento moduli di base")
    

import erman
up()

from version import __version__, __modversion__, MODVERSION_NAME
up()

import versionchanges
up()

import cfg.tabsetup as tabsetup
up()

import os
def opj(x, y):
    return os.path.join(x, y).replace('\\', '/')
up()

import awc.controls.windows as aw
up()

import awc.util as awu
up()

import promem
up()

from X_wdr import *
up()

# ------------------------------------------------------------------------------


ID_TB_CLIENT = wx.NewId()
ID_TB_FORNIT = wx.NewId()
ID_TB_EMIDOC = wx.NewId()
ID_TB_INCPAG = wx.NewId()
ID_TB_INTSOTT = wx.NewId()
ID_TB_INTART = wx.NewId()
ID_TB_SCADCF = wx.NewId()


_evtSTATUSBAR_TEXTCHANGE_EVENT = wx.NewEventType()
EVT_STATUSBAR_TEXTCHANGE_EVENT = wx.PyEventBinder(_evtSTATUSBAR_TEXTCHANGE_EVENT, 0)

class StatusBarTextChangeEvent(wx.PyCommandEvent):
    
    def __init__(self, text=''):
        wx.PyCommandEvent.__init__(self, _evtSTATUSBAR_TEXTCHANGE_EVENT)
        self.text = text
    
    def SetText(self, text):
        self.text = text
    
    def GetText(self):
        return self.text

    
# ------------------------------------------------------------------------------


class AutoCheckUpdates_Thread(object):
    
    def __init__(self, parent):
        object.__init__(self)
        self.parent = parent

    def Start(self):
        import thread
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def Run(self):
        self.TrigTextEvent('Controllo presenza aggiornamenti in corso...')
        from prgup import VersionsDb
        db = VersionsDb()
        try:
            downloads = db.CheckUpdates()
            if downloads:
                self.TrigTextEvent('Aggiornamenti disponibili!')
            else:
                self.TrigTextEvent('Nessun aggiornamento trovato.')
                wx.Sleep(3)
                self.TrigTextEvent('')
        except Exception, e:
            self.TrigTextEvent(repr(e.args))
        self.running = False
    
    def TrigTextEvent(self, msg):
        try:
            e = StatusBarTextChangeEvent(msg)
            self.parent.GetEventHandler().AddPendingEvent(e)
        except:
            pass

    
# ------------------------------------------------------------------------------


class XFrame(aw.Frame):
    
    def __init__(self, parent=None, id=-1, title="X4",
                 pos=(0,0), size=(600, 160),
                 style = wx.DEFAULT_FRAME_STYLE ):
        
        aw.Frame.__init__(self, parent, id, title, pos, size, style)
        
        show_promem = show_feeds = True
        show_pages = []
        
        self.custom_info = None
        ci = self.GetFrameCustomInfo()
        if ci:
            try:
                f = ci.getElementsByTagName('customize_frame')[0]
                def _int(n, d):
                    try:
                        return int(n)
                    except:
                        return d
                show_promem = _int(f.getAttribute('promemoria'), 1)
                show_feeds = _int(f.getAttribute('feeds'), 1)
                frame_width = _int(f.getAttribute('width'), 0)
                frame_height = _int(f.getAttribute('height'), 0)
                if frame_width and frame_height:
                    def set_size():
                        self.SetSize((frame_width, frame_height))
                    wx.CallAfter(set_size)
            except:
                pass
            
            
            for pages in ci.getElementsByTagName('pages'):
                for page in pages.getElementsByTagName('page'):
                    pt = page.getAttribute('title')
                    pp = page.getAttribute('panel')
                    if pp and pt:
                        n = pp.rindex('.')
                        pm, pc = pp[:n], pp[n+1:]
                        m = __import__(pm, fromlist=True)
                        if hasattr(m, pc):
                            show_pages.append((pt, getattr(m, pc)))
        
        self.menuext = []
        self.ftdif = []
        
        self.menupers = {}
        self.toolpers = {}
        self.toollist = []
        
        self.CreateMenuBar()
        
        self.CreateXToolBar()
        
        self.CreateStatusBar(2)
        self.SetStatusText("Welcome!")
        
        self.DisplayUserStatusBar()
        
        sizer = wx.FlexGridSizer(0, 1, 0, 0)
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)
        
        if show_promem or show_feeds or show_pages:
            
            self.workzone = nb = wx.Notebook(self, -1)
            sizer.Add(nb, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 0)
            
            if show_promem:
                rp = promem.PromemPanel(nb, -1)
                nb.AddPage(rp, 'Promemoria')
            
            if show_feeds:
                feeds = [['Notizie (beta)', "http://www.ilsole24ore.com/rss/norme-e-tributi/fisco.xml"]]
                i = self.custom_info
                if i:
                    for ff in i.getElementsByTagName('feeds'):
                        for f in ff.getElementsByTagName('feed'):
                            try:
                                feeds.append([f.getAttribute('title'), f.getAttribute('url')])
                            except:
                                pass
                for title, url in feeds:
                    rss.AddNotebookFeedPage(nb, title, url)
            
            for title, Panel in show_pages:
                nb.AddPage(Panel(nb), title)
        
        self.SetSizer(sizer)
        sizer.SetSizeHints(self)
        
        self.Fit()
        self.Layout()
        
        if show_promem:
            rp.populate()
            self.promem = rp
            if hasattr(sys, 'frozen'):
                rp.autoUpdate(5)
                rp.startReminder(1)
        
        self.Bind(lib.EVT_CHANGEMENU, self.OnChangeMenu)
        self.Bind(EVT_STATUSBAR_TEXTCHANGE_EVENT, self.OnStatusBarTextChange)
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
    
    def DisplayUserStatusBar(self):
        import Env
        v = Env.version
        l = Env.Azienda.Login
        sb = self.GetStatusBar()
        msg = 'X4 v.%s' % v.VERSION_STRING
        if v.MODVERSION_NAME:
            msg += ' mod %s v.%s' % (v.MODVERSION_NAME, v.MODVERSION_STRING)
        msg += ' - Op.: %s - %s' % (l.usercode, l.username)
        self.SetStatusText(msg, sb.GetFieldsCount()-1)
    
    def Show(self, *args, **kwargs):
        
        aw.Frame.Show(self, *args, **kwargs)
        
        cfg = Env.Azienda.config
        if cfg.get('Updates', 'user') and cfg.get('Updates', 'pswd'):
            if cfg.get('Updates', 'autocheck') == '2':
                msg =\
                """E' possibile impostare questa workstation in modo che effettui\n"""\
                """automaticamente il controllo della presenza di nuove versioni\n"""\
                """all'avvio.\n\n"""\
                """Desideri attivare questa possibilità?"""
                r = aw.awu.MsgDialog(self, msg, 'Aggornamenti automatici', 
                                     style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
                if r == wx.ID_YES:
                    v = '1'
                else:
                    v = '0'
                cfg.set('Updates', 'autocheck', v)
                cfg.write()
            self.AutoCheckUpdates()
    
    def AutoCheckUpdates(self):
        cfg = Env.Azienda.config
        if cfg.get('Updates', 'user') and cfg.get('Updates', 'pswd'):
            if cfg.get('Updates', 'autocheck') == '1':
                t = AutoCheckUpdates_Thread(self)
                t.Start()
    
    def OnStatusBarTextChange(self, event):
        sb = self.GetStatusBar()
        text = event.GetText()
        if text:
            sb.SetStatusText(text, sb.GetFieldsCount()-1)
        else:
            self.DisplayUserStatusBar()
        event.Skip()
    
    def OnChangeMenu(self, event):
        self.CreateMenuBar()
        self.CreateXToolBar()
        event.Skip()
    
    def GetFrameCustomInfo(self):
        if not hasattr(self, 'custom_info'):
            self.custom_info = None
        if self.custom_info is None:
            ua = adb.DbTable('x4.diritti', 'ua')
            ua.Reset()
            if hasattr(ua, 'customize_frame'):
                aa = adb.DbTable('x4.aziende', 'aa')
                if aa.Retrieve('aa.codice=%s', Env.Azienda.codice) and aa.OneRow():
                    if ua.Retrieve('ua.id_azienda=%s AND ua.id_utente=%s AND ua.attivo=1', 
                                   aa.id, Env.Azienda.Login.userid) and ua.OneRow():
                        if ua.customize_frame:
                            try:
                                self.custom_info = xml.dom.minidom.parseString(ua.customize_frame)
                                return self.custom_info
                            except:
                                pass
            p = None
            try:
                p = Env.Azienda.config.get('Site', 'folder')
            except:
                pass
            if not p:
                p = Env.config_base_path
            p = opj(p, 'cust')
            p = opj(p, 'frame')
            p = opj(p, Env.Azienda.codice)
            names = []
            if Env.Azienda.params['custom-menu']:
                names.append(Env.Azienda.params['custom-menu'])
            names.append(Env.Azienda.Login.username)
            names.append('__allusers__')
            for f in names:
                f = opj(p, f)
                if not f.endswith('.x4f'):
                    f += '.x4f'
                if os.path.exists(f):
                    try:
                        self.custom_info = xml.dom.minidom.parse(f)
                        break
                    except Exception, e:
                        aw.awu.MsgDialog(self, repr(e.args), style=wx.ICON_ERROR)
        return self.custom_info
    
    def GetMenuPers(self):
        i = self.GetFrameCustomInfo()
        if i:
            try:
                return i.getElementsByTagName('menu')[0]
            except:
                pass
        return None
    
    def GetFrameInfo(self):
        i = self.GetFrameCustomInfo()
        if i:
            try:
                f = i.getElementsByTagName('customize_frame')[0]
                o = {}
                for name in f.attributes.keys():
                    o[name] = f.getAttribute(name)
                return o
            except:
                pass
        return None
    
    def CreateXMenuBar(self):
        
        menubar = None
        
        c = self.GetMenuPers()
        if c:
            err = False
            menubar = wx.MenuBar()
            for g in c.getElementsByTagName("group"):
                menu = wx.Menu()
                for v in g.getElementsByTagName("voice"):
                    keys = v.attributes.keys()
                    if 'menu' in keys:
                        mid = wx.NewId()
                        menu.Append(mid, v.getAttribute('menu'))
                        err = None
                        try:
                            sf, mv, md = map(lambda x: v.getAttribute(x),
                                             'frame menu desc'.split())
                            n = sf.rindex('.')
                            sm, sf = sf[:n], sf[n+1:]
                            cm = __import__(sm, fromlist=True)
                            if hasattr(cm, sf):
                                fc = getattr(cm, sf)
                                self.menupers[mid] = {'frame': fc,
                                                      'voice': mv,
                                                      'desc': md,}
                                for key in keys:
                                    if key.startswith('frame_'):
                                        self.menupers[mid][key] = v.getAttribute(key)
                            else:
                                err = "Frame non trovato: %s" % sf
                            if not err:
                                tb = v.getAttribute('toolbar')
                                if tb:
                                    n = tb.rindex('.')
                                    tm, ti = tb[:n], tb[n+1:]
                                    im = __import__(tm, fromlist=True)
                                    if not hasattr(im, ti):
                                        err = "Immagine toolbar non trovata: %s" % ti
                                    else:
                                        tid = wx.NewId()
                                        self.toolpers[tid] = {'image': getattr(im, ti),
                                                              'frame': fc,
                                                              'voice': mv,
                                                              'desc': md,}
                                        self.toollist.append(tid)
                        except Exception, e:
                            err = "Configurazione voce menu errata: %s" % repr(e.args)
                        except ImportError, e:
                            err = "Modulo non trovato: %s" % sm
                        if err:
                            aw.awu.MsgDialog(self, err, style=wx.ICON_ERROR)
                        else:
                            self.Bind(wx.EVT_MENU, self.OnMenuPers, id=mid)
                    elif 'separator' in keys:
                        if 'menu' in v.getAttribute('separator'):
                            menu.AppendSeparator()
                        if 'toolbar' in v.getAttribute('separator'):
                            if not -1 in self.toolpers:
                                self.toolpers[-1] = {'separator': True,}
                            self.toollist.append(-1)
                if err:
                    break
                menubar.Append(menu, g.getAttribute('name'))
        
        if menubar is None and not self.menupers:
            menubar = XMenuBarFunc()
        
        return menubar
    
    def CreateMenuBar(self):
        
        menubar = self.CreateXMenuBar()
        menubar = self.AdaptMenuBar_CheckSetup(menubar)
        menubar = self.AdaptMenuBar_CheckUtente(menubar)
        menubar = self.AdaptMenuBar_Clean(menubar)
        
        self.SetMenuBar(menubar)
        
        #costruzione menu fatturazione differita
        mod = menubar.FindItemById(ID_MAGOPEDIF)
        del self.menuext[:]
        if mod:
            mod = mod.GetSubMenu()
            if mod:
                fd = adb.DbTable(Env.Azienda.BaseTab.TABNAME_CFGFTDIF,
                                 writable=False)
                if fd.Retrieve():
                    def RunFtDif(fdid):
                        from magazz.ftdif import FtDifFrame
                        dlg = self.LaunchFrame(FtDifFrame, show=False)
                        dlg.SetRaggr(fdid)
                        dlg.Show()
                    for f in fd:
                        mid = wx.NewId()
                        mod.Append(mid, f.descriz)
                        self.menuext.append((mid, RunFtDif))
                        self.Bind(wx.EVT_MENU, self.OnMenuExt, id=mid)
                        self.ftdif.append((mid, f.id, f.codice, f.descriz))
        
        #handlers menu
        for func, cid in (
            
            #gestione tabelle di base
            (self.OnQuit,                      ID_QUIT),
            (self.OnGestCasse,                 ID_GESCASSE),
            (self.OnGestBanche,                ID_GESBANCHE),
            (self.OnGestEffetti,               ID_GESEFFETT),
            (self.OnGestCatCli,                ID_GESCLIENT_CATEGO),
            (self.OnGestStatCli,               ID_GESCLIENT_STATUS),
            (self.OnGestClienti,               ID_GESCLIENT),
            (self.OnGestCatFor,                ID_GESFORNIT_CATEGO),
            (self.OnGestStatFor,               ID_GESFORNIT_STATUS),
            (self.OnGestFornit,                ID_GESFORNIT),
            (self.OnGestProd,                  ID_GESPROD),
            (self.OnGestProdPromo,             ID_GESPRODPROMO),
            (self.OnGestCatArt,                ID_GESPROD_CATART),
            (self.OnGestGruArt,                ID_GESPROD_GRUART),
            (self.OnGestInvStru,               ID_GESINVSTR),
            (self.OnGestStatArt,               ID_GESPROD_STATUS),
            (self.OnGestTipArt,                ID_GESPROD_TIPART),
            (self.OnGestMarArt,                ID_GESPROD_MARART),
            (self.OnGestTipList,               ID_GESPROD_TIPLIST),
            (self.OnGestGruPrez,               ID_GESPROD_GRUPREZ),
            (self.OnGestPdc,                   ID_GESBILPDC),
            (self.OnGestPdcCee,                ID_GESPDCCEE),
            (self.OnGestStatPdc,               ID_GESSTATPDC),
            (self.OnGestPdcStru,               ID_GESBILSTR),
            (self.OnGestPdcRiclStru,           ID_GESBILRICLSTR),
            (self.OnGestBilMas,                ID_GESBILMAS),
            (self.OnGestBilCon,                ID_GESBILCON),
            (self.OnGestBriMas,                ID_GESBRIMAS),
            (self.OnGestBilCee,                ID_GESBILCEE),
            (self.OnGestBriCon,                ID_GESBRICON),
            (self.OnGestModPag,                ID_GESMODPAG),
            (self.OnGestAliqIva,               ID_GESALQIVA),
            (self.OnGestStati,                 ID_CFGSTATI),
            (self.OnGestPdcTip,                ID_GESTIPANA),
            (self.OnGestScadGrp,               ID_GESGRUSCA),
            (self.OnGestListini,               ID_GESLISVEN),
            (self.OnGestStampaListino,         ID_GESSTALIS),
            (self.OnGestGrpCli,                ID_GESGRPCLI),
            (self.OnGestGrpFor,                ID_GESGRPFOR),
            (self.OnPrintGrpCli,               ID_STAGRPCLI),
            (self.OnPrintGrpFor,               ID_STAGRPFOR),
            (self.OnGestDatiFiscaliClienti,    ID_GESDATIFISC_CLI),
            (self.OnGestDatiFiscaliFornitori,  ID_GESDATIFISC_FOR),
            
            #gestione tabelle organizzazione maazzino/vendite
            (self.OnGestZone,                  ID_GESTZONE),
            (self.OnGestAgenti,                ID_GESTAGENTI),
            (self.OnGestSpeInc,                ID_GESTSPEINC),
            (self.OnGestMagazz,                ID_CFGMAGAZZ),
            
            #gestione tabelle dati trasporto x agazzino
            (self.OnGestTraCau,                ID_GESTRACAU),
            (self.OnGestTraCur,                ID_GESTRACUR),
            (self.OnGestTraAsp,                ID_GESTRAASP),
            (self.OnGestTraPor,                ID_GESTRAPOR),
            (self.OnGestTraCon,                ID_GESTRACON),
            (self.OnGestTraVet,                ID_GESTRAVET),
            
            #interrogazioni contabili sottoconti/movimenti
            (self.OnPdcInterrCli,              ID_INTCONCLI),
            (self.OnPdcInterrFor,              ID_INTCONFOR),
            (self.OnPdcInterrCas,              ID_INTCONCAS),
            (self.OnQuadRegCont,               ID_CTR_QUADCON),
            (self.OnPdcInterrBan,              ID_INTCONBAN),
            (self.OnPdcInterrEff,              ID_INTCONEFF),
            (self.OnPdcInterrPdc,              ID_INTCONPDC),
            (self.OnPcfInterrCli,              ID_INTPCFCLI),
            (self.OnPcfInterrFor,              ID_INTPCFFOR),
            
            #bilanci
            (self.OnBilVerif,                  ID_CONTABIL_VERIF),
            (self.OnBilGest,                   ID_CONTABIL_GEST),
            (self.OnBilContr,                  ID_CONTABIL_CONTR),
            (self.OnBilVerifRicl,              ID_CONTABRI_VERIF),
            (self.OnBilGestRicl,               ID_CONTABRI_GEST),
            (self.OnBilContrRicl,              ID_CONTABRI_CONTR),
            (self.OnBilCee,                    ID_CONTABIL_CEE),
            
            #interrogazioni contabili
            (self.OnScadenzario,               ID_SCAD_SCAD),
            (self.OnScadenzarioGruppo,         ID_SCAD_SCADGRP),
            (self.OnScadGlobal,                ID_SCAD_GLOBAL),
            (self.OnScadGlobalIncassi,         ID_SCAD_GLOBAL_INCASSI),
            (self.OnScadGlobalPagamenti,       ID_SCAD_GLOBAL_PAGAMENTI),
            (self.OnScadGlobalEffettiDaEm,     ID_SCAD_GLOBAL_EFFETTIDAEMETTERE),
            (self.OnScadGlobalEffettiEmessi,   ID_SCAD_GLOBAL_EFFETTIEMESSI),
            (self.OnScadGlobalEffettiInsoluti, ID_SCAD_GLOBAL_EFFETTIINSOLUTI),
            (self.OnQuadPcfCont,               ID_SCAD_CTRQUAD),
            (self.OnCalcIntPcf,                ID_SCAD_CALCINT),
            (self.OnSituazioneFidiClienti,     ID_SCAD_SITFIDO),
            (self.OnCtrCassa,                  ID_CTR_CASSA),
            (self.OnIntRegCon,                 ID_INTREGCON),
            (self.OnEmiEffetti,                ID_EMIEFF),
            (self.OnAccorpaEffetti,            ID_RAGGRPCF),
            (self.OnMastriSottoconto,          ID_CONTAB_MASTRI),
            (self.OnGiornaleGenerale,          ID_CONTAB_GIORNALE),
            (self.OnFatturatoAcqVen,           ID_FATCONACQVEN),
            (self.OnVendAziPriv,               ID_VENDAZIPRIV),
            (self.OnSpesometro,                ID_CONTAB_SPESOM),
            
            #interrogazioni iva
            (self.OnIntRegIva,                 ID_INTREGIVA),
            (self.OnAliqRegIva,                ID_INTALIQIVA),
            (self.OnRegIva,                    ID_REGIVA),
            (self.OnLiqIva,                    ID_LIQIVA),
            #(self.OnAllegati,                  ID_ALLEGCF),
            (self.OnCtrIvaSeq,                 ID_IVASEQ),
            
            #interrogazioni magazzino prodotto/movimenti
            (self.OnInterrProdotto,            ID_INTPROD),
            (self.OnIntDocMag,                 ID_INTDOCMAG),
            (self.OnIntDocVet,                 ID_INTDOCVET),
            (self.OnIntMovMag,                 ID_INTMOVMAG),
            (self.OnIntEvaMag,                 ID_INTEVAMAG),
            (self.OnIntInvPres,                ID_INTGIAPRE),
            (self.OnIntInvent,                 ID_INTINVENT),
            (self.OnIntSottoSc,                ID_INTSOTTOSC),
            (self.OnIntMagSrcDes,              ID_INTMAGSRCDES),
            (self.OnIntMagProvAge,             ID_PROVAGE),
            (self.OnProdRiPro,                 ID_MAGPRODPRORIC),
            (self.OnProdRiCos,                 ID_MAGPRODCOSTIZERO),
            (self.OnPdcIntMagCli,              ID_INTMAGCLI),
            (self.OnPdcSituazioneAcconti,      ID_INTMAGACC),
            (self.OnPdcIntMagFor,              ID_INTMAGFOR),
            (self.OnBarCodesSpot,              ID_BARCODESPOT),
            
            #statistiche magazzino
            (self.OnPdcFtProd,                 ID_PDCSINTART),
            (self.OnStatFatCli,                ID_STATFATCLI),
            (self.OnStatFatCliCatArt,          ID_STATFATCLICAT),
            (self.OnStatFatPro,                ID_STATFATPRO),
            (self.OnStatFatProCli,             ID_STATFATPROCLI),
            (self.OnStatFatAge,                ID_STATFATAGE),
            (self.OnStatFatCatArt,             ID_STATFATCATART),
            (self.OnStatValCosAcq,             ID_STATCOSACQ),
            (self.OnStatValPreApp,             ID_STATPREAPP),
            (self.OnStatReddVend,              ID_STATREDDVEND),
            
            #setup
            (self.OnCfgLicense,                ID_CFGLICENSE),
            (self.OnCfgActivationCodes,        ID_CFGACTIVATIONCODES),
            (self.OnCfgAzienda,                ID_CFGAZIENDA),
            (self.OnCfgEmail,                  ID_CFGEMAIL),
            (self.OnCfgXmpp,                   ID_CFGXMPP),
            (self.OnCfgDocsEmail,              ID_CFGDOCSEMAIL),
            (self.OnCfgTipiEvento,             ID_CFGTIPEVENT),
            (self.OnCfgEventManager,           ID_CFGEVENTMGR),
            (self.OnCfgCauContab,              ID_CFGCONCAU),
            (self.OnCfgProgrContab,            ID_CFGPROGRCON),
            (self.OnCfgRegIva,                 ID_CFGREGIVA),
            (self.OnCfgProgrIva,               ID_CFGLIQIVA),
            (self.OnCfgAutoContab,             ID_CFGAUTCON),
            (self.OnCfgCauMagazz,              ID_CFGMAGCAU),
            (self.OnCfgFtDif,                  ID_CFGFTDIF),
            (self.OnCfgAutoMagazz,             ID_CFGAUTMAG),
            (self.OnCfgWorkstation,            ID_CFGWKS),
            (self.OnCfgUpdates,                ID_CFGUPDATES),
            (self.OnCfgPdcRange,               ID_CFGPDCRANGE),
            (self.OnCfgMassimaliSpesometro,    ID_CFGSPESOM),
            
            #dataentry contabili
            (self.OnDataEntryContabIva,        ID_CONTABGES_ACQVEN),
            (self.OnDataEntryContabSaldaConto, ID_CONTABGES_INCPAG),
            (self.OnDataEntryContabComposto,   ID_CONTABGES_ALTRO),
            (self.OnDataEntryContabSolaIva,    ID_CONTABGES_SOLIVA),
            (self.OnPcfNew,                    ID_SCADINS),
            
            #dataentry magazzino
            (self.OnDataEntryMagazz,           ID_MAGAZZINS),
            (self.OnStaDif,                    ID_STADIFF),
            
            #chiusure contabili
            (self.OnChiusContabGenMov,         ID_CHIUSCONT_GENMOV),
            (self.OnChiusContabSovrapp,        ID_CHIUSCONT_SOVRAPP),
            (self.OnChiusContabAnnuale,        ID_CHIUSCONT_ANNUALE),
            (self.OnChiusContabIVA,            ID_CHIUSIVA_CHIUSIVA),
            
            #chiusure magazzino
            (self.OnChiusMagazzConsCosti,      ID_CHIUSMAGAZZ_CREACOSTI),
            (self.OnChiusMagazzEditGiacenze,   ID_CHIUSMAGAZZ_EDITGIAC),
            (self.OnChiusMagazzGenMoviIni,     ID_CHIUSMAGAZZ_GENMOVINI),
            
            (self.OnBackupExplorer,            ID_BACKUPEXPLORER),

            (self.OnChangeIva,                 ID_CHANGEIVA),
            
            (self.OnHelp,                      ID_HELP),
            (self.OnAbout,                     ID_ABOUT),
            (self.OnProgramUpdate,             ID_UPDATES),
            ):
            self.Bind(wx.EVT_MENU, func, id=cid)
        
        #menu specifici della mod
        
        return menubar
    
    def AdaptMenuBar_CheckSetup(self, menubar):
        
        bt = Env.Azienda.BaseTab
        
        #rimozione voci x bilanci riclassificati se non gestiti
        if not bt.CONBILRICL:
            for cid in (ID_GESTBILRICL, ID_BILRICL):
                item = menubar.FindItemById(cid)
                if item:
                    item.GetMenu().Remove(cid)
        
        #rimozione voci x bilancio cee se non gestito
        if not bt.CONBILRCEE:
            for cid in (ID_GESTBILCEE, ID_BILCEE):
                item = menubar.FindItemById(cid)
                if item:
                    item.GetMenu().Remove(cid)
        
        #rimozione voci x griglie prezzi se non gestite
        for flag, cid in ((bt.MAGATTGRIP, ID_GRIPCLI),
                          (bt.MAGATTGRIF, ID_GRIPFOR)):
            if not flag:
                item = menubar.FindItemById(cid)
                if item:
                    item.GetMenu().Remove(cid)
        
        #rimozione voce x gestione acconti se non gestito
        if bt.MAGGESACC != 1:
            cid = ID_INTMAGACC
            item = menubar.FindItemById(cid)
            if item:
                item.GetMenu().Remove(cid)
        
        #rimozione voce x situazione fidi clienti
        if bt.GESFIDICLI != '1':
            cid = ID_SCAD_SITFIDO
            item = menubar.FindItemById(cid)
            if item:
                item.GetMenu().Remove(cid)
        
        #adeguamento voci di chiusura contabile in funzione della sovrapposizione
        #gestita o meno e dello stato di esecuzione delle procedure di generazione
        #movimenti di chiusura/apertura
        from cfg.dbtables import ProgrEsercizio
        pe = ProgrEsercizio()
        try:
            #menu attivazione sovrapposizione di esercizio
            item = menubar.FindItemById(ID_CHIUSCONT_SOVRAPP)
            if bt.CONSOVGES == 1:
                #chiusure in sovrapposizione
                if pe.GetSovrapposizione():
                    #sovrapposizione eseguita, disabilito voce di attivazione
                    item.GetMenu().Enable(ID_CHIUSCONT_SOVRAPP, False)
                else:
                    #sovrapposizione non ancora attivata, disabilito voce generazione
                    item.GetMenu().Enable(ID_CHIUSCONT_GENMOV, False)
            else:
                #chiusure senza sovrapposizione, elimino voce di attivazione
                item.GetMenu().Remove(ID_CHIUSCONT_SOVRAPP)
            #menu generazione movimenti di chiusura/apertura
            item = menubar.FindItemById(ID_CHIUSCONT_GENMOV)
            if pe.GetMovimentiGenerati():
                #movimenti già generati, disabilito voce generazione
                item.GetMenu().Enable(ID_CHIUSCONT_GENMOV, False)
            else:
                #movimenti non acora generati, disabilito voce chiusura
                item.GetMenu().Enable(ID_CHIUSCONT_ANNUALE, False)
            
            #rimozione voci x listino attuale se non gestito o non x data
            if bt.MAGNUMLIS == 0 or not bt.MAGDATLIS:
                item = menubar.FindItemById(ID_GESSTALIS)
                if item:
                    item.GetMenu().Remove(ID_GESSTALIS)
            
            #rimozione voci x promozioni se non gestito
            if not bt.MAGPPROMO:
                item = menubar.FindItemById(ID_GESPRODPROMO)
                if item:
                    item.GetMenu().Remove(ID_GESPRODPROMO)
            
            #rimozione voci x provvigioni agenti se non gestite
            if not bt.MAGPROVATT:
                item = menubar.FindItemById(ID_MENUPROVAGE)
                if item:
                    item.GetMenu().Remove(ID_MENUPROVAGE)
        except:
            pass
        
        return menubar
    
    def AdaptMenuBar_CheckUtente(self, menubar):
        
        #inizio sequenza di controlli per rimozioni menu in base ai permessi dell'utente
        datute = Env.Azienda.Login.userdata
        
        #controllo permessi contabilità: tolgo tendina se non posso inserire, interrogare, gestire
        try:
            if datute.can_contabins != 1 and datute.can_contabint != 1 and datute.can_contabges != 1:
                n = menubar.FindMenu('Contabilità')
                if n >= 0:
                    menubar.Remove(n)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: inserimento
        try:
            if datute.can_contabins != 1:
                item = menubar.FindItemById(ID_MENUCONTINS)
                if item:
                    item.GetMenu().Delete(ID_MENUCONTINS)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: interrogazioni
        try:
            if datute.can_contabint != 1:
                item = menubar.FindItemById(ID_MENUCONTINT)
                if item:
                    item.GetMenu().Delete(ID_MENUCONTINT)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: stampe fiscali ed iva
        try:
            if datute.can_contabfis != 1:
                for cid in (ID_MENUSTAFIS, ID_MENUIVA):
                    item = menubar.FindItemById(cid)
                    if item:
                        item.GetMenu().Delete(cid)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: bilanci
        try:
            if datute.can_contabbil != 1:
                for cid in (ID_MENUBIL, ID_BILRICL, ID_BILCEE):
                    item = menubar.FindItemById(cid)
                    if item:
                        item.GetMenu().Delete(cid)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: gestione
        try:
            if datute.can_contabges != 1:
                item = menubar.FindItemById(ID_MENUCONTGES)
                if item:
                    item.GetMenu().Delete(ID_MENUCONTGES)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: scadenzari
        try:
            if datute.can_contabsca != 1:
                n = menubar.FindMenu('Scadenzari')
                if n >= 0:
                    menubar.Remove(n)
        except Exception, e:
            pass
        
        #controllo permesso contabilità: effetti
        try:
            if datute.can_contabeff != 1:
                n = menubar.FindMenu('Effetti')
                if n >= 0:
                    menubar.Remove(n)
        except Exception, e:
            pass
        
        #controllo permessi magazzino: tolgo tendina se non posso inserire, interrogare, fare op.differite, elaborare
        try:
            if datute.can_magazzins != 1 and datute.can_magazzint != 1 and datute.can_magazzdif != 1 and datute.can_magazzela != 1:
                n = menubar.FindMenu('Magazzino')
                if n >= 0:
                    menubar.Remove(n)
        except Exception, e:
            pass
        
        #controllo permesso magazzino: inserimento
        try:
            if datute.can_magazzins != 1:
                item = menubar.FindItemById(ID_MAGAZZINS)
                if item:
                    item.GetMenu().Delete(ID_MAGAZZINS)
        except Exception, e:
            pass
        
        #controllo permesso magazzino: inserimento
        try:
            if datute.can_magazzint != 1:
                item = menubar.FindItemById(ID_MAGAZZINT)
                if item:
                    item.GetMenu().Delete(ID_MAGAZZINT)
        except Exception, e:
            pass
        
        #controllo permesso magazzino: inserimento
        try:
            if datute.can_magazzdif != 1:
                item = menubar.FindItemById(ID_MAGOPEDIF)
                if item:
                    item.GetMenu().Delete(ID_MAGOPEDIF)
        except Exception, e:
            pass
        
        #controllo permesso magazzino: inserimento
        try:
            if datute.can_magazzela != 1:
                item = menubar.FindItemById(ID_MENUMAGELAB)
                if item:
                    item.GetMenu().Delete(ID_MENUMAGELAB)
        except Exception, e:
            pass
        
        #controllo permessi setup impostazioni: tolgo tendina se non ho accesso a setup contab, magazz, impostaz, opzioni, altre impostazioni da esterno, altre opzioni da esterno
        try:
            if datute.can_setupcontab != 1 and datute.can_setupmagazz != 1 and datute.can_setupsetup != 1 and datute.can_setupoption != 1 and datute.can_setupother != 1 and datute.can_setupoptoth != 1:
                item = menubar.FindItemById(ID_MENUSETUP)
                if item:
                    item.GetMenu().Delete(ID_MENUSETUP)
        except Exception, e:
            pass
        
        #controllo permesso setup: contabilità
        try:
            if datute.can_setupcontab != 1:
                item = menubar.FindItemById(ID_MENUSETUP_CONTAB)
                if item:
                    item.GetMenu().Delete(ID_MENUSETUP_CONTAB)
        except Exception, e:
            pass
        
        #controllo permesso setup: magazzino
        try:
            if datute.can_setupmagazz != 1:
                item = menubar.FindItemById(ID_MENUSETUP_MAGAZZ)
                if item:
                    item.GetMenu().Delete(ID_MENUSETUP_MAGAZZ)
        except Exception, e:
            pass
        
        #controllo permesso setup: impostazioni
        try:
            if datute.can_setupsetup != 1:
                item = menubar.FindItemById(ID_MENUSETUP_IMPOSTAZIONI)
                if item:
                    item.GetMenu().Delete(ID_MENUSETUP_IMPOSTAZIONI)
        except Exception, e:
            pass
        
        #controllo permesso setup: opzioni
        try:
            if datute.can_setupoption != 1 and datute.can_setupoptoth != 1:
                item = menubar.FindItemById(ID_MENUSETUP_OPZIONI)
                if item:
                    item.GetMenu().Delete(ID_MENUSETUP_OPZIONI)
        except Exception, e:
            pass
        
        #controllo permessi setup impostazioni: tolgo tendina se non ho accesso a setup contab, magazz, impostaz, opzioni, altro da esterno
        try:
            if datute.can_contabchi != 1 and datute.can_magazzchi != 1:
                item = menubar.FindItemById(ID_MENUCHIUSURE)
                if item:
                    item.GetMenu().Delete(ID_MENUCHIUSURE)
        except Exception, e:
            pass
        
        #controllo permesso chiusure: contabilità
        try:
            if datute.can_contabchi != 1:
                for cid in (ID_MENUCHIUSCONTAB, ID_MENUCHIUSIVA):
                    item = menubar.FindItemById(cid)
                    if item:
                        item.GetMenu().Delete(cid)
        except Exception, e:
            pass
        
        #controllo permesso chiusure: magazzino
        try:
            if datute.can_magazzchi != 1:
                item = menubar.FindItemById(ID_MENUCHIUSMAGAZZ)
                if item:
                    item.GetMenu().Delete(ID_MENUCHIUSMAGAZZ)
        except Exception, e:
            pass
        
        #controllo permesso backup explorer
        try:
            if datute.can_backupdata != 1 and datute.can_restoredata != 1:
                while True:
                    #inspiegabilmente, tolta la voce di backup, essa permane.
                    #forse perché l'ultima voce della tendina? boh misteri wx
                    item = menubar.FindItemById(ID_BACKUPEXPLORER)
                    if item:
                        item.GetMenu().Remove(ID_BACKUPEXPLORER)
                    else:
                        break
        except Exception, e:
            pass
        
        return menubar
    
    def AdaptMenuBar_Clean(self, menubar):
        
        def CleanMenu(menu):
            ws = True
            for item in menu.GetMenuItems():
                if item.IsSeparator():
                    if ws:
                        #separatore duplicato o come prima voce del menu, lo elimino
                        item.GetMenu().Delete(item.GetId())
                    else:
                        ws = True
                else:
                    ws = False
                submenu = item.GetSubMenu()
                if submenu:
                    if not CleanMenu(submenu):
                        #il sottomenu è vuoto, elimino la relativa voce
                        item.GetMenu().Delete(item.GetId())
                        
            return len(menu.GetMenuItems()) > 0
        
        m2d = []
        for x in range(menubar.GetMenuCount()):
            if not CleanMenu(menubar.GetMenu(x)):
                m2d.append(x)
        
        for x in range(len(m2d)-1, -1, -1):
            menubar.Remove(m2d[x])
        
        return menubar
    
    def OnMenuExt(self, event):
        mid = event.GetId()
        for emid, ecbf in self.menuext:
            if emid == mid:
                for fdmenu, fdid, fdcod, fddes in self.ftdif:
                    if fdmenu == mid:
                        ecbf(fdid)
                        #event.Skip()
                        return
    
    def OnMenuPers(self, event):
        self.LaunchMenuPers(event.GetId())
        #event.Skip()
    
    def LaunchMenuPers(self, menuid):
        if menuid in self.menupers:
            mp = self.menupers[menuid]
            fc = mp['frame']
            kw = {}
            for key in mp.keys():
                if key.startswith('frame_'):
                    kw[key] = mp[key]
            self.LaunchFrame(fc, **kw)
    
    def OnToolPers(self, event):
        self.LaunchToolPers(event.GetId())
        event.Skip()
    
    def LaunchToolPers(self, toolid):
        if toolid in self.toolpers:
            fc = self.toolpers[toolid]['frame']
            self.LaunchFrame(fc)
    
    def CreateStdToolBar(self):
        old = self.GetToolBar()
        if old:
            old.Destroy()
        tb = self.CreateToolBar(wx.TB_FLAT|wx.TB_HORIZONTAL|wx.TB_TEXT)
        tb.SetToolBitmapSize((48, 48))
        tb.SetMargins((2,2))
        return tb
    
    def CreateXToolBar(self):
        tb = None
        if self.toolpers:
            tb = self.CreateStdToolBar()
            err = False
            for tid in self.toollist:
                tp = self.toolpers[tid]
                if 'voice' in tp:
                    try:
                        voice = tp['voice']
                        desc = tp['desc']
                        bmp = tp['image']
                        t = tb.AddLabelTool(tid, voice, bmp(), wx.NullBitmap, wx.ITEM_NORMAL, "")
                        #t.SetToolTipString(tp['desc'])
                        self.Bind(wx.EVT_TOOL, self.OnToolPers, id=tid)
                    except:
                        pass
                elif 'separator' in tp:
                    if tp['separator']:
                        tb.AddSeparator()
        elif not self.menupers:
            
            from imgfac import ToolbarImagesFactory
            fac = ToolbarImagesFactory()
            w = 64
            
            def PU(x, d=True):
                return getattr(Env.Azienda.Login.userdata, x, d)
            
            tb = self.CreateStdToolBar()
            for id, bmp, cnd, lbl in (
                (ID_TB_EMIDOC,  fac.getEmiDocBitMap(w), PU('can_magazzins'), "Documenti"),
                (ID_TB_INTART,  fac.getIntArtBitMap(w), True,                "Prodotti",),
                (ID_TB_SCADCF,  fac.getScadCFBitMap(w), PU('can_contabint'), "Scadenzari"),
                (ID_TB_INCPAG,  fac.getIncPagBitMap(w), PU('can_contabins'), "Inc./Pag."),
                (ID_TB_CLIENT,  fac.getIntCliBitMap(w), True,                "Clienti"),
                (ID_TB_FORNIT,  fac.getIntForBitMap(w), True,                "Fornitori"),
                (ID_TB_INTSOTT, fac.getIntPdcBitMap(w), PU('can_contabint'), "P.d.C."),):
                if cnd:
                    tb.AddLabelTool(id, lbl, bmp, wx.NullBitmap, wx.ITEM_NORMAL, "")
            
            for func, cid in (
                (self.OnPdcInterrCli,              ID_TB_CLIENT),
                (self.OnPdcInterrFor,              ID_TB_FORNIT),
                (self.OnDataEntryMagazz,           ID_TB_EMIDOC),
                (self.OnInterrProdotto,            ID_TB_INTART),
                (self.OnDataEntryContabSaldaConto, ID_TB_INCPAG),
                (self.OnScadenzario,               ID_TB_SCADCF),
                (self.OnPdcInterrPdc,              ID_TB_INTSOTT),
                ):
                self.Bind(wx.EVT_TOOL, func, id=cid)
        if tb:
            tb.Realize()
    
    def OnGestPdc(self, event):
        from anag.pdc import PdcFrame
        self.LaunchFrame(PdcFrame)
    
    def OnGestPdcCee(self, event):
        from anag.pdc import PdcCeeFrame
        self.LaunchFrame(PdcCeeFrame)
    
    def OnGestStatPdc(self, event):
        from anag.statpdc import StatPdcFrame
        self.LaunchFrame(StatPdcFrame)
    
    def OnGestPdcStru(self, event):
        from anag.pdcstru import PdcStrutturaFrame
        self.LaunchFrame(PdcStrutturaFrame)
    
    def OnGestPdcRiclStru(self, event):
        from anag.pdcstru import PdcStrutturaRiclFrame
        self.LaunchFrame(PdcStrutturaRiclFrame)
    
    def OnGestCatCli(self, event):
        from anag.catcli import CatCliFrame
        self.LaunchFrame(CatCliFrame)
    
    def OnGestStatCli(self, event):
        from anag.statcli import StatCliFrame
        self.LaunchFrame(StatCliFrame)
    
    def OnGestClienti(self, event):
        from anag.clienti import ClientiFrame
        self.LaunchFrame(ClientiFrame)
    
    def OnGestDatiFiscaliClienti(self, event):
        from anag.clifor_datifisc import Clienti_DatiFiscaliFrame
        self.LaunchFrame(Clienti_DatiFiscaliFrame)
    
    def OnGestCatFor(self, event):
        from anag.catfor import CatForFrame
        self.LaunchFrame(CatForFrame)
    
    def OnGestStatFor(self, event):
        from anag.statfor import StatForFrame
        self.LaunchFrame(StatForFrame)
    
    def OnGestFornit(self, event):
        from anag.fornit import FornitFrame
        self.LaunchFrame(FornitFrame)
    
    def OnGestDatiFiscaliFornitori(self, event):
        from anag.clifor_datifisc import Fornitori_DatiFiscaliFrame
        self.LaunchFrame(Fornitori_DatiFiscaliFrame)
    
    def OnGestProd(self, event):
        from anag.prod import ProdFrame
        self.LaunchFrame(ProdFrame)
    
    def OnGestProdPromo(self, event):
        from anag.prodpromo import ProdPromoFrame
        self.LaunchFrame(ProdPromoFrame)
    
    def OnGestCatArt(self, event):
        from anag.catart import CatArtFrame
        self.LaunchFrame(CatArtFrame)
    
    def OnGestGruArt(self, event):
        from anag.gruart import GruArtFrame
        self.LaunchFrame(GruArtFrame)
    
    def OnGestInvStru(self, event):
        from anag.invstru import InvStrutturaFrame
        self.LaunchFrame(InvStrutturaFrame)
    
    def OnGestStatArt(self, event):
        from anag.statart import StatArtFrame
        self.LaunchFrame(StatArtFrame)
    
    def OnGestTipArt(self, event):
        from anag.tipart import TipArtFrame
        self.LaunchFrame(TipArtFrame)
    
    def OnGestMarArt(self, event):
        from anag.marart import MarArtFrame
        self.LaunchFrame(MarArtFrame)
    
    def OnGestTipList(self, event):
        from anag.tiplist import TipListFrame
        self.LaunchFrame(TipListFrame)
    
    def OnGestGruPrez(self, event):
        from anag.gruprez import GruPrezFrame
        self.LaunchFrame(GruPrezFrame)
    
    def OnGestCasse(self, event):
        from anag.casse import CasseFrame
        self.LaunchFrame(CasseFrame)
    
    def OnGestBanche(self, event):
        from anag.banche import BancheFrame
        self.LaunchFrame(BancheFrame)
    
    def OnGestEffetti(self, event):
        from anag.effetti import EffettiFrame
        self.LaunchFrame(EffettiFrame)
    
    def OnGestBilMas(self, event):
        from anag.bilmas import BilMasFrame
        self.LaunchFrame(BilMasFrame)
    
    def OnGestBilCon(self, event):
        from anag.bilcon import BilConFrame
        self.LaunchFrame(BilConFrame)
    
    def OnGestBriMas(self, event):
        from anag.brimas import BriMasFrame
        self.LaunchFrame(BriMasFrame)
    
    def OnGestBriCon(self, event):
        from anag.bricon import BriConFrame
        self.LaunchFrame(BriConFrame)
    
    def OnGestBilCee(self, event):
        from cfg.bilcee  import BilCeeFrame
        self.LaunchFrame(BilCeeFrame)
    
    def OnGestModPag(self, event):
        from anag.modpag import ModPagFrame
        self.LaunchFrame(ModPagFrame)
    
    def OnGestAliqIva(self, event):
        from anag.aliqiva import AliqIvaFrame
        self.LaunchFrame(AliqIvaFrame)
    
    def OnGestStati(self, event):
        from cfg.stati import StatiFrame
        self.LaunchFrame(StatiFrame)
    
    def OnGestPdcTip(self, event):
        from anag.pdctip import PdcTipFrame
        self.LaunchFrame(PdcTipFrame)
    
    def OnGestScadGrp(self, event):
        from anag.scadgrp import ScadGrpFrame
        self.LaunchFrame(ScadGrpFrame)
    
    def OnGestListini(self, event):
        from magazz.listini import ListiniFrame
        self.LaunchFrame(ListiniFrame)
    
    def OnGestStampaListino(self, event):
        from magazz.stalis import ListiniAttualiFrame
        self.LaunchFrame(ListiniAttualiFrame)
    
    def OnGestGrpCli(self, event):
        from magazz.griglie import GrigliaClientiFrame
        self.LaunchFrame(GrigliaClientiFrame)
    
    def OnGestGrpFor(self, event):
        from magazz.griglie import GrigliaFornitFrame
        self.LaunchFrame(GrigliaFornitFrame)
    
    def OnPrintGrpCli(self, event):
        from magazz.stagrip import GrigliaPrezziAttualiClientiFrame
        self.LaunchFrame(GrigliaPrezziAttualiClientiFrame)
    
    def OnPrintGrpFor(self, event):
        from magazz.stagrip import GrigliaPrezziAttualiFornitFrame
        self.LaunchFrame(GrigliaPrezziAttualiFornitFrame)
    
    def OnGestZone(self, event):
        from anag.zone import ZoneFrame
        self.LaunchFrame(ZoneFrame)

    def OnGestAgenti(self, event):
        from anag.agenti import AgentiFrame
        self.LaunchFrame(AgentiFrame)
    
    def OnGestSpeInc(self, event):
        from anag.speinc import SpeIncFrame
        self.LaunchFrame(SpeIncFrame)

    def OnGestMagazz(self, event):
        from anag.mag import MagazzFrame
        self.LaunchFrame(MagazzFrame)

    def OnGestTraCau(self, event):
        from anag.trasp import TraCauFrame
        self.LaunchFrame(TraCauFrame)

    def OnGestTraCur(self, event):
        from anag.trasp import TraCurFrame
        self.LaunchFrame(TraCurFrame)

    def OnGestTraAsp(self, event):
        from anag.trasp import TraAspFrame
        self.LaunchFrame(TraAspFrame)

    def OnGestTraPor(self, event):
        from anag.trasp import TraPorFrame
        self.LaunchFrame(TraPorFrame)

    def OnGestTraCon(self, event):
        from anag.trasp import TraConFrame
        self.LaunchFrame(TraConFrame)

    def OnGestTraVet(self, event):
        from anag.trasp import TraVetFrame
        self.LaunchFrame(TraVetFrame)

    def OnPdcInterrCli(self, event):
        from contab.pdcint import ClientiInterrFrame
        self.PdcRelShowInterrFrame(ClientiInterrFrame)

    def OnPdcInterrFor(self, event):
        from contab.pdcint import FornitInterrFrame
        self.PdcRelShowInterrFrame(FornitInterrFrame)

    def OnPdcInterrCas(self, event):
        from contab.pdcint import CasseInterrFrame
        self.PdcRelShowInterrFrame(CasseInterrFrame)
    
    def OnPdcInterrBan(self, event):
        from contab.pdcint import BancheInterrFrame
        self.PdcRelShowInterrFrame(BancheInterrFrame)

    def OnPdcInterrEff(self, event):
        from contab.pdcint import EffettiInterrFrame
        self.PdcRelShowInterrFrame(EffettiInterrFrame)

    def OnPdcInterrPdc(self, event):
        from contab.pdcint import PdcInterrFrame
        self.PdcRelShowInterrFrame(PdcInterrFrame)
    
    def OnPcfInterrCli(self, event):
        from contab.pdcint import ClientiInterrFrame
        self.PdcRelShowInterrFrame(ClientiInterrFrame, 'Scadenzario')

    def OnPcfInterrFor(self, event):
        from contab.pdcint import FornitInterrFrame
        self.PdcRelShowInterrFrame(FornitInterrFrame, 'Scadenzario')

    def OnBilVerif(self, event):
        from contab.bil import BilVerifFrame
        self.LaunchFrame(BilVerifFrame, centered=True)

    def OnBilGest(self, event):
        from contab.bil import BilGestFrame
        self.LaunchFrame(BilGestFrame, centered=True)

    def OnBilCee(self, event):
        from contab.bil import BilCeeFrame as BilRiclCeeFrame
        self.LaunchFrame(BilRiclCeeFrame, centered=True)

    def OnBilContr(self, event):
        from contab.bil import BilContrFrame
        self.LaunchFrame(BilContrFrame, centered=True)
    
    def OnBilVerifRicl(self, event):
        from contab.bilric import BilVerifFrame as BilVerifRiclFrame
        self.LaunchFrame(BilVerifRiclFrame, centered=True)

    def OnBilGestRicl(self, event):
        from contab.bilric import BilGestFrame as BilGestRiclFrame
        self.LaunchFrame(BilGestRiclFrame, centered=True)

    def OnBilContrRicl(self, event):
        from contab.bilric import BilContrFrame as BilContrRiclFrame
        self.LaunchFrame(BilContrRiclFrame, centered=True)
    
    def OnScadenzario(self, event):
        from contab.scadenzario import ScadenzarioFrame
        self.LaunchFrame(ScadenzarioFrame)
    
    def OnScadenzarioGruppo(self, event):
        from contab.scadenzario import ScadenzarioGruppoFrame
        self.LaunchFrame(ScadenzarioGruppoFrame)
    
    def OnQuadPcfCont(self, event):
        from contab.quadpcfcont import PdcQuadPcfContFrame
        self.LaunchFrame(PdcQuadPcfContFrame)
    
    def OnQuadRegCont(self, event):
        from contab.quadreg import QuadRegFrame
        self.LaunchFrame(QuadRegFrame)
    
    def OnScadGlobal(self, event):
        from contab.scadglobal import ScadGlobalFrame
        self.LaunchFrame(ScadGlobalFrame)
    
    def OnCalcIntPcf(self, event):
        from contab.calcintpcf import CalcIntPcfFrame
        self.LaunchFrame(CalcIntPcfFrame)
    
    def OnSituazioneFidiClienti(self, event):
        from contab.sitfidicli import SitFidiClientiFrame
        self.LaunchFrame(SitFidiClientiFrame)
    
    def OnScadGlobalIncassi(self, event):
        from contab.scadglobal import ScadGlobalIncassiFrame
        self.LaunchFrame(ScadGlobalIncassiFrame)
    
    def OnScadGlobalPagamenti(self, event):
        from contab.scadglobal import ScadGlobalPagamentiFrame
        self.LaunchFrame(ScadGlobalPagamentiFrame)
    
    def OnScadGlobalEffettiDaEm(self, event):
        from contab.scadglobal import ScadGlobalEffettiDaEmettereFrame
        self.LaunchFrame(ScadGlobalEffettiDaEmettereFrame)
    
    def OnScadGlobalEffettiEmessi(self, event):
        from contab.scadglobal import ScadGlobalEffettiEmessiFrame
        self.LaunchFrame(ScadGlobalEffettiEmessiFrame)
    
    def OnScadGlobalEffettiInsoluti(self, event):
        from contab.scadglobal import ScadGlobalEffettiInsolutiApertiFrame
        self.LaunchFrame(ScadGlobalEffettiInsolutiApertiFrame)
    
    def OnCtrCassa(self, event):
        from contab.ctrcassa import CtrCassaFrame
        self.LaunchFrame(CtrCassaFrame)

    def OnRegIva(self, event):
        from contab.regiva import RegIvaFrame
        self.LaunchFrame(RegIvaFrame)

    def OnLiqIva(self, event):
        from contab.liqiva import LiqIvaFrame
        self.LaunchFrame(LiqIvaFrame)

    #===========================================================================
    # def OnAllegati(self, event):
    #    from contab.alleg import AllegatiFrame
    #    self.LaunchFrame(AllegatiFrame)
    #===========================================================================

    def OnCtrIvaSeq(self, event):
        from contab.ivaseq import CtrIvaSeqFrame
        self.LaunchFrame(CtrIvaSeqFrame)
    
    def OnIntRegCon(self, event):
        from contab.intreg import IntRegConFrame
        self.LaunchFrame(IntRegConFrame)

    def OnIntRegIva(self, event):
        from contab.intreg import IntRegIvaFrame
        self.LaunchFrame(IntRegIvaFrame)
    
    def OnAliqRegIva(self, event):
        from contab.intreg import IntAliqIvaFrame
        self.LaunchFrame(IntAliqIvaFrame)

    def OnEmiEffetti(self, event):
        from eff.effetti import EmiEffettiFrame
        self.LaunchFrame(EmiEffettiFrame)

    def OnAccorpaEffetti(self, event):
        from eff.accorpa import AccorpaFrame as AccorpaEffettiFrame
        self.LaunchFrame(AccorpaEffettiFrame)

    def OnMastriSottoconto(self, event):
        from contab.mastri import MastriSottocontoFrame
        self.LaunchFrame(MastriSottocontoFrame)
        
    def OnGiornaleGenerale(self, event):
        from contab.giobol import GiornaleFrame
        self.LaunchFrame(GiornaleFrame)
    
    def OnFatturatoAcqVen(self, event):
        from contab.fatclifor import FatturatoContabileClientiFornitFrame
        self.LaunchFrame(FatturatoContabileClientiFornitFrame)
    
    def OnVendAziPriv(self, event):
        from contab.vendazipriv import VendAziPrivFrame
        self.LaunchFrame(VendAziPrivFrame)
    
    def OnSpesometro(self, event):
        from contab.spesometro_2013 import SpesometroFrame
        self.LaunchFrame(SpesometroFrame)
    
    def OnCfgAutoContab( self, event ):
        from cfg.automat import AutomatContabFrame
        self.LaunchFrame(AutomatContabFrame)

    def OnCfgAutoMagazz( self, event ):
        from cfg.automat import AutomatMagazzFrame
        self.LaunchFrame(AutomatMagazzFrame)

    def OnCfgRegIva( self, event ):
        from cfg.regiva import RegIvaFrame as CfgRegIvaFrame
        self.LaunchFrame(CfgRegIvaFrame)        
        
    def OnCfgProgrIva( self, event ):
        from cfg.progriva import ProgrLiqIvaFrame
        self.LaunchFrame(ProgrLiqIvaFrame)
    
    def OnCfgAzienda( self, event ):
        from cfg.azisetup import AziendaSetupDialog
        dlg = self.LaunchFrame(AziendaSetupDialog, show=False)
        if dlg:
            dlg.ShowModal()
    
    def OnCfgEmail(self, event):
        from cfg.comsetup import EmailSetupDialog
        dlg = self.LaunchFrame(EmailSetupDialog, show=False)
        if dlg:
            dlg.ShowModal()
    
    def OnCfgXmpp(self, event):
        from cfg.comsetup import XmppSetupDialog
        dlg = self.LaunchFrame(XmppSetupDialog, show=False)
        if dlg:
            dlg.ShowModal()
    
    def OnCfgDocsEmail(self, event):
        from cfg.docsemail import DocsEmailSetupDialog
        dlg = self.LaunchFrame(DocsEmailSetupDialog, show=False)
        if dlg:
            dlg.ShowModal()
    
    def OnCfgTipiEvento(self, event):
        from cfg.eventi import TipiEventoFrame
        self.LaunchFrame(TipiEventoFrame)
    
    def OnCfgEventManager(self, event):
        from cfg.eventi import EventManagerFrame
        self.LaunchFrame(EventManagerFrame)
    
    def OnCfgLicense( self, event ):
        from cfg.license import LicenseDialog
        dlg = self.LaunchFrame(LicenseDialog, show=False)
        dlg.setConfig(Env.Azienda.license)
        if dlg:
            dlg.ShowModal()
    
    def OnCfgActivationCodes( self, event ):
        from cfg.license import ActivationCodesDialog
        dlg = self.LaunchFrame(ActivationCodesDialog, show=False)
        dlg.setConfig(Env.Azienda.license)
        if dlg:
            dlg.ShowModal()
    
    def OnCfgCauContab( self, event ):
        from cfg.caucontab import CauContabFrame
        self.LaunchFrame(CauContabFrame)
    
    def OnCfgProgrContab( self, event ):
        from cfg.progrcon import ProgrContabFrame
        self.LaunchFrame(ProgrContabFrame)
    
    def OnCfgMassimaliSpesometro(self, event):
        from cfg.spesometro_2011 import MassimaliSpesometroFrame
        self.LaunchFrame(MassimaliSpesometroFrame)
    
    def OnCfgCauMagazz( self, event ):
        from cfg.caumagazz import CauMagazzFrame
        self.LaunchFrame(CauMagazzFrame)

    def OnCfgFtDif( self, event ):
        from cfg.ftdif import FtDifFrame as CfgFtDifFrame
        self.LaunchFrame(CfgFtDifFrame)
    
    def OnCfgWorkstation( self, event ):
        from cfg.wksetup import WorkstationSetupDialog
        frame = self.LaunchFrame(WorkstationSetupDialog, show=False)
        frame.setConfig(Env.Azienda.config)
        frame.ShowModal()
        frame.Destroy()
    
    def OnCfgUpdates(self, event):
        from prgup import ProgramUpdateSetupDialog as CfgUpdatesDialog
        frame = self.LaunchFrame(CfgUpdatesDialog, show=False)
        frame.setConfig(Env.Azienda.config)
        check = frame.ShowModal() == wx.ID_OK
        frame.Destroy()
        if check:
            self.AutoCheckUpdates()
    
    def OnCfgPdcRange( self, event ):
        from cfg.pdcrange import PcdRangeFrame
        self.LaunchFrame(PcdRangeFrame)
    
    def OnDataEntryContabIva(self, event):
        bt = Env.Azienda.BaseTab
        if bt.TIPO_CONTAB == "O":
            from contab.dataentry_i_o import ContabFrameTipo_I_O as RegContabFrameIva_O
            self.LaunchFrame(RegContabFrameIva_O)
        elif bt.TIPO_CONTAB == "S":
            from contab.dataentry_i_s import ContabFrameTipo_I_S as RegContabFrameIva_S
            self.LaunchFrame(RegContabFrameIva_S)
        else:
            awu.MsgDialog(None, message="Manca setup contabilità ordinaria/semplificata")

    def OnDataEntryContabSaldaConto(self, event):
        from contab.dataentry_sc import ContabFrameTipo_SC as RegContabFrameSC
        self.LaunchFrame(RegContabFrameSC)

    def OnDataEntryContabComposto(self, event):
        from contab.dataentry_c import ContabFrameTipo_C as RegContabFrameC
        self.LaunchFrame(RegContabFrameC)
    
    def OnDataEntryContabSolaIva(self, event):
        from contab.dataentry_i_si import ContabFrameTipo_I_SI as RegContabFrameIva_SI
        self.LaunchFrame(RegContabFrameIva_SI)
        
    def OnPcfNew(self, event):
        from contab.pcf import PcfDialog
        dlg = self.LaunchFrame(PcfDialog, show=False, centered=True)
        dlg.ShowModal()
        dlg.Destroy()
    
    def OnDataEntryMagazz(self, event):
        from magazz.dataentry_o import MagazzFrame_O as DocMagazzFrame
        self.LaunchFrame(DocMagazzFrame)
    
    def OnInterrProdotto(self, event):
        from magazz.prodint import ProdInterrFrame
        self.LaunchFrame(ProdInterrFrame)
    
    def OnIntDocMag(self, event):
        from magazz.docint import DocIntFrame
        self.LaunchFrame(DocIntFrame)
    
    def OnIntDocVet(self, event):
        from magazz.vetint import TraVetIntFrame
        self.LaunchFrame(TraVetIntFrame)
    
    def OnIntMovMag(self, event):
        from magazz.movint import MovIntFrame
        self.LaunchFrame(MovIntFrame)
    
    def OnIntEvaMag(self, event):
        from magazz.evaint import EvaIntFrame
        self.LaunchFrame(EvaIntFrame)
    
    def OnIntInvPres(self, event):
        from magazz.invpres import InventarioPresuntoFrame
        self.LaunchFrame(InventarioPresuntoFrame)
    
    def OnIntInvent(self, event):
        from magazz.invent import InventFrame
        self.LaunchFrame(InventFrame)
    
    def OnIntSottoSc(self, event):
        from magazz.sottosc import SottoscortaFrame
        self.LaunchFrame(SottoscortaFrame)
    
    def OnIntMagSrcDes(self, event):
        from anag.destsrc import DestinazSearchFrame
        self.LaunchFrame(DestinazSearchFrame)
    
    def OnIntMagProvAge(self, event):
        from magazz.provage.provvig import ProvvigAgentiFrame
        self.LaunchFrame(ProvvigAgentiFrame)
        
    def OnProdRiPro(self, event):
        from magazz.prodripro import ProdRiProFrame
        self.LaunchFrame(ProdRiProFrame)
    
    def OnProdRiCos(self, event):
        from magazz.prodricos import ProdRiCosFrame
        self.LaunchFrame(ProdRiCosFrame)
    
    def OnPdcFtProd(self, event):
        from magazz.stat.prodvencli import ProdVenCliFrame
        self.LaunchFrame(ProdVenCliFrame)
    
    def OnStatFatCli(self, event):
        from magazz.stat.fatpdc import FatturatoClientiFrame
        self.LaunchFrame(FatturatoClientiFrame)
    
    def OnStatFatCliCatArt(self, event):
        from magazz.stat.fatpdc import FatturatoCliCatArtFrame
        self.LaunchFrame(FatturatoCliCatArtFrame)
    
    def OnStatFatPro(self, event):
        from magazz.stat.fatpro import FatturatoProdottiFrame
        self.LaunchFrame(FatturatoProdottiFrame)
    
    def OnStatFatProCli(self, event):
        from magazz.stat.fatpro import FatturatoProCliFrame
        self.LaunchFrame(FatturatoProCliFrame)
    
    def OnStatFatAge(self, event):
        from magazz.stat.fatage import FatturatoAgentiFrame
        self.LaunchFrame(FatturatoAgentiFrame)
    
    def OnStatFatCatArt(self, event):
        from magazz.stat.fatcatart import FatturatoCatArtFrame
        self.LaunchFrame(FatturatoCatArtFrame)
    
    def OnStatValCosAcq(self, event):
        from magazz.stat.valcosacq import ValutaCostiFrame
        self.LaunchFrame(ValutaCostiFrame)
    
    def OnStatValPreApp(self, event):
        from magazz.stat.valpreapp import ValutaPrezziFrame
        self.LaunchFrame(ValutaPrezziFrame)
    
    def OnStatReddVend(self, event):
        from magazz.stat.reddvend import ReddVendFrame
        self.LaunchFrame(ReddVendFrame)
    
    def OnPdcIntMagCli(self, event):
        from contab.pdcint import ClientiInterrFrame
        self.PdcRelShowInterrFrame(ClientiInterrFrame, 'Magazzino')
    
    def OnPdcSituazioneAcconti(self, event):
        from magazz.sitacc import SituazioneGlobaleAccontiFrame
        self.LaunchFrame(SituazioneGlobaleAccontiFrame)
        
    def OnPdcIntMagFor(self, event):
        from contab.pdcint import FornitInterrFrame
        self.PdcRelShowInterrFrame(FornitInterrFrame, 'Magazzino')

    def OnStaDif(self, event):
        from magazz.stadif import StaDifFrame
        self.LaunchFrame(StaDifFrame)
    
    def OnBarCodesSpot(self, event):
        from magazz.barcodes import EtichetteProdottiFrame
        self.LaunchFrame(EtichetteProdottiFrame)
    
    def OnChiusContabGenMov(self, event):
        from contab.chiusure.genmov import GeneraMovimentiFrame as ChiusContabGenMovFrame
        self.LaunchFrame(ChiusContabGenMovFrame)
    
    def OnChiusContabSovrapp(self, event):
        from contab.chiusure.sovrapp import SovrapposizioneFrame as ChiusContabSovrappFrame
        self.LaunchFrame(ChiusContabSovrappFrame)
    
    def OnChiusContabAnnuale(self, event):
        from contab.chiusure.chiudieserc import ChiusuraContabileFrame as ChiusContabAnnualeFrame
        self.LaunchFrame(ChiusContabAnnualeFrame)
    
    def OnChiusContabIVA(self, event):
        from contab.chiusure.iva import ChiusuraIVAFrame
        self.LaunchFrame(ChiusuraIVAFrame)
        
    def OnChiusMagazzConsCosti(self, event):
        from magazz.chiusure.consocos import ConsolidamentoCostiFrame
        self.LaunchFrame(ConsolidamentoCostiFrame)
    
    def OnChiusMagazzEditGiacenze(self, event):
        from magazz.chiusure.editgiac import EditGiacenzeFrame
        self.LaunchFrame(EditGiacenzeFrame)
    
    def OnChiusMagazzGenMoviIni(self, event):
        from magazz.chiusure.genmov import GeneraMovimentiFrame
        self.LaunchFrame(GeneraMovimentiFrame)
    
    def OnBackupExplorer(self, event):
        from backexp import BackupExplorerFrame
        self.LaunchFrame(BackupExplorerFrame)
    
    def OnChangeIva(self, event):
        from strumenti.changeiva import ChangeIvaFrame
        self.LaunchFrame(ChangeIvaFrame)            
            
    
    def OnHelp(self, event):
        a = wx.GetApp()
        a.HelpBuilder_ShowObjectHelp()
    
    def OnAbout(self, event):
        dialog = AboutDialog(self)
        dialog.CentreOnScreen()
        dialog.ShowModal()
        dialog.Destroy()
    
    def OnProgramUpdate(self, event):
        from prgup import ProgramUpdateDialog
        dialog = ProgramUpdateDialog(self)
        dialog.ShowModal()
        dialog.Destroy()
    
    def OnQuit(self, event):
        self.Close(True)
    
    def OnCloseWindow(self, event):
        quit = True
        #frames and dialogs cleanup test
        for child in self.GetChildren():
            if isinstance(child, (wx.Frame, wx.Dialog,)):
                if child.IsShown():
                    CanClose = 'CanClose'
                    if hasattr(child, CanClose):
                        if not getattr(child, CanClose)():
                            quit = False
                            break
        if quit:
            event.Skip()
    
    def LaunchFrame(self, frameclass, size=None, show=True, centered=False, **kwargs):
#        wait = awu.WaitDialog(self, message="Caricamento modulo in corso.",
#                              style=wx.SIMPLE_BORDER)
        wx.BeginBusyCursor()
        frame = None
        err = None
        try:
            if True:#try:
                frame = frameclass(self, **kwargs)
                if size:
                    frame.SetSize(size)
                if centered:
                    frame.CenterOnScreen()
#            except Exception, e:
#                err = '\n'.join(map(str, e.args))
        finally:
#            wait.Destroy()
            wx.EndBusyCursor()
        if err:
            awu.MsgDialog(self, message=err, style=wx.ICON_ERROR)
        else:
            if show and frame is not None:
                s = frame.GetSize()
                frame.SetSize((s[0]+1, s[1]+1))
                frame.SetSize(s)
                frame.Show()
                frame.SetFocus()
        return frame
    
    def PdcRelShowInterrFrame(self, frameclass, page='Mastro', size=None):
        f = self.LaunchFrame(frameclass, centered=True, show=False, size=size)
        if f:
            wz = f.FindWindowByName('workzone')
            if wz:
                pages = [n for n in range(wz.GetPageCount())
                         if wz.GetPageText(n) == page]
                if pages:
                    wz.SetSelection(pages[0])
            f.Layout()
            f.Show()


# ------------------------------------------------------------------------------


class AboutDialog(aw.Dialog):
    def __init__(self, *args, **kwargs):
        kwargs['title'] = 'About'
        kwargs['style'] = wx.DEFAULT_DIALOG_STYLE
        aw.Dialog.__init__(self, *args, **kwargs)
        p = AboutPanel(self)
        self.AddSizedPanel(p)
