#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         mx/DateTime.py
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

from datetime import date
from datetime import datetime as dtime
from datetime import timedelta


FORMAT_DATE = '%d.%m.%Y'
FORMAT_DATE_SH = '%d.%m.%y'
def SetFormatDate(f):
    global FORMAT_DATE
    FORMAT_DATE = f
def GetFormatDate():
    return FORMAT_DATE

FORMAT_DATETIME = '%d.%m.%Y %H:%M:%S'
FORMAT_DATETIME_SH = '%d.%m.%y %H:%M:%S'
def SetFormatDateTime(f):
    global FORMAT_DATETIME
    FORMAT_DATETIME = f
def GetFormatDateTime():
    return FORMAT_DATETIME


class dtmix(object):
    
    def GetDaysInMonth(self):
        d = _date(self.year, self.month, 28)
        while True:
            d2 = d+timedelta(days=1)
            if d2.month != d.month:
                break
            d = d2
        return d.day
    
    def GetMonthName(self):
        return 'Gennaio Febbraio Marzo Aprile Maggio Giugno Luglio Agosto Settembre Ottobre Novembre Dicembre'.split()[self.month-1]
    
    def GetDayName(self):
        return 'Lunedi Martedi Mercoledi Giovedi Venerdi Sabato'.split()[self.weekday()]
    
    def __lt__(self, x):
        if x is None:
            return False
        return self.baseclass.__lt__(self, x)
    
    def __le__(self, x):
        if x is None:
            return False
        return self.baseclass.__le__(self, x)
    
    def __gt__(self, x):
        if x is None:
            return True
        return self.baseclass.__gt__(self, x)
    
    def __ge__(self, x):
        if x is None:
            return True
        return self.baseclass.__ge__(self, x)
    
    def __eq__(self, x):
        return self.baseclass.__eq__(self, x)


# ------------------------------------------------------------------------------


class _date(date, dtmix):
    
    baseclass = date
    
    def __add__(self, x):
        """
        Aggiunge 'x' alla data; se x è di tipo numerico (int/float/long) viene
        restituita la data maggiorata di 'x' giorni, altrimenti funzionalità
        standard della somma di un datetime.date con altro (timdelta)
        """
        if isinstance(x, (int, float, long)):
            return _date(self.year, self.month, self.day)+timedelta(days=x)
        d = date.__add__(self, x)
        return _date(d.year, d.month, d.day)
    
    def __sub__(self, x):
        """
        Sottrae 'x' dalla data; se x è di tipo numerico (int/float/long) viene
        restituita la data defalcata di 'x' giorni, altrimenti funzionalità
        standard della sottrazioe da un datetime.date di altro (timdelta)
        """
        if isinstance(x, (int, float, long)):
            #sottraggo un numero dalla data, detraggo in giorni
            return _date(self.year, self.month, self.day)-timedelta(days=x)
        d = date.__sub__(self, x)
        if isinstance(x, (_date, _datetime)):
            # data-data = timedelta, lo restituisco
            return d
        #sottrazione standard
        return _date(d.year, d.month, d.day)
    
    def __lt__(self, x):
        if isinstance(x, dtime):
            x = _date(x.year, x.month, x.day)
        return dtmix.__lt__(self, x)
    
    def __le__(self, x):
        if isinstance(x, dtime):
            x = _date(x.year, x.month, x.day)
        return dtmix.__le__(self, x)
    
    def __gt__(self, x):
        if isinstance(x, dtime):
            x = _date(x.year, x.month, x.day)
        return dtmix.__gt__(self, x)
    
    def __ge__(self, x):
        if isinstance(x, dtime):
            x = date(x.year, x.month, x.day)
        return dtmix.__ge__(self, x)
    
    def __eq__(self, x):
        if isinstance(x, dtime):
            x = _date(x.year, x.month, x.day)
        return dtmix.__eq__(self, x)
    
    def strftime(self, fmt='%c'):
        try:
            return dtime.strftime(self, fmt)
        except ValueError, e:
            return None
    
    def Format(self, fmt=None):
        if fmt is None:
            fmt = FORMAT_DATE
        try:
            return dtime.strftime(self, fmt)
        except ValueError, e:
            return None
    
    def FormatANSI(self):
        return '%s-%s-%s' % (str(self.year).zfill(4), str(self.month).zfill(2), str(self.day).zfill(2))


# ------------------------------------------------------------------------------


class _datetime(dtime, dtmix):
    
    baseclass = dtime
    
    def __add__(self, x):
        """
        Aggiunge 'x' alla data; se x è di tipo numerico (int/float/long) viene
        restituita la data maggiorata di 'x' giorni, altrimenti funzionalità
        standard della somma di un datetime.datetime con altro (timdelta)
        """
        if isinstance(x, (int, float, long)):
            return _datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)+timedelta(days=x)
        d = dtime.__add__(self, x)
        return _datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)
    
    def __sub__(self, x):
        """
        Sottrae 'x' dalla data; se x è di tipo numerico (int/float/long) viene
        restituita la data defalcata di 'x' giorni, altrimenti funzionalità
        standard della sottrazioe da un datetime.date di altro (timdelta)
        """
        if isinstance(x, (int, float, long)):
            #sottraggo un numero dalla data, detraggo in giorni
            return _datetime(self.year, self.month, self.day, self.hour, self.minute, self.second)-timedelta(days=x)
        d = dtime.__sub__(self, x)
        if isinstance(x, (_date, _datetime)):
            # data-data = timedelta, lo restituisco
            return d
        #sottrazione standard
        return _datetime(d.year, d.month, d.day, d.hour, d.minute, d.second)
    
    def __lt__(self, x):
        if isinstance(x, date) and not isinstance(x, _datetime):
            return x.__gt__(self)
        return dtmix.__lt__(self, x)
    
    def __le__(self, x):
        if isinstance(x, date) and not isinstance(x, _datetime):
            return x.__ge__(self)
        return dtmix.__le__(self, x)
    
    def __gt__(self, x):
        if isinstance(x, date) and not isinstance(x, _datetime):
            return x.__lt__(self)
        return dtmix.__gt__(self, x)
    
    def __ge__(self, x):
        if isinstance(x, date) and not isinstance(x, _datetime):
            return x.__le__(self)
        return dtmix.__ge__(self, x)
    
    def __eq__(self, x):
        if isinstance(x, date) and not isinstance(x, _datetime):
            return x.__eq__(self)
        return dtmix.__eq__(self, x)
    
    def strftime(self, fmt='%c'):
        try:
            return dtime.strftime(self, fmt)
        except ValueError, e:
            return None
    
    def Format(self, fmt=None):
        if fmt is None:
            fmt = FORMAT_DATETIME
        try:
            return dtime.strftime(self, fmt)
        except ValueError, e:
            return None
    
    def FormatANSI(self):
        return '%s-%s-%s %s:%s:%s' % (str(self.year).zfill(4), str(self.month).zfill(2), str(self.day).zfill(2), str(self.hour).zfill(2), str(self.minute).zfill(2), str(self.second).zfill(2))


# ------------------------------------------------------------------------------


import datetime
datetime.date = _date
datetime.datetime = _datetime


Date = datetime.date
DateTime = datetime.datetime
DateTimeDelta = datetime.timedelta


SECONDS_IN_MINUTE = 60
SECONDS_IN_HOUR =   SECONDS_IN_MINUTE*60
SECONDS_IN_DAY =    SECONDS_IN_HOUR*24


class DateTimeDiff(DateTimeDelta):
    
    def get_days(self):
        return int(self.seconds/SECONDS_IN_DAY)
    
    def get_hours(self):
        h = self.seconds/SECONDS_IN_HOUR
        if h>24:
            h = h % 24
        return h
    
    def get_minutes(self):
        m = self.seconds/SECONDS_IN_HOUR
        if m > 60:
            m = m % 60
        return m
    
    def get_seconds(self):
        s = self.seconds
        if s > 60:
            s = s % 60
        return s


today = datetime.date.today
now = datetime.datetime.now


if __name__ == '__main__':
    
    d1 = _date.today()
    d2 = _datetime.now()
    
    print 'd1=', d1, d1.__class__
    print 'd2=', d2, d2.__class__
    
    print d1 == d2
    print d1 > d2
    print d1 >= d2
    print d1 < d2
    print d1 <= d2

    print d2 == d1
    print d2 > d1
    print d2 >= d1
    print d2 < d1
    print d2 <= d1
