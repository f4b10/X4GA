#!/bin/env python
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name:         versionchanges.py
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
Riepilogo dei cambiamenti apportati alla versione
"""

import mx.DateTime as dt

history = (
    
    ('1.3.12', None, (
         ("BUG1077",
         """Correzione bug in liquidazione iva, il suo richiamo originava eccesione
         in seguito ad test della periodicità non allineato alla nuova struttura
         dati in unicode."""),
        ),),
    
    ('1.3.12', None, (
         ("BUG1074",
         """Correzione immissione date: in alcuni casi compilava automaticamente
         l'anno della data in digitazione."""),
         ("BUG1075",
         """Correzione immissione valori in griglia: la digitazione del primo 
         carattere della cella, se la cella non era ancora in fase di editazione,
         causava una eccezione se il tasto digitato era un carattere particolare
         non facente parte della codifica ascii (lettere accentate, simbolo 
         dell'euro, ecc)."""),
         ("BUG1076",
         """Correzione immissione valori data in griglia: dopo attivazione 
         editazione cella, sia abbandonando con il tasto ESC che uscendo dalla
         cella con il tasto TAB con valore vuoto, la griglia perdeva il focus di 
         tastiera, costringendo l'utente all'uso del mouse per il riposizionamento
         sulla griglia stessa."""),
        ),),
    
    ('1.3.11', None, (
         ("BET1096",
         """Ottimizzate le dimensioni delle finestre dei dataentry contabili
         e razionalizzate le griglie contenute (tolti gli ancoraggi alle 
         colonne)."""),
        ),),
    
    ('1.3.10', None, (
         ("BUG1073",
         """Correzione bug nell'impostazione di valori numerici, comparso 
         nella versione 1.3.07."""),
        ),),
    
    ('1.3.09', None, (
         ("BUG1072",
         """Indagine crash in chiusura applicazione, riutilizzo della
         libreria wx versione 2.8.10.1 (unicode)."""),
        ),),
    
    ('1.3.08', None, (
         ("BET1095",
         """Migliorata la creazione di nuova azienda con la creazione
         automatica dei progressivi contabili e messaggio finale per il 
         completamento manuale del setup dell'azienda."""),
        ),),
    
    ('1.3.07', None, (
         ("BUG1071",
         """Correzione chiusure contabili nel caso di chiusura di esercizio
         in perdita."""),
         ("BET1093",
         """Ottimizzata la finestra delle chiusure contabili."""),
         ("BET1094",
         """Ottimizzata la finestra dei bilanci."""),
        ),),
    
    ('1.3.06', None, (
         ("BET1092",
         """Ottimizzata la finestra e la griglia dell'emissione effetti."""),
        ),),
    
    ('1.3.05', None, (
         ("BET1091",
         """Adozione di utf-8 come unico charset in tutta l'applicazione e
         nel database."""),
        ),),
    
    ('1.3.04', dt.Date(2011,5,18), (
         ("BET1090",
         """Rilascio ufficiale su piattaforma Linux. Ora X4 è anche open!"""),
        ),),
    
    ('1.3.01', None, (
         ("BUG1070",
         """Ripristinate le stampe di riepilogo delle aliquote iva dalla funzione
         di liquidazione, sia per registro che per tipo di registro: erano 
         diventate inacessibili dalla versione 1.2.90."""),
        ),),
    
    ('1.3.00', None, (
         ("BET1089",
         """Apportate modifiche ed implementazioni interne per funzionamento 
         su Linux/GTK."""),
        ),),
    
    ('1.2.97', dt.Date(2011,4,19), (
         ("BUG1069",
         """Corretto bug identificazione registro iva in documenti con 
         contabilizzazione su causale non iva (fatture proforma)."""),
        ),),
    
    ('1.2.96', dt.Date(2011,4,18), (
         ("BUG1068",
         """Corretto bug invio documenti per mail da dataentry documenti di magazzino: 
         dopo avere individuato un indirizzo di spedizione ad un certo cliente, 
         tale indirizzo email rimaneva in memoria e proposto per la spedizione 
         nei successivi documenti riferiti a clienti sprovvisti di indirizzo di 
         spedizione."""),
        ),),
    
    ('1.2.94', None, (
         ("BUG1067",
         """Eliminata eccezione durante l'evasione di documenti da fornitore."""),
         ("BET1086",
         """Aggiunto, nel dataentry dei documenti di magazzino, il 
         controllo di coerenza tra il tipo di aliquota iva delle righe
         di dettaglio, se particolare, rispetto al tipo di registro iva."""),
         ("BET1087",
         """Aggiunto, nel dataentry dei documenti di magazzino, il 
         controllo di congruenza tra l'eventuale aliquota iva in testata
         rispetto a quella delle righe di dettaglio."""),
         ("BET1088",
         """Aggiunta, nel programma di setup, la richiesta a fine installazione
         di avvio automatico del programma."""),
        ),),
    
    ('1.2.93', None, (
         ("BET1085",
         """Estesa la funzionalità del cash flow: è ora possibile, 
         mediante il nuovo sottomenu presente nel menu scadenzari, 
         l'analisi di: cash flow generale (come prima); analisi incassi;
         analisi pagamenti; portafoglio effetti da emettere; scadenzario
         effetti emessi; scadenzario effetti insoluti."""),
        ),),
    
    ('1.2.92', None, (
         ("BUG1066",
         """Corretta la funzione di generazione file effetti: in presenza
         di clienti con indirizzo più lungo di 30 caratteri generava la 
         riga corrispondente in modo non idoneo al tracciato riba/rid."""),
         ("BET1084",
         """Implementata la possibilità nello scadenzario di raggruppare
         in base all'agente del documento invece che del cliente."""),
        ),),
    
    ('1.2.91', None, (
         ("BUG1065",
         """Corretta la funzione di generazione reportistica per creare
         automaticamente le cartelle mancanti nel percorso di generazione
         del report."""),
        ),),
    
    ('1.2.90', None, (
         ("BUG1062",
         """Corretto il controllo dei fidi clienti per eliminazione bug
         conteggio ddt ancora da fatturare, che venivano considerati due 
         volte."""),
         ("BUG1063",
         """Corretto dataentry documenti magazzino per esclusione dei 
         documenti contrassegnati come acquisiti durante la ricerca dei
         documenti da evadere (per coerenza con la fatturazione differita)."""),
         ("BUG1064",
         """Corretto dataentry documenti magazzino per inibizione editing colonna
         quantità e obbligo di evasione dell'intero documento se il tipo di 
         evasione è 'acquisizione' (per coerenza con la fatturazione differita)."""),
        ),),
    
    ('1.2.89', None, (
         ("BUG1060",
         """Corretto problema nell'inserimento di registrazioni in saldaconto che
         causava una eccezione nel caso in cui venivano selezionate partite poi
         escluse dalla griglia della partite del cliente/fornitore mediante la
         casella di controllo per la inclusione o meno delle partite a saldo 
         zero."""),
         ("BUG1061",
         """Corretta inesattezza dei totali dare/avere alla chiusura di una 
         registrazione in saldaconto: non venivano azzerati."""),
         ("BET1081",
         """Introdotta la possibilità di inclusione delle colonne di costo di 
         acquisto e/o pezzi per confezione nella griglia di visualizzazione dei
         listini validi alla data."""),
         ("BET1082",
         """Introdotto il controllo di integrità referenziale sulla gestione 
         della scheda anagrafica della partita: limita la sua cancellazione
         al fatto che non esistano registrazioni che puntano ad essa."""),
         ("BET1083",
         """Introdotto il controllo di coerenza delle partite nelle registrazioni
         in saldaconto: ora non è più possibile salvare tali registrazioni se
         contengono una o più scadenze che si riferiscono a partite inesistenti."""),
        ),),
    
    ('1.2.86', None, (
         ("BUG1059",
         """Nella totalizzazione del documento di magazzino, il calcolo del costo
         totale e del relativo margine (se abilitati alla visualizzazione) non 
         tenevano conto delle righe di sconto ripartito."""),
        ),),
    
    ('1.2.85', None, (
         ("BET1080",
         """Implementata la possibilità di estrazione delle sole partite marcate
         come insolute (al di la del loro saldo) nello scadenzario della singola
         anagrafica, nello scadenzario clienti/fornitori e nello scadenzario di 
         gruppo."""),
        ),),
    
    ('1.2.84', None, (
         ("BET1078",
         """Implementata la possibilità di corredare il documento di magazzino con
         destinazione merce non codificata e dati del vettore non codificato."""),
         ("BET1079",
         """Implementata la possibilità di effettuare la ricerca dei prodotti in
         modo tale da identificare subito il prodotto dal codice digitato, anche se
         ce ne sono altri con il codice che inizia con quanto digitato.  In questa
         situazione, è comunque possibile trovare gli altri, semplicamente 
         aggiungendo ".." alla fine del codice."""),
        ),),
    
    ('1.2.76', dt.Date(2011,1,7), (
        ("BUG1057",
         """Corretto bug in anagrafica fornitori: non aggiornava lo storico delle
         email spedite da stampa documenti magazzino."""),
        ("BUG1058",
         """Corretto bug in generazione reports: se in workstation era indicato di
         generare i files pdf su un percorso che iniziava con "//" o "\\", non
         veniva costruita la serie di sottocartelle necessarie alla stampa dei 
         documenti di magazzino (.../Documenti ANNO/FORMATOSTAMPA/...)."""),
         ("BET1076",
         """Implementata la possibilità nella configurazione delle causali di 
         magazzino di impostare il tipo di ricalcolo da effettuare nel caso di
         modifica dell'importo di riga: prima ricalcolava solo gli sconti, ora si
         può impostare il tipo di movimento in modo che ricalcoli la quantità o
         il prezzo."""),
         ("BET1077",
         """Implementata la possibilità di visualizzare nella griglia di ricerca
         della gestione prodotti anche la giacenza globale di tutti i magazzini
         invece che solo di un magazzino alla volta.  Di conseguenza, a differenza
         di prima, la giacenza viene visualizzata sempre e comunque (se attivato 
         il relativo flag nel setup azienda), a prescindere dalla selezione di un
         magazzino o meno.  Adeguato il comportamento della ricerca e della stampa
         anche in presenza di richiesta di visualizzazione dei soli prodotti con
         giacenza non nulla."""),
        ),),
    
    ('1.2.75', dt.Date(2010,12,23), (
        ("BUG1055",
         """Corretto bug in dataentry contabile: il tasto 'pareggia', richiamato
         sulla riga vuota (adibita ad inserimento di una nuova riga) della griglia 
         dare/avere, causava una segnalazione di errore; ora si limita a non fare 
         nulla."""),
        ("BUG1056",
         """Corretto bug in controllo date in dataentry documento magazzino, 
         impediva l'inserimento di documenti con data di registrazione successiva
         a quella del documento."""),
         ),),
    
    ('1.2.74', dt.Date(2010,12,21), (
        ("BUG1052",
         """Corretto bug in gestione anagrafiche piano dei conti: se la
         workstation era configurata come remota, le finestre di gestione dei
         vari sottoconti richiedevano conferma di abbandono dei dati modificati
         alla prima ricerca effettuata, ancor prima di digitare qualsiasi dato
         della scheda."""),
        ("BUG1053",
         """Corretto bug in richiamo scheda/mastro del sottoconto da griglie 
         bilancio: se la workstation era configurata come remota, veniva aperta 
         una scheda vuota, come se si fosse in inserimento."""),
        ("BUG1054",
         """Corretto bug in contabilizzazione documento di magazzino contenente
         ritenute d'acconto: dalla versione 1.2.67 non generava la riga della
         ritenuta, causando registrazione squadrata."""),
         ),),
    
    ('1.2.73', dt.Date(2010,12,20), (
        ("BUG1051",
         """Corretto bug nella contabilizzazione dei documenti di magazzino: 
         in presenza di righe omaggio originava eccezione e non contabilizzava
         la scrittura."""),
         ),),
    
    ('1.2.72', dt.Date(2010,12,20), (
        ("BUG1048",
         """Corretto l'autocompletamento delle date: in assenza di indicazione
         dell'anno o indicazione mediante le ultime due cifre dell'anno invece
         che con l'anno per esteso su quattro cifre, l'autocompletamento veniva
         eseguito in ritardo rispetto alla determinazione della data inserita
         (tale comportamento veniva innescato dalla pressione di un bottone o
         mediante relativo acceleratore di tastiera).  Tale comportamento poteva
         portare alla errata interpretazione della data (vista come data nulla), 
         sebbene poi a video la data comparisse esatta."""),
        ("BUG1049",
         """Aggiunti meccanismi di controllo di coerenza delle data inserite nel
         dataentry di magazzino: ora viene anche testata la conguenza dell'anno
         della data di registrazione rispetto all'anno della data di login,
         rispetto al quale non può eccedere; la data del documento inoltre non 
         può essere successiva alla data di login, nel qual caso l'operatore 
         viene avvisato e può forzare il controllo; l'operatore viene avvisato
         anche se la data di registrazione e/o la data del documento è relativa
         ad un anno inferiore all'anno precedente la data di login)."""),
        ("BUG1050",
         """Corretto dataentry magazzino: una volta inserito un documento, la
         finestra riposizionava correttamente il cursore sulla causale, ma non
         veniva attivato il bottone di default, con la conseguente perdita di 
         funzionalità del tasto <Invio> come scorciatoia per l'inserimento di
         un nuovo documento."""),
        ("BET1075",
         """Modificato il comportamento del flag di inibizione scontistiche sulla
         tabella gruppi prezzo (vedi BET1069): ora le scontistiche vengono 
         considerate se proventienti dalle condizioni promozionali o dalle 
         griglie."""),
         ),),
    
    ('1.2.71', None, (
        ("BUG1047",
         """Corrette le totalizzazioni nell'interrogazione dei vettori, che non 
         risentivano del cambiamento dei filtri applicati."""),
        ("BET1073",
         """Implementata la sezione dei conti d'ordine sul bilancio contrapposto."""),
        ("BET1074",
         """Aggiunta la verifica di congruenza delle versioni del software: per ogni
         componente installato (X4, personalizzazione, elenco plugins), viene 
         effettuato un controllo di versione tra software in esecuzione e relativo
         livello di aggiornamento sul database dell'azienda.
         Per ognuno di questi, se la versione riscontrata sul database risulta più 
         recente riespetto al relativo software in esecuzione, ne viene data 
         segnalazione, al fine di segnalare all'operatore la necessità di 
         aggiornamento della workstation."""),
         ),),
    
    ('1.2.70', dt.Date(2010,11,30), (
        ("BET1071",
         """Modificate le stampe delle statistiche di magazzino per ampliamento
         larghezza codice prodotto ed ottimizzazione degli spazi."""),
        ("BET1072",
         """Migliorata l'evidenziazione dei vari totali nell'interrogazione dei
         documenti di magazzino."""),
         ),),
    
    ('1.2.69', None, (
        ("BET1069",
         """Implementata su tabella gruppi prezzo la possibilità di inibire le
         scontistiche (tranne da condizioni promozionali)."""),
        ("BET1070",
         """Modificati alcuni report attinenti ai prodotti per allargamento della 
         colonna del codice."""),
         ),),
    
    ('1.2.68', None, (
        ("BET1068",
         """Evidenziazione della versione di programma, eventuale personalizzazione 
         ed operatore attivo nella status bar della finestra principale."""),
         ),),
    
    ('1.2.66', None, (
        ("BUG1046",
         """Risolto bug in creazione tabella progressivi prodotti: non provvedeva
         a impostare a zero i progressivi in fase di inserimento record per il
         nuovo prodotto, causando il mancato funzionamento delle progressivazioni
         successive, fino al ricalcolo degli stessi."""),
         ),),
    
    ('1.2.65', None, (
        ("BUG1045",
         """Risolto bug in controlli visuali relativi a tabelle: in alcune situazioni, 
         allo spostamento della finestra padre si scatenava una eccezione."""),
        ("BET1065",
         """Introdotta interrogazione sui vettori."""),
        ("BET1066",
         """Aggiunta la colonna della parte indeducibile dell'imposta sulla 
         visualizzazione e stampa del registro iva."""),
        ("BET1067",
         """Modifica di interfaccia nei controlli visuali atti a cercare informazioni
         anagrafiche che sono dotati di uno o più filtri richiamabili con il bottone
         a forma di lente o con il tasto F12: ora i filtri vengono accompagnati da
         apposito bottone di conferma e non basta più cambiare il contenuto di uno
         di essi per applicarli.  Questo per migliorare l'interattività da tastiera."""),
         ),),
    
    ('1.2.64', None, (
        ("BUG1044",
         """Risolto bug in anagrafiche clienti e fornitori, nelle quali la finestra
         di gestione gestiva erroneamente lo stato nella situazione di cerca valori."""),
         ),),
    
    ('1.2.63', None, (
        ("BUG1043",
         """Risolto bug in anagrafiche clienti e fornitori, nelle quali la finestra
         di gestione portava saltuariamente ad una eccezione in seguito ad errato
         controllo dello stato se non presente."""),
         ),),
    
    ('1.2.62', None, (
        ("BUG1041",
         """Corretta la contabilizzazione del documento di magazzino: non scriveva
         il sottoconto della contropartita sulla prima riga della registrazione.
         Questa versione provvede anche a scrivere taale informazioni sulle
         registrazioni presenti, se mancante."""),
        ("BUG1042",
         """Controllo quadratura registrazioni contabili: in presenza di fatture
         caricate al contrario (come se fossero note di credito), riscontrava
         incongruenza di partite, dovuto all'errata interpretazione del valore
         della prima riga.  Viene ora testata la congruenza del segno contabile
         della prima riga rispetto a quello della configurazione della causale
         associata."""),
         ),),
    
    ('1.2.61', None, (
        ("BUG1040",
         """Corretta l'editazione delle condizioni promozionali sui prodotti: in
         inserimento nuova riga, non compariva lo spazio di editazione del codice
         e della descrizione del prodotto."""),
         ),),
    
    ('1.2.60', None, (
        ("BUG1039",
         """Nelle gestioni anagrafiche, cercando con estremi di ricerca che non
         trovavano nulla, la finestra si settava come contenente dati modificati."""),
        ("BET1063",
         """Implementata possibilità di selezione multipla dei registri iva in
         fatturato contabile e sitesi vendite aziende/privati."""),
        ("BET1064",
         """Nel raggruppamento ddt, le note di stampa dei documenti generati sono
         ora riempite con le note da stampare della scheda cliente, se presenti."""),
         ),),
    
    ('1.2.59', None, (
        ("BUG1038",
         """Corretta la liquidazione iva per evitare che, richiamando la stampa
         del riepilogo aliquote senza prima aver aggiornato i dati, compaia
         un messaggio di errore."""),
        ("BET1062",
         """Ottimizzate le griglie nei data entry contabili."""),
         ),),
    
    ('1.2.58', None, (
        ("BET1060",
         """Implementazione tabella Stati e integrazione nelle schede 
         anagrafiche di clienti e fornitori."""),
        ("BET1061",
         """Implementazione analisi del fatturato contabile in acquisto e
         vendita, con selezione di periodo, stati (tutti/italia/cee/fuori cee),
         e tipo anagrafiche (tutte, solo in blacklist, solo con stato in
         blacklist)."""),
         ),),
    
    ('1.2.56', None, (
        ("BET1049",
         """Implementazione dei tasti acceleratore nel menu principale, nelle
         finestre di gestione anagrafica, nei dataentry di contabilità e
         magazzino.  Migliarata la gestione del focus di tastiera nei
         dataentry."""),
        ("BET1050",
         """Correzione gestione destinatari di clienti/fornitori: prima, in 
         presenza di una o più detinazioni, una di esse veniva contrassegnata
         come preferita, ora se si vuole si possono impostare le destinazioni
         senza la necessità che una di esse sia per forza preferita."""),
        ("BET1051",
         """Implementati i decimali della quantità sui pezzi per confezione."""),
        ("BET1052",
         """Implementata la possibilità di richiesta, a stampa documento, di
         intestare graficamente il foglio o meno (per default viene proposto
         il flag 'intestazione' della causale)."""),
        ("BET1053",
         """Implementata la possibilità di richiesta, a stampa documento, di
         mettere i prezzi sul ddt o meno (per default viene proposto quanto 
         specificato sul nuovo flag apposito presente sulla scheda del 
         cliente).  Sul cliente è ora anche possibile indicare che la scelta
         di mettere i prezzi o meno sul ddt sia non modificabile in fase di
         selezione della stampa."""),
        ("BET1054",
         """Implementazione di codice e descrizione del prodotto esterni sulle
         griglie di prezzo clienti/fornitori, onde consentirne l'utilizzo in 
         fase di stampa dei documenti nel caso che il cliente/fornitore voglia
         vedere nel documento i suoi codici e/o descrizioni invece che quelli 
         nativi interni."""),
        ("BET1055",
         """Implementata la possibilità di utilizzo di una griglia prezzi, da
         parte di un cliente, di quella di un altro cliente.  Stessa metodica 
         nei confronti dei fornitori."""),
        ("BET1056",
         """Implementata la possibilità di inibire, nell'immissione documento
         di magazzino, l'utilizzo di prodotti non a griglia, con la possibilità
         o meno di forzare la situazione a seconda del flag apposito sulla 
         scheda del cliente."""),
        ("BET1057",
         """Implementata la possibilità di lasciare il prezzo nullo su righe 
         di movimento che lo necessitano; a seguito di tale possibilità da 
         attivare sulla configurazione del tipo di movimento, è stato introdotto
         nella fatturazione differita il controllo nella non esistenza di righe
         del genere nei documenti in raggruppamento, nel qual caso l'elaborazione
         non viene portata a termine, nonché la possibilità di estrarre righe del
         genere sia dall'interrogazione dei movimenti che dal mastro movimenti
         del prodotto."""),
        ("BET1058",
         """Implementata la possibilità di indirizzare il comportamento del focus
         di tastiera su codice o descrizione nei punti in cui viene richiesto
         l'inserimento di un sottoconto, di un cliente, di un fornitore; è
         possibile specificarne il comportamento, per ogniuna delle tre situazioni,
         sia nel caso la richiesta avvenga in una scheda piuttosto che in una 
         griglia."""),
        ("BET1059",
         """Attivato il controllo, nelle finestre di gestione anagrafica, di
         abbandono dei cambiamenti attivi."""),
         ),),
    
    ('1.2.54', None, (
        ("BET1048",
         """Introdotta la possibilità, nel dataentry dei documenti di magazzino,
         di inserire righe configurate come richiedenti qta e prezzo ma con prezzo
         nullo.  Utile nelle situazioni in cui la riga effettivamente deve essere
         comprensiva anche del prezzo e del relativo importo totale, ma al momento
         del suo inserimento non si conosce ancora il prezzo da applicare.
         La fatturazione differita non permette il completamento in presenza di 
         anche solo un ddt che presenti anche solo una riga del genere."""),
         ),),
    
    ('1.2.53', None, (
        ("BET1047",
         """Implementata nuova statistica di magazzino atta a valutare i prezzi di
         vendita applicati per ogni prodotto in un periodo di tempo.  Per ogni
         prodotto vengono evidenziati codice, descrizione, codice fornitore (se 
         attivato in setup azienda sezione magazzino), tripletta (valore minimo, 
         massimo e medio) per il prezzo unitario e stessa tripletta per il prezzo
         scontato."""),
        ("BUG1037",
         """Corretta interrogazione contabile di analisi del venduto e ripartizione
         tra clienti italiani privati e aziende, aziende cee, azienda estero: in
         alcuni casi il cliente veniva 'spalmato' su più righe invece che 
         sintetizzato su una sola riga."""),
         ),),
    
    ('1.2.52', dt.Date(2010,9,29), (
        ("BUG1036",
         """Corretto dataentry contabile composto: coinvolgendo alla prima riga
         un cliente o fornitore, si manifestava una eccezione alla riapertura della
         registrazione, con l'impossibilità di riprendere la registrazione per la 
         modifica."""),
         ),),
    
    ('1.2.50', None, (
        ("BET1046",
         """Introdotta la gestione degli acconti clienti: interrogazione acconti
         attivi, visualizzazione acconto residuo in testata documento, aggancio
         ad acconto a scelta su riga di storno acconto."""),
         ),),
    
    ('1.2.49', None, (
        ("BUG1035",
         """Il menu principale soffriva di un bug in base al quale era impossibile
         richiamare il dataentry di magazzino, se non dalla relativa icona della
         barra degli strumenti."""),
        ("BET1044",
         """Aggiunta la possibilità, nel setup dei dati aziendali, di impostare
         la ricerca dei prodotti in modo da visualizzarne, a fianco dei dati
         anagrafici, anche la giacenza e/o il prezzo al pubblico."""),
        ("BET1045",
         """Migliorate le selezioni di destinatario e banca sulla testata dei 
         documenti di magazzino: vengono ora evidenziati, nella ricerca, anche
         indirizzo, cap, citta, provincia per le destinazioni e abi, cab, c/c per
         le banche."""),
         ),),
    
    ('1.2.48', dt.Date(2010,9,6), (
        ("BUG1034",
         """Corretto il calcolo delle provvigioni: prima venivano considerati
         i movimenti di magazzino in base all'indicazione del fatturato vendita;
         ora viene considerato il flag relativo impostato a livello di intero
         documento, ad esclusione dei tipi di movimento sui quali sia stato
         espressamente indicato di non effettuare il calcolo provvigionale."""),
         ),),
    
    ('1.2.46', None, (
        ("BUG1033",
         """Nella stampa del giornale non si riusciva ad effettuare la ristampa
         nel caso l'esericio interessato fosse già stato chiuso.  Ora lo si può 
         selezionare in caso di ristampa."""),
        ("BET1043",
         """Aggiunta la funzione che consente di aggiornare il costo del prodotto
         su ogni riga di movimenti in base al costo attualmente presente sulla 
         scheda del prodotto."""),
         ),),
    
    ('1.2.43', None, (
        ("BET1041",
         """Introdotte le funzionalità di backup/restore del database 
         dell'azienda."""),
         ),),
    
    ('1.2.42', dt.Date(2010,7,15), (
        ("BUG1029",
         """Corrette le valutazioni statistiche di magazzino per evitare di
         considerare anche i documenti annullati o acquisiti e i movimenti
         annullati."""),
        ("BUG1030",
         """Corretto il dataentry contabile di registrazioni composte non
         iva con generazione partite nello scadenzario, che ne impediva 
         la memorizzazione."""),
        ("BUG1031",
         """Corretto il bug nella stampa dell'inventario che causava l'errata
         impostazione del magazzino da analizzare nel caso in cui, una volta 
         estratto l'inventario relativo ad un determinato magazzino, lo si 
         richiedesse nuovamente per tutti i magazzini, eliminandone la 
         selezione; in tal caso veniva comunque analizzato l'inventario del 
         magazzino precedentemente selezionato."""),
        ("BUG1032",
         """Corretta l'interpretazione delle date digitate: all'inserimento
         di valori errati, a seconda dei casi scaturiva un errore di
         interpretazione della data."""),
        ("BET1031",
         """Aggiunte le stampe nell'interrogazione delle registrazioni IVA e 
         nell'interrogazione dell'utilizzo alquote IVA."""),
        ("BET1032",
         """Storicizzazione del costo prodotti e gestione del margine sui 
         documenti di vendita."""),
        ("BET1033",
         """Possibilità di escludere dalla gestione dei listini di vendita
         i prodotti con costo e/o prezzo nulli."""),
        ("BET1034",
         """Attivazione dei meccanismi di controllo sul dataentry di magazzino
         per la possibilità di inibire l'uso di clienti con status opportuno 
         relativamente ai documenti classificati come ordine da cliente, 
         vendita a cliente, reso da cliente; l'uso di fornitori con status
         opportuno relativamente ai documenti classificati come ordine a 
         fornitore, carico da fornitore, reso a fornitore; l'uso di prodotti
         con status opportuno relativamente ai documenti classificati come
         ordine a fornitore, carico da fornitore, reso a fornitore, ordine da
         cliente, vendita a cliente, reso da cliente; l'uso di clienti con
         status opportuno relativamente alle modalità di pagamento con 
         effetti.  Inserita la classificazione nel setup dei documenti di 
         magazzino atta a rilevare le situazioni menzionate."""),
        ("BET1035",
         """Attivazione filtri per esclusione documenti annullati e/o acquisiti
         nell'interrogazione dei documenti di magazzino."""),
        ("BET1036",
         """Introduzione meccanismi di calcolo delle provvigioni agenti, con
         possibilità di indicazione della percentuale di provvigione sul
         cliente e sul prodotto, con eventuale ereditarietà a livello di riga
         del movimento di vendita, e calcolo delle provvigioni per agente e
         periodo, su tutti i documenti o solo quelli saldati."""),
        ("BET1037",
         """Aggiunta la possibilità di richiamo del pdf a fine stampa mediante
         dichiarazione esplicita del programma da utilizzare."""),
        ("BET1038",
         """Evidenziazione degli omaggi nella stampa del registro iva."""),
        ("BET1039",
         """Attivazione modalità di gestione dell'iva per le contabilità
         semplificate: unico dataentry contabile/iva, possibilità di stampa
         del registro iva comprensivo dei costi/ricavi."""),
        ("BET1040",
         """Modificato il comportamento della digitazione delle date: in 
         assenza di indicazione dell'anno, la data viene ora impostata
         tenendo conto della data di ingresso nel programma anziche della
         data di sistema."""),
         ),),
    
    ('1.2.36', dt.Date(2010,5,27), (
        ("BET1030",
         """Modifica dei criteri di riporto dei sottoconti patrimoniali (vedasi 
         BET1029): in caso di bilancio di esercizio precedente quello in corso,
         non viene riportato alcun saldo per i sottoconti patrimoniali, ma 
         vengono analizzate solo le registrazioni inerenti l'esercizio 
         desiderato."""),
        ("BET1031",
         """Modifica del programma di installazione: ora è possibile eseguire il
         setup di installazione da un utente privo dei privilegi di 
         amministratore."""),
         ),),
    
    ('1.2.35', dt.Date(2010,5,26), (
        ("BUG1028",
         """Corretto bug in dataentry registrazioni contabili con iva in presenza
         di registro iva con attivata la possibilità di protocollare a posteriori:
         in caso di presenza di altra registrazione su stesso registro con stesso
         numero documento, impediva la memorizzazione."""),
        ("BET1026",
         """Integrata nell'esportazione di file CSV la possibilità di trattare le
         informazioni di tipo testuale che iniziano con un carattere compreso tra
         0-9 come formule, al fine di evitare che Excel ne interpreti il contenuto
         come numero, perdendo la parte iniziale del testo."""),
        ("BET1027",
         """Adeguamento colori griglie a colori del tema impostato a livello di
         sistema."""),
        ("BET1028",
         """Aggiunta nella stampa mastri la possibilità di ordinare per codice,
         descrizione, classificazioni di bilancio, nonchè possibilità di stampa di
         un sottoconto per ogni pagina e l'inclusione o meno dei dati di 
         intestazione pagine.  Sulla stampa compaiono ora anche le classificazioni
         di bilancio mastro e conto."""),
        ("BET1029",
         """Modificati i criteri di valutazione dell'esercizio nei mastri e nei
         bilanci relativi a sottoconti di tipo patrimoniale: fino alla versione 
         1.2.34, venivano considerate tutte le operazioni precedenti l'esercizio 
         desiderato. 
         Questo comportava la conformazione di progressivi dare/avere relativi a 
         più esercizi, se presenti in numero maggiore di uno.  Ora, in base 
         all'esercizio desidarato, si ha la seguente selezione: bilancio 
         dell'esercizio in corso: nessun riporto; bilancio di esercizio successivo 
         a quello in corso: riporto dall'esercizio in corso a quello desiderato; 
         bilancio di esercizio precedente quello in corso (esercizio chiuso): 
         come prima, riporto di tutto ciò che precede l'esercizio desiderato."""),
         ),),
    
    ('1.2.34', dt.Date(2010,5,12), (
        ("BUG1026",
         """Corretta la determinazione dell'esercizio nell'immissione delle
         registrazioni contabili in caso di inizio esercizio diverso dal 1/1."""),
        ("BUG1027",
         """Corretta la liquidazione iva che memorizzava, in caso di versamento,
         il debito del versamento come debito da riportare nella liquidazione
         successiva. Bug introdotto in versione 1.2.32."""),
        ("BET1025",
         """Migliorata la gestione, nelle selezioni della liquidazione iva,
         del tipo di selezione del periodo automatico/manuale; scegliendo
         periodo manuale ed alterando le date, riportando in periodo
         automatico non ricalcolava le date di inizio e fine in modo
         congruente al periodo correntemente selezionato.
         Disabilita anche il periodo (mese/trimestre) in caso di selezione
         manuale delle date ed impostazione del focus di tastiera sulla
         data di inzio in caso di selezione di periodo automatico o sul
         periodo (mese/trimestre) in caso di selezione di periodo manuale."""),
         ),),
    
    ('1.2.32', dt.Date(2010,4,28), (
        ("BUG1023",
         """Corretto il dataentry delle registrazioni contabili con iva:
         attivando la sezione iva, non settava correttamente il controllo del
         sottoconto iva e iva indeducibile, proponendo l'aiuto dal piano dei
         conti su colonne errate."""),
        ("BUG1024",
         """Corretto il dataentry delle registrazioni contabili con iva:
         in presenza di documenti con totale negativo, gestiti a partire 
         dalla modifica BET1015, si verificavano strani comportamenti 
         modificando il totale del documento e/o la parte iva."""),
        ("BUG1025",
         """Corretta la liquidazione iva definitiva: consentiva di avviare
         l'estrazione dei dati dopo aver deselezionato il registro da 
         analizzare."""),
        ("BET1022",
         """Correzione controllo online della partita iva comunitaria per 
         adeguamento al cambio di endpoint soap sulla url del fornitore di 
         servizio controllo partite iva 'ec.europa.eu'."""),
        ("BET1023",
         """Modificata la ricerca dei codici durante la digitazione: ora
         l'elemento viene identificato solo a digitazione completa del 
         codice."""),
        ("BET1024",
         """Modificata la ricerca dei codici durante l'ingresso in 
         editazione del codice sottoconto all'interno delle griglie: ora
         il focus della tastiera viene posto sulla descrizione solo al
         di fuori delle griglie; prima poneva il focus della tastiera 
         sulla descrizione del sottoconto anche all'interno delle griglie, 
         causando confusione nel caso si iniziasse a digitare il codice del 
         sottoconto prima di entrare in editazione (manteneva il carattere
         digitato nella prima posizione del codice, quindi si spostava
         automaticamente sulla descrizione."""),
         ),),
    
    ('1.2.31', dt.Date(2010,4,23), (
        ("BUG1019",
         """Corretta la liquidazione iva per integrazione campo VP13 (crediti 
         speciali di imposta detratti), nonché la gestione del versamento minimo
         pari a euro 25.82, che determina, in caso di versamento inferiore a tale
         cifra, il versamento a zero ed il riporto della cifra che non si versa
         come debito periodo precedente nei progressivi della liquidazione, come
         avveniva solo in caso di liquidazione a credito.
         Corretta scheda progressivi liquidazione iva per integrazione del citato 
         debito periodo precedente, nel caso di versamento non effettuato in
         quanto inferiore alla menzionata soglia minima."""),
        ("BUG1020",
         """Nel controllo di cassa si verificava un errore nella determinazione
         del valore da presentare come data di riporto iniziale usando come
         server dei dati MySQL versione 5.1"""),
        ("BUG1021",
         """Corretta scheda marca prodotto per malfunzionamento che ne impediva
         la visualizzazione e gestione a livello di singola marca."""),
        ("BUG1022",
         """Corretta la gestione dei tipi di evento e la visualizzazione degli
         eventi presenti, le relative voci di menu portavano rispettivamente
         ad un errore e a nessuna reazione a causa di una configurazione errata
         del menu Setup/Opzioni/Eventi."""),
        ),),
    
    ('1.2.29', dt.Date(2010,3,29), (
        ("BUG1018",
         """Attivando la funzionalità di spedizione documenti via email, dal
         dataentry di magazzino proponeva sempre e comunque l'invio del 
         messaggio email, anche per quei clienti sprovvisti di apposito 
         indirizzo di ricezione dei documenti in formato elettronico."""),
        ),),
    
    ('1.2.28', dt.Date(2010,3,16), (
        ("BET1021",
         """Attivata la funzionalità di spedizione documenti via email anche 
         sulla stampa differita."""),
        ("BUG1017",
         """Corretto problema nella stampa differita: in presenza di più 
         magazzini, non effettuava l'eventuale filtro sul magazzino."""),
        ),),
    
    ('1.2.25', dt.Date(2010,3,12), (
        ("BET1020",
         """Inserita la possibilità di registrare in contabilità documenti con 
         iva con totale negativo: occorre attivare relativo permesso sulla 
         configurazione della causale e confermare all'occorrenza il messaggio
         di avvertimento relativo ai segni invertiti.  Nella sezione contabile
         vengono invertiti i segni della riga di partita (cliente/fornitore)
         nonché degli eventuali sottoconti preferiti dotati di segno; nella 
         sezione iva e nello scadenzario gli importi sono algebricamente 
         invertiti.  La stessa possibilità è anche presente nell'inserimento
         dei documenti di magazzino."""),
        ("BUG1014",
         """Controllo esistenza partita iva su sistema comunitario vies: è stato
         aggiunto il controllo dell'errore nel caso in cui il sistema non sia 
         accessibile mediante webservice, nel caso ciò accada viene mostrato un
         avviso, prima si scatenava un errore.  La consultazione via web è 
         comunque possibile, mediante l'apposito bottone della finestrella di
         controllo."""),
        ("BUG1015",
         """Corretto problema nell'inserimento di un nuovo listino nella scheda
         del prodotto: in caso di gestione dei listini con data di validità, la
         data sulla nuova riga di listino veniva impostata uguale alla data di 
         lavoro, anche modificandola."""),
        ("BUG1016",
         """Corretto problema nell'inserimento di registrazioni contabili di 
         sola iva: la griglia delle aliquote era erroneamente non accessibile
         durante l'inserimento della registrazione."""),
        ),),
    
    ('1.2.24', dt.Date(2010,3,3), (
        ("BET1019",
         """Inserita la possibilità di recapito elettronico dei documenti di 
         magazzino, tipo fattura e quant'altro.  Per ogni documento che si voglia
         recapitare per via elettronica, occorre specificarne il flag ed il testo
         da includere come corpo del messaggio.  Sulla scheda anagrafica del 
         cliente/fornitore è stato aggiunto il campo relativo all'indirizzo di
         posta elettronica su cui inviare i documenti."""),
        ),),
    
    ('1.2.23', dt.Date(2010,2,26), (
        ("BUG1013",
         """Corretto bug in liquidazione iva: effettuava controllo di congruenza
         tra la data di liquidazione e la data di stampa definitiva dei vari 
         registri, anche per la liquidazione provvisoria."""),
        ),),
    
    ('1.2.22', dt.Date(2010,2,25), (
        ("BUG1012",
         """Corretto bug in bilancio in base al quale venivano erroneamente
         considerate anche le righe di iva omaggio."""),
        ),),
    
    ('1.2.21', dt.Date(2010,2,5), (
        ("BET1018",
         """Implementato nei registri iva il flag di identificazione di registro
         riepilogativo.  Tale impostazione consente di evitare il controllo delle
         date di stampa dei registri in fase di liquidazione, nel caso si vogliano
         stampare le liquidazioni su un registro appunto riepilogativo a cui non
         fa riferimento alcuna registrazione."""),
        ),),
    
    ('1.2.20', dt.Date(2010,2,5), (
        ("BUG1011",
         """Corretto bug nelle stampe della liquidazione iva: in caso di liquidazione
         provvisoria, non incrementava il numero di pagina tra le varie stampe
         separate coinvolte nella liquidazione (riepiloghi aliquote, prospetti di
         liquidazione)."""),
        ("BUG1012",
         """Corretto bug nella stampa pluriprezzo dei listini di vendita: il pannello
         di selezione dei valori da includere nella stampa comprendeva anche il costo,
         ma selezionandolo questo non veniva stampato."""),
        ),),
    
    ('1.2.19', dt.Date(2010,1,22), (
        ("BUG1009",
         """Corretto bug nel dataentry dei documenti di magazzino, introdotto 
         nella versione 1.2, a causa del quale la data di inizio trasporto non 
         veniva memorizzata, né stampata."""),
        ("BUG1010",
         """Corretto bug in evasione documenti documenti di magazzino: nel caso 
         la configurazione preveda l'annullamento del documento evaso, questo
         veniva annullato anche quando il documento evaso aveva ancora righe
         da evadere."""),
        ),),
    
    ('1.2.18', dt.Date(2010,1,15), (
        ("BET1016",
         """Aggiunto il controllo di congruenza dei registri IVA nella funzione
         di controllo di quadratura delle registrazioni."""),
        ("BET1017",
         """Aggiunto il controllo di presenza del registro IVA nei dataentry
         contabili di registrazioni con IVA e di sola IVA."""),
        ),),
    
    ('1.2.16', dt.Date(2010,1,7), (
        ("BET1014",
         """Aggiunto il controllo formale sulla partita iva per tutti gli stati
         comunitarie.  Alterato inoltre il meccanismo di verifica online della
         partita iva cee, che ora sfrutta il webservice che il sito web
         comunitario mette a disposizione per controlli automatizzati simili a 
         questo; l'apertura della pagina web corrispondente non ha subito 
         variazioni."""),
        ("BET1015",
         """Aggiunta la documentazione dei cambiamenti di versione per quanto
         concerne l'eventuale personalizzazione di X4: se presente, la finestra
         dei cambiamenti consente di visualizzare anche quelli specifici della
         personalizzazione (versione modificata di X4, 'mod')."""),
        ("BUG1008",
         """Corretta la selezione dell'esercizio da considerare in bilancio: 
         ad inizio anno, invocando il bilancio senza aver ancora registrato alcuna
         operazione nel nuovo anno, si verificava un errore e non si presentava la
         maschera di selezione del bilancio.  A parità di condizioni, ora la 
         selezione dell'esercizio è inizializzata con l'esercizio trovato più
         recente."""),
        ),),
    
    ('1.2.14', dt.Date(2009,12,30), (
        ("BET1013",
         """Dataentry contabile registrazioni composte: corretta la contropartita
         della prima riga: prima corrispondeva al sottoconto dell'ultima riga
         non automatica; ora corrisponde al sottoconto della prima riga non 
         automatica."""),
        ),),
    
    ('1.2.13', dt.Date(2009,12,28), (
        ("BET1011",
         """Dataentry contabile registrazioni con IVA: adeguata la selezione del
         cliente/fornitore alla ricerca dedicata a tali tipi di anagrafiche (con
         visualizzazione dei dati anagrafici nella finestra di ricerca e filtri
         sull'apposito status del cliente o del fornitore)."""),
        ("BET1012",
         """Dataentry contabile registrazioni con IVA: la selezione della casella
         relativa agli omaggi nella sezione IVA (BET1010) non rinfrescava 
         correttamente la griglia, causando il corretto trattamento degli importi
         ma la visualizzazione errata della casella stessa."""),
        ),),
    
    ('1.2.11', dt.Date(2009,12,26), (
        ("BET1005",
         """Miglioramento gestione bottone di default.  Sulle maschere complesse
         il bottone di default è contestuale al controllo che ha il focus della
         tastiera, consentendo di indirizzare il bottone opportuno a seconda
         del posto in cui si digita con la tastiera."""),
        ("BET1006",
         """Implementazioni su interrogazione registrazioni contabili: 
         introdotto la possibilità di filtrare registrazioni con iva, di sola
         iva e senza iva, per default tutte attivate; aggiunta la selezione
         delle registrazioni che contengono una determinata aliquota iva e/o un
         determinato sottoconto, questo evidenziato in stampa."""),
        ("BET1007",
         """Migliorato l'inserimento delle date: ora è possibile digitare la data
         con l'anno a 2 cifre, all'uscita dell'editazione l'anno verrà 
         automaticamente espanso su 4; digitando solo giorno e mese, l'anno viene
         aggiunto automaticamente all'uscita con l'anno della data di sistema."""),
        ("BET1008",
         """Aggiunta la funzione di controllo sequenza protocolli IVA."""),
        ("BET1009",
         """Aggiunto il controllo di numerazione in fase di conferma di un documento 
         di magazzino: sia per numerazioni automatiche sul magazzino che su quelle
         derivanti dal protocollo della registrazione iva collegata, viene ora
         effettuato un controllo di univocità (rispettivamente sui documenti di 
         magazzino e sulle registrazioni contabili) del numero immesso.
         Se il numero inserito viene riscontrato già presente in altre registrazioni,
         viene evidenziata la situazione e il documento rimane da salvare, dopo la
         correzione manuale del numero."""),
        ("BET1010",
         """Aggiunta la colonna per contrassegnare come omaggio nella griglia
         iva delle registrazioni contabili con IVA.  In tale colonna occorre 
         spuntare quelle righe che si riferiscono ad omaggi, per i quali occorre
         conteggiare, nella parte contabile, l'imposta ma non l'imponibile.
         Le righe di sola IVA sono ora gestite mediante un tipo riga che identifica
         la situazione di sola iva.
         Questo consente anche di evitare la segnalazione, peraltro errata, durante
         il controllo di congruenza delle registrazioni contabili, di squadrature
         tra IVA e Dare/Avere in corrispondenza di registrazioni con righe di sola 
         IVA.
         Tutte le registrazioni IVA derivanti da collegamento contabile dal magazzino
         che al loro interno contengono righe di sola IVA, contrassegnate con la 
         scritta "OMAGGI" nelle note, vengono automaticamente adeguate a questa
         gestione."""),
        ("BET1011",
         """Implementata, nel dataentry dei documenti di magazzino, la possibilità
         di digitare, su ogni riga di dettaglio, un testo al posto della singola 
         descrizione.  Questo consente di inserire un testo, anche suddiviso su più 
         righe, in corrispondenza di una riga di corpo, o più di una.  Tale 
         possibilità deve essere concertata sia con il setup della causale di 
         magazzino che con il formato del report che genera la stampa del 
         documento."""),
        ("BET1012",
         """Implementata la funzione di previsione delle giacenze prodotti in 
         funzione degli ordini clienti e/o fornitori.  La funzione determina, per
         ogni prodotto esaminato, la giacenza e l'ammontare degli ordini residui
         (backorders) di clienti e fornitori, consentendo quindi l'analisi del
         magazzino a fronte delle richieste di merce verso fornitori e clienti.
         Per ogni prodotto è possibile consultare anche il dettaglio dei backorders
         attivi, e per ognuno di questi visualizzare l'elenco dei documenti che
         lo hanno evaso fino a quel momento."""),
        ("BUG1004",
         """In inserimento anagrafiche del piano dei conti, se effettuato dalla
         interrogazione, non azzerava le maschere di consultazione (mastro, 
         scadenzario, magazzino)."""),
        ("BUG1005",
         """Corretto dataentry registrazioni iva con scorporo, in alcune 
         situazioni generava una squadratura D/A di un centesimo, che andava
         sistemata manualmente."""),
        ("BUG1006",
         """Corretta funzione di consolidamento dei costi e delle giacenze a fine
         anno: in alcune situazioni, determinati prodotti non venivano considerati
         correttamente dall'elaborazione e non venivano quindi nè presentati per 
         l'editazione delle giacenze rilevate, nè considerati nella funzione di 
         generazione delle giacenze iniziali."""),
        ("BUG1007",
         """Corretta la griglia del documento di magazzino, che consentiva 
         l'inserimento di campi di testo più lunghi del dovuto, causando problemi 
         nel salvataggio del documento stesso."""),
        ),),
    
    ('1.1.41', dt.Date(2009,11,5), (
        ("BUG1002",
         """Risolto bug in liquidazione IVA in base al quale, in determinate
         condizioni, non veniva considerato l'eventuale credito del periodo
         precedente.  Corretta inoltre la visualizzazione di data e protocollo
         ultima stampa per ogni registro.  Aggiunta la visualizzazione del 
         periodo e della data limite dell'ultima liquidazione definitiva nel 
         pannello delle selezioni ed il relativo controllo di congruenza della
         data iniziale del periodo da liquidare, che deve essere successivo alla
         data dell'ultima liquidazione."""),
        ("BUG1003",
         """Risolto bug in dataentry magazzino in base al quale, in determinate
         condizioni, non veniva impostato correttamente il numero di protocollo
         iva al variare della data di registrazione."""),
        ("BET1004",
         """E' ora possibile impostare determinate stampe in modo tale da 
         ottenere molteplici copie, ognuna delle quali può riportare una diversa
         descrizione (ad esempio 'Copia interna' e 'Copia cliente' sui DDT e
         sulle Fatture)."""),
        ),),
    
    ('1.1.40', dt.Date(2009,10,29), (
        ("BET1002",
         """Modificato dataentry schede anagrafiche: ora, su elementi esistenti,
         il codice e la descrizione non sono più modificabili in maniera
         immediata, per evitare che l'utente azzeri e/o alteri inavvertitamente
         il loro contenuto, visto che sono generalmente i primi campi presenti
         nelle videate di questo tipo, quini sono i primi a ricevere il focus
         da tastiera.  Nel caso occorra modificare codice e/o descrizione, 
         occorre specificare tale volontà mediante un semplice doppio click del 
         mouse su codice o descrizione: in tal caso i due campi verranno resi
         disponibili per la modifica, fino a che si rimane in modifica su
         quell'elemento."""),
        ("BET1003",
         """Modificato dataentry registrazioni iva: ora attivando la sezione 
         iva, la colonna dell'aliquota nella griglia dare/avere non viene
         annullata ed è consentito il cambiamento.  Questo in vista di nuova
         interrogazione che darà modo di visionare i costi relativamente ad una 
         certa aliquota iva."""),
        ),),
    
    ('1.1.39', dt.Date(2009,10,25), (
        ("BET1001",
         """Migliorata la gestione di banche e destinazioni merce su scheda 
         anagrafica clienti/fornitori: ora, per entrambe le sezioni, esiste la
         griglia che presenta il codice e la descrizione degli elementi 
         presenti, mentre i dettagli vongono gestiti in appositi campi di fianco
         alla griglia, un elemento alla volta."""),
        ),),
    
    ('1.1.38', dt.Date(2009,9,8), (
        ("BUG1001",
         """Inserito controllo presenza scadenze in registrazione saldaconto,
         permetteva la conferma di registrazione vuota con righe contabili 
         presenti ma a zero e generava errore in scrittura scadenze."""),
        ),),
    
)


# ------------------------------------------------------------------------------


historymod = ()
