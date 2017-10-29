# CPKSemanticEnrichment

# KnowledgeBase

Pre svoju činnosť nástroj vyžaduje českú KnowledgeBase. KBje uložená vo formáte TSV, pričom na každom riadku sú uložené informácie o jednej entite. Bližšie informácie o tvorbe KB a význame jednotlivých stĺpcov sú na wiki stránke:

`https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech3`

Aktuálna verzia českej KB sa nachádza v zložke:

` /mnt/minerva1/nlp/projects/entity_kb_czech3/kb`

## Príprava KB

KB je najskor potrebné nakopírovať do zložky pomocou príkazu:

`cp /mnt/minerva1/nlp/projects/entity_kb_czech3/kb/KB_cs.all .`

Po presune slúži pre prípravu KB skript `prepare_data`. Pred použitím je potrebné zabezpečiť aby sa v zložke nachádzali štatistiky získané z wikipedie. Tie sú aktuálne uložené v súbore `wiki_stats`. V prípade novšej verzie je potrebné tieto štatistiky nakopírovať pomocou príkazu:

`cp cesta_k_statistikam wiki_stats`

Výsledkom skriptu je súbor KBstatsMetrics.all. Popis je zhodný s:

`https://knot.fit.vutbr.cz/wiki/index.php/Decipher_ner#Tvorba_KBstatsMetrics.all`

# Tvorba slovníkov

Nástroj ner.py ke své činnosti využívá nástroje figa, který pomocí několika slovníků dokáže v textu rozpoznávat entity. Popis nástroje figa i slovníků je možné najít na stránce projektu . V této kapitole je popsána pouze jejich tvorba.

Tvorba slovníků pro NER i pro autocomplete je prováděna pomocí skriptů create_cedar.sh a create_cedar_autocomplete.sh. Tyto skripty pracují se souborem KBstatsMetrics.all, z něhož získají seznam jmen, který se následně předloží nástrojem figav1.0, který dané automaty vytvoří.

Tieto skripty sa nachádzajú v zložke:
`figa/make_automat`

Použitie je popísané tu:

```
figa/make_automat/create_cedar.sh
 
 použití: create_cedar.sh [-h] [-l|-u] [-c|-d] --knowledge-base=KBstatsMetrics.all
 
 povinné argumenty:
 
   -k KB, --knowledge-base=KB  cesta ke KBstatsMetrics.all
 
 nepovinné argumenty:
 
   -h, --help                  vypíše nápovědu a skončí
   -l, --lowercase             všechna jména budou převedena na malá písmena
   -u, --uri                   vygeneruje seznam URI
   -c, --cedar (default)       vygeneruje slovníky CEDAR (přípona .ct)
   -d, --darts                 vygeneruje slovníky DARTS (přípona .dct)
```

Pre tvorbu slovníkov sa používaju viaceré skripty zo zložky `figa/make_automat` upravené pre tvorbu slovníkov z českej KB. V zložke `figa/make_automat/czechnames` sú navyše uložené skripty pre generovanie alternatívnych mien entít. Bližšie je popísaný na wiki stránke: `https://knot.fit.vutbr.cz/wiki/index.php/Entity_kb_czech_names`. V prípade novšej verzie je potrebné nahradiť aktuálnu verziu v zložke `czechnames`.

# Nástroj ner.py

Nástroj pre rozpoznávánie a disambiguáciue entít je implementovný v skripte ner.py. Pre jeho činnosť je najprv potrebné pripraviť KB a automat z predchádzajúcich krokov. Skript ner.py využívá k svojej činnosti KB, která je nahraná ve zdielanej pamäti pomocou SharedKB. Bližší popis tohto programu je na wiki stránkach: 

`https://knot.fit.vutbr.cz/wiki/index.php/Decipher_ner#Program_a_knihovny_pro_KB_ve_sd.C3.ADlen.C3.A9_pam.C4.9Bti_.28xdolez52.29`

Nástroj pracuje s knowledge base s pridanými stĺpcami obsahujúcmi štatistické dáta z Wikipedie a predpočítaným skóre pre disambiguáciu. Vyhľadávanie entít v texte a ich disambiguáciu potom umožňuje skript `ner.py`:

```
 použití: ner.py [-h] [-a | -s] [-d] [-f FILE]
 
 Nepovinné argumenty:
   -h, --help            vypíše nápovědu a skončí
   -a, --all             Vypíše všechny entity ze vstupu bez rozpoznání.
   -s, --score           Vypíše pro každou entitu v textu všechny její možné významy a ohodnocení každého z těchto významů.
   -d, --daemon-mode     "mód Daemon" (viz níže)
   -f FILE, --file FILE  Použije zadaný soubor jako vstup.
   -r, --remove-accent   Odstraní diakritiku ze vstupu.
   -l, --lowercase       Převod vstupu na malá písmena a použití 
                         zvláštního automatu pouze s malými písmeny.
Je také možné vstup načítat ze standardního vstupu (možnost využití přesměrování).
```

# Výstup

Na štandardný výstup nástroj vypisuje zoznam nájdených entít v poradí, v akom sa vyskytujú vo vstupnom texte. Každej entite patrí jeden riadok, a stĺpce sú oddelené tabulátormi. Riadky výstupu majú formát:

`BEGIN_OFFSET    END_OFFSET      TYPE    TEXT    OTHER`

BEGIN_OFFSET a END_OFFSET vyjadrujú pozíciu začiatku a konca entity v texte.

TYPE označuje typ entity: kb pre položku knowledge base, date a interval pre datum a interval, coref pre koreferenciu zámenom alebo časťou mena osoby.

TEXT obsahuje textovú podobu entity tak, ako sa vyskytla vo vstupnom texte.

OTHER pre typy kb a coref má podobu zoznamu zodpovedajúcich čísel riadku v knowledge base oddelených znakom ";". Ak je zapnutá disambiguácia, zvolený je len jeden riadok zodpovedajúci najpravdepodobnejšiemu významu. Při použití skriptu s parametrem -s se zobrazí dvojice číslo řádku a ohodnocení entity, dvojice jsou od sebe odděleny středníkem. Pre typy date a interval obsahuje údaj v normalizovanom ISO formáte.

# Popis činnosti

Nástroj funguje podobne ako verzia pre anglickú verziu popísaný tu: `https://knot.fit.vutbr.cz/wiki/index.php/Decipher_ner#Jak_funguje_ner.py.3F_.28xmagdo00.29`

Kontextová disabiguácia je ale o niečo rozšírená. V prvom kole sa pre jednotlivé odstavce ukladajú informácie o rozpoznaných entitách podľa ich typov. V druhom kole sa tieto informácie využívajú pre lepšie určenie konkrétnej entity.

U osob sa pre výpočet skóre potom využívajú informácie o predošlich výskytoch danej osoby v odstavci. Okrem toho sa pracuje aj s výskytom lokácii v danom odstavci, kde sa sleduje výskyt lokácii ktoré sú spojené s danou osobou, teda miestom jej narodenia apod. Vzužívaju sa aj dátumy spojene s touto osobou a ich výskyt v odstavci a taktiež zamestanie osoby apod.

U ostatných entít je postúp podobný. Sledujú sa informácie z odstavca, ktoré sú s danou entitou spojené a pomáhaju tak s vačsiou určitosťou vybrať správnu entitu.

Nástroj taktiež ropoznáva menné koreferencie, koreferencie zámen a dátumy v texte.
