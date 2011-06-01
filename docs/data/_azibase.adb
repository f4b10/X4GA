<tablesBackup version="1" database="x4__azibase" content="all" comment="">
    <table name="bilmas">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="14">
            <row id="218" codice="A" descriz="CASSA E BANCHE" tipo="P"  />
            <row id="219" codice="B" descriz="CREDITI" tipo="P"  />
            <row id="220" codice="C" descriz="DEBITI" tipo="P"  />
            <row id="221" codice="D" descriz="RATEI RISCONTI" tipo="P"  />
            <row id="222" codice="E" descriz="MAGAZZINO" tipo="P"  />
            <row id="223" codice="F" descriz="IMMOBILIZZAZ." tipo="P"  />
            <row id="224" codice="G" descriz="FONDI" tipo="P"  />
            <row id="225" codice="H" descriz="CAPITALE NETTO" tipo="P"  />
            <row id="226" codice="O" descriz="COSTI ESERCIZIO" tipo="E"  />
            <row id="227" codice="N" descriz="RIMANENZE" tipo="E"  />
            <row id="228" codice="P" descriz="COSTI ASSESTAM." tipo="E"  />
            <row id="229" codice="U" descriz="RICAVI ESERCIZ." tipo="E"  />
            <row id="230" codice="V" descriz="RICAVI ASSEST." tipo="E"  />
            <row id="231" codice="W" descriz="CONTI TRANSIT." tipo="O"  />
        </content>
    </table>
    <table name="bilcon">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bilmas" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_bilmas,codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="id_bilmas,descriz" />
        </structure>
        <content rows="52">
            <row id="232" codice="A/AA" descriz="CASSA" id_bilmas="218"  />
            <row id="233" codice="A/AB" descriz="BANCHE" id_bilmas="218"  />
            <row id="234" codice="B/BA" descriz="CREDITI CLIENTI" id_bilmas="219"  />
            <row id="235" codice="B/BH" descriz="EFFETTI ATTIVI" id_bilmas="219"  />
            <row id="236" codice="B/BE" descriz="CREDITI DIVERSI" id_bilmas="219"  />
            <row id="237" codice="B/BG" descriz="CREDITI ERARIO" id_bilmas="219"  />
            <row id="238" codice="D/DA" descriz="RATEI RISC. ATT" id_bilmas="221"  />
            <row id="239" codice="F/FA" descriz="TERRENI FABBRIC" id_bilmas="223"  />
            <row id="240" codice="F/FC" descriz="CESPITI AMMORT." id_bilmas="223"  />
            <row id="241" codice="F/FE" descriz="SPESE PLURIENN." id_bilmas="223"  />
            <row id="242" codice="F/FG" descriz="IMMOB. FINANZ." id_bilmas="223"  />
            <row id="243" codice="E/EA" descriz="MERCI IN MAGAZZ" id_bilmas="222"  />
            <row id="244" codice="C/CA" descriz="FORNITORI MERCI" id_bilmas="220"  />
            <row id="245" codice="C/CE" descriz="DEBITI DIVERSI" id_bilmas="220"  />
            <row id="246" codice="C/CG" descriz="DEBITI ERARIO" id_bilmas="220"  />
            <row id="247" codice="C/CI" descriz="DEBITI FINANZ." id_bilmas="220"  />
            <row id="248" codice="C/CC" descriz="EFFETTI PASSIVI" id_bilmas="220"  />
            <row id="249" codice="C/CM" descriz="DEBITI V/DIPEND" id_bilmas="220"  />
            <row id="250" codice="G/GA" descriz="FONDI AMMORTAM." id_bilmas="224"  />
            <row id="251" codice="G/GC" descriz="FONDI ACCANTON." id_bilmas="224"  />
            <row id="252" codice="D/DB" descriz="RATEI RISC.PASS" id_bilmas="221"  />
            <row id="253" codice="H/HA" descriz="CAPITALE NETTO" id_bilmas="225"  />
            <row id="254" codice="O/OA" descriz="ACQUISTO BENI" id_bilmas="226"  />
            <row id="255" codice="O/OC" descriz="ACQ. SERVIZI" id_bilmas="226"  />
            <row id="256" codice="O/OG" descriz="ONERI DIPENDENT" id_bilmas="226"  />
            <row id="257" codice="O/OI" descriz="COMPENSI TERZI" id_bilmas="226"  />
            <row id="258" codice="O/OM" descriz="SPESE GENERALI" id_bilmas="226"  />
            <row id="259" codice="O/OE" descriz="COSTI COMMERC." id_bilmas="226"  />
            <row id="260" codice="O/OO" descriz="ONERI FINANZIAR" id_bilmas="226"  />
            <row id="261" codice="P/PA" descriz="AMMORTAMENTI" id_bilmas="228"  />
            <row id="262" codice="P/PC" descriz="ACCANTONAMENTI" id_bilmas="228"  />
            <row id="263" codice="N/NA" descriz="RIMAN. INIZIALI" id_bilmas="227"  />
            <row id="264" codice="P/PE" descriz="SOPRAVV.PASSIVE" id_bilmas="228"  />
            <row id="265" codice="U/UA" descriz="RICAVI VENDITA" id_bilmas="229"  />
            <row id="266" codice="U/UC" descriz="ALTRI RICAVI" id_bilmas="229"  />
            <row id="267" codice="U/UE" descriz="PROVENTI FINANZ" id_bilmas="229"  />
            <row id="268" codice="V/VA" descriz="SOPRAVV.ATTIVE" id_bilmas="230"  />
            <row id="269" codice="N/NB" descriz="RIMAN. FINALI" id_bilmas="227"  />
            <row id="270" codice="W/WA" descriz="APERTURA CHIUS." id_bilmas="231"  />
            <row id="271" codice="C/CB" descriz="FORNIT. SERVIZI" id_bilmas="220"  />
            <row id="272" codice="X/XG" descriz="IMMOBILIZZI"  />
            <row id="273" codice="X/XA" descriz="LIQUIDITA' IMM."  />
            <row id="274" codice="X/XC" descriz="CREDITI A BREVE"  />
            <row id="275" codice="X/XE" descriz="DISPONIBILITA'"  />
            <row id="276" codice="Y/YA" descriz="DEBITI A BREVE"  />
            <row id="277" codice="Y/YC" descriz="DEBITI A LUNGO"  />
            <row id="278" codice="Y/YE" descriz="CAPITALE NETTO"  />
            <row id="279" codice="Z/ZA" descriz="UTILE LORDO"  />
            <row id="280" codice="Z/ZC" descriz="UTILE OPERATIVO"  />
            <row id="281" codice="Z/ZE" descriz="UTILE PRE-TASSE"  />
            <row id="282" codice="Z/ZG" descriz="UTILE NETTO"  />
            <row id="302" codice="G/GB" descriz="FONDI PLUSVAL." id_bilmas="224"  />
        </content>
    </table>
    <table name="pdctip">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bilmas" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bilcon" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bilcee" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcrange" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="19">
            <row id="205" codice="B" descriz="BANCA" tipo="B" id_bilcee="0" id_pdcrange="1"  />
            <row id="206" codice="C" descriz="CLIENTI" tipo="C" id_bilmas="219" id_bilcon="234" id_bilcee="0" id_pdcrange="2"  />
            <row id="207" codice="F" descriz="FORNITORI" tipo="F" id_bilmas="220" id_bilcon="244" id_bilcee="0" id_pdcrange="3"  />
            <row id="208" codice="A" descriz="CASSA" tipo="A" id_bilcee="0" id_pdcrange="1"  />
            <row id="209" codice="R" descriz="RICAVI CORRENTI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="210" codice="S" descriz="SPESE CORRENTI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="211" codice="I" descriz="CONTI IVA" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="212" codice="T" descriz="CONTI ASSESTAM." tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="213" codice="U" descriz="ALTRE ATTIVITA'" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="214" codice="V" descriz="ALTRE PASSIVITA" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="215" codice="W" descriz="ALTRI COSTI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="216" codice="X" descriz="ALTRI RICAVI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="217" codice="Y" descriz="CONTI APERT/CH." tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="283" codice="G" descriz="IMMOBILIZZAZION" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="284" codice="D" descriz="PORTAFOGLIO ATT" tipo="D" id_bilcee="0" id_pdcrange="1"  />
            <row id="285" codice="L" descriz="ERARIO" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="286" codice="M" descriz="DIPENDENTI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="287" codice="N" descriz="FONDI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
            <row id="288" codice="Z" descriz="RATEI RISCONTI" tipo="X" id_bilcee="0" id_pdcrange="1"  />
        </content>
    </table>
    <table name="aliqiva">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="perciva" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="percind" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralcc1" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralcc2" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralcc3" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralcc4" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralfc1" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralfc2" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralfc3" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralfc4" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="modo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="24">
            <row id="198" codice="38" descriz="IVA 38%" tipo="" perciva="38.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="199" codice="I1" descriz="IVA 20% INDED. AL 50% " tipo="" perciva="20.0" percind="50.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="200" codice="I2" descriz="IVA INDEDUC.20%" tipo="" perciva="20.0" percind="100.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="201" codice="NI" descriz="NON IMP. ART.15" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="204" codice="NS" descriz="NON IMP.AR.15/2" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="289" codice="N2" descriz="F.C.I.ART.1-2-3" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="F"  />
            <row id="290" codice="N3" descriz="NON TERRIT. A.7" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="291" codice="N4" descriz="F.C.I.A.74 C1,2" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="F"  />
            <row id="292" codice="E1" descriz="ESENTE ART.10" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="E"  />
            <row id="303" codice="N9" descriz="NON IMP. ART- 9" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="304" codice="04" descriz="IVA 4%" tipo="" perciva="4.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="305" codice="I3" descriz="IVA INDED. 19%" tipo="" perciva="19.0" percind="100.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="306" codice="12" descriz="IVA 12%" tipo="" perciva="12.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="307" codice="14" descriz="I.V.A. IND.4" tipo="" perciva="4.0" percind="100.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="308" codice="N5" descriz="NON IMP ART 8" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="309" codice="C4" descriz="IVA 4% CEE" tipo="" perciva="4.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="310" codice="C9" descriz="IVA 9% CEE" tipo="" perciva="9.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="311" codice="C2" descriz="IVA 10% CEE" tipo="C" perciva="10.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="312" codice="C3" descriz="IVA 20% CEE" tipo="C" perciva="20.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="313" codice="N6" descriz="NON IMP ART 26" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="315" codice="10" descriz="IVA 10%" tipo="" perciva="10.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="316" codice="41" descriz="IVA COMUNITARIA" tipo="" perciva="0.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="N"  />
            <row id="318" codice="20" descriz="IVA 20%" tipo="" perciva="20.0" percind="0.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
            <row id="321" codice="I4" descriz="IVA INDETR. 20%" tipo="" perciva="20.0" percind="100.0" pralcc1="0" pralcc2="0" pralcc3="0" pralcc4="0" pralfc1="0" pralfc2="0" pralfc3="0" pralfc4="0" modo="I"  />
        </content>
    </table>
    <table name="agenti">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cap" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="piva" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numcel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="email" type="varchar(80)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="banca" type="varchar(80)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="abi" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cab" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numcc" type="varchar(12)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="iban" type="varchar(27)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_zona" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noprovvig" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="siteurl" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="2">
            <row id="1" codice="A1" descriz="AGENTE 01" indirizzo="INDIRIZZO AGENTE 01" cap="18038" citta="SANREMO" prov="IM" piva="01010101010" numtel="" numtel2="" numcel="" numfax="" email="" noprovvig="0" siteurl=""  />
            <row id="2" codice="A2" descriz="AGENTE 02" indirizzo="" cap="" citta="" prov="" piva="" numtel="" numtel2="" numcel="" numfax="" email="" noprovvig="0" siteurl=""  />
        </content>
    </table>
    <table name="zone">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="4">
            <row id="1" codice="1" descriz="NORD"  />
            <row id="2" codice="2" descriz="CENTRO"  />
            <row id="3" codice="3" descriz="SUD"  />
            <row id="4" codice="4" descriz="ESTERO"  />
        </content>
    </table>
    <table name="valute">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="cambio" type="decimal(22,6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="2">
            <row id="319" codice="LI" descriz="LIRE ITALIANE" cambio="1936.27"  />
            <row id="320" codice="EU" descriz="EURO" cambio="1.0"  />
        </content>
    </table>
    <table name="modpag">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="contrass" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askbanca" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askspese" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="modocalc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipoper" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="finemese" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numscad" type="tinyint(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="mesi1" type="tinyint(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="mesitra" type="tinyint(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sc1noeff" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sc1iva" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sc1perc" type="decimal(3,0)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcpi" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg01" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg02" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg03" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg04" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg05" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg06" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg07" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg08" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg09" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg10" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg11" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg12" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg13" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg14" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg15" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg16" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg17" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg18" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg19" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg20" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg21" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg22" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg23" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg24" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg25" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg26" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg27" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg28" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg29" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg30" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg31" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg32" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg33" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg34" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg35" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="gg36" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ggextra" type="int(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="14">
            <row id="202" codice="1" descriz="CONTANTI" tipo="C" contrass="0" askbanca="0" askspese="0" modocalc="D" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0"  />
            <row id="203" codice="2" descriz="RIMESSA DIRETTA" tipo="C" contrass="0" askbanca="0" askspese="1" modocalc="D" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="0" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0" gg13="0" gg14="0" gg15="0" gg16="0" gg17="0" gg18="0" gg19="0" gg20="0" gg21="0" gg22="0" gg23="0" gg24="0" gg25="0" gg26="0" gg27="0" gg28="0" gg29="0" gg30="0" gg31="0" gg32="0" gg33="0" gg34="0" gg35="0" gg36="0" ggextra="0"  />
            <row id="293" codice="32" descriz="R.B. 60GG D.F." tipo="R" contrass="0" askbanca="1" askspese="1" modocalc="D" tipoper="G" finemese="0" numscad="2" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="30" gg02="30" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0"  />
            <row id="294" codice="11" descriz="PAGATO" tipo="C" contrass="1" askbanca="1" askspese="1" modocalc="S" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="0" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0" gg13="0" gg14="0" gg15="0" gg16="0" gg17="0" gg18="0" gg19="0" gg20="0" gg21="0" gg22="0" gg23="0" gg24="0" gg25="0" gg26="0" gg27="0" gg28="0" gg29="0" gg30="0" gg31="0" gg32="0" gg33="0" gg34="0" gg35="0" gg36="0"  />
            <row id="295" codice="12" descriz="BONIFICO BAN 30" tipo="B" contrass="0" askbanca="0" askspese="0" modocalc="S" tipoper="M" finemese="0" numscad="1" mesi1="1" mesitra="1" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="30" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0"  />
            <row id="296" codice="13" descriz="FACTOR" tipo="C" contrass="0" askbanca="0" askspese="0" modocalc="D" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="30"  />
            <row id="297" codice="33" descriz="R.B. 90 G.G.D_F" tipo="R" contrass="0" askbanca="1" askspese="1" modocalc="D" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="90" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0"  />
            <row id="298" codice="31" descriz="R.B. 30 G.G.D.F" tipo="R" contrass="0" askbanca="1" askspese="1" modocalc="D" tipoper="G" finemese="1" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="30" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0" gg13="0" gg14="0" gg15="0" gg16="0" gg17="0" gg18="0" gg19="0" gg20="0" gg21="0" gg22="0" gg23="0" gg24="0" gg25="0" gg26="0" gg27="0" gg28="0" gg29="0" gg30="0" gg31="0" gg32="0" gg33="0" gg34="0" gg35="0" gg36="0"  />
            <row id="299" codice="42" descriz="R.B. 30/60 GG D F" tipo="R" contrass="0" askbanca="1" askspese="1" modocalc="S" tipoper="M" finemese="0" numscad="2" mesi1="1" mesitra="1" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="120" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0" gg13="0" gg14="0" gg15="0" gg16="0" gg17="0" gg18="0" gg19="0" gg20="0" gg21="0" gg22="0" gg23="0" gg24="0" gg25="0" gg26="0" gg27="0" gg28="0" gg29="0" gg30="0" gg31="0" gg32="0" gg33="0" gg34="0" gg35="0" gg36="0"  />
            <row id="301" codice="15" descriz="CONTRASSEGNO" tipo="C" contrass="1" askbanca="0" askspese="1" modocalc="D" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="0" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0" gg13="0" gg14="0" gg15="0" gg16="0" gg17="0" gg18="0" gg19="0" gg20="0" gg21="0" gg22="0" gg23="0" gg24="0" gg25="0" gg26="0" gg27="0" gg28="0" gg29="0" gg30="0" gg31="0" gg32="0" gg33="0" gg34="0" gg35="0" gg36="0"  />
            <row id="314" codice="44" descriz="OMAGGIO" tipo="R" contrass="0" askbanca="1" askspese="1" modocalc="D" tipoper="G" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0"  />
            <row id="317" codice="21" descriz="RIM.DIR.60 GGDF" tipo="C" contrass="0" askbanca="0" askspese="0" modocalc="S" tipoper="M" finemese="0" numscad="1" mesi1="2" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="0" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0"  />
            <row id="322" codice="45" descriz="RIBA 30.09." tipo="C" contrass="0" askbanca="0" askspese="0" modocalc="D" tipoper="M" finemese="0" numscad="1" mesi1="0" mesitra="0" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="0" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0"  />
            <row id="326" codice="03" descriz="BON BAN 60/90" tipo="B" contrass="0" askbanca="0" askspese="0" modocalc="S" tipoper="M" finemese="0" numscad="2" mesi1="2" mesitra="1" sc1noeff="0" sc1iva="0" sc1perc="0.0" gg01="0" gg02="0" gg03="0" gg04="0" gg05="0" gg06="0" gg07="0" gg08="0" gg09="0" gg10="0" gg11="0" gg12="0" gg13="0" gg14="0" gg15="0" gg16="0" gg17="0" gg18="0" gg19="0" gg20="0" gg21="0" gg22="0" gg23="0" gg24="0" gg25="0" gg26="0" gg27="0" gg28="0" gg29="0" gg30="0" gg31="0" gg32="0" gg33="0" gg34="0" gg35="0" gg36="0" ggextra="0"  />
        </content>
    </table>
    <table name="travet">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(255)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="cap" type="char(8)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="codfisc" type="char(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="email" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nazione" type="char(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="piva" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="siteurl" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_stato" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="3">
            <row id="1" codice="CDF" descriz="CURSOR DEI FLORIS"  />
            <row id="2" codice="TNT" descriz="CURSOR TNT LOC. GOMBI DELLA LUNA - CHIUSAVECCHIA"  />
            <row id="3" codice="CB" descriz="BARTOLINUS SPA - V DON GIOVANNI MINZONI 10 - MEDIOLANUM"  />
        </content>
    </table>
    <table name="speinc">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="importo" type="decimal(9,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="2">
            <row id="21" codice="1" descriz="SCAGLIONE #1" importo="0.0" id_aliqiva="318"  />
            <row id="22" codice="2" descriz="SCAGLIONE # 2" importo="3.5" id_aliqiva="318"  />
        </content>
    </table>
    <table name="regiva">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="intestaz" type="varchar(160)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="intanno" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="intpag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="lastprtnum" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="lastprtdat" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noprot" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="rieponly" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="stacosric" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="3">
            <row id="85" codice="A" descriz="ACQUISTI" tipo="A" intanno="2009" intpag="15" lastprtnum="145" lastprtdat="2009-06-30"  />
            <row id="86" codice="V" descriz="VENDITE" tipo="V" intestaz="" intanno="2009" intpag="32" lastprtnum="368" lastprtdat="2009-06-30" noprot="0" rieponly="0" stacosric="0"  />
            <row id="140" codice="C" descriz="CEE" tipo="C"  />
        </content>
    </table>
    <table name="cfgcontab">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="esercizio" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_regiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="regivadyn" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datdoc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numdoc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numiva" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="modpag" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcf" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcfscon" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcfimp" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcfsgn" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcfabb" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcfspe" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pcfins" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pades" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdctippa" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pasegno" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cpdes" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdctipcp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pralcf" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcrow1" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="camsegr1" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="quaivanob" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="davscorp" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="event_msg" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tipevent" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="60">
            <row id="27" codice="01" descriz="FATT. VENDITA" tipo="I" esercizio="0" id_regiva="86" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="a cliente " id_pdctippa="206" pasegno="D" cpdes="CONTROPAR." id_pdctipcp="209"  />
            <row id="28" codice="02" descriz="FATT. ACQUISTO" tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="0" numdoc="0" numiva="1" modpag="1" pcf="1" pcfscon="0" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="da fornit." id_pdctippa="207" pasegno="A" cpdes="CONTROPAR." id_pdctipcp="210" pralcf="0" camsegr1="0" quaivanob="0" davscorp="0" event_msg=""  />
            <row id="29" codice="03" descriz="NOTA CREDITO EM" tipo="I" esercizio="0" id_regiva="86" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="2" pcfsgn="+" pcfabb="" pcfspe="" pades="a cliente " id_pdctippa="206" pasegno="A" cpdes="CONTROPAR." id_pdctipcp="209"  />
            <row id="30" codice="04" descriz="NOTA CREDITO RC" tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="2" pcfsgn="+" pcfabb="" pcfspe="" pades="da fornit." id_pdctippa="207" pasegno="D" cpdes="CONTROPAR." id_pdctipcp="210"  />
            <row id="31" codice="21" descriz="INCASSO" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="+" pcfabb="P" pcfspe="0" pcfins="0" pades="da clienti" id_pdctippa="206" pasegno="A" cpdes="a cassa   " id_pdctipcp="208" pralcf="0"  />
            <row id="32" codice="22" descriz="BONIFICO CLI." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="+" pcfabb="P" pcfspe="" pades="da Cliente" id_pdctippa="206" pasegno="A" cpdes="a banca   " id_pdctipcp="205"  />
            <row id="33" codice="23" descriz="REINTEGRO" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="da banca  " id_pdctippa="205" pasegno="A" cpdes="a cassa   " id_pdctipcp="208"  />
            <row id="34" codice="24" descriz="VERSAMENTO" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="0" pcfscon="0" pcfimp="" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="da cassa  " id_pdctippa="208" pasegno="A" cpdes="a banca   " id_pdctipcp="205" pralcf="0"  />
            <row id="35" codice="25" descriz="PAGAM. DA CASSA" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="+" pcfabb="A" pcfspe="0" pcfins="0" pades="a fornit. " id_pdctippa="207" pasegno="D" cpdes="da cassa  " id_pdctipcp="208" pralcf="0"  />
            <row id="36" codice="26" descriz="PAGAM. da BANCA" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="+" pcfabb="A" pcfspe="" pades="a fornit. " id_pdctippa="207" pasegno="D" cpdes="da banca  " id_pdctipcp="205"  />
            <row id="37" codice="32" descriz="ACCREDITO R.B." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="A BANCA   " id_pdctippa="205" pasegno="D" cpdes="EFFETTI   " id_pdctipcp="284"  />
            <row id="38" codice="41" descriz="ABBUONO" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="" pcfimp="2" pcfsgn="+" pcfabb="" pcfspe="" pades="ANAGRAFICA" pasegno="D" cpdes="CONTROPAR."  />
            <row id="39" codice="AC" descriz="ACCANTONAMENTO" tipo="S" esercizio="1" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="FONDO     " id_pdctippa="287" pasegno="A" cpdes="COSTO     " id_pdctipcp="212"  />
            <row id="40" codice="AM" descriz="AMMORTAMENTO" tipo="S" esercizio="1" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="FONDO     " id_pdctippa="287" pasegno="A" cpdes="COSTO     " id_pdctipcp="212"  />
            <row id="41" codice="10" descriz="BOLLA DOGANALE" tipo="E" esercizio="0" id_regiva="85" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="DA DOGANA " id_pdctippa="207" pasegno="A" cpdes="DA DOGANA " id_pdctipcp="207"  />
            <row id="42" codice="27" descriz="BONIFICO FOR." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="+" pcfabb="A" pcfspe="" pades="A FORNIT. " id_pdctippa="207" pasegno="D" cpdes="DA BANCA  " id_pdctipcp="205"  />
            <row id="43" codice="11" descriz="CORRISP. INCAS." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="0" pcfscon="0" pcfimp="" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="Cassa     " id_pdctippa="208" pasegno="D" cpdes="RICAVO    " id_pdctipcp="209" pralcf="0"  />
            <row id="44" codice="42" descriz="CONTRIBUTI" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="INPS C.C. " id_pdctippa="214" pasegno="A" cpdes="ONERI SOC." id_pdctipcp="210"  />
            <row id="45" codice="48" descriz="ERRATA REGISTR." tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CONTO     " pasegno="D" cpdes="CONTO     "  />
            <row id="46" codice="05" descriz="VENDITA BENI ST" tipo="I" esercizio="0" id_regiva="86" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="A DIVERSI " id_pdctippa="213" pasegno="D" cpdes="IMMOBILIZ." id_pdctipcp="283"  />
            <row id="47" codice="06" descriz="ACQUISTO IMMOB." tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="FORNITORE " id_pdctippa="207" pasegno="A" cpdes="IMMOBILIZ." id_pdctipcp="283"  />
            <row id="48" codice="19" descriz="FATTURA ESTERO" tipo="S" esercizio="0" id_regiva="85" regivadyn="0" datdoc="1" numdoc="1" numiva="" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="FORNIT.EST" id_pdctippa="207" pasegno="A" cpdes="SPESE     " id_pdctipcp="210"  />
            <row id="49" codice="07" descriz="FATT. RICEVUTA" tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="FORNITORE " id_pdctippa="207" pasegno="A" cpdes="CONTROPAR." id_pdctipcp="210"  />
            <row id="50" codice="GA" descriz="GIR.APER.CL./D" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CONTO     " id_pdctippa="217" pasegno="A" cpdes="CONTROPAR." id_pdctipcp="206"  />
            <row id="51" codice="GC" descriz="GIROC. CHIUSURA" tipo="C" esercizio="1" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CONTO     " pasegno="D" cpdes="CONTROPAR."  />
            <row id="52" codice="GD" descriz="GIROCONTO a DIV" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="Conto     " cpdes="CONTROPAR."  />
            <row id="53" codice="28" descriz="INSOLUTO" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="1" pades="DA CLIENTE" id_pdctippa="206" pasegno="D" cpdes="CONTROPAR." id_pdctipcp="284" pralcf="0" camsegr1="0" quaivanob="0" davscorp="0" event_msg=""  />
            <row id="54" codice="08" descriz="PARCELLA CONS." tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="CONSULENTE" id_pdctippa="207" pasegno="A" cpdes="SPESE     " id_pdctipcp="210"  />
            <row id="55" codice="43" descriz="SALARI E STIP." tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="RETR.LORDE" id_pdctippa="210" pasegno="D" cpdes="CASSA     " id_pdctipcp="208"  />
            <row id="56" codice="29" descriz="RICEVUTA BANC." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="+" pcfabb="" pcfspe="" pades="A CLIENTE " id_pdctippa="206" pasegno="A" cpdes="effetti   " id_pdctipcp="284"  />
            <row id="57" codice="30" descriz="RICHIAMA EFFET." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="-" pcfabb="" pcfspe="" pades="A CLIENTE " id_pdctippa="206" pasegno="D" cpdes="EFFETTI   " id_pdctipcp="284"  />
            <row id="58" codice="RF" descriz="RIMANZE FINALI" tipo="S" esercizio="1" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="RIMANENZE " id_pdctippa="212" pasegno="D" cpdes="RICAVI    " id_pdctipcp="209"  />
            <row id="59" codice="31" descriz="RIMBORSO" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="1" pcfimp="2" pcfsgn="-" pcfabb="P" pcfspe="" pades="A CLIENTE " id_pdctippa="206" pasegno="D" cpdes="CONTO FIN."  />
            <row id="60" codice="44" descriz="RITENUTA IRPEF" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CONSULENTE" id_pdctippa="207" pasegno="D" cpdes="ERARIO    " id_pdctipcp="285"  />
            <row id="61" codice="RS" descriz="RATEO-RISCONTO" tipo="C" esercizio="1" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="RATEI/RISC" id_pdctippa="288" cpdes="CONTROPAR."  />
            <row id="62" codice="47" descriz="SPESE DIVERSE" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="SPESA     " id_pdctippa="210" pasegno="D" cpdes="CONTROPAR." id_pdctipcp="206"  />
            <row id="63" codice="09" descriz="SCHEDA CARBUR." tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="0" numdoc="0" numiva="1" modpag="" pcf="0" pcfscon="0" pcfimp="" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="SCHEDA    " id_pdctippa="207" pasegno="A" cpdes="SPESA     " id_pdctipcp="210" pralcf="0" camsegr1="0" quaivanob="0" davscorp="1" event_msg=""  />
            <row id="64" codice="45" descriz="VERSAM. ERARIO" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="ERARIO    " id_pdctippa="285" pasegno="D" cpdes="BANCA     " id_pdctipcp="205"  />
            <row id="65" codice="46" descriz="VERSAMENTO IVA" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="IVA RIEP. " id_pdctippa="211" pasegno="D" cpdes="CONTROPAR." id_pdctipcp="205"  />
            <row id="66" codice="ZC" descriz="PARTITE CLIENTE" tipo="P" esercizio="" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="Cliente   " id_pdctippa="206" cpdes="          "  />
            <row id="67" codice="ZF" descriz="PARTITE FORNIT." tipo="P" esercizio="" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="Fornitore " id_pdctippa="207" cpdes="          "  />
            <row id="68" codice="GE" descriz="GIROCONTO E.P." tipo="C" esercizio="1" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CONTO     " pasegno="D" cpdes="CONTROPAR."  />
            <row id="69" codice="50" descriz="INT.ATT.BANCARI" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="BANCA     " id_pdctippa="205" pasegno="D" cpdes="INT.ATT.  " id_pdctipcp="209"  />
            <row id="70" codice="51" descriz="ONERI BANCARI" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="BANCA     " id_pdctippa="205" pasegno="A" cpdes="CONTROPAR." id_pdctipcp="210"  />
            <row id="71" codice="52" descriz="UTILI SU CAMBI" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="BANCA     " id_pdctippa="205" pasegno="D" cpdes="UTILI     " id_pdctipcp="209"  />
            <row id="72" codice="53" descriz="PERDITE CAMBI" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="BANCA     " id_pdctippa="205" pasegno="A" cpdes="PERDITE   " id_pdctipcp="210"  />
            <row id="73" codice="54" descriz="INT.PAS.BANCARI" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="BANCA     " id_pdctippa="205" pasegno="A" cpdes="INT.PASS. " id_pdctipcp="210"  />
            <row id="84" codice="18" descriz="AUTOFATTURA" tipo="I" esercizio="0" regivadyn="0" datdoc="1" numdoc="1" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="FORNITORE " id_pdctippa="207" pasegno="A" cpdes="COSTO     " id_pdctipcp="210"  />
            <row id="93" codice="12" descriz="IVA CORR. MENS." tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CORRISP.  " id_pdctippa="209" pasegno="D" cpdes="IVA CORR. " id_pdctipcp="211"  />
            <row id="94" codice="55" descriz="CAUS. GENERICA" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="PARTITA   " pasegno="D" cpdes="CONTROPAR."  />
            <row id="95" codice="56" descriz="BUON.CONS.CIPR." tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="CLIENTE   " id_pdctippa="206" pasegno="D" cpdes="CASSA     " id_pdctipcp="208"  />
            <row id="97" codice="57" descriz="BUON.CONS.VALL." tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="1" pcf="1" pcfscon="0" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="CLIENTE   " id_pdctippa="206" pasegno="D" cpdes="CASSA     " id_pdctipcp="208" pralcf="0"  />
            <row id="99" codice="13" descriz="ANTIC. IVA" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="FORNITORE " id_pdctippa="207" pasegno="A" cpdes="IVA       " id_pdctipcp="211"  />
            <row id="100" codice="GB" descriz="GIR.APER.FOR./A" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="CONTO     " id_pdctippa="217" pasegno="D" cpdes="CONTROP.  " id_pdctipcp="207"  />
            <row id="102" codice="58" descriz="BUON.CONS.LATTE" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="CLIENTE   " id_pdctippa="206" pasegno="D" cpdes="CASSA     " id_pdctipcp="208"  />
            <row id="103" codice="49" descriz="COMM.PARITETICA" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="COMM.PARIT" id_pdctippa="214" pasegno="A" cpdes="COMM.PARIT" id_pdctipcp="210"  />
            <row id="141" codice="14" descriz="FATT.ACQ.   CEE" tipo="I" esercizio="0" id_regiva="85" regivadyn="0" datdoc="0" numdoc="0" numiva="1" modpag="1" pcf="1" pcfscon="" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="" pades="FORNITORE " id_pdctippa="207" pasegno="A" cpdes="COSTO     " id_pdctipcp="210"  />
            <row id="142" codice="15" descriz="AUTOFATT. CEE" tipo="E" esercizio="0" id_regiva="86" regivadyn="0" datdoc="0" numdoc="0" numiva="1" modpag="1" pcf="0" pcfscon="0" pcfimp="1" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="Fornitore" id_pdctippa="207" pasegno="D" cpdes="Fornitore" id_pdctipcp="207" pralcf="0" camsegr1="0" quaivanob="0" davscorp="0" event_msg=""  />
            <row id="197" codice="59" descriz="INC. BANCOMAT" tipo="S" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" modpag="" pcf="" pcfscon="" pcfimp="" pcfsgn="" pcfabb="" pcfspe="" pades="          " id_pdctippa="208" pasegno="D" cpdes="          " id_pdctipcp="209"  />
            <row id="198" codice="2E" descriz="VERSAMENTO ASS.ESTERO" tipo="C" esercizio="0" regivadyn="0" datdoc="" numdoc="" numiva="" pcf="0" pcfscon="0" pcfimp="" pcfsgn="+" pcfabb="" pcfspe="0" pcfins="0" pades="Cassa" id_pdctippa="208" pasegno="A" cpdes="Banca" id_pdctipcp="205" pralcf="0" camsegr1="0" quaivanob="0" davscorp="0" event_msg=""  />
        </content>
    </table>
    <table name="catcli">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="4">
            <row id="1" codice="PA" descriz="PATRIZIO"  />
            <row id="2" codice="PL" descriz="PLEBEO"  />
            <row id="3" codice="LE" descriz="LEGIONARIO"  />
            <row id="4" codice="AL" descriz="RESTO"  />
        </content>
    </table>
    <table name="catfor">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="1">
            <row id="1" codice="X" descriz="XXXXX"  />
        </content>
    </table>
    <table name="statcli">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="hidesearch" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_ordcli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_vencli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noeffetti" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_rescli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="2">
            <row id="1" codice="NU" descriz="NON UTILIZZARE" hidesearch="1" nomov_ordcli="0" nomov_vencli="0"  />
            <row id="2" codice="SO" descriz="SOSPESO" hidesearch="0" nomov_ordcli="0" nomov_vencli="1"  />
        </content>
    </table>
    <table name="statfor">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="hidesearch" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_carfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_ordfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_resfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="1">
            <row id="1" codice="NU" descriz="NON UTILIZZARE" hidesearch="1" nomov_carfor="0" nomov_ordfor="0"  />
        </content>
    </table>
    <table name="pdc">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tipo" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_bilmas" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="id_bilcon" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="id_brimas" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bricon" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bilcee" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_statpdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="KEY" type="BTREE" fields="id_tipo,descriz" />
        </structure>
        <content rows="141">
            <row id="1" codice="10001" descriz="CASSA SESTERTIUM" id_tipo="208" id_bilmas="218" id_bilcon="232" id_brimas="1" id_bricon="1" id_bilcee="361"  />
            <row id="2" codice="10012" descriz="NOVELLUM BANQUUS AMBROSIANOX" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="3" codice="10013" descriz="BANQUUS COMMERCIUM PENINSULA" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="4" codice="10101" descriz="CREDITI DIVERSI" id_tipo="213" id_bilmas="219" id_bilcon="236" id_bilcee="350"  />
            <row id="5" codice="10102" descriz="DEPOSITI CAUZIONALI A TERZI" id_tipo="213" id_bilmas="219" id_bilcon="236" id_bilcee="0"  />
            <row id="6" codice="10142" descriz="EFFETTI SU CASSA RISPARMIUM LIGURIAE" id_tipo="284" id_bilmas="219" id_bilcon="235" id_bilcee="346"  />
            <row id="7" codice="10143" descriz="EFFETTI SU BANQUUS COMMERCIUM PENINSULA" id_tipo="284" id_bilmas="219" id_bilcon="235"  />
            <row id="8" codice="10144" descriz="EFFETTI ALLO SCONTO" id_tipo="284" id_bilmas="219" id_bilcon="235" id_bilcee="0"  />
            <row id="9" codice="10145" descriz="EFFETTI INSOLUTI E PROTESTATI" id_tipo="284" id_bilmas="219" id_bilcon="235"  />
            <row id="10" codice="10161" descriz="RATEI ATTIVI" id_tipo="288" id_bilmas="221" id_bilcon="238" id_bilcee="364"  />
            <row id="11" codice="10162" descriz="RISCONTI ATTIVI" id_tipo="288" id_bilmas="221" id_bilcon="238" id_bilcee="364"  />
            <row id="12" codice="10181" descriz="RIMANENZE FINALI" id_tipo="212" id_bilmas="222" id_bilcon="243" id_bilcee="405"  />
            <row id="13" codice="10201" descriz="TERRENI" id_tipo="283" id_bilmas="223" id_bilcon="239" id_bilcee="0"  />
            <row id="14" codice="10202" descriz="FORUM ROMANUM ALBINTIMILIUM" id_tipo="283" id_bilmas="223" id_bilcon="239"  />
            <row id="15" codice="10211" descriz="MACCHINARI IMPIANTI ATTREZZAT." id_tipo="283" id_bilmas="223" id_bilcon="240" id_bilcee="0"  />
            <row id="16" codice="10212" descriz="IMPIANTI DI SOLLEVAMENTO" id_tipo="283" id_bilmas="223" id_bilcon="240" id_bilcee="313"  />
            <row id="17" codice="10213" descriz="MOBILI E MACCHINE ORD.UFFICIO" id_tipo="283" id_bilmas="223" id_bilcon="240" id_bilcee="0"  />
            <row id="18" codice="10215" descriz="MACCHINE UFFICIO ELETTRONICHE" id_tipo="283" id_bilmas="223" id_bilcon="240" id_bilcee="0"  />
            <row id="19" codice="10216" descriz="AUTOMEZZI" id_tipo="283" id_bilmas="223" id_bilcon="240" id_bilcee="0"  />
            <row id="20" codice="10231" descriz="SPESE PLURIENN. COSTITUZ. IMP." id_tipo="283" id_bilmas="223" id_bilcon="241" id_bilcee="0"  />
            <row id="22" codice="10233" descriz="MANUT. E RIPAR. DA AMMORTIZZ." id_tipo="283" id_bilmas="223" id_bilcon="241" id_bilcee="0"  />
            <row id="23" codice="10234" descriz="ALTRI COSTI PLURIENNALI" id_tipo="283" id_bilmas="223" id_bilcon="241" id_bilcee="0"  />
            <row id="24" codice="10242" descriz="TITOLI" id_tipo="213" id_bilmas="223" id_bilcon="242" id_bilcee="0"  />
            <row id="25" codice="10311" descriz="DEBITI DIVERSI" id_tipo="214" id_bilmas="220" id_bilcon="245" id_bilcee="0"  />
            <row id="26" codice="10313" descriz="RITENUTE INPS DIPENDENTI" id_tipo="214" id_bilmas="220" id_bilcon="245" id_bilcee="0"  />
            <row id="27" codice="10331" descriz="ERARIO C/ RIT. FISCALI DIPEND." id_tipo="285" id_bilmas="220" id_bilcon="246" id_bilcee="394"  />
            <row id="28" codice="10332" descriz="ERARIO C/ RITENUTE ACCONTO" id_tipo="285" id_bilmas="220" id_bilcon="246" id_bilcee="394"  />
            <row id="29" codice="10334" descriz="ERARIO C/ IRPEF" id_tipo="285" id_bilmas="220" id_bilcon="246" id_bilcee="394"  />
            <row id="30" codice="10335" descriz="ERARIO C/ IVA" id_tipo="211" id_bilmas="220" id_bilcon="246" id_bilcee="394"  />
            <row id="31" codice="10336" descriz="IVA SU VENDITE" id_tipo="211" id_bilmas="220" id_bilcon="246" id_bilcee="394"  />
            <row id="32" codice="10337" descriz="IVA TRANSITORIO CEE" id_tipo="211" id_bilmas="220" id_bilcon="246" id_bilcee="394"  />
            <row id="33" codice="10338" descriz="IVA SU ACQUISTI" id_tipo="211" id_bilmas="220" id_bilcon="246" id_bilcee="350"  />
            <row id="34" codice="10341" descriz="RATEI PASSIVI" id_tipo="288" id_bilmas="221" id_bilcon="252" id_bilcee="399"  />
            <row id="35" codice="10342" descriz="RISCONTI PASSIVI" id_tipo="288" id_bilmas="221" id_bilcon="252" id_bilcee="399"  />
            <row id="36" codice="10351" descriz="TITOLARE C/ FINANZIAMENTI" id_tipo="214" id_bilmas="220" id_bilcon="247" id_bilcee="0"  />
            <row id="37" codice="10530" descriz="FONDO AMM. CAPANNA MAXIMA" id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="422"  />
            <row id="38" codice="10531" descriz="FONDO AMM. MAC.IMP.ATTREZZ." id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="422"  />
            <row id="39" codice="10532" descriz="FONDO AMM. IMPIANTI DI SOLLEV." id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="0"  />
            <row id="40" codice="10533" descriz="FONDO AMM. MOB.MACCH. UFFICIO" id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="0"  />
            <row id="41" codice="10534" descriz="FONDO AMM. REGISTRATORI CASSA" id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="0"  />
            <row id="42" codice="10535" descriz="FONDO AMM.MACC.UFF.ELETTRONIC." id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="422"  />
            <row id="43" codice="10536" descriz="FONDO AMM. AUTOMEZZI" id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="422"  />
            <row id="44" codice="10552" descriz="FONDO SVALUTAZIONE CREDITI" id_tipo="287" id_bilmas="224" id_bilcon="251" id_bilcee="0"  />
            <row id="45" codice="10553" descriz="TRATTAMENTO DI FINE RAPPORTO" id_tipo="212" id_bilmas="224" id_bilcon="251" id_bilcee="0"  />
            <row id="46" codice="10571" descriz="CAPITALE NETTO" id_tipo="212" id_bilmas="225" id_bilcon="253" id_bilcee="0"  />
            <row id="47" codice="10572" descriz="RISERVE E FONDI DIVERSI" id_tipo="212" id_bilmas="225" id_bilcon="253" id_bilcee="0"  />
            <row id="48" codice="10575" descriz="UTILE/PERDITA DI ESERCIZIO" id_tipo="212" id_bilmas="225" id_bilcon="253" id_bilcee="367"  />
            <row id="49" codice="10591" descriz="GIACENZE INIZIALI" id_tipo="212" id_bilmas="227" id_bilcon="263" id_bilcee="405"  />
            <row id="50" codice="10601" descriz="ACQUISTO MERCI" id_tipo="210" id_bilmas="226" id_bilcon="254" id_bilcee="411"  />
            <row id="51" codice="10612" descriz="SPESE X ACQUA E RISCALDAMENTO" id_tipo="210" id_bilmas="226" id_bilcon="255" id_bilcee="428"  />
            <row id="52" codice="10613" descriz="SPESE PER TRASPORTO" id_tipo="210" id_bilmas="226" id_bilcon="255" id_bilcee="412"  />
            <row id="53" codice="10621" descriz="SPESE ILLUMINAZ. ED ENERGIA" id_tipo="210" id_bilmas="226" id_bilcon="255" id_bilcee="412"  />
            <row id="54" codice="10624" descriz="SPESE TELEFONICHE" id_tipo="210" id_bilmas="226" id_bilcon="255" id_bilcee="412"  />
            <row id="55" codice="10641" descriz="SPESE PER PUBBLICITA'" id_tipo="210" id_bilmas="226" id_bilcon="259" id_bilcee="412"  />
            <row id="56" codice="10642" descriz="OMAGGI" id_tipo="210" id_bilmas="226" id_bilcon="259" id_bilcee="0"  />
            <row id="57" codice="10643" descriz="PROVVIGIONI PASSIVE" id_tipo="210" id_bilmas="226" id_bilcon="259" id_bilcee="0"  />
            <row id="58" codice="10645" descriz="ABBUONI PASSIVI" id_tipo="210" id_bilmas="226" id_bilcon="259" id_bilcee="428"  />
            <row id="59" codice="10661" descriz="RETRIBUZIONI LORDE" id_tipo="210" id_bilmas="226" id_bilcon="256" id_bilcee="0"  />
            <row id="60" codice="10662" descriz="CONTRIBUTI PREVIDENZIALI" id_tipo="210" id_bilmas="226" id_bilcon="256" id_bilcee="411"  />
            <row id="61" codice="10663" descriz="ASSICURAZIONI INAIL" id_tipo="210" id_bilmas="226" id_bilcon="256" id_bilcee="0"  />
            <row id="62" codice="10681" descriz="COMPENSI A CONSULENTI" id_tipo="210" id_bilmas="226" id_bilcon="257" id_bilcee="412"  />
            <row id="63" codice="10701" descriz="SPESE PER ATTREZZATURA MINUTA" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="64" codice="10702" descriz="CANONI DI LOCAZIONE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="65" codice="10703" descriz="CANONI DI LEASING" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="66" codice="10704" descriz="MANUTENZIONE IMPIANTI E AUTOM." id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="67" codice="10705" descriz="ASSICURAZIONI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="68" codice="10706" descriz="VIGILANZA" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="69" codice="10707" descriz="PULIZIA" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="70" codice="10708" descriz="TASSE COMUNALI RINNOVO LICENZE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="71" codice="10709" descriz="VALORI BOLLATI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="72" codice="10712" descriz="LIBRI ABBONAMENTI E RIVISTE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="73" codice="10713" descriz="SPESE POSTALI E TELEGRAFICHE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="74" codice="10714" descriz="IMPOSTE E TASSE DEDUCIBILI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="75" codice="10715" descriz="IMPOSTE E TASSE INDEDUCIBILI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="412"  />
            <row id="76" codice="10716" descriz="VIDIMAZIONI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="77" codice="10717" descriz="BOLLI E SPESE INCASSO DOVUTE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="412"  />
            <row id="78" codice="10719" descriz="CARBURANTI E LUBRIFICANTI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="79" codice="10710" descriz="CANCELLERIA E STAMPATI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="412"  />
            <row id="80" codice="10720" descriz="AUTOMEZZI C/ESERCIZIO" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="81" codice="10721" descriz="SPESE VARIE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="82" codice="10725" descriz="SPESE INDEDUCIBILI" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="83" codice="10741" descriz="INT. X DILAZIONI DI PAGAMENTO" id_tipo="210" id_bilmas="226" id_bilcon="260" id_bilcee="0"  />
            <row id="84" codice="10742" descriz="ONERI BANCARI E COMMISSIONI" id_tipo="210" id_bilmas="226" id_bilcon="260" id_bilcee="412"  />
            <row id="85" codice="10743" descriz="INTERESSI PASSIVI BANCARI" id_tipo="210" id_bilmas="226" id_bilcon="260" id_bilcee="412"  />
            <row id="86" codice="10744" descriz="PERDITE SU CAMBI" id_tipo="210" id_bilmas="226" id_bilcon="260" id_bilcee="0"  />
            <row id="87" codice="10745" descriz="INTERESSI PASS. DA FINANZIAM." id_tipo="210" id_bilmas="226" id_bilcon="260" id_bilcee="411"  />
            <row id="88" codice="10782" descriz="SVALUTAZIONE CREDITI" id_tipo="212" id_bilmas="228" id_bilcon="262" id_bilcee="0"  />
            <row id="89" codice="10791" descriz="SOPRAVVENIENZE PASSIVE" id_tipo="212" id_bilmas="228" id_bilcon="264" id_bilcee="0"  />
            <row id="90" codice="10792" descriz="MINUSVALENZE" id_tipo="212" id_bilmas="228" id_bilcon="264" id_bilcee="0"  />
            <row id="91" codice="10801" descriz="RIMANENZE FINALI MERCE X VEND." id_tipo="212" id_bilmas="227" id_bilcon="269" id_bilcee="0"  />
            <row id="92" codice="10811" descriz="MERCI C/ VENDITE" id_tipo="209" id_bilmas="229" id_bilcon="265" id_bilcee="405"  />
            <row id="93" codice="10813" descriz="PRESTAZIONE DI SERVIZI" id_tipo="209" id_bilmas="229" id_bilcon="265" id_bilcee="0"  />
            <row id="94" codice="10832" descriz="BOLLI SU RICEVUTE BANCARIE" id_tipo="209" id_bilmas="229" id_bilcon="266" id_bilcee="0"  />
            <row id="95" codice="10834" descriz="ABBUONI ATTIVI" id_tipo="209" id_bilmas="229" id_bilcon="266" id_bilcee="405"  />
            <row id="96" codice="10851" descriz="INTERESSI ATTIVI BANCARI" id_tipo="209" id_bilmas="229" id_bilcon="267" id_bilcee="405"  />
            <row id="97" codice="10852" descriz="ALTRI INTERESSI ATTIVI" id_tipo="209" id_bilmas="229" id_bilcon="267" id_bilcee="0"  />
            <row id="98" codice="10853" descriz="UTILI SU CAMBI" id_tipo="209" id_bilmas="229" id_bilcon="267" id_bilcee="0"  />
            <row id="99" codice="10861" descriz="PLUSVALENZE" id_tipo="212" id_bilmas="230" id_bilcon="268" id_bilcee="0"  />
            <row id="100" codice="10862" descriz="SOPRAVVENIENZE ATTIVE" id_tipo="212" id_bilmas="230" id_bilcon="268" id_bilcee="0"  />
            <row id="101" codice="10871" descriz="BILANCIO DI APERTURA" id_tipo="217" id_bilmas="231" id_bilcon="270" id_bilcee="0"  />
            <row id="102" codice="10872" descriz="BILANCIO DI CHIUSURA" id_tipo="217" id_bilmas="231" id_bilcon="270" id_bilcee="0"  />
            <row id="103" codice="10873" descriz="PROFITTI E PERDITE" id_tipo="217" id_bilmas="231" id_bilcon="270" id_bilcee="0"  />
            <row id="104" codice="10875" descriz="CASSA RISPARMIUM LIGURIAE" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="105" codice="10878" descriz="FATTURE DA EMETTERE" id_tipo="213" id_bilmas="219" id_bilcon="234" id_bilcee="0"  />
            <row id="106" codice="10879" descriz="FATTURE DA RICEVERE" id_tipo="214" id_bilmas="220" id_bilcon="245" id_bilcee="0"  />
            <row id="107" codice="10880" descriz="NOTE DI CREDITO DA EMETTERE" id_tipo="213" id_bilmas="219" id_bilcon="234" id_bilcee="0"  />
            <row id="108" codice="10881" descriz="NOTE DI CREDITO DA RICEVERE" id_tipo="214" id_bilmas="220" id_bilcon="245" id_bilcee="0"  />
            <row id="109" codice="10882" descriz="ERARIO C/CR. IMP.REG. DI CASSA" id_tipo="285" id_bilmas="219" id_bilcon="237" id_bilcee="0"  />
            <row id="110" codice="10884" descriz="MAN E RIP MOB MACC.UFFICIO" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="411"  />
            <row id="111" codice="10885" descriz="SPESE DI RAPPRESENTANZA" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="112" codice="10886" descriz="COMMISSIONI BANCARIE" id_tipo="210" id_bilmas="226" id_bilcon="260" id_bilcee="412"  />
            <row id="113" codice="10887" descriz="PERDITE DIVERSE" id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="114" codice="10888" descriz="PERDITE NON DEDUCIBILI FISCAL." id_tipo="210" id_bilmas="226" id_bilcon="258" id_bilcee="0"  />
            <row id="115" codice="10889" descriz="FORUM ROMANUM CAMPI FLEGREI" id_tipo="283" id_bilmas="223" id_bilcon="239"  />
            <row id="116" codice="10890" descriz="REGISTRATORI DI CASSA" id_tipo="283" id_bilmas="223" id_bilcon="240" id_bilcee="0"  />
            <row id="117" codice="10891" descriz="TITOLARE C/ PRELEVAMENTO UTILI" id_tipo="214" id_bilmas="220" id_bilcon="247" id_bilcee="0"  />
            <row id="118" codice="10892" descriz="FONDO AMM. CAPAN. VALLEBONA" id_tipo="287" id_bilmas="224" id_bilcon="250" id_bilcee="0"  />
            <row id="120" codice="10894" descriz="CORRISPETTIVI ALBINTIMILIUM" id_tipo="209" id_bilmas="229" id_bilcon="265" id_bilcee="405"  />
            <row id="121" codice="10895" descriz="CORRISPETTIVI ALBINTIMILIUM" id_tipo="209" id_bilmas="229" id_bilcon="265"  />
            <row id="122" codice="10897" descriz="INAIL" id_tipo="285" id_bilmas="220" id_bilcon="245" id_bilcee="0"  />
            <row id="125" codice="10904" descriz="CORRISPETTIVI CAMPI FLEGREI" id_tipo="209" id_bilmas="229" id_bilcon="265"  />
            <row id="128" codice="10907" descriz="COMMISSIONE PARITETICA" id_tipo="214" id_bilmas="220" id_bilcon="245" id_bilcee="0"  />
            <row id="130" codice="10909" descriz="AMMORTAMENTO ORDINARIO" id_tipo="212" id_bilmas="228" id_bilcon="261" id_bilcee="422"  />
            <row id="131" codice="10910" descriz="AMMORTAMENTO ANTICIPATO" id_tipo="212" id_bilmas="228" id_bilcon="261" id_bilcee="0"  />
            <row id="132" codice="10911" descriz="INDENNITA' MALATTIA" id_tipo="287" id_bilmas="220" id_bilcon="245"  />
            <row id="133" codice="10912" descriz="INDENNITA MALATTIA" id_tipo="287" id_bilmas="220" id_bilcon="245"  />
            <row id="134" codice="10913" descriz="RIMANENZE INIZIALI" id_tipo="212" id_bilmas="222" id_bilcon="243" id_bilcee="0"  />
            <row id="135" codice="10914" descriz="BILANCIO D'APERTURA SECONDARIUM" id_tipo="217" id_bilmas="231" id_bilcon="270"  />
            <row id="136" codice="10915" descriz="GIACENZE FINALI" id_tipo="212" id_bilmas="227" id_bilcon="269" id_bilcee="425"  />
            <row id="138" codice="10920" descriz="BANQUUS COMMERCIUM ALBINTIMILIUM" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="139" codice="10921" descriz="BANQUS COMMERCIUS GALLIAE" id_tipo="210" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="140" codice="10922" descriz="SOCI C/UTILI" id_tipo="214" id_bilmas="220" id_bilcon="247" id_bilcee="396"  />
            <row id="141" codice="10923" descriz="CAPITALE SOCIALE" id_tipo="212" id_bilmas="225" id_bilcon="253" id_bilcee="323"  />
            <row id="144" codice="10933" descriz="BANQUUS FINANZIARIUM CATILINO" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="145" codice="10934" descriz="BANCO MUTUANTI" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="146" codice="11111" descriz="IVA C/IMPORTAZIONI CEE" id_tipo="211" id_bilmas="220" id_bilcon="246" id_bilcee="350"  />
             <row id="3996" codice="12001" descriz="CASSA NO SESTERTIUM" id_tipo="208" id_bilmas="218" id_bilcon="232" id_bilcee="361"  />
            <row id="4463" codice="10833" descriz="RIMBORSO SPESE FATTURAZ/SPEDIZ" id_tipo="209" id_bilmas="229" id_bilcon="265" id_bilcee="405"  />
            <row id="4509" codice="12003" descriz="BANQUUS AGRO PONTINUM" id_tipo="205" id_bilmas="218" id_bilcon="233" id_bilcee="359"  />
            <row id="4510" codice="10898" descriz="FATTURE DA RICEVERE" id_tipo="288" id_bilmas="221" id_bilcon="252" id_bilcee="412"  />
            <row id="4511" codice="10902" descriz="MERCI C/RIMANENZE FINALI" id_tipo="209" id_bilmas="229" id_bilcon="266"  />
        </content>
    </table>
    <table name="clienti">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="0" extra="" />
            <column name="indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cap" type="char(8)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="codfisc" type="char(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nazione" type="char(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="piva" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="email" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt1nome" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt1email" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt1numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt2nome" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt2email" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt2numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt3nome" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt3email" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt3numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spddes" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdind" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdcap" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdcit" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdpro" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="chiusura" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notedoc" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fdr0doc" type="tinyint(3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fdr0imp" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fdr1doc" type="tinyint(3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fdr1imp" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_zona" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_agente" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_valuta" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_modpag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_speinc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tiplist" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_travet" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_categ" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_status" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_clifat" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_scadgrp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bancapag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="allegcf" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fido_maxpcf" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fido_maxggs" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fido_maximp" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="fido_maxesp" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sogritacc" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="siteurl" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docsemail" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noexemail" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="perpro" type="decimal(7,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ddtfixpre" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ddtstapre" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="grpstop" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcgrp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_stato" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="is_blacklisted" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="destin">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cap" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numcel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="email" type="varchar(80)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="contatto" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pref" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_pdc,codice" />
            <index name="index2" family="KEY" type="BTREE" fields="id_pdc,descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="bancf">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="abi" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cab" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numcc" type="varchar(19)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="iban" type="varchar(34)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="bic" type="varchar(11)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pref" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="bban" type="varchar(23)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cinbban" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ciniban" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="paese" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_pdc,descriz" />
        </structure>
        <content rows="20">
            <row id="358" codice="20247" descriz="NBA VALKLECROSIA" abi="" cab="" numcc="" iban="" bic="" id_pdc="358"  />
            <row id="2379" codice="22395" descriz="AMBRO VENETO" abi="" cab="" numcc="" iban="" bic="" id_pdc="2379"  />
            <row id="2769" codice="23048" descriz="CARIGE ARMA TAGGIA" abi="" cab="" numcc="" iban="" bic="" id_pdc="2769"  />
            <row id="3010" codice="23296" descriz="CARIPLO AG GE SE PO" abi="" cab="" numcc="" iban="" bic="" id_pdc="3010"  />
            <row id="3304" codice="23599" descriz="CARIGE AG 45" abi="" cab="" numcc="" iban="" bic="" id_pdc="3304"  />
            <row id="3308" codice="23603" descriz="CA.RI.SA SV AG PORTO" abi="06310" cab="" numcc="" iban="" bic="" id_pdc="3308"  />
            <row id="3325" codice="23620" descriz="CARIGE AG225 ALBENGA" abi="6175" cab="" numcc="120/30" iban="" bic="" id_pdc="3325"  />
            <row id="3530" codice="30077" descriz="AMBRO VENETO" abi="" cab="" numcc="" iban="" bic="" id_pdc="3530"  />
            <row id="3641" codice="30189" descriz="ANBRO VENETO" abi="" cab="" numcc="" iban="" bic="" id_pdc="3641"  />
            <row id="3737" codice="30285" descriz="B.N.L." abi="01005" cab="01612" numcc="000000000081" iban="IT97X01005016120000000000081" bic="X" id_pdc="3737"  />
            <row id="3781" codice="30340" descriz="AMBRO VENETO" abi="" cab="" numcc="" iban="" bic="" id_pdc="3781"  />
            <row id="3809" codice="30408" descriz="AMBRO VENETO" abi="" cab="" numcc="" iban="" bic="" id_pdc="3809"  />
            <row id="3810" codice="30410" descriz="AMBRO VENETO" abi="" cab="" numcc="" iban="" bic="" id_pdc="3810"  />
            <row id="4303" codice="25311" descriz="" abi="05418" cab="49100" numcc="174570016808" iban="IT52" bic="AMBPIT2M" id_pdc="4303"  />
            <row id="4398" codice="25380" descriz="CASSA RISPARMIO FIR." abi="06160" cab="71870" numcc="" iban="" bic="" id_pdc="4398"  />
            <row id="4402" codice="25384" descriz="SELLA" abi="03268" cab="14700" numcc="52902677980" iban="" bic="M" id_pdc="4402"  />
            <row id="4403" codice="1" descriz="CASSA RISPARMIUM LIGURIAE - AG.27" abi="03105" cab="22700" numcc="000000146820" iban="IT27K0310522700000000146820" bic="BC4235A756" pref="1" id_pdc="4027" bban="K0310522700000000146820" cinbban="K" ciniban="27" paese="IT"  />
            <row id="4404" codice="2" descriz="BANQUUS COMMERCIUM PENINSULA" abi="03328" cab="22703" numcc="100000567890" iban="IT33B0332822703100000567890" bic="BCP432Z123" pref="0" id_pdc="4027" bban="B0332822703100000567890" cinbban="B" ciniban="33" paese="IT"  />
            <row id="4405" codice="1" descriz="CARIGE - SANREMO AG.22" abi="06175" cab="22700" numcc="146820" iban="IT10D0617522700000000146820" pref="1" id_pdc="1149" bban="D0617522700000000146820" cinbban="D" ciniban="10" paese="IT"  />
            <row id="4406" codice="1" descriz="BANQUUS SAN GEORGEUS" abi="03328" cab="22455" numcc="147345" iban="IT43X0332822455000000147345" pref="1" id_pdc="2579" bban="X0332822455000000147345" cinbban="X" ciniban="43" paese="IT"  />
        </content>
    </table>
    <table name="fornit">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="0" extra="" />
            <column name="indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cap" type="char(8)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="codfisc" type="char(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nazione" type="char(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="piva" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numtel2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numfax2" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="email" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt1nome" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt1email" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt1numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt2nome" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt2email" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt2numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt3nome" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt3email" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctt3numtel" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spddes" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdind" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdcap" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdcit" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spdpro" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_valuta" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_modpag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_speinc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_travet" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_categ" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_zona" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_status" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_scadgrp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bancapag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="allegcf" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="siteurl" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="grpstop" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcgrp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_stato" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="is_blacklisted" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="casse">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="0" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
        </structure>
        <content rows="6">
            <row id="1"  />
            <row id="132"  />
            <row id="133"  />
            <row id="144"  />
            <row id="145"  />
            <row id="3996"  />
        </content>
    </table>
    <table name="banche">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="0" extra="" />
            <column name="abi" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cab" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numcc" type="varchar(12)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cin" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="iban" type="varchar(27)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sia" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="setif" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="desriba1" type="varchar(24)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="desriba2" type="varchar(24)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="desriba3" type="varchar(24)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="desriba4" type="varchar(24)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="firmariba" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="provfin" type="varchar(15)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aubanum" type="varchar(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aubadat" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
        </structure>
        <content rows="5">
            <row id="2" abi="" cab="" numcc="" cin="" iban="" sia="" setif="" desriba1="" desriba2="" desriba3="" desriba4="" firmariba="" provfin="" aubanum=""  />
            <row id="3" abi="" cab="" numcc="" iban="" sia="" setif=""  />
            <row id="104" abi="" cab="" numcc="" iban="" sia="" setif=""  />
            <row id="138" abi="" cab="" numcc="" iban="" sia="" setif=""  />
            <row id="4509" abi="03268" cab="48960" numcc="052212993640" cin="S" iban="IT24S0326848960052212993640" sia="" setif="" desriba1="" desriba2="" desriba3="" desriba4="" firmariba="" provfin="" aubanum=""  />
        </content>
    </table>
    <table name="contab_h">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="esercizio" type="int(4) unsigned" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="id_caus" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipreg" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datreg" type="date" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="datdoc" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numdoc" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numiva" type="int(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numreg" type="int(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="st_regiva" type="tinyint(1)" can_null="YES" key_type="" default_value="0" extra="" />
            <column name="st_giobol" type="tinyint(1)" can_null="YES" key_type="" default_value="0" extra="" />
            <column name="id_valuta" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_regiva" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_modpag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocalciva" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index2" family="KEY" type="BTREE" fields="datreg,id_regiva,numiva" />
            <index name="index1" family="KEY" type="BTREE" fields="id_regiva,numiva,numdoc" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="contab_b">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_reg" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="numriga" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipriga" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nrigiobol" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="importo" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="imponib" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="imposta" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="indeduc" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="segno" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcpa" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_pdccp" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_pdciva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcind" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivaman" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="davscorp" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="solocont" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_reg,numriga" />
            <index name="index3" family="KEY" type="BTREE" fields="id_pdccp,id_reg,id" />
            <index name="index2" family="KEY" type="BTREE" fields="id_pdcpa,id_reg" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="pcf">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_pdc" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_caus" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_modpag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="riba" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="contrass" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="insoluto" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datdoc" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numdoc" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datscad" type="date" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="imptot" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="imppar" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="impeff" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="imptot_ve" type="decimal(22,6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="imppar_ve" type="decimal(22,6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_effsele" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_effemes" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_effcont" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_effban" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_effbap" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_effreg" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="effdate" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_effpdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_pdc,datscad" />
            <index name="index2" family="KEY" type="BTREE" fields="datscad" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="contab_s">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_reg" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="datscad" type="date" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="importo" type="decimal(12,2)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="importo_ve" type="decimal(22,6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="abbuono" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="spesa" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_riba" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pcf" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipabb" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_reg,datscad" />
            <index name="index2" family="KEY" type="BTREE" fields="id_pcf,id_reg" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="cfgprogr">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="varchar(20)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="keydiff" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="key_id" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="progrnum" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="progrdate" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="progrimp1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="progrimp2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="progrdesc" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice,keydiff,key_id" />
        </structure>
        <content rows="56">
            <row id="1" codice="ccg_giobol_da" descriz="Progressivi Giornale Bollato" keydiff="2008" progrnum="9995" progrdate="2008-12-31"  />
            <row id="2" codice="ccg_giobol_da" descriz="Progressivi Giornale Bollato" keydiff="2008" progrimp1="6228578.31" progrimp2="6228578.31"  />
            <row id="3" codice="ccg_giobol_da" descriz="Progressivi Giornale Bollato" keydiff="2007" progrimp1="12269217.25" progrimp2="12269217.25"  />
            <row id="4" codice="CCG_MASTRI" descriz="Stampa fiscale mastrini" keydiff="2008" key_id="0" progrdate="2008-03-31"  />
            <row id="5" codice="ccg_aggcon" descriz="Aggiornamento contabile" keydiff="0" progrdate="2008-12-31"  />
            <row id="6" codice="ccg_accsal" descriz="Accantonamento saldi" keydiff="0" progrdate="2007-12-31"  />
            <row id="7" codice="ccg_accsal_flag" descriz="Accantonamento saldi" keydiff="0" progrnum="1"  />
            <row id="8" codice="ccg_apechi_flag" descriz="Movimenti apertura/chiusura" keydiff="0" progrnum="1"  />
            <row id="9" codice="ccg_chiusura" descriz="Movimenti chiusura esercizio" keydiff="0" progrdate="2008-03-31"  />
            <row id="10" codice="ccg_apertura" descriz="Movimenti apertura esercizio" keydiff="0" progrdate="2008-04-01"  />
            <row id="11" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="22"  />
            <row id="12" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="2009" key_id="23" progrnum="544" progrdate="2009-02-28"  />
            <row id="13" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="24"  />
            <row id="14" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="25"  />
            <row id="15" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="75"  />
            <row id="16" codice="IVA_STAREG" descriz="Ultima stampa definitiva" keydiff="2008" key_id="85" progrdate="2008-12-31"  />
            <row id="17" codice="IVA_ULTINS" descriz="Ultima registrazione immessa" keydiff="2008" key_id="85" progrnum="276" progrdate="2008-12-31"  />
            <row id="18" codice="IVA_ULTINS" descriz="Ultima registrazione immessa" keydiff="2007" key_id="85" progrnum="316"  />
            <row id="19" codice="IVA_STAREG" descriz="Ultima stampa definitiva" keydiff="2008" key_id="86" progrdate="2008-12-31"  />
            <row id="20" codice="IVA_ULTINS" descriz="Ultima registrazione immessa" keydiff="2009" key_id="86" progrnum="786" progrdate="2009-01-02"  />
            <row id="21" codice="IVA_ULTINS" descriz="Ultima registrazione immessa" keydiff="2008" key_id="86" progrnum="956"  />
            <row id="22" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="90"  />
            <row id="23" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="96"  />
            <row id="24" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="112"  />
            <row id="25" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="113"  />
            <row id="26" codice="IVA_STAREG" descriz="Ultima stampa definitiva" keydiff="2008" key_id="140" progrdate="2008-12-31"  />
            <row id="27" codice="IVA_ULTINS" descriz="Ultima registrazione immessa" keydiff="2008" key_id="140" progrnum="2" progrdate="2008-03-31"  />
            <row id="28" codice="IVA_ULTINS" descriz="Ultima registrazione immessa" keydiff="2007" key_id="140" progrnum="0"  />
            <row id="29" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="143"  />
            <row id="30" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="145"  />
            <row id="31" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="148"  />
            <row id="32" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="None" key_id="150"  />
            <row id="33" codice="MAG_LASTDOC" descriz="Ultimo documento magazzino" keydiff="2009" key_id="171" progrnum="665" progrdate="2009-02-09"  />
            <row id="34" codice="ccg_esercizio" keydiff="0" progrnum="2009" progrimp1="1.0" progrimp2="0.0"  />
            <row id="35" codice="ccg_giobol" keydiff="0" progrnum="1590" progrdate="2009-03-31" progrimp1="2009.0" progrimp2="25.0" progrdesc=""  />
            <row id="36" codice="ccg_giobol_ec" keydiff="0" progrimp1="710323.99" progrimp2="710323.99"  />
            <row id="37" codice="ccg_giobol_ep" keydiff="0" progrimp1="13321287.03" progrimp2="13321287.03"  />
            <row id="38" codice="ccg_giobol_stm" descriz="Data stampa mastri per l'esercizio 2009" keydiff="2009"  />
            <row id="39" codice="ccg_giobol_stm" descriz="Data stampa mastri per l'esercizio 2008" keydiff="2008"  />
            <row id="40" codice="ccg_giobol_stm" descriz="Data stampa mastri per l'esercizio 2007" keydiff="2007"  />
            <row id="41" codice="mag_lastdoc" keydiff="909" key_id="171" progrnum="215"  />
            <row id="42" codice="mag_lastdoc" keydiff="2008" key_id="23" progrnum="786"  />
            <row id="43" codice="mag_lastdoc" keydiff="2008" key_id="171" progrnum="956"  />
            <row id="44" codice="mag_lastdoc" keydiff="2008" key_id="24" progrnum="774"  />
            <row id="45" codice="iva_stareg" keydiff="2009" key_id="85" progrdate="2009-06-30"  />
            <row id="46" codice="iva_stareg" keydiff="2009" key_id="86" progrdate="2009-06-30"  />
            <row id="47" codice="iva_cricomdisp" keydiff="2009" progrimp1="0.0"  />
            <row id="48" codice="iva_debcred" keydiff="2009" progrnum="6" progrdate="2009-10-26" progrimp1="0.0"  />
            <row id="49" codice="mag_lastdoc" keydiff="2010" key_id="171" progrnum="4"  />
            <row id="50" codice="iva_lastins" keydiff="2010" key_id="86" progrnum="1"  />
            <row id="51" codice="mag_lastdoc" keydiff="2010" key_id="23" progrnum="5"  />
            <row id="52" codice="mag_lastdoc" keydiff="2010" key_id="172" progrnum="1"  />
            <row id="53" codice="mag_lastdoc" keydiff="2010" key_id="174" progrnum="1230"  />
            <row id="54" codice="ccg_giobol_stm" descriz="Data stampa mastri per l'esercizio 2010" keydiff="2010"  />
            <row id="55" codice="mag_lastdoc" keydiff="2011" key_id="23" progrnum="3"  />
            <row id="56" codice="mag_lastdoc" keydiff="2011" key_id="171" progrnum="2"  />
        </content>
    </table>
    <table name="cfgautom">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="varchar(20)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aut_id" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
        </structure>
        <content rows="61">
            <row id="1" codice="ivaacq" descriz="Sottoconto IVA su acquisti" aut_id="33"  />
            <row id="2" codice="ivaven" descriz="Sottoconto IVA su vendite" aut_id="31"  />
            <row id="3" codice="ivacor" descriz="Sottoconto IVA su vendite da corrispettivi" aut_id="32"  />
            <row id="4" codice="ivaind" descriz="Sottoconto IVA indeducibile su acquisti" aut_id="82"  />
            <row id="5" codice="abbatt" descriz="Sottoconto abbuoni attivi" aut_id="95"  />
            <row id="6" codice="abbpas" descriz="Sottoconto abbuoni passivi" aut_id="58"  />
            <row id="7" codice="regchibil" descriz="Sottoconto bilancio chiusura" aut_id="102"  />
            <row id="8" codice="regchiprp" descriz="Sottoconto profitti/poerdite chiusura" aut_id="103"  />
            <row id="9" codice="regchiupe" descriz="Sottoconto utile/perdita esercizio chiusura" aut_id="48"  />
            <row id="10" codice="regapebil" descriz="Sottoconto bilancio apertura" aut_id="101"  />
            <row id="11" codice="regapeupe" descriz="Sottoconto profitti/perdite apertura" aut_id="48"  />
            <row id="12" codice="regchicau" descriz="Causale bilancio chiusura" aut_id="51"  />
            <row id="13" codice="regapecau" descriz="Causale bilancio apertura" aut_id="50"  />
            <row id="14" codice="magivascm" descriz="Aliquota Iva per sconto merce" aut_id="204"  />
            <row id="15" codice="magivaest" descriz="Aliquota Iva per documenti estero"  />
            <row id="16" codice="TIPUTICAM" descriz="Tipo pdc per utile su cambi" aut_id="287"  />
            <row id="17" codice="uticam" descriz="Sottoconto utile su differenza cambio"  />
            <row id="18" codice="TIPPERCAM" descriz="Tipo pdc per perdite su cambi"  />
            <row id="19" codice="percam" descriz="Sottoconto perdita su differenza cambio"  />
            <row id="20" codice="TIPSPECAM" descriz="Tipo pdc per spese su cambi"  />
            <row id="21" codice="SPECAM" descriz="Sottoconto spese su cambi"  />
            <row id="22" codice="ivaacqcee" descriz="Sottoconto IVA su acquisti cee"  />
            <row id="23" codice="ivavensos" descriz="Sottoconto IVA per vendite in sospensione di IVA"  />
            <row id="24" codice="ivaacqsos" descriz="Sottoconto IVA per acquisti in sospensione di IVA"  />
            <row id="25" codice="magomaggi" descriz="Sottoconto Omaggi"  />
            <row id="26" codice="pdctip_BANCHE" descriz="Tipo sottoconto default per tabella banche" aut_id="205"  />
            <row id="27" codice="bilmas_CLIENTI" descriz="Mastro di bilancio default per tabella clienti" aut_id="219"  />
            <row id="28" codice="bilcon_CLIENTI" descriz="Conto di bilancio default per tabella clienti" aut_id="234"  />
            <row id="29" codice="pdctip_CLIENTI" descriz="Tipo sottoconto default per tabella clienti" aut_id="206"  />
            <row id="30" codice="bilmas_FORNIT" descriz="Mastro di bilancio default per tabella fornit" aut_id="220"  />
            <row id="31" codice="bilcon_FORNIT" descriz="Conto di bilancio default per tabella fornit" aut_id="244"  />
            <row id="32" codice="pdctip_FORNIT" descriz="Tipo sottoconto default per tabella fornit" aut_id="207"  />
            <row id="33" codice="pdctip_CASSA" descriz="Tipo P.d.C. standard per la tabella cassa" aut_id="208"  />
            <row id="34" codice="speinc" descriz="Sottoconto spese incasso"  />
            <row id="35" codice="bilcon_effetti" descriz="Conto di bilancio default per tabella effetti" aut_id="235"  />
            <row id="36" codice="bilmas_casse" descriz="Mastro di bilancio default per tabella casse" aut_id="218"  />
            <row id="37" codice="pdctip_ricavi" descriz="Tipo sottoconto default per ricavi" aut_id="209"  />
            <row id="38" codice="bilcon_banche" descriz="Conto di bilancio default per tabella banche" aut_id="233"  />
            <row id="39" codice="bilcon_casse" descriz="Conto di bilancio default per tabella casse" aut_id="232"  />
            <row id="40" codice="pdctip_casse" descriz="Tipo sottoconto default per tabella casse" aut_id="208"  />
            <row id="41" codice="pdctip_effetti" descriz="Tipo sottoconto default per tabella effetti" aut_id="284"  />
            <row id="42" codice="bilmas_banche" descriz="Mastro di bilancio default per tabella banche" aut_id="218"  />
            <row id="43" codice="pdctip_costi" descriz="Tipo sottoconto default per costi" aut_id="210"  />
            <row id="44" codice="bilmas_effetti" descriz="Mastro di bilancio default per tabella effetti" aut_id="219"  />
            <row id="45" codice="maginidoc" descriz="Documento giacenza iniziale" aut_id="172"  />
            <row id="46" codice="magivacee" descriz="Aliquota Iva per documenti CEE"  />
            <row id="47" codice="maginimov" descriz="Movimento giacenza iniziale" aut_id="174"  />
            <row id="48" codice="magfilfor" descriz="Filtro ricerca articoli per fornitore" aut_id="0"  />
            <row id="49" codice="magfilcat" descriz="Filtro ricerca articoli per categoria" aut_id="0"  />
            <row id="50" codice="magomareg" descriz="Omaggi in registrazione" aut_id="0"  />
            <row id="51" codice="magfilmar" descriz="Filtro ricerca articoli per marca" aut_id="0"  />
            <row id="52" codice="magordfta" descriz="Ordinamento in interr.prodotti fatturati" aut_id="0"  />
            <row id="53" codice="magordinv" descriz="Ordine inverso su interrogazioni sottoconto" aut_id="0"  />
            <row id="54" codice="magivadef" descriz="Aliquota Iva di default"  />
            <row id="55" codice="magfiltip" descriz="Filtro ricerca articoli per tipo" aut_id="0"  />
            <row id="56" codice="magintcli" descriz="Visualizzazione di default su scheda cliente" aut_id="0"  />
            <row id="57" codice="bilcee_fornit" descriz="Classificazione CEE default per tabella fornit" aut_id="389"  />
            <row id="58" codice="bilcee_banche" descriz="Classificazione CEE default per tabella banche" aut_id="359"  />
            <row id="59" codice="bilcee_effetti" descriz="Classificazione CEE default per tabella effetti" aut_id="346"  />
            <row id="60" codice="bilcee_clienti" descriz="Classificazione CEE default per tabella clienti" aut_id="346"  />
            <row id="61" codice="bilcee_casse" descriz="Classificazione CEE default per tabella casse" aut_id="361"  />
        </content>
    </table>
    <table name="cfgpdcpref">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="ambito" type="tinyint(1)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="key_id" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pdcord" type="int(3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="segno" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="ambito,key_id" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="tipart">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="catart">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="id_pdcacq" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcven" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="gruart">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_catart" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_catart,codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="id_catart,descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="statart">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="hidesearch" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_carfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_ordcli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_ordfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nomov_vencli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="prod">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(16)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="um" type="char(5)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="costo" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="barcode" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="codfor" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pzconf" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="kgconf" type="decimal(11,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="dimx" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="dimy" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="dimz" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="volume" type="decimal(13,5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="stetic" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descetic" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descextra" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="perpro" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="scomin" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="scomax" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="scaffale" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="id_tipart" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_catart" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_gruart" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_fornit" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_status" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_marart" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_gruprez" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcacq" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdcven" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ricar1" type="decimal(7,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ricar2" type="decimal(7,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ricar3" type="decimal(7,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="KEY" type="BTREE" fields="id_tipart,descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="artfor">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="datins" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="codice" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="barcode" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="predef" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_prod,id_pdc" />
            <index name="index2" family="KEY" type="BTREE" fields="id_pdc,id_prod" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="listini">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_valuta" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="data" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo1" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo2" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo3" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo4" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo5" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo6" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo7" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo8" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo9" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_prod,data" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="griglie">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="data" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prebloc" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pzconf" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ext_codice" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ext_descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_prod,id_pdc,data" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="magazz">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="1">
            <row id="1" codice="1" descriz="SEDE"  />
        </content>
    </table>
    <table name="cfgmagdoc">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="valuta" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdctip" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descanag" type="varchar(30)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datdoc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numdoc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numest" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docfam" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ctrnum" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggnum" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pienum" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_acqdoc1" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_acqdoc2" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_acqdoc3" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_acqdoc4" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipacq1" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipacq2" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipacq3" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipacq4" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="annacq1" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="annacq2" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="annacq3" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="annacq4" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="checkacq1" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="checkacq2" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="checkacq3" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="checkacq4" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askmagazz" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_magazz" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askmodpag" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askmpnoeff" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askdestin" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askrifdesc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askrifdata" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askrifnum" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askagente" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askzona" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asklist" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askbanca" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askdatiacc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktracau" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tracau" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktracur" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tracur" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktravet" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_travet" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktraasp" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_traasp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktrapor" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_trapor" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktracon" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tracon" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="asktrakgc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="colcg" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_caucg" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tdoctra" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askprotiva" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="scorpiva" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totali" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totzero" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totneg" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tiposta" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="staobb" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="stanoc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="provvig" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="toolprint" type="varchar(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="toolbarra" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="staintest" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="stalogo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="viscosto" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="visgiac" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vislistini" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="visultmov" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ultmovbef" type="tinyint(1)" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="printetic" type="tinyint(1)" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="pdcdamag" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="checkfido" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sogritacc" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc_ra" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="autoqtaonbc" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="printer" type="char(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="copies" type="int(3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="custde" type="varchar(44)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docemail" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="txtemail" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="clasdoc" type="char(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vismargine" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askstaint" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askstapre" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="5">
            <row id="23" codice="2" descriz="FATTURA EMESSA" valuta="" id_pdctip="206" descanag="CLIENTE" datdoc="3" numdoc="3" numest="" docfam="" ctrnum="X" aggnum="X" pienum="" id_acqdoc1="171" tipacq1="E" tipacq2="" tipacq3="" tipacq4="" annacq1="1" annacq2="0" annacq3="0" annacq4="0" checkacq1="0" checkacq2="0" checkacq3="0" checkacq4="0" askmagazz="" id_magazz="1" askmodpag="X" askmpnoeff="" askdestin="X" askrifdesc="X" askrifdata="X" askrifnum="X" askagente="" askzona="" asklist="" askbanca="X" askdatiacc="X" asktracau="X" id_tracau="1" asktracur="X" id_tracur="1" asktravet="X" asktraasp="X" asktrapor="" asktracon="" asktrakgc="X" colcg="X" id_caucg="27" askprotiva="" scorpiva="1" totali="X" totzero="" totneg="" tiposta="S2" staobb="" stanoc="" provvig="0" toolprint="Fattura" toolbarra="" staintest="X" stalogo="X" viscosto="0" visgiac="0" vislistini="0" visultmov="0" ultmovbef="0" printetic="0" pdcdamag="0" checkfido="0" sogritacc="0" autoqtaonbc="0" copies="0" custde="" docemail="0" txtemail="" vismargine="0"  />
            <row id="24" codice="6" descriz="NOT_CRED_EMESSA" valuta="" id_pdctip="206" descanag="CLIENTE" datdoc="1" numdoc="3" numest="" docfam="" ctrnum="X" aggnum="" pienum="" tipacq1="" tipacq2="" tipacq3="" tipacq4="" annacq1="0" annacq2="0" annacq3="0" annacq4="0" checkacq1="0" checkacq2="0" checkacq3="0" checkacq4="0" askmagazz="" id_magazz="1" askmodpag="X" askmpnoeff="X" askdestin="X" askrifdesc="X" askrifdata="X" askrifnum="X" askagente="" askzona="" asklist="" askbanca="" askdatiacc="" asktracau="" asktracur="" asktravet="" asktraasp="" asktrapor="" asktracon="" asktrakgc="" colcg="X" id_caucg="29" askprotiva="" scorpiva="1" totali="X" totzero="" totneg="" tiposta="S2" staobb="" stanoc="" provvig="0" toolprint="Fattura" toolbarra="" staintest="X" stalogo="X" viscosto="0" visgiac="0" vislistini="0" visultmov="0" ultmovbef="0" printetic="0" pdcdamag="0" checkfido="0" sogritacc="0" autoqtaonbc="0" copies="0" custde="" docemail="0" txtemail="" vismargine="0"  />
            <row id="172" codice="G" descriz="GIACENZE INIZIALI" valuta="" descanag="" datdoc="3" numdoc="1" numest="" docfam="" ctrnum="X" aggnum="X" pienum="" tipacq1="" tipacq2="" tipacq3="" tipacq4="" annacq1="0" annacq2="0" annacq3="0" annacq4="0" checkacq1="0" checkacq2="0" checkacq3="0" checkacq4="0" askmagazz="" id_magazz="1" askmodpag="" askmpnoeff="" askdestin="" askrifdesc="" askrifdata="" askrifnum="" askagente="" askzona="" asklist="" askbanca="" askdatiacc="" asktracau="" asktracur="" asktravet="" asktraasp="" asktrapor="" asktracon="" asktrakgc="" colcg="" askprotiva="" scorpiva="" totali="" totzero="" totneg="" staobb="" stanoc="" provvig="0" toolprint="" toolbarra="" staintest="" stalogo="" viscosto="0" visgiac="0" vislistini="0" visultmov="0" ultmovbef="0" printetic="0" pdcdamag="0" checkfido="0" sogritacc="0" autoqtaonbc="0" copies="0" custde="" docemail="0" txtemail="" vismargine="0"  />
            <row id="171" codice="5" descriz="DOCUM.TRASPORTO" valuta="" id_pdctip="206" descanag="CLIENTE" datdoc="3" numdoc="1" numest="" docfam="" ctrnum="X" aggnum="X" pienum="" tipacq1="" tipacq2="" tipacq3="" tipacq4="" annacq1="0" annacq2="0" annacq3="0" annacq4="0" checkacq1="0" checkacq2="0" checkacq3="0" checkacq4="0" askmagazz="" id_magazz="1" askmodpag="X" askmpnoeff="" askdestin="X" askrifdesc="X" askrifdata="X" askrifnum="X" askagente="" askzona="" asklist="" askbanca="X" askdatiacc="X" asktracau="X" asktracur="X" asktravet="X" asktraasp="X" asktrapor="X" asktracon="X" asktrakgc="X" colcg="" askprotiva="" scorpiva="1" totali="X" totzero="" totneg="" tiposta="" staobb="" stanoc="" provvig="0" toolprint="ddt" toolbarra="" staintest="" stalogo="" viscosto="0" visgiac="0" vislistini="0" visultmov="1" ultmovbef="1" printetic="0" pdcdamag="0" checkfido="0" sogritacc="0" autoqtaonbc="0" copies="0" custde="" docemail="0" txtemail="" vismargine="0" askstaint="" askstapre=""  />
            <row id="174" codice="2X" descriz="FATTURA RICEVUTA" valuta="" id_pdctip="207" descanag="FORNITORE" datdoc="0" numdoc="0" numest="" docfam="" ctrnum="X" aggnum="X" pienum="" tipacq1="" tipacq2="" tipacq3="" tipacq4="" annacq1="0" annacq2="0" annacq3="0" annacq4="0" checkacq1="0" checkacq2="0" checkacq3="0" checkacq4="0" askmagazz="X" id_magazz="1" askmodpag="X" askmpnoeff="" askdestin="X" askrifdesc="" askrifdata="" askrifnum="" askagente="X" askzona="X" asklist="" askbanca="X" askdatiacc="" asktracau="" asktracur="" asktravet="" asktraasp="" asktrapor="" asktracon="" asktrakgc="" colcg="" askprotiva="" scorpiva="" totali="X" totzero="" totneg="" staobb="" stanoc="" provvig="0" toolprint="Fattura" toolbarra="" staintest="X" stalogo="X" viscosto="0" visgiac="0" vislistini="0" visultmov="0" ultmovbef="0" printetic="0" pdcdamag="0" checkfido="0" sogritacc="0" autoqtaonbc="0" copies="0" custde="" docemail="0" txtemail="" clasdoc="carfor" vismargine="0"  />
        </content>
    </table>
    <table name="cfgmagmov">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="id_tipdoc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="aggcosto" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggprezzo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="agggrip" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="riccosto" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="riccostosr" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ricprezzo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="riclist" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="newlist" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggini" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="agginiv" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggcar" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggcarv" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggsca" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggscav" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggordcli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggordfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggfornit" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggcvccar" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggcvcsca" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggcvfcar" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="aggcvfsca" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="statftcli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="statftfor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="askvalori" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="stadesc" type="varchar(30)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipvaluni" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipsconti" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noprint" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipologia" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_acqpdt" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="proobb" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tqtaxpeso" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tqtaxcolli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="lendescriz" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="mancosto" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noprovvig" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="statcscli" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prtdestot" type="char(15)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="is_acconto" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="is_accstor" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="canprezzo0" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="modimpricalc" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_tipdoc,codice" />
        </structure>
        <content rows="19">
            <row id="9" codice="D" descriz="DESCRIZIONI" id_tipdoc="23" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="1" aggscav="1" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="0" askvalori="D" tipvaluni="L" tipsconti="" tipologia="D" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0" statcscli="1" prtdestot=""  />
            <row id="174" codice="GI" descriz="GIACENZA INIZIALE" id_tipdoc="172" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="1" agginiv="1" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="T" tipvaluni="1" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0" statcscli="0" prtdestot=""  />
            <row id="26" codice="E" descriz="SCONTO MERCE" id_tipdoc="23" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="T" tipvaluni="2" tipsconti="" tipologia="E" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="10" codice="M" descriz="VENDITA MERCE" id_tipdoc="23" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="1" aggscav="1" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="0" askvalori="T" id_pdc="92" tipvaluni="2" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0" statcscli="0" prtdestot=""  />
            <row id="11" codice="S" descriz="SPESE FATT/SPED" id_tipdoc="23" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="V" id_pdc="4463" tipvaluni="" tipsconti="" tipologia="S" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="173" codice="D" descriz="DESCRIZIONE DDT" id_tipdoc="171" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="D" tipvaluni="" tipsconti="" tipologia="D" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0" statcscli="0" prtdestot="" is_acconto="0" is_accstor="0" canprezzo0="0" modimpricalc=""  />
            <row id="172" codice="M" descriz="MERCE DDT" id_tipdoc="171" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="T" tipvaluni="2" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="13" codice="D" descriz="DESCRIZIONE" id_tipdoc="24" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="D" tipvaluni="" tipsconti="" tipologia="D" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0"  />
            <row id="14" codice="M" descriz="MERCE RESA N.C." id_tipdoc="24" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="-1" statftfor="0" askvalori="T" id_pdc="92" tipvaluni="2" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="15" codice="V" descriz="VALORE" id_tipdoc="24" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="-1" statftfor="0" askvalori="V" id_pdc="93" tipvaluni="" tipsconti="" tipologia="V" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="179" codice="V" descriz="VALOREX" id_tipdoc="174" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="0" askvalori="V" id_pdc="93" tipvaluni="" tipsconti="" tipologia="V" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="178" codice="S" descriz="SPESE FATT/SPEDX" id_tipdoc="174" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="V" id_pdc="4463" tipvaluni="" tipsconti="" tipologia="S" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="177" codice="M" descriz="CARICO MERCE" id_tipdoc="174" aggcosto="2" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="1" aggcarv="1" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="1" askvalori="T" id_pdc="92" tipvaluni="1" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0" statcscli="0" prtdestot=""  />
            <row id="176" codice="E" descriz="SCONTO MERCEX" id_tipdoc="174" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="T" tipvaluni="2" tipsconti="" tipologia="E" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="175" codice="D" descriz="DESCRIZIONIX" id_tipdoc="174" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="0" statftfor="0" askvalori="D" tipvaluni="" tipsconti="" tipologia="D" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60" mancosto="N" noprovvig="0" statcscli="0" prtdestot=""  />
            <row id="81" codice="W" descriz="VALORE MERCE" id_tipdoc="24" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="-1" statftfor="0" askvalori="V" id_pdc="92" tipvaluni="" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="12" codice="V" descriz="VALORE" id_tipdoc="23" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="0" askvalori="V" id_pdc="93" tipvaluni="" tipsconti="" tipologia="V" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="80" codice="W" descriz="VALORE merce" id_tipdoc="23" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="0" askvalori="V" id_pdc="92" tipvaluni="" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
            <row id="180" codice="W" descriz="VALORE MERCEX" id_tipdoc="174" aggcosto="" aggprezzo="" agggrip="" riccosto="" riccostosr="" ricprezzo="" riclist="" newlist="" aggini="0" agginiv="0" aggcar="0" aggcarv="0" aggsca="0" aggscav="0" aggordcli="0" aggordfor="0" aggfornit="" aggcvccar="0" aggcvcsca="0" aggcvfcar="0" aggcvfsca="0" statftcli="1" statftfor="0" askvalori="V" id_pdc="92" tipvaluni="" tipsconti="" tipologia="M" f_acqpdt="0" proobb="0" tqtaxpeso="0" tqtaxcolli="0" lendescriz="60"  />
        </content>
    </table>
    <table name="movmag_h">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="datreg" type="date" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="datdoc" type="date" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="numdoc" type="int(10)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="numiva" type="int(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datrif" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="numrif" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="desrif" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notedoc" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notevet" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="noteint" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totimponib" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totimposta" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totimporto" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sogritacc" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="perritacc" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="comritacc" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="impritacc" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totritacc" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totdare" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totmerce" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totservi" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tottrasp" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totspese" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totscrip" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totscmce" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totomagg" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totpeso" type="decimal(9,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="totcolli" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="impcontr" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tipdoc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_valuta" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_magazz" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_modpag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bancf" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_speinc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_dest" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_agente" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_zona" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tiplist" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tracau" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tracur" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_travet" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_traasp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_trapor" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tracon" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_reg" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_doctra" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_ann" type="tinyint(1)" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_acq" type="tinyint(1)" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_genrag" type="tinyint(1)" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="id_docacq" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_printed" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="initrasp" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_emailed" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="enable_nocodedes" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="enable_nocodevet" type="tinyint(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodedes_cap" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodedes_citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodedes_descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodedes_id_stato" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodedes_indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodedes_prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_cap" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_citta" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_codfisc" type="char(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_id_stato" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_indirizzo" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_nazione" type="char(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_piva" type="char(20)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nocodevet_prov" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_magazz,datdoc,id_pdc,id_tipdoc,numdoc" />
            <index name="index2" family="KEY" type="BTREE" fields="id_pdc,datdoc,id_tipdoc,numdoc" />
            <index name="index3" family="KEY" type="BTREE" fields="id_reg,datreg" />
            <index name="index4" family="KEY" type="BTREE" fields="id_agente,datreg,id_tipdoc,numdoc" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="movmag_b">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_doc" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_tipmov" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="numriga" type="int(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_prod" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="descriz" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="um" type="char(5)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nmconf" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pzconf" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="qta" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo" type="decimal(13,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="importo" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_aliqiva" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_moveva" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="f_ann" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_acq" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="perpro" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdccg" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="agggrip" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="costot" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="costou" type="decimal(13,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_movacc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_doc,numriga" />
            <index name="index2" family="KEY" type="BTREE" fields="id_prod,id_doc,numriga" />
            <index name="index3" family="KEY" type="BTREE" fields="id_moveva" />
            <index name="index4" family="KEY" type="BTREE" fields="id_movacc" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="macro">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="macro" type="varchar(2048)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="tiplist">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="tipoprezzo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_macro" type="varchar(2048)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="tracau">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="esclftd" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="3">
            <row id="1" codice="VE" descriz="VENDITA" esclftd="0"  />
            <row id="2" codice="CR" descriz="CONTO RIPARAZIONE" esclftd="0"  />
            <row id="3" codice="PU" descriz="PRESTITO D'USO" esclftd="1"  />
        </content>
    </table>
    <table name="tracur">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="askvet" type="tinyint(1)" can_null="NO" key_type="" default_value="0" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="3">
            <row id="1" codice="DE" descriz="DESTINATARIO" askvet="0"  />
            <row id="2" codice="VE" descriz="VETTORE" askvet="1"  />
            <row id="3" codice="MI" descriz="MITTENTE" askvet="0"  />
        </content>
    </table>
    <table name="traasp">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="3">
            <row id="1" codice="C" descriz="CARTONI"  />
            <row id="2" codice="SC" descriz="SCATOLE"  />
            <row id="3" codice="AV" descriz="A VISTA"  />
        </content>
    </table>
    <table name="trapor">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="2">
            <row id="1" codice="A" descriz="ASSEGNATO"  />
            <row id="2" codice="F" descriz="FRANCO"  />
        </content>
    </table>
    <table name="tracon">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="NO" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="2">
            <row id="1" codice="AB" descriz="ASSEGNO BANCARIO"  />
            <row id="2" codice="CO" descriz="CONTANTI"  />
        </content>
    </table>
    <table name="cfgeff">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_banca" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="zona" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="riga" type="int(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="macro" type="mediumtext" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_banca,tipo,zona,riga" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="allegati">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="attscope" type="varbinary(45)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="attkey" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="description" type="varbinary(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="folderno" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="file" type="varbinary(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="size" type="int(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="url" type="varbinary(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datins" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="attach_type" type="tinyint(3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="hidden" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="autotext" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="voiceatt_id" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="attscope,attkey,attach_type,datins" />
            <index name="index2" family="KEY" type="BTREE" fields="attscope,attkey,datins" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="liqiva">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="anno" type="int(4)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="periodo" type="int(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datmin" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datmax" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datliq" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vennor1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vennor2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vencor1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vencor2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="venven1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="venven2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="acqnor1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="acqnor2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="acqcee1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="acqcee2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tivper1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tivper2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vensos1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vensos2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivaind1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivaind2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docper1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docper2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivaesi1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivadet2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivadcp1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivadcp2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="varpre1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="varpre2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="invpre1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="invpre2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docpre1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docpre2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cricom2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivadov1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ivadov2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="percint" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="inttri1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="acciva2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="vertra1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docfin1" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="docfin2" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ciciniz" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ciculiq" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cicuf24" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cicfine" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="crsdet2" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="anno,periodo" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="cfgsetup">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="chiave" type="char(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="flag" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="codice" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="data" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="importo" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="chiave" />
        </structure>
        <content rows="92">
            <row id="1" chiave="azienda_codice" descriz="_azibase"  />
            <row id="2" chiave="azienda_ragsoc" descriz="*** AZIENDA BASE PER INSTALLAZIONI ***"  />
            <row id="3" chiave="azienda_indirizzo" descriz="."  />
            <row id="4" chiave="azienda_cap" descriz="."  />
            <row id="5" chiave="azienda_citta" descriz="."  />
            <row id="6" chiave="azienda_prov" descriz="."  />
            <row id="7" chiave="azienda_codfisc" descriz="."  />
            <row id="8" chiave="azienda_stato" descriz="IT"  />
            <row id="9" chiave="azienda_piva" descriz="."  />
            <row id="10" chiave="esercizio_startgg" descriz="1" importo="1.0"  />
            <row id="11" chiave="esercizio_startmm" descriz="1" importo="1.0"  />
            <row id="12" chiave="contab_decimp" importo="2.0"  />
            <row id="13" chiave="magdec_qta" importo="2.0"  />
            <row id="14" chiave="magqta_prez" importo="3.0"  />
            <row id="15" chiave="x4_version" codice="1.3.07" descriz="0.0.00 "  />
            <row id="16" chiave="x4_version_old" codice="1.3.07" descriz="0.0.00 "  />
            <row id="17" chiave="azienda_numtel" descriz="."  />
            <row id="18" chiave="azienda_numfax" descriz="."  />
            <row id="19" chiave="azienda_email" descriz="."  />
            <row id="20" chiave="tipo_contab" flag="O"  />
            <row id="21" chiave="liqiva_periodic" flag="M"  />
            <row id="22" chiave="contab_valcon" importo="320.0"  />
            <row id="23" chiave="gesfidicli" flag="0"  />
            <row id="24" chiave="bilricl" flag="0"  />
            <row id="25" chiave="conattritacc" flag="0"  />
            <row id="26" chiave="conperritacc" importo="0.0"  />
            <row id="27" chiave="concomritacc" importo="0.0"  />
            <row id="28" chiave="magazz_default:site sede" importo="1.0"  />
            <row id="29" chiave="magdec_prez" importo="3.0"  />
            <row id="30" chiave="magricpre" importo="0.0"  />
            <row id="31" chiave="magpzconf" flag="0"  />
            <row id="32" chiave="magpzgrip" flag="0"  />
            <row id="33" chiave="magscorpcos" flag=""  />
            <row id="34" chiave="magscorppre" flag=""  />
            <row id="35" chiave="magscocat" flag="0"  />
            <row id="36" chiave="magdatchi" data="2008-12-31"  />
            <row id="37" chiave="magnumlis" importo="3.0"  />
            <row id="38" chiave="magdatlis" flag="0"  />
            <row id="39" chiave="mageanprefix" descriz="22"  />
            <row id="40" chiave="magattgrip" flag="0"  />
            <row id="41" chiave="magattgrif" flag="0"  />
            <row id="42" chiave="magdatgrip" flag="0"  />
            <row id="43" chiave="magagggrip" flag="0"  />
            <row id="44" chiave="magalwgrip" flag="0"  />
            <row id="45" chiave="magimgprod" flag="0"  />
            <row id="46" chiave="magdigsearch" flag="0"  />
            <row id="47" chiave="opttabsearch" flag="1"  />
            <row id="48" chiave="optdigsearch" flag="0"  />
            <row id="49" chiave="conbilricl" flag="0"  />
            <row id="50" chiave="magforlis" flag="0"  />
            <row id="51" chiave="magppromo" flag="0"  />
            <row id="52" chiave="optnotifiche" flag="0"  />
            <row id="53" chiave="conbilrcee" flag="0"  />
            <row id="58" chiave="magvisgia" flag="0"  />
            <row id="63" chiave="magprovatt" flag="0"  />
            <row id="64" chiave="magprovcli" flag="0"  />
            <row id="65" chiave="magprovpro" flag="0"  />
            <row id="66" chiave="magprovmov" flag=""  />
            <row id="67" chiave="magprovseq" descriz=""  />
            <row id="68" chiave="consovges" flag="0"  />
            <row id="69" chiave="optbackupdir" descriz="C:\Backup_X4"  />
            <row id="70" chiave="contacts_plugin_version" codice="1.0.04"  />
            <row id="71" chiave="optlnkcrdpdc" flag="1"  />
            <row id="72" chiave="optlnkgrdpdc" flag="0"  />
            <row id="73" chiave="optlnkcrdcli" flag="1"  />
            <row id="74" chiave="optlnkgrdcli" flag="1"  />
            <row id="75" chiave="optlnkcrdfor" flag="1"  />
            <row id="76" chiave="optlnkgrdfor" flag="1"  />
            <row id="77" chiave="maggesacc" flag="0"  />
            <row id="78" chiave="magcdegrip" flag="0"  />
            <row id="79" chiave="magcdegrif" flag="0"  />
            <row id="80" chiave="magviscos" flag="0"  />
            <row id="81" chiave="magvispre" flag="0"  />
            <row id="82" chiave="magviscpf" flag="0"  />
            <row id="83" chiave="magvisbcd" flag="0"  />
            <row id="84" chiave="mytest_plugin_version" codice="1.2.04"  />
            <row id="85" chiave="azienda_titprivacy" descriz=""  />
            <row id="86" chiave="azienda_infatti" descriz=""  />
            <row id="87" chiave="magerplis" importo="0.0"  />
            <row id="88" chiave="magesplis" importo="0.0"  />
            <row id="89" chiave="magvrglis" importo="0.0"  />
            <row id="90" chiave="magvsglis" importo="0.0"  />
            <row id="91" chiave="magreplis" flag="0"  />
            <row id="92" chiave="magrellis" flag="0"  />
            <row id="93" chiave="magseplis" flag="0"  />
            <row id="94" chiave="magsellis" flag="0"  />
            <row id="95" chiave="magnocodevet" flag="0"  />
            <row id="96" chiave="magnocdefvet" flag="0"  />
            <row id="97" chiave="magextravet" flag="0"  />
            <row id="98" chiave="magnocodedes" flag="0"  />
            <row id="99" chiave="magnocdefdes" flag="0"  />
            <row id="100" chiave="magexcsearch" flag="0"  />
        </content>
    </table>
    <table name="cfgftdif">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="id_docgen" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_sepall" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_sepmp" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_sepdest" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_solosta" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_setacq" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_setann" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_setgen" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="1" extra="" />
            <column name="f_nodesrif" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="f_chgmag" type="tinyint(1) unsigned" can_null="NO" key_type="" default_value="0" extra="" />
            <column name="id_chgmag" type="tinyint(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="1">
            <row id="1" codice="FD" descriz="Fatturazione Differita" id_docgen="23" f_sepall="0" f_sepmp="0" f_sepdest="0" f_solosta="0" f_setacq="1" f_setann="1" f_setgen="1" f_nodesrif="0" f_chgmag="0"  />
        </content>
    </table>
    <table name="cfgftddr">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_ftd" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_docrag" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="f_attivo" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_ftd,id_docrag" />
        </structure>
        <content rows="3">
            <row id="1" id_ftd="1" id_docrag="171" f_attivo="1"  />
            <row id="2" id_ftd="1" id_docrag="23" f_attivo="0"  />
            <row id="3" id_ftd="1" id_docrag="24" f_attivo="0"  />
        </content>
    </table>
    <table name="cfgperm">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_utente" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ambito" type="char(60)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_rel" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="attivo" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="leggi" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="scrivi" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="permesso" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="ambito,id_rel,id_utente" />
        </structure>
        <content rows="7">
            <row id="31" id_utente="1" ambito="caumagazz" id_rel="23" leggi="1" scrivi="1"  />
            <row id="35" id_utente="1" ambito="caumagazz" id_rel="171" leggi="1" scrivi="1"  />
            <row id="32" id_utente="2" ambito="caumagazz" id_rel="23" leggi="1" scrivi="1"  />
            <row id="36" id_utente="2" ambito="caumagazz" id_rel="171" leggi="1" scrivi="1"  />
            <row id="21" id_utente="2" ambito="caumagazz" id_rel="24" leggi="1" scrivi="1"  />
            <row id="27" id_utente="2" ambito="caumagazz" id_rel="172" leggi="1" scrivi="1"  />
            <row id="30" id_utente="2" ambito="caumagazz" id_rel="174" leggi="1" scrivi="1"  />
        </content>
    </table>
    <table name="effetti">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_banca" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_caus" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="filepath" type="varchar(250)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
        </structure>
        <content rows="3">
            <row id="6" tipo="R" id_banca="104" id_caus="56" filepath="%allusersprofile%\Trasmissioni RIBA\CASSA RISPARMIUM LIGURIAE"  />
            <row id="7" tipo="R" id_banca="3" id_caus="56" filepath="%allusersprofile%\Trasmissioni RIBA\BANQUUS COMMERCIUM PENINSULA"  />
            <row id="9" tipo="R" filepath=""  />
        </content>
    </table>
    <table name="scadgrp">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="promem">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="datains" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="uteins" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datasca" type="datetime" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="datarem" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="globale" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="oggetto" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="status" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="avvisa" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="datasca" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="promemu">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_promem" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="utente" type="char(2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="refresh" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_promem,utente" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="cfgmagriv">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_caus" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_magazz" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="id_regiva" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_caus,id_magazz,id_regiva" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="marart">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="pdcrange">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="rangemin" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="rangemax" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="3">
            <row id="1" codice="1" descriz="PDC" rangemin="10000" rangemax="19999"  />
            <row id="2" codice="2" descriz="CLI" rangemin="20000" rangemax="29999"  />
            <row id="3" codice="3" descriz="FOR" rangemin="30000" rangemax="99999"  />
        </content>
    </table>
    <table name="brimas">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="tipo" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="bricon">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_bilmas" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_bilmas,codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="id_bilmas,descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="prodpro">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="NO" key_type="MUL" default_value="None" extra="" />
            <column name="id_magazz" type="int(6)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="ini" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="car" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sca" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="iniv" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="carv" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="scav" type="decimal(14,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cvccar" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cvcsca" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cvfcar" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="cvfsca" type="decimal(10,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_prod,id_magazz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="gruprez">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="calcpc" type="char(1)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="calclis" type="char(1)" can_null="NO" key_type="" default_value="None" extra="" />
            <column name="prccosric1" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prccosric2" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prccosric3" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prcpresco1" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prcpresco2" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prcpresco3" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric1" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric2" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric3" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric4" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric5" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric6" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric7" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric8" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisric9" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco1" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco2" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco3" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco4" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco5" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco6" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco7" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco8" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclissco9" type="decimal(6,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_lisdagp" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas1" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas2" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas3" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas4" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas5" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas6" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas7" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas8" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisbas9" type="char(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar1" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar2" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar3" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar4" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar5" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar6" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar7" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar8" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prclisvar9" type="decimal(8,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="nosconti" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="sconticc">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_catart" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(4,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_pdc,id_catart" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="pdt_h">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="uid" type="char(32)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="descriz" type="varchar(64)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="pdtnum" type="int(3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datins" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="ready" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="uid" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="pdt_b">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_h" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="uid" type="char(32)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="barcode" type="char(32)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_prod" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="qta" type="decimal(2,0)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="uid" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="procos">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="anno" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="costou" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="costom" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzop" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo1" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo2" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo3" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo4" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo5" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo6" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo7" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo8" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo9" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_prod,anno" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="progia">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="id_magazz" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="anno" type="int(4)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datgia" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="giacon" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="giafis" type="decimal(12,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="movgen" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="id_prod,id_magazz,anno" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="promo">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="id_prod" type="int(6)" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="datmin" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="datmax" type="date" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="prezzo" type="decimal(15,3)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto1" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto2" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="sconto3" type="decimal(5,2)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="note" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="id_prod,datmin" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="statpdc">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="hidesearch" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="tipevent">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="codice" type="char(10)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="descriz" type="varchar(60)" can_null="YES" key_type="UNI" default_value="None" extra="" />
            <column name="notify_emailto" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notify_xmppto" type="varchar(255)" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="UNIQUE KEY" type="BTREE" fields="codice" />
            <index name="index2" family="UNIQUE KEY" type="BTREE" fields="descriz" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="eventi">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="data_evento" type="datetime" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="wksname" type="varchar(128)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="wksaddr" type="varchar(128)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="usercode" type="varchar(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="username" type="varchar(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_tipevent" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="dettaglio" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tablename" type="char(16)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tableid" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notified_email" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notifieddemail" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notified_xmpp" type="tinyint(1)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="notifieddxmpp" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="data_evento" />
        </structure>
        <content rows="0">
        </content>
    </table>
    <table name="docsemail">
        <structure>
            <column name="id" type="int(6)" can_null="NO" key_type="PRI" default_value="None" extra="auto_increment" />
            <column name="datcoda" type="datetime" can_null="YES" key_type="MUL" default_value="None" extra="" />
            <column name="datsend" type="datetime" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_pdc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="id_doc" type="int(6)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="tipologia" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="mittente" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="destinat" type="varchar(120)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="oggetto" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="testo" type="varchar(1024)" can_null="YES" key_type="" default_value="None" extra="" />
            <column name="documento" type="longblob" can_null="YES" key_type="" default_value="None" extra="" />
            <index name="PRIMARY" family="PRIMARY KEY" type="BTREE" fields="id" />
            <index name="index1" family="KEY" type="BTREE" fields="datcoda" />
        </structure>
        <content rows="0">
        </content>
    </table>
</tablesBackup>
