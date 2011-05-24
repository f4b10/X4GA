#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         _makedocver.py
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

import versionchanges as vc
relnm = vc.history[0][0]
relok = vc.history[0][1] is not None

def gendoc():
    
    print "Creo verchg.txt relativo alla release %s" % relnm
    
    
    path = ''
    
    def fmt(x, w=76):
        out = ''
        while '\n' in x:
            x = x.replace('\n', ' ')
        while '  ' in x:
            x = x.replace('  ', ' ')
        while len(x):
            l = ''
            do = True
            while do and len(x):
                if ' ' in x:
                    n = x.index(' ')
                    if len(l)+n<w:
                        l += x[:n+1]
                        x = x[n+1:]
                    else:
                        do = False
                else:
                    if len(l)+len(x)<w:
                        l += x
                        x = ''
                    else:
                        do = False
            out += ('  %s\n' % l)
        return out
    
    
    for history, vtag, filename in ((vc.history,    'Versione', 'verchg.txt'),
                                    (vc.historymod, 'Mod',      'modchg.txt')):
        
        text = ""
        
        for version, reldate, changes in history:
            
            #versione
            if text:
                text += '\n\n'
            if reldate:
                reldat = reldate.Format('%d.%m.%Y')
            else:
                reldat = 'non rilasciata'
            title = '%s: %s (%s)' % (vtag, version, reldat)
            text += title+'\n%s' % ('='*len(title))
            text += '\n\n'
            
            for tag, change in changes:
                while '  ' in change:
                    change = change.replace('  ', ' ')
                text += '- %s\n' % tag
                text += '%s\n' % fmt(change)
        
        if text:
            text = '\n'+text
            fp = open(path+filename, 'w')
            fp.write(text)
            fp.close()
            print "Generato %s con %d linee." % (filename, text.count('\n'))


if __name__ == '__main__':
    gendoc()
