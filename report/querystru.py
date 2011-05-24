#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         report/querystru.py
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

_debug=0

class QueryStru:
    '''
    La classe consente di acquisire informazioni sulla struttura dei campi
    della query su cui poggia il report.
    @cVar Struttura: conserva la lista passata alla classe all'atto della creazione.
    @type Struttura: lista
    '''
    #Struttura=None
    def __init__(self, DbStru):
        """
        Riceve come parametro la struttura di tutti i campi che compaiono nella query. 
        B{DbStru} è infatti costituita da una lista di elementi in cui ogni singolo elemento è 
        a sua volta costituito da una lista contenente le caratteristiche del campo a cui si riferisce. 
        
        Le informazioni presenti in ogni singolo elemento della lista DbStru sono le seguenti:
            - name
            - type_code
            - display_size
            - internal_size
            - precision
            - scale
            - null_ok
        @type DbStru: lista
        """
        self.Struttura=DbStru
        if _debug==1:
            print
            print "Struttura query"
            print "=================================="
            for r in self.Struttura:
                print r
            print "=================================="

    def get_FieldCount(self):
        '''
        Restituisce il numero dei campi  presenti nella query
        @return: numero totale dei campi nella query
        @rtype: int
        '''
        return int(len(self.Struttura))
        
    def get_FieldName(self, Index):
        '''
        Restituisce il nome del campo che compare in posizione Index nell'ambito
        della struttura della Query
        @param Index: Posizione del campo nell'ambito della struttura.
        @type Index: int
        @return: nome del campo.
        @rtype: string
        '''
        return self.Struttura[Index][0]

    def get_FieldType(self, Index):
        '''
        Restituisce il tipo del campo che compare in posizione Index nell'ambito
        della struttura della Query
        @param Index: Posizione del campo nell'ambito della struttura.
        @type Index: int
        @return: tipo del campo espresso secondo la seguente tabella di corrispondenza:
            
            - 0   NUMERIC
            - 0   DECIMAL
            - 1   BOOL
            - 2   SMALLINT
            - 3   INTEGER
            - 3   INT
            - 4   FLOAT
            - 5   DOUBLE
            - 5   REAL
            - 7   TIMESTAMP
            - 8   BIGINT
            - 9   MEDIUMINT
            - 10  DATE
            - 11  TIME
            - 12  DATETIME
            - 13  YEAR
            - 252 LONGTEXT
            - 252 MEDIUMTEXT
            - 252 TEXT
            - 252 TINYTEXT
            - 252 LONGBLOB
            - 252 MEDIUMBLOB
            - 252 BLOB
            - 252 TINYBLOB
            - 253 VARCHAR
            - 254 CHAR

        @rtype: int
        '''
        return self.Struttura[Index][1]
    
    
    def get_IndexbyName(self, Name):
        '''
        Restituisce la posizione, nell'ambito della struttura,  in cui compare il 
        campo con none Name. Nell'eventualità che non fosse presente alcun campo
        con il nome specificato viene restituiro None.
        @param Name: Nome del campo ricercato
        @type Name: string
        @return: posizione del campo nell'ambito della struttura
        @rtype: int
        '''
        Index=0
        for element in self.Struttura:
            if element[0]==Name:
                return Index
            Index=Index+1
        return None
     
