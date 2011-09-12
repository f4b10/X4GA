#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         version.py
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

appcode = "x4ga"
appdesc = "X4 Gestione Aziendale"

from _branch import branch
VERSION_BRANCH  = branch

from _version import apptype, appType, appinfo

VERSION_MAJOR   = 1
VERSION_MINOR   = 3
VERSION_RELEASE = 28
VERSION_TAG     = ""
VERSION_TYPE    = apptype
VERSION_TYPEXT  = appType
VERSION_INFO    = appinfo

__min_compat_ver__ = '1.3.28'

VERSION = (VERSION_MAJOR, VERSION_MINOR, VERSION_RELEASE, VERSION_TAG)

VERSION_STRING  = "%s.%s.%s" % (VERSION_MAJOR,
                                VERSION_MINOR,
                                str(VERSION_RELEASE).zfill(2))

__version_exe__ = VERSION_STRING

if VERSION_TAG:
    VERSION_STRING += " %s" % VERSION_TAG

__version__ = VERSION_STRING

def OSS():
    return VERSION_TYPE == 'community'


MODVERSION_NAME    = ""

MODVERSION_MAJOR   = 0
MODVERSION_MINOR   = 0
MODVERSION_RELEASE = 00
MODVERSION_TAG     = ""

__min_compat_mod__ = ''

MODVERSION = (MODVERSION_MAJOR, 
              MODVERSION_MINOR, 
              MODVERSION_RELEASE, 
              MODVERSION_TAG)

MODVERSION_STRING  = "%s.%s.%s" % (MODVERSION_MAJOR, 
                                   MODVERSION_MINOR, 
                                   str(MODVERSION_RELEASE).zfill(2))

__modversion_exe__ = MODVERSION_STRING

if MODVERSION_TAG:
    MODVERSION_STRING += " %s" % MODVERSION_TAG

__modversion__ = MODVERSION_STRING
