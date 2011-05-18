#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         lib.py
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

from mx import DateTime
import locale
import sys
import wx

_evtCHANGEMENU = wx.NewEventType()
EVT_CHANGEMENU = wx.PyEventBinder(_evtCHANGEMENU, 0)


def MonthEndDate(date):
    assert isinstance(date, DateTime.DateTimeType),\
           "L'argomento deve essere di tipo mx.DateTime"
    
    return DateTime.Date(date.year, date.month, date.GetDaysInMonth())


# ------------------------------------------------------------------------------


def AddMonths(date, months):
    day = date.day
    for m in range(months):
        date = DateTime.Date(date.year, date.month, date.GetDaysInMonth())+1
        date = DateTime.Date(date.year, date.month, min(day, date.GetDaysInMonth()))
    return date


# ------------------------------------------------------------------------------


def dtoc(d):
    """
    Restituisce la data sotto forma di stringa, coerentemente con le 
    impostazioni di locale.
    """
    return d.Format().split()[0]


# ------------------------------------------------------------------------------


def SameFloat(f1, f2):
    #return abs(f1-f2)<0.00000001
    return round(f1,6) == round(f2,6)


# ------------------------------------------------------------------------------


class StdErrCatcher(object):
    def __init__(self, logfile):
        object.__init__(self)
        self.logfile = logfile
    def write(self, msg):
        print "ERRORE!!!"
        try:
            f = open(self.logfile, 'a')
            f.write(msg)
            f.close()
            print "  -loggato"
        except:
            pass


# ------------------------------------------------------------------------------


def InitErrorsLog(logfile='errors.log'):
    sys.stderr = StdErrCatcher(logfile)


# ------------------------------------------------------------------------------


class XFrame(wx.Frame):
    pass
