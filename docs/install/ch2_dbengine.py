#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         docs/install/ch2_dbengine.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
# Created:      2007/11/07
# Copyright:    (C) 2011 Astra S.r.l. C.so Cavallotti, 122 18038 Sanremo (IM)
# ------------------------------------------------------------------------------

from reportlab.tools.docco.rl_doc_utils import *
import reportlab

import sys
sys.path.append('../..')
import version as ver

#title("X4 Gestione Aziendale")
#title("Manuale di installazione")
#centred('X4 Versione ' + ver.__version__)

nextTemplate("Normal")

################################################################################
###                                                                          ###
###                              CAPITOLO 2                                  ###
###                                                                          ###
################################################################################


heading1("Installazione del Database")
disc("""
X4 opera con tecnologia client/server per quanto concerne i dati gestiti, ovvero
si appoggia ad un motore SQL.
In base alla configurazione, tale motore può essere di vari tipi; al momento è
gestito MySQL versione 5.0, questo capitolo affronta l'installazione e la 
configurazione di questo motore.
""")

heading2("Identificazione della macchina server")
disc("""
La connessione al server MySQL avviene su protocollo TCP/IP: la sua installazione
quindi può essere eseguita su qualsiasi PC o server presente nella LAN.
MySQL può essere installato anche su un normale PC, in assenza di server, in
piccole installazioni (numero limitato di postazioni di lavoro, basso volume di 
dati da gestire).  Le prestazioni del database dipenderanno sia dal carico di 
lavoro, che dal numero di accessi contemporanei, che, ovviamente, dalle 
prestazioni della macchina su cui gira.
Occorre quindi identificare a priori quale macchina fungerà da server dei dati 
e su questa procedere all'installazione del database.
""")

heading2("Setup del server MySQL")
disc("""L'installazione del server MySQL comporta, solitamente, il setup di 
tre distinte parti:
""")
list("""Setup del server MySQL.  Il setup avviene eseguendo il programma di 
installazione, il cui nome dipende dalla versione e dalla release.
Si consiglia l'uso della versione 5.0, nella release disponibile al momento 
dell'installazione.  Esempio: mysql-essential-5.0.51a-win32.msi  
L'installazione avviene mediante un wizard e risulta decisamente semplice: 
scegliere la voce "typical" e confermare.  Il setup provvederà all'installazione
dei files binari e quant'altro necessario al funzionamento del server.
Una volta terminata l'installazione, il wizard segnalerà la fine del processo di
setup, dando modo di procedere alla prima configurazione: lasciare quindi 
spuntata la voce "Configure the MySQL Server now" e premere sul tasto "Finish".
""")
list("""
Verrà quindi eseguito il wizard della prima configurazione: scegliere 
"Detailed Configuration" e premere "Next", scegliere il tipo di "peso" che deve
avere il motore SQL sulle performances del PC (per installazione su Server 
scegliere "Server Machine", altrimenti su un normale PC scegliere 
"Developer Machine") e premere "Next".  Selezionare quindi la prima voce 
"Multifunctional Database" e premere "Next"; premere nuovamente "Next" nella 
parte seguente, che permette di indicare la locazione fisica che dovranno avere 
i files dei database di tipo InnoDB, che X4 non usa; selezionare quindi la prima
voce "Decision Support (DSS)/OLAP", che imposta un numero di connessioni pari a 
venti e premere "Next"; lasciare spuntate le due scelte proposte, se non ci sono 
esigenze particolari lasciare inalterato il valore della porta TCP/IP da usare e 
premere "Next"; selezionare la voce 
"Manual Selected Default Character Set / Collation" e quindi selezionare la voce 
"latin1" dall'elenco a discesa, quindi premere "Next"; lasciare spuntata la voce 
"Install As Windows Service" e selezionare il nome "MySQL5" dall'elenco a 
discesa, nonché spuntare la voce "Include Bin Directory in Windows PATH" e 
premere "Next"; impostare la password dell'utente root (amministratore del 
database) e premere "Next"; confermare quindi il tutto premendo "Execute".
Verrà configurato ed avviato il servizio MySQL.
Nota: è possibile che il firewall installato sul sistema impedisca il corretto 
funzionamento di MySQL: se appaiono richieste di conferma dell'attività server 
TCP/IP del processo mysqld-nt.exe autorizzare in modo permanente; se invece i 
criteri del firewall non consentono l'interazione con l'utente, si dovrà 
provvedere manualmente alla sua configurazione, indicando che MySQL Server possa
agire da server su TCP/IP e consentendone le connessioni sulla porta apposita 
(3306 di default).
Premere su "Finish" per tarminare il wizard di configurazione.
Nota: tale wizard può essere rieseguito a posteriori, nel caso occorresse 
modificare uno dei parametri qui impostati, eseguendo la voce 
"MySQL Server Instance Config Wizard", presente nel menu 
"MySQL / MySQL Server 5.0" nei programmi del pulsante "Start" di Windows.
""")
list("""Setup delle utility: MySQL Administrator, MySQL Query Browser.  Questi 
programmi consentono di amministrare il server e i database gestiti.
Eseguire il setup opportuno, eseguendo il programma di installazione a corredo 
di MySQL, ad esempio mysql-gui-tools-5.0-r12-win32.msi
Una volta installate queste utility, eseguire MySQL Administrator (disponibile 
sotto il menu "MySQL" dei programmi di Windows. Collegarsi al server appena 
installato, con le credenziali di 'root', e provvedere alla creazione 
dell'utente MySQL con il quale le postazioni di lavoro di X4 si collegheranno al
database: X4, infatti, utilizza una sua tabella di utenti, per cui è normalmente
sufficente creare un unico utente a livello MySQL.
Prima di creare l'utente, attivare la visualizzazione dei privilegi globali: 
dal menu "Tools/Options", spuntare la casella "Show Global Privileges" e 
confermare con "Apply".
Creare quindi l'utente: scegliere "User Administration" dal menu grafico 
verticale presente sulla sinistra della finestra di MySQL Administrator: 
la parte sottostante riporterà l'elenco degli utenti presenti (ovviamente si 
vedrà solo l'utente 'root'): in tale sezione mediante il tasto destro del mouse 
scegliere "Add new user" dal menu contestuale che comparirà e, nella parte 
destra della finestra, inserire il nome utente desiderato di fianco alla 
voce "MySQL User"; selezionare il tabulatore "Global Privileges" ed assegnare 
tutti i privilegi all'utente (portare tutte le voci presenti nella colonna di 
destra denominata "Available Privileges" nella colonne di sinistra denominata 
"Assigned Privileges", quindi confermare il tutto premendo su "Apply Changes".
A questo punto occorre impostare la password dell'utente: tale password non deve
essere inserita contestualmente al nome utente, anche se richiesto da MySQL 
Administrator, in quanto i criteri di valutazione della password presenti su X4
non sono compatibili con le password impostate in tale sezione, procedere invece
come segue.
Dal menu "Tools" di MySQL Administrator, richiamare la voce 
"MySQL Command Line Client": si aprira una shell di sistema con i comandi 
amministrativi del database ed inserire il seguente comando:
SET PASSWORD FOR 'nome_utente'@'%' = OLD_PASSWORD('password_desiderata');
seguito dal comando:
FLUSH PRIVILEGES;
Ovviamente bisogna sostituire nome_utente con il nome dell'utente desiderato, 
e "password_desiderata" con la password desiderata.
Questa accoppiata utente/password dovrà essere inserita nella configurazione X4
su ogni workstation che si andrà ad installare.
""")
list("""Setup dei componenti necessari per la connettività ODBC.  Questo è 
necessario solo nel caso in cui si debbano impostare delle estrazioni dati da
altri software, come ad esempio interrogazioni da Excel o stampe in fusione da Word.
Eseguire questo setup solo sulle macchine che dovranno svolgere tali attività di
collegamento ai dati.
""")
