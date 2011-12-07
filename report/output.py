#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/output.py
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

import locale
import getopt
import sys
import os
import string

import stormdb as adb

import report
from report.read import iReportDef
from report.multielement import *
from report.element import *
from report.querystru import *
from report.variables import *
from types import *

from reportlab.pdfgen import canvas
from reportlab import rl_config
from reportlab.lib.pagesizes import A4, landscape, portrait

import MySQLdb

import wx
import awc.controls.windows as aw
import awc.util as awu

import stormdb as adb


_debug = 0


class astraCanvas(canvas.Canvas):
    """
    """
    oPageFormat=None
    recordSource=None
    queryStru=None
    recordSetRow=None
    row=None
    pageNumber=None
    newPage=None
    userVariableList=None
    
    def __init__(self, oIreport, pdfFileName):
        self.oPageFormat=page_Format(oIreport.get_ReportStru(), pdfFileName)
        if self.oPageFormat.orientamento=="Landscape":    
            x=landscape((self.oPageFormat.larghezza,self.oPageFormat.altezza))
        else:
            x=portrait((self.oPageFormat.larghezza,self.oPageFormat.altezza))
            
        self.set_row(self.oPageFormat.altezza-self.oPageFormat.topMargin)
        canvas.Canvas.__init__(self, self.oPageFormat.nomepdf,
                               pagesize=x,
                               bottomup =1,
                               pageCompression=0,
                               #encoding=rl_config.defaultEncoding,
                               verbosity=0)
        self.pageNumber=0

    def incrementaVariabili(self, bandName):
        if isinstance(bandName, list):
            incrementType=bandName[0]
            if incrementType=="GroupHeader":
                incrementType="Group"
            incrementGroup=bandName[1]
        else:
            if bandName=="PageHeader":
                bandName="Page"
            elif bandName == 'Detail':
                #in iReport non c'è un incremento di tipo Detail => uso Column
                bandName = 'Column'
            incrementType=bandName
        varlist = list(self.userVariableList)
        varlist.sort()
        for i in varlist:
            o=self.userVariableList[i]
            if o.incrementType==incrementType:
                if incrementType=="Group":
                    if o.incrementGroup==incrementGroup:
                        o.incrementa(self)
                else:
                    o.incrementa(self)
    
    def resetVariabili(self, bandName):
        if isinstance(bandName, list):
            resetType=bandName[0]
            if resetType=="GroupFooter":
                resetType="Group"
            resetGroup=bandName[1]
        else:
            resetType=bandName
        for i in self.userVariableList:
            o=self.userVariableList[i]
            if o.resetType==resetType:
                if resetType=="Group":
                    if o.resetGroup==resetGroup:
                        o.reset(self)
                else:
                    o.reset(self)
            pass
        
    def set_recordSource(self, record):
        self.recordSource=record

    def set_queryStru(self, oStru):
        self.queryStru=oStru
        
    def print_margin(self):
        """Il metodo, presente a fini di debug, provvede a disegnare il contorno dello spazio utile per la stampa.
        """
        x1=self.oPageFormat.get_leftMargin()
        y1=self.oPageFormat.get_bottomMargin()
        x2=self.oPageFormat.get_larghezza()- self.oPageFormat.get_rightMargin()
        y2=self.oPageFormat.get_altezza()- self.oPageFormat.get_topMargin()
        dx=self.oPageFormat.get_larghezzaReale()
        dy=self.oPageFormat.get_altezzaReale()
        self.rect(x1,y1,dx,dy)

    def get_row(self):
        """Restituisce la posizione orizzontale di stampa (riga) in pixel.
        """
        return self.row

    def set_row(self, r):
        """Imposta la posizione orizzontale di stampa (riga) in pixel.
        """
        self.row=r

    def get_altezza(self):
        """Restituisce la dimensione verticale del foglio in pixel.
        """
        return self.oPageFormat.get_altezza()

    def get_largezza(self):
        """Restituisce la dimensione orizzontale del foglio in pixel.
        """
        return self.oPageFormat.get_larghezza()
    
    def get_topMargin(self):
        return self.oPageFormat.get_topMargin()
    
    def get_bottomMargin(self):
        return self.oPageFormat.get_bottomMargin()
    
    def get_rightMargin(self):
        """Restituisce la posizione in pixel del margine destro di stampa.
        """
        return self.oPageFormat.get_rightMargin()
    
    def get_leftMargin(self):
        """Restituisce la posizione in pixel del margine sinistro di stampa.
        """
        return self.oPageFormat.get_leftMargin()
    
    def get_larghezzaReale(self):
        """Restituisce la dimesione orizzontale in pixel dello spazio utile per la stampa.
        
        Equivale a B{larghezza foglio - margine sinistro - margine destro}
        """
        return self.oPageFormat.get_larghezzaReale()

    def get_altezzaReale(self):
        """Restituisce la dimesione verticale in pixel dello spazio utile per la stampa.
        
        Equivale a B{altezza foglio - margine superiore - margine inferiore}
        """
        return self.oPageFormat.get_altezzaReale()
    
    def ejectPage(self):
        if _debug==1:
            self.print_margin()
        self.showPage()


import report.report_wdr as wdr

class MultiCopiaPanel(wx.Panel):
    
    def __init__(self, *args, **kwargs):
        multicopia = kwargs.pop('multicopia')
        wx.Panel.__init__(self, *args, **kwargs)
        self.multicopia = wdr.multicopia = multicopia
        wdr.MultiCopiaFunc(self)
        self.Layout()
        self.Bind(wx.EVT_BUTTON, self.OnConferma, self.FindWindowByName('butok'))
    
    def OnConferma(self, event):
        if self.Validate():
            event.Skip()
    
    def Validate(self):
        out = True
        return out

class MultiCopiaDialog(aw.Dialog):
    
    def __init__(self, *args, **kwargs):
        multicopia = kwargs.pop('multicopia')
        aw.Dialog.__init__(self, *args, **kwargs)
        self.panel = MultiCopiaPanel(self, multicopia=multicopia)
        self.Fit()
        self.Bind(wx.EVT_BUTTON, self.OnConferma, self.FindWindowByName('butok'))
    
    def OnConferma(self, event):
        self.EndModal(wx.ID_OK)
    
    def GetCopieSelez(self):
        return self.FindWindowByName('copiepanel').GetCopieSelez()


class print_Report:
    '''
    La classe si fa carico di generare il documento  .PDF secondo quanto previsto
    dal file .jrxml esaminato (file in formato XML prodotto da iReport).
    
    @cvar oReport: Definizione del report, sotto forma di dizionario, cosi' come definito nel file in formato .XML.
    Viene ottenuto istanziando la classe B{L{iReportDef(nameXmlFile, source)}}.
    @type oReport: Dizionario nel formato descritto da L{iReportDef} 
    @cvar oQueryStru: Oggetto che conserva le informazioni sulla struttura dei campi della query su cui poggia il report.
    @type oQueryStru: L{QueryStru}
    @cvar oCanvas: Oggetto che presiede alla produzione del documento in formato PDF. Viene ottenuto istanziando la classe B{L{astraCanvas}}.
    @type oCanvas: L{astraCanvas}
    @cvar oTitle: Oggetto che presiede alla gestione del titolo del documento.
    @type oTitle: L{title}
    @cvar oPageHeader: Oggetto che presiede alla gestione dell'intestazione di pagina del report.
    @type oPageHeader: L{pageHeader}
    @cvar oColumnHeader: Oggetto che presiede alla gestione delle colonne di dettaglio del report.
    @type oColumnHeader: L{columnHeader}
    @cvar oDetail: Oggetto che presiede alla gestione del dettaglio del report.
    @type oDetail: L{detail}
    @cvar oPageFooter: Oggetto che presiede alla gestione del piè di pagina del report.
    @type oPageFooter: L{pageFooter}
    @cvar lGroup: lista degli oggetti di tipo L{group} che presiedono alla gestione delle rotture nell'ambito del report.
    @type lGroup: lista di L{group}
    '''
    oReport=None
    oQueryStru=None
    oCanvas=None
    oBackGround=None
    oTitle=None
    oPageHeader=None
    oColumnHeader=None
    oDetail=None
    oPageFooter=None
    lGroup=None
    lFlatReport=None
    #oPageFormat=None
    #cQueryExpression=None
    StoreRecordPosition=None
    completed = False
    nameOutputFile = None

    def __init__(self, 
                 nameXmlFile=None, 
                 nameOutputFile=None, 
                 output="VIEW",
                 source=None,
                 cursor=None,
                 connection=None,
                 sqlString=None,
                 queryStructure=None,
                 recordSet=None,
                 progressBar=None,
                 dbTable=None,
                 waitMessage=None,
                 pageCount=None,
                 pdfWindow=None,
                 noMove=None,
                 exitOnGroup=None,
                 parentWindow=None,
                 rowFunc=None,
                 rowFilter=None,
                 canvas=None,
                 startFunc=None,
                 endFunc=None,
                 messages=True,
                 usedde=False,
                 printer=None,
                 labeler=None,
                 copies=None,
                 pdfcmd=None,
                 firstPageNumber=None,
                 filtersPanel=None,
                 changefilename=None,
                 multicopia_init=None,
                 multicopia_reactor=None):
        
        self.printed = False
        
        output=upper(output)
        if not output in ["VIEW", "PRINT", "STORE"]:
            output="VIEW"
        
        if nameOutputFile and type(nameOutputFile) in (str, unicode):
            nameOutputFile = report.epura(nameOutputFile, True).replace('\\', '/')
#            p = ''
#            for pp in awu.up(nameOutputFile).split('/')[:-1]:
#                if pp:
#                    p = os.path.join(p, pp).replace('\\', '/')
#                else:
#                    p += '/'
#                if len(p)>=3 and (not p.startswith('//') or len(p)-len(p.replace('/', ''))>3):
#                    c = True
#                    if not os.path.isdir(p):
#                        os.mkdir(p)
            basePath, _ = os.path.split(nameOutputFile)
            try:
                if not os.path.isdir(basePath):
                    os.makedirs(basePath)
            except:
                msg = 'Impossibile creare la cartella %s' % basePath
                if messages:
                    awu.MsgDialog(None, msg, style=wx.ICON_ERROR)
                    return None
                else:
                    raise Exception, msg
        
        #impostazione multicopia
        multicopia = ['standard']
        if output in 'VIEW PRINT'.split():
            mc = nameXmlFile.replace('\\', '/')
            mc = mc.replace('.jrxml', '.multicopia')
            if os.path.exists(mc):
                try:
                    h = open(mc, 'r')
                    l = h.readlines()
                    h.close()
                    multicopia = [[x.replace('\n',''), 1] for x in l]
                    for mc in multicopia:
                        if mc[0].endswith('[0]'):
                            mc[0] = mc[0][:-3]
                            mc[1] = 0
                        elif mc[0].endswith('[1]'):
                            mc[0] = mc[0][:-3]
                    if callable(multicopia_init):
                        multicopia_init(multicopia)
                    mc = multicopia
                    if messages:
                        d = MultiCopiaDialog(parentWindow, -1, 'MultiCopia', multicopia=multicopia)
                        d.CenterOnParent()
                        do = d.ShowModal() == wx.ID_OK
                        c2p = d.GetCopieSelez()
                        d.Destroy()
                        if not do:
                            return
                        if callable(multicopia_reactor):
                            multicopia_reactor(multicopia)
                        multicopia = []
                        for c, p in mc:
                            if c2p[c]:
                                multicopia.append(c)
                    else:
                        if callable(multicopia_reactor):
                            multicopia_reactor(multicopia)
                        multicopia = []
                        for c, p in mc:
                            if p:
                                multicopia.append(c)
                    if len(multicopia) == 0:
                        msg = "Definire almeno una copia"
                        if messages:
                            aw.awu.MsgDialog(parentWindow, msg)
                            return
                        raise Exception, msg
                except Exception, e:
                    msg = repr(e.args)
                    if messages:
                        aw.awu.MsgDialog(parentWindow, msg)
                        return
                    raise Exception, msg
        
        if sys.platform == 'win32':
            nameXmlFile = nameXmlFile.replace('/', '\\')
        
        self.oReport = iReportDef(nameXmlFile, source)
        
        if changefilename:
            fp, fn = os.path.split(nameOutputFile)
            nameOutputFile = os.path.join(fp, changefilename).replace('/', '\\')
            if not nameOutputFile.lower().endswith('.pdf'):
                nameOutputFile += '.pdf'
        
        if canvas is None:
            #nuovo canvas
            self.oCanvas = astraCanvas(self.oReport, nameOutputFile)
        else:
            #canvas già creato (report accodato)
            self.oCanvas = canvas
        
        """
        Inizio del ciclo di stampa
        """
        
        # Predispongo i vari elementi del report
        self.loadUserParameter(self.oReport.get_ReportStru()) 
        
        
        #xx= self.oReport.get_FlatProperty()
        if isPrompting():
            print "VISUALIZZA PROMPT"
        self.loadUserVariable(self.oReport.get_ReportStru())
        
        if firstPageNumber is not None:
            vnp = self.oCanvas.userVariableList['PAGE_NUMBER']
            vnp.oResetExpression.textFieldExpression=str(firstPageNumber)
        
        #spostate sotto
        #for o in self.oCanvas.userVariableList.keys():
        #     #Variable.variableList[o].reset(self.oCanvas)
        #     self.oCanvas.userVariableList[o].reset(self.oCanvas)
        
        #self.oBackGround=background(self.oReport.get_ReportStru(), self.oCanvas)
        #self.oTitle=title(self.oReport.get_ReportStru(), self.oCanvas)
        #self.oPageHeader=pageHeader(self.oReport.get_ReportStru(), self.oCanvas)
        #self.oColumnHeader=columnHeader(self.oReport.get_ReportStru(), self.oCanvas)
        #self.oPageFooter=pageFooter(self.oReport.get_ReportStru(), self.oCanvas)
        #self.loadGroup(self.oReport.get_ReportStru(), self.oCanvas)
        
        uselabeler = False
        
        #valutazione proprietà personalizzare
        queuedef = queuetab = None
        stru = self.oReport.get_ReportStru()
        prop = [e for e in stru if e[:8]=="property"]
        for p in prop:
            elem = stru[p]
            name, val = elem['name'], elem['value']
            #valutazione espressioni di tutte le prop. che iniziano con 'py_'
            if name.startswith('py_'):
                val = val.split("|")
                if val is not None:
                    for expr in (val):
                        if len(expr)>0:
                            expr = replace(expr, "RS.", "dbTable.")
                            try:
                                eval(expr)
                            except:
                                msg = "Espressione non valida per la proprietà denominata '%s'" % elem['name']
                                if messages:
                                    aw.awu.MsgDialog(parentWindow, message=msg)
                                else:
                                    raise Exception, msg
            elif name == 'EnqueueReport':
                val = replace(val, "RS.", "dbTable.")
                try:
                    queuedef = eval(val)
                except Exception, e:
                    msg = 'Errore in valutazione nome report accodato\n(%s)'\
                        % repr(e.args)
                    if messages:
                        aw.awu.MsgDialog(parentWindow, message=msg)
                    else:
                        raise Exception, msg
            elif name == 'EnqueueTable':
                val = replace(val, "RS.", "dbTable.")
                try:
                    queuetab = eval(val)
                except Exception, e:
                    msg = 'Errore in valutazione tabella report accodato\n(%s)'\
                        % repr(e.args)
                    if messages:
                        aw.awu.MsgDialog(parentWindow, message=msg)
                    else:
                        raise Exception, msg
            elif name == 'UseLabeler':
                uselabeler = (val == 'True')
        
        if uselabeler and printer != labeler:
            msg = "Il report usa un formato specifico per etichettatrice, la stampante selezionata potrebbe portare a risultati non idonei."
            if labeler:
                msg += "\nUso la stampante etichettatrice '%s' ?" % labeler
            else:
                msg += "Non risulta essere configurata l'etichettatrice su questa workstation, si consiglia di non proseguire nella stampa.\nInterrompo l'elaborazione?"
            if aw.awu.MsgDialog(parentWindow, msg, style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES:
                if labeler:
                    printer = labeler
                else:
                    return
        
        doprogress = progressBar is None and progressBar.__class__.__name__ != 'NullProgress' and output != "STORE"
        
        for mc in multicopia:
            
            dbTable._info.report_nome_copia = mc
            
            self.lFlatReport=self.loadFlatProperty(self.oReport.get_ReportStru(), dbTable)
            if self.lFlatReport == True:
                dbTable.SetFlatView()       
            
            self.oCanvas.set_recordSource(dbTable)
            self.oBackGround=background(self.oReport.get_ReportStru(), self.oCanvas)
            self.oTitle=title(self.oReport.get_ReportStru(), self.oCanvas)
            self.oPageHeader=pageHeader(self.oReport.get_ReportStru(), self.oCanvas)
            self.oColumnHeader=columnHeader(self.oReport.get_ReportStru(), self.oCanvas)
            self.oPageFooter=pageFooter(self.oReport.get_ReportStru(), self.oCanvas)
            self.loadGroup(self.oReport.get_ReportStru(), self.oCanvas)
            
            self.oTitle.mnemonicName = 'Title'
            
            statit = False
            if filtersPanel:
                if messages:
                    statit = awu.MsgDialog(parentWindow, "Vuoi stampare le selezioni?", style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT) == wx.ID_YES
                    if statit:
                        self.AddFiltersPanelTitleElements(filtersPanel)
                else:
                    statit = False
            
            if doprogress:
                re_enable = awu.GetParentFrame(parentWindow).Disable()
                wait = awu.WaitDialog(parentWindow, message=waitMessage,
                                      maximum=dbTable.RowsCount())
                self.progressBar = progressBar = wait.progress
                if messages:
                    focused_object = parentWindow.FindFocus()
            else:
                wait = None
            
            try:
                r=0
                if progressBar <> None:
                    progressBar.SetRange(dbTable.RowsCount())
                if pageCount <> None:
                    pageCount.SetLabel("0")
                
                if not noMove:
                    if self.oCanvas.recordSource.IsEmpty():
                        dbrow = None
                    else:
                        dbrow = dbTable.RowNumber()
                    self.oCanvas.recordSource.MoveFirst()
                for o in self.oCanvas.userVariableList.keys():
                    self.oCanvas.userVariableList[o].reset(self.oCanvas)
                
                if exitOnGroup is None:
                    exitOnGroup = False
                
                if rowFilter is None:
                    rowFilter = lambda *x: True
                
                dbt = self.oCanvas.recordSource
                
                groups = []
                for g in self.lGroup:
                    groups.append([0,0])
                
                lEof=False
                lBeginReport=True
                
                if callable(startFunc):
                    startFunc(self, dbTable)
                
                self.rowFunc = rowFunc
                
                if doprogress:
                    self.timer = wx.Timer(progressBar)
                    progressBar.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
                    self.timer.Start(1000)
                else:
                    self.timer = None
                
                self.dbt_row = None
                
                while not lEof:
                    
                    if callable(rowFunc):
                        rowFunc(self, dbTable)
                    
#                    if progressBar <> None:
#                        progressBar.SetValue(dbt.RowNumber()+1)
                    if progressBar:
                        self.dbt_row = dbt.RowNumber()
                        if messages:
                            wx.YieldIfNeeded()
                    
                    if not rowFilter(dbt):
                        if not dbt.MoveNext():
                            break
                        continue
                    
                    if statit:
                        self.stampaTitoloBand()
                        self.DelFiltersPanelTitleElements()
                        statit = False
                    self.stampaTestata()
                    
                    if not lBeginReport and self.rotturaGruppo():
                        self.stampoRottura()
                        if exitOnGroup:
                            break
                    else:
                        lBeginReport=False
                        lEof = self.stampoDettaglio(pageCount) 
                
                if callable(endFunc):
                    endFunc(self, dbTable)
                
                lg=self.lGroup.keys()
                lg.sort()
                if not exitOnGroup:
                    self.stampaFooterGruppi( True)
                    self.ejectPage()
                
            finally:
                if wait is not None:
                    wait.Destroy()
                    try:
                        del self.timer
                    except:
                        pass
                    awu.GetParentFrame(parentWindow).Enable(re_enable)
                    if messages:
                        if focused_object is not None:
                            try:
                                wx.CallAfter(lambda: focused_object.SetFocus())
                            except:
                                pass

            
            if queuedef:
                if not queuetab.IsEmpty():
                    #richiamo report accodato
                    qd = nameXmlFile.replace('\\','/')
                    qd = qd[:qd.rindex('/')+1]+queuedef+'.jrxml'
                    pn = self.oCanvas.userVariableList['PAGE_NUMBER'].valore
                    print_Report(qd, dbTable=queuetab, canvas=self.oCanvas,
                                 parentWindow=parentWindow, firstPageNumber=pn)
            
            if self.lFlatReport == True:
                dbTable.SetFlatView(False)       
            
            if not noMove and dbrow is not None:
                dbTable.MoveRow(dbrow)
            
            del dbTable._info.report_nome_copia
        
        if canvas:
            #report accodato, ritorno
            # la chiusura del file è fatta dal report principale
            return
        
        self.completed = True
        
        while True:
            try:
                self.oCanvas.save()
                if type(nameOutputFile) in (str, unicode) and sys.platform == 'win32':
                    nameOutputFile = nameOutputFile.replace('/', '\\')
                if output != "STORE":
                    if sys.platform == 'win32':
                        from pdfprint import PdfView, PdfPrint
                    else:
                        from pdflinux import PdfView, PdfPrint
                    if output == "VIEW":
                        PdfView(os.path.abspath(nameOutputFile), usedde=usedde, pdfcmd=pdfcmd)
                    elif output == "PRINT":
                        if messages:
                            f = parentWindow.FindFocus()
                            def RipristinaFocus():
                                if f is not None:
                                    f.SetFocus()
                        else:
                            def RipristinaFocus():
                                pass
                        if printer.startswith('gcp://'):
                            from report.pdfcloud import PdfCloudPrint
                            PdfCloudPrint(os.path.abspath(nameOutputFile), printer[6:], RipristinaFocus)
                        else:
                            copies = copies or 1
                            PdfPrint(os.path.abspath(nameOutputFile), printer, copies, RipristinaFocus)
                    else:
                        raise Exception, 'tipo di output non riconosciuto'
                self.nameOutputFile = nameOutputFile
                self.printed = True
                break
            except IOError, e:
                if e.args[0] == 13:
                    #permission denied, file is open
                    msg =\
                        """Il documento risulta non sovrascrivibile, """\
                        """probabilmente è aperto da un'altra applicazione.\n"""
                else:
                    #other file error
                    msg = """Non è possibile generare il documento:\n%s\n(%s)\n"""\
                        % (nameOutputFile, repr(e.args))
                if messages:
                    msg += """Vuoi riprovare a ricoprirlo nuovamente?"""
                    n = aw.awu.MsgDialog(None, message=msg,
                                         style=wx.ICON_QUESTION|wx.YES_NO|wx.YES_DEFAULT)
                    if n == wx.ID_NO:
                        aw.awu.MsgDialog(None, message=\
                                         """Il documento pdf non è stato """
                                         """generato.""")
                        break
                else:
                    raise Exception, msg
    
    def OnTimer(self, event):
        self.progressBar.SetValue(self.dbt_row+1)
    
    def GetFileName(self):
        return self.nameOutputFile
    
    def AddFiltersPanelTitleElements(self, filtersPanel):
        
        from report.element import staticText as ST
        from report.element import linea as LINE
        import copy
        
        t = self.oTitle
        t.dDefinizione_Banda = copy.copy(self.oPageHeader.dDefinizione_Banda)
        self.oTitle.insideObject = copy.copy(self.oPageHeader.insideObject)
        self.oTitle.altezza = self.oPageHeader.altezza
        self.oTitle.altezzaEstesa = self.oPageHeader.altezzaEstesa
        
        controls = awu.GetAllChildrens(filtersPanel, lambda x: isinstance(x, (wx.StaticText, wx.TextCtrl, wx.CheckBox)))
        controls = [[c.GetParent().ClientToScreen(c.GetPosition())[1],
                     c.GetParent().ClientToScreen(c.GetPosition())[0],
                     c.GetSize()[1],
                     c.GetSize()[0],
                     c] for c in controls]
        controls.sort()
        
        pf = self.oCanvas.oPageFormat
        drawable_width = pf.larghezza-pf.leftMargin-pf.rightMargin
        
        miny = minx = 44444
        for cy, cx, ch, cw, c in controls:
            miny = min(miny, cy)
            minx = min(minx, cx)
        WX_RATIO_X = float(filtersPanel.GetSize()[0])/float(drawable_width)
        WX_RATIO_Y = 2
        for c in controls:
            c[0] = (c[0]-miny)/WX_RATIO_Y
            c[1] = (c[1]-minx)/WX_RATIO_X
            c[2] = c[2]/WX_RATIO_Y
            c[3] = c[3]/WX_RATIO_X
        
        def_text = {}
        def_text['reportElement'] = {
            'backcolor':                  '#FFFFFF',
            'forecolor':                  '#000000',
            'height':                     10,
            'isPrintInFirstWholeBand':    'false',
            'isPrintRepeatedValues':      'true',
            'isPrintWhenDetailOverflows': 'false',
            'isRemoveLineWhenBlank':      'false',
            'key':                        'keyelement-0000',
            'mode':                       'Transparent',
            'positionType':               'FixRelativeToTop',
            'stretchType':                'NoStrech',
            'width':                      100,
            'x':                          0,
            'y':                          0
        }
        
        def_text['text'] = {'DATA': 'text'}
        
        def_text['textElement'] = {
            'font':              {'fontName':        'Times New Roman',
                                  'isBold':          'false',
                                  'isItalic':        'false',
                                  'isPdfEmbedded':   'false',
                                  'isStrikeThrough': 'false',
                                  'isUnderline':     'false',
                                  'pdfEncoding':     'Cp1252',
                                  'pdfFontName':     'Times-Roman',
                                  'size':            7,
                                  },
            'lineSpacing':       'Single',
            'rotation':          'None',
            'textAlignment':     'Left',
            'verticalAlignment': 'Top'
        }
        
        def_line = {
            'direction': 'TipDown',
            'graphicElement': {'fill':        'Solid',
                               'pen':         'Thin',
                               'stretchType': 'NoStrech'
                           },
            'reportElement': def_text['reportElement']
        }
        
        yos = self.oTitle.altezza
        hec = 15
        d = def_text
        re = d['reportElement']
        te = d['textElement']
        tx = d['text']
        
        for cy, cx, ch, cw, c in controls:
            
            ey = yos+cy
            ex = cx
            
            if isinstance(c, wx.StaticText):
                re['key'] = 'autolabel-%s' % c.GetName()
                tx['DATA'] = c.GetLabel()
                ta = 'Left'
                if not c.GetLabel().lower() in 'da: a:'.split():
                    ta = 'Right'
                te['textAlignment'] = ta
                te['font']['fontName'] =    'Times New Roman'
                te['font']['pdfFontName'] = 'Times-Roman'
                te['font']['isBold'] =      'false'
                
            elif isinstance(c, wx.TextCtrl):
                re['key'] = 'autovalue-%s' % c.GetName()
                tx['DATA'] = c.GetValue()
                te['textAlignment'] = 'Left'
                #if type(c.GetValue()) in (int, long, float, Env.DateTime.Date):
                    #te['font']['fontName'] =    'Courier New'
                    #te['font']['pdfFontName'] = 'Courier-Bold'
                #else:
                    #te['font']['fontName'] =    'Arial'
                    #te['font']['pdfFontName'] = 'Helvetica-Bold'
                te['font']['fontName'] =    'Times New Roman'
                te['font']['pdfFontName'] = 'Times-Roman'
                te['font']['isBold'] = 'true'
                ey += 3
                
            elif isinstance(c, wx.CheckBox) and c.IsChecked():
                re['key'] = 'autovalue-%s' % c.GetName()
                tx['DATA'] = c.GetLabel()
                te['textAlignment'] = 'Left'
                #te['font']['fontName'] =    'Arial'
                #te['font']['pdfFontName'] = 'Helvetica-Bold'
                te['font']['fontName'] =    'Times New Roman'
                te['font']['pdfFontName'] = 'Times-Roman'
                te['font']['isBold'] =      'true'
                
            else:
                continue
            
            re['y'] = ey
            re['x'] = ex
            re['width'] = cw
            re['height'] = 10#ch
            self.oTitle.insideObject.append(ST(d, self.oCanvas))
            ey = max(ey, ey)
        
        d = def_line
        re = d['reportElement']
        re['x'] = 0
        re['y'] = ey+hec
        re['width'] = drawable_width
        re['height'] = 0
        self.oTitle.insideObject.append(LINE(d))
        self.oTitle.altezza = self.oTitle.altezzaEstesa = ey+hec+5
    
    def DelFiltersPanelTitleElements(self):
        self.oTitle.dDefinizione_Banda = {}
        self.oTitle.insideObject = []
        self.oTitle.altezza = 0
        self.oTitle.altezzaEstesa = 0
    
    def stampoDettaglio(self, pageCount):
        lEof = False
        #????????????????
        self.oDetail = detail(self.oReport.get_ReportStru(), self.oCanvas)
        self.oDetail.format(self.oCanvas)
        if self.oCanvas.get_row()-self.oDetail.set_altezzaEstesa()<self.oCanvas.get_bottomMargin()+self.oPageFooter.get_altezza():
            self.ejectPage()
            if pageCount <> None:
                pageCount.SetLabel(str(self.oCanvas.pageNumber))
        else:
            self.oCanvas.set_row(self.oDetail.output(self.oCanvas))
            self.StoreRecordPosition=self.oCanvas.recordSource.SavePosition()
            if not self.oCanvas.recordSource.MoveNext():
                lEof = True
        if _debug == 1:
            print "stampa dettaglio"
        return lEof
           
    def stampoRottura(self):
        # per stampare la rottura è necessario tornare indietro di un record
        # poichè questa funzionalità è inibita nel caso di dbTable di tipo
        # FlatView verranno utilizzate i metodi SavePositio e RestorePosition
        dbt = self.oCanvas.recordSource
        if not self.lFlatReport:
            dbt.MovePrevious()
        else:
            pos = dbt.SavePosition()
            dbt.RestorePosition(self.StoreRecordPosition)
        if self.rowFunc:
            if callable(self.rowFunc):
                self.rowFunc(self, dbt)
        if not self.stampaFooterGruppi():
            #controllo se siano presenti gruppi in attesa di stampa dell'intestazione
            #che richiedano la stampa su nuova pagina
            if self.gruppiOnNewPage():
                self.ejectPage()
        if not self.lFlatReport:
            dbt.MoveNext()
        else:
            dbt.RestorePosition(pos)
        if self.rowFunc:
            if callable(self.rowFunc):
                self.rowFunc(self, dbt)
        if _debug==1:
            print "Stampa Rottura"
    
    def stampaTitoloBand(self):
        if self.oTitle.isToPrint():
            self.oCanvas.incrementaVariabili("Page")
            self.oCanvas.set_row(self.oTitle.output(self.oCanvas))
            self.oPageHeader.isToPrint(False)
            lPrint=True
    
    def stampaTestata(self, resetGroup=True):
        lPrint=False
        if self.oBackGround.isToPrint():
            self.oBackGround.output(self.oCanvas)
            lPrint=True
        if self.oTitle.isToPrint():
            self.oCanvas.set_row(self.oTitle.output(self.oCanvas))
            lPrint=True
        if self.oPageHeader.isToPrint():
            self.oCanvas.incrementaVariabili("Page")
            self.oCanvas.set_row(self.oPageHeader.output(self.oCanvas))
            lPrint=True
        if self.oColumnHeader.isToPrint():
            self.oCanvas.set_row(self.oColumnHeader.output(self.oCanvas))
            lPrint=True
        if self.stampaHeaderGruppi(resetGroup):
            lPrint=True
        if lPrint:
            if _debug==1:
                print "Stampa Testata"
        
    def loadFlatProperty(self,d, dbTable):
        v=None
        l= [e for e in d if e[:8]=="property"]
        for i in l:
            e=d[i]
            if e["name"]=="FlatSection":
                #print e
                v=e["value"].split("|")
        if not v==None:
            for i in (v):
                if len(i)>0:
                    i=replace(i, "RS.", "dbTable.")
                    eval(i)
            self.flatProperty=v        
        return not (v==None)

    def gruppiOnNewPage(self):
        """
        Il metodo, verifica se sia presente un gruppo che richieda la stampa dell'header 
        a nuova pagina se questo è il caso tutti i gruppi precedenti che richiedano la 
        stampa dell'header al cambio di pagina verranno marchiati come da stampare 
        isHeaderToPrint(True). 
        La modalità in cui viene effettuato il controllo è in senso inverso, dal gruppo
        più interno a quello più esterno.
        """
        lNeedNewPage=False
        lg=self.lGroup.keys()
        lg.sort()
        lg.reverse()
        for e in lg:
            pagechanged = False
            if lNeedNewPage==True:
                if self.lGroup[e].isReprintHeaderOnEachPage=="true":
                    self.lGroup[e].isHeaderToPrint(True)
                    pagechanged = True
                self.lGroup[e].setPageChanged(pagechanged)
            elif self.lGroup[e].isHeaderToPrint()==True and self.lGroup[e].isStartNewPage=="true":
                lNeedNewPage=True
        return lNeedNewPage
    
    def stampaHeaderGruppi(self, reset=True):
        """
        Il metodo, ciclando su tutti i gruppi presenti sul report, provvede a stampare i
        le intestazioni dei gruppi in attesa di essere stampati.
        """
        lPrint=False
        lAlreadyNewPage=False
        lg=self.lGroup.keys()
        lg.sort()
        for e in lg:            
            if self.lGroup[e].isHeaderToPrint():
                if self.oCanvas.newPage==False and self.lGroup[e].isStartNewPage=="true":
                    if lAlreadyNewPage==False:
                        lAlreadyNewPage=True
                        self.ejectPage()
                #else:
                #    if self.oCanvas.get_row() < self.lGroup[e].minHeightToStartNewPage:
                #        if lAlreadyNewPage==False:
                #            lAlreadyNewPage=True
                #            self.ejectPage()
                    
                
                if self.oCanvas.get_row()-self.lGroup[e].oGroupHeader.altezza-self.oPageFooter.get_altezza()-self.oCanvas.get_bottomMargin()<0:
                    self.ejectPage()
                    self.stampaTestata()
                    break
                
                if not reset:
                    self.lGroup[e].oGroupHeader.needResetVariable=reset
                self.oCanvas.set_row(self.lGroup[e].oGroupHeader.output(self.oCanvas))
                self.lGroup[e].evaluate(self.oCanvas)
                lPrint=True
        return lPrint
                
    def stampaFooterGruppi(self, fineReport=False):
        """
        Il metodo, ciclando su tutti i gruppi presenti sul report, provvede a stampare i
        piedi dei gruppi per i quali si è in attesa di stamparne l'intestazione, cioè i 
        piedi di quei gruppi per cui è True il metodo isHeaderWaitingFooter().
        La stampa procede in senso inverso rispetto al livello di gruppo, cioè procede
        dal gruppo più interno a quello più esterno.
        Restituisce True o False a seconda che la stampa dei piedi gruppo abbia innescato
        o meno il salto pagina.
        """
        lNewPage=False
        dbt = self.oCanvas.recordSource
        lg=self.lGroup.keys()
        lg.sort()
        lg.reverse()
        i=0
        while i<len(lg):
            e=lg[i]
            if self.lGroup[e].isHeaderWaitingFooter()==True:
                if self.lGroup[e].isHeaderToPrint()==True or fineReport:
                    att=self.oCanvas.get_row()-self.lGroup[e].oGroupFooter.get_altezza()
                    inizioPageFootner=self.oCanvas.get_bottomMargin()+self.oPageFooter.get_altezza()
                    #self.oCanvas.setFillColorRGB(1,0,1)
                    #self.oCanvas.setFont("Helvetica", 3)        
                    #self.oCanvas.drawString(100,self.oCanvas.get_row(),str(att)+','+str(inizioPageFootner))
                    if att < inizioPageFootner:
                        self.ejectPage()
                        self.stampaTestata(False)
                        i=i-1
                        lNewPage=True
                    else:
                        self.oCanvas.incrementaVariabili(['Group', self.lGroup[e].name])
                        self.oCanvas.set_row(self.lGroup[e].oGroupFooter.output(self.oCanvas))
            i=i+1        
        return lNewPage
        
    def rotturaGruppo(self):
        """
        Il metodo restituisce True o False a seconda che si sia in presenza o meno 
        di una rottura di gruppo.
        Qualora sia stata accertata la presenza di una rottura, il metodo provvede
        a marchiare da stampare (isHeaderToPrint(True)) le intestazione del gruppo
        soggetto alla rottura e di quelli successivi(gruppi di livello più interno).
        """
        lPrintGruppi=False
        lg=self.lGroup.keys()
        lg.sort()
        for e in lg:
            if lPrintGruppi==True:
                self.lGroup[e].check_rottura(self.oCanvas)                    
                self.lGroup[e].oGroupHeader.needResetVariable=True
                self.lGroup[e].isHeaderToPrint(True)
            elif self.lGroup[e].check_rottura(self.oCanvas) == True:
                self.lGroup[e].oGroupHeader.needResetVariable=True
                self.lGroup[e].isHeaderToPrint(True)
                lPrintGruppi=True
        return lPrintGruppi
        
    def set_canvas(self):
        """
        Il metodo si fa carico di impostare il formato di pagina conseguentemente all'orientamento
        specificato.
        """
        if self.oPageFormat.orientamento=="landscape":    
            x=landscape((self.oPageFormat.larghezza,self.oPageFormat.altezza))
        else:
            x=portrait((self.oPageFormat.larghezza,self.oPageFormat.altezza))
        return astraCanvas(self.oPageFormat.nomepdf,pagesize=x)
    
    def ejectPage(self):
        """
        Il metodo si fa carico di stampare il piè di pagina, concludere la produzione della corrente pagina 
        e quindi impostare i vari attributi in modo tale che il prossimo ciclo di stampa provvederà, tramite il
        metodo stampaTestata(), a produrre la stampa di tutti gli elementi richiesti su una nuova pagina
        ( pageHeader, groupHeader, columnHeader, ecc).
        """
        self.oCanvas.set_row(self.oPageFooter.output(self.oCanvas))
        self.oCanvas.ejectPage()
        self.oBackGround.isToPrint(True)
        self.oPageHeader.isToPrint(True)
        self.oColumnHeader.daStampare=True
        self.oCanvas.set_row(self.oCanvas.get_bottomMargin()+
                             self.oCanvas.get_altezzaReale())
        self.stampaGroupHeaderOnNewPage()

    def stampaGroupHeaderOnNewPage(self):
        """
        Il metodo si fa carico di ispezionare i vari gruppi presenti nel report
        al fine di individuare quelli per i quali è richiesta comunque la stampa
        dell'intestazione all'atto della stampa di una nuova pagina. Via via che tali gruppi
        vengono individuati, provvede a settare a True l'attributo B{isHeaderToPrint} che, 
        ispezionato ad ogni ciclo di stampa, stabilisce se l'intestazione del gruppo debba essere stampata o meno.
        """
        lg=self.lGroup.keys()
        lg.sort()
        for e in lg:
            if self.lGroup[e].isReprintHeaderOnEachPage=="true":
                self.lGroup[e].isHeaderToPrint(True)
                self.lGroup[e].isHeaderWaitingFooter(False)
        
                
    def loadGroup(self, dDefinizione_report, oCanvas):
        """
        Il metodo si fa carico di caricare una lista con gli oggetti L{group}
        corrispondenti ai gruppi presenti nel report.
        """
        lGruppi={}
        oGroup=None
        l= [e for e in dDefinizione_report.keys() if e[:5]=="group"]
        for e in l:
            lGruppi[e]=group(self.oReport.get_ReportStru()[e], oCanvas)
        lg=lGruppi.keys()
        lg.sort()
        self.lGroup={}
        for e in lg:
            self.lGroup[e]=lGruppi[e]
    
    
    def loadUserVariable(self, dDefinizione_report):
        """
        Il metodo si fa carico di caricare un dizionario  con gli oggetti L{userVariable}
        corrispondenti alle vartiabili utente presenti nel report. La chiave del dizionario è
        data dal nome della variabile.
        """
        self.oCanvas.userVariableList={}
        Variable.variableList={}
        oVariable=None
        l= [e for e in dDefinizione_report.keys() if e[:8]=="variable"]
        for e in l:
            v=userVariable(self.oReport.get_ReportStru()[e])
            #self.__dict__[v.set_name()] = v 
            self.oCanvas.userVariableList[v.set_name()]=v
            #Variable.variableList[v.set_name()]=v
        v=PAGE_NUMBER()
        self.oCanvas.userVariableList[v.set_name()]=v

    def loadUserParameter(self, dDefinizione_report):
        """
        Il metodo si fa carico di caricare un dizionario  con gli oggetti L{userVariable}
        corrispondenti alle vartiabili utente presenti nel report. La chiave del dizionario è
        data dal nome della variabile.
        """
        Variable.parameterList={}
        oParameter=None
        l= [e for e in dDefinizione_report.keys() if e[:9]=="parameter"]
        for e in l:
            p=userParameter(self.oReport.get_ReportStru()[e])
            Variable.parameterList[p.set_name()]=p

def usage():
    print __doc__
