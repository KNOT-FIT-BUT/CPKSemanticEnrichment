# Formát gramatik
Zde si popíšeme formát souboru s gramatikou.
* První řádek je startovací symbol.
* Zbytek řádků představuje pravidla. Vždy jedno pravidlo na řádku.
  * Formát pravidla: Neterminál -> Terminály a neterminály odděleny bílým znakem
* Startovací symbol je z množiny neterminálů. Znak ε je vyhrazen pro prázdný řetězec.
* Pokud je jako 1. znak v neterminálu uveden !, pak se jedná o neohebnou část jména (dědí se dále v derivačním stromu).
* Neterminály mohou být zvoleny libovolně avšak odlišně od terminálů. Nepoužívejte vyhrazené posloupnosti znaků jako jsou: ->.
* Je možné používat komentáře, které jsou uvozeny znakem #. Stejně, tak ignoruje prázdné řádky, či řádky, které obsahují pouze komentář.

Terminály jsou předdefinované. Jejich seznam je následující:

	1	- podstatné jméno
	2	- přídavné jméno
	3	- zájméno
	4	- číslovka
	5	- sloveso
	6	- příslovce
	7	- předložka
	7m	- vybrané předložky von,da a de
	8	- spojka
	9	- částice
	10	- citoslovce
	t	- titul (Slovo s tečkou na konci o délce větší než 2 [včetně tečky])
	r	- římská číslice (od I do XXXIX)
	a	- zkratka
	ia	- Iniciálová zkratka. (Slovo s tečkou na konci o délce 2 [včetně tečky])

Terminálům můžeme přiřazovat atributy. Uvádějí se bezprostředně za terminál do složených závorek. Uvedeme si příklad:

	1{t=G,c=1,n=S,g=M}

Tento zápis říká, že máme podstatné jméno rodu mužského v jednotném čísle, v 1. pádě a druh slova ve jméně je KŘESTNÍ JMÉNO.

Možné atributy a jejich hodnoty:

	g - rod slova    (filtrovací atribut)
		M	mužský životný
	    I	mužský neživotný
	    N	střední
	    F	ženský
	    R	rodina (příjmení)
	n - Mluvnická kategorie číslo.(filtrovací atribut)
		S	jednotné
    	P	množné
    	D	duál
	    R	hromadné označení členů rodiny (Novákovi)
	c - Pád slova.   (filtrovací atribut)
		1	1. pád: Nominativ s pádovými otázkami (kdo, co)
    	2	2. pád: Genitiv (koho, čeho)
    	3	3. pád: Dativ (komu, čemu)
    	4	4. pád: Akuzativ (koho, co)
    	5	5. pád: Vokativ (oslovujeme, voláme)
    	6	6. pád: Lokál (kom, čem)
    	7	7. pád: Instrumentál (kým, čím)
	t - Druh slova ve jméně: Křestní, příjmení atd. (Informační atribut)
		G	Křestní jméno. Příklad: Petra
    	S	Příjmení. Příklad: Novák
    	L	Lokace. Příklad: Brno
    	R	Římská číslice. Příklad: IV
    	7	Předložka.
    	8	Spojka.
    	T	Titul. Příklad: prof.
    	I	Iniciálová zkratka. Příklad H. ve jméně John H. White
    	U	Neznámé
    r - Regulární výraz, který určuje podobu slova.
    	Hodnota musí být vepsána v uvozovkách.
    	
    	Příklad: "^.*ová$"	
    		Všechna slova končící na ová.



## Příklad

    S
	S -> !T_GROUP 1{t=G,c=1,n=S,g=M}
	!T_GROUP -> t{t=T} !T_GROUP	#komentář
	!T_GROUP -> ε
	
	