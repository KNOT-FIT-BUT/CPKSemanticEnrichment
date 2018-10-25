"""
Created on 17. 6. 2018

Modul pro práci s gramatikou (Bezkontextovou).

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""
from namegenPack import Errors
import re
from typing import Set, Dict
from namegenPack.morpho.MorphCategories import MorphCategory, Gender, Number,\
    MorphCategories, POS, StylisticFlag, Case
from enum import Enum
from builtins import isinstance
from namegenPack.Word import Word, WordTypeMark
import itertools
import copy

class Terminal(object):
    """
    Reprezentace parametrizovaného terminálu.
    """
    
    class Type(Enum):
        """
        Druh terminálu.
        """
        EOF= 0 #konec vstupu
        
        N= "1"    #podstatné jméno
        A= "2"    #přídavné jméno
        P= "3"    #zájméno
        C= "4"    #číslovka
        V= "5"    #sloveso
        D= "6"    #příslovce
        R= "7"    #předložka
        RM= "7m"    #předložka za níž se ohýbají slova (von, da, de)
        J= "8"    #spojka
        T= "9"    #částice
        I= "10"   #citoslovce
        ABBREVIATION= "a"  #zkratka

        DEGREE_TITLE= "t"   #titul
        ROMAN_NUMBER= "r"   #římská číslice
        INITIAL_ABBREVIATION= "ia"    #Iniciálová zkratka.
        X= "x"    #neznámé
        
        @property
        def isPOSType(self):
            """
            Určuje zda-li se jedná o typ terminálu odpovídajícím slovnímu druhu.
            
            :return: True odpovídá slovnímu druhu. False jinak.
            :rtype: bool
            """
            try:
                return self.isPOS
            except AttributeError:
                #ptáme se poprvé
                self.isPOS=self in self.POSTypes
                return self.isPOS
            
        def toPOS(self):
            """
            Provede konverzi do POS.
            Pokud nelze vrací None
            
            :return: Mluvnická kategorie.
            :rtype: POS
            """
            try:
                return self.toPOSMap[self]
            except KeyError:
                #lze převést pouze určité typy terminálu
                #a to pouze typy terminálu, které vyjadřují slovní druhy
                return None
        
    Type.POSTypes={Type.N, Type.A,Type.P,Type.C,Type.V,Type.D,Type.R,Type.RM,Type.J,Type.T, Type.I, Type.ABBREVIATION}
    """Typy, které jsou POS"""
    
    Type.toPOSMap={
                    Type.N: POS.NOUN,           #podstatné jméno
                    Type.A: POS.ADJECTIVE,      #přídavné jméno
                    Type.P: POS.PRONOUN,        #zájméno
                    Type.C: POS.NUMERAL,        #číslovka
                    Type.V: POS.VERB,           #sloveso
                    Type.D: POS.ADVERB,         #příslovce
                    Type.R: POS.PREPOSITION,    #předložka
                    Type.RM: POS.PREPOSITION_M,    #předložka za níž se ohýbají slova
                    Type.J: POS.CONJUNCTION,    #spojka
                    Type.T: POS.PARTICLE,       #částice
                    Type.I: POS.INTERJECTION,    #citoslovce
                    Type.ABBREVIATION: POS.ABBREVIATION    #zkratka
                    }
    """Zobrazení typu do POS."""
    
    class Attribute(object):
        """
        Terminálový atributy.
        """
        
        
        class Type(Enum):
            """
            Druh atributu.
            """
            
            GENDER="g"  #rod slova musí být takový    (filtrovací atribut)
            NUMBER="n"  #mluvnická kategorie číslo. Číslo slova musí být takové. (filtrovací atribut)
            CASE="c"    #pád slova musí být takový    (filtrovací atribut)
            TYPE="t"    #druh slova ve jméně Křestní, příjmení atd. (Informační atribut)
            MATCH_REGEX="r"    #Slovo samotné sedí na daný regulární výraz. (Speciální atribut)
            #Pokud přidáte nový je třeba upravit Attribute.createFrom a isFiltering


            @property
            def isFiltering(self):
                """
                Určuje zda-li daný typ je filtrovacím (klade dodatečné restrikce).
                
                :return: True filtrovací. False jinak.
                :rtype: bool
                """

                return self in self.FILTERING_TYPES
            
        Type.FILTERING_TYPES={Type.GENDER, Type.NUMBER, Type.CASE}
        """Filtrovací atributy. POZOR filtrovací atributy musí mít value typu MorphCategory!"""
        
        def __init__(self, attrType, val):
            """
            Vytvoří atribut neterminálu.
            
            :param attrType: Druh attributu.
            :type attrType: self.Type
            :param val: Hodnota atributu.
            :raise InvalidGrammarException: Při nevalidní hodnotě atributu.
            """
            
            self._type=attrType
            if self.type.isFiltering and not isinstance(val, MorphCategory):
                #u filtrovacích atributů musí být hodnota typu MorphCategory
                raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE)
            self._val=val
            
        @classmethod
        def createFrom(cls, s):
            """
            Vytvoří atribut z řetězce.
            
            :param s: Řetezec reprezentující atribut a jeho hodnotu
                Příklad: "g=M"
            :type s: str
            :raise InvalidGrammarException: Při nevalidní hodnotě atributu.
            """
            
            aT, aV= s.strip().split("=")
            try:
                t=cls.Type(aT)
            except ValueError:
                #neplatný argumentu
                
                raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_ARGUMENT, \
                                              Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_ARGUMENT).format(s))
            v=None
            
            #vytvoříme hodnotu atributu
            if cls.Type.GENDER==t:
                v=Gender.fromLntrf(aV)
            elif cls.Type.NUMBER==t:
                v=Number.fromLntrf(aV)
            elif cls.Type.CASE==t:
                v=Case.fromLntrf(aV)
            elif cls.Type.MATCH_REGEX==t:
                try:
                    v=re.compile(aV[1:-1])  #[1:-1] odstraňujeme # ze začátku a konce
                except re.error:
                    raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_ARGUMENT, \
                                              Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_ARGUMENT).format(s))
            else:
                v=WordTypeMark(aV)
            
            return cls(t,v)
        
        @property
        def type(self):
            return self._type
        
        @property
        def value(self):
            """
            :return: Hodnota attributu.
            """
            return self._val
        
        @property
        def valueRepresentation(self):
            """
            :return: Reprezentace hodnoty attributu.
            """
            return self._val if self.type!=self.Type.MATCH_REGEX else self._val.pattern
            
        
        def __str__(self):
            return str(self._type.value)+"="+str(self.valueRepresentation)
                        
        def __hash__(self):
            return hash((self._type, self._val))
        
        def __eq__(self, other):
            if self.__class__ is other.__class__:
                return self._type==other._type and self._val==other._val
            
            return False
        
    
    def __init__(self, terminalType, attr=set()):
        """
        Vytvoření terminálu.
        Pokud není předán atribut s typem slova ve jméně, tak je automaticky přidán
        attribut s hodnotou WordTypeMark.UNKNOWN
        
        :param terminalType: Druh terminálu.
        :type terminalType: Type
        :param attr: Attributy terminálu. Určují dodatečné podmínky/informace na vstupní slovo.
                Musí vždy obsahovat atribut daného druhu pouze jedenkrát. Jinak může způsobit nedefinované chování
                u nějakých metod.
        :type attr: Attribute
        """
        
        self._type=terminalType
        
        
        #zjistíme, zda-li byl předán word type mark
        if not any(a.type==self.Attribute.Type.TYPE for a in attr):
            #nebyl, přidáme neznámý
            attr=attr|set([self.Attribute(self.Attribute.Type.TYPE, WordTypeMark.UNKNOWN)])
        
        self._attributes=frozenset(attr)
        
        #pojďme zjistit hodnoty filtrovacích atributů
        self._fillteringAttrVal=set(a.value for a in self._attributes if a.type.isFiltering)
        
    def getAttribute(self, t):
        """
        Vrací atribut daného druhu.
        
        :param t: druh attributu
        :type t: self.Attribute.Type
        :return: Atribut daného druhu a None, pokud takový atribut nemá.
        :rtype: self.Attribute | None
        """
        
        for a in self._attributes:
            if a.type==t:
                return a
        
        return None
    
    @property
    def type(self):
        """
        Druh terminálu.
        
        :rtype: self.Type
        """
        return self._type
        
    @property
    def fillteringAttrValues(self):
        """
        Získání všech hodnot attributů, které kladou dodatečné podmínky (např. rod musí být mužský).
        Všechny takové attributy mají value typu MorphCategory.
        Nevybírá informační atributy.
        
        :return: Hodnoty filtrovacích atributů, které má tento terminál.
        :rtype: Set[Attribute]
        """
    
        return self._fillteringAttrVal
    
    def tokenMatch(self, t):
        """
        Určuje zda daný token odpovídá tomuto terminálu.
        
        :param t: Token pro kontrolu.
        :type t: Token
        :return: Vrací True, pokud odpovídá. Jinak false.
        :rtype: bool
        :raise WordCouldntGetInfoException: Problém při analýze slova.
        """
        
        mr=self.getAttribute(self.Attribute.Type.MATCH_REGEX)
        if mr is not None and not mr.value.match(str(t.word)):
            #kontrola na regex match neprošla
            return False
            
        #Zjistíme zda-li se jedná o token, který potenciálně potřebuje analyzátor (ANALYZE, ROMAN_NUMBER)
        
        if t.type!=Token.Type.ANALYZE and t.type!=Token.Type.ROMAN_NUMBER:
            #Jedná se o jednoduchý token bez nutnosti morfologické analýzy.
            return t.type.value==self._type.value   #V tomto případě požívá terminál a token stejné hodnoty u typů
        else:
            #Token je buď ANALYZE, nebo se jedná o římské číslo.
            #Musíme zjistit jaký druh terminálu máme
            if self._type.isPOSType:
                #jedná se o typ terminálu používající analyzátor
                pos=t.word.info.getAllForCategory(MorphCategories.POS, self.fillteringAttrValues, {StylisticFlag.COLLOQUIALLY})  #nechceme hovorové
                
                #máme všechny možné slovní druhy, které prošly atributovým filtrem 
                return self._type.toPOS() in pos
            else:
                #pro tento terminál se nepoužívá analyzátor
                #musí být shoda na římské číslo
                return t.type.value==self._type.value==Token.Type.ROMAN_NUMBER.value

    def __str__(self):
        s=str(self._type.value)
        if self._attributes:
            s+="{"+", ".join( str(a) for a in self._attributes )+"}"
        return s
    
    def __hash__(self):
        return hash((self._type,self._attributes))
        
    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self._type==other._type and self._attributes==other._attributes
        
        return False
class Token(object):
    """
    Token, který je získán při lexikální analýze.
    """
    
    class Type(Enum):
        """
        Druh tokenu
        """
        ANALYZE=1   #komplexní typ určený pouze morfologickou analýzou slova
        DEGREE_TITLE= Terminal.Type.DEGREE_TITLE.value   #titul
        ROMAN_NUMBER= Terminal.Type.ROMAN_NUMBER.value   #římská číslice Je třeba zohlednit i analýzu kvůli shodě s předložkou V
        INITIAL_ABBREVIATION= Terminal.Type.INITIAL_ABBREVIATION.value   #Iniciálová zkratka.
        EOF= Terminal.Type.EOF.value #konec vstupu
        X= Terminal.Type.X.value    #neznámé
        #Pokud zde budete něco měnit je třeba provést úpravy v Token.terminals.

        def __str__(self):
            return str(self.value)
                
        def __hash__(self):
            return hash(self.value)
        
        def __eq__(self, other):
            if self.__class__ is other.__class__:
                return self.value==other.value
            
            return False
    
    def __init__(self, word:Word, tokenType):
        """
        Vytvoření tokenu.
        
        :param word: Slovo ze, kterého token vznikl.
        :type word: namegenPack.Name.Word
        :param tokenType: Druh tokenu.
        :type tokenType: self.Type
        """
        self._word=word
        self._type=tokenType
        
    @property
    def word(self):
        """
        Slovo ze vstupu, které má přiřazeno tento token.
        """
        
        return self._word;
    
    @property
    def type(self):
        """
        Druh tokenu.
        
        :rtype: Type 
        """
        return self._type
    
    def __str__(self):
        return str(self._type)+"("+str(self._word)+")"
    
    
class Lex(object):
    """
    Lexikální analyzátor pro jména.
    """

    ROMAN_NUMBER_REGEX=re.compile(r"^X{0,3}(IX|IV|V?I{0,3})\.?$", re.IGNORECASE)
    
    @classmethod
    def getTokens(cls, name):
        """
        Získání tokenů pro sémantický analyzátor.

        :param name: Jméno pro analýzu
        :type name: Name
        :return: List tokenů pro dané jméno.
        :rtype: [str]
        :raise Word.WordCouldntGetInfoException: Vyjímka symbolizující, že se nepovedlo získat morfologické kategorie ke slovu.
        """
        tokens=[]
        for w in name:
            if cls.ROMAN_NUMBER_REGEX.match(str(w)):
                #římská číslovka
                token=Token(w, Token.Type.ROMAN_NUMBER)
            elif w[-1] == ".":
                if any(str.isdigit(c) for c in w):
                    #obsahuje číslici
                    #nemůže se jednat o zkratku, či titul
                    token=Token(w, Token.Type.ANALYZE)
                else:
                    #slovo neobsahuje číslovku
                    #předpokládáme titul nebo iniciálovou zkratku
                    if len(w)==2:
                        #zkratka
                        token=Token(w, Token.Type.INITIAL_ABBREVIATION)
                    else:
                        #titul
                        token=Token(w, Token.Type.DEGREE_TITLE)
                    
            else:
                #ostatní
                token=Token(w, Token.Type.ANALYZE)
                
            tokens.append(token)
            
        tokens.append(Token(None, Token.Type.EOF)) 
    
        return tokens  
     
class AnalyzedToken(object):
    """
    Jedná se o analyzovaný token, který vzniká při syntaktické analýze.
    Přidává k danému tokenu informace získané analýzou. Informace jako je například zda se má
    dané slovo ohýbat, či nikoliv.
    """
    
    def __init__(self, token:Token, morph:bool=None, matchingTerminal:Terminal=None):
        """
        Pro běžný token vyrobí jaho analyzovanou variantu.
        
        :param token: Pro kterého budujeme analýzu.
        :type token: Token
        :param morph:Příznak zda se slovo, jenž je reprezentováno tímto tokenem, má ohýbat. True ohýbat. False neohýbat.
        :type morph: bool
        :param matchingTerminal: Získaný terminál při analýze, který odpovídal tokenu.
        :type matchingTerminal: Terminal
        """
        
        self._token=token
        self._morph=morph    #příznak zda-li se má dané slovo ohýbat
        self._matchingTerminal=matchingTerminal #Příslušný terminál odpovídající token (získaný při analýze).
        
    @property
    def token(self):
        """
        :param token: Pro který máme tuto analýzu.
        :type token: Token
        """
        return self._token
    
    @property
    def morph(self):
        """
        Příznak zda se slovo, jenž je reprezentováno tímto tokenem, má ohýbat.
        
        :return: None neznáme. True ohýbat. False neohýbat.
        :rtype: bool
        """
        return self._morph
        
    @morph.setter
    def morph(self, val:bool):
        """
        Určení zda-li se má slovo, jenž je reprezentováno tímto tokenem, ohýbat.
        
        :param val: True ohýbat. False neohýbat.
        :type val: bool
        """
        self._morph=val
    
    @property
    def matchingTerminal(self)->Terminal:
        """
        Získaný terminál při analýze, který odpovídal tokenu.
        
        :return: Odpovídající terminál z gramatiky.
        :rtype: Terminal
        """
        
        return self._matchingTerminal
    
    @matchingTerminal.setter
    def matchingTerminal(self, t:Terminal):
        """
        Přiřazení terminálu.
        
        :param t: Odpovídající terminál.
        :type t: Terminal
        """
        
        self._matchingTerminal=t
    
    @property
    def morphCategories(self) -> Set[MorphCategory]:
        """
        Získání morfologických kategorií, které na základě analýzy má dané slovo patřící k tokenu mít.
        Vybere jen ty hodnoty, které v nějaké z kategorii zpřesňují odhad , tedy pokud analýza určí, že dané slovo
        může mít pouze hodnoty v kategorii DegreeOfComparison 1 a 2, tak tyto hodnoty vrátí. Kdyby mohlo slovo nabývat všech
        hodnot, tak je vůbec nevrací.

        Příklad: Analýzou jsme zjistili, že se může jednat pouze o podstatné jméno rodu mužského v jednotném čísle.
        
        Pozor! Je zakázán výběr StylisticFlag.COLLOQUIALLY
        Tyto dodatečné podmínky jsou přímo uzpůsobeny pro použití výsledku ke generování tvarů.
        
        :rtype: Set[MorphCategory]
        """
        
        #nejprve vložíme filtrovací atributy
        categories=self.matchingTerminal.fillteringAttrValues.copy()
        
        
        #můžeme získat další kategorie na základě morfologické analýzy
        if self.matchingTerminal.type.isPOSType:
            #pro práci s morfologickou analýzou musí byt POS type
            
            categories.add(self.matchingTerminal.type.toPOS()) #vložíme požadovaný slovní druh do filtru
            
            #Například pokud víme, že máme přídavné jméno rodu středního v jednotném čísle
            #a morf. analýza nám řekne, že přídavné jméno může být pouze prvního stupně, tak tuto informaci zařadíme
            #k filtrům
                
            for _, morphCategoryValues in self._token.word.info.getAll(categories, {StylisticFlag.COLLOQUIALLY}).items():# hovorové nechceme
                
                if len(next(iter(morphCategoryValues)).__class__)>len(morphCategoryValues):
                    #danou kategorii má cenu filtrovat jelikož analýza určila, že slovo nemá všechny
                    #hodnoty z této kategorie.
                    categories|=morphCategoryValues
   
        return categories

class InvalidGrammarException(Errors.ExceptionMessageCode):
    pass

class Rule(object):
    """
    Reprezentace pravidla pro gramatiku.
    """
    
    TERMINAL_REGEX=re.compile("^(.+?)(\{(.*)\})?$") #oddělení typu a attrbutů z terminálu
    
    def __init__(self, fromString, terminals=None, nonterminals=None):
        """
        Vytvoření pravidla z řetězce.
        formát pravidla: Neterminál -> Terminály a neterminály
        
        :param fromString: Pravidlo v podobě řetězce.
        :type fromString: str
        :param terminals: Zde bude ukládat nalezené terminály.
        :type terminals: set
        :param nonterminals: Zde bude ukládat nalezené neterminály.
        :type nonterminals: set
        :raise InvalidGrammarException: 
             pokud je pravidlo v chybném formátu.
        """
        try:
            self._leftSide, self._rightSide=fromString.split("->")
        except ValueError:
            #špatný formát pravidla
            raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE,
                                          Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE)+"\n\t"+fromString)
            
        self._leftSide=self._parseSymbol(self._leftSide)
        if isinstance(self._leftSide, Terminal) or self._leftSide==Grammar.EMPTY_STR:
            #terminál nebo prázdný řetězec
            #ovšem v naší gramatice může být na levé straně pouze neterminál
            raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE,
                                          Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE)+"\n\t"+fromString)
        
        #neterminál, vše je ok
        if nonterminals is not None:
            nonterminals.add(self._leftSide)

            
        self._rightSide=[x for x in self._rightSide.split()]

        #vytvoříme ze řetězců potřebné struktury a přidáváme nalezené (ne)terminály do množiny (ne)terminálů
        for i, x in enumerate(self._rightSide):
            try:
                self.rightSide[i]=self._parseSymbol(x)
                
                if terminals is not None or nonterminals is not None:
                    if isinstance(self.rightSide[i], Terminal):
                        # terminál
                        if terminals is not None:
                            terminals.add(self.rightSide[i])
                    else:
                        #neterminál nebo prázdný řetězec
                        if self.rightSide[i]!=Grammar.EMPTY_STR:
                            #neterminál
                            if nonterminals is not None:
                                nonterminals.add(self.rightSide[i])
            except:
                #došlo k potížím s aktuálním pravidlem
                raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE, 
                                              Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_INVALID_FILE)+"\n\t"+x+"\t"+fromString)
        
    @classmethod
    def _parseSymbol(cls, s):
        """
        Získá z řetězce symbol z gramatiky.
        
        :param s: Řetězec, který by měl obsahovat neterminál, terminál či symbol prázdného řetězce.
        :type s: str
        :return: Symbol v gramatice
        :raise InvalidGrammarException: 
             pokud je symbol nevalidní
        """
        x=s.strip()
        
        if x==Grammar.EMPTY_STR:
            #prázdný řetězec není třeba dále zpracovávat
            return x
            
        mGroups=cls.TERMINAL_REGEX.match(x)
        #máme naparsovaný terminál/neterminál
        #příklad: rn{g=M,t=G}
        #Group 1.    0-2    `rn`
        #Group 2.    2-11    `{g=M,t=G}`
        #Group 3.    3-10    `g=M,t=G`

        termType=None
        try:
            termType=Terminal.Type(mGroups.group(1) )
        except ValueError:
            #neterminál, nemusíme nic měnit
            #stačí původní reprezentace
            return x
        
        #máme terminál
        attrs=set()
        attrTypes=set() #pro kontorolu opakujicich se typu
        if mGroups.group(3):
            #terminál má argumenty
            
            state="R"   #Read
            attribute=""
            
            #Budeme číst attributy oddělené ,
            #Pokud však narazíme na ", tak čárka nemusí být oddělovačem attributu
             
            for s in mGroups.group(3):
                if state=="R" and s==",":
                    #Read
                    if s==",":
                        #máme potenciální atribut
                        ta=Terminal.Attribute.createFrom(attribute)
                        if ta.type in attrTypes:
                            #typ argumentu se opakuje
                            raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_ARGUMENT_REPEAT, \
                                                              Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_ARGUMENT_REPEAT).format(attribute))
                        attrTypes.add(ta.type)
                        attrs.add(ta)
                        attribute=""
                    elif s=='"':
                        state="Q"  #QUOTATION MARKS
                        attribute+=s
                    else:
                        attribute+=s
                elif "Q":
                    #QUOTATION MARKS
                    if s=='"':
                        state="R"
                        attribute+=s
                    elif s=="\\":
                        state="B" #BACKSLASH
                        attribute+=s
                    else:
                        attribute+=s
                else:
                    #BACKSLASH
                    state="Q"
                    if s=='"':
                        attribute=attribute[:-1]
                        attribute+=s

            if len(attribute)>0:
                #máme potenciální atribut
                ta=Terminal.Attribute.createFrom(attribute)
                if ta.type in attrTypes:
                    #typ argumentu se opakuje
                    raise InvalidGrammarException(Errors.ErrorMessenger.CODE_GRAMMAR_ARGUMENT_REPEAT, \
                                                              Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_ARGUMENT_REPEAT).format(attribute))
                attrTypes.add(ta.type)
                attrs.add(ta)

            
        return Terminal(termType, attrs)
        
        
    def getSymbols(self):
        """
        Vrací všechny terminály a neterminály.
        
        :return: Množinu terminálů a neterminálů figurujících v pravidle.
        :rtype: set
        """
        
        return set(self._leftSide)+set(self._rightSide)
    
    @property
    def leftSide(self):
        """
        Levá strana pravidla.
        :return: Neterminál.
        :rtype: str
        """
        return self._leftSide
    
    @leftSide.setter
    def leftSide(self, value):
        """
        Nová levá strana pravidla.
        
        :param value:Nová hodnota na levé straně prvidla.
        :type value: string
        :return: Neterminál.
        :rtype: str
        """
        self._leftSide=value
    
    @property
    def rightSide(self):
        """
        Pravá strana pravidla.
        
        :return: Terminály a neterminály (epsilon) na právé straně pravidla.
        :rtype: list
        """
        return self._rightSide
    
    @rightSide.setter
    def rightSide(self, value): 
        """
        Nová pravá strana pravidla.
        
        :param value: Nová pravá strana.
        :type value: List()
        :return: Terminály a neterminály (epsilon) na právé straně pravidla.
        :rtype: list
        """
        self._rightSide=value
    
    
    def __str__(self):
        return self._leftSide+"->"+" ".join(str(x) for x in self._rightSide)
    
    def __repr(self):
        return str(self)
    
    def __hash__(self):
            return hash((self._leftSide, tuple(self._rightSide)))
        
    def __eq__(self, other):
        if self.__class__ is other.__class__:
            return self._leftSide==other._leftSide and self._rightSide==other._rightSide
            
        return False


class Symbol(object):
        """
        Reprezentace symbolu na zásobníku
        """
        
        def __init__(self, s, isTerm=True, morph=True):
            """
            Vytvoření symbolu s typu t.
            :param s: Symbol
            :type s:
            :param isTerm: Druh terminál(True)/neterminál(False).
            :type isTerm: bool
            :param morph: Příznak zda se má slovo odpovídající termínálu ohýbat.
                V případě neterminálu tento příznak určuje zda se mají slova odpovídající všem
                terminálů, které je možné vygenerovat z daného neterminálu ohýbat/neohýbat.
                Alternativní definice:
                Flag, který určuje zda-li se nacházíme v části stromu, kde se slova mají ohýbat, či ne.
                Jedná se o zohlednění příznaku self.NON_GEN_MORPH_SIGN z gramatiky.
            :type morph: bool
            """
            
            self._s=s
            self._isTerm=isTerm
            self._morph=morph
            
        @property
        def val(self):
            return self._s
        
        @property
        def isTerm(self):
            """
            True jedná se o terminál. False jedná se neterminál.
            """
            return self._isTerm
        
        @property
        def isMorph(self):
            """
            True ohýbat. False jinak.
            """
            return self._morph
    
class Grammar(object):
    """
    Používání a načtení gramatiky ze souboru.
    Provádí sémantickou analýzu
    """
    EMPTY_STR="ε"   #Prázdný řetězec.
    
    #Má-li neterminál tuto značku na začátku znamená to, že všechny derivovatelné řetězce z něj
    #se nemají ohýbat.
    NON_GEN_MORPH_SIGN="!"   
    
    
    class NotInLanguage(Errors.ExceptionMessageCode):
        """
        Řetězec není v jazyce generovaným danou gramatikou.
        """
        pass
    
    class ParsingTableSymbolRow(dict):
        """
        Reprezentuje řádek parsovací tabulky, který odpovídá symbolu.
        Chová se jako dict() s tím rozdílem, že
        pokud je namísto běžného SymbolRow[Terminal] použito SymbolRow[Token], tak pro daný symbol na zásobníku
        vybere všechna pravidla (vrací množinu pravidel), která je možné aplikovat pro daný token (jeden token může odpovídat více terminálům).
    
        Vkládané klíče musí být Terminály.
        
        """
        
        def __getitem__(self, key):
            """
            Pokud je namísto běžného SymbolRow[Terminal] použito SymbolRow[Token], tak pro daný symbol na zásobníku
            vybere všechna pravidla (vrací množinu pravidel), která je možné aplikovat pro daný token (jeden token může odpovídat více terminálům).
            :param key: Terminal/token pro výběr.
            :type key: Terminal | Token
            :raise WordCouldntGetInfoException: Problém při analýze slova.
            """
            if isinstance(key, Token):
                #Nutné zjistit všechny terminály, které odpovídají danému tokenu.
                res=set()
                for k in self.keys():
                    if k.tokenMatch(key):
                        #daný terminál odpovídá tokenu, přidejme pravidla
                        res|=dict.__getitem__(self, k)
                return res
            else:
                #běžný výběr
                return dict.__getitem__(self, key)
            


    def __init__(self, filePath):
        """
        Inicializace grammatiky jejim načtením ze souboru.
        
        :param filePath: Cesta k souboru s gramatikou
        :type filePath: str
        :raise exception:
            Errors.ExceptionMessageCode pokud nemůže přečíst vstupní soubor.
            InvalidGrammarException pokud je problém se samotnou gramtikou.
        """
        self._terminals=set([Terminal(Terminal.Type.EOF)])  #implicitní terminál je konec souboru
        self._nonterminals=set()
        
        self.load(filePath)

        self._removeAllUsellesSymbols()
        #vytvoříme si tabulku pro parsování
        self._makeTable()
        
    
    def load(self,filePath):
        """
        Načtení gramatiky ze souboru.
        
        :param filePath: Cesta k souboru s gramatikou.
        :type filePath: str
        :raise exception:
            Errors.ExceptionMessageCode pokud nemůže přečíst vstupní soubor.
            InvalidGrammarException pokud je problém se samotnou gramtikou.
            
        """
        try:
            with open(filePath, "r") as fG:
    
                firstNonEmptyLine=""
                for line in fG:
                    firstNonEmptyLine=self._procGFLine(line)
                    if len(firstNonEmptyLine)>0:
                        break
                
                #první řádek je startovací neterminál
                self._startS=self._procGFLine(firstNonEmptyLine)
                if len(self._startS) == 0:
                    raise InvalidGrammarException(code=Errors.ErrorMessenger.CODE_GRAMMAR_NO_START_SYMBOL)

                #Zbytek řádků představuje pravidla. Vždy jedno pravidlo na řádku.
                self._rules=set()
                for line in fG:
                    line=self._procGFLine(line)
                    if len(line)==0:
                        #prázdné přeskočíme
                        continue
                    #formát pravidla: Neterminál -> Terminály a neterminály
                    #přidáváme nová pravidla a zároveň tvoříme množinu terminálů a neterminálů
                    self._rules.add(Rule(line, self._terminals, self._nonterminals))
                    
                
                if len(self._rules) == 0:
                    raise InvalidGrammarException(code=Errors.ErrorMessenger.CODE_GRAMMAR_NO_RULES)

                if self._startS not in self._nonterminals:
                    #startovací symbol není v množině neterminálů
                    raise InvalidGrammarException(code=Errors.ErrorMessenger.CODE_GRAMMAR_START_SYMBOL)
            
        except IOError:
            raise Errors.ExceptionMessageCode(Errors.ErrorMessenger.CODE_COULDNT_READ_INPUT_FILE,
                                              Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_COULDNT_READ_INPUT_FILE)+"\n\t"+filePath)
            
        
    def __str__(self):
        """
        Converts grammar to string.
        in format:
        S=start_symbol
        N={nonterminals}
        T={terminals}
        P={
            rules
        }
        """
        s="S="+self._startS+"\n"
        s+="N={"+", ".join(sorted( str(n) for n in self._nonterminals))+"}\n"
        s+="T={"+", ".join(sorted( str(t) for t in self._terminals))+"}\n"
        s+="P={\n"
        for r in sorted( str(r) for r in self._rules):
            s+="\t"+str(r)+"\n"
        s+="}"
        return s
        
    @staticmethod
    def _procGFLine(line):
        """
        Před zpracování řádku ze souboru s gramatikou. Odstraňuje komentáře a zbytečné bíle znaky.
        
        :param line: Řádek ze souboru s gramatikou.
        :type line: str
        """
        return line.split("#",1)[0].strip()
        
            
    def analyse(self, tokens):
        """
        Provede syntaktickou analýzu pro dané tokeny.
        Poslední token předpokládá EOF. Pokud jej neobsahuje, tak jej sám přidá na konec tokens.
        
        
        :param tokens: Tokeny pro zpracování.
        :type tokens: list
        :return: Dvojici s listem listu pravidel určujících všechny možné derivace a list listů analyzovaných tokenů.
        :rtype: (list(list(Rule)), list(list(AnalyzedToken)))
        :raise NotInLanguage: Řetězec není v jazyce generovaným danou gramatikou.
        :raise WordCouldntGetInfoException: Problém při analýze slova.
        """
        
        if tokens[-1].type!=Token.Type.EOF:
            tokens.append(Token(None,Token.Type.EOF))
            
        # Přidáme na zásoník konec vstupu a počáteční symbol
        stack=[Symbol(Terminal(Terminal.Type.EOF), True, True), Symbol(self._startS, False, self._startS[0]!=self.NON_GEN_MORPH_SIGN)]
        position=0
        
        #provedeme samotnou analýzou a vrátíme výsledek
        return self.crawling(stack, tokens, position)
        
    
    def crawling(self, stack, tokens, position):
        """
        Provádí analýzu zda-li posloupnost daných tokenů patří do jazyka definovaného gramatikou.
        Vrací posloupnost použitých pravidel. Nezastaví se na první vhodné posloupnosti pravidel, ale hledá všechny možné.
        
        Tato metoda slouží především pro možnost implementace zpětného navracení při selhání, či hledání další vhodné posloupnosti
        pravidel.
        
        :param stack: Aktuální obsah zásobníku. (modifukuje jej)
        :type stack: list(Symbol)
        :param tokens: posloupnost tokenů na vstupu
        :type tokens: list(Token)
        :param position: Index aktuálního tokenu. Definuje část vstupní posloupnosti tokenů, kterou budeme procházet.
            Od předaného indexu do konce.
        :type position: integer
        :return: Dvojici s listem listu pravidel určujících všechny možné derivace a list listů analyzovaných tokenů.
        :rtype: (list(list(Rule)), list(list(AnalyzedToken)))
        :raise NotInLanguage: Řetězec není v jazyce generovaným danou gramatikou.
        :raise WordCouldntGetInfoException: Problém při analýze slova.
        """
        aTokens=[]  #analyzované tokeny
        
        while(len(stack)>0):
            s=stack.pop()
            token=tokens[position]
            
            if s.isTerm:
                #terminál na zásobníku
                if s.val.tokenMatch(token):
                    #stejný token můžeme se přesunout
                    #token odpovídá terminálu na zásobníku
                    position+=1
                    
                    #ještě vytvoříme analyzovaný token
                    aTokens.append(AnalyzedToken(token, s.isMorph, s.val))# s je odpovídající terminál
                    
                else:
                    #chyba rozdílný terminál na vstupu a zásobníku
                    raise self.NotInLanguage(Errors.ErrorMessenger.CODE_GRAMMAR_NOT_IN_LANGUAGE, \
                                             Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_NOT_IN_LANGUAGE))
            else:
                #neterminál na zásobníku

                #vybereme všechna možná pravidla pro daný token na vstupu a symbol na zásobníku
                
                actRules=self._table[s.val][token]  #díky použité třídě ParsingTableSymbolRow si můžeme dovolit použít přímo token
                
                if not actRules:
                    #v gramatice neexistuje vhodné pravidlo
                    raise self.NotInLanguage(Errors.ErrorMessenger.CODE_GRAMMAR_NOT_IN_LANGUAGE, \
                                             Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_NOT_IN_LANGUAGE))
                
                #pro každou možnou derivaci zavoláme rekurzivně tuto metodu
                newRules=[]
                newATokens=[]

                for r in actRules:
                    try:
                        #prvně aplikujeme pravidlo na nový stack
                        newStack=stack.copy()
                        self.putRuleOnStack(r, newStack, s.isMorph)
                        
                        #zkusíme zda-li s tímto pravidlem uspějeme
                        resRules, resATokens=self.crawling(newStack, tokens, position)
                        
                        if resRules and resATokens:
                            #zaznamenáme aplikováná pravidla a analyzované tokeny
                            #může obsahovat i více různých derivací
                            for x in resRules:
                                #musíme předřadit aktuální pravidlo a pravidla předešlá
                                newRules.append([r]+x)
                                
                            for x in resATokens:
                                #musíme předřadit předešlé analyzované tokeny
                                newATokens.append(aTokens+x)
                                
                    except self.NotInLanguage:
                        #tato větev nikam nevede, takže ji prostě přeskočíme
                        pass
            
                if len(newRules) == 0:
                    #v gramatice neexistuje vhodné pravidlo
                    raise self.NotInLanguage(Errors.ErrorMessenger.CODE_GRAMMAR_NOT_IN_LANGUAGE, \
                                             Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_GRAMMAR_NOT_IN_LANGUAGE))
                    
                #jelikož jsme zbytek prošli rekurzivním voláním, tak můžeme již skončit
                return (newRules,newATokens)
                    
        
        
        #Již jsme vyčerpali všechny možnosti. Příjmáme naši část vstupní pousloupnosti a končíme.
        #Zde se dostaneme pouze pokud jsme po cestě měli možnost aplikovat pouze jen přímo terminály.
        return ([[]], [aTokens])
     
    def putRuleOnStack(self, rule:Rule, stack, morph):
        """
        Vloží pravou stranu pravidla na zásobník.
        
        :param rule: Pravidlo pro vložení.
        :type rule: Rule
        :param stack: Zásobník pro manipulaci. Obsahuje výsledek.
        :type stack:list
        :param morph: Příznak ohýbání slov.
        :type morph: bool
        """
        
        for rulePart in reversed(rule.rightSide):
            if rulePart!=self.EMPTY_STR: #prázdný symbol nemá smysl dávat na zásobník
                isTerminal=rulePart in self._terminals or rulePart==self.EMPTY_STR
                #aby se jednalo o ohebnou část jména musíme se nacházet v ohebné částistromu (morph=true)
                #a navíc pokud máme neterminál, tak musím zkontrolovat zda-li se nedostáváme do neohebné části
                #rulePart.val[0]!=self.NON_GEN_MORPH_SIGN
                shouldMorph=morph and (True if isTerminal else rulePart[0]!=self.NON_GEN_MORPH_SIGN)
                stack.append(Symbol(rulePart, isTerminal, shouldMorph))
                
    
    @classmethod
    def getMorphMask(cls, rules, morph=True):
        """
        Zjistí pro jaká slova má generovat tvary.
        Tím, že si tvoří z pravidel syntaktický strom.
        
        :param rules: (MODIFIKUJE TENTO PARAMETR!) Pravidla získaná z analýzy (metoda analyse).
        :type rules: list
        :param morph: Pokud je false znamená to, že v této části syntaktického stromu negenerujeme tvary.
        :type morph: boolean
        :return: Maska v podobě listu, kde pro každé slovo je True (generovat) nebo False (negenerovat).
        :rtype: list
        """

        actRule=rules.pop(0)

        if morph:
            #zatím jsme mohli ohýbat, ale to se může nyní změnit
            morph=actRule.leftSide[0]!=cls.NON_GEN_MORPH_SIGN  #příznak toho, že v tomto stromu na tomto místě se mají/nemají ohýbat slova

        morphMask=[]  #maska určující zda-li se má ohýbat. True znamená, že ano. 
        
        
        #máme levou derivaci, kterou budeme symulovat a poznamenáme si vždy
        #zda-li zrovna nejsme v podstromě, který má příznak pro neohýbání.
        #pravidlo je vždy pro první neterminál z leva
        
        for x in [p for p in  actRule.rightSide if p!=cls.EMPTY_STR]:
            if any( x==r.leftSide for r in rules):
                #lze dále rozgenerovávat
                #přidáme masku od potomka
                
                morphMask+=cls.getMorphMask(rules, morph)#rovnou odstraní použitá pravidla v rules
            else:
                #nelze
                morphMask.append(morph)  

        return morphMask
                
    def _simplify(self):
        """
        Provede zjednodušení gramatiky.
        """

        self._eliminatingEpRules()
        self._removeUnaryRules()
        self._removeAllUsellesSymbols()

        
    
    def _removeAllUsellesSymbols(self):
        """
        Provede odstranění zbytečných symbolů.
        
        Neterminál je zbytečný pokud se z něj nedá proderivovat k řetězci.
        Neterminál je také zbytečný pokud se z k němu nedá proderivovat z počátečního neterminálu.
        """
        
        #které neterminály nevedou k řetězci?
        #vytvoříme si množinu obsahující bezpečné symboly, které se určitě derivují k řetězci.
        #Prvně vložíme terminály a epsilon. Ty se sice nederivují, ale zpřehledníme si tím práci.
        deriveToTerminals=self._terminals.copy()
        deriveToTerminals.add(self.EMPTY_STR)

        #Nejprve vezme všechny neterminály, které přímo derivují terminály (i epsilon).
        #Dále nás budou zajímat i pravidla, která obsahují i neterminály, o kterých víme, že vedou na řetězec.
        change=True
        while change:
            #Procházíme dokud dostáváme nové symboly, které také vedou k řetězci
            change=False
            
            for r in self._rules:
                if all(x in deriveToTerminals for x in r.rightSide):
                    if r.leftSide not in deriveToTerminals:
                        deriveToTerminals.add(r.leftSide)
                        change=True
                    
        #odstraníme všechny pravidla obsahující nepovolené neterminály a i samotné nepovolené neterminály
        self._rules={r for r in self._rules if r.leftSide in deriveToTerminals and not any( s not in deriveToTerminals for s in r.rightSide)}
        self._nonterminals={ n for n in self._nonterminals if n in deriveToTerminals}
        
        #Teď budeme odstraňovat neterminály, ke kterým se nedostaneme z počátečního symbolu.
        #začínáme od počátečního symbolu
        usedRules=set()
        usedSymbols={self._startS}
        change=True
        while change:
            change=False
            for r in self._rules:
                if r.leftSide in usedSymbols:
                    if r not in usedRules:
                        #přidáme pravidlo
                        usedRules.add(r)
                        change=True
                        for s in r.rightSide:
                            #přidáme symboly
                            usedSymbols.add(s)
                
        #odstraníme všechny nepoužitá pravidla a symboly
        self._rules=usedRules
        self._nonterminals=self._nonterminals & usedSymbols
        self._terminals=self._terminals & usedSymbols
        
        #musíme přidat ještě terminál s koncem souboru, protože byl zrovna odstraněn
        self._terminals.add(Terminal(Terminal.Type.EOF))
    
    def _eliminatingEpRules(self):
        """
        Provede eliminaci epsilon pravidel.
        """
        
        #vytvoříme empty množinu
        self._makeEmptySets()
        
        tmpRules=set()
        for r in self._rules:
            if not r.rightSide==[self.EMPTY_STR]:   #pravidla A ->ε vynecháváme
                #vytvoříme všechny kombinace z pravidla, kde můžeme vynechat 0-x neterminálu, které se derivují na empty
                
                #0-vynechání
                tmpRules.add(r)
                
                allEmptyOnRSide={n for n in r.rightSide if self._empty[n]}
                
                for i in range(1, len(allEmptyOnRSide)+1):
                    #vynecháváme 1-x symbolů
                    for shouldRemove in itertools.combinations(allEmptyOnRSide, i):
                        #vybraná kombinace pro odstranění
                        newRule=copy.copy(r)
                        #upravíme pravou stranu
                        newRule.rightSide=[s for s in newRule.rightSide if s not in shouldRemove]
                        if len(newRule.rightSide)>0:
                            tmpRules.add(newRule)
        if self._empty[self._startS]:
            tmpRules.add(Rule("S->"+self.EMPTY_STR))
        self._rules=tmpRules
        
        
    def _removeUnaryRules(self):
        """
        Provede odstranění jednoduchých pravidel ve formě: A->B, kde A,B jsou neterminály.
        POZOR!: Předpokládá gramatiku, na kterou bylo použito eliminatingEpRules.
        """
        
        #zjistíme takzvané jednotkové páry (Unit pair).
        #X,Y z N je jednotkový pár, pokud  X=>*Y
        
        unitPairs={r for r in self._rules if len(r.rightSide)==1 and not isinstance(r.rightSide[0], Terminal) and r.rightSide[0]!=self.EMPTY_STR}#na pravé straně je pouze 1 neterminál
        numberOfPairs=0
        while numberOfPairs!=len(unitPairs):
            numberOfPairs=len(unitPairs)
            
            tmpUnitPair=unitPairs.copy()
            for unitPairRule in tmpUnitPair:  #(X->Y)
                for unitPairRuleOther in {r for r in tmpUnitPair if r.leftSide==unitPairRule.rightSide[0] }:#(Y->Z)
                    newRule=copy.copy(unitPairRule)
                    newRule.rightSide=unitPairRuleOther.rightSide[0]
                    unitPairs.add(newRule)#(X->Z)
        
        #odstraníme jednoduchá pravidla
        oldRules=self._rules.copy()
        self._rules -= unitPairs
        
        for unitPairRule in unitPairs:  #X->A
            for r in {oldR for oldR in oldRules if oldR.leftSide==unitPairRule.rightSide[0]}:   #A->w
                if len(r.rightSide)>1 or (isinstance(r.rightSide[0], Terminal) or r.rightSide[0]==self.EMPTY_STR):
                    #na levé straně není pouze neterminál
                    
                    newRule=copy.copy(unitPairRule)
                    newRule.rightSide=r.rightSide
                    self._rules.add(newRule)
        
    def _makeTable(self):
        """
        Vytvoření parsovací tabulky.
        
        """
        self._makeEmptySets()
        #COULD BE DELETED print("empty", self._empty)
        self._makeFirstSets()
        #COULD BE DELETED print("first", self._first)
        self._makeFollowSets()
        #COULD BE DELETED print("follow", self._follow)
        self._makePredictSets()
        #COULD BE DELETED print("predict", ", ".join(str(r)+":"+str(t) for r,t in self._predict.items()))
        
        """
        COULD BE DELETED
        print("predict")
        
        for i, l in enumerate([ str(k)+":"+str(x) for k,x in self._predict.items()]):
            print(i,l)
            
        """

        #inicializace tabulky
        self._table={ n:self.ParsingTableSymbolRow({t:set() for t in self._terminals}) for n in self._nonterminals}
        
        #zjištění pravidla pro daný terminál na vstupu a neterminál na zásobníku
        for r in self._rules:
            for t in self._terminals:
                if t in self._predict[r]:
                    #t může být nejlevěji derivován
                    self._table[r.leftSide][t].add(r)

        #Jen pro testovani self.printParsingTable()
                  
    '''
    Jen pro testovani
    Potřebuje importovat pandas.
    
    def printParsingTable(self):
        """
        Vytiskne na stdout tabulku pro analýzu.
        """
        inputSymbols=[Token.Type.EOF.terminalRepr]+list(sorted(self._terminals))
        
        ordeNon=list(self._nonterminals)
        data=[]
        for n in ordeNon:
            data.append([str(self._table[n][iS]) for iS in inputSymbols])
            
        print(pandas.DataFrame(data, ordeNon, inputSymbols))
    '''
    
    def _makeEmptySets(self, force=False):
        """
        Získání "množin" empty (v aktuální gramatice) v podobě dict s příznaky True/False,
         zda daný symbol lze derivovat na prázdný řetězec.
         
        Jedná se o Dict s příznaky: True lze derivovat na prázdný řetězec, či False nelze. 
        
        :param force: Pokud je True, tak vytvoří množinu empty bez ohledu na to, zda-li je už vytvořena.
            Pokud False, tak ji nebude vytvářet, pokud již existuje.
        :type force: Bool
        """
        if not force:
            try:
                return self._empty
            except AttributeError:
                #tak nic ještě empty nemáme
                pass
            
        self._empty={t:False for t in self._terminals} #terminály nelze derivovat na prázdný řetězec
        self._empty[self.EMPTY_STR]=True    #prázdný řetězec mohu triviálně derivovat na prázdný řetězec
        
        for N in self._nonterminals:
            #nonterminály inicializujeme na false
            self._empty[N]=False
        
        
        #pravidla typu: N -> ε
        for r in self._rules:
            if r.rightSide == [self.EMPTY_STR]:
                self._empty[r.leftSide]=True
            else:
                self._empty[r.leftSide]=False
        
        #hledáme ty, které se mohou proderivovat na prázdný řetězec ve více krocích
        #procházíme pravidla dokud se mění nějaká množina empty
        change=True
        while change: 
            change=False
            
            for r in self._rules:
                if all(self._empty[rN] for rN in r.rightSide):
                    #všechny symboly na pravé straně pravidla lze derivovat na prázdný řetězec
                    if not self._empty[r.leftSide]:
                        #došlo ke změně
                        self._empty[r.leftSide]=True
                        change=True
   
    
    def _makeFirstSets(self):
        """
        Získání "množin" first (v aktuální gramatice) v podobě dict s množinami 
        prvních terminálů derivovatelných pro daný symbol.
        
        Před zavoláním této metody je nutné zavolat _makeEmptySets!
        """

        self._first={t:set([t]) for t in self._terminals} #terminály mají jako prvního samy sebe
        self._first[self.EMPTY_STR]=set()

        #inicializace pro neterminály
        for n in self._nonterminals:
            self._first[n]=set()
            
        #Hledáme first na základě pravidel
        change=True
        while change: 
            change=False
            for r in self._rules:
                #přidáme všechny symboly z first prvního symbolu, který se nederivuje na prázdný
                #také přidáváme first všech po cestě, kteří se derivují na prázdný
                for x in r.rightSide:
                    if self._empty[x]:
                        #derivuje se na prázdný budeme se muset podívat i na další
                        tmp=self._first[r.leftSide] | self._first[x]
                        if tmp!= self._first[r.leftSide]:
                            #došlo ke změně
                            self._first[r.leftSide] = tmp
                            change=True
                    else:
                        #nalezen první, který se nederivuje na prázdný
                        tmp=self._first[r.leftSide] | self._first[x]
                        if tmp!= self._first[r.leftSide]:
                            #došlo ke změně
                            self._first[r.leftSide] = tmp
                            change=True
                        break

    def _makeFollowSets(self):
        """
        Získání množiny všech terminálů, které se mohou vyskytovat vpravo od nějakého neterminálu A ve větné formě.
        
        Před zavoláním této metody je nutné zavolat _makeEmptySets, _makeFirstSets!

        """
        self._follow={ n:set() for n in self._nonterminals} #pouze pro neterminály
        #u startovacího neterminálu se ve větné formě na pravo od něj může vyskytovat pouze konec vstupu
        self._follow[self._startS]=set([Terminal(Terminal.Type.EOF)])
        
        #hledání follow na základě pravidel
        change=True
        while change: 
            change=False
            for r in self._rules:
                for i, x in enumerate(r.rightSide):
                    if x in self._nonterminals:
                        #máme neterminál
                        if i+1<len(r.rightSide):
                            #nejsme na konci
                            tmp=self._follow[x]|self._firstFromSeq(r.rightSide[i+1:])
                            if tmp!=self._follow[x]:
                                #zmena
                                self._follow[x]=tmp
                                change=True
                                
                        if i+1>=len(r.rightSide) or self._emptySeq(r.rightSide[i+1:]):
                            #v pravo je prázdno nebo se proderivujeme k prázdnu
                            
                            tmp=self._follow[x]|self._follow[r.leftSide]
                            if tmp!=self._follow[x]:
                                #zmena
                                self._follow[x]=tmp
                                change=True
                                    
       

        
    
    def _makePredictSets(self):
        """
        Vytvoření množiny Predict(A → x), která je množina všech terminálů, které mohou být aktuálně nejlevěji
        vygenerovány, pokud pro libovolnou větnou formu použijeme pravidlo A → x.
        
        Před zavoláním této metody je nutné zavolat _makeEmptySets, _makeFirstSets, _makeFollowSets!
        
        """
        
        self._predict={}
        
        for r in self._rules:
            if self._emptySeq(r.rightSide):
                self._predict[r]=self._firstFromSeq(r.rightSide)|self._follow[r.leftSide]
            else:
                self._predict[r]=self._firstFromSeq(r.rightSide)
    
    def _firstFromSeq(self,seq):
        """
        Získání množiny first z posloupnosti terminálů a neterminálů
        
        Před zavoláním této metody je nutné zavolat _makeEmptySets, _makeFirstSets!
        
        :param seq: Posloupnost terminálů a neterminálů.
        :type seq: list
        :return: Množina first.
        :rtype: set|None
        """
        
        first=set()
        
        for x in seq:
            if self._empty[x]:
                #derivuje se na prázdný budeme se muset podívat i na další
                first=first|self._first[x]
            else:
                #nalezen první, který se nederivuje na prázdný
                first=first|self._first[x]
                break
        
        return first
    
    def _emptySeq(self,seq):
        """
        Určení množiny empty pro posloupnost terminálů a neterminálů
        
        Před zavoláním této metody je nutné zavolat _makeEmptySets!
        
        :param seq: Posloupnost terminálů a neterminálů.
        :type seq: list
        :return: True proderivuje se k prázdnému řetězce. Jinak false.
        :rtype: bool
        """
        
        return all(self._empty[s] for s in seq)


                
                