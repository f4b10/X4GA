#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         docs/install/ch1_intro.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
# Created:      2007/11/07
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

from reportlab.tools.docco.rl_doc_utils import *
import reportlab

import sys
sys.path.append('../..')
import version as ver

title("X4 Gestione Aziendale")
title("Manuale di installazione")
centred('X4 Versione ' + ver.__version__)

nextTemplate("Normal")

################################################################################
###                                                                          ###
###                              CAPITOLO 1                                  ###
###                                                                          ###
################################################################################


heading1("Introduzione")


heading2("Note riguardanti questo documento")
disc("""
Questo documento descrive il processo di installazione di X4.
E' richiesta una minima familiarità con il sistema operativo e la conoscenza
di base di MySQL.
""")

disc("""In questo capitolo, saranno affrontati i seguenti punti:""")
bullet("Cosa è esattamente X4?")
bullet("Cosa è necessario installare per rendere operativo X4?")
bullet("Comeprocedere con la prima installazione di X4?")

disc("")
todo("""
X4 è un software giovane ed in continua evoluzione, cosi' come la sua 
documentazione.  Per rendere entrambi migliori, apprezziamo la segnalazione di 
qualsiasi errore, anomalia o informazione non esatta o parziale contenuta nel
manuale.  Le segnalazioni e/o richieste possono essere inviate ad Astra 
mediante l'apposita sezione sul portale del prodotto, 
<a href="http://www.x4ga.com/feedback/">www.x4ga.com</a>.
""")

heading2("Cosa è esattamente X4?")
disc("""
X4 è un programma di gestione aziendale.  X4 aiuta l'azienda nell'operatività
quotidiana, negli adempimenti fiscali e nelle valutazioni contabili, logistiche
ed amministrative.
Con X4 si puo':""")
bullet("Gestire la contabilità in modo agevole e veloce")
bullet("Emettere documenti dal magazzino con la possibilità di contabilizzarli automaticamente")
bullet("Gestire il carico/scarico del magazzino, gli ordini clienti e gli ordini fornitori")
buffer("Gestire i debiti e crediti dei clienti e fornitori")
