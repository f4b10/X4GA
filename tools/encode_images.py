#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         encode_images.py
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


"""
Encoding immagini del programma in images.py
"""

from __builtin__ import file as file_bi
def _file(name, mode=None, *args):
    """
    Workaround per malfunzionamento di img2py: in wx 2.8, pare che cerchi di
    aprire il file immagine senza specificare il modo binario, causando il
    caricamento errato dell'immagine.
    """
    if mode is None:
        mode = 'rb'
    return file_bi(name, mode, *args)
import __builtin__
__builtin__.file = _file

import sys
from wx.tools import img2py


img = []

img.append(('../images.py', (
    "   -u -n SplashLogo         imgsource/x4_splash.png",
    "-a -u -n X4Logo             imgsource/x4_logo.png",
    "-a -u -n SplashLogoLite     imgsource/x4_splash_lite.png",
    "-a -u -n X4LogoLite         imgsource/x4_logo_lite.png",
    "-a -u -n X4LogoSanVal       imgsource/x4_logo_sanvalentino.png",
    "-a -u -n X4LogoBirth7       imgsource/x4_logo_birthday7.png",
    "-a -u -n X4LogoBackup       imgsource/x4_logo_backup.png",
    "-a -u -n Icon               imgsource/x4_icon.png",
    "-a -u -n SplashLogoNatale   imgsource/x4_splash_natale.png",
    "-a -u -n X4LogoNatale       imgsource/x4_logo_natale.png",
    "-a -u -n SplashLogoBrindisi imgsource/x4_splash_brindisi.png",
    "-a -u -n X4LogoBrindisi     imgsource/x4_logo_brindisi.png",
    "-a -u -n SplashLogoBefana   imgsource/x4_splash_befana.png",
    "-a -u -n X4LogoBefana       imgsource/x4_logo_befana.png",
    
    #toolbar - old
    "-a -u -n TB_Clienti         imgsource/tb_clienti.png",
    "-a -u -n TB_Fornit          imgsource/tb_fornit.png",
    "-a -u -n TB_EmiDoc          imgsource/tb_emidoc.png",
    "-a -u -n TB_IncPag          imgsource/tb_incpag.png",
    "-a -u -n TB_IntSott         imgsource/tb_intsott.png",
    "-a -u -n TB_IntArt          imgsource/tb_intart.png",
    "-a -u -n TB_Generic         imgsource/tb_generic.png",
    "-a -u -n TB_ScadCF          imgsource/tb_vista_scadcf.png",
    
    #toolbar - spheric
    "-a -u -n TB_Spheric_EmiDoc  imgsource/tb_spheric_emidoc.png",
    "-a -u -n TB_Spheric_IntArt  imgsource/tb_spheric_intart.png",
    "-a -u -n TB_Spheric_IncPag  imgsource/tb_spheric_incpag.png",
    "-a -u -n TB_Spheric_IntCli  imgsource/tb_spheric_intcli.png",
    "-a -u -n TB_Spheric_IntFor  imgsource/tb_spheric_intfor.png",
    "-a -u -n TB_Spheric_IntPdc  imgsource/tb_spheric_intpdc.png",
    "-a -u -n TB_Spheric_ScadCF  imgsource/tb_vista_scadcf.png",
    
    #toolbar - vista
    "-a -u -n TB_Vista_EmiDoc    imgsource/tb_vista_emidoc.png",
    "-a -u -n TB_Vista_IntArt    imgsource/tb_vista_intart.png",
    "-a -u -n TB_Vista_IncPag    imgsource/tb_vista_incpag.png",
    "-a -u -n TB_Vista_IntCli    imgsource/tb_vista_intcli.png",
    "-a -u -n TB_Vista_IntFor    imgsource/tb_vista_intfor.png",
    "-a -u -n TB_Vista_IntPdc    imgsource/tb_vista_intpdc.png",
    "-a -u -n TB_Vista_ScadCF    imgsource/tb_vista_scadcf.png",
    
    #toolbar - pastel
    "-a -u -n TB_Pastel_EmiDoc   imgsource/tb_pastel_emidoc.png",
    "-a -u -n TB_Pastel_IntArt   imgsource/tb_pastel_intart.png",
    "-a -u -n TB_Pastel_IncPag   imgsource/tb_pastel_incpag.png",
    "-a -u -n TB_Pastel_IntCli   imgsource/tb_pastel_intcli.png",
    "-a -u -n TB_Pastel_IntFor   imgsource/tb_pastel_intfor.png",
    "-a -u -n TB_Pastel_IntPdc   imgsource/tb_pastel_intpdc.png",
    "-a -u -n TB_Pastel_ScadCF   imgsource/tb_vista_scadcf.png",
    
    "-a -u -n Info32             imgsource/info32.png",
    "-a -u -n Lock               imgsource/lock.png",
    "-a -u -n AstraLittle        imgsource/astra_little.png",
    "-a -u -n ProgramUpdate      imgsource/programupdates.png",
    "-a -u -n Euro               imgsource/euro.png",
    )))


img.append(('../awc/controls/images.py', (
    "   -u -n Wait32       imgsource/awc/wait32.png",
    "-a -u -n CardEmpty16  imgsource/awc/emptypaper16.png",
    "-a -u -n CardFull16   imgsource/awc/fullpaper16.png",
    "-a -u -n CardError16  imgsource/awc/errorpaper16.png",
    "-a -u -n Image16      imgsource/awc/image16.png",
    "-a -u -n Image32      imgsource/awc/image32.png",
    "-a -u -n Scanner16    imgsource/awc/scanner16.png",
    "-a -u -n Scanner32    imgsource/awc/scanner32.png",
    "-a -u -n Printer16    imgsource/awc/printer16.png",
    "-a -u -n Printer32    imgsource/awc/printer32.png",
    "-a -u -n Web16        imgsource/awc/web16.png",
    "-a -u -n Web32        imgsource/awc/web32.png",
    "-a -u -n Audio16      imgsource/awc/audio16.png",
    "-a -u -n Audio32      imgsource/awc/audio32.png",
    "-a -u -n Text16       imgsource/awc/text16.png",
    "-a -u -n Text20       imgsource/awc/text20.png",
    "-a -u -n Text32       imgsource/awc/text32.png",
    "-a -u -n Filter16     imgsource/awc/filter16.png",
    "-a -u -n FilterAt16   imgsource/awc/filterat16.png",
    "-a -u -n Filter20     imgsource/awc/filter20.png",
    "-a -u -n CheckYes     imgsource/awc/checkyes16.png",
    "-a -u -n CheckNo      imgsource/awc/checkno16.png",
    "-a -u -n Mail20       imgsource/awc/mail20.png",
    "-a -u -n Jabber16     imgsource/awc/jabber16.png",
    "-a -u -n Jabber20     imgsource/awc/jabber20.png",
    "-a -u -n Jabber32     imgsource/awc/jabber32.png",
    "-a -u -n Web20        imgsource/awc/web20.png",
    "-a -u -n Phone20      imgsource/awc/phone20.png",
    "-a -u -n Folder20     imgsource/awc/folder20.png",
    "-a -u -n Error        imgsource/awc/error.png",
    "-a -u -n Earth20      imgsource/awc/earth20.png",
    )))

img.append(('../awc/layout/images.py', (
    "   -u -n Left20               imgsource/awc/left20.png",
    "-a -u -n Leftmost20           imgsource/awc/leftmost20.png",
    "-a -u -n Right20              imgsource/awc/right20.png",
    "-a -u -n Rightmost20          imgsource/awc/rightmost20.png",
    "-a -u -n Save20               imgsource/awc/save20.png",
    "-a -u -n Undo20               imgsource/awc/undo20.png",
    "-a -u -n New20                imgsource/awc/new20.png",
    "-a -u -n Delete20             imgsource/awc/delete20.png",
    "-a -u -n OrderUp20            imgsource/awc/orderup20.png",
    "-a -u -n OrderDown20          imgsource/awc/orderdown20.png",
    "-a -u -n Search16             imgsource/awc/search16.png",
    "-a -u -n SearchAt16           imgsource/awc/searchat16.png",
    "-a -u -n Search20             imgsource/awc/search20.png",
    "-a -u -n Pdf32                imgsource/awc/pdf32.png",
    
    #internal browser - spheric
    "-a -u -n Web_Spheric_Previous imgsource/awc/web_spheric_previous.png",
    "-a -u -n Web_Spheric_Next     imgsource/awc/web_spheric_next.png",
    "-a -u -n Web_Spheric_Home     imgsource/awc/web_spheric_home.png",
    "-a -u -n Web_Spheric_World    imgsource/awc/web_spheric_world.png",
    
    #internal browser - vista
    "-a -u -n Web_Vista_Previous imgsource/awc/web_vista_previous.png",
    "-a -u -n Web_Vista_Next     imgsource/awc/web_vista_next.png",
    "-a -u -n Web_Vista_Home     imgsource/awc/web_vista_home.png",
    "-a -u -n Web_Vista_World    imgsource/awc/web_vista_world.png",
    
    #internal browser - pastel
    "-a -u -n Web_Pastel_Previous imgsource/awc/web_pastel_previous.png",
    "-a -u -n Web_Pastel_Next     imgsource/awc/web_pastel_next.png",
    "-a -u -n Web_Pastel_Home     imgsource/awc/web_pastel_home.png",
    "-a -u -n Web_Pastel_World    imgsource/awc/web_pastel_world.png",
    
    )))


if __name__ == "__main__":
    for source, commands in img:
        print "Generating %s" % source
        for cmd in commands:
            args = cmd.split()+[source]
            img2py.main(args)
