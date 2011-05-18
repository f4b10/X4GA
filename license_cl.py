#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         license_cl.py
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

from reportlab.tools.docco.rl_doc_utils import *
import reportlab

H1.alignment = 0
H1.fontSize = 8
H1.spaceBefore = 4
H1.spaceAfter = 0
H1.leading = 8

text_content = []

def heading1(text):
    p = Paragraph('<seq id="Chapter"/>) ' + quickfix(text), H1)
    getStory().append(p)
    text_content.append(["H3", text])

import copy
H0 = copy.deepcopy(H1)

H0.alignment = 1
H0.fontSize = 10
H0.spaceBefore = 4
H0.spaceAfter = 0
H0.leading = 12
H0.name = 'Heading0'

def heading0(text):
    p = Paragraph(quickfix(text), H0)
    getStory().append(p)
    text_content.append(["H2", text])

def disc(text, klass=Paragraph, style=discussiontextstyle):
    text = quickfix(text)
    p = klass(text, style)
    p.style.spaceBefore = 0
    p.style.spaceAfter = 0
    p.style.fontSize = 7
    p.style.leading = 7
    p.style.alignment = 4 #giustificato
    getStory().append(p)
    text_content.append(["B", text])


disc("""""")
disc("""Premesse:""")
disc("""a) Si definisce "Cliente" l'intestatario della presente Licenza d'uso, 
le cui generalita' sono riportate sul modulo stampato e dal Cliente 
controfirmato.""")
disc("""b) Si definisce "Produttore" la Astra S.r.l. con sede in 
C.so Cavallotti, 122 - 18038 Sanremo (IM) Italy.""")
disc("""c) Il presente contratto e' valido solo dopo l'accettazione da parte 
del Produttore ed il diligente rispetto delle istruzioni per la compilazione 
riportate sul modulo stampato della licenza d'uso.""")
disc("""Tutto cio' premesso, tra il Produttore ed il Cliente si conviene il 
presente contratto di Concessione di Licenza d'uso che il Cliente sottoscrive 
per l'accettazione, alle seguenti:""")

heading0("CONDIZIONI GENERALI DI LICENZA D'USO DI PRODOTTI PROGRAMMA")

heading1("PREMESSE E GENERALITA'")
disc("""Le premesse e le Generalita' sopra riportate costituiscono parte 
integrante del presente contratto.""")

heading1("OGGETTO DEL CONTRATTO")
disc("""Oggetto del presente contratto e' la concessione da parte del 
Produttore al Cliente di UNA licenza non esclusiva e non trasferibile per 
l'uso dei/del prodotti/prodotto programma di cui in calce vengono riportati 
gli estremi, costituito dalle informazioni contenute nel supporto di
installazione, dalla documentazione d'uso e qualsiasi altro materiale 
relativo.""")

heading1("FINALITA'")
disc("""Il Cliente dichiara di stipulare il presente contratto per l'uso 
IN PROPRIO dei/del prodotti/prodotto programma di cui in calce, ogni altro 
uso viene quindi espressamente vietato.""")

heading1("CONDIZIONI")
disc("""La licenza d'uso di cui all'oggetto e gli eventuali aggiornamenti 
vengono ceduti o rilasciati alle condizioni economiche stabilite con apposito 
modulo d'ordine.""")

heading1("RESPONSABILITA'")
disc("""Il Cliente e' responsabile dell'uso per fini propri o di terzi, 
della verifica, del funzionamento e della idoneita' dei programmi al fine 
del raggiungimento dei risultati dallo stesso voluti.  Il Produttore non si 
assume alcuna responsabilita' inerente malfunzionamenti o non idoneita' del 
prodotto programma oggetto del contratto.""")

heading1("GARANZIA LIMITATA")
disc("""Il Produttore garantisce di avere eseguito i normali test diagnostici 
di funzionamento dei prodotti programma correttamente installati sulle 
apparecchiature funzionanti e dotate degli adeguati sistemi operativi come 
descritto nelle informazioni commerciali.  Il Produttore non puo' comunque 
garantire che i prodotti programma, siano esenti all'origine da alcun vizio 
o difetto, o che soddisfino le esigenze del Cliente.  Il Cliente ha il 
diritto, per la rimozione di ogni errore riscontrato entro 90 giorni dalla 
data di stipula del contratto di licenza d'uso, alla fornitura di aggiornamenti 
senza nessun addebito, tranne le spese e le prestazioni di assistenza, 
sempre che il Produttore non decida di restituire l'importo pagato e 
risolvere il contratto di licenza d'uso stipulato.  Entro tale periodo di 
90 giorni, il Cliente ha comunque il diritto di restituire tutto il materiale 
ricevuto e a richiedere la restituzione dell'importo pagato per i prodotti 
programma, a fronte di una dichiarazione di cessazione totale dell'utilizzo.""")

heading1("AGGIORNAMENTI")
disc("""Il Cliente, che sottoscrivera' per la richiesta di aggiornamenti, 
avra' diritto a ricevere ogni aggiornamento che il produttore vorra' 
realizzare relativamente ai prodotti programma in calce riportati.
Gli aggiornamenti verranno predisposti dal produttore per: a) rilasciare 
eventuali nuove versioni del programma; b) eliminare eventuali difetti e/o 
malfunzionamenti che siano stati opportunamente segnalati e documentati al 
produttore.  Ogni aggiornamento o versione successiva dei prodotti programma 
diventeranno parte integrante del modulo iniziale e saranno pertanto soggetti 
a tutte le clausole della presente licenza d'uso.  Nel caso il Cliente non 
avesse sottoscritto la richiesta di aggiornamenti, potra' ottenere l'ultima 
versione rilasciata dal produttore mediante la corresponsione dei canoni di 
aggiornamento arretrati.  Il Cliente ed il produttore, entrambi, hanno il 
diritto di richiedere la cessazione del serviziodi aggiornamento in qualsiasi 
momento, comunicando la recessione con lettera raccomandata almento 30 giorni 
prima della scadenza.  In questo caso il Cliente potra' mantenere la 
condizione di licenza d'uso della versione in suo possesso o richiedere la 
risoluzione definitiva del contratto.
Il servizio di aggiornamento e' offerto dal produttore nel periodo dell'anno 
solare.  Nel caso di stipule infrannuali, il contrato avra' comunque scadenza 
il 31 dicembre dell'anno considerato e la quota relativa sara' in funzione dei 
dodicesimi mancanti al 31 dicembre.""")

heading1("SOSPENSIONE DEGLI AGGIORNAMENTI")
disc("""Il ritardato o mancato pagamento del canone di Aggiornamento Programmi 
causa l'immediata sospensione del servizio previsto dal presente contratto, 
fino alla definitiva definizione delle parti sospese.""")

heading1("SVILUPPO DI APPLICAZIONI")
disc("""Il produttore potra' sviluppare applicazioni personalizzate, ovvero 
modifiche ai prodotti programma oggetto della presente licenza d'uso, su 
ordine e/o commessa del Cliente o del Distributore.  La proprieta', salvo 
diverso accordo scritto, di queste applicazioni rimarra' in capo al produttore, 
il Cliente ne acquisira' la licenza illimitata ma non trasferibile a terzi e 
non esclusiva.  Il prezzo stabilito per lo sviluppo non comprende 
l'installazione e l'avviamento, che saranno regolate secondo le tariffe 
in vigore.  La garanzia da' diritto alla rimozione di errori entro 90 giorni 
dalla data di consegna del prodotto programma e non comprende gli interventi 
presso il Cliente e/o il Distributore.  I prodotti programma sviluppati su 
commessa si rifanno comunque alle condizioni generali di licenza d'uso 
riportate nella presente richiesta di licenza d'uso.""")

heading1("ASSISTENZA APPLICATIVA")
disc("""Il Cliente e/o Distributore potra' richiedere al produttore servizi 
di assistenza applicativa e hot line, tali servizi saranno regolati alle 
tariffe in vigore.  Il produttore si riserva di rifiutare tale richiesta e 
comunque non puo' garantire che tali servizi possano risolvere 
malfunzionamenti delle procedure.  Al termine di ogni intervento sulle 
procedure installate presso il Cliente sara' cura dello stesso Cliente 
accertare il corretto funzionamento delle stesse.""")

heading1("RESPONSABILITA' DEL PRODUTTORE")
disc("""Salvo in caso di dolo, il fornitore esclude specificatamente ogni 
qualsiasi forma di responsabilita' per danni diretti e indiretti che il 
Cliente o terzi possano in alcun modo subire conseguentemente all'uso o alla 
incapacita' di usare i prodotti programma.  In deroga a quanto previsto dagli 
articoli 1578 e segg. C.C., il produttore non risponde di danni derivanti al 
Cliente anche per vizi originari o sopravvenuti dei prodotti programma.  
Il Cliente dichiara di aver esaminato, attentamente tutte le elaborazioni e 
le stampe ottenibili dai prodotti programma e di averli trovati aderenti agli 
scopi che si prefigge.""")

heading1("FORNITURA DEI PRODOTTI E SERVIZI")
disc("""La fornitura dei prodotti programma e degli eventuali aggiornamenti 
saranno effettuati a cura del distributore e/o del rivenditore sulla base di 
autonomo contratto di licenza d'uso, manutenzione e fornitura di servizi 
applicativi, indicante prezzi, canoni, tariffe, modalita' di fornitura e 
pagamento, sulla base del proprio listino.""")

heading1("SPESE")
disc("""Sono a carico del Cliente le spese di spedizione nonche' i supporti 
su cui sono registrati i prodotti programma, anche in caso di errori.""")

heading1("DURATA")
disc("""Il presente contratto di licenza d'uso ha durata a tempo 
indeterminato.  La licenza d'uso si riferisce unicamente alla versione 
indicata nel presente contratto, tranne nel caso in cui il Cliente faccia 
espressa richiesta di rilascio di aggiornamenti sottoscrivendo tale richiesta 
nell'apposito spazio.  Qualora il Cliente volesse recedere validamente dal 
presente contratto dovra' darne comunicazione scritta al produttore tramite 
lettera raccomandata R.R. attestante l'avvenuta distruzione e la restituzione 
di tutto il materiale ricevuto.""")

heading1("INADEMPIMENTI PER CREDITI")
disc("""Qualora il Cliente divenisse inadempiente nei confronti del 
Distributore e/o Produttore, per pagamenti non eseguiti alle scadenze 
previste e per qualsivoglia ragione il Produttore e/o il Distributore 
avra' facolta' di interrompere la fornitura degli aggiornamenti, compresi 
la correzione di errori anche in periodo di garanzia.  Avra' altresi' la 
facolta' di interrompere qualsiasi tipo di servizio.""")

heading1("ACCETTAZIONE DELLA LICENZA D'USO")
disc("""Il Cliente conferma di aver letto il testo del presente contratto 
compresi i termini e le clausole, accettandolo come unico ed esclusivo 
accordo tra le parti.""")

heading1("FORO COMPETENTE E LEGGE APPLICABILE")
disc("""Il presente contratto si uniforma con le leggi in vigore nella 
Repubblica Italiana alla data di stipulazione dello stesso; nel caso in cui 
vi fossero emanazioni di leggi o decreti che rendessero invalidata o 
inapplicabile una qualsiasi clausola o termine, resta inteso che il resto 
del presente contratto resta in vigore.  Per quanto non previsto dal 
presente contratto, si fa riferimento alla normativa vigente in termini 
di diritti d'autore, brevetti e marchi.  Per qualsiasi controversia 
sara' competente in via esclusiva il foro di Sanremo.""")


def tab(data):
    t = Table(data, colWidths=282)
    t.setStyle(TableStyle([('ALIGN',(-1, 0),(-1, 0), 'CENTER'),
                           ('ALIGN',(-1,-1),(-1,-1), 'RIGHT'),]))
    getStory().append(t)

tab(data = [["Data", "Timbro e firma"],
            ["_"*16, "_"*52]])
        

heading1("CLAUSOLA RISOLUTIVA")
disc("""Ai sensi e per gli effetti degli artt. 1341 e 1342 C.C.
si approvano espressamente le condizioni e patuizioni contenute negli articoli: 
2 (Oggetto del Contratto), 3 (Finalita'), 4 (Condizioni), 5 (Responsabilita'),
6 (Garanzia Limitata), 7 (Aggiornamenti), 8 (Sospensione degli aggiornamenti),
9 (Sviluppo Applicazioni), 10 (Assistenza Applicativa), 11 (Responsabilita' del
Produttore), 12 (Fornitura dei Prodotti Programma), 13 (Spese), 14 (Durata), 
15 (Inadempimenti per Crediti), 16 (Accettazione della Licenza d'Uso),
17 (Foro competente e Legge Applicabile).""")

tab(data = [["Timbro e firma per richiesta aggiornamenti", "Timbro e firma per approvazione clausola risolutiva"],
            ["_"*52, "_"*52]])


heading1("Consenso ai sensi del D.LGS. 196/03 (Privacy)")
disc("""In esecuzione dell'art. 23 del D. Lgs. 196/03, recante disposizioni 
a tutela delle persone e degli altri soggetti rispetto al trattamento dei 
dati personali, il Richiedente fornisce il consenso al trattamento dei propri 
dati personali, direttamente o anche attraverso terzi, oltre che per 
l'integrale esecuzione del contratto o per ottemperare ad obblighi previsti 
dalla legge, da un regolamento o dalla normativa comunitaria, anche per le 
seguenti finalita': elaborare studi, ricerche statistiche e di mercato; 
inviare materiale pubblicitario ed informativo; compiere attivita' dirette 
di vendita o di collocamento di prodotti o servizi; inviare informazioni 
commerciali; effettuare comunicazioni commerciali interattive.""")
disc("""In ogni momento, a norma dell'art. 7 del citato D. Lgs. 196/03, 
il Richiedente potra' avere accesso ai propri dati, richiederne la modifica 
o la cancellazione, oppure opporsi al loro utilizzo se non essenziali per 
l'esecuzione del contratto, mediante richiesta scritta.  
Il titolare del Trattamento a' la Astra S.r.l., ed il Responsabile del Trattamento 
e' il suo Legale Rappresentante.""")
disc("""Nel caso in cui il Richiedente opti per il No, significa che lo 
stesso ha prestato il proprio consenso solamente per l'integrale esecuzione 
del presente Contratto.""")

tab(data = [["SI/NO", "Timbro e firma per consenso privacy"],
            ["_"*16, "_"*52]])
