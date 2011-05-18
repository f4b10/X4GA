#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         report/read.py
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

"""
Gestione Report
Uso: python rpt.py [opzioni] [source]

Opzioni:
  -r ...                  file XML che contiene la definizione del report
  -h, --help              visualizza questo help
  -d                      visualizza informazioni di debug

Examples:
  rpt.py         
  rpt.py -d-r xml_test2.xml
  rpt.py "<xref id='paragraph'/>"  
  rpt.py template.xml
  
"""

from xml.dom import minidom
from types import *
from string import *

#import random
import report.tool
import sys
import getopt

_debug = 0

class iReportDef:
    """La classe si fa carico di acquisire la struttura del report dalla sua definizione in formato XML.
    
    Una volta inizializzata, il I{dizionario} B{self.structure} riproduce la definizione del report.
    
    I vari nodi presenti nel file B{xml} sono rappresentati a loro volta da dizionari ottenendo un struttura del tipo::
        
         { propr1:"A",
           propr2:"B",
           NODO1:{propr1:"C",
                  propr2:"D",
                  propr3:"E",
                  NODO11:{propr1:"C",
                          propr2:"D",
                          propr3:"E"},
                  NODO12:{propr1:"F",
                          propr2:"G",
                          propr3:"H"},
                          NODO121:{propr1:"F",
                                   propr2:"G",
                                   propr3:"H"},
                 ]
           NODO2:{propr1:"C",
                  propr2:"D",
                  NODO21:{propr1:"C"},
                  NODO22:{propr1:"F",
                          propr2:"G",
                          NODO221:{propr1:"F",
                                   propr2:"G",
                                   propr3:"H"},
                 }
           .  
           .
           .
            NODOn:{........}
         }
         
         I nodi presenti allo stesso livello che presentano identico nome sono
         riportati all'interno del dizionario con un nome univoco ottenuto
         aggiungendo al nome stesso un contatore così se in xml si ha:
             
                     <group ..............>
                         <.............>
                     </group>
                     <group ..............>
                         <.............>
                     </group>
                     <group ..............>
                         <.............>
                     </group>

         allora il dizionario sara':

         {......., "group":{....}, "group1":{....}, "

    @cVar _internalStru: Struttura interna
    """
    _internalStru = None
    structure=None

    def __init__(self, nameXmlFile, source=None):
        if _debug==1:
            print nameXmlFile
        self._set_internalStru(nameXmlFile)
        self._set_Stru()
        if _debug==1:
            self.printStru(self.structure)


    def printStru(self, dictNode, tab=""):
        keys=dictNode.keys()
        keys.sort()
        for k in keys:
            if type(dictNode[k])<>DictType:
                print tab+k+ " = " ,
                print dictNode[k]
        for k in keys:
            if type(dictNode[k])==DictType:
                print tab+"<"+k+ ">|"  
                self.printStru(dictNode[k], tab+"|".rjust(len(k)+3))
                
                
    def _load(self, nameXmlFile):
        """load XML input source, return parsed XML document
        - a URL of a remote XML file ("http://diveintopython.org/kant.xml")
        - a filename of a local XML file ("~/diveintopython/common/py/kant.xml")
        - standard input ("-")
        - the actual XML document, as a string
        """
        sock = report.tool.openAnything(nameXmlFile)
        xmldoc = minidom.parse(sock)
        sock.close()
        return xmldoc

    def _set_internalStru(self, nameXmlFile):
        self._internalStru = self._load(nameXmlFile)
   

    def _set_Stru(self):
        which=None
        attributi={}
        mainNode =[e for e in self._internalStru.childNodes if e.nodeType == e.ELEMENT_NODE][0]
        which=mainNode.tagName
        for a in mainNode.attributes.keys():
            if e.getAttribute(a).isdigit():
                attributi[a.encode()]=float(e.getAttribute(a))
            else:
                attributi[a.encode()]=e.getAttribute(a).encode()
        self.structure=dict(attributi.items()+ self.explore_iReport(mainNode, "").items())
        

    def explore_iReport(self, node, tab):
        dizionario={}
        index=0
        lConta=False
        
        if node.tagName=="band":
            lConta=True
        
        
        for subNode in node.childNodes:
            attributi={}

            if (subNode.nodeType == subNode.ELEMENT_NODE):
                if lConta:
                    index=index+1
                    which = zfill(str(index),3)+"_"+subNode.tagName
                else:
                    which = subNode.tagName
                if _debug==1:
                    print tab+which
                for a in subNode.attributes.keys():
                    if subNode.getAttribute(a).isdigit():
                        attributi[a.encode()]=float(subNode.getAttribute(a))
                    else:
                        attributi[a.encode()]=subNode.getAttribute(a).encode()
                    if _debug==1:
                        print tab+a+" = ",
                        print subNode.getAttribute(a)
                i=0
                new_which = which    
                while dizionario.has_key(new_which):
                    i=i+1
                    new_which=which+str(i)
                dizionario[new_which]=dict(attributi.items()+ self.explore_iReport(subNode, tab+"  ").items())
            elif (subNode.nodeType == subNode.COMMENT_NODE):
                dizionario["commento"]=subnode.data
            elif (subNode.nodeType == subNode.DOCUMENT_TYPE_NODE):
                pass
            elif (subNode.nodeType == subNode.TEXT_NODE):
                pass
            elif (subNode.nodeType == subNode.CDATA_SECTION_NODE):
                dizionario["DATA"]=subNode.data
        return dizionario
    

    def get_ReportStru(self):
        return self.structure
    
    def get_PageSetup(self):
        return self._get_property(self.structure)
    
    def _get_property(self, dictionary):
        """
        Il metodo si fa carico di estrarre dal dizionario ricevuto come input
        i soli elementi che non siano a loro volta dizionari (foglie del ramo).
        Pertanto, nell'ottica dei file xml, il metodo restituisce di fatto un
        dizionario di tutte le proprietà di un particolare nodo
        """
        dic={}
        for i in [e for e in dictionary if type(dictionary[e]) <> DictType]:
            dic=dict(dic.items()+[(i,dictionary[i])])
        return dic
        
    



def usage():
    print __doc__
    

def main(argv):
    report_definition = None
    try:
        opts, args = getopt.getopt(argv, "hr:d", ["help", "report_definition="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt == '-d':
            global _debug
            _debug = 1
        elif opt in ("-r"):
            report_definition = arg
            
    if report_definition==None:
        usage()
        sys.exit(2)
    

    source = "".join(args)
    k = iReportDef(report_definition, source)

if __name__ == "__main__":
    main(sys.argv[1:])
