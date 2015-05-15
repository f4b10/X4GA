#!/usr/bin/python2
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Copyright (c) 2008-2011 Cédric Krier.
# Copyright (c) 2008-2011 B2CK.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

'''
Check the VAT number depending of the country based on formula from
http://sima-pc.com/nif.php
http://en.wikipedia.org/wiki/Vat_number
'''

__version__ = '0.5'
VIES_URL='http://ec.europa.eu/taxation_customs/vies/api/checkVatPort?wsdl'

def countries():
    '''
    Return the list of country's codes that have check function
    '''
    res = [x.replace('check_vat_', '').upper() for x in globals()
            if x.startswith('check_vat_')]
    res.sort()
    return res

def mult_add(i, j):
    '''
    Sum each digits of the multiplication of i and j.
    '''
    mult = i * j
    res = 0
    for i in range(len(str(mult))):
        res += int(str(mult)[i])
    return res

def check_vat_at(vat):
    '''
    Check Austria VAT number.
    '''
    if len(vat) != 9:
        return False
    if vat[0] != 'U':
        return False
    num = vat[1:]
    try:
        int(num)
    except ValueError:
        return False
    check_sum = int(num[0]) + mult_add(2, int(num[1])) + \
            int(num[2]) + mult_add(2, int(num[3])) + \
            int(num[4]) + mult_add(2, int(num[5])) + \
            int(num[6])
    check = 10 - ((check_sum + 4) % 10)
    if check == 10:
        check = 0
    if int(vat[-1:]) != check:
        return False
    return True

def check_vat_al(vat):
    '''
    Check Albania VAT number.
    '''
    if len(vat) != 10:
        return False
    if vat[0] not in ('J', 'K'):
        return False
    try:
        int(vat[1:9])
    except ValueError:
        return False
    if ord(vat[9]) < 65 and ord(vat[9]) > 90:
        return False
    return True

def check_vat_be(vat):
    '''
    Check Belgium VAT number.
    '''
    if len(vat) != 10:
        return False
    if vat[0] != '0':
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[-2:]) != \
            97 - (int(vat[:8]) % 97):
        return False
    return True

def check_vat_bg(vat):
    '''
    Check Bulgaria VAT number.
    '''
    if len(vat) == 9:
        #XXX don't know any rules for this length
        return True
    if len(vat) != 10:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0]) in (2, 3) and \
            int(vat[1:2]) != 22:
        return False
    check_sum = 4 * int(vat[0]) + 3 * int(vat[1]) + 2 * int(vat[2]) + \
            7 * int(vat[3]) + 6 * int(vat[4]) + 5 * int(vat[5]) + \
            4 * int(vat[6]) + 3 * int(vat[7]) + 2 * int(vat[8])
    check = 11 - (check_sum % 11)
    if check == 11:
        check = 0
    if check == 10:
        return False
    if check != int(vat[9]):
        return False
    return True

def check_vat_cl(rut):
    '''
    Check Chile RUT number.
    '''
    try:
        int(str(rut)[:len(str(rut))-1])
    except ValueError:
        return False
    sum = 0
    RUTLen = len(str(rut))
    for i in range (RUTLen - 2, -1, -1):
        sum += int(str(rut)[i]) * (((RUTLen - 2 - i) % 6) + 2)
    check = 11 - (sum % 11)
    if check == 11:
        return str(rut)[len(str(rut)) -1] == '0'
    elif check == 10:
        return str(rut)[len(str(rut)) -1].upper() == 'K'
    else:
        return str(check) == str(rut)[len(str(rut)) -1]

def check_vat_co(rut):
    '''
    Check Colombian RUT number.
    '''
    if len(str(rut)) != 10:
        return False
    try:
        int(rut)
    except ValueError:
        return False
    nums = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
    sum = 0
    RUTLen = len(str(rut))
    for i in range (RUTLen - 2, -1, -1):
        sum += int(str(rut)[i]) * nums [RUTLen - 2 - i]
    if sum % 11 > 1:
         return str(rut)[RUTLen - 1] == str(11 - (sum % 11))
    else:
         return str(rut)[RUTLen - 1] == str(sum % 11)

def check_vat_cy(vat):
    '''
    Check Cyprus VAT number.
    '''
    if len(vat) != 9:
        return False
    try:
        int(vat[:8])
    except ValueError:
        return False
    num0 = int(vat[0])
    num1 = int(vat[1])
    num2 = int(vat[2])
    num3 = int(vat[3])
    num4 = int(vat[4])
    num5 = int(vat[5])
    num6 = int(vat[6])
    num7 = int(vat[7])

    conv = {
        0: 1,
        1: 0,
        2: 5,
        3: 7,
        4: 9,
        5: 13,
        6: 15,
        7: 17,
        8: 19,
        9: 21,
    }

    num0 = conv.get(num0, num0)
    num2 = conv.get(num2, num2)
    num4 = conv.get(num4, num4)
    num6 = conv.get(num6, num6)

    check_sum = num0 + num1 + num2 + num3 + num4 + num5 + num6 + num7
    check = chr(check_sum % 26 + 65)
    if check != vat[8]:
        return False
    return True

def check_vat_cz(vat):
    '''
    Check Czech Republic VAT number.
    '''
    if len(vat) not in (8, 9, 10):
        return False
    try:
        int(vat)
    except ValueError:
        return False

    if len(vat) == 8:
        if int(vat[0]) not in (0, 1, 2, 3, 4, 5, 6, 7, 8):
            return False
        check_sum = 8 * int(vat[0]) + 7 * int(vat[1]) + 6 * int(vat[2]) + \
                5 * int(vat[3]) + 4 * int(vat[4]) + 3 * int(vat[5]) + \
                2 * int(vat[6])
        check = 11 - (check_sum % 11)
        if check == 10:
            check = 0
        if check == 11:
            check = 1
        if check != int(vat[7]):
            return False
    elif len(vat) == 9 and int(vat[0]) == 6:
        check_sum = 8 * int(vat[1]) + 7 * int(vat[2]) + 6 * int(vat[3]) + \
                5 * int(vat[4]) + 4 * int(vat[5]) + 3 * int(vat[6]) + \
                2 * int(vat[7])
        check = 9 - ((11 - (check_sum % 11)) % 10)
        if check != int(vat[8]):
            return False
    elif len(vat) == 9:
        if int(vat[0:2]) > 53 and int(vat[0:2]) < 80:
            return False
        if int(vat[2:4]) < 1:
            return False
        if int(vat[2:4]) > 12 and int(vat[2:4]) < 51:
            return False
        if int(vat[2:4]) > 62:
            return False
        if int(vat[2:4]) in (2, 52) and int(vat[0:2]) % 4 > 0:
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 28:
                return False
        if int(vat[2:4]) in (2, 52) and int(vat[0:2]) % 4 == 0:
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 29:
                return False
        if int(vat[2:4]) in (4, 6, 9, 11, 54, 56, 59, 61):
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 30:
                return False
        if int(vat[2:4]) in (1, 3, 5, 7, 8, 10, 12, 51,
                53, 55, 57, 58, 60, 62):
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 31:
                return False
    elif len(vat) == 10:
        if int(vat[0:2]) < 54:
            return False
        if int(vat[2:4]) < 1:
            return False
        if int(vat[2:4]) > 12 and int(vat[2:4]) < 51:
            return False
        if int(vat[2:4]) > 62:
            return False
        if int(vat[2:4]) in (2, 52) and int(vat[0:2]) % 4 > 0:
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 28:
                return False
        if int(vat[2:4]) in (2, 52) and int(vat[0:2]) % 4 == 0:
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 29:
                return False
        if int(vat[2:4]) in (4, 6, 9, 11, 54, 56, 59, 61):
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 30:
                return False
        if int(vat[2:4]) in (1, 3, 5, 7, 8, 10, 12, 51,
                53, 55, 57, 58, 60, 62):
            if int(vat[4:6]) < 1:
                return False
            if int(vat[4:6]) > 31:
                return False
        if (int(vat[0:2]) + int(vat[2:4]) + int(vat[4:6]) + int(vat[6:8]) +
                int(vat[8:10])) % 11 != 0:
            return False
        if int(vat[0:10]) % 11 != 0:
            return False
    return True

def check_vat_de(vat):
    '''
    Check Germany VAT number.
    '''
    if len(vat) != 9:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0:7]) <= 0:
        return False
    check_sum = 0
    for i in range(8):
        check_sum = (2 * ((int(vat[i]) + check_sum + 9) % 10 + 1)) % 11
    check = 11 - check_sum
    if check == 10:
        check = 0
    if int(vat[8]) != check:
        return False
    return True

def check_vat_dk(vat):
    '''
    Check Denmark VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0]) <= 0:
        return False
    check_sum = 2 * int(vat[0]) + 7 * int(vat[1]) + 6 * int(vat[2]) + \
            5 * int(vat[3]) + 4 * int(vat[4]) + 3 * int(vat[5]) + \
            2 * int(vat[6]) + int(vat[7])
    if check_sum % 11 != 0:
        return False
    return True

def check_vat_ee(vat):
    '''
    Check Estonia VAT number.
    '''
    if len(vat) != 9:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    check_sum = 3 * int(vat[0]) + 7 * int(vat[1]) + 1 * int(vat[2]) + \
            3 * int(vat[3]) + 7 * int(vat[4]) + 1 * int(vat[5]) + \
            3 * int(vat[6]) + 7 * int(vat[7])
    check = 10 - (check_sum % 10)
    if check == 10:
        check = 0
    if check != int(vat[8]):
        return False
    return True

def check_vat_es(vat):
    '''
    Check Spain VAT number.
    '''
    if len(vat) != 9:
        return False

    conv = {
        1: 'T',
        2: 'R',
        3: 'W',
        4: 'A',
        5: 'G',
        6: 'M',
        7: 'Y',
        8: 'F',
        9: 'P',
        10: 'D',
        11: 'X',
        12: 'B',
        13: 'N',
        14: 'J',
        15: 'Z',
        16: 'S',
        17: 'Q',
        18: 'V',
        19: 'H',
        20: 'L',
        21: 'C',
        22: 'K',
        23: 'E',
    }

    if vat[0] in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'J', 'U', 'V'):
        try:
            int(vat[1:])
        except ValueError:
            return False
        check_sum = mult_add(2, int(vat[1])) + int(vat[2]) + \
                mult_add(2, int(vat[3])) + int(vat[4]) + \
                mult_add(2, int(vat[5])) + int(vat[6]) + \
                mult_add(2, int(vat[7]))
        check = 10 - (check_sum % 10)
        if check == 10:
            check = 0
        if check != int(vat[8]):
            return False
        return True
    elif vat[0] in ('N', 'P', 'Q', 'R', 'S', 'W'):
        try:
            int(vat[1:8])
        except ValueError:
            return False
        check_sum = mult_add(2, int(vat[1])) + int(vat[2]) + \
                mult_add(2, int(vat[3])) + int(vat[4]) + \
                mult_add(2, int(vat[5])) + int(vat[6]) + \
                mult_add(2, int(vat[7]))
        check = 10 - (check_sum % 10)
        check = chr(check + 64)
        if check != vat[8]:
            return False
        return True
    elif vat[0] in ('K', 'L', 'M', 'X', 'Y', 'Z'):
        if vat[0] == 'Y':
            check_value = '1' + vat[1:8]
        elif vat[0] == 'Z':
            check_value = '2' + vat[1:8]
        else:
            check_value = vat[1:8]

        try:
            int(check_value)
        except ValueError:
            return False
        check = 1 + (int(check_value) % 23)

        check = conv[check]
        if check != vat[8]:
            return False
        return True
    else:
        try:
            int(vat[:8])
        except ValueError:
            return False
        check = 1 + (int(vat[:8]) % 23)

        check = conv[check]
        if check != vat[8]:
            return False
        return True

def check_vat_fi(vat):
    '''
    Check Finland VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    check_sum = 7 * int(vat[0]) + 9 * int(vat[1]) + 10 * int(vat[2]) + \
            5 * int(vat[3]) + 8 * int(vat[4]) + 4 * int(vat[5]) + \
            2 * int(vat[6])
    check = 11 - (check_sum % 11)
    if check == 11:
        check = 0
    if check == 10:
        return False
    if check != int(vat[7]):
        return False
    return True

def check_vat_fr(vat):
    '''
    Check France VAT number.
    '''
    if len(vat) != 11:
        return False

    try:
        int(vat[2:11])
    except ValueError:
        return False

    system = None
    try:
        int(vat[0:2])
        system = 'old'
    except ValueError:
        system = 'new'

    if system == 'old':
        check = ((int(vat[2:11]) * 100) + 12) % 97
        if check != int(vat[0:2]):
            return False
        return True
    else:
        conv = ['0', '1', '2', '3', '4', '5', '6', '7',
            '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
            'J', 'K', 'L', 'M', 'N', 'P', 'Q', 'R', 'S', 'T',
            'U', 'V', 'W', 'X', 'Y', 'Z']
        if vat[0] not in conv \
                or vat[1] not in conv:
            return False
        check1 = conv.index(vat[0])
        check2 = conv.index(vat[1])

        if check1 < 10:
            check_sum = check1 * 24 + check2 - 10
        else:
            check_sum = check1 * 34 + check2 - 100

        mod_x = check_sum % 11
        check_sum = (int(check_sum) / 11) + 1
        mod_y = (int(vat[2:11]) + check_sum) % 11
        if mod_x != mod_y:
            return False
        return True

def check_vat_gb(vat):
    '''
    Check United Kingdom VAT number.
    '''

    if len(vat) == 5:
        try:
            int(vat[2:5])
        except ValueError:
            return False

        if vat[0:2] == 'GD':
            if int(vat[2:5]) >= 500:
                return False
            return True
        if vat[0:2] == 'HA':
            if int(vat[2:5]) < 500:
                return False
            return True
        return False
    elif len(vat) in (9, 10):
        try:
            int(vat)
        except ValueError:
            return False

        if int(vat[0:7]) < 1:
            return False
        if int(vat[0:7]) > 19999 and int(vat[0:7]) < 1000000:
            return False
        if int(vat[7:9]) > 97:
            return False
        if len(vat) == 10 and int(vat[9]) != 3:
            return False

        check_sum = 8 * int(vat[0]) + 7 * int(vat[1]) + 6 * int(vat[2]) + \
                5 * int(vat[3]) + 4 * int(vat[4]) + 3 * int(vat[5]) + \
                2 * int(vat[6]) + 10 * int(vat[7]) + int(vat[8])
        if check_sum % 97 != 0:
            return False
        return True
    elif len(vat) in (12, 13):
        try:
            int(vat)
        except ValueError:
            return False

        if int(vat[0:3]) not in (0, 1):
            return False

        if int(vat[3:10]) < 1:
            return False
        if int(vat[3:10]) > 19999 and int(vat[3:10]) < 1000000:
            return False
        if int(vat[10:12]) > 97:
            return False
        if len(vat) == 13 and int(vat[12]) != 3:
            return False

        check_sum = 8 * int(vat[3]) + 7 * int(vat[4]) + 6 * int(vat[5]) + \
                5 * int(vat[6]) + 4 * int(vat[7]) + 3 * int(vat[8]) + \
                2 * int(vat[9]) + 10 * int(vat[10]) + int(vat[11])
        if check_sum % 97 != 0:
            return False
        return True
    return False

def check_vat_gr(vat):
    '''
    Check Greece VAT number.
    '''
    try:
        int(vat)
    except ValueError:
        return False
    if len(vat) == 8:
        check_sum = 128 * int(vat[0]) + 64 * int(vat[1]) + 32 * int(vat[2]) + \
                16 * int(vat[3]) + 8 * int(vat[4]) + 4 * int(vat[5]) + \
                2 * int(vat[6])
        check = check_sum % 11
        if check == 10:
            check = 0
        if check != int(vat[7]):
            return False
        return True
    elif len(vat) == 9:
        check_sum = 256 * int(vat[0]) + 128 * int(vat[1]) + 64 * int(vat[2]) + \
                32 * int(vat[3]) + 16 * int(vat[4]) + 8 * int(vat[5]) + \
                4 * int(vat[6]) + 2 * int(vat[7])
        check = check_sum % 11
        if check == 10:
            check = 0
        if check != int(vat[8]):
            return False
        return True
    return False

def check_vat_el(vat):
    '''
    Check Greece VAT number.
    '''
    return check_vat_gr(vat)

def check_vat_hu(vat):
    '''
    Check Hungary VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0]) <= 0:
        return False
    check_sum = 9 * int(vat[0]) + 7 * int(vat[1]) + 3 * int(vat[2]) + \
            1 * int(vat[3]) + 9 * int(vat[4]) + 7 * int(vat[5]) + \
            3 * int(vat[6])
    check = 10 - (check_sum % 10)
    if check == 10:
        check = 0
    if check != int(vat[7]):
        return False
    return True

def check_vat_ie(vat):
    '''
    Check Ireland VAT number.
    '''
    if len(vat) != 8:
        return False
    if (ord(vat[1]) >= 65 and ord(vat[1]) <= 90) \
            or vat[1] in ('+', '*'):
        try:
            int(vat[0])
            int(vat[2:7])
        except ValueError:
            return False

        if int(vat[0]) <= 6:
            return False

        check_sum = 7 * int(vat[2]) + 6 * int(vat[3]) + 5 * int(vat[4]) + \
                4 * int(vat[5]) + 3 * int(vat[6]) + 2 * int(vat[0])
        check = check_sum % 23
        if check == 0:
            check = 'W'
        else:
            check = chr(check + 64)
        if check != vat[7]:
            return False
        return True
    else:
        try:
            int(vat[0:7])
        except ValueError:
            return False

        check_sum = 8 * int(vat[0]) + 7 * int(vat[1]) + 6 * int(vat[2]) + \
                5 * int(vat[3]) + 4 * int(vat[4]) + 3 * int(vat[5]) + \
                2 * int(vat[6])
        check = check_sum % 23
        if check == 0:
            check = 'W'
        else:
            check = chr(check + 64)
        if check != vat[7]:
            return False
        return True

def check_vat_it(vat):
    '''
    Check Italy VAT number.
    '''
    vat=vat.rstrip()
    if len(vat) != 11:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    #===========================================================================
    # Controlli rimossi perchè non trovano correispondenza su indicazioni
    # ministeriali per il controllo della partita Iva.
    #===========================================================================
    # if int(vat[0:7]) <= 0:
    #     return False
    # if int(vat[7:10]) <= 0:
    #     return False
    # if int(vat[7:10]) > 100 and int(vat[7:10]) < 120:
    #     return False
    # if int(vat[7:10]) > 121:
    #     return False
    #===========================================================================

    check_sum = int(vat[0]) + mult_add(2, int(vat[1])) + int(vat[2]) + \
            mult_add(2, int(vat[3])) + int(vat[4]) + \
            mult_add(2, int(vat[5])) + int(vat[6]) + \
            mult_add(2, int(vat[7])) + int(vat[8]) + \
            mult_add(2, int(vat[9]))
    check = 10 - (check_sum % 10)
    if check == 10:
        check = 0
    if check != int(vat[10]):
        return False
    return True

def check_vat_lt(vat):
    '''
    Check Lithuania VAT number.
    '''
    try:
        int(vat)
    except ValueError:
        return False

    if len(vat) == 9:
        if int(vat[7]) != 1:
            return False
        check_sum = 1 * int(vat[0]) + 2 * int(vat[1]) + 3 * int(vat[2]) + \
                4 * int(vat[3]) + 5 * int(vat[4]) + 6 * int(vat[5]) + \
                7 * int(vat[6]) + 8 * int(vat[7])
        if check_sum % 11 == 10:
            check_sum = 3 * int(vat[0]) + 4 * int(vat[1]) + 5 * int(vat[2]) + \
                    6 * int(vat[3]) + 7 * int(vat[4]) + 8 * int(vat[5]) + \
                    9 * int(vat[6]) + 1 * int(vat[7])
        check = check_sum % 11
        if check == 10:
            check = 0
        if check != int(vat[8]):
            return False
        return True
    elif len(vat) == 12:
        if int(vat[10]) != 1:
            return False
        check_sum = 1 * int(vat[0]) + 2 * int(vat[1]) + 3 * int(vat[2]) + \
                4 * int(vat[3]) + 5 * int(vat[4]) + 6 * int(vat[5]) + \
                7 * int(vat[6]) + 8 * int(vat[7]) + 9 * int(vat[8]) + \
                1 * int(vat[9]) + 2 * int(vat[10])
        if check_sum % 11 == 10:
            check_sum = 3 * int(vat[0]) + 4 * int(vat[1]) + 5 * int(vat[2]) + \
                    6 * int(vat[3]) + 7 * int(vat[4]) + 8 * int(vat[5]) + \
                    9 * int(vat[6]) + 1 * int(vat[7]) + 2 * int(vat[8]) + \
                    3 * int(vat[9]) + 4 * int(vat[10])
        check = check_sum % 11
        if check == 10:
            check = 0
        if check != int(vat[11]):
            return False
        return True
    return False

def check_vat_lu(vat):
    '''
    Check Luxembourg VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0:6]) <= 0:
        return False
    check = int(vat[0:6]) % 89
    if check != int(vat[6:8]):
        return False
    return True

def check_vat_lv(vat):
    '''
    Check Latvia VAT number.
    '''
    if len(vat) != 11:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0]) >= 4:
        check_sum = 9 * int(vat[0]) + 1 * int(vat[1]) + 4 * int(vat[2]) + \
                8 * int(vat[3]) + 3 * int(vat[4]) + 10 * int(vat[5]) + \
                2 * int(vat[6]) + 5 * int(vat[7]) + 7 * int(vat[8]) + \
                6 * int(vat[9])
        if check_sum % 11 == 4 and int(vat[0]) == 9:
            check_sum = check_sum - 45
        if check_sum % 11 == 4:
            check = 4 - (check_sum % 11)
        elif check_sum % 11 > 4:
            check = 14 - (check_sum % 11)
        elif check_sum % 11 < 4:
            check = 3 - (check_sum % 11)
        if check != int(vat[10]):
            return False
        return True
    else:
        if int(vat[2:4]) == 2 and int(vat[4:6]) % 4 > 0:
            if int(vat[0:2]) < 1 or int(vat[0:2]) > 28:
                return False
        if int(vat[2:4]) == 2 and int(vat[4:6]) % 4 == 0:
            if int(vat[0:2]) < 1 or int(vat[0:2]) > 29:
                return False
        if int(vat[2:4]) in (4, 6, 9, 11):
            if int(vat[0:2]) < 1 or int(vat[0:2]) > 30:
                return False
        if int(vat[2:4]) in (1, 3, 5, 7, 8, 10, 12):
            if int(vat[0:2]) < 1 or int(vat[0:2]) > 31:
                return False
        if int(vat[2:4]) < 1 or int(vat[2:4]) > 12:
            return False
        return True

def check_vat_mt(vat):
    '''
    Check Malta VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False

    if int(vat[0:6]) < 100000:
        return False

    check_sum = 3 * int(vat[0]) + 4 * int(vat[1]) + 6 * int(vat[2]) + \
            7 * int(vat[3]) + 8 * int(vat[4]) + 9 * int(vat[5])
    check = 37 - (check_sum % 37)
    if check != int(vat[6:8]):
        return False
    return True

def check_vat_nl(vat):
    '''
    Check Netherlands VAT number.
    '''
    if len(vat) != 12:
        return False
    try:
        int(vat[0:9])
        int(vat[10:12])
    except ValueError:
        return False
    if int(vat[0:8]) <= 0:
        return False
    if vat[9] != 'B':
        return False

    check_sum = 9 * int(vat[0]) + 8 * int(vat[1]) + 7 * int(vat[2]) + \
            6 * int(vat[3]) + 5 * int(vat[4]) + 4 * int(vat[5]) + \
            3 * int(vat[6]) + 2 * int(vat[7])

    check = check_sum % 11
    if check == 10:
        return False
    if check != int(vat[8]):
        return False
    return True

def check_vat_pl(vat):
    '''
    Check Poland VAT number.
    '''
    if len(vat) != 10:
        return False
    try:
        int(vat)
    except ValueError:
        return False

    check_sum = 6 * int(vat[0]) + 5 * int(vat[1]) + 7 * int(vat[2]) + \
            2 * int(vat[3]) + 3 * int(vat[4]) + 4 * int(vat[5]) + \
            5 * int(vat[6]) + 6 * int(vat[7]) + 7 * int(vat[8])
    check = check_sum % 11
    if check == 10:
        return False
    if check != int(vat[9]):
        return False
    return True

def check_vat_pt(vat):
    '''
    Check Portugal VAT number.
    '''
    if len(vat) != 9:
        return False
    try:
        int(vat)
    except ValueError:
        return False

    if int(vat[0]) <= 0:
        return False

    check_sum = 9 * int(vat[0]) + 8 * int(vat[1]) + 7 * int(vat[2]) + \
            6 * int(vat[3]) + 5 * int(vat[4]) + 4 * int(vat[5]) + \
            3 * int(vat[6]) + 2 * int(vat[7])
    check = 11 - (check_sum % 11)
    if check == 10 or check == 11:
        check = 0
    if check != int(vat[8]):
        return False
    return True

def check_vat_ro(vat):
    '''
    Check Romania VAT number.
    '''
    try:
        int(vat)
    except ValueError:
        return False

    if len(vat) >= 2 and len(vat) <= 10:
        vat = (10 - len(vat)) * '0' + vat
        check_sum = 7 * int(vat[0]) + 5 * int(vat[1]) + 3 * int(vat[2]) + \
                2 * int(vat[3]) + 1 * int(vat[4]) + 7 * int(vat[5]) + \
                5 * int(vat[6]) + 3 * int(vat[7]) + 2 * int(vat[8])
        check = (check_sum * 10) % 11
        if check == 10:
            check = 0
        if check != int(vat[9]):
            return False
        return True
    elif len(vat) == 13:
        if int(vat[0]) not in (1, 2, 3, 4, 6):
            return False
        if int(vat[3:5]) < 1 or int(vat[3:5]) > 12:
            return False
        if int(vat[3:5]) == 2 and int(vat[1:3]) % 4 > 0:
            if int(vat[5:7]) < 1 or int(vat[5:7]) > 28:
                return False
        if int(vat[3:5]) == 2 and int(vat[1:3]) % 4 == 0:
            if int(vat[5:7]) < 1 or int(vat[5:7]) > 29:
                return False
        if int(vat[3:5]) in (4, 6, 9, 11):
            if int(vat[5:7]) < 1 or int(vat[5:7]) > 30:
                return False
        if int(vat[3:5]) in (1, 3, 5, 7, 8, 10, 12):
            if int(vat[5:7]) < 1 or int(vat[5:7]) > 31:
                return False

        check_sum = 2 * int(vat[0]) + 7 * int(vat[1]) + 9 * int(vat[2]) + \
                1 * int(vat[3]) + 4 * int(vat[4]) + 6 * int(vat[5]) + \
                3 * int(vat[6]) + 5 * int(vat[7]) + 8 * int(vat[8]) + \
                2 * int(vat[9]) + 7 * int(vat[10]) + 9 * int(vat[11])
        check = check_sum % 11
        if check == 10:
            check = 1
        if check != int(vat[12]):
            return False
        return True
    return False

def check_vat_se(vat):
    '''
    Check Sweden VAT number.
    '''
    if len(vat) != 12:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[9:11]) <= 0:
        return False

    check_sum = mult_add(2, int(vat[0])) + int(vat[1]) + \
            mult_add(2, int(vat[2])) + int(vat[3]) + \
            mult_add(2, int(vat[4])) + int(vat[5]) + \
            mult_add(2, int(vat[6])) + int(vat[7]) + \
            mult_add(2, int(vat[8]))
    check = 10 - (check_sum % 10)
    if check == 10:
        check = 0
    if check != int(vat[9]):
        return False
    return True

def check_vat_si(vat):
    '''
    Check Slovenia VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    if int(vat[0:7]) <= 999999:
        return False

    check_sum = 8 * int(vat[0]) + 7 * int(vat[1]) + 6 * int(vat[2]) + \
            5 * int(vat[3]) + 4 * int(vat[4]) + 3 * int(vat[5]) + \
            2 * int(vat[6])
    check = 11 - (check_sum % 11)
    if check == 10:
        check = 0
    if check == 11:
        check = 1
    if check != int(vat[7]):
        return False
    return True

def check_vat_sk(vat):
    '''
    Check Slovakia VAT number.
    '''
    try:
        int(vat)
    except ValueError:
        return False
    if len(vat) not in(9, 10):
        return False

    if int(vat[0:2]) == 0 and len(vat) == 10:
        return True

    if len(vat) == 10:
        if int(vat[0:2]) < 54 or int(vat[0:2]) > 99:
            return False

    if len(vat) == 9:
        if int(vat[0:2]) > 53 :
            return False

    if int(vat[2:4]) < 1:
        return False
    if int(vat[2:4]) > 12 and int(vat[2:4]) < 51:
        return False
    if int(vat[2:4]) > 62:
        return False
    if int(vat[2:4]) in (2, 52) and int(vat[0:2]) % 4 > 0:
        if int(vat[4:6]) < 1 or int(vat[4:6]) > 28:
            return False
    if int(vat[2:4]) in (2, 52) and int(vat[0:2]) % 4 == 0:
        if int(vat[4:6]) < 1 or int(vat[4:6]) > 29:
            return False
    if int(vat[2:4]) in (4, 6, 9, 11, 54, 56, 59, 61):
        if int(vat[4:6]) < 1 or int(vat[4:6]) > 30:
            return False
    if int(vat[2:4]) in (1, 3, 5, 7, 8, 10, 12,
            51, 53, 55, 57, 58, 60, 62):
        if int(vat[4:6]) < 1 or int(vat[4:6]) > 31:
            return False
    return True

def check_vat_sm(vat):
    '''
    Check San Marino VAT number.
    '''
    if len(vat) != 5:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    return True

def check_vat_ua(vat):
    '''
    Check Ukraine VAT number.
    '''
    if len(vat) != 8:
        return False
    try:
        int(vat)
    except ValueError:
        return False
    return True

def check_vat_uk(vat):
    '''
    Check United Kingdom VAT number.
    '''
    return check_vat_gb(vat)

def check_vies(vat):
    '''
    Check VAT number for EU member state using the SOAP Service
    '''
    from SOAPpy import WSDL
    code = vat[:2]
    number = vat[2:]
    server = WSDL.Proxy(VIES_URL)
    res = server.checkVat(code, number)
    return bool(res['valid'])
