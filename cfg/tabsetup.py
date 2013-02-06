#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         cfg/tabsetup.py
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

import cfg.tabsetup_wdr as wdr

import Env
adb = Env.adb

import version as ver


ADEG_MISSINGTABLE =  0
ADEG_MISSINGFIELD =  1
ADEG_WRONGTYPE =     2
ADEG_WRONGLENGHT =   3
ADEG_WRONGDECIMALS = 4
ADEG_INDEX =         5
ADEG_REINDEX =       6



class TabSetupPanel(aw.Panel):
    """
    Setup tabelle
    """
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.TabSetupPanelFunc(self)
        
        ci = lambda x: self.FindWindowById(x)
        
        pos = [0,0]
        
        #p = aw.Panel(ci(wdr.ID_SCROLLED), pos=pos)
        #wdr.RowTitleFunc(p)
        #pos[1] += p.GetSize()[1]
        
        ci(wdr.ID_VERSION).SetLabel(Env.__version__)
        
        self.tabs = {}
        self.adeg = {}
        
        bt = Env.Azienda.BaseTab
        
        for name, desc, stru, index, constr, voice in bt.tabelle:
            p = aw.Panel(ci(wdr.ID_SCROLLED), pos=pos)
            wdr.RowTableFunc(p)
            id1, id2, id3 = wx.NewId(), wx.NewId(), wx.NewId()
            ci(wdr.ID_TABNAME).SetId(id1)
            ci(wdr.ID_TABDESC).SetId(id2)
            ci(wdr.ID_TABSTAT).SetId(id3)
            ci(id1).SetLabel(name)
            ci(id2).SetLabel(desc)
            ci(id3).SetLabel('')
            pos[1] += p.GetSize()[1]
            self.tabs[name] = id3
        
        h = p.GetSize()[1]
        ci(wdr.ID_SCROLLED).SetScrollbars(\
            1, h, 20, len(bt.tabelle), 0, 0 )
        ci(wdr.ID_SHOWDIFF).Show(False)
        
        self.Fit()
        self.Layout()

    def Analizza(self):
        
        ci = lambda x: self.FindWindowById(x)
        
        blobs = ("BLOB", "LONGBLOB", "VARBINARY", "VARCHAR", "TEXT")
        ctradeg = ci(wdr.ID_NUMADEG)
        nta = 0
        adeg = []
        
        #MySQL SHOW INDEXES - struttura analisi:
        I_TABLE =      0
        I_NOTUNIQUE =  1
        I_KEYNAME =    2
        I_SEQUENCE =   3
        I_COLUMN =     4
        I_COLLATION =  5
        I_CARDINAL =   6
        I_SUBPART =    7
        I_PACKED =     8
        I_NULL =       9
        I_INDEXTYPE = 10
        I_COMMENT =   11
        
        bt = Env.Azienda.BaseTab
        
        for name, desc, stru, index, constr, voice in bt.tabelle:
            
            adeg = []
            tabchange = tabcreate = False
            
            try:
                
                status = ci(self.tabs[name])
                status.SetLabel('Analisi...')
                self.Update()
                wx.Yield()
                
                tab = adb.DbTable(name, writable=False)
                tab.Get(-1)
                tabchange = False
                tabcreate = False
                struphys = tab._GetStructure()
                
                #controllo struttura campi
                for fname, ftype, flen, fdec, fnote, fspec in stru:
                    
                    change = False
                    
                    #test esistenza campo
                    try:
                        n = aw.awu.ListSearch(struphys, lambda x: x[0] == fname)
                    except IndexError:
                        adeg.append((fname, ADEG_MISSINGFIELD))
                        change = True
                    
                    #test congruenza tipologia
                    if not change:
                        if not struphys[n][1] == "CHAR" and ftype == "STRING":
                            change = struphys[n][1] != ftype and not\
                                   (struphys[n][1] in blobs and ftype in blobs)
                            if change:
                                adeg.append((fname, ADEG_WRONGTYPE))
                    
                    #test lunghezza
                    if not change and flen:
                        change = struphys[n][2] < (flen + (fdec or 0))
                        if change:
                            adeg.append((fname, ADEG_WRONGLENGHT))
                    
                    #test decimali
                    if not change and type(fdec) is int:
                        change = struphys[n][3] < fdec
                        if change:
                            adeg.append((fname, ADEG_WRONGDECIMALS))
                    
                    if change:
                        tabchange = True
                
                #controllo indici
                c = tab._info.db._dbCon.cursor()
                c.execute("SHOW INDEXES FROM %s" % name)
                rsi = c.fetchall()
                for i, (indtype, indexpr) in enumerate(index):
                    if "PRIMARY" in indtype:
                        indname = "PRIMARY"
                        keydesc = "primaria"
                    else:
                        indname = "index%d" % i
                        keydesc = "#%d" % i
                    expr = ''
                    for r in rsi:
                        if r[I_KEYNAME] == indname:
                            expr += ','+r[I_COLUMN]
                            isun = not r[I_NOTUNIQUE]
                    if expr: expr = expr[1:]
                    do = not expr == indexpr
                    if not do:
                        stun = ("UNIQUE" in indtype or "PRIMARY" in indtype)
                        do = (stun and not isun) or (not stun and isun)
                    if do:
                        if expr:
                            adegtype = ADEG_REINDEX
                        else:
                            adegtype = ADEG_INDEX
                        adeg.append(("Chiave "+keydesc, adegtype, i))
                        tabchange = True
                c.close()
                
            except Exception, e:
                #if '1146' in e.args[0]:
                err = e.args[0]
                if type(err) in (list, tuple):
                    err = err[0]
                if '1146' in err:
                    adeg.append(('-', ADEG_MISSINGTABLE))
                    tabcreate = True
                else:
                    aw.awu.MsgDialog(self,\
                                     """Errore durante la lettura della """
                                     """tabella %s\n%s"""
                                     % (name, repr(e.args)))
                    p = self.GetParent()
                    if p.IsModal():
                        p.EndModal(2)
                    else:
                        p.Close()
            
            if tabchange:
                self.adeg[name] = adeg
                label = "DA ADEGUARE"
                nta += 1
                
            elif tabcreate:
                self.adeg[name] = adeg
                label = "DA CREARE"
                nta += 1
                
            else:
                label = "OK"
            
            if nta > 0:
                ctradeg.SetLabel("%d tabelle da adeguare - Analisi in corso..."\
                                 % nta)
                ctradeg.SetForegroundColour('red')
            status.SetLabel(label)
            self.Update()
            wx.Yield()
        
        but = ci(wdr.ID_SHOWDIFF)
        if nta > 0:
            ctradeg.SetLabel("""%d tabelle da adeguare""" % nta)
            but.SetLabel("Prosegui...")
            self.Bind(wx.EVT_BUTTON, self.OnShowDiff, but)
        else:
            ctradeg.SetLabel(
                """Tutte le tabelle sono congruenti con questa versione.""")
            ctradeg.SetForegroundColour('blue')
            but.SetLabel("Chiudi")
            self.Bind(wx.EVT_BUTTON, self.OnClose, but)
        but.Show()
    
    def OnShowDiff(self, event):
        self.GetParent().EndModal(2)
    
    def OnClose(self, event):
        self.GetParent().EndModal(1)


# ------------------------------------------------------------------------------


class TabSetupDialog(aw.Dialog):
    """
    Dialog Setup tabelle.
    """
    def __init__(self, *args, **kwargs):
        kwargs['title'] = "Setup tabelle"
        if not kwargs.has_key('style') and len(args) < 5:
            kwargs['style'] = wx.DEFAULT_DIALOG_STYLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = TabSetupPanel(self, -1)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()
    
    def ShowModal(self):
        self.Show()
        self.panel.Analizza()
        self.Show(False)
        return aw.Dialog.ShowModal(self)

    def EndModal(self, ret):
        if ret == 2:
            dlg = AdeguaDialog(self.panel.adeg)
            ret = dlg.ShowModal()
            dlg.Destroy()
        self.PerformAdaptations()
        adb.dbtable.ClearCache()
        aw.Dialog.EndModal(self, ret)

    def PerformAdaptations(self):
        """
        Esegue gli adattamenti da struttura precedente, una volta che le
        strutture sono state adattate alla versione attuale.
        """
        ok = True
        
        bt = Env.Azienda.BaseTab
        
        keyver = wx.GetApp().keyver
        setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable='True')
        
        if setup.Retrieve("setup.chiave=%s", keyver) and setup.OneRow():
            db = setup._info.db
            
            oldver, oldmod = setup.codice, setup.descriz
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'0.9.45' and ok:
                ok = db.Execute("""
                UPDATE %s SET viscosto=0, visgiac=0, vislistini=0, visultmov=0
                """ % bt.TABNAME_CFGMAGDOC)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'0.9.66' and ok:
                do = db.Execute("""
                INSERT INTO %s (id,codice,descriz,calcpc,calclis) 
                     VALUES (1,'1','STANDARD','P','P')
                """ % bt.TABNAME_GRUPREZ)
                if do:
                    ok = db.Execute("""
                    UPDATE %s SET id_gruprez=1
                    """ % bt.TABNAME_PROD)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'0.9.74' and ok:
                do = db.Execute("""
                INSERT INTO %s (chiave,descriz) VALUES ('mageanprefix','22')
                """ % bt.TABNAME_CFGSETUP)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.0.11' and ok:
                do = db.Execute("""
                ALTER TABLE `x4`.`aziende` 
                 ADD COLUMN `modname` VARCHAR(20) AFTER `codice`
                """)
                if do:
                    do = db.Execute("""
                    UPDATE `x4`.`aziende` SET modname=%s
                    """, ver.MODVERSION_NAME or None)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.0.19' and ok:
                if db.Retrieve("""
                SELECT id FROM `x4`.`utenti` 
                 ORDER BY codice
                """):
                    uid = [r[0] for r in db.rs]
                    tpd = adb.DbTable(bt.TABNAME_CFGMAGDOC, 'tipdoc')
                    from cfg.dbtables import PermessiUtenti
                    p = PermessiUtenti()
                    if tpd.Retrieve():
                        for tpd in tpd:
                            p.Reset()
                            p.SetAmbito('caumagazz')
                            p.SetIdRel(tpd.id)
                            for u in uid:
                                p.CreateNewRow()
                                p.id_utente = u
                                p.leggi = 1
                                p.scrivi = 1
                            p.Save()
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.0.98' and ok:
                for tabkey, envkey, val in (('opttabsearch', 'OPTTABSEARCH', 1),
                                            ('optdigsearch', 'OPTDIGSEARCH', 0),):
                    db.Execute("""
                    INSERT INTO %s (chiave, flag) VALUES (%%s,%%s)""" % bt.TABNAME_CFGSETUP,
                                                                       (tabkey, val,))
                    setattr(bt, envkey, val)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.1.00' and ok:
                e = adb.DbTable(bt.TABNAME_EFFETTI, 'eff')
                e.Retrieve()
                for e in e:
                    b = e.id_banca
                    if b:
                        if e.id_caus:
                            db.Execute("UPDATE pcf SET id_effpdc=%d WHERE id_effban=%d AND (SELECT id_caus FROM contab_h WHERE contab_h.id=pcf.id_effreg)=%%s" % (e.id, b), (e.id_caus,))
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.1.14' and ok:
                db.Execute("UPDATE cfgcontab SET camsegr1=0 WHERE camsegr1 IS NULL")
                db.Execute("UPDATE cfgcontab SET quaivanob=0 WHERE quaivanob IS NULL")
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.1.32':
                
                #creo tab.cfg.email su db x4
                db.Execute("""
CREATE TABLE IF NOT EXISTS `x4`.`cfgmail` (
  `id` int(6) NOT NULL auto_increment COMMENT 'ID',
  `azienda`  char(16)   default NULL COMMENT 'Codice Azienda',
  `sender`   char(128)  default NULL COMMENT 'Indirizzo Mittente',
  `smtpaddr` char(64)   default NULL COMMENT 'Indirizzo Server SMTP',
  `smtpport` int(4)     default NULL COMMENT 'Porta Server SMTP',
  `authreq`  tinyint(1) default NULL COMMENT 'Autorizzazione richiesta',
  `authuser` char(128)  default NULL COMMENT 'Nome utente per login smtp',
  `authpswd` char(128)  default NULL COMMENT 'Password per login smtp',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `index1` (`azienda`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Setup SMTP'
""")
                
                #creo tab.cfg.xmpp su db x4
                db.Execute("""
CREATE TABLE IF NOT EXISTS `x4`.`cfgxmpp` (
  `id`         int(6) NOT NULL auto_increment COMMENT 'ID',
  `azienda`    char(16)   default NULL COMMENT 'Codice Azienda',
  `xmppaddr`   char(128)  default NULL COMMENT 'URL Server XMPP',
  `xmppport`   int(5)     default NULL COMMENT 'Porta Server XMPP',
  `authuser`   char(128)  default NULL COMMENT 'Nome utente per login smtp',
  `authpswd`   char(128)  default NULL COMMENT 'Password per login XMPP',
  `onlineonly` tinyint(1) default NULL COMMENT 'Flag invio solo a contatto online',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `index1` (`azienda`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Setup XMPP'
""")
        
                #inserisco opzione notifiche in setup azienda, per default=0
                for tabkey, envkey, val in (('optnotifiche', 'OPTNOTIFICHE', 0),):
                    db.Execute("""
                    INSERT INTO %s (chiave, flag) VALUES (%%s,%%s)""" % bt.TABNAME_CFGSETUP,
                                                                       (tabkey, val,))
                    setattr(bt, envkey, val)
                
                db.Execute("""
                UPDATE %s SET lendescriz=60
                """ % bt.TABNAME_CFGMAGMOV)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.1.34':
                
                #creo tab. bilancio cee su db x4
                db.Execute("""
CREATE TABLE IF NOT EXISTS `x4`.`bilcee` (
  `id`         int(6) NOT NULL 
                      auto_increment    COMMENT 'ID PDC CEE',
  `codice`     char(9)     default NULL COMMENT 'Codice',
  `descriz`    char(128)   default NULL COMMENT 'Descrizione',
  `sezione`    char(1)     default NULL COMMENT 'Sezione',
  `voce`       char(1)     default NULL COMMENT 'Voce',
  `capitolo`   char(4)     default NULL COMMENT 'Capitolo',
  `dettaglio`  char(2)     default NULL COMMENT 'Dettaglio',
  `subdett`    char(1)     default NULL COMMENT 'Sub-dettaglio',
  `selectable` tinyint(1)  default NULL COMMENT 'Flag selezionabile in pdc',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `index1` (`codice`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Bilancio CEE'
""")
            
            test = adb.DbTable('x4.bilcee')
            test.AddLimit(1)
            test.Retrieve()
            if test.IsEmpty():
                db.Execute("""
INSERT INTO `x4`.`bilcee` 
(`id`,`codice`,`descriz`,`sezione`,`voce`,`capitolo`,`dettaglio`,`subdett`,`selectable`) 
VALUES 
 (307,"1","ATTIVO","1","","","","",0),
 (308,"1A","CREDITI VERSO SOCI PER VERSAMENTI ANCORA DOVUTI","1","A","","","",0),
 (309,"1A      a","PARTE RICHIAMATA","1","A","","","a",1),
 (310,"1A      b","PARTE NON RICHIAMATA","1","A","","","b",1),
 (311,"1B","IMMOBILIZZAZIONI","1","B","","","",0),
 (312,"1BI","IMMOBILIZZAZIONI IMMATERIALI","1","B","I","","",0),
 (313,"1BI   01","COSTI DI IMPIANTO E DI AMPLIAMENTO","1","B","I","01","",1),
 (314,"1BI   02","COSTI DI RICERCA, DI SVILUPPO E DI PUBBLICITA'","1","B","I","02","",1),
 (315,"1BI   03","DIRITTI BREV. INDUSTR. E DIR. UTILIZZO OPERE DELL'INGEGNO","1","B","I","03","",1),
 (316,"1BI   04","CONCESSIONI, LICENZE, MARCHI E DIRITTI SIMILI","1","B","I","04","",1),
 (317,"1BI   05","AVVIAMENTO","1","B","I","05","",1),
 (318,"1BI   06","IMMOBILIZZAZIONI IN CORSO E ACCONTI","1","B","I","06","",1),
 (319,"1BI   07","ALTRE","1","B","I","07","",1),
 (320,"1BII","IMMOBILIZZAZIONI MATERIALI","1","B","II","","",0),
 (321,"1BII  01","TERRENI E FABBRICATI","1","B","II","01","",1),
 (322,"1BII  02","IMPIANTI E MACCHINARIO","1","B","II","02","",1),
 (323,"1BII  03","ATTREZZATURE INDUSTRIALI E COMMERCIALI","1","B","II","03","",1),
 (324,"1BII  04","ALTRI BENI","1","B","II","04","",1),
 (325,"1BII  05","IMMOBILIZZAZIONI IN CORSO E ACCONTI","1","B","II","05","",1),
 (326,"1BIII","IMMOBILIZZAZIONI FINANZIARIE","1","B","III","","",0),
 (327,"1BIII 01","PARTECIPAZIONI","1","B","III","01","",0),
 (328,"1BIII 01a","IMPRESE CONTROLLATE","1","B","III","01","a",1),
 (329,"1BIII 01b","IMPRESE COLLEGATE","1","B","III","01","b",1),
 (330,"1BIII 01c","ALTRE IMPRESE","1","B","III","01","c",1),
 (331,"1BIII 02","CREDITI","1","B","III","02","",0),
 (332,"1BIII 02a","CREDITI VERSO IMPRESE CONTROLLATE","1","B","III","02","a",1),
 (333,"1BIII 02b","CREDITI VERSO IMPRESE COLLEGATE","1","B","III","02","b",1),
 (334,"1BIII 02c","CREDITI VERSO IMPRESE CONTROLLANTI","1","B","III","02","c",1),
 (335,"1BIII 02d","CREDITI VERSO ALTRI","1","B","III","02","d",1),
 (336,"1BIII 03","ALTRI TITOLI","1","B","III","03","",1),
 (337,"1BIII 04","AZIONI PROPRIE","1","B","III","04","",1),
 (338,"1C","ATTIVO CIRCOLANTE","1","C","","","",0),
 (339,"1CI","RIMANENZE","1","C","I","","",0),
 (340,"1CI   01","MATERIE PRIME, SUSSIDIARIE E DI CONSUMO","1","C","I","01","",1),
 (341,"1CI   02","PRODOTTI IN CORSO DI LAVORAZIONE E SEMILAVORATI","1","C","I","02","",1),
 (342,"1CI   03","LAVORI IN CORSO SU ORDINAZIONE","1","C","I","03","",1),
 (343,"1CI   04","PRODOTTI FINITI E MERCI","1","C","I","04","",1),
 (344,"1CI   05","ACCONTI","1","C","I","05","",1),
 (345,"1CII","CREDITI","1","C","II","","",0),
 (346,"1CII  01","CREDITI VERSO CLIENTI","1","C","II","01","",1),
 (347,"1CII  02","CREDITI VERSO IMPRESE CONTROLLATE","1","C","II","02","",1),
 (348,"1CII  03","CREDITI VERSO IMPRESE COLLEGATE","1","C","II","03","",1),
 (349,"1CII  04","CREDITI VERSO CONTROLLANTI","1","C","II","04","",1),
 (350,"1CII  05","CREDITI VERSO ALTRI","1","C","II","05","",1),
 (351,"1CIII","ATTIVITA' FINANZIARIE NON IMMOBILIZZAZIONI","1","C","III","","",0),
 (352,"1CIII 01","PARTECIPAZIONI IN IMPRESE CONTROLLATE","1","C","III","01","",1),
 (353,"1CIII 02","PARTECIPAZIONI IN IMPRESE COLLEGATE","1","C","III","02","",1),
 (354,"1CIII 03","ALTRE PARTECIPAZIONI","1","C","III","03","",1),
 (355,"1CIII 04","AZIONI PROPRIE","1","C","III","04","",1),
 (356,"1CIII 05","ALTRI TITOLI","1","C","III","05","",1),
 (357,"1CIV","DISPONIBILITA' LIQUIDE","1","C","IV","","",0),
 (359,"1CIV  01","DEPOSITI BANCARI E POSTALI","1","C","IV","01","",1),
 (360,"1CIV  02","ASSEGNI","1","C","IV","02","",1),
 (361,"1CIV  03","DENARO E VALORI IN CASSA","1","C","IV","03","",1),
 (362,"1D","RATEI E RISCONTI","1","D","","","",0),
 (363,"1D    01","DISAGGIO SUI PRESTITI","1","D","","01","",1),
 (364,"1D    02","ALTRI","1","D","","02","",1),
 (365,"2","PASSIVO","2","","","","",0),
 (366,"2A","PATRIMONIO NETTO","2","A","","","",0),
 (367,"2AI","CAPITALE","2","A","I","","",1),
 (368,"2AII","RISERVA DA SOVRAPREZZO AZIONI","2","A","II","","",1),
 (369,"2AIII","RISERVE DI RIVALUTAZIONE","2","A","III","","",1),
 (370,"2AIV","RISERVA LEGALE","2","A","IV","","",1),
 (371,"2AV","RISERVA PER AZIONI PROPRIE IN PORTAFOGLIO","2","A","V","","",1),
 (372,"2AVI","RISERVE STATUTARIE","2","A","VI","","",1),
 (373,"2AVII","ALTRE RISERVE","2","A","VII","","",0),
 (374,"2AVII 01","RISERVA STRAORDINARIA","2","A","VII","01","",1),
 (375,"2AVII 02","RISERVA STRAORDINARIA DA FUSIONE","2","A","VII","02","",1),
 (376,"2AVII 03","VERSAMENTO SOCI IN CONTO CAPITALE","2","A","VII","03","",1),
 (377,"2AVIII","UTILI (PERDITE) PORTATI A NUOVO","2","A","VIII","","",1),
 (378,"2B","FONDI PER RISCHI E ONERI","2","B","","","",0),
 (379,"2B    01","F. TRATTAMENTI DI QUIESCENZA E OBBLIGHI SIMILI","2","B","","01","",1),
 (380,"2B    02","FONDO IMPOSTE E TASSE","2","B","","02","",1),
 (381,"2B    03","ALTRI FONDI","2","B","","03","",1),
 (382,"2C","TRATTAMENTO DI FINE RAPPORTO DI LAVORO SUBORDINATO","2","C","","","",1),
 (383,"2D","DEBITI","2","D","","","",0),
 (384,"2D    01","OBBLIGAZIONI","2","D","","01","",1),
 (385,"2D    02","OBBLIGAZIONI CONVERTIBILI","2","D","","02","",1),
 (386,"2D    03","DEBITI VERSO BANCHE","2","D","","03","",1),
 (387,"2D    04","DEBITI VERSO ALTRI FINANZIATORI","2","D","","04","",1),
 (388,"2D    05","ACCONTI","2","D","","05","",1),
 (389,"2D    06","DEBITI VERSO FORNITORI","2","D","","06","",1),
 (390,"2D    07","DEBITI RAPPRESENTATI DA TITOLI DI CREDITO","2","D","","07","",1),
 (391,"2D    08","DEBITI VERSO IMPRESE CONTROLLATE","2","D","","08","",1),
 (392,"2D    09","DEBITI VERSO IMPRESE COLLEGATE","2","D","","09","",1),
 (393,"2D    10","DEBITI VERSO CONTROLLANTI","2","D","","10","",1),
 (394,"2D    11","DEBITI TRIBUTARI","2","D","","11","",1),
 (395,"2D    12","DEBITI VERSO ISTITUTI DI PREVIDENZA E SICUREZZA SOCIALE","2","D","","12","",1),
 (396,"2D    13","ALTRI DEBITI","2","D","","13","",1),
 (397,"2E","RATEI E RISCONTI","2","E","","","",0),
 (398,"2E    01","AGGIO SUI PRESTITI","2","E","","01","",1),
 (399,"2E    02","ALTRI","2","E","","02","",1),
 (400,"3","CONTI D'ORDINE","3","","","","",0),
 (401,"3 I","CONTI D'ORDINE ATTIVO","3","","I","","",1),
 (402,"3 II","CONTI D'ORDINE PASSIVO","3","","II","","",1),
 (403,"4","CONTO ECONOMICO","4","","","","",0),
 (404,"4A","VALORE DELLA PRODUZIONE","4","A","","","",0),
 (405,"4A    01","RICAVI DELLE VENDITE E DELLE PRESTAZIONI","4","A","","01","",1),
 (406,"4A    02","VARIAZIONE DELLE RIMANENZE","4","A","","02","",1),
 (407,"4A    03","VARIAZIONE DEI LAVORI IN CORSO SU ORDINAZIONE","4","A","","03","",1),
 (408,"4A    04","INCREMENTI DI IMMOBILIZZAZIONI PER LAVORI INTERNI","4","A","","04","",1),
 (409,"4A    05","ALTRI RICAVI E PROVENTI","4","A","","05","",1),
 (410,"4B","COSTI DELLA PRODUZIONE","4","B","","","",0),
 (411,"4B    06","COSTI DELLA PROD. PER MATERIE I, SUSSID., DI CONSUMO E MERCI","4","B","","06","",1),
 (412,"4B    07","COSTI DELLA PRODUZIONE PER SERVIZI","4","B","","07","",1),
 (413,"4B    08","COSTI DELLA PRODUZIONE PER GODIMENTO DI BENI DI TERZI","4","B","","08","",1),
 (414,"4B    09","COSTI DELLA PRODUZIONE PER IL PERSONALE","4","B","","09","",0),
 (415,"4B    09a","SALARI E STIPENDI","4","B","","09","a",1),
 (416,"4B    09b","ONERI SOCIALI","4","B","","09","b",1),
 (417,"4B    09c","TRATTAMENTO DI FINE RAPPORTO","4","B","","09","c",1),
 (418,"4B    09d","TRATTAMENTO DI QUIESCENZA E SIMILI","4","B","","09","d",1),
 (419,"4B    09e","ALTRI COSTI","4","B","","09","e",1),
 (420,"4B    10","AMMORTAMENTI E SVALUTAZIONI","4","B","","10","",0),
 (421,"4B    10a","AMMORTAMENTO DELLE IMMOBILIZZAZIONI IMMATERIALI","4","B","","10","a",1),
 (422,"4B    10b","AMMORTAMENTO DELLE IMMOBILIZZAZIONI MATERIALI","4","B","","10","b",1),
 (423,"4B    10c","ALTRE SVALUTAZIONI DELLE IMMOBILIZZAZIONI","4","B","","10","c",1),
 (424,"4B    10d","SVAL. DEI CREDITI DELL'ATTIVO CIRCOLANTE E DISPONIB. LIQUIDE","4","B","","10","d",1),
 (425,"4B    11","VARIAZIONE DELLE RIMANENZE","4","B","","11","",1),
 (426,"4B    12","ACCANTONAMENTI PER RISCHI","4","B","","12","",1),
 (427,"4B    13","ALTRI ACCANTONAMENTI","4","B","","13","",1),
 (428,"4B    14","ONERI DIVERSI DI GESTIONE","4","B","","14","",1),
 (429,"4C","PROVENTI E ONERI FINANZIARI","4","C","","","",0),
 (430,"4C    15","PROVENTI DA PARTECIPAZIONI IN IMPRESE","4","C","","15","",0),
 (431,"4C    15a","PROV. DA PARTECIPAZIONI IN IMPRESE CONTROLLATE","4","C","","15","a",1),
 (432,"4C    15b","PROV. DA PARTECIPAZIONI IN IMPRESE COLLEGATE","4","C","","15","b",1),
 (433,"4C    16","ALTRI PROVENTI FINANZIARI","4","C","","16","",0),
 (434,"4C    16a","ALTRI PROVENTI FIN. DA CREDITI ISCRITTI NELLE IMMOBILIZ.","4","C","","16","a",1),
 (435,"4C    16b","DA TITOLI ISCRITTI NELLE IMM. CHE NON COST. PARTECIPAZIONI","4","C","","16","b",1),
 (436,"4C    16c","DA TITOLI ISCRITTI NELL'ATTIVO CIRCOL. CHE NON COST. PARTEC.","4","C","","16","c",1),
 (437,"4C    16d","PROVENTI DIVERSI DAI PRECEDENTI","4","C","","16","d",1),
 (438,"4C    17","INTERESSI E ALTRI ONERI FINANZIARI","4","C","","17","",0),
 (439,"4C    17a","INT. E ALTRI ONERI FINAN. DA IMPRESE CONTROLLATE","4","C","","17","a",1),
 (440,"4C    17b","INT. E ALTRI ONERI FIN. DA IMPRESE CONTROLLANTI","4","C","","17","b",1),
 (441,"4C    17c","INT. E ALTRI ONERI FIN. DA IMPRESE COLLEGATE","4","C","","17","c",1),
 (442,"4C    17d","INT. E ALTRI ONERI FIN. DA ALTRE IMPRESE","4","C","","17","d",1),
 (443,"4D","RETTIFICHE DI VALORE DI ATTIVITA' FINANZIARIE","4","D","","","",0),
 (444,"4D    18","RIVALUTAZIONI","4","D","","18","",0),
 (445,"4D    18a","RIVALUTAZIONI DI PARTECIPAZIONI","4","D","","18","a",1),
 (446,"4D    18b","RIVALUT. DI IMMOBILIZ. FINANZ. CHE NON COST. PARTECIPAZIONI","4","D","","18","b",1),
 (447,"4D    18c","RIV. DI TIT. ISCRITTI NELL'ATTIVO CIRC. CHE NON COST. PART.","4","D","","18","c",1),
 (448,"4D    19","SVALUTAZIONI","4","D","","19","",0),
 (449,"4D    19a","SVAL. DI PARTECIPAZIONI","4","D","","19","a",1),
 (450,"4D    19b","SVAL. DI IMMOB. FIN. CHE NON COSTITUISCONO PARTECIPAZIONI","4","D","","19","b",1),
 (451,"4D    19c","SVAL. DI TIT. ISCRITTI ALL'ATTIVO CIRC. CHE NON COST. PART.","4","D","","19","c",1),
 (452,"4E","PROVENTI E ONERI STRAORDINARI","4","E","","","",0),
 (453,"4E    20","PROVENTI","4","E","","20","",1),
 (454,"4E    21","ONERI","4","E","","21","",1),
 (455,"4E    22","IMPOSTE SUL REDDITO DELL'ESERCIZIO","4","E","","22","",1),
 (456,"4E    24","RETTIF. DI VAL. OPERATE ESCLUSIV. IN APPLIC. DI NORME TRIB.","4","E","","24","",1),
 (457,"4E    25","ACCANT. OPERATI ESCLUSIV. IN APPLIC. DI NORME TRIBUTARIE","4","E","","25","",1)
                """)
        
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.2.10':
                
                #cambio tipo riga righe contabili da "I" a "O" ed adeguo il tot.riga iva escludendo 
                #l'imponibile per le righe iva degli omaggi
                #che nella contabilizzazione dal magazzino venivano contrassegnate con
                #note = "OMAGGI"
                db.Execute("""
UPDATE contab_b
SET tipriga="O", importo=imposta+indeduc
WHERE tipriga="I" AND note="OMAGGI"
                """)
        
            if oldver<'1.2.56' and ok:
                for tabkey, envkey, val in (('optlnkcrdpdc', 'OPTLNKCRDPDC', 1),
                                            ('optlnkgrdpdc', 'OPTLNKGRDPDC', 0),
                                            ('optlnkcrdcli', 'OPTLNKCRDCLI', 1),
                                            ('optlnkgrdcli', 'OPTLNKGRDCLI', 1),
                                            ('optlnkcrdfor', 'OPTLNKCRDFOR', 1),
                                            ('optlnkgrdfor', 'OPTLNKGRDFOR', 1),):
                    db.Execute("""
                    INSERT INTO %s (chiave, flag) VALUES (%%s,%%s)""" % bt.TABNAME_CFGSETUP,
                                                                       (tabkey, val,))
                    setattr(bt, envkey, val)
            
                #inserisco opzione notifiche in setup azienda, per default=0
                for tabkey, envkey, val in (('optnotifiche', 'OPTNOTIFICHE', 0),):
                    db.Execute("""
                    INSERT INTO %s (chiave, flag) VALUES (%%s,%%s)""" % bt.TABNAME_CFGSETUP,
                                                                       (tabkey, val,))
                    setattr(bt, envkey, val)
                
                db.Execute("""
                UPDATE %s SET lendescriz=60
                """ % bt.TABNAME_CFGMAGMOV)
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.2.58' and ok:
                #creo tab.stati su db x4
                if not db.Retrieve("""DESCRIBE x4.stati""") and db.dbError.code == 1146:
                    db.Execute("""
CREATE TABLE IF NOT EXISTS `x4`.`stati` (
  `id`             INT(6)      NOT NULL AUTO_INCREMENT COMMENT 'ID',
  `codice`         CHAR(10)    DEFAULT NULL COMMENT 'Codice/Sigla Stato',
  `vatprefix`      CHAR(10)    DEFAULT NULL COMMENT 'Prefisso partite iva',
  `descriz`        VARCHAR(60) DEFAULT NULL COMMENT 'Denominazione Stato',
  `desceng`        VARCHAR(60) DEFAULT NULL COMMENT 'Denominazione Stato in lingua inglese',
  `is_cee`         TINYINT(1)  DEFAULT NULL COMMENT 'Flag Stato CEE',
  `is_blacklisted` TINYINT(1)  DEFAULT NULL COMMENT 'Flag Blacklist acquisti/vendite',
  `codunico`       CHAR(3)     DEFAULT NULL COMMENT 'Codice Unico',
  PRIMARY KEY  (`id`),
  UNIQUE KEY `index1` (`codice`),
  UNIQUE KEY `index2` (`descriz`)
) ENGINE=MyISAM AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='Stati'""")
        
                    db.Execute("""
INSERT INTO `x4`.`stati`  
    (`id`,`codice`,`vatprefix`,`descriz`,`desceng`,`is_cee`,`is_blacklisted`) 
VALUES 
    (  1, "AT", "AT", "AUSTRIA",         "AUSTRIA",        1, 0),
    (  2, "BE", "BE", "BELGIO",          "BELGIUM",        1, 0),
    (  3, "BG", "BG", "BULGARIA",        "BULGARIA",       1, 0),
    (  4, "CY", "CY", "CIPRO",           "CYPRUS",         1, 0),
    (  5, "DK", "DK", "DANIMARCA",       "DENMARK",        1, 0),
    (  6, "EE", "EE", "ESTONIA",         "ESTONIA",        1, 0),
    (  7, "FI", "FI", "FINLANDIA",       "FINLAND",        1, 0),
    (  8, "FR", "FR", "FRANCIA",         "FRANCE",         1, 0),
    (  9, "DE", "DE", "GERMANIA",        "GERMANY",        1, 0),
    ( 10, "GB", "GB", "GRAN BRETAGNA",   "UNITED KINGDOM", 1, 0),
    ( 11, "EL", "EL", "GRECIA",          "GREECE",         1, 0),
    ( 12, "IE", "IE", "IRLANDA",         "IRELAND",        1, 0),
    ( 13, "IT", "IT", "ITALIA",          "ITALY",          1, 0),
    ( 14, "LV", "LV", "LETTONIA",        "LATVIA",         1, 0),
    ( 15, "LT", "LT", "LITUANIA",        "LITHUANIA",      1, 0),
    ( 16, "LU", "LU", "LUSSEMBURGO",     "LUXEMBOURG",     1, 0),
    ( 17, "MT", "MT", "MALTA",           "MALTA",          1, 0),
    ( 18, "NL", "NL", "OLANDA",          "NETHERLANDS",    1, 0),
    ( 19, "PL", "PL", "POLONIA",         "POLAND",         1, 0),
    ( 20, "PT", "PT", "PORTOGALLO",      "PORTUGAL",       1, 0),
    ( 21, "CZ", "CZ", "REPUBBLICA CECA", "CZECH REPUBLIC", 1, 0),
    ( 22, "RO", "RO", "ROMANIA",         "ROMANIA",        1, 0),
    ( 23, "SK", "SK", "SLOVACCHIA",      "SLOVAKIA",       1, 0),
    ( 24, "SI", "SI", "SLOVENIA",        "SLOVENIA",       1, 0),
    ( 25, "ES", "ES", "SPAGNA",          "SPAIN",          1, 0),
    ( 26, "SE", "SE", "SVEZIA",          "SWEDEN",         1, 0),
    ( 27, "HU", "HU", "UNGHERIA",        "HUNGARY",        1, 0),
    ( 28, "SM", "SM", "SAN MARINO",      "SAN MARINO",     0, 1),
    ( 29, "MC", "FR", "MONACO",          "MONACO",         0, 1),
    ( 30, "CH", "CH", "SVIZZERA",        "SWISS",          0, 1),
    (999, "ZZ", "ZZ", "ZZ-INDEFINITO-",  "ZZ-UNDEFINED-",  0, 0)""")
                
                #adeguamento id_stato su clienti,fornitori in base a campo nazione
                mancanti = []
                for name in 'clienti fornit'.split():
                    
                    db.Execute("""
UPDATE %(name)s 
SET id_stato=(

    SELECT stato.id
      FROM x4.stati stato
     WHERE stato.codice=%(name)s.nazione OR stato.codice="IT" AND %(name)s.nazione=""
)
                    """ % locals())
                    
                    db.Retrieve("""
SELECT COUNT(*)
FROM %(name)s anag
LEFT JOIN x4.stati stato ON stato.id=anag.id_stato OR (anag.nazione="" AND stato.codice="IT")
WHERE anag.nazione<>"" AND anag.id_stato IS NULL""" % locals())
                    
                    if db.rs:
                        if db.rs[0][0]>0:
                            mancanti.append('%s (%d)' % (name, db.rs[0][0]))
                    
                    db.Execute("""
UPDATE %(name)s 
SET id_stato=999
WHERE id_stato IS NULL""" % locals())
                
                if mancanti:
                    msg =\
                    """Durante l\'adeguamento dello stato dei clienti/fornitori,\n"""\
                    """non è stato possibile riconoscere lo stato di alcune anagrafiche:\n\n"""
                    msg += ', '.join(mancanti)+'\n\n'
                    msg +=\
                    """Tali anagrafiche sono state impostate con stato INDEFINITO."""
                    aw.awu.MsgDialog(self, msg, style=wx.ICON_WARNING)
                
                #adeguamento nuovo campo 'modo' su tab.aliquote in base a perc.calcolo e descrizione
                db.Execute(r"""
UPDATE aliqiva 
SET modo=IF(perciva>0, "I",
         IF(descriz LIKE "%ES.%" OR descriz LIKE "%ESEN%", "E", 
         IF(descriz LIKE "%F.C%" OR descriz LIKE "%F%CAMP%", "F", "N")))""")
                msg =\
                """La tabella delle aliquote IVA contiene ora un nuovo campo,\n"""\
                """denominato 'modo', che indica se le cifre assogettate all'aliquota\n"""\
                """sono da considerarsi imponibili iva, non imponibili, esenti o fuori\n"""\
                """campo di applicazione.\n"""\
                """Tale informazione è stata inizializzata in questa fase di adeguamento\n"""\
                """delle strutture dati, ma si consiglia di verificare, per ogni aliquota\n"""\
                """presente, la correttezza del menzionato 'modo'."""  
                aw.awu.MsgDialog(self, msg, style=wx.ICON_INFORMATION)
        
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.2.62' and ok:
                tpd = adb.DbTable(bt.TABNAME_CFGMAGDOC, 'tipdoc')
                tpd.Retrieve('tipdoc.colcg="X" AND tipdoc.id_caucg IS NOT NULL')
                if not tpd.IsEmpty():
                    tpds = ','.join(map(str, [tpd.id_caucg for tpd in tpd]))
                    rw = adb.DbTable(bt.TABNAME_CONTAB_B, 'body', fields='id,id_reg,id_pdccp')
                    rw.AddJoin(bt.TABNAME_CONTAB_H, 'reg')
                    rw.AddFilter('reg.id_caus IN (%s)' % tpds)
                    rw.AddFilter('YEAR(reg.datreg)=2010')
                    rw.AddFilter('body.numriga=1 AND body.id_pdccp IS NULL')
                    rw.Retrieve()
                    rr = adb.DbTable(bt.TABNAME_CONTAB_B, 'body')
                    rr.AddJoin(bt.TABNAME_CONTAB_H, 'reg')
                    rr.AddOrder('body.numriga')
                    rr.AddFilter('body.numriga>=3')
                    for r in rw:
                        rr.Retrieve('body.id_reg=%s', r.id_reg)
                        r.id_pdccp = rr.id_pdcpa
                    rw.Save()
        
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.2.66' and ok:
                
                #adeguamento struttura tabella progressivi prodotti per inserimento valore di default 
                DQ = Env.Azienda.BaseTab.MAGQTA_DECIMALS
                DI = Env.Azienda.BaseTab.VALINT_DECIMALS
                db.Execute(r"""
  ALTER TABLE `prodpro` 
MODIFY COLUMN `ini`    DECIMAL(10,%(DQ)s) DEFAULT 0,
MODIFY COLUMN `car`    DECIMAL(10,%(DQ)s) DEFAULT 0,
MODIFY COLUMN `sca`    DECIMAL(10,%(DQ)s) DEFAULT 0,
MODIFY COLUMN `iniv`   DECIMAL(14,%(DI)s) DEFAULT 0,
MODIFY COLUMN `carv`   DECIMAL(14,%(DI)s) DEFAULT 0,
MODIFY COLUMN `scav`   DECIMAL(14,%(DI)s) DEFAULT 0,
MODIFY COLUMN `cvccar` DECIMAL(10,%(DQ)s) DEFAULT 0,
MODIFY COLUMN `cvcsca` DECIMAL(10,%(DQ)s) DEFAULT 0,
MODIFY COLUMN `cvfcar` DECIMAL(10,%(DQ)s) DEFAULT 0,
MODIFY COLUMN `cvfsca` DECIMAL(10,%(DQ)s) DEFAULT 0""" % locals())
        
        
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.2.82' and ok:
                
                #spostamento variabile di setup: il numero di listini prima era sul campo flag, ora sposto su importo 
                db.Execute(r"""
UPDATE `cfgsetup`
   SET importo=flag, flag=NULL
 WHERE chiave="magnumlis" """)
        
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.3.06' and ok:
                #adeguo il charset di ugni tabella in utf8
                err = None
                try:
                    db.Execute("ALTER DATABASE CHARACTER SET utf8")
                except Exception, e:
                    err = repr(e.args)
                if err:
                    aw.awu.MsgDialog(self, "Errore in conversione database:\n%s" % err)
                else:
                    wait = aw.awu.WaitDialog(self, "Adeguamento charset utf-8", "",
                                             maximum=len(bt.tabelle))
                    wx.BeginBusyCursor()
                    try:
                        for n, tabstru in enumerate(bt.tabelle):
                            tabname, tabdesc = tabstru[:2]
                            wait.SetMessage("Tabella: %s - %s" % (tabname, tabdesc))
                            try:
                                db.Execute("ALTER TABLE %s CONVERT TO CHARACTER SET utf8" % tabname)
                            except Exception, e:
                                err = repr(e.args)
                                break
                            wait.SetValue(n)
                    finally:
                        wx.EndBusyCursor()
                        wait.Destroy()
                    if err:
                        aw.awu.MsgDialog(self, "Errore in conversione tabella:\n%s" % err)
                if err:
                    ok = False
            
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.3.14' and ok:
                
                #imposto i massimali conosciuti per azienda/privato per gli anni 2010 e 2011
                for anno, maxazi, maxpri in ((2010, 25000, 25000),
                                             (2011,  3000,  3600),):
                    cmd = """
                    INSERT INTO cfgprogr (codice,       keydiff,   progrimp1,  progrimp2)
                                  VALUES ('spesometro', %(anno)s, %(maxazi)s, %(maxpri)s)""" % locals()
                    db.Execute(cmd)
                
                #adeguo il nuovo flag azienda/privato su tabelle clienti e fornitori
                err = None
                try:
                    for tab_name in 'clienti fornit'.split():
                        db.Execute('UPDATE %(tab_name)s SET aziper=IF((piva IS NULL OR LENGTH(piva)=0) AND LENGTH(codfisc)=16,"P","A")' % locals())
                except Exception, e:
                    err = repr(e.args)
                if err:
                    aw.awu.MsgDialog(self, "Errore in adeguamento tabella %(tab_name)s:\n%(err)s" % locals())
                    ok = False
                
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.3.28' and ok:
                
                try:
                    for key in 'magnumric magnumsco'.split():
                        db.Execute('INSERT INTO cfgsetup (chiave, importo) VALUES ("%(key)s", 3)' % locals())
                except Exception, e:
                    pass
        
            # -------------------------------------------------------------------------------------
            
            if oldver<'1.4.12' and ok:
                
                #adeguamento struttura tabella stati per aggiunta codice stato 
                #nella codifica del modello unico di dichiarazione dei redditi
                if db.Execute(r"""ALTER TABLE `x4`.`stati` 
                                    ADD COLUMN `codunico` CHAR(3) AFTER `is_blacklisted`"""):
                    for stato_desc, cod_unico in \
                        (("AUSTRIA",         "008"),
                         ("BELGIO",          "009"),
                         ("BULGARIA",        "012"),
                         ("CIPRO",           "101"),
                         ("DANIMARCA",       "021"),
                         ("ESTONIA",         "257"),
                         ("FINLANDIA",       "028"),
                         ("FRANCIA",         "029"),
                         ("GERMANIA",        "094"),
                         ("GRAN BRETAGNA",   "031"),
                         ("GRECIA",          "032"),
                         ("IRLANDA",         "040"),
                         ("LETTONIA",        "258"),
                         ("LITUANIA",        "259"),
                         ("LUSSEMBURGO",     "092"),
                         ("MALTA",           "105"),
                         ("OLANDA",          "050"),
                         ("POLONIA",         "054"),
                         ("PORTOGALLO",      "055"),
                         ("REPUBBLICA CECA", "275"),
                         ("ROMANIA",         "061"),
                         ("SLOVACCHIA",      "276"),
                         ("SLOVENIA",        "260"),
                         ("SPAGNA",          "067"),
                         ("SVEZIA",          "068"),
                         ("UNGHERIA",        "077"),
                         ("SAN MARINO",      "037"),
                         ("MONACO",          "091"),
                         ("SVIZZERA",        "071"),):
                        db.Execute(r"""UPDATE `x4`.`stati` 
                        SET codunico=%s WHERE descriz=%s""", (cod_unico, stato_desc))
        
            if oldver<'1.4.43' and ok:
                
                #adeguamento struttura tabella stati per aggiunta codice stato 
                #nella codifica del modello unico di dichiarazione dei redditi
                db.Execute(r"""ALTER TABLE `x4`.`cfgmail` 
                                    ADD COLUMN `authtls` TINYINT(1) AFTER `authpswd`""")
        
#            if oldver<'1.4.52' and ok:
            if ok:
                
                #crea vista per analisi utile, ricarica e marginalità su vendite
                db.Execute(r"""
CREATE VIEW stat_reddvend AS
SELECT  tpd.codice 'causale_cod',
        tpd.descriz 'causale',
        doc.numdoc 'doc_numero',
        doc.datdoc 'doc_data',
        pdc.codice 'cliente_cod',
        pdc.descriz 'cliente',
        doc.totimponib*IF(tpd.clasdoc="vencli",1,-1) 'ricavo',
        SUM(mov.costot)*IF(tpd.clasdoc="vencli",1,-1) 'costo',
        (doc.totimponib-IF(SUM(mov.costot) IS NULL, 0, SUM(mov.costot)))*IF(tpd.clasdoc="vencli",1,-1) 'utile',
        IF(SUM(mov.costot) IS NULL, 100, 100*(doc.totimponib-SUM(mov.costot))/SUM(mov.costot))*IF(tpd.clasdoc="vencli",1,-1) 'ricarica',
        IF(SUM(mov.costot) IS NULL, 100, 100*(doc.totimponib-SUM(mov.costot))/doc.totimponib)*IF(tpd.clasdoc="vencli",1,-1) 'margine',
        YEAR(doc.datdoc) 'anno',
        MONTH(doc.datdoc) 'mese',
        tpd.id 'causale_id',
        doc.id 'doc_id',
        pdc.id 'cliente_id'
FROM movmag_h doc
JOIN cfgmagdoc tpd ON tpd.id=doc.id_tipdoc
JOIN movmag_b mov ON mov.id_doc=doc.id
JOIN pdc ON pdc.id=doc.id_pdc
WHERE tpd.clasdoc IN ("vencli", "rescli") AND (doc.f_ann IS NULL OR doc.f_ann<>1)
GROUP BY doc.id""")
        if ok:
            self.PerformExternalAdaptations()
        
        if ok:
            WriteCurrentVersion()
        else:
            aw.awu.MsgDialog(self, repr(db.dbError.description),
                             "Adattamento tabelle")
        
        return ok
    
    def PerformExternalAdaptations(self):
        pass


# ------------------------------------------------------------------------------


class TablesGrid(dbglib.DbGrid):
    """
    Griglia tabelle di cui adeguare la struttura
    """
    def __init__(self, parent, tabdict):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable registro iva (derivati da contab.dbtables.RegIva)
        """
        
        self.rstab = [(key,) for key in tabdict]
        
        size = parent.GetClientSizeTuple()
        
        cn = lambda db, col: db._GetFieldIndex(col, inline=True)
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            ( 90, (0, "Tabella", _STR, True )),\
            )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData( self.rstab, colmap, canedit, canins,\
                      links, afteredit)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(0)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class DiffsGrid(dbglib.DbGrid):
    """
    Griglia differenze di struttura sulla tabella
    """
    def __init__(self, parent):
        """
        Parametri:
        parent griglia  (wx.Panel)
        dbtable registro iva (derivati da contab.dbtables.RegIva)
        """
        
        size = parent.GetClientSizeTuple()
        
        _NUM = gl.GRID_VALUE_NUMBER
        _STR = gl.GRID_VALUE_STRING
        _DAT = gl.GRID_VALUE_DATETIME
        
        cols = (\
            (100, (0, "Colonna",    _STR, True )),\
            (360, (1, "Differenze", _STR, True )),\
            )
        
        colmap  = [c[1] for c in cols]
        colsize = [c[0] for c in cols]
        canedit = False
        canins = False
        
        dbglib.DbGrid.__init__(self, parent, -1, size=size, style=0)
        
        links = None
        
        afteredit = None
        self.SetData( (), colmap, canedit, canins, links, afteredit)
        
        map(lambda c:\
            self.SetColumnDefaultSize(c[0], c[1]), enumerate(colsize))
        
        self.SetFitColumn(1)
        self.AutoSizeColumns()
        sz = wx.FlexGridSizer(1,0,0,0)
        sz.AddGrowableCol( 0 )
        sz.AddGrowableRow( 0 )
        sz.Add(self, 0, wx.GROW|wx.ALL, 0)
        parent.SetSizer(sz)
        sz.SetSizeHints(parent)


# ------------------------------------------------------------------------------


class WarningDialog(aw.Dialog):
    
    def __init__(self, parent):
        aw.Dialog.__init__(self, parent, -1, 'Warning Adeguamento Database')
        p = aw.Panel(self)
        wdr.WarningFunc(p)
        self.AddSizedPanel(p)
        self.Bind(wx.EVT_CHECKBOX, self.OnCheck)
        self.Bind(wx.EVT_BUTTON, self.OnStart)
    
    def OnCheck(self, event):
        def cn(x):
            return self.FindWindowByName(x)
        e = True
        for name in 'check1 check2'.split():
            e = e and cn(name).IsChecked()
        cn('butstart').Enable(e)
        event.Skip()
    
    def OnStart(self, event):
        self.EndModal(wx.ID_OK)


# ------------------------------------------------------------------------------


class AdeguaPanel(aw.Panel):
    """
    Adeguamento strutture tabelle
    """
    
    def __init__(self, *args, **kwargs):
        
        aw.Panel.__init__(self, *args, **kwargs)
        wdr.DiffDetailsFunc(self)
        ci = lambda x: self.FindWindowById(x)
        ci(wdr.ID_VERSION).SetLabel(Env.__version__)
        
        self.Bind(wx.EVT_BUTTON, self.OnAdegua, ci(wdr.ID_ADEGUA))
        
        self.adeg = {}
    
    def SetAdeg(self, adeg):
        
        self.adeg = adeg
        
        ci = lambda x: self.FindWindowById(x)
        self.gritab = TablesGrid(ci(wdr.ID_PGTAB), self.adeg)
        self.gridif = DiffsGrid(ci(wdr.ID_PGDIF))
        
        self.gritab.Bind(gl.EVT_GRID_CMD_SELECT_CELL, self.OnTabSelected)
        self.UpdateDiffs(0)
    
    def OnTabSelected(self, event):
        self.UpdateDiffs(event.GetRow())
        event.Skip()
    
    def UpdateDiffs(self, row):
        tab = self.gritab.rstab[row][0]
        dif = self.adeg[tab]
        rsdif = []
        for d in dif:
            field = d[0]
            if   d[1] == ADEG_MISSINGTABLE:
                diff = "Tabella mancante, verrà creata"
            elif d[1] == ADEG_MISSINGFIELD:
                diff = "Colonna non presente, verrà aggiunta"
            elif d[1] == ADEG_WRONGTYPE:
                diff = "Tipologia di colonna diversa dal previsto"
            elif d[1] == ADEG_WRONGLENGHT:
                diff = "Lunghezza della colonna insufficiente"
            elif d[1] == ADEG_WRONGDECIMALS:
                diff = "Numero di decimali insufficiente"
            elif d[1] == ADEG_INDEX:
                diff = "Indice mancante"
            elif d[1] == ADEG_REINDEX:
                diff = "Indice incongruente"
            rsdif.append((field, diff))
        self.gridif.ChangeData(rsdif)
    
    def OnAdegua(self, event):
        dlg = WarningDialog(self)
        do = (dlg.ShowModal() == wx.ID_OK)
        dlg.Destroy()
        if do:
            self.Adegua()
        event.Skip()
    
    def Adegua(self):
        
        db = adb.db.__database__
        wait = aw.awu.WaitDialog(self, maximum=len(self.adeg))
        errors = False
        
        bt = Env.Azienda.BaseTab
        
        for n, tab in enumerate(self.adeg):
            
            wait.SetMessage("E' in corso l'adeguamento della struttura di: %s"\
                            % tab)
            
            t = aw.awu.ListSearch(bt.tabelle, lambda x: x[0] == tab)
            stru = bt.tabelle[t][bt.TABSETUP_TABLESTRUCTURE]
            indx = bt.tabelle[t][bt.TABSETUP_TABLEINDEXES]
            
            create = False
            if self.adeg[tab][0][1] == ADEG_MISSINGTABLE:
                cmd = "CREATE TABLE %s (" % tab
                diffs = [(c[bt.TABSETUP_COLUMNNAME], ADEG_MISSINGFIELD)
                         for c in stru]
                create = True
            else:
                cmd = "ALTER TABLE %s " % tab
                diffs = [(x[1], x) for x in self.adeg[tab] if x[1] < ADEG_INDEX]
                diffs.sort()
                diffs = [x[1] for x in diffs]
            
            diffs += [x for x in self.adeg[tab] if x[1] >= ADEG_INDEX]
            
            #diffs = lista differenze:
            #0 = nome colonna
            #1 = tipo differenza, ADEG_*
            #2 = (eventuale) numero indice da (ri)creare
            
            #creazione/adeguamento struttura campi
            for d in diffs:
                
                field = d[0]
                diff = d[1]
                
                if field == '-' or diff >= ADEG_INDEX:
                    continue
                
                if not create:
                    if diff == ADEG_MISSINGFIELD:
                        cmd += "ADD COLUMN "
                    else:
                        cmd += "MODIFY COLUMN "
                    
                c = aw.awu.ListSearch(stru, lambda c: c[0] == field)
                col = stru[c]
                fname, ftype, flen, fdec, fadd, fdes =\
                     (col[bt.TABSETUP_COLUMNNAME],
                      col[bt.TABSETUP_COLUMNTYPE],
                      col[bt.TABSETUP_COLUMNLENGTH],
                      col[bt.TABSETUP_COLUMNDECIMALS],
                      col[bt.TABSETUP_COLUMNATTRIBUTES],
                      col[bt.TABSETUP_COLUMNDESCRIPTION])
                
                cmd += "%s %s" % (fname, ftype)
                
                if flen:
                    cmd += "(%d" % (flen + (fdec or 0))
                    if fdec:
                        cmd += ",%d" % fdec
                    cmd += ")"
                if fadd:
                    cmd += " %s" % fadd
                if fdes:
                    fdes = fdes.replace("'", "\\'")
                    fdes = fdes.replace("%", "perc.")
                    cmd += " COMMENT '%s'" % fdes
                cmd += ", "
            
            #creazione primary key
            if create:
                cmd += "PRIMARY KEY (%s), " % stru[0][bt.TABSETUP_COLUMNNAME]
            
            #creazione/adeguamento indici
            for d in diffs:
                if d[1] >= ADEG_INDEX:
                    i = d[2]
                    #cancellazione indice se incongruente
                    if d[1] == ADEG_REINDEX:
                        cmd += "DROP INDEX index%d, " % i
                    indtype, indexpr = indx[i]
                    #creazione nuovo indice
                    if not create:
                        cmd += "ADD "
                    if "UNIQUE" in indtype:
                        cmd += "UNIQUE "
                    else:
                        cmd += "INDEX "
                    cmd += "index%d (%s), " % (i, indexpr)
            
            cmd = cmd[:-2]
            if create:
                cmd += ") ENGINE = MYISAM"
            
            if not db.Execute(cmd):
                wait.Destroy()
                if create:
                    action = "la creazione"
                else:
                    action = "l'adeguamento di struttura"
                aw.awu.MsgDialog(self, 
                                 """Si è verificato un problema durante """
                                 """%s della tabella %s:\n%s"""\
                                 % (action, tab, db.dbError.description))
                #self.GetParent().EndModal(2)
                errors = True
            
            wait.SetValue(n)
            
        wait.Destroy()
        
        if errors:
            aw.awu.MsgDialog(self,\
                             """Si sono verificati problemi nel processo di """
                             """adeguamento strutture, impossibile proseguire.""",\
                             style=wx.ICON_ERROR)
            self.GetParent().EndModal(2)
        else:
            aw.awu.MsgDialog(self,\
                             """Le tabelle sono state adeguate con successo """
                             """alla corrente versione %s""" % Env.__version__,\
                             style=wx.ICON_INFORMATION)
            self.GetParent().EndModal(1)


# ------------------------------------------------------------------------------


def WriteCurrentVersion():
    keyver = wx.GetApp().keyver
    bt = Env.Azienda.BaseTab
    setup = adb.DbTable(bt.TABNAME_CFGSETUP, 'setup', writable='True')
    if setup.Retrieve("setup.chiave=%s", keyver):
        #scrittura versione head e mod
        if not setup.OneRow():
            setup.CreateNewRow()
            setup.chiave = keyver
        oldversion = setup.codice
        oldmodversion = setup.descriz
        setup.codice = Env.__version__
        setup.descriz = '%s %s' % (Env.__modversion__[:6], ver.MODVERSION_NAME)
        if setup.Save():
            if setup.Retrieve("setup.chiave=%s", "%s_old" % keyver):
                if not setup.OneRow():
                    setup.CreateNewRow()
                    setup.chiave = '%s_old' % keyver
                setup.codice = oldversion
                setup.descriz = oldmodversion
                setup.Save()
        #scrittura versione plugin installati
        for name in Env.plugins:
            p = Env.plugins[name]
            if hasattr(p, 'version'):
                key = "%s_plugin_version" % name
                if setup.Retrieve("setup.chiave=%s", key):
                    if not setup.OneRow():
                        setup.CreateNewRow()
                        setup.chiave = key
                    oldversion = setup.codice
                    setup.codice = p.version
                    setup.Save()


# ------------------------------------------------------------------------------


class AdeguaDialog(aw.Dialog):
    """
    Adeguamento strutture tabelle
    """
    def __init__(self, adeg, *args, **kwargs):
        kwargs['title'] = "Adeguamento tabelle"
        if not kwargs.has_key('style') and len(args) < 6:
            kwargs['style'] = wx.DEFAULT_DIALOG_STYLE
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = AdeguaPanel(self, -1)
        self.panel.SetAdeg(adeg)
        self.AddSizedPanel(self.panel)
        self.CenterOnScreen()


# ------------------------------------------------------------------------------


if __name__ == '__main__':
    
    class _testApp(wx.App):
        def OnInit(self):
            wx.InitAllImageHandlers()
            Env.Azienda.DB.testdb()
            db = adb.DB()
            out = db.Connect(host='marcel')
            if not out:
                print "Problema in connessione:\n%s"\
                      % repr(db.dbError.description)
            return out
    
    app = _testApp(True)
    app.MainLoop()
    Env.InitSettings()
    test = TabSetupDialog()
    test.ShowModal()
