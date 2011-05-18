#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         report/variables.py
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

import Env
import locale
from string import *


TYPE_NUMERIC =0
TYPE_BOOL =1
TYPE_SMALLINT=2
TYPE_INTEGER=3
TYPE_FLOAT=4
TYPE_DOUBLE=5
TYPE_TIMESTAMP=7
TYPE_BIGINT=8
TYPE_MEDIUMINT=9
TYPE_DATE=10
TYPE_TIME=11
TYPE_DATETIME=12
TYPE_YEAR=13
TYPE_TEXT=252
TYPE_VARCHAR=253
TYPE_CHAR=254


def isPrompting():
    prompt=False
    for p in Variable.parameterList.keys():
        x=Variable.parameterList[p]
        if Variable.parameterList[p].set_isForPrompting() == "true"  and prompt == False:
            prompt=True
    #print "Promp:",
    #print prompt
    return prompt



class Variable:
    VariableList=None
    parameterList=None
    

from datetime import *


class adate(date):

  #def __str__(self):
    #return self.strftime("%x")
  pass

class adatetime(datetime):

  def __str__(self):
    return self.strftime("%x %X")
    
    

class Expression:
    listaCampi=None
    listaVariabili=None
    textFieldExpression=None

    def __init__(self, espressione):
        self.textFieldExpression=espressione
        self.listaCampi=self.set_listaCampi()
        self.listaVariabili=self.set_listaVariabili()
    
    def estraiCampi(self,s, sep):
        l=[r for r in split(s,sep) if len(r)>0 and r[0]=="{"]
        for index in range(0,len(l)):
            l[index]=l[index][1:find(l[index],"}")]
        return l
    
    def set_listaCampi(self):
        return self.estraiCampi(self.textFieldExpression, "$F") 
        
    def set_listaVariabili(self):
        return self.estraiCampi(self.textFieldExpression, "$V") 


    def evaluate(self, oCanvas, object=None):
        exp=self.textFieldExpression
        for v in oCanvas.userVariableList:
            exp=replace(exp,"$V{" +v + "}", "oCanvas.userVariableList['"+v+"'].valore")
        exp=replace(exp, "$F{", "")
        exp=replace(exp, "RS.", "oCanvas.recordSource.")
        exp=replace(exp, "}", "")
        try:
            val=eval(exp, globals(), locals())
            if val is None: val = ""
            if type(val) in (str, unicode):
                for vold, vnew in (("&", "&amp;"),\
                                   ("<", "&lt;"),\
                                   (">", "&gt;")):
                    if vold in val:
                        val = val.replace(vold, vnew)
        except Exception, e:
            val=self.textFieldExpression
        return val
            
            
    def value2string(self, express, valore, tipo):
        ret=None
        if tipo == TYPE_VARCHAR or tipo == TYPE_CHAR:
            if valore <> None:
                ret = chr(34)+replace(str(valore),chr(34),"'")+chr(34)
        elif tipo == TYPE_DOUBLE or tipo == TYPE_FLOAT or tipo == TYPE_INTEGER or tipo == TYPE_NUMERIC or tipo==TYPE_YEAR:
            if valore <> None:
                ret = str(valore)
        elif tipo == TYPE_DATE:
            if valore <> None:
                ret= \
                    "adate("+ \
                    str(int(str(valore)[:4]))+ \
                    ","+ \
                    str(int(str(valore)[5:7]))+ \
                    ","+ \
                    str(int(str(valore)[8:10]))+ \
                    ")"+ \
                    ""
        elif tipo == TYPE_TIME :
            #time( hour=0, minute=0, second=0, microsecond=0, tzinfo=None) 
            if valore<>None:
                ret= \
                    "time("+ \
                    str(int(str(valore)[:2]))+ \
                    ","+ \
                    str(int(str(valore)[3:5]))+ \
                    ","+ \
                    str(int(str(valore)[6:8]))+ \
                    ","+ \
                    str(int(str(valore)[9:11]))+ \
                    ")"+ \
                    ""
        elif tipo == TYPE_DATETIME or tipo== TYPE_TIMESTAMP:
            if valore<>None:
                ret= \
                    "adatetime("+ \
                    str(int(str(valore)[:4]))+ \
                    ","+ \
                    str(int(str(valore)[5:7]))+ \
                    ","+ \
                    str(int(str(valore)[8:10]))+ \
                    ","+ \
                    str(int(str(valore)[11:13]))+ \
                    ","+ \
                    str(int(str(valore)[14:16]))+ \
                    ","+ \
                    str(int(str(valore)[17:19]))+ \
                    ","+ \
                    str(int(str(valore)[20:22]))+ \
                    ")"+ \
                    ""
        else:
            ret = chr(34)+express+chr(34)
        return ret


    def searchVariable(self, name):
        try:
            return Variable.variableList[name]
        except:
            return ""


class userObject:
    name=None
    java_type=None
    python_type=None
    valore=None
    
    def set_name(self, value=None):
        if value<>None:
            self.name=value
        return self.name
    
    def set_type(self, value=None):
        if value<>None:
            self.java_type=value
            self.java2python()
        return self.java_type


    def java2python(self):
        type=""
        if find(self.java_type, "String")>=0:
            type=TYPE_VARCHAR
        elif find(self.java_type, "Date")>=0:
            type=TYPE_DATE
        elif find(self.java_type, "TimeStamp")>=0:
            type=TYPE_TIMESTAMP
        elif find(self.java_type, "Time")>=0:
            type=TYPE_TIME
        elif find(self.java_type, "Double")>=0:
            type=TYPE_DOUBLE
        elif find(self.java_type, "Float")>=0:
            type=TYPE_FLOAT
        elif find(self.java_type, "Integer")>=0:
            type=TYPE_INTEGER
        elif find(self.java_type, "Long")>=0:
            type=TYPE_BIGINT
        elif find(self.java_type, "Short")>=0:
            type=TYPE_SMALLINT
        self.python_type=type    


class userParameter(userObject):
    description=None
    defaultValue=None
    isForPrompting=None
    
    def __init__(self, definizione):
        self.set_name(definizione["name"])
        self.set_type(definizione["class"])
        self.set_description(definizione["parameterDescription"])
        self.set_defaultValue(definizione["defaultValueExpression"])
        self.set_isForPrompting(definizione["isForPrompting"])

    def set_defaultValue(self, d=None):
        if d<>None:
            self.defaultValue=Expression(d["DATA"].encode())
        return self.defaultValue

    def set_description(self, d=None):
        if d<>None:
            self.description=d["DATA"].encode()
        return self.description

    def set_isForPrompting(self, value=None):
        if value<>None:
            self.isForPrompting=value
        return self.isForPrompting
    
    
    

class userVariable(userObject):
    
    incrementType=None
    incrementGroup=None
    calculation=None
    initialValueExpression=None
    oResetExpression=None
    resetType=None
    resetGroup=None
    oExpression=None
    variableExpression=None
    
    def __init__(self, definizione, built_in=False):
        
        #self.incrementLevel="Detail"
        self.incrementType="Detail"
        self.set_calculation(definizione["calculation"])
        self.set_type(definizione["class"])
        self.set_name(definizione["name"])

        try:
            self.set_incrementType(definizione["incrementType"])
            try:
                self.set_incrementGroup(definizione["incrementGroup"])
            except:
                pass
        except:
            pass
        
        self.set_resetType(definizione["resetType"])
        try:
            self.set_resetGroup(definizione["resetGroup"])
        except:
            pass
        try:
            self.set_resetExpression(definizione["initialValueExpression"])
            self.set_Expression(definizione["variableExpression"])
        except:
            pass
    

    def set_incrementType(self, value=None):
        if value<>None:
            self.incrementType=value
        return self.incrementType
        
    def set_incrementGroup(self, value=None):
        if value<>None:
            self.incrementGroup=value
        return self.incrementGroup
        
        #if d<>None:
            #try:
                #if d["incrementType"].encode()=="Group":
                    #self.incrementLevel=d["incrementGroup"].encode()
                #else:
                    #self.incrementLevel=d["incrementType"].encode()
                    #if self.incrementLevel=="None":
                        #self.incrementLevel="Detail"
            #except:
                #self.incrementLevel="Detail"
                
        #return self.incrementLevel



    def set_calculation(self, value=None):
        if value<>None:
            self.calculation=value
        return self.calculation
    
    def set_resetType(self, value=None):
        if value<>None:
            self.resetType=value
        return self.resetType
    
    def set_resetGroup(self, value=None):
        if value<>None:
            self.resetGroup=value
        return self.resetGroup
    
    def set_resetExpression(self, d=None):
        if d<>None:
            self.oResetExpression=Expression(d["DATA"].encode())
        return self.oResetExpression
    
    def set_Expression(self, d=None):
        if d<>None:
            self.oExpression=Expression(d["DATA"].encode())
        return self.oExpression

    def reset(self, oCanvas):
        import datetime
        #print "eval("+ self.oResetExpression.textFieldExpression + ")"
        macro = self.oResetExpression.textFieldExpression
        if len(macro)>0:
            exp = Expression(macro)
            val = exp.evaluate(oCanvas)
            self.valore = val
        
    def incrementa(self, oCanvas):
        import datetime
        #print "eval("+ self.oResetExpression.textFieldExpression + ")"
        macro = self.oExpression.textFieldExpression
        if len(macro)>0:
            exp = Expression(macro)
            val = exp.evaluate(oCanvas)
            self.valore = val

class PAGE_NUMBER(userVariable):
    def __init__(self):
        self.incrementType="Page"
        self.set_calculation("$V{PAGE_NUMBER}+1")
        self.set_type("DOUBLE")
        self.set_name("PAGE_NUMBER")
        self.set_resetType("Report")
        try:
            self.set_resetGroup("")
        except:
            pass
        try:
            self.set_resetExpression({"DATA": "0"})
            self.set_Expression({"DATA": "$V{PAGE_NUMBER}+1"})
        except:
            pass
