> Po aktualizaci souboru KB.all je nutné znovu vytvořit konečné automaty. Je to z důvodu možných posunů indexů jednotlivých entit.

# Popis nástrojů
## Tvorba slovníkov

Nástroj ner_cz.py ke své činnosti využívá nástroje figa, který pomocí několika slovníků dokáže v textu rozpoznávat entity.

Tvorba slovníků pro NER i pro autocomplete je prováděna pomocí skriptů create_cedar.sh a create_cedar_autocomplete.sh. Tyto skripty pracují se souborem KBstatsMetrics.all, z něhož získají seznam jmen, který se následně předloží nástrojem figa (aktuální verze: figav1.0), který dané automaty vytvoří.

Použití:

```
./create_cedar.sh
 
 použití: create_cedar.sh --knowledge-base=KBstatsMetrics.all
 
 povinné argumenty:
 
   -k KB, --knowledge-base=KB  cesta ke KBstatsMetrics.all
```

Pro tvorbu slovníků se používá více skriptů z aktuálního adresáře (`figa/make_automat`) upravené pro tvorbu slovníků z české KB. V složce `czechnames/` se nacházejí skripty pro generování alternatívních jmen entit. 

## allow_list
Soubor s výjimkami jmen, které se maji přidat do KA.

## freg_terms_filtred.all
Seznam slov, které se mají z jmen odstranit.

## stop_list
Seznam názvů entit, které nebudou vyhledávány.

## KB2namelist.py
Skript vytahující názvy entit a jejich pozici v `KB.all`.

## uniq_namelist.py
Spojí všechny údaje o číslech řádků entit se stejným názvem.

## utf2symbols
Převod UTF-8 znaků na ASCII reprezentaci.

## str2bin
Převod čísel řádků z formátu `string` do binární podoby.

---

# Popis prefixů
* VISUAL ARTIST (prefix: a)
* LOCATION (prefix: l)
* ARTWORK (prefix: w)
* MUSEUMS (prefix: c)
* EVENT (prefix: e)
* ART FORM (prefix: f) 
* ART MEDIUM (prefix: d)
* ART PERIOD MOVEMENT (prefix: m)
* ART GENRE (prefix: g)
* NATIONALITY (prefix: n)
* MYTHOLOGY (prefix: y)
* ARTIST GROUP OR COLLECTIVE (prefix: r)
* ARTISTS FAMILIES (prefix: i)
