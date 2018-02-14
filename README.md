# CPKSemanticEnrichment

## KnowledgeBase

Nástroj pro svojí činnost vyžaduje českou KnowledgeBase (dále jako KB). KB je uložená ve formátu TSV (tab-separated value), kdy na každém jednom řádku jsou uložené informace o jedné entitě.

## Příprava slovníků, nástrojů, ...
Celý proces přípravy je zjednodušen tak, že stačí spustit jediný skript, který zařídí vše potřebné:
`./start.sh`

Tento skript zkompiluje potřebné nástroje a zároveň z KB vytvoří slovníky ([popis tvorby slovníků](https://github.com/KNOT-FIT-BUT/CPKSemanticEnrichment/tree/master/figa/make_automat#tvorba-slovn%C3%ADkov))

## Nástroj ner_cz.py

Nástroj na rozpoznávání a disambiguaci (anotaci) entit je implementovaný ve skriptu ner_cz.py (pro jeho činnost je potřeba provést kroky uvedené v předchozí kapitole). Skript ner_cz.py využívá ke svojí činnosti KB, která je nahraná ve sdílené paměti pomocí nástrojů z adresáře SharedKB (není třeba nic dalšího spouštět, vše je zahrnuto v předchozím skriptu `./start.sh`).

Nástroj pracuje s KB s přidanými sloupci, které obsahují statistická data z Wikipedie a předpočítané skóre pro disambiguaci. 

```
 použití: ner_cz.py [-h] [-a | -s] [-d] [-f FILE]
 
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

### Výstup

Na standardní výstup nástroj vypisuje seznam nalezených entit v pořadí, v jakém se vyskytují ve vstupním textu. Každé jedné entitě patří jeden řádek; sloupce jsou odděleny znakem tabulátor. Řádky vstupu mají formát:

```
BEGIN_OFFSET    END_OFFSET      TYPE    TEXT    OTHER
```

`BEGIN_OFFSET` a `END_OFFSET` vyjadřují pozici začátku a konce entity v textu.

`TYPE` označuje typ entity: `kb` pro položku KB, `date` a `interval` pro datum a interval, `coref` pro koreferenci zájménem nebo částí jména osoby.

`TEXT` obsahuje textovou podobu entity tak, jak se vyskytla ve vstupním textu.

`OTHER` pro typy `kb` a `coref` má podobu seznamu odpovídajících čísel řádků v KB oddělených znakem středník (`;`). Pokud je zapnutá disambiguace, zvolený je pouze jeden řádek odpovídající nejpravděpodobnějšímu významu. Při použití skriptu s parametrem `-s` se zobrazí dvojice číslo řádku a ohodnocení entity, dvojice jsou od sebe odděleny středníkem. Pro typy `date` a `interval` obsahuje údaj v normalizovaném ISO formátu.

### Popis činnosti

Nástroj funguje podobně jako anglická verze, kontextová disabiguace je ale o něco rozšířená. V prvním kole se pro jednotlivé odstavce ukládají informace o rozpoznaných entitách podle jejich typů. V druhém kole se tyto informace využívají pro lepší určení konkrétní entity.

U osob se pro výpočet skóre využívají informace o předešlých výskytech dané osoby v odstavci. Kromě toho se pracuje i s výskytem lokací v daném odstavci, kde se sleduje výskyt lokací, které jsou spojené s danou osobou, tedy místem její narození apod. Využívají se i datumy spojené s touto osobou a jejich výskyt v odstavci a taktéž zaměstnání dané osoby apod.

U ostatních entit je postup podobný. Sledují se informace z odstavce, které jsou s danou entitou spojené a pomáhají tak s větší jistotou vybrat správnou entitu.

Nástroj taktéž ropoznává jmenné koreference, koreference zájmen a datumy v textu.
