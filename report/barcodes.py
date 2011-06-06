#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/barcodes.py
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

from PIL import Image, ImageDraw

import reportlab.graphics.barcode.code39 as c39
import reportlab.graphics.barcode.code128 as code128
import reportlab.graphics.barcode.eanbc as eanbc

import string


BARCODE_TYPE_NONE =         0
BARCODE_TYPE_2OF7 =         1
BARCODE_TYPE_3OF9 =         2
BARCODE_TYPE_BOOKLAND =     3
BARCODE_TYPE_CODABAR =      4
BARCODE_TYPE_CODE128 =      5
BARCODE_TYPE_CODE128A =     6
BARCODE_TYPE_CODE128B =     7
BARCODE_TYPE_CODE128C =     8
BARCODE_TYPE_CODE39 =       9
BARCODE_TYPE_EAN128 =      10
BARCODE_TYPE_EAN13 =       11
BARCODE_TYPE_GLOBALTRADE = 12
BARCODE_TYPE_INT2OF5 =     13
BARCODE_TYPE_MONARCH =     14
BARCODE_TYPE_NW7 =         15
BARCODE_TYPE_PDF417 =      16
BARCODE_TYPE_SCC14SHIP =   17
BARCODE_TYPE_SHIPMENTID =  18
BARCODE_TYPE_SSCC18 =      19
BARCODE_TYPE_STD2OF5 =     20
BARCODE_TYPE_UCC128 =      21
BARCODE_TYPE_UPCA =        22
BARCODE_TYPE_USD3 =        23
BARCODE_TYPE_USD4 =        24
BARCODE_TYPE_USPS =        25
BARCODE_TYPE_CODE39EXT =   26

#iReport 3.0.0 is missing qrcode, so use pdf417 instead
BARCODE_TYPE_2D_QR =       BARCODE_TYPE_PDF417


class Code39Barcode(c39.Standard39):
    
    def getPngImage(self, w, h, fgcol, bgcol):
        
        w = int(w)
        h = int(h)
        
        self._calculate()
        barWidth = self.barWidth
        wx = barWidth * self.ratio
        
        left = self.quiet and self.lquiet or 0
        b = self.bearers * barWidth
        bb = b * 0.5
        tb = self.barHeight - (b * 1.5)
        
        bars = []
        
        for c in self.decomposed:
            if c == 'i':
                left = left + self.gap
            elif c == 's':
                left = left + barWidth
            elif c == 'S':
                left = left + wx
            elif c == 'b':
                #self.rect(left, bb, barWidth, tb)
                bars.append((left, barWidth))
                left = left + barWidth
            elif c == 'B':
                #self.rect(left, bb, wx, tb)
                bars.append((left, wx))
                left = left + wx
        
        img = Image.new('RGB', (left, h), bgcol)
        d = ImageDraw.Draw(img)
        for bx, bw in bars:
            d.rectangle(((bx, 0), (bx+bw-1, h-1)), fgcol)
        del d
        
        return img


# ------------------------------------------------------------------------------


class Code128Barcode(code128.Code128):
    
    def getPngImage(self, w, h, fgcol, bgcol):
        
        w = int(w)
        h = int(h)
        
        self._calculate()
        oa, oA = ord('a') - 1, ord('A') - 1
        barWidth = self.barWidth
        left = self.quiet and self.lquiet or 0
        
        bars = []
        
        for c in self.decomposed:
            oc = ord(c)
            if c in string.lowercase:
                left = left + (oc - oa) * barWidth
            elif c in string.uppercase:
                w = (oc - oA) * barWidth
                #self.rect(left, 0, w, self.barHeight)
                bars.append((left, w))
                left += w
        
        img = Image.new('RGB', (left, h), bgcol)
        d = ImageDraw.Draw(img)
        for bx, bw in bars:
            d.rectangle(((bx, 0), (bx+bw-1, h-1)), fgcol)
        del d
        
        return img


# ------------------------------------------------------------------------------


class Ean13Barcode(eanbc.Ean13BarcodeWidget):
    
    def getPngImage(self, w, h, fgcol, bgcol):
        
        w = int(w)
        h = int(h)
        
        barWidth = self.barWidth
        width = self.width
        barHeight = self.barHeight
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
        
        b = ''.join(b)
        left = self.quiet and self.lquiet or 0
        
        bars = []
        
        lrect = None
        for i,c in enumerate(b):
            if c == '1':
                bars.append((left, barWidth))
            left += barWidth
        
        img = Image.new('RGB', (left, h), bgcol)
        d = ImageDraw.Draw(img)
        for bx, bw in bars:
            d.rectangle(((bx, 0), (bx+bw-1, h-1)), fgcol)
        del d
        
        return img


# ------------------------------------------------------------------------------


import StringIO
try:
    from pygooglechart import QRChart
except ImportError:
    class QRChart:
        def __init__(self, *args, **kwargs):
            raise Exception, "Manca package pygooglechart"

class QRCode(object):
    
    def __init__(self, w, h, message, **kwargs):
        self.qrc = QRChart(w, h, **kwargs)
        self.qrc.add_data(message)
    
    def getPngImage(self, w, h, fgcol, bgcol):
        
        w = int(w)
        h = int(h)
        
#        img = Image.new('RGB', (w, h), bgcol)
#        d = ImageDraw.Draw(img)
#        for bx, bw in bars:
#            d.rectangle(((bx, 0), (bx+bw-1, h-1)), fgcol)
#        del d
        
        import urllib2
        opener = urllib2.urlopen(self.qrc.get_url())

        if opener.headers['content-type'] != 'image/png':
            raise Exception('Server responded with a ' \
                'content-type of %s' % opener.headers['content-type'])

        stream = opener.read()
        
        opener.close()
        
        img = Image.open(StringIO.StringIO(stream))
        
        return img


# ------------------------------------------------------------------------------


def getBarcodeImage(oCanvas, x0, y0, dx, dy, fgcol, bgcol, 
                    ctype, ccode, cflag1, cflag2, cflag3, cflag4, cflag5):
    
    img = None
    
    fgcol, bgcol = map(lambda c: (int(c.r*255), 
                                  int(c.g*255), 
                                  int(c.b*255)), (fgcol, bgcol))
    
    btype = int(ctype)
    
    if btype == BARCODE_TYPE_CODE39:
        kw = {'barHeight': dy,
              'barWidth':  1,
              'checksum': 0}
        kw['lquiet'] = kw['rquiet'] = 0
        kw['ratio'] = 2
        bc = Code39Barcode(ccode, **kw)
        img = bc.getPngImage(dx, dy, fgcol, bgcol)
        
    elif btype == BARCODE_TYPE_CODE128:
        kw = {'barHeight': dy,
              'barWidth':  1,
              'checksum': 0}
        kw['lquiet'] = kw['rquiet'] = 0
        kw['ratio'] = 2
        bc = Code128Barcode(ccode, **kw)
        img = bc.getPngImage(dx, dy, fgcol, bgcol)
        
    elif btype == BARCODE_TYPE_EAN13:
        kw = {'barWidth': 1,
              'barHeight': dy}
        kw['lquiet'] = kw['rquiet'] = 0
        bc = Ean13Barcode(ccode, **kw)
        img = bc.getPngImage(dx, dy, fgcol, bgcol)
        
    elif btype == BARCODE_TYPE_2D_QR:
#        kw = {'barWidth': 1,
#              'barHeight': dy}
#        kw['lquiet'] = kw['rquiet'] = 0
        bc = QRCode(int(dx), int(dy), ccode)#, **kw)
        img = bc.getPngImage(dx, dy, fgcol, bgcol)
    
    return img
