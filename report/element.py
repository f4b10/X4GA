#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/element.py
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

from report.read import iReportDef
from report.variables import *
import report.barcodes as rbc

from types import *

from reportlab.pdfgen import canvas
from reportlab import rl_config
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.colors import *
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import Paragraph as BaseParagraph
from reportlab.platypus.paragraph import _handleBulletWidth, ParaLines, _parser, _sameFrag, FragLine
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.styles import ParagraphStyle, PropertySet

from string import *

import os.path
import Env

import report


_debug =0

def _myGetFragWords(frags):
    ''' given a Parafrag list return a list of fragwords
        [[size, (f00,w00), ..., (f0n,w0n)],....,[size, (fm0,wm0), ..., (f0n,wmn)]]
        each pair f,w represents a style and some string
        each sublist represents a word
    '''
    whitespace = ' \t\r\v\f'
    R = []
    W = []
    n = 0
    for f in frags:
        text = f.text
        #del f.text # we can't do this until we sort out splitting
                    # of paragraphs
        if text!='':
            S = split(text, ' ')
            if S==[]: S = ['']
            if W!=[] and text[0] in whitespace:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0

            for w in S[:-1]:
                W.append((f,w))
                n = n + stringWidth(w, f.fontName, f.fontSize)
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0

            w = S[-1]
            W.append((f,w))
            n = n + stringWidth(w, f.fontName, f.fontSize)
            if text[-1] in whitespace:
                W.insert(0,n)
                R.append(W)
                W = []
                n = 0
        elif hasattr(f,'cbDefn'):
            W.append((f,''))

    if W!=[]:
        W.insert(0,n)
        R.append(W)

    return R

    
def AdjustLineFeeds(text):
    text = text.replace('\n', ' \n')
    return text

class Paragraph(BaseParagraph):
    def _setup(self, text, style, bulletText, frags, cleaner):
        if frags is None:
            #text = cleaner(text)
            text = AdjustLineFeeds(text)
            _parser.caseSensitive = self.caseSensitive
            style, frags, bulletTextFrags = _parser.parse(text,style)
            if frags is None:
                raise "xml parser error (%s) in paragraph beginning\n'%s'"\
                    % (_parser.errors[0], str(text[:min(30,len(text))]))
            if bulletTextFrags: bulletText = bulletTextFrags

        #AR hack
        self.text = text
        self.frags = frags
        self.style = style
        self.bulletText = bulletText
        self.debug = 0  #turn this on to see a pretty one with all the margins etc.

    def breakLines(self, width):
        """
        Returns a broken line structure. There are two cases

        A) For the simple case of a single formatting input fragment the output is
            A fragment specifier with
                kind = 0
                fontName, fontSize, leading, textColor
                lines=  A list of lines
                        Each line has two items.
                        1) unused width in points
                        2) word list

        B) When there is more than one input formatting fragment the out put is
            A fragment specifier with
                kind = 1
                lines=  A list of fragments each having fields
                            extraspace (needed for justified)
                            fontSize
                            words=word list
                                each word is itself a fragment with
                                various settings

        This structure can be used to easily draw paragraphs with the various alignments.
        You can supply either a single width or a list of widths; the latter will have its
        last item repeated until necessary. A 2-element list is useful when there is a
        different first line indent; a longer list could be created to facilitate custom wraps
        around irregular objects."""

        if type(width) <> ListType: maxWidths = [width]
        else: maxWidths = width
        lines = []
        lineno = 0
        style = self.style
        fFontSize = float(style.fontSize)

        #for bullets, work out width and ensure we wrap the right amount onto line one
        _handleBulletWidth(self.bulletText,style,maxWidths)

        maxWidth = maxWidths[0]

        self.height = 0
        frags = self.frags
        nFrags= len(frags)
        if nFrags==1:
            f = frags[0]
            fontSize = f.fontSize
            fontName = f.fontName
            words = hasattr(f,'text') and split(f.text, ' ') or f.words
            spaceWidth = stringWidth(' ', fontName, fontSize)
            cLine = []
            currentWidth = - spaceWidth   # hack to get around extra space for word 1
            for word in words:
                wordWidth = stringWidth(word, fontName, fontSize)
                newWidth = currentWidth + spaceWidth + wordWidth
                if newWidth>maxWidth and len(cLine)>0 or word.startswith('\n'):
                    if currentWidth>self.width: self.width = currentWidth
                    #end of line
                    lines.append((maxWidth - currentWidth, cLine))
                    if word.startswith('\n'):
                        word = word[1:]
                    cLine = [word]
                    currentWidth = wordWidth
                    lineno = lineno + 1
                    try:
                        maxWidth = maxWidths[lineno]
                    except IndexError:
                        maxWidth = maxWidths[-1]  # use the last one
                else:
                    # fit one more on this line
                    cLine.append(word)
                    currentWidth = newWidth

            #deal with any leftovers on the final line
            if cLine!=[]:
                if currentWidth>self.width: self.width = currentWidth
                lines.append((maxWidth - currentWidth, cLine))

            return f.clone(kind=0, lines=lines)
        elif nFrags<=0:
            return ParaLines(kind=0, fontSize=style.fontSize, fontName=style.fontName,
                            textColor=style.textColor, lines=[])
        else:
            if hasattr(self,'blPara'):
                #NB this is an utter hack that awaits the proper information
                #preserving splitting algorithm
                return self.blPara
            n = 0
            nSp = 0
            for w in _myGetFragWords(frags):
                spaceWidth = stringWidth(' ',w[-1][0].fontName, w[-1][0].fontSize)

                if n==0:
                    currentWidth = -spaceWidth   # hack to get around extra space for word 1
                    words = []
                    maxSize = 0

                wordWidth = w[0]
                #w[1][1] = w[1][1].replace(' \n', '\n')
                f = w[1][0]
                if wordWidth>0:
                    newWidth = currentWidth + spaceWidth + wordWidth
                else:
                    newWidth = currentWidth
                if (newWidth<=maxWidth or n==0) and not '\n' in w[1][1]:
                    # fit one more on this line
                    n = n + 1
                    maxSize = max(maxSize,f.fontSize)
                    nText = w[1][1]
                    if words==[]:
                        g = f.clone()
                        words = [g]
                        g.text = nText
                    elif not _sameFrag(g,f):
                        #if currentWidth>0 and ((nText!='' and nText[0]!=' ') or hasattr(f,'cbDefn')):
                        if currentWidth>0 and (nText!='' or hasattr(f,'cbDefn')):
                            if hasattr(g,'cbDefn'):
                                i = len(words)-1
                                while hasattr(words[i],'cbDefn'): i = i-1
                                words[i].text = words[i].text + ' '
                            else:
                                g.text = g.text + ' '
                            nSp = nSp + 1
                        g = f.clone()
                        words.append(g)
                        g.text = nText
                    else:
                        if nText!='':# and nText[0]!=' ':
                            g.text = g.text + ' ' + nText

                    for i in w[2:]:
                        g = i[0].clone()
                        g.text=i[1]
                        words.append(g)
                        maxSize = max(maxSize,g.fontSize)

                    currentWidth = newWidth
                else:
                    if currentWidth>self.width: self.width = currentWidth
                    #end of line
                    lines.append(FragLine(extraSpace=(maxWidth - currentWidth),wordCount=n,
                                        words=words, fontSize=maxSize))

                    #start new line
                    lineno = lineno + 1
                    try:
                        maxWidth = maxWidths[lineno]
                    except IndexError:
                        maxWidth = maxWidths[-1]  # use the last one
                    currentWidth = wordWidth
                    n = 1
                    maxSize = f.fontSize
                    g = f.clone()
                    words = [g]
                    g.text = w[1][1]
                    
                    for i in w[2:]:
                        g = i[0].clone()
                        g.text=i[1]
                        words.append(g)
                        maxSize = max(maxSize,g.fontSize)

            #deal with any leftovers on the final line
            if words<>[]:
                if currentWidth>self.width: self.width = currentWidth
                lines.append(ParaLines(extraSpace=(maxWidth - currentWidth),wordCount=n,
                                    words=words, fontSize=maxSize))
            return ParaLines(kind=1, lines=lines)

        return lines

    
###
# Code generated by ObjectDomain R3 using Python script "pythonCodeGen 1.0"
#

class imageExpression:
    
    imageName=None
    
    def __init__(self,definizione):
        self.imageName=self.set_imageName(definizione)
        
    def set_imageName(self, d):
        x=d["DATA"].encode()
        if x[0]== x[len(x)-1] and x[0] in ['"', "'"]:
            x=x[1:len(x)-1]
        return x
    
    def get_imageName(self):
        return self.imageName
    


class rpt_color:
    r=None
    g=None
    b=None
    def __init__(self, s):
        self.r=float(int(s[1:3],16))/255
        self.g=float(int(s[3:5],16))/255
        self.b=float(int(s[5:7],16))/255
    
    def get_r(self):
        return self.r
    def get_g(self):
        return self.g
    def get_b(self):
        return self.b
    




class elemento_Visuale:
    
    definition=None

    key=None
    foreground=None
    background=None
    trasparent=None
    topFromBand=None
    leftFromBand=None
    topFromPage=None
    leftFromPage=None
    height=None
    extendedheight=None
    width=None
    position_type=None
    stretch_type=None
    isPrintRepeatedValues=None
    isRemoveLineWhenBlank=None
    isPrintWhenDetailOverflows=None
    printConditionExpression=None
    isStretchWithOverflow=None
    isToPrint=None
    

    
    def __init__(self,definizione):
        self.isStretchWithOverflow=False
        self.definition=definizione["reportElement"]
        self.set_key(getFromDict(self.definition, "key", None))

        self.set_foreground(getFromDict(self.definition,"forecolor","#000000"))
        self.set_background(getFromDict(self.definition,"backcolor","#FFFFFF"))
        self.set_position_type(getFromDict(self.definition,"positionType","FixRelativeToTop"))
        self.set_stretch_type(getFromDict(self.definition,"stretchType","NoStretch"))
        self.set_isStretchWithOverflow(getFromDict(definizione, "isStretchWithOverflow", "false"))
        self.set_isPrintRepeatedValues(getFromDict(self.definition,"isPrintRepeatedValues","true"))
        self.set_isRemoveLineWhenBlank(getFromDict(self.definition,"isRemoveLineWhenBlank","false"))
        self.set_isPrintWhenDetailOverflows(getFromDict(self.definition,"isPrintWhenDetailOverflows","false"))
        self.set_trasparent(getFromDict(self.definition,"mode","Opaque"))
        self.set_topFromBand(self.definition["y"])
        self.set_leftFromBand(self.definition["x"])
        self.set_height(self.definition["height"])
        self.set_extendedheight(self.definition["height"])
        self.set_width(self.definition["width"])
        self.set_printCondition()
    
    def set_printCondition(self):
        try:
            self.printConditionExpression=self.definition["printWhenExpression"]["DATA"]
        except:
            self.printConditionExpression=""
    
    def set_foreground(self,color=None):
        """
        Provvede a settare l'attributo foreground. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di
        foreground.
        """
        if color<>None:
            self.foreground=rpt_color(color)
        return self.foreground
    
    def set_background(self,color=None):
        """
        Provvede a settare l'attributo background. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di
        background.
        """
        if color<>None:
            self.background=rpt_color(color)
        return self.background
    
    def set_topFromBand(self,y0=None):
        """
        Provvede a settare l'attributo top. Nel caso venga omesso il parametro,
        il metodo si limita a restituire il valore corrente di top.
        """
        if y0<>None:
            self.topFromBand=y0
        return self.topFromBand

    def set_leftFromBand(self,x0=None):
        """
        Provvede a settare l'attributo left. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di left.
        """
        if x0<>None:
            self.leftFromBand=x0
        return self.leftFromBand

    def set_trasparent(self,lSet=None):
        """
        Provvede a settare l'attributo trasparent. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di
        trasparent.
        """
        if lSet<>None:
            if lSet=="Opaque":
                self.trasparent=False
            else:
                self.trasparent=True
        return self.trasparent
    
    def set_height(self,dy=None):
        if dy == 1:
            dy = 0
        if dy<>None:
            self.height=dy
        return self.height
    
    def set_extendedheight(self,dy=None):
        if dy<>None:
            self.extendedheight=dy
        return self.extendedheight

    def set_width(self,dx=None):
        """
        Provvede a settare l'attributo width. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di width.
        """
        if dx<>None:
            self.width=dx
        return self.width
    
    def set_position_type(self,nType=None):
        """
        Provvede a settare l'attributo set_position_type. Nel caso venga omesso
        il parametro, il metodo si limita a restituire il valore corrente di
        set_position_type.
        """
        if nType<>None:
            self.position_type=nType
        return self.position_type
    
    def set_isPrintWhenDetailOverflows(self,lSet=None):
        """
        Provvede a settare l'attributo when_detail_overflow. Nel caso venga
        omesso il parametro, il metodo si limita a restituire il valore
        corrente di when_detail_overflow.
        """
        if lSet<>None:
            if lSet=="true":
                self.isPrintWhenDetailOverflows=True
            else:
                self.isPrintWhenDetailOverflows=False
        return self.isPrintWhenDetailOverflows
    
    def set_isPrintRepeatedValues(self,lSet=None):
        """
        Provvede a settare l'attributo when_repeated_value. Nel caso venga
        omesso il parametro, il metodo si limita a restituire il valore
        corrente di when_repeated_value.
        """
        if lSet<>None:
            if lSet=="true":
                self.isPrintRepeatedValues=True
            else:
                self.isPrintRepeatedValues=False
        return self.isPrintRepeatedValues
    
    def set_isRemoveLineWhenBlank(self,lSet=None):
        """
        Provvede a settare l'attributo remove_line_when_blank. Nel caso venga
        omesso il parametro, il metodo si limita a restituire il valore
        corrente di remove_line_when_blank.
        """
        if lSet<>None:
            if lSet=="true":
                self.isRemoveLineWhenBlank=True
            else:
                self.isRemoveLineWhenBlank=False
        return self.isRemoveLineWhenBlank
    
    def set_key(self,cName=None):
        """
        Provvede a settare l'attributo key. Nel caso venga omesso il parametro,
        il metodo si limita a restituire il valore corrente di key.
        """
        if cName<>None:
            self.key=cName
        return self.key
    
    def set_stretch_type(self,nType=None):
        """
        Provvede a settare l'attributo stretch_type. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di
        stretch_type.
        """
        if nType<>None:
            self.stretch_type=nType
        return self.stretch_type

    def set_isStretchWithOverflow(self, value=None):
        if value<>None:
            if value=="true":
                self.isStretchWithOverflow=True
            else:
                self.isStretchWithOverflow=False
        return self.isStretchWithOverflow

    def set_origine(self, oCanvas, y):
        #============ DA CORREGGERE =================================
        self.leftFromPage=oCanvas.get_leftMargin()+int(self.leftFromBand)
        self.topFromPage=y-self.height-int(self.topFromBand)
        
    def get_x0(self):
        return self.leftFromPage
    
    def get_y0(self):
        return self.topFromPage
    
    def format(self, oCanvas):
        pass
    
    def refresh(self):
        pass
    
    def set_attributiTesto(self):
        pass
   
    def set_isToPrint(self, oCanvas):
        self.isToPrint=True
        if len(self.printConditionExpression)>0:
            self.isToPrint=False
            xx=Expression(self.printConditionExpression)
            if xx.evaluate(oCanvas, self)==True:
                self.isToPrint=True

class elemento_Grafico(elemento_Visuale):
    pen = None
    style = None
    fill = None
    
    def __init__(self,definizione):
        elemento_Visuale.__init__(self, definizione)
        try:
            d = definizione['graphicElement']
        except KeyError:
            definizione['graphicElement'] = d = {}
        try:
            y = d["pen"]
        except KeyError:
            y = {"lineWidth":"1", "lineStyle":"Solid"}
            d["pen"] = y
            
        if type(y) is dict:
            styleTratto = d["pen"]
        else:
            # old iReport Version
            oldLineWidth = getFromDict(d, "pen", "Thin")
            if oldLineWidth=="Dotted":
                styleTratto={"lineWidth":"1", "lineStyle":"Dotted"}
            else:
                x={"None":"0", "Thin":"1", "1Point":"2", "2Point":"3", "4Point":"4"}
                styleTratto={"lineWidth":x[oldLineWidth], "lineStyle":"Solid"}
        self.set_pen(float(getFromDict(styleTratto,"lineWidth","1")))
        self.set_style(getFromDict(styleTratto,"lineStyle","Solid"))
        self.set_fill(getFromDict(d,"fill","false"))

    def set_pen(self,cType=None):
        """
        Provvede a settare l'attributo pen in termini di pixel. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di pen.
        """
        if cType<>None:
            self.pen=cType
        return self.pen
        
    def set_style(self,cType=None):
        """
        Provvede a settare l'attributo style. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di pen.
        """
        if cType<>None:
            self.style=cType
        return self.style
        
    def set_fill(self,lSet=None):
        """
        Provvede a settare l'attributo fill. Nel caso venga
        omesso il parametro, il metodo si limita a restituire il valore
        corrente di fill.
        """
        if lSet<>None:
            if lSet=="true":
                self.fill=True
            else:
                self.fill=False
        return self.fill
        
    def set_lineColor(self, oCanvas):
        if self.set_pen()==0 and self.set_trasparent()==False:
            oCanvas.setStrokeColorRGB(self.background.get_r(),
                                      self.background.get_g(),
                                      self.background.get_b())
            oCanvas.setFillColorRGB(self.background.get_r(),
                                    self.background.get_g(),
                                    self.background.get_b())
        elif self.set_pen()>0 and self.set_trasparent()==False:
            oCanvas.setStrokeColorRGB(self.foreground.get_r(),
                                      self.foreground.get_g(),
                                      self.foreground.get_b())
            oCanvas.setFillColorRGB(self.background.get_r(),
                                    self.background.get_g(),
                                    self.background.get_b())
        elif self.set_pen()>0 and self.set_trasparent()==True:
            oCanvas.setStrokeColorRGB(self.foreground.get_r(),
                                      self.foreground.get_g(),
                                      self.foreground.get_b())

        oCanvas.setLineWidth(self.set_pen())  
        
        x={"Solid":[1,0], "Dashed":[3,3], "Dotted":[1,1], "Double":[1,0]}
        
        oCanvas.setDash(x[self.style])
        
        
        

class linea(elemento_Grafico):
    direction=None
    
    def __init__(self,definizione):
        elemento_Grafico.__init__(self, definizione)
        self.set_direction(getFromDict(definizione, 'direction', 'TopDown'))
    
    
    def set_direction(self,cType=None):
        """
        Provvede a settare l'attributo pen. Nel caso venga omesso il
        parametro, il metodo si limita a restituire il valore corrente di
        pen.
        """
        if cType<>None:
            self.direction=cType
        return self.direction
    
    
    def output(self, oCanvas, y, pen=0):
        self.set_isToPrint(oCanvas)
        if not self.isToPrint:
            return
        self.set_origine(oCanvas,y)
        if self.set_pen()==0 and self.set_trasparent()==True:
            pass
        else:
            self.set_lineColor(oCanvas)
            if self.set_direction()=="BottomUp":    
                oCanvas.line(self.get_x0(),
                             self.get_y0(),
                             self.get_x0()+self.set_width(),
                             self.get_y0()+self.set_height())
            else:
                oCanvas.line(self.get_x0(),
                             self.get_y0()+self.set_height(),
                             self.get_x0()+self.set_width(),
                             self.get_y0())
            oCanvas.setLineWidth(0.25)   
            oCanvas.setDash(1,0)
            

            
 
class elisse(elemento_Grafico):
    
    def __init__(self,definizione):
        elemento_Grafico.__init__(self, definizione)

        
    def output(self, oCanvas, y):
        self.set_isToPrint(oCanvas)
        if not self.isToPrint:
            return
        fill=0
        if self.set_trasparent()==False:
            fill=1
            
        self.set_origine(oCanvas,y)
        if self.set_pen()==0 and self.set_trasparent()==True:
            pass
        else:
            self.set_lineColor(oCanvas)
            oCanvas.ellipse(self.get_x0(),
                         self.get_y0(),
                         self.get_x0()+self.set_width(),
                         self.get_y0()+self.set_height(),
                         stroke=1,
                         fill=fill)

        
 
class rettangolo(elisse):
    radius=None
     
    def __init__(self,definizione):
        elisse.__init__(self, definizione)
        try:
            self.set_radius(definizione["radius"])
        except:
            self.set_radius(0)
            
    def set_radius(self, r=None):
        if r<>None:
            self.radius=r
        return self.radius
    
    def output(self, oCanvas, y):
        self.set_isToPrint(oCanvas)
        if not self.isToPrint:
            return
         
        fill=0
        if self.set_trasparent()==False:
            fill=1
            
        self.set_origine(oCanvas,y)
        if self.set_pen()==0 and self.set_trasparent()==True:
            pass
        else:
            self.set_lineColor(oCanvas)
            oCanvas.roundRect(self.get_x0(),
                         self.get_y0(),
                         self.set_width(),
                         self.set_height(),
                         self.set_radius(),
                         fill=fill)


class immagine(rettangolo):
    oImageExpression=None
    scaleImage=None
    verticalAlignment=None
    horizontalAlignment=None
    evaluationTime=None
    evaluationGroup=None
    imageName=None
    #isUsingCache
     

    def __init__(self,definizione):
        rettangolo.__init__(self, definizione)
        self.set_imageName(definizione["imageExpression"])
        self.set_scaleImage(getFromDict(definizione, "scaleImage", "FillFrame"))
        self.set_verticalAlignment(getFromDict(definizione, "vAlign", "Top"))
        self.set_horizontalAlignment(getFromDict(definizione, "hAlign", "Left"))
        self.set_evaluationTime(getFromDict(definizione, "evaluationTime", "Now"))

    def set_imageName(self, d=None):
        if d<>None:
            x=d["DATA"].encode().rstrip()
            while x[0]== x[-1] and x[0] in ['"', "'"]:
                x=(x[1:-1]).rstrip()
            self.imageName=x
        return self.imageName


    
    def set_scaleImage(self, expr=None):
        if expr<>None:
            self.scaleImage = expr
        return self.scaleImage
    
    def set_verticalAlignment(self, expr=None):
        if expr<>None:
            self.verticalAlignment = expr
        return self.verticalAlignment
    
    def set_horizontalAlignment(self, expr=None):
        if expr<>None:
            self.horizontalAlignment = expr
        return self.horizontalAlignment

    def set_evaluationTime(self, expr=None):
        if expr<>None:
            self.evaluationTime = expr
        return self.evaluationTime
    
    def output(self, oCanvas, y):
        self.set_isToPrint(oCanvas)
        if not self.isToPrint:
            return
        self.set_origine(oCanvas,y)
        x0=self.get_x0()
        y0=self.get_y0()
        dx=self.set_width()
        dy=self.set_height()
        n=self.set_imageName()
        
        test = 'it.businesslogic.ireport.barcode.BcImage.getBarcodeImage('
        if n.startswith(test):
            #barcodes
            fgcol = self.set_foreground()
            bgcol = self.set_background()
            self.set_lineColor(oCanvas)
            n = n.replace(test, '')
            n = n[:-1]
            n = n.replace('false', 'False')
            n = n.replace('true',  'True')
            n = n.replace('null',  'None')
            e = Expression(n)
            n = e.evaluate(oCanvas)
            parms = [oCanvas, x0, y0, dx, dy, fgcol, bgcol] + list(n)
            img = rbc.getBarcodeImage(*parms)
            if img is not None:
                oCanvas.drawInlineImage(img,
                                        x0+self.set_pen(),
                                        y0+self.set_pen(),
                                        dx-(self.set_pen()*2),
                                        dy-(self.set_pen()*2))
            return
        
        elif n.startswith('$code39$'):
            #barcodes - vecchia gestione -- deprecated
            try:
                bw = 72*0.0100
                n = n[8:]
                kw = {'barHeight': dy,
                      'barWidth':  72*0.0100,
                      'checksum': 0}
                if '{' in n:
                    n, p = n.split('{')
                    try:
                        p = eval('{'+p.replace("RS.", "oCanvas.recordSource."))
                        for k in p:
                            kw[k] = p[k]
                    except:
                        pass
                e = Expression(n)
                c = e.evaluate(oCanvas)
                bc = Code39Barcode(c, **kw)
                self.set_foreground()
                self.set_background()
                self.set_lineColor(oCanvas)
                bc.drawOn(oCanvas, x0-oCanvas.get_leftMargin(), y0)
            except:
                pass
            return
            
        elif n.startswith('$code128$'):
            try:
                bw = 72*0.0100
                n = n[9:]
                kw = {'barHeight': dy,
                      'barWidth':  72*0.0100,
                      'checksum': 0}
                if '{' in n:
                    n, p = n.split('{')
                    try:
                        p = eval('{'+p.replace("RS.", "oCanvas.recordSource."))
                        for k in p:
                            kw[k] = p[k]
                    except:
                        pass
                e = Expression(n)
                c = e.evaluate(oCanvas)
                bc = Code128Barcode(c, **kw)#, ratio=2)#, xdim=1*units.inch)
                self.set_foreground()
                self.set_background()
                self.set_lineColor(oCanvas)
                bc.drawOn(oCanvas, x0-oCanvas.get_leftMargin(), y0)
            except:
                pass
            return
            
        elif n.startswith('$ean13$'):
            try:
                e = Expression(n[7:])
                c = e.evaluate(oCanvas)
                if len(c) == 13 and c[-1] == Ean13Barcode._checkdigit(c[:12]):
                    bc = Ean13Barcode(c, barHeight=dy)#, ratio=2)#, xdim=1*units.inch)
                    self.set_foreground()
                    self.set_background()
                    self.set_lineColor(oCanvas)
                    bc.drawOn(oCanvas, x0-6, y0)
            except:
                pass
            return
        
        rettangolo.output(self, oCanvas, y)
        
        if n.startswith('^'):
            #il nome del file deriva dalla valutazione di una espressione
            e = Expression(n[1:])
            name = e.evaluate(oCanvas)
            
        else:
            #il nome del file è scritto direttamente nell'espressione dell'immagine
            #scarto la path definita e cerco l'immagine sotto le possibili path del
            #report 
            (imagePath, imageName) = os.path.split(n)
            name = None
            for n in range(2):
                if n == 0:
                    name = os.path.join(report.pathsub, 'immagini')
                else:
                    name = report.pathimg
                name = os.path.join(name, imageName)
                name = name.replace('\\', '/')
                if os.path.exists(name):
                    break
                else:
                    name = None
#        if name is None:
#            name = os.path.join(report.pathimg, 'noimage.jpg').replace('\\', '/')
        if name is not None and os.path.exists(name):
            #===================================================================
            # oCanvas.drawInlineImage(str(name),
            #                         x0+self.set_pen(),
            #                         y0+self.set_pen(),
            #                         dx-(self.set_pen()*2),
            #                         dy-(self.set_pen()*2))
            #===================================================================

            oCanvas.drawInlineImage(str(name),
                                    x0+self.set_pen(),
                                    y0+self.set_pen(),
                                    dx-(self.set_pen()*2),
                                    dy-(self.set_pen()*2),
                                    preserveAspectRatio=(self.scaleImage=='RetainShape')
                                    )


import reportlab.graphics.barcode.eanbc as eanbc
from reportlab.platypus.flowables import Flowable

class Ean13Barcode(eanbc.Ean13BarcodeWidget):
    
    def __init__(self, code, **kwargs):
        eanbc.Ean13BarcodeWidget.__init__(self, code, **kwargs)
        self.humanReadable = False
    
    def drawOn(self, canvas, x, y):
        self.draw(canvas, x, y)
    
    def draw(self, canvas, x, y):
        #self._calculate()
        #barWidth = self.barWidth
        #wx = barWidth * self.ratio
        
        #left = self.quiet and self.lquiet or 0
        #b = self.bearers * barWidth
        #bb = b * 0.5
        #tb = self.barHeight - (b * 1.5)
        
        #for c in self.decomposed:
            #if c == 'i':
                #left = left + self.gap
            #elif c == 's':
                #left = left + barWidth
            #elif c == 'S':
                #left = left + wx
            #elif c == 'b':
                #self.rect(left, bb, barWidth, tb)
                #left = left + barWidth
            #elif c == 'B':
                #self.rect(left, bb, wx, tb)
                #left = left + wx
        
        #if self.bearers:
            #self.rect(self.lquiet, 0, \
                #self._width - (self.lquiet + self.rquiet), b)
            #self.rect(self.lquiet, self.barHeight - b, \
                #self._width - (self.lquiet + self.rquiet), b)
        
        #self.drawHumanReadable()
        
        barWidth = self.barWidth
        width = self.width
        barHeight = self.barHeight
        self.rect(canvas, x,y,width,barHeight,fillColor=None,strokeColor=None,strokeWidth=0)
        s = self.value+self._checkdigit(self.value)
        self._lquiet = lquiet = self._calc_quiet(self.lquiet)
        rquiet = self._calc_quiet(self.rquiet)
        b = [lquiet*'0',self._tail] #the signal string
        a = b.append
        self._encode_left(s,a)
        a(self._sep)
        
        z = ord('0')
        _right = self._right
        for c in s[self._start_right:]:
            a(_right[ord(c)-z])
        a(self._tail)
        a(rquiet*'0')
        
        fontSize = self.fontSize
        barFillColor = self.barFillColor
        barStrokeWidth = self.barStrokeWidth
        
        fth = fontSize*1.2
        b = ''.join(b)
        
        lrect = None
        for i,c in enumerate(b):
            if c=="1":
                dh = self._short_bar(i) and fth or 0
                yh = y+dh
                if lrect and lrect.y==yh:
                    lrect.width += barWidth
                else:
                    lrect = self.rect(canvas,x,yh,barWidth,barHeight-dh,fillColor=barFillColor,strokeWidth=barStrokeWidth,strokeColor=barFillColor)
            else:
                lrect = None
            x += barWidth
        
        if self.humanReadable:
            self.drawHumanReadable(canvas, s)

    def rect(self, canvas, x, y, w, h, fillColor=None, strokeColor=None, strokeWidth=0):
        canvas.rect(x, y, w, h, stroke=strokeWidth, fill=(fillColor is not None))

    def drawHumanReadable(self, canvas, s):
        #we have text
        from reportlab.pdfbase.pdfmetrics import getAscent, stringWidth
        fontSize = self.fontSize
        fontName = self.fontName
        w = stringWidth(s,fontName,fontSize)
        width = self.width
        if self.quiet:
            width -= (self.lquiet or 0)+(self.rquiet or 0)
            x = self.lquiet or 0
        else:
            x = 0
        if w>width: fontSize *= width/float(w)
        y = 1.07*getAscent(fontName)*fontSize/1000.
        self.annotate(canvas, x+width/2.,-y,s,fontName,fontSize)

    def annotate(self,canv,x,y,text,fontName,fontSize,anchor='middle'):
        canv.saveState()
        canv.setFont(self.fontName,fontSize)
        if anchor=='middle': func = 'drawCentredString'
        elif anchor=='end': func = 'drawRightString'
        else: func = 'drawString'
        getattr(canv,func)(x,y,text)
        canv.restoreState()


import reportlab.graphics.barcode.code128 as code128
class Code128Barcode(code128.Code128):
    pass

import reportlab.graphics.barcode.code39 as c39
class Code39Barcode(c39.Standard39):
    pass


class elemento_Testuale(elemento_Visuale):
    
    oCanvas=None
    report_font=None
    font_name=None
    font_size=None
    pdf_font_name=None
    isBold=None
    isItalic=None
    isUnderline=None
    isStrike_trough=None
    is_styled_text=None
    line_spacing=None
    vertical_alignment=None
    text_alignment=None
    rotation=None
    testo=None
    
    def __init__(self, definizione, oCanvas):
        elemento_Visuale.__init__(self, definizione)
        self.oCanvas=oCanvas
        textProperty=definizione["textElement"]
        self.set_line_spacing(getFromDict(textProperty, "textElement", "Single"))
        self.set_rotation(getFromDict(textProperty, "rotation", "None"))
        self.set_text_alignment(getFromDict(textProperty, "textAlignment", "Left"))
        self.set_vertical_alignment(getFromDict(textProperty, "verticalAlignment", "Top"))
        fontProperty=textProperty["font"]
        self.set_font_name(getFromDict(fontProperty, "fontName", "SansSerif"))
        self.set_bold(getFromDict(fontProperty, "isBold", "false"))
        self.set_italic(getFromDict(fontProperty, "isItalic", "false"))
        self.set_strike_trough(getFromDict(fontProperty, "isStrikeThrough", "false"))
        self.set_underline(getFromDict(fontProperty, "isUnderline", "false"))
        self.set_report_font(getFromDict(fontProperty, "pdfEncoding", "Cp1252"))
        self.set_pdf_font_name(getFromDict(fontProperty, "pdfFontName", "Helvetica"))
        self.set_font_size(getFromDict(fontProperty, "size", 10))
        self.set_style()
        
    def set_line_spacing(self, value=None):
        if value<>None:
            self.line_spacing=value
        return self.line_spacing
    
    def set_rotation(self, value=None):
        if value<>None:
            self.rotation=value
        return self.rotation

    def set_text_alignment(self, value=None):
        if value<>None:
            self.text_alignment=value
        return self.text_alignment
    
    def set_vertical_alignment(self, value=None):
        if value<>None:
            self.vertical_alignment=value
        return self.vertical_alignment
        
    def set_font_name(self, value=None):
        if value<>None:
            self.font_name=value
        return self.font_name
        
    def set_bold(self, value=None):
        if value<>None:
            if value=="true":
                self.isBold=True
            else:
                self.isBold=False
        return self.isBold
    
    def set_italic(self, value=None):
        if value<>None:
            if value=="true":
                self.isItalic=True
            else:
                self.isItalic=False
        return self.isItalic

    def set_strike_trough(self, value=None):
        if value<>None:
            if value=="true":
                self.isStrike_trough=True
            else:
                self.isStrike_trough=False
        return self.isStrike_trough

    def set_underline(self, value=None):
        if value<>None:
            if value=="true":
                self.isUnderline=True
            else:
                self.isUnderline=False
        return self.isUnderline
    
    def set_report_font(self, value=None):
        if value<>None:
            self.report_font=value
        return self.report_font
    
    def set_pdf_font_name(self, value=None):
        if value<>None:
            self.pdf_font_name=value
        return self.pdf_font_name

    def set_font_size(self, value=None):
        if value<>None:
            self.font_size=value
        return self.font_size

    def set_is_styled_text(self, value=None):
        if value<>None:
            self.is_styled_text=value
        return self.is_styled_text

    def set_style(self):
        self.style = ParagraphStyle( name='pbear-bold',
                                fontName=self.set_pdf_font_name(),
                                fontSize=self.set_font_size(),
                                bulletFontName=self.set_pdf_font_name(),
                                bulletFontSize=self.set_font_size(),
                                leading=self.set_font_size(),
                                spaceBefore=0,
                                alignment=TA_LEFT,
                                wordWrap=0
                                )
        self.style.textColor=Color(self.foreground.get_r(),
                              self.foreground.get_g(),
                              self.foreground.get_b())

        # Gestione Allineamento Orizzontale
        if self.set_text_alignment()=="Center":
            self.style.alignment=TA_CENTER 
        elif self.set_text_alignment()=="Right":
            self.style.alignment=TA_RIGHT 
        elif self.set_text_alignment()=="Left":
            self.style.alignment=TA_LEFT 
        elif self.set_text_alignment()=="Justify":
            self.style.alignment=TA_JUSTIFY 
        #self.set_attributiTesto()            

class staticText(elemento_Testuale):
    def __init__(self,definizione, oCanvas):
        elemento_Testuale.__init__(self, definizione, oCanvas)
        try:
            self.set_testo(definizione["text"])
        except:
            pass

    def set_testo(self, d=None):
        if d<>None:
            self.testo=d["DATA"].encode()
        return self.testo


    def set_attributiTesto(self):
        if self.isBold:
            self.testo='<b>' + unicode(self.testo) + '</b>'
        if self.isItalic:
            self.testo='<i>' + unicode(self.testo) + '</i>'
        if self.isUnderline:
            self.testo='<u>' + unicode(self.testo) + '</u>'
        
    def format(self, oCanvas):
        if self.isStretchWithOverflow:
            if self.rotation=="Left" or self.rotation=="Right":
                rotate=-1
            else:
                rotate=1
            left, top, width, height = self.text_rect(rotate)
            para = self.normalize(oCanvas, self.style, rotate)
            new_width, new_height = para.wrap(width, rotate*height)
            self.set_extendedheight(new_height+2)
        
    def text_rect(self, rotate):
        if rotate==1:
            x0,y0,dx,dy=self.set_leftFromBand(), self.set_topFromBand(), self.set_width(), self.set_height()
        else:
            x0,y0,dx,dy=self.set_topFromBand(), self.set_leftFromBand(), self.set_height(), self.set_width()
        return x0,y0,dx,dy
   
    def set_newRect(self, oCanvas):
        """
        Il metodo si fa carico di calcolare, mantenendo fissa la larghezza della casella di testo,
        quale debba essere l'altezza della stessa affinchè possa contenere l'intero testo senza
        che questi subisca alcun troncamento.
        Il metodo viene richiamato per gli oggetti per cui è stata impostat a vero la proprietà
        'Allunga se il testo cresce' (isStretchWithOverflow).
        """
        if self.rotation=="Left" or self.rotation=="Right":
            rotate=-1
        else:
            rotate=1
        left, top, width, height = self.text_rect(rotate)
        para = self.normalize(oCanvas, self.style, rotate)
        new_width, new_height = para.wrap(width, rotate*height)
        self.set_width(new_width)
        self.set_height(new_height+2)
    
    def output(self, oCanvas,y):
        self.set_isToPrint(oCanvas)
        if not self.isToPrint:
            return
        self.set_attributiTesto()
        if self.isStretchWithOverflow:
            self.format(oCanvas)
            self.set_height(self.set_extendedheight())
            #self.set_newRect(oCanvas)
        rotate=1
        oCanvas.rotate(0)
        # clip su testo in overflow
        self.set_origine(oCanvas,y)
        oCanvas.saveState()
        p = oCanvas.beginPath()
        oCanvas.setFillColorRGB(self.background.get_r(),
                                  self.background.get_g(),
                                  self.background.get_b())
        oCanvas.setStrokeColorRGB(self.background.get_r(),
                                self.background.get_g(),
                                self.background.get_b())
        if self.rotation=="Left" or self.rotation=="Right":
            rotate=-1
            if self.rotation=="Left":
                oCanvas.rotate(90)
            else:
                oCanvas.rotate(90)
            p.rect(self.get_y0(),
                   -self.get_x0(),
                   self.set_height(),
                   -self.set_width())
        else:
            rotate=1
            p.rect(self.get_x0(),
                   self.get_y0(),
                   self.set_width(),
                   self.set_height())
            
        if self.set_trasparent()==True:
            oCanvas.clipPath(p,stroke=0, fill=0)
        else:
            oCanvas.clipPath(p,stroke=0, fill=1)
        self.output_testo(oCanvas, rotate)       
        oCanvas.restoreState()

    def output_testo(self, oCanvas, rotate):
        if rotate==1:
            x0=self.get_x0()          # origine del controllo testo
            y0=self.get_y0()          #
            dx=self.set_width()       # larghezza oggetto testo
            dy=self.set_height()      # altezza oggetto testo
        else:
            x0=self.get_y0()          # origine del controllo testo
            y0=self.get_x0()          #
            dy=self.set_width()       # larghezza oggetto testo
            dx=self.set_height()      # altezza oggetto testo
        oCanvas.setFillColorRGB(self.foreground.get_r(),
                                self.foreground.get_g(),
                                self.foreground.get_b())
        para = self.normalize(oCanvas, self.style, rotate)
        w, h = para.wrap(dx, rotate*dy)             # calcolo larghezza e altezza necessari

        # Gestione Allineamento Verticale
        if rotate==1:
            if self.set_vertical_alignment()=="Middle":
                y0=y0+(dy-h)/2
            elif  self.set_vertical_alignment()=="Top":
                y0=y0+dy-h
            elif  self.set_vertical_alignment()=="Bottom":
                y0=y0+self.set_font_size()/4
            para.drawOn(oCanvas, x0, y0)
        else:
            para.drawOn(oCanvas, x0, rotate*(y0+h))
            

        
        
    def normalize(self, oCanvas, style, rotate):
        """
        Il metodo si fa carico di esaminare il paragrafo da mandare in stampa
        al fine di controllare che possa essere stampato all'interno della
        dimensione orizzontale della 'casella di testo'. Eventuali parola troppo
        ampie per essere riportate all'interno della casella di testo vengono
        adeguatamente spezzate.
        """
        s = None
        new1 = None
        new2 = None
        oFont = None
        dx = None
        dy = None
        para = None
        w = None
        oldw=None
        h = None
        
        #s = unicode(str(self.set_testo()), 'latin-1')
        #s = unicode(str(self.set_testo()), 'Windows-1252') #per il simbolo dell'euro
        try:
            s = unicode(self.set_testo())
        except Exception, e:
            s = repr(e.args)
        
        if rotate==1:
            dx=self.set_width()       # larghezza oggetto testo
            dy=self.set_height()      # altezza oggetto testo
        else:
            dy=self.set_width()       # larghezza oggetto testo
            dx=self.set_height()      # altezza oggetto testo
            
        para = Paragraph(s, style)# trasformo il testo in paragrafo
        w, h = para.wrap(dx, dy)  # calcolo larghezza e altezza necessari
                                  # a visualizzare l'intero testo
                                  
        oldw=-1

        if s.find("amp") <> -1:
            pass
        
        
        
        
        while w > dx and oldw<>w:
            oldw=w
            parole = split(s)
            parole.sort(lambda x,y: len(y)-len(x))
            new1=parole[0]
            new2=""
            while dx<oCanvas.stringWidth(new1,self.set_pdf_font_name(), self.set_font_size()):
                nSkip=self.terminaCon(new1, ('&amp;','<b>', '</b>', '<u>', '</u>', '<i>', '</i>'))
                #nSkip=1
                new2=new1[(len(new1)-nSkip):]+new2
                new1=new1[0:(len(new1)-nSkip)]
                
            s=replace( s, parole[0], new1+" "+new2)
            para = Paragraph(s, style)          # trasformo il testo in paragrafo
            w, h = para.wrap(dx, dy)            # calcolo larghezza e altezza necessari
        return para


    def terminaCon(self, s, t):
        l=1
        for sfx in t:
            if s.endswith(sfx):
                l=len(sfx)
                break
        return l    
    
    
class variableText(staticText):
    evaluationTime=None
    isBlankWhenNull=None
    pattern=None
    oExpression=None
    
    def __init__(self,definizione, oCanvas):
        
        if self.key=="head_numpag":
            print "alt"
        
        staticText.__init__(self, definizione, oCanvas)
        
        def gf(x,y=None):
            return getFromDict(definizione, x, y)
        
        self.set_evaluationTime(gf('evaluationTime', 'Now'))
        self.set_isBlankWhenNull(gf('isBlankWhenNull', 'true'))
        #self.set_isStretchWithOverflow(gf('isStretchWithOverflow', 'true'))
        self.set_pattern(gf('pattern', None))
        self.oExpression=Expression(definizione["textFieldExpression"]["DATA"].encode('Windows-1252'))
        self.refresh()
        
    def refresh(self):
        if self.key=="head_numpag":
            self.testo=self.oExpression.evaluate(self.oCanvas)
        else:
            self.testo=self.oExpression.evaluate(self.oCanvas)

    
 
    def set_evaluationTime(self, value=None):
        if value<>None:
            self.evaluationTime=value
        return self.evaluationTime
    
    def set_isBlankWhenNull(self, value=None):
        if value<>None:
            if value=="true":
                self.isBlankWhenNull=True
            else:
                self.isBlankWhenNull=False
        return self.isBlankWhenNull

    def set_pattern(self, value=None):
        if value<>None:
            self.pattern=value
        return self.pattern
    
    def output(self, oCanvas,y):
        self.set_isToPrint(oCanvas)
        if self.isToPrint:
            staticText.output(self, oCanvas, y)
    
def getFromDict(dict, key, default):
    try:
        value=dict[key]
    except:
        value=default
    return value
