#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         crypt.py
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

from Crypto.Cipher import DES3
from random import randint

DES3LEN = 24


def complete(string, number=DES3LEN):
    #verica se la stringa e' un multiplo della variabile number
    #altresi' incrementa la stringa con caratteri casuali
    h = divmod(len(string), number)
    if h[-1] != 0:
        string += '\021'
        if (number-h[1]) > 1:
            # Genera la sequenza di caratteri casuali
            for x in range(1, number-h[1]):
                string += chr(randint(0, 255))
    return string

def encrypt_data(string):
    obj = DES3.new(password, crypt_type)
    return obj.encrypt(complete(string))

def decrypt_data(string):
    obj = DES3.new(password, crypt_type)
    return obj.decrypt(string).split('\021')[0]


crypt_type = DES3.MODE_ECB
password = '(:x4:)'*4


if __name__ == '__main__':
    password = complete(password)
    a = encrypt_data('TUTTO FUNZIONA CORRETTAMENTE')
    b = encrypt_data('TUTTO FUNZIONA CORRETTAMENTE')
    print 'Le stringhe crittate sono uguali?', a == b
    print decrypt_data(a), decrypt_data(b)
    print '-----------'
    pwd = 'passorig'
    pwd1 = encrypt_data(pwd)
    pwd2 = decrypt_data(pwd1)
    print " Original password: *%s*" % pwd
    print "  Crypted password: *%s*" % pwd1
    print "Decrypted password: *%s*" % pwd2
    
    #f = open('test.pwd', 'wb')
    #f.write(encrypt_data('fabio0'))
    #f.close()
    #print 'done'
