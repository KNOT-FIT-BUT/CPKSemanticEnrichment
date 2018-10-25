"""
Created on 17. 6. 2018
Modul se třídami pro reprezentaci jména/názvu.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""

from enum import Enum
import sys

from namegenPack import Errors
import logging

from namegenPack.morpho import MorphCategories
from namegenPack.morpho.MorphCategories import Case, StylisticFlag, POS

from typing import List
import namegenPack.Grammar

from namegenPack.Word import Word, WordTypeMark


class Name(object):
    """
    Reprezentace celého jména osoby či lokace.
    """

    
    class NameCouldntCreateException(Errors.ExceptionMessageCode):
        """
        Nepodařilo se vytvořit jméno. Deatil ve zprávě
        """
        pass
    
  
    class Type(Enum):
        """
        Přípustné druhy jmen.
        """
        MALE="M"
        FEMALE="F"
        LOCATION="L"
        
        def __str__(self):
            return self.value

    def __init__(self, name, nType):
        """
        Konstruktor jména.
        
        :param name: Řetězec se jménem.
        :type name: String
        :param nType: Druh jména.
        :type nType: Name.Type
        :raise NameCouldntCreateException: Nelze vytvořit jméno.
        """
        self._type=nType
        
        if self._type is not None:
            #typ je určen nemusí se dělat odhad, pouze pokud se jedná o typ určující jméno osoby, tak může být dále případně změněn.
            try:
                #nejprve převedeme a validujeme druh jména
                self._type=self.Type(nType)
            except KeyError:
                raise self.NameCouldntCreateException(Errors.ErrorMessenger.CODE_INVALID_INPUT_FILE_UNKNOWN_NAME_TYPE,
                                                      Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_INVALID_INPUT_FILE_UNKNOWN_NAME_TYPE)+"\n\t"+name+"\t"+nType)
                    
        #rozdělíme jméno na jednotlivá slova a oddělovače
        words, self._separators = self._findWords(name)
        self._words=[Word(w) for w in words]

        
    def __str__(self):
        n=""
        i=0
        for w in self._words:
            n+=str(w)
            if i < len(self._separators):
                n+=self._separators[i]
            i+=1
            
        return n
    
    def __repr__(self):
        return str((str(self), self._type))
    
    def __eq__(self, other):
        return str(self)==str(other) and self._type == other._type
    
    def __hash__(self):
        return hash(str(self))^hash(self._type)
    
    def __iter__(self):
        for w in self._words:
            yield w
            
    def guessType(self, grammars=None, tokens:List[namegenPack.Grammar.Token]=None):
        """
        Provede odhad typu jména. Jedná se o jisté zpochybnění zda-li se jedná o mužské, či ženské jméno.
        Jména lokací nezpochybňujě. 
        Přepíše typ jména pokud si myslí, že je jiný.
        Pokud není typ jména uveden odhadne jej, ovšem pevně předpokládá, že se jedná o jméno osoby.
        (Dle zadání má být automaticky předpokládána osoba, kde se může stát, že typ není uveden.)
        
        :param grammars: Aktivuje pokročilé určování typů jména na základě gramatik.
            Klíč je typ jména(self.Type) a hodnota je příslušná gramatika. Pokud jméno patří právě do jednoho jazyka
            generovaným jednou z poskytnutých gramatik, tak mu je přiřazen příslušný typ.
        :type grammars: None, Dict[Grammar]
        :param tokens: Tokeny odpovídající tomuto jménu. Tento volitelný parametr je zde zaveden pro zrychlení výpočtu, aby nebylo nutné v některých případech
            provádět vícekrát lexikální analýzu. Pokud bude vynechán nic se neděje jen si provede lexikální analýzu sám.
        :type tokens: List[Token]
        :return: Zde vrací analyzované tokeny, získané při analýze pomocí gramatiky, která generuje jazyk
            v němž je toto jméno. Pokud je jméno ve více gramatikách nebo v žádné vrátí None.
        :rtype aTokens: List | None
        :raise Word.WordCouldntGetInfoException:Pokud se nepodařilo analyzovat nějaké slovo.
        """
        if self._type==self.Type.LOCATION:
            #lokace -> ponecháváme
            return
        if not tokens:
            tokens=namegenPack.Grammar.Lex.getTokens(self)

        #zkusíme zpochybnit typ jména
        changeTo=None
        #najdeme první podstatné nebo přídavné jméno od konce (příjmení)
        #Příjmení jak se zdá může být i přídavné jméno (`Internetová jazyková příručka <http://prirucka.ujc.cas.cz/?id=320#nadpis3>`_.)
        
        try:
            for token in reversed(tokens):
                if token.type==namegenPack.Grammar.Token.Type.ANALYZE:
                    #získáme možné mluvnické kategorie
                    analyze=token.word.info
                    posCat=analyze.getAllForCategory(MorphCategories.MorphCategories.POS, {Case.NOMINATIVE})    #máme zájem jen o 1. pád
                    if MorphCategories.POS.NOUN in posCat or MorphCategories.POS.ADJECTIVE in posCat:
                        if token.word[-3:] == "ová":
                            #muž s přijmení končícím na ová, zřejmě není
                            #změníme typ pokud není ženský
                            changeTo=self.Type.FEMALE
                        break
        except Word.WordCouldntGetInfoException:
            #nepovedlo se získat informace o slově
            #končíme
            return
    
        aTokens=None
        if changeTo is None and grammars:
            #příjmení nekončí na ová
            for t, g in grammars.items():
                try:
                    _, tmpATokens=g.analyse(tokens)

                    if changeTo is None:
                        #zatím odpovída jedna gramatika
                        changeTo=t
                        aTokens=tmpATokens
                    else:
                        #více než jedna gramatika odpovídá
                        changeTo=None
                        aTokens=None
                        break
                        
                except namegenPack.Grammar.Grammar.NotInLanguage:
                    continue

                    
        if changeTo is not None:
            if self._type is None:
                logging.info("Pro "+str(self)+" přiřazuji "+str(changeTo)+".")
            elif self._type is not changeTo:
                logging.info("Pro "+str(self)+" měním "+str(self._type)+" na "+str(changeTo)+".")    
            self._type=changeTo
        
        return aTokens
        
    @property
    def words(self):
        """
        Slova tvořící jméno.
        @return: Slova ve jméně
        @rtype: list
        """
        
        return self._words  
    
    @property
    def separators(self):
        """
        Oddělovače ve jméně.
        @return: Oddělovače ve jméně
        @rtype: list
        """
        
        return self._separators
    
    @staticmethod
    def _findWords(name):
        """
        Získání slov a oddělovačů v daném slově.
        
        :param name: Daný název.
        :type name: String
        :return: Dvojici se slovy a oddělovači.
        """
        
        words=[]
        separators=[]
        
        actWord=""
        actSeparator=""
        
        #Procházíme jméno a hledáme slova s jejich oddělovači.
        #Vynacháváme oddělovače na konci a začátku.
        for c in name:
            if (c.isspace() or c=='-'):
                #separátor
                
                if len(actWord)>0:
                    #počáteční vynecháváme
                    actSeparator+=c
            else:
                #znak slova
                if len(actSeparator)>0:
                    #již se má načítat další slovo
                    #uložíme to staré a příslušný separátor
                    words.append(actWord)
                    actWord=""
                    
                    separators.append(actSeparator)
                    actSeparator=""
                    
                actWord+=c
            
                
        if len(actWord)>0:
            words.append(actWord)
        
        return (words, separators)
    
    
    def simpleWordsTypesGuess(self,tokens:List[namegenPack.Grammar.Token]=None):
        """
        Provede zjednodušený odhad typů slov ve jméně. Bez použití morfologické analýzy.
        
        :param tokens: Tokeny odpovídající tomuto jménu. Tento volitelný parametr je zde zaveden pro zrychlení výpočtu, aby nebylo nutné v některých případech
            provádět vícekrát lexikální analýzu. Pokud bude vynechán nic se neděje jen si provede lexikální analýzu sám.
        :type tokens: List[Token]
        :return: Typy pro slova ve jméně.
        :rtype: List(namegenPack.Word.WordTypeMark)
        """
        
        if not tokens:
            tokens=namegenPack.Grammar.Lex.getTokens(self)
        
        types=[]
        
        #používá se u mužských/ženských jmen, kde za předložkou dáváme lokaci
        womanManType=namegenPack.Word.WordTypeMark.GIVEN_NAME 
        
        for token in tokens:
            if token.type==namegenPack.Grammar.Token.Type.ANALYZE:
                if self._type==self.Type.LOCATION:
                    types.append(namegenPack.Word.WordTypeMark.LOCATION)
                else:
                    try:

                        pos=token.word.info.getAllForCategory(MorphCategories.MorphCategories.POS)  
                        if len({POS.PREPOSITION, POS.PREPOSITION_M} & pos)>0:
                            #jedná se o předložku
                            types.append(namegenPack.Word.WordTypeMark.PREPOSITION)
                            #přepneme z křestního na lokaci
                            womanManType=namegenPack.Word.WordTypeMark.LOCATION
                        else:
                            types.append(womanManType)
                            
                    except Word.WordCouldntGetInfoException:
                        types.append(womanManType)
            elif token.type==namegenPack.Grammar.Token.Type.INITIAL_ABBREVIATION:
                types.append(namegenPack.Word.WordTypeMark.INITIAL_ABBREVIATION)
            elif token.type==namegenPack.Grammar.Token.Type.ROMAN_NUMBER:
                if self._type!=self.Type.LOCATION:
                    #může být i předložka v, kvůli stejné reprezentaci s římskou číslicí 5
                    if str(token.word)=="v":
                        #jedná se o malé v bez tečky, bereme jako předložku
                        types.append(namegenPack.Word.WordTypeMark.PREPOSITION)
                        #přepneme z křestního na lokaci
                        womanManType=namegenPack.Word.WordTypeMark.LOCATION
                    else:
                        types.append(namegenPack.Word.WordTypeMark.ROMAN_NUMBER)
                else:
                    types.append(namegenPack.Word.WordTypeMark.ROMAN_NUMBER)
            elif token.type==namegenPack.Grammar.Token.Type.DEGREE_TITLE:
                types.append(namegenPack.Word.WordTypeMark.DEGREE_TITLE)
            else:
                types.append(namegenPack.Word.WordTypeMark.UNKNOWN)
        
        if types.count(namegenPack.Word.WordTypeMark.GIVEN_NAME)>1:   #máme více jak jedno křestní
            #poslední křestní se stane příjmením
            
            for i in range(len(types)-1, -1, -1):
                if types[i]==namegenPack.Word.WordTypeMark.GIVEN_NAME:
                    types[i]=namegenPack.Word.WordTypeMark.SURNAME
                    break
            if self._type==self.Type.FEMALE: 
                #+ u žen každé křestní končící na ová se stane příjmením
                for i in range(len(types)):
                    if types[i]==namegenPack.Word.WordTypeMark.GIVEN_NAME and self._words[i][-3:] == "ová":
                        types[i]=namegenPack.Word.WordTypeMark.SURNAME
        
        return types
    
    def genMorphs(self, analyzedTokens:List[namegenPack.Grammar.AnalyzedToken]):
        """
        Na základě slovům odpovídajících analyzovaných tokenů ve jméně vygeneruje tvary jména.
        
        :param analyzedTokens: Analyzované tokeny, získané ze syntaktické analýzy tohoto jména.
        :type analyzedTokens: List[namegenPack.Grammar.AnalyzedToken]
        :return:  Vygenerované tvary.
        :rtype: list(str)
        :raise Word.WordNoMorphsException: Pokud se nepodaří získat tvary u nějakého slova.
        :raise Word.WordMissingCaseException: Pokud chybí nějaký pád.
        :raise WordCouldntGetInfoException: Vyjímka symbolizující, že se nepovedlo získat mluvnické kategorie ke slovu.
        """
        
        #získáme tvary jednotlivých slov
        genMorphsForWords=[]
        for word, aToken in zip(self._words, analyzedTokens):
            if aToken.morph:
                cateWord=aToken.morphCategories    #podmínky na původní slovo

                cateMorph=set() #podmínky přímo na tvary
                #překopírujeme a ignorujeme pády, jelikož nemůžeme vybrat jen jeden, když chceme
                #generovat všechny
                for x in cateWord:
                    if x.category() !=  MorphCategories.MorphCategories.CASE:
                        cateMorph.add(x)
    
                genMorphsForWords.append(word.morphs(cateMorph, cateWord))
            else:
                genMorphsForWords.append(None)

        #z tvarů slov poskládáme tvary jména
        #Set[Tuple[MARule,str]]
        morphs=[]
        

        for c in [Case.NOMINATIVE, Case.GENITIVE, Case.DATIVE, Case.ACCUSATIVE, Case.VOCATIVE, Case.LOCATIVE, Case.INSTRUMENTAL]:#pády
            morph=""
            sepIndex=0
            for i, (word, aToken) in enumerate(zip(self._words, analyzedTokens)):
                if aToken.morph and isinstance(genMorphsForWords[i], set):
                    #ohýbáme
                    notMatch=True
                    for maRule, wordMorph in genMorphsForWords[i]:
                        #najdeme tvar slova pro daný pád
                        try:
                            if maRule[MorphCategories.MorphCategories.CASE]==c:
                                if not notMatch:
                                    #můžeme mít více tvarů daného slova
                                    #toto je jeden z dalších tvarů
                                    morph += "/"
                                morph+=wordMorph+"["+maRule.lntrf+"]"
                                wordType=aToken.matchingTerminal.getAttribute(namegenPack.Grammar.Terminal.Attribute.Type.TYPE)
                                if wordType!=WordTypeMark.UNKNOWN:
                                    morph+="#"+str(wordType.value)
                                notMatch=False
                        except KeyError:
                            #pravděpodobně nemá pád vůbec
                            pass
                        
                    if notMatch:
                        #nepovedlo se získat některý pád
                        
                        raise Word.WordMissingCaseException(word, Errors.ErrorMessenger.CODE_WORD_MISSING_MORF_FOR_CASE,\
                                    Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_WORD_MISSING_MORF_FOR_CASE)+"\t"+str(c.value)+"\t"+str(word))
                else:
                    #neohýbáme
                    morph+=str(word)+"#"+str(aToken.matchingTerminal.getAttribute(namegenPack.Grammar.Terminal.Attribute.Type.TYPE).value)
                
                #přidání oddělovače slov
                if sepIndex < len(self._separators):
                    morph+=self._separators[sepIndex]
                sepIndex+=1
        
            morphs.append(morph)
            
        return morphs
    
          
    @staticmethod  
    def getWordsOfType(wordType:WordTypeMark, analyzedTokens:List[namegenPack.Grammar.AnalyzedToken]):   
        """
        Na základě slovům odpovídajících analyzovaných tokenů ve jméně vybere slova daného typu.
        
        :param wordType: Druh slova na základě, kterého vybírá
        :type wordType: WordTypeMark
        :param analyzedTokens: Analyzované tokeny, získané ze syntaktické analýzy tohoto jména.
        :type analyzedTokens: List[namegenPack.Grammar.AnalyzedToken]
        :return: List s vybranými slovy a příslušnými značko pravidly.
        :rtype: List[Touple[Word, Set[MARule]]]
        """
        selection=[]
        for aToken in analyzedTokens:
            if aToken.matchingTerminal.getAttribute(namegenPack.Grammar.Terminal.Attribute.Type.TYPE).value==wordType:
                
                #získáme příslušná pravidla
                cateFilters=aToken.morphCategories    #podmínky na původní slovo

                rules={r for r, w in aToken.token.word.morphs(cateFilters, cateFilters) if str(w)==str(aToken.token.word)}
                selection.append((aToken.token.word,{r for r in rules}))
                
        
        return selection
        
        
    @property
    def type(self):
        """Getter pro druh jména."""
        return self._type
        
class NameReader(object):
    """
    Třída pro čtení vstupního souboru a převedení vstupu do posloupnosti objektů Name.

    """
    
    def __init__(self, inputFile):
        """
        Konstruktor 
        
        :param inputFile: Cesta ke vstupnímu souboru se jmény.
        :type inputFile: string

        """
        self.names=[]
        self._errorCnt=0 #počet chybných nenačtených jmen
        with open(inputFile, "r") as rInput:
            for line in rInput:
                line=line.strip()
                parts = line.split("\t")
                if len(parts) != 2:
                    if len(parts) > 2:
                        #nevalidní formát vstupu
                        print(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_INVALID_NAME)+"\t"+line, file=sys.stderr)
                        self._errorCnt+=1
                        continue
                        
                    #Necháme provést odhad typu slova.
                    #Dle zadání má být automaticky předpokládána osoba, kde se může stát, že typ není uveden.
                    #Řešeno v Name
                    parts.append(None)
                    
                #provedeme analýzu jména a uložíme je 
                try:
                    self.names.append(Name(parts[0], parts[1]))
                except Name.NameCouldntCreateException as e:
                    #problém při vytváření jména
                    print(e.message, file=sys.stderr)
                    self._errorCnt+=1
                
    @property
    def errorCnt(self):
        """
        Počet chybných nenačtených jmen
        """
        return self._errorCnt
    
    def allWords(self, stringRep=False):
        """
        Slova vyskytující se ve všech jménech.
        
        :param stringRep: True v str reprezentaci. False jako Word objekt.
        :type stringRep: bool
        :return Množina všech slov ve jménech.
        :rtype: Set[Word] | Set[str]
        """
        words=set()
        if stringRep:
            for name in self.names:
                for w in name:
                    words.add(str(w))
        else:
            for name in self.names:
                for w in name:
                    words.add(w)
        
        return words
    
    def __iter__(self):
        """
        Iterace přes všechna jména.
        """
        
        for name in self.names:
            yield name
            