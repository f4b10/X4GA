#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/multielement.py
# Author:       Marcello Montaldo <marcello.montaldo@gmail.com>
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

import getopt
import sys
from report.read import iReportDef
from report.element import *

from types import *

from reportlab.pdfgen import canvas
from reportlab import rl_config
from reportlab.lib.pagesizes import A4, landscape, portrait
from report.variables import *


_debug=0

class page_Format:
    """
    La classe, operando sulla definizione della struttura del Report (I{dizionario}), 
    provvede ad impostare i vari degli attributi che delineano il formato della pagina del report, 
    oltre ad altre caratteristiche di tipo generale.
    
    In particolarem gli attributi che descrivono il formato pagina sono i seguenti.
    
       - topMargin
       - bottomMargin
       - leftMargin
       - rightMargin
       - larghezza
       - altezza
       - orientamento
       - nomepdf
    @cvar topMargin: posizione margine superiore espresso in pixel
    @type topMargin: int
    @cvar bottomMargin: posizione margine inferiore espresso in pixel
    @type bottomMargin: int
    @cvar leftMargin: posizione margine sinistro espresso in pixel
    @type leftMargin: int
    @cvar rightMargin: posizione margine destro espresso in pixel
    @type rightMargin: int
    @cvar larghezza: dimensione orizzontale foglio espresso in pixel
    @type larghezza: int
    @cvar altezza: dimensione orizzontale foglio espresso in pixel
    @type altezza: int
    @cvar orientamento: orientamento del foglio
    @type orientamento: string
    @cvar nomepdf: Nome del file, in formato PDF, da generare
    @type nomepdf: string

    """
    topMargin=None
    bottomMargin=None
    leftMargin=None
    rightMargin=None
    larghezza=None
    altezza=None
    orientamento=None
    nomepdf=None

    def __init__(self, dDefinizione_report, pdfFileName):
        self.setup_Page(dDefinizione_report, pdfFileName)
        
    
    def setup_Page(self, d, pdfFileName):
        """
        Il metodo si fa carico di chiamare i vari metodi della classe che provvedono
        ad impostare gli attributi che descrivono il formato del foglio.
        @param d: Definizione Report. 
        @type d: dictionary
        """
        self.topMargin=self.set_topMargin(d)
        self.bottomMargin=self.set_bottomMargin(d)
        self.leftMargin=self.set_leftMargin(d)
        self.rightMargin=self.set_rightMargin(d)
        self.larghezza=self.set_larghezza(d)
        self.altezza=self.set_altezza(d)
        self.orientamento=self.set_orientation(d)
        if pdfFileName==None:
            self.nomepdf=self.set_pdfname(d)
        else:
            self.nomepdf=pdfFileName
    
    
    def set_topMargin(self, d):
        """
        Setta margine superiore pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: posizione margine superiore foglio espresso in pixel
        @rtype: int
        """
        if _debug==1:
            print "Margine superiore:",
            print d["topMargin"]
        return d["topMargin"]

    def set_bottomMargin(self, d):
        """
        Setta margine inferiore pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: posizione margine inferiore foglio espresso in pixel
        @rtype: int
        """
        if _debug==1:
            print "Margine inferiore:",
            print d["bottomMargin"]
        return d["bottomMargin"]

    def set_leftMargin(self, d):
        """
        Setta margine sinistro pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: posizione margine sinistro foglio espresso in pixel
        @rtype: int
        """
        if _debug==1:
            print "Margine sinistro:",
            print d["leftMargin"]
        return d["leftMargin"]

    def set_rightMargin(self, d):
        """
        Setta margine destro pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: posizione margine destro foglio espresso in pixel
        @rtype: int
        """
        if _debug==1:
            print "Margine destro:",
            print d["rightMargin"]
        return d["rightMargin"]
    
    def set_orientation(self, d):
        """
        Setta orientamento pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: orientamento pagina. Possibili valori attesi:
             - B{portrait}
             - B{landscape}
        @rtype: string
        """
        try:
            o = d["orientation"]
        except KeyError:
            o = 'Portrait'
        if _debug==1:
            print "Orientamento:",
            print o
        return o


    def set_larghezza(self, d):
        """
        Setta larghezza pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: larghezza foglio espresso in pixel
        @rtype: int
        """
        if _debug==1:
            print "Larghezza pagina:",
            d["pageWidth"]
        return d["pageWidth"]

    def set_altezza(self, d):
        """
        Setta altezza pagina in base al valore specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: altezza foglio espresso in pixel
        @rtype: int
        """
        if _debug==1:
            print "Altezza pagina:",
            d["pageHeight"]
        return d["pageHeight"]

    def set_pdfname(self, d):
        """
        Setta nome del file .PDF da generare, in base a quanto specificato nella definizione
        della struttura del record.
        @param d: Definizione Report. 
        @type d: dictionary
        @return: nome file .PDF da generare
        @rtype: string
        """
        if _debug==1:
            print "Nome file da generare:" + d["name"]+".pdf"
        return d["name"]+".pdf"


    def get_topMargin(self):
        """
        Restituisce la posizione del margine superiore
        @return: posizione del margine superiore
        @rtype: int
        """
        return self.topMargin

    def get_bottomMargin(self):
        """
        Restituisce la posizione del margine inferiore
        @return: posizione del margine inferiore
        @rtype: int
        """
        return self.bottomMargin

    def get_leftMargin(self):
        """
        Restituisce la posizione del margine sinistro
        @return: posizione del margine sinistro
        @rtype: int
        """
        return self.leftMargin

    def get_rightMargin(self):
        """
        Restituisce la posizione del margine destro
        @return: posizione del margine destro
        @rtype: int
        """
        return self.rightMargin
    
    def get_orientation(self):
        """
        Restituisce l'orientamento della pagina. Possibili valori attesi:
             - B{portrait}
             - B{landscape}
        @return: orientamento della pagina
        @rtype: string
        """
        return self.orientamento


    def get_larghezza(self):
        """
        Restituisce la larghezza del foglio espresso in pixel.
        @return: larghezza foglio
        @rtype: int
        """
        return self.larghezza

    def get_altezza(self):
        """
        Restituisce l'altezza del foglio espresso in pixel.
        @return: altezza foglio
        @rtype: int
        """
        return self.altezza

    def get_pdfname(self):
        """
        Restituisce il nome del file .PDF che deve essere generato
        @return: nome file .PDF
        @rtype: string
        """
        return self.nomepdf

    
    def get_larghezzaReale(self):
        """
        Restituisce la larghezza di stampa utile, ottenuta come:
            
        B{self.larghezza - self.leftMargin - self.rightMargin}
        
        @return: larghezza di stampa utile 
        @rtype: int
        """
        return self.larghezza - self.leftMargin -self.rightMargin
    
    def get_altezzaReale(self):
        """
        Restituisce la altezza di stampa utile, ottenuta come:
            
        B{self.altezza - self.topMargin - self.bottomMargin}
        
        @return: altezza di stampa utile 
        @rtype: int
        """
        return self.altezza - self.topMargin -self.bottomMargin






class queryString:
    '''
    La classe si fa carico di estrarre dalla definizione del report
    l'espressione del record set su cui lo stesso opera.
    @cvar queryExpression: Istruzione Sql utilizzata per reperire i dati 
    da considerare ai fini della produzione del report.
    @type queryExpression: String
    '''
    queryExpression=None

    def __init__(self, dDefinizione_report):
        self.queryExpression= dDefinizione_report["queryString"]["DATA"]
    

     
        
class group:
    """
    La classe si fa carico di acquisire la definizione dei raggruppamenti 
    presenti nel report.
    @cvar isStartNewColumn: non gestita
    @cvar isStartNewPage: indica se l'intestazione gruppo deve necessariamente comparire
                          a nuova pagina.
    @cvar isResetPageNumber: non gestita
    @cvar isReprintHeaderOnEachPage: indica sa l'intestazione deve essere ripetuta, valori possibili: true, false
                                    ad ogni interruzione di pagina
    @type isReprintHeaderOnEachPage: String
    @cvar minHeightToStartNewPage: non gestita
    @cvar groupExpression: espressione di rottura del gruppo
    @type groupExpression: String
    @cvar valoreAttuale: valore attuale dell'espressione di rottura
    @cvar valorePrecedente: valore precedente dell'espressione di rottura
    @cvar stampatoHeader: indica se l'intestazione del gruppo è già stata stampata
    @type stampatoHeader: bool
    
    
    """
    name=None
    isStartNewColumn=None    
    isStartNewPage=None
    isResetPageNumber=None
    isReprintHeaderOnEachPage=None
    minHeightToStartNewPage=None
    oGroupExpression=None
    #rottura=None
    oGroupHeader=None
    oGroupFooter=None
    valoreAttuale=None
    valorePrecedente=None
    stampatoHeader=None
    pageChanged=False
    
    def __init__(self, dDefinizione_report, oCanvas):
        self.valorePrecedente=None
        self.name=dDefinizione_report["name"]
        try:
            self.isStartNewColumn=dDefinizione_report["isStartNewColumn"]
        except:
            self.isStartNewColumn=False
            
        try:
            self.isStartNewPage=dDefinizione_report["isStartNewPage"]
        except:
            self.isStartNewPage=False
            
        try:
            self.isResetPageNumber=dDefinizione_report["isResetPageNumber"]
        except:
            self.isResetPageNumber=False
            
        try:
            self.isReprintHeaderOnEachPage=dDefinizione_report["isReprintHeaderOnEachPage"]
        except:
            self.isReprintHeaderOnEachPage=False
        try:
            self.minHeightToStartNewPage=dDefinizione_report["minHeightToStartNewPage"]
        except:
            self.minHeightToStartNewPage=0
            
        self.oGroupExpression=Expression(dDefinizione_report["groupExpression"]["DATA"].encode())
        self.oGroupHeader=groupHeader(dDefinizione_report, oCanvas, self.name)
        self.oGroupFooter=groupFooter(dDefinizione_report, oCanvas, self.name)
    
    def evaluate(self, oCanvas):
        """
        Valuta l'espressione di rottura del gruppo e in ogni caso provvede 
        ad assegnare il vecchio valore dell'espressione di rottura alla variabile
        B{self.valorePrecedente} ed il nuova valore appena valutato alla variabile
        B{self.valoreAttuale}
        @return: valore attuale dell'espressione di rottura del gruppo
        @rtype: dipende dalla espressione di rottura
        """
        self.valorePrecedente=self.valoreAttuale
        self.valoreAttuale=self.oGroupExpression.evaluate(oCanvas)
        return self.valoreAttuale
    
    def check_rottura(self, oCanvas):
        """
        Verifica se si è in presenza di rottura di gruppo (B{True}) o meno (B{False})
        @return: 
            - B{True} se rottura di gruppo
            - B{False} viceversa
        @rtype: bool
        """
        dbt = oCanvas.recordSource
        #if dbt.IsFlatView():
            #out = dbt.CheckNextSkipping()
        #else:
            #self.evaluate(oCanvas)
            #out = self.valoreAttuale != self.valorePrecedente
        #return out
        self.evaluate(oCanvas)
        out = self.valoreAttuale != self.valorePrecedente
        return out
    
    def isHeaderToPrint(self, lSet=None):
        """
        Ispeziona e setta lo stato della variabile che controlla la stampa
        dell'intestazione del gruppo.
        Nel caso non venga fornito alcun parametro il metodo restituisce lo
        stato della variabile (True/False), in caso contrario provvede a settarla
        secondo quanto fornito come parametro.
        @return: B{True} se è necessario provvedere alla stampa dell'intestazione del gruppo, {False} in caso contario
        @rtype: bool
        """
        return self.oGroupHeader.isToPrint(lSet)
    
    def isFooterToPrint(self, lStampa=True):
        """
        Ispeziona e setta lo stato della variabile che controlla la stampa
        del piede del gruppo.
        Nel caso non venga fornito alcun parametro il metodo restituisce lo
        stato della variabile (True/False), in caso contrario provvede a settarla
        secondo quanto fornito come parametro.
        @return: B{True} se è necessario provvedere alla stampa del piede del gruppo, B{False} in caso contario
        @rtype: bool
        """
        self.oGroupFooter.isToPrint(lStampa)
    
    def isHeaderWaitingFooter(self, lSet=None):
        """
        Il metodo ispeziona e setta la variabile che controlla l'alternanza di stampa
        dell'intestazione e del piede. Ogni volta che viene stampata l'intestazione del gruppo 
        la variabile viene impostata a B{True} mentre ad ogni stampa del piede del gruppo viene impostata a B{False}.
        @return: B{True} se risulta essere già stato stampata l'intestazione del gruppo, B{False} in caso contrario
        @rtype: bool
        """
        return self.oGroupHeader.isWaitingFooter(lSet)
    
    def setPageChanged(self, x):
        self.pageChanged = x
    
    def getPageChanged(self):
        return self.pageChanged


class genericBand:
    '''
    La classe si fa carico di trattare le vari elementi (B{I{bande}}) di cui si compone la definizione del report.
    
    Con il termine B{bande} si intendono le varie fasce di cui si compone il report e quindi:
        - Intestazione report
        - Intestazione pagina
        - Intestazione gruppi
        - Dettaglio
        - Piede gruppi
        - Piede Pagina
        - ecc.
        
    La classe viene instanziata passadogli il ramo del dizionario contenente la definizionme della banda desiderata.
    
    @cvar daStampare: indica se l'elemento del report (B{banda}) debba essere stampata B{True} o meno B{False}
    @type daStampare: bool
    @cvar altezza: indica l'altezza dell'elemento del report (B{banda}) espressa in pixel.
    @type altezza: int
    @cvar dDefinizione_Banda: definizione dettagliata degli elementi che compaiono nella (B{banda} così come sono definiti nel file in  formato XML che definisce il report.
    @type dDefinizione_Banda: dizionario
    '''
    oCanvas=None
    daStampare=None
    altezza=None
    altezzaEstesa=None
    dDefinizione_Banda=None
    needResetVariable=None
    mnemonicName=None
    printWhenExpression=None
    insideObject=None
    
    def __init__(self, dDefinizione_report, oCanvas):
        """
        @param dDefinizione_report: dizionario di definizione report relativo all'elemento che deve essere rappresentato.
        @type dDefinizione_report: dizionario
        """
        self.oCanvas=oCanvas
        self.daStampare=True
        self.needResetVariable=True        
        self.dDefinizione_Banda=dDefinizione_report["band"]
        self.loadInsideObject()
        self.altezza=self.set_altezza()
        self.altezzaEstesa=self.altezza
        self.set_printWhenExpression() 


    def loadInsideObject(self):
        self.insideObject=[]
        l=[e for e in self.dDefinizione_Banda if e[3:4]=='_' and e[:3].isdigit()]
        l.sort()
        for e, d in [(x[4:],self.dDefinizione_Banda[x])  for x in l]:
            if  e == "staticText":
                self.insideObject.append(staticText(d, self.oCanvas))
            elif e == "textField":
                self.insideObject.append(variableText(d, self.oCanvas))
            elif e == "rectangle":
                self.insideObject.append(rettangolo(d))
            elif e == "ellipse":
                self.insideObject.append(elisse(d))
            elif e == "line":
                self.insideObject.append(linea(d))
            elif e == "image":
                self.insideObject.append(immagine(d))

    def set_printWhenExpression(self):
        self.printWhenExpression=""
        for e in [k for k in self.dDefinizione_Banda.keys() if "printWhenExpression" in k]:
            try:
                self.printWhenExpression=self.dDefinizione_Banda[e]["DATA"]
            except:
                pass
                
    def set_altezza(self):
        try:
            o = self.dDefinizione_Banda["height"]
        except KeyError:
            o = 0
        return o

    def get_altezza(self):
        return self.altezza

    def set_altezzaEstesa(self, h=None):
        if h<>None:
            self.altezzaEstesa=h
        return self.altezzaEstesa
    
    def isToPrint(self, lSet=None):
        """
        Ispeziona e setta lo stato della variabile che controlla la stampa.
        Nel caso non venga fornito alcun parametro isToPrint() restituisce lo
        stato della variabile (True/False), in caso contrario provvede a settarla
        secondo quanto fornito come parametro.
        @return: B{True} se è necessario provvedere alla stampa, {False} in caso contario
        @rtype: bool
        """
        if lSet<>None:
            self.daStampare=lSet
        return self.daStampare

    def format(self, oCanvas, y=None):
        _max=self.set_altezza()
        self.set_altezzaEstesa(self.get_altezza())
        #print "Altezza Banda: %d" % self.set_altezza()
        for o in self.insideObject:
            o.refresh()
            o.set_attributiTesto()
            o.format(oCanvas)
            _max=max(_max, int(o.set_topFromBand())+o.set_extendedheight()+1)
        #print "Nuova Altezza Banda: %d" % _max
        self.set_altezzaEstesa(_max)
            
            
            

    def output(self, oCanvas, y=None):
        """
        Stampa Banda.
        Il metodo si fa carico di esaminare tutti gli elementi che compaiono nella definizione
        della B{Banda} e produrne l'output sul documento pdf.
        @parameter oCanvas: oggetto che presiede alla produzione del file PDF.
        @type oCanvas: L{astraCanvas}
        @parameter y: (facoltativo). Indica la posizione verticale a cui ha origine la banda, 
        nel caso non venga specificata viene assunta come origine della banda la posizione a 
        cui terninava la banda precedente.
        @type y: int
        @return: Posizione verticale occupato dal lato inferiore della B{banda}, praticamente indica sulla pagina fino a dove la banda si estende.
        @rtype: int
        """
        lPrint=True
        if len(self.printWhenExpression)>0:
            lPrint=False
            xx=Expression(self.printWhenExpression)
            if xx.evaluate(oCanvas)==True:
                lPrint=True
        if y==None:
            y=oCanvas.get_row()
        if not lPrint==True:
            return y
        self.isToPrint(False)
        for o in self.insideObject:
            o.refresh()
            o.output(oCanvas, y)
        #oCanvas.setFillColorRGB(1,0,1)
        #oCanvas.setFont("Helvetica", 3)        
        #oCanvas.drawString(0,y,str(y)+','+str(y-self.altezza)+' ' + self.__class__.__name__ )
        if self.needResetVariable==True:
            oCanvas.resetVariabili(self.mnemonicName)            
        return y-self.altezzaEstesa
    
class groupHeader(genericBand):
    """
    La classe si fa carico di estrarre dalla definizione del report
    la definizione dell'intestazione di Gruppo GROUP HEADER
    
    @cvar nomeGruppo: nome simbolico che identifica il gruppo a cui si riferische il groupHeader.
    @type nomeGruppo: string
    @cvar needResetVariable: indica se all'atto della stampa delle instestazione di gruppo deve essere avviata la procedura che resetta le variabili utente secondo quanto spefcificato del file XML.
    @type needResetVariable: bool
    @cvar waitFooter: indica se l'intestazione gruppo sia già stata stampata e pertanto se sia in attesa che venga stampato l'eventuale piede gruppo.
    @type waitFooter: bool
    """
    nomeGruppo=None
    waitFooter=None
    
    def __init__(self, dDefinizione_report, oCanvas, nomeGruppo=None):
        """
        @param dDefinizione_report: Definizione Report. 
        @type dDefinizione_report: dizionario
        @param nomeGruppo: nome simbolico gruppo a cui si riferisce l'oggetto.
        @type nomeGruppo: string
        """
        self.waitFooter=False
        self.nomeGruppo=nomeGruppo
        genericBand.__init__(self, dDefinizione_report["groupHeader"], oCanvas)
        self.mnemonicName=["GroupHeader", nomeGruppo]

    def isWaitingFooter(self, lSet=None):
        """
        Il metodo ispeziona e setta la variabile che controlla l'alternanza di stampa
        dell'intestazione e del piede. Ogni volta che viene stampata l'intestazione del gruppo 
        la variabile viene impostata a B{True} mentre ad ogni stampa del piede del gruppo viene impostata a B{False}.
        @return: B{True} se risulta essere già stato stampata l'intestazione del gruppo, B{False} in caso contrario
        @rtype: bool
        """
        if lSet<>None:
            self.waitFooter=lSet
        return self.waitFooter
        
        
    def output(self, oCanvas):
        """
        Stampa Intestazione Gruppo dopo:
        - aver provveduto ad impostare a B{True} la variabile B{self.waitFooter} ad indicare che vi è una intestazione di 
        gruppo I{"aperta"} che dovrà essere successivamente I{"chiusa"} con la stampa del piede gruppo.
        - avere provveduto a resettare le variabili utente se richiesto da L{needResetVariable}
        Il metodo overrides quello della classe padre B{genericBand} unicamente al fine di 
        provvede all'esecuzione delle succitate funzioni e quindi richiama in modo espilito il metodo del padre.
        @param oCanvas: Definizione Report. 
        @type oCanvas: astraCanvas
        @return: altezza in pixel della stampa prodotta
        @rtype: int
        """
        self.waitFooter=True
        xx=genericBand.output(self, oCanvas)
        self.needResetVariable=False
        return xx
    
    
    # vecchia definizione della resetVariable
    #def resetVariable(self, nomeGruppo, oCanvas):
        #resetType=None
        #for v in Variable.variableList.keys():
            #resetType=Variable.variableList[v].resetType
            #if resetType=="Group":
                #x=Variable.variableList[v].resetGroup
                #if x==nomeGruppo:
                    #Variable.variableList[v].reset(self.oCanvas)
                    #print "RESET PAGE:",
                    #print Variable.variableList[v].valore
        #self.needResetVariable=False
    
    
class groupFooter(genericBand):
    '''
    La classe si fa carico di estrarre dalla definizione del report
    la definizione del piè di Gruppo GROUP FOOTER
    '''

    def __init__(self, dDefinizione_report, oCanvas, nomeGruppo=None):
        """
        @param dDefinizione_report: Definizione Report. 
        @type dDefinizione_report: dizionario
        @param nomeGruppo: nome simbolico gruppo a cui si riferisce l'oggetto.
        @type nomeGruppo: string
        """
        self.nomeGruppo=nomeGruppo
        genericBand.__init__(self, dDefinizione_report["groupFooter"], oCanvas)
        self.mnemonicName=["GroupFooter", nomeGruppo]




class pageHeader(genericBand):
    '''
    La classe si fa carico di estrarre dalla definizione del report
    la definizione dell'intestazione Pagina PAGE HEADER.
    '''
    
    def __init__(self, dDefinizione_report, oCanvas):
        genericBand.__init__(self,dDefinizione_report["pageHeader"], oCanvas)
        self.mnemonicName="PageHeader"
        
     
    def output(self, oCanvas):
        """
        Stampa Intestazione Pagina
        Dopo aver impostato a True l'attributo di NewPage ed aver incrementato il numero di pagina, 
        provvede a stampare l'intestazione pagina ricorrendo al metodo B{L{output<genericBand.output>}}
        dell'oggetto padre B{L{genericBand}}.
        
        @param oCanvas: Oggetto che presiede alla produzione del documento in formato PDF. 
        @type oCanvas: L{astraCanvas}
        @return: altezza in pixel della stampa prodotta
        @rtype: int
        """
        oCanvas.newPage=True
        oCanvas.pageNumber=oCanvas.pageNumber+1
        return genericBand.output(self, oCanvas)
     
    

class pageFooter(genericBand):
    """
    La classe si fa carico di estrarre dalla definizione del report
    la definizione del piè pagina PAGE FOOTER
    """
    
    def __init__(self, dDefinizione_report, oCanvas):
        genericBand.__init__(self, dDefinizione_report["pageFooter"], oCanvas)
        self.mnemonicName="PageFooter"
        
        
     
    def output(self, oCanvas):
        """
        Stampa Piè Pagina.
        """
        return genericBand.output(self,oCanvas, oCanvas.get_bottomMargin()+self.get_altezza())
     

        
class background(genericBand):
    """
    La classe si fa carico di estrarre dalla definizione del report
    la definizione del background del report BACKGROUND.
    """
    def __init__(self, dDefinizione_report, oCanvas):
        genericBand.__init__(self,dDefinizione_report["background"], oCanvas)
        self.mnemonicName="Background"
        
class title(genericBand):
    """
    La classe si fa carico di estrarre dalla definizione del report
    la definizione dell'intestazione del report TITLE.
    """
    def __init__(self, dDefinizione_report, oCanvas):
        genericBand.__init__(self,dDefinizione_report["title"], oCanvas)
        self.mnemonicName="Report"

    
class columnHeader(genericBand):
    """
    La classe si fa carico di estrarre dalla definizione del report
    la definizione dell'intestazione delle colonne COLUMN HEADER.
    """
    def __init__(self, dDefinizione_report, oCanvas):
        genericBand.__init__(self, dDefinizione_report["columnHeader"], oCanvas)
        self.mnemonicName="ColumnHeader"
        
        
     
class detail(genericBand):
    """
    La classe si fa carico di estrarre dalla definizione del report
    la definizione delle righe di dettaglio.
    """
    def __init__(self, dDefinizione_report, oCanvas):
        genericBand.__init__(self, dDefinizione_report["detail"], oCanvas)
        self.mnemonicName="Detail"
        
     
    def output(self, oCanvas):
        """
        Stampa Dettaglio.
        """
        oCanvas.newPage=False
        oCanvas.incrementaVariabili("Detail")
        return genericBand.output(self, oCanvas)
    

