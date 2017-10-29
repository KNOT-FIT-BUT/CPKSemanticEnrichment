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
