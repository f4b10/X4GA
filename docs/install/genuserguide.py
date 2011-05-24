#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         docs/install/genuserguide.py
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

from reportlab.lib.units import inch, cm
from reportlab.rl_config import defaultPageSize
from reportlab.platypus import PageTemplate, BaseDocTemplate, Frame, Paragraph
from reportlab.tools.docco.rltemplate import FrontCoverTemplate

class _FrontCoverTemplate(FrontCoverTemplate):
    
    def __init__(self, id, pageSize=defaultPageSize):
        self.pageWidth = pageSize[0]
        self.pageHeight = pageSize[1]
        frame1 = Frame(inch,
                       3*inch,
                       self.pageWidth - 2*inch,
                       self.pageHeight - 518, id='cover')
        PageTemplate.__init__(self, id, [frame1])  # note lack of onPage

    def afterDrawPage(self, canvas, doc):
        canvas.saveState()
        canvas.drawImage('../../imgsource/x4_splash.png',2*inch, 8*inch)
        canvas.setFont('Times-Roman', 10)
        canvas.line(inch, 120, self.pageWidth - inch, 120)
        canvas.drawString(inch, 100, 'Astra S.r.l.')
        canvas.drawString(inch, 88, 'C.so Cavallotti, 122')
        canvas.drawString(inch, 76, '18038 Sanremo (IM)')
        canvas.drawString(inch, 64, 'ITALY')
        canvas.restoreState()

import reportlab.tools.docco.rltemplate as rlt
rlt.FrontCoverTemplate = _FrontCoverTemplate

def unitext(text):
    return unicode(text or '', 'latin-1')

from reportlab.tools.docco.rl_doc_utils import heading1, quickfix
import reportlab.tools.docco.rl_doc_utils as rldu
def _heading1(text):
    """Use this for chapters.  Lessons within a big chapter
    should now use heading2 instead.  Chapters get numbered."""
    rldu.getStory().append(rldu.PageBreak())
    p = rldu.Paragraph('Capitolo <seq id="Chapter"/> '+rldu.quickfix(text), rldu.H1)
    rldu.getStory().append(p)
rldu.heading1 = _heading1

def _bullet(text):
    text=u'<bullet><font name="Symbol">\xe2\x80\xa2</font></bullet>' + rldu.quickfix(text)
    P = Paragraph(text, rldu.BU)
    rldu.getStory().append(P)
rldu.bullet = _bullet

def _quickfix(text):
    return quickfix(unitext(text))
rldu.quickfix = _quickfix

def run(pagesize=None, verbose=0, outDir=None):
    import os
    from reportlab.tools.docco.rl_doc_utils import setStory, getStory, RLDocTemplate, defaultPageSize
    from reportlab.tools.docco import rl_doc_utils
    from reportlab.lib.utils import open_and_read, _RL_DIR
    if not outDir: 
        outDir = '../manuals/'#os.path.join(_RL_DIR,'docs')
        if not os.path.isdir(outDir):
            os.mkdir(outDir)
    destfn = os.path.join(outDir,'X4 - Installazione.pdf')
    doc = RLDocTemplate(destfn,pagesize = pagesize or defaultPageSize)
    doc.title = 'X4 Setup'
    doc.subject = 'Manuale di installazione di X4GA'
    doc.author = 'Astra S.r.l.'

    #this builds the story
    setStory()
    G = {}
    exec 'from reportlab.tools.docco.rl_doc_utils import *' in G, G
    for f in (
        'ch1_intro',
        'ch2_dbengine',
        'ch3_workstation',
        #'ch3_pdffeatures',
        #'ch4_platypus_concepts',
        #'ch5_paragraphs',
        #'ch6_tables',
        #'ch7_custom',
        #'ch9_future',
        #'app_demos',
        ):
        exec open_and_read(f+'.py',mode='t') in G, G
    del G

    story = getStory()
    if verbose: print 'Built story contains %d flowables...' % len(story)
    doc.build(story)
    if verbose: print 'Saved "%s"' % destfn

def makeSuite():
    "standard test harness support - run self as separate process"
    from reportlab.test.utils import ScriptThatMakesFileTest
    return ScriptThatMakesFileTest('../docs/userguide', 'genuserguide.py', 'userguide.pdf')

def main():
    import sys
    outDir = filter(lambda x: x[:9]=='--outdir=',sys.argv)
    if outDir:
        outDir = outDir[0]
        sys.argv.remove(outDir)
        outDir = outDir[9:]
    else:
        outDir = None
    verbose = '-s' not in sys.argv
    if not verbose: sys.argv.remove('-s')
    timing = '-timing' in sys.argv
    if timing: sys.argv.remove('-timing')
    prof = '-prof' in sys.argv
    if prof: sys.argv.remove('-prof')

    if len(sys.argv) > 1:
        try:
            pagesize = (w,h) = eval(sys.argv[1])
        except:
            print 'Expected page size in argument 1', sys.argv[1]
            raise
        if verbose:
            print 'set page size to',sys.argv[1]
    else:
        pagesize = None
    if timing:
        from time import time
        t0 = time()
        run(pagesize, verbose,outDir)
        if verbose:
            print 'Generation of userguide took %.2f seconds' % (time()-t0)
    elif prof:
        import profile
        profile.run('run(pagesize,verbose,outDir)','genuserguide.stats')
    else:
        run(pagesize, verbose,outDir)
if __name__=="__main__":
    main()
