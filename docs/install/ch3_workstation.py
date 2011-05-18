#!/bin/env python
# -*- coding: iso-8859-1 -*-
# ------------------------------------------------------------------------------
# Name:         docs/install/ch3_workstation.py
# Author:       Fabio Cassini <fabio.cassini@gmail.com>
# Created:      2009/08/28
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
###                              CAPITOLO 3                                  ###
###                                                                          ###
################################################################################


heading1("Installazione di X4 Gestione Aziendale")
disc("""
X4 viene installato mediante l'esecuzione del relativo setup, file eseguibile 
con nome nella forma 'x4setup-x.y.zz.exe', dove x.y.zz è la versione; quindi,
ad esempio, l'avvio di x4setup-1.1.26.exe installerà la versione 1.1.26 di X4.
L'installazione avviene tramite una procedura guidata che provvede ad installare
tutti i files necessari ed a configurare Windows per quanto riguarda i programmi
installati.
""")

heading2("Cartelle e files di configurazione")
disc("""
X4 non utilizza in alcun modo il Registry del sistema, se non per quanto 
riguarda le informazioni di installazione/disinstallazione.
La configurazione del software è realizzata mediante files di configurazione,
mentre la configurazione di ogni singola azienda gestita risiede su apposite
tabelle del database specifico dell'azienda stessa.
Vediamo in questo capitolo quali sono i files e le cartelle di configurazione
della workstation (impostazioni relative al programma e le sue funzionalità,
quindi indipendenti dalla singola azienda).
""")

heading2("La cartella di configurazione")
disc("""
Il file di configurazione principale di X4 è config.ini, la cui 
dislocazione sul sistema non è assoluta, ma funzione di alcune variabili.
Normalmente, infatti, esso risiede sulla cartella di configurazione di tutti gli
utenti, la quale, a seconda della versione di Windows utilizzata, si chiama ed 
è posizionata in modo diverso sul disco:
""")
disc("""
Per Windows 2000 e Windows XP:
""")
eg("""
C:\\Documents and settings\\All users\\Dati applicazioni\\X4 Gestione Aziendale
""",after=0.1)
disc("""
Per Windows Vista:
""")
eg("""
C:\\ProgramData\\X4 Gestione Aziendale
""",after=0.1)
disc("""
Per verificare effettivamente quale cartella viene utilizzata, è possibile
da un prompt dei comandi verificare la variabile di sistema 'allusersprofile' e
vedere dove punta:
set ALLUSERSPROFILE
Considerando che su XP tale variabile punta alla cartella home di 'All users', 
alla quale bisogna accodare la cartella 'Dati applicazioni', mentre su Vista 
essa punta alla cartella equivalente su tale sistema.
""")

disc("""
La cartella di configurazione, ove serva, può essere anche impostata a 
piacimento, mediante l'impostazione della variabile di sistema X4_CONFIG_PATH
Questa impostazione generalmente non è necessaria sull'installazione effettiva
del cliente, ma è possibile utilizzarla sulla macchina del sistemista che deve
avere in locale una copia dell'installazione del cliente per ovvi motivi di
debug e/o assistenza.
Il modo migliore di gestire molteplici installazioni di X4 su un singolo PC
(nelle quali la parte eseguibile di X4 è costante, ma varia la configurazione 
della workstation, la licenza d'uso e possibilmente anche personalizzazioni) è
ricorrere a tale variabile prima di avviare X4; ad esempio:
""")
eg("""
set X4_CONFIG_PATH=C:\\x4cfg\\rossi
C:
cd \\Programmi\\X4 Gestione Aziendale
X4.exe
""",after=0.1)
disc("""
Questo avvia X4 indicando come cartella di confgurazione quella spcifica del 
cliente Rossi, che risiede su C:\\x4cfg\\rossi, mentre
""")
eg("""
set X4_CONFIG_PATH=C:\\x4cfg\\bianchi
C:
cd \\Programmi\\X4 Gestione Aziendale
X4.exe
""",after=0.1)
disc("""
avvia X4 indicando come cartella di confgurazione quella spcifica del 
cliente Bianchi, che risiede su C:\\x4cfg\\bianchi.
Al fine di agevolare l'avvio di molteplici installazioni mediante la semplice 
apertura di determinate icone sul pc del sistemista, può essere una soluzione
il ricorso ad un file .bat che automatizzi queste impostazioni, con un contenuto
simile al seguente file batch di esempio c:\\x4run.bat:
""")
eg("""
set X4_CONFIG_PATH=C:\\x4cfg\\%1
C:
cd \\Programmi\\X4 Gestione Aziendale
X4.exe
""",after=0.1)
disc("""
Avendo cura di creare, sotto la cartella x4cfg (il nome è a piacimento, basti 
impostare una cartella generale che conterrà tante sottocartelle quante sono le
aziende gestite), una sottocartella che conterrà le informazioni di configurazione
necessarie, e richiamando il batch con il nome della sottocartella in questione.
Quindi l'avvio di X4 per un'azienda o l'altra coincide con l'esecuzione di:
""")
eg("""
c:\\x4run rossi
""",after=0.1)
disc("""
per avviare X4 con le impostazioni del cliente Rossi, o
""")
eg("""
c:\\x4run bianchi
""",after=0.1)
disc("""
per avviare X4 con le impostazioni del cliente Bianchi.
""")

disc("""
Vista la varietà di percorsi possibili per la cartella di configurazione, ci si
riferirà d'ora in avanti a tale cartella con il nome simbolico CONFIG_DIR.
""")


heading2("I file di configurazione e personalizzazioni programma")
disc("""
Il file di configurazione principale di X4 è, come accennato, il file 
'config.ini', posizionato nella cartella di configurazione menzionata a cui 
ci riferiamo ora con il nome di CONFIG_DIR.
""")
disc("""
Essa contiene i seguenti files, indispensabili:
""")
restartList()
list("""
config.ini, contenente la configurazione della workstation.
""")
list("""
mysql.pswd, contenente la password crittografata dell'utente del database.
""")
disc("""
Eventualmente, possono essere presenti anche i seguenti ulteriori files:
""")
list("""
updates.pswd, contenente la password crittografata dell'utente degli 
aggiornamenti online del programma.
""")
list("""
cartella 'cust', contenente i moduli di personalizzazione del programma.
""")
list("""
cartella 'plugin', contenente gli eventuali moduli plugin per estensione 
delle funzionalità del programma.
""")
list("""
cartella 'addon', contenente gli eventuali moduli addon per estensione 
di determinate funzionalità del programma.
""")


heading2("Installazione in ambito di rete")
disc("""
Oltre ai menzionati files e cartelle di configurazione, specifiche di ogni
macchina sulla quale deve girare X4, ci possono essere anche altre informazioni 
a corredo dell'installazione da condividere con tutti gli utenti X4.
Lo scopo della prima cosa che il setup workstation chiede, ovvero la cosiddetta
'cartella comune', e' proprio consentire l'accentramento in una unica 
cartella di questo materiale, del quale parleremo nella prossima sezione.
Tale cartella non è obbligatoria, per un motivo molto semplice: laddove essa non
venga specificata, verrà assunta come corrispondente alla stessa cartella di 
configurazione del pc, vedasi considerazioni precedenti a proposito di 
CONFIG_DIR.
""")


heading2("La cartella comune")
disc("""
La cartella comune contiene l'eventuale materiale che deve essere condiviso con 
tutte le macchine che eseguiranno X4, come ad esempio:
""")
restartList()
list("""
informazioni sulla licenza d'uso
""")
list("""
definizioni di report personalizzati
""")
disc("""
Vista la varietà di percorsi possibili per la cartella di comune, ci si
riferirà d'ora in avanti a tale cartella con il nome simbolico COMMON_DIR.
""")
disc("""
Nel setup della workstation sono richiesti anche i seguenti percorsi:
""")
restartList()
list("""
File per allegati.  Percorso che conterrà il materiale allegato alle 
informazioni del database mediante il bottone 'Allegati' presente nelle schede 
anagrafiche e nelle principali maschere di dataentry.
Se non specificato, come normalmente avviene, viene settata pari a:
""")
eg("""
COMMON_DIR\\attach_files
""",after=0.1)
list("""
Report personalizzati.  Percorso che conterrà le definizioni di report 
personalizzati specifiche di ogni azienda; il percorso punta ad una cartella 
generica, la quale conterrà una sottocartella specifica per ogni azienda per la
quale si vogliono rendere disponibili determinati report personalizzati.
Il nome di ogni sottocartella relativa alla singola azienda deve essere nella
forma: azienda_XXXXX, dove XXXX è il codice azienda in X4.
Se non specificato, come normalmente avviene, viene settata pari a:
""")
eg("""
COMMON_DIR\\report
""",after=0.1)

disc("""
Nella maschera di setup workstation sono anche presenti i seguenti percorsi:
""")
restartList()
list("""
Definizioni report.  Percorso che contiene le definizioni dei report standard,
forniti a corredo del programma ed installati dal setup di X4.
Normalmente punta a:
""")
eg("""
./report/jrxml
""",after=0.1)
list("""
Immagini.  Percorso che contiene le immagini contenute in alcuni report standard,
forniti a corredo del programma ed installati dal setup di X4.
Normalmente punta a:
""")
eg("""
./report/immagini
""",after=0.1)
list("""
Pdf generati.  Percorso che contiene tutte le stampe che si effettuano in X4.
Normalmente punta a:
""")
eg("""
./report/pdf
""",after=0.1)
disc("""
Può risultare utile far puntare tale percorso ad una cartella diversa, 
immediatamente consultabile dall'utente nel caso voglia riprendere a posteriori 
una determinata stampa fatta; sono gestite le variabili di sistema 'userprofile' 
e 'allusersprofile', che puntano rispettivamente alla cartella 'home' 
dell'utente e alla cartella 'home' di tutti gli utenti.
Ad esempio, impostando il seguente percorso:
""")
eg("""
%userprofile%\\Documenti\\Stampe X4
""",after=0.1)
disc("""
si otterrà la produzione delle stampe di X4 nella cartella 'Stampe X4' 
posizionata nella cartella 'Documenti' dell'utente specifico.
""")
disc("""
N.B.  La parte iniziale del percorso, './', sta ad indicare che il percorso è relativo
alla dislocazione del programma eseguibile, normalmente installato nella 
cartella:
""")
eg("""
C:\\Programmi\\X4 Gestione Aziendale
""",after=0.1)
disc("""
E' consigliabile non alterare il contenuto di tale percorso, ove non specificato 
diversamente.
""")


heading2("Setup postazione")
disc("""
Ora che abbiamo chiarito i concetti relativi alle varie cartelle di 
configurazione, vediamo quali informazioni richiede la maschera di 'Setup 
postazione'.  Questa è suddivisa in alcuni blocchi, come di seguito evidenziato.
""")

heading3("Sito installazione")
restartList()
list("""
Cod.Identificativo:  E' una sigla che identifica la rete nella quale si sta 
lavorando.  Normalmente pari alla dicitura 'sede', nel caso di installazione in
altro sito remoto (sede distaccata, ufficio vendite distaccato, ecc.) occorre 
specificare una sigla diversa.
""")
list("""
Cartella comune.  Vedi considerazioni su COMMON_DIR.
""")

heading3("Database")
restartList()
list("""
Descrizione:  E' la descrizione che comparirà nella maschera di login ad ogni
accesso, consente di descrivere umanamente il server a cui si sta cercando
di accedere.
""")
list("""
Server URL: E' l'indirizzo IP o il nome LAN della macchina che agisce da server
del database.
""")
list("""
Porta: E' la porta TCP/IP alla quale richiedere l'accesso sul server.  Il valore
di default della porta per MySQL è 3306.
""")
list("""
Utente/Password: E' l'accoppiata nome utente e password dell'utente di MySQL che
verrà utilizzata per stabilire la connessione.
""")
list("""
Bottone 'Test': Consente di verificare l'esattezza dei parametri di connessione
al database; viene restituito un messaggio di avvenuta connessione o meno.
""")
disc("""
Tramite il bottone 'Aggiungi Server' è possibile specificare altri insiemi di 
configurazione database, nel caso in cui la macchina debba accedere a più di un 
server a seconda di determinate condizioni.
""")

heading3("Cartelle")
restartList()
list("""
File per allegati.
""")
list("""
Definizioni report.
""")
list("""
Immagini.
""")
list("""
Pdf generati.
""")
list("""
Report personalizzati.
""")
disc("""
Per tutte queste cartelle vedasi considerazioni all'inizio del capitolo.
""")
list("""
Stampante predefinita:  E' possibile impostare una determinata stampante di 
Windows come stampante predefinita per le stampe dirette (vedi seguito).
""")
list("""
Etichettatrice:  E' possibile impostare una determinata stampante di 
Windows come stampante predefinita per alcuni tipi di stampa diretta (etichette:
indirizzi, codici a b arre, ecc.).
""")
list("""
DDE: Attivando questa opzione, sarà possibile ottimizzare i meccanismi che 
governano la gestione dei files pdf una volta generati.
La mancata spunta di questo parametro farà si che i pdf, una volta generati, 
vengano dati in pasto al sistema operativo che li dovrebbe aprire esattamente 
come accade quando si fa doppio click su un file pdf (qualsiasi lettore di pdf è
consentito, non solo Acrobat).
La spunta di questo parametro invece attiva il meccanismo DDE, il quale consente
il colloquio tra X4 ed Adobe Reader (da versione 8 in poi) in modo tale da
permettere sia l'anteprima classica nella finestra propria di Adobe, sia l'avvio
della stampa automaticamente senza l'obbligo di passare dall'anteprima.
In questo caso è possibile selezionare la stampante da usare ed il numero di 
copie da stampare nel pannello di selezione report di X4. Attenzione che alcune
caratteristiche di stampa in Adobe Reader, modificabili dall'utente, vengono
memorizzate in Adobe in modo da riutilizzarle automaticamente nelle stampe
successive, anche dopo aver chiuso Adobe.  Caratteristiche come ad esempio il 
tipo di ridimensionamento della stampa, stampa opuscolo ecc. sono di fatto 
gestite in tale modo, quindi la stampa 'diretta' da X4 potrebbe portare con se
tali impostazioni precedentemente utilizzate, anche se erano state attivate da
stampe di documenti pdf indipendenti da X4 stesso.
""")
list("""
Comportamento di default del pannello di stampa: a completamento di quanto 
sopra esposto, questa impostazione consente di preimpostare il tipo di
comportamento nelle stampe.  Valido solo in concomitanza di DDE attivao.
""")

heading3("Collegamento ad Internet")
restartList()
list("""
Questa workstation dispone di un accesso permanente: spuntanto tale voce,
nei punti di programma in cui deve essere stabilita una connessione verso
qualche server web o comunque inerente la rete pubblica, non verrà richiesta 
alcuna autorizzazione, mentre la mancanza di tale spunta attiverà tale richiesta 
ad ogni connessione.
""")

heading3("Esportazione dati: Formato file .CSV")
restartList()
list("""
Tutte le griglie presenti nel programma sono esportabili in Excel o similare 
mediante click destro su una intestazione di colonna qualsiasi e scelta nel menu
contestuale della voce 'Esporta file CSV'.
CSV è (o dovrebbe essere) un formato standard di interscambio dati: file di 
testo con valori delimitati e separati, come dice l'acronimo stesso, dalla 
virgola.
Ovviamente in Windows lo standard è diverso, perché normalmente in Excel la 
separazione tra due informazioni avviene mediante l'utilizzo del carattere di
punto e virgola invece che del carattere virgola.
Qui è possibile agire su questo tipo di comportamento: spuntando la voce 
'Esporta i valori come presentati nelle griglie' (scelta di default) verrà 
utilizzato, come da standard, il carattere virgola (opzione che va bene nel caso
in cui sia installato OpenOffice invece di Microsoft Office).
La mancata spunta di tale voce attiva le tre opzioni successive:
Separatore colonne (virgola o punto e virgola, se si usa Excel), Delimitatore 
colonna (standard = doppio apice), Impiego dei delimitatori (standard = Testo).
""")

heading3("Aspetto e navigazione")
restartList()
list("""
Sulle griglie, il tasto TAB naviga su:
Le celle della griglia = una volta che la griglia ha il focus della tastiera,
questa consentira il passaggio al controllo successivo (esterno alla griglia)
mediante Ctrl-Tab, poiché la pressione del tasto Tab provocherà la navigazione
tra le celle della griglia stessa.
I controlli adiacenti alla griglia = Il tasto Tab premuto all'interno della
griglia provocherà, contrariamente a prima, l'uscita dalla griglia stessa ed il
posizionamento del cursore nel controllo immediatamente successivo alla griglia.
""")
disc("""
E' consigliabile lasciare la selezione sulla prima voce, altrimenti l'utente
potrebbe rimanere spiazzato nel momento in cui, volendosi spostare sulla cella
adiacente a quella in editazione all'interno di una determinata griglia, 
premendo il tasto Tab, uscirebbe dalla griglia di interesse.
""")
