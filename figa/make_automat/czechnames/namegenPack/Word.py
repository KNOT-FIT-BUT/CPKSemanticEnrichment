"""
Created on 17. 6. 2018
Modul pro práci se slovem.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""
from enum import Enum
from namegenPack import Errors
from namegenPack.morpho.MorphoAnalyzer import MorphoAnalyzer,MorphoAnalyze, MorphCategory
from namegenPack.morpho.MorphCategories import StylisticFlag
from typing import Set

class WordTypeMark(Enum):
    """
    Značka druhu slova ve jméně. Vyskytuje se jako atribut v gramatice.
    """
    GIVEN_NAME="G"                  #Křestní jméno. Příklad: Petra
    SURNAME="S"                     #Příjmení. Příklad: Novák
    LOCATION="L"                    #Lokace. Příklad: Brno
    ROMAN_NUMBER="R"                #Římská číslice. Příklad: IV
    PREPOSITION="7"                 #Předložka.
    CONJUCTION="8"                  #Spojka.
    DEGREE_TITLE="T"                #Titul. Příklad: prof.
    INITIAL_ABBREVIATION="I"        #Iniciálová zkratka. Příklad H. ve jméně John H. White
    UNKNOWN="U"                     #Neznámé

    def __str__(self):
        return self.value

class Word(object):
    """
    Reprezentace slova.
    """
    
    class WordException(Errors.ExceptionMessageCode):
        """
        Vyjímka se zprávou a kódem a slovem, který ji vyvolal.
        """
        def __init__(self, word, code, message=None):
            """
            Konstruktor pro vyjímku se zprávou a kódem.
            
            :param word: Pro toto slovo se generuje tato vyjímka
            :type word: Word
            :param code: Kód chyby. Pokud je uveden pouze kód, pak se zpráva automaticky na základě něj doplní.
            :param message: zpráva popisující chybu
            """
            self.word=word
            
            super().__init__(code, message)
    
    class WordCouldntGetInfoException(WordException):
        """
        Vyjímka symbolizující, že se nepovedlo získat mluvnické kategorie ke slovu.
        """
        pass
    
    class WordNoMorphsException(WordException):
        """
        Vyjímka symbolizující, že se nepovedlo získat ani jeden tvar slova.
        """
        pass
    
    class WordMissingCaseException(WordException):
        """
        Vyjímka symbolizující, že se nepovedlo získat některý pád.
        """
        pass
    
    ma=None
    """Morfologický analyzátor."""
    
    def __init__(self, w):
        """
        Kontruktor slova.
        
        :param w: Řetězcová reprezentace slova.
        :type w: String
        """
        self._w=w
        
    @classmethod
    def setMorphoAnalyzer(cls, ma:MorphoAnalyzer):
        """
        Přiřazení morfologického analyzátoru.
        
        :param ma: Morfologický analyzátor, který se bude používat k získávání informací o slově.
        :type ma: MorphoAnalyzer
        """
        
        cls.ma=ma
        
    
    @property
    def info(self) -> MorphoAnalyze:
        """
        Vrací informace o slově (morfologické kategorie a tvary). V podobě morfologické analýzy.

        :returns: Morfologická analýza slova.
        :rtype: MorphoAnalyze
        :raise WordCouldntGetInfoException: Problém při analýze slova.
        """
        if self.ma is None:
            #nemohu provést morfologickou analýzu bez analyzátoru
            raise self.WordCouldntGetInfoException(self, Errors.ErrorMessenger.CODE_WORD_ANALYZE,
                                                       Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_WORD_ANALYZE)+"\t"+self._w)
        
        #získání analýzy
        a=self.ma.analyze(self._w)
        if a is None:
            raise self.WordCouldntGetInfoException(self, Errors.ErrorMessenger.CODE_WORD_ANALYZE,
                                                       Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_WORD_ANALYZE)+"\t"+self._w)
                
        return a
    
    
    def morphs(self, categories: Set[MorphCategory], wordFilter: Set[MorphCategory] =set()):
        """
        Vygeneruje tvary slova s ohledem na poskytnuté kategorie. Vybere jen tvary jenž odpovídají daným kategoriím.
        Příklad: V atributu categories jsou: podstatné jméno, rodu mužský, jednotné číslo
            Potom vygeneruje tvary, které jsou: podstatné jméno rodu mužského v jednotném čísle.
        
        :param categories: Kategorie, které musí mít generované tvary.
        :type categories: Set[MorphCategory]
        :param wordFilter: Podmínky na původní slovo. Jelikož analýza nám může říci několik variant, tak tímto filtrem můžeme
            spřesnit odhad.
            Chceme-li získat všechny tvary, které se váží na případy, kdy se předpokládá, že původní slovo mělo
            danou morfologickou kategorii, tak použijeme tento filtr.
                Příklad: Pokud je vložen 1. pád. Budou brány v úvahu jen tvary, které patří ke skupině tvarů vázajících se na případ
                že původní slovo je v 1. pádu.
        :type wordFilter: Set[MorphCategory]
        :return: Vrací možné tvary i s jejich pravidly.
                Set[Tuple[MARule,str]]    str je tvar
        :rtype: Set[Tuple[MARule,str]]
        :raise WordNoMorphsException: pokud se nepodaří získat tvary.
        """
        #na základě filtrů získáme všechny možné tvary
        #nechceme hovorové tvary ->StylisticFlag.COLLOQUIALLY
                
        tmp=self.info.getMorphs(categories, {StylisticFlag.COLLOQUIALLY}, wordFilter)
        if tmp is None or len(tmp)<1:

            raise self.WordNoMorphsException(self, Errors.ErrorMessenger.CODE_WORD_NO_MORPHS_GENERATED,
                Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_WORD_NO_MORPHS_GENERATED)+"\t"+self._w)
        return tmp
    
    def __repr__(self):
        return self._w
    
    def __str__(self):
        return self._w
    
    def __getitem__(self, key):
        return self._w[key]
    
    def __len__(self): 
        return len(self._w)
