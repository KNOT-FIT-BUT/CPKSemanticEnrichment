"""
Created on 28. 7. 2018

Tento modul obsahuje výčet morfologických kategorií a jejich hodnot.
Také obsahuje metody pro převod mezi formáty (lntrf).

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""

from enum import Enum
from namegenPack import Errors


class MorphCategoryException(Errors.ExceptionMessageCode):
    """
    Bázová vyjímka pro morfologické kategorie.
    """

class MorphCategoryInvalidException(MorphCategoryException):
    """
    Nevalidní morfologická kategorie. Používá se při vytváření enumu z dané hodnoty.
    """
    def __init__(self, value):
        """
        Konstruktor pro vyjímku nevalidní kategorie.

        :param value: Hodnota způsobující potíže.
        :type value: str
        """
        self.code = Errors.ErrorMessenger.CODE_MORPH_ENUM_INVALID_CATEGORY
        self.message = Errors.ErrorMessenger.getMessage(self.code).format(value)
        
class MorphCategoryInvalidValueException(MorphCategoryException):
    """
    Nevalidní hodnota morfologické kategorie. Používá se při vytváření enumu z dané hodnoty.
    """
    def __init__(self, category, value):
        """
        Konstruktor pro vyjímku nevalidní hodnoty.
        
        :param category: Označení kategorie.
        :type category: str
        :param value: Hodnota způsobující potíže.
        :type value: str
        """
        self.code = Errors.ErrorMessenger.CODE_MORPH_ENUM_INVALID_VALUE
        self.message = Errors.ErrorMessenger.getMessage(self.code).format(category, value)

class MorphCategory(Enum):
    """
    Bázová třída pro morfologickou kategorii.
    """
    
    @staticmethod
    def category():
        """
        Morfologická kategorie.
        
        :return: Morfoligická kategorie jejiž hodnoty jsou reprezentovány tímto enumem.
        :rtype: MorphCategories
        """
        raise NotImplementedError

    @property
    def lntrf(self):
        """
        V lntrf formátu i s označením kategorie.
        Příklad:    k1
        """
        return self.category().lntrf+self.lntrfValue
    
    @property
    def lntrfValue(self):
        """
        V lntrf formátu, pouze hodnota.
        """
        return self._mappingLntrf[self]
    
        
    @classmethod    
    def fromLntrf(cls, val):
        """
        Vytvoří z lntrf formátu.
        Použije k převodu reverzní mapování z _mappingLntrf.

        :param val: Vstupní hodnota v lntrf formátu.
        :type val: str
        :return: Odpovídající mluvnickou kategorii.
        :rtype: MorphCategory
        :raise MorphCategoryInvalidValueException: On invalid value.
        """

        try:
            return cls._mappingLntrfInverse[val]
        except KeyError:
            raise MorphCategoryInvalidValueException(cls.category().lntrf, val)
        
MorphCategory._mappingLntrf={e:str(e.value) for e in MorphCategory}
"""Zobrazení sloužící pro konverzi s LNTRF."""
MorphCategory._mappingLntrfInverse={v: k for k, v in MorphCategory._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""

        
class MorphCategories(Enum):
    """
    Morfologické kategorie.
    """
    
    POS=0
    """slovní druh"""
    
    GENDER=1
    """rod"""
    
    NUMBER=2
    """číslo"""
    
    CASE=3
    """pád"""
    
    NEGATION=4
    """negace"""
    
    DEGREE_OF_COMPARISON=5
    """stupeň"""
    
    PERSON=6
    """osoba"""
    
    STYLISTIC_FLAG=7
    """stylistický příznak"""
    

    @property
    def lntrf(self):
        """
        V lntrf formátu.
        """
        return self._lntrfMap[self]
        
    @classmethod    
    def fromLntrf(cls, val):
        """
        Vytvoří z lntrf formátu.

        :param val: Vstupní hodnota v lntrf formátu.
        :type val: str
        :return: Odpovídající mluvnickou kategorii.
        :rtype: MorphCategories
        :raise MorphCategoryInvalidException: On invalid value.
        """
        try:
            return cls._lntrfMapInverse[val]
        except KeyError:
            raise MorphCategoryInvalidException(val)
        
    def createCategoryFromLntrf(self, val) -> MorphCategory:
        """
        Vytvoří MorphCategory z předané validní hodnoty aktuální morfologické kategorie.
        Tedy pokud je MorphCategories typu POS, pak očekává lntrf hodnoty pro POS.
        Příklad:
        1 -> POS.NOUN
        
        :param val: Lntrf hodnota, ze které bude vytvořeno MorphCategory.
        :type val: str
        :return: Odpovídající mluvnickou kategorii.
        :rtype: MorphCategory
        :raise MorphCategoryInvalidValueException: On invalid value.
        """
 
        return self._lntrfCatMap[self](val)

MorphCategories._lntrfMap={
            MorphCategories.POS:"k",
            MorphCategories.GENDER:"g",
            MorphCategories.NUMBER:"n",
            MorphCategories.CASE:"c",
            MorphCategories.NEGATION:"e",
            MorphCategories.DEGREE_OF_COMPARISON:"d",
            MorphCategories.PERSON:"p",
            MorphCategories.STYLISTIC_FLAG:"w"
            }
"""Zobrazení pro lntrf konverzi."""

MorphCategories._lntrfMapInverse={v: k for k, v in MorphCategories._lntrfMap.items()}
"""Inverzní zobrazení k _lntrfMap."""


class POS(MorphCategory):
    """
    Slovní druhy.
    """
    NOUN=1
    """podstatné jméno"""
    
    ADJECTIVE=2
    """přídavné jméno"""
    
    PRONOUN=3
    """zájméno"""
    
    NUMERAL=4
    """číslovka"""
    
    VERB=5
    """sloveso"""

    ADVERB=6
    """příslovce"""

    PREPOSITION=7
    """předložka"""
    
    PREPOSITION_M="m"
    """Speciální druh předložky, za kterou se v češtině slova ve jméně ohýbají. (da, von ...)"""

    CONJUNCTION=8
    """spojka"""
    
    PARTICLE=9
    """částice"""

    INTERJECTION=10
    """citoslovce"""
    
    ABBREVIATION="a"
    """zkratka"""
    
    @staticmethod
    def category():
        return MorphCategories.POS

POS._mappingLntrf={e:str(e.value) for e in POS}
"""Zobrazení sloužící pro konverzi s LNTRF."""        
POS._mappingLntrfInverse={v: k for k, v in POS._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""

class Gender(MorphCategory):
    """
    Rod
    """
    
    MASCULINE_ANIMATE="M"
    """mužský životný"""
    
    MASCULINE_INANIMATE="I"
    """mužský neživotný"""
    
    NEUTER="N"
    """střední"""
    
    FEMINE="F"
    """ženský"""
    
    FAMILY="R"
    """rodina (příjmení) [asi něco navíc v libma?]"""
    
    
    @staticmethod
    def category():
        return MorphCategories.GENDER
    
Gender._mappingLntrf={e:str(e.value) for e in Gender}
"""Zobrazení sloužící pro konverzi s LNTRF."""   
Gender._mappingLntrfInverse={v: k for k, v in Gender._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""

class Number(MorphCategory):
    """
    Číslo
    """
    
    SINGULAR="S"
    """jednotné"""
    
    PLURAL="P"
    """množné"""
    
    DUAL="D"
    """duál"""
    
    R="R"
    """hromadné označení členů rodiny (Novákovi)"""
    
    @staticmethod
    def category():
        return MorphCategories.NUMBER
    
Number._mappingLntrf={e:str(e.value) for e in Number}
"""Zobrazení sloužící pro konverzi s LNTRF."""  
Number._mappingLntrfInverse={v: k for k, v in Number._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""
            
class Case(MorphCategory):
    """
    Pád
    """
    
    NOMINATIVE=1
    """1. pád: Nominativ s pádovými otázkami (kdo, co)"""
    
    GENITIVE=2
    """2. pád: Genitiv (koho, čeho)"""
    
    DATIVE=3
    """3. pád: Dativ (komu, čemu)"""
    
    ACCUSATIVE=4
    """4. pád: Akuzativ (koho, co)"""
    
    VOCATIVE=5
    """5. pád: Vokativ (oslovujeme, voláme)"""
    
    LOCATIVE=6
    """6. pád: Lokál (kom, čem)"""
    
    INSTRUMENTAL=7
    """7. pád: Instrumentál (kým, čím)"""
    
    
    @staticmethod
    def category():
        return MorphCategories.CASE
Case._mappingLntrf={e:str(e.value) for e in Case}
"""Zobrazení sloužící pro konverzi s LNTRF."""  
Case._mappingLntrfInverse={v: k for k, v in Case._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""
  
class Negation(MorphCategory):
    """
    Negace
    """
    
    AFFIRMATIVE="A"
    """afirmace"""
    
    NEGATED="N"
    """negace"""
   
    @staticmethod
    def category():
        return MorphCategories.NEGATION
Negation._mappingLntrf={e:str(e.value) for e in Negation}
"""Zobrazení sloužící pro konverzi s LNTRF.""" 
Negation._mappingLntrfInverse={v: k for k, v in Negation._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""

class DegreeOfComparison(MorphCategory):
    """
    Stupeň
    """
    
    POSITIVE=1
    """pozitiv (příklad: velký)"""
    
    COMPARATIVE=2
    """komparativ (příklad: větší)"""
    
    SUPERLATIVE=3
    """superlativ (příklad: největší)"""
   
    
    @staticmethod
    def category():
        return MorphCategories.DEGREE_OF_COMPARISON
DegreeOfComparison._mappingLntrf={e:str(e.value) for e in DegreeOfComparison}
"""Zobrazení sloužící pro konverzi s LNTRF."""     
DegreeOfComparison._mappingLntrfInverse={v: k for k, v in DegreeOfComparison._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""

class Person(MorphCategory):
    """
    Osoba
    """
    
    FIRST=1
    """první osoba"""
    
    SECOND=2
    """druhá osoba"""
    
    THIRD=3
    """třetí osoba"""
    
    ANY="X"
    """první nebo druhá nebo třetí"""

    @staticmethod
    def category():
        return MorphCategories.PERSON
Person._mappingLntrf={e:str(e.value) for e in Person}
"""Zobrazení sloužící pro konverzi s LNTRF."""
Person._mappingLntrfInverse={v: k for k, v in Person._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""

class StylisticFlag(MorphCategory):
    """
    Stylistický příznak.
    """
    ARCHAISM="A"
    """archaismus"""
    
    POETIC="B"
    """básnicky"""
    
    ONLY_IN_CORPUSCLES="C"
    """pouze v korpusech"""
    
    EXPRESSIVELY="E"
    """expresivně"""
    
    COLLOQUIALLY="H"
    """hovorově"""
    
    BOOK="K"
    """knižně"""
    
    REGIONALLY="O"
    """oblastně"""
    
    RATHER="R"
    """řidčeji"""
    
    OBSOLETE="Z"
    """zastarale"""

    @staticmethod
    def category():
        return MorphCategories.STYLISTIC_FLAG
    
StylisticFlag._mappingLntrf={e:str(e.value) for e in StylisticFlag}
"""Zobrazení sloužící pro konverzi s LNTRF."""    
StylisticFlag._mappingLntrfInverse={v: k for k, v in StylisticFlag._mappingLntrf.items()}
"""Inverzní zobrazení k _mappingLntrf."""   

MorphCategories._lntrfCatMap={
            MorphCategories.POS: POS.fromLntrf,
            MorphCategories.GENDER: Gender.fromLntrf,
            MorphCategories.NUMBER: Number.fromLntrf,
            MorphCategories.CASE: Case.fromLntrf,
            MorphCategories.NEGATION: Negation.fromLntrf,
            MorphCategories.DEGREE_OF_COMPARISON: DegreeOfComparison.fromLntrf,
            MorphCategories.PERSON: Person.fromLntrf,
            MorphCategories.STYLISTIC_FLAG: StylisticFlag.fromLntrf
            }
"""Zobrazení pro lntrf konverzi. Pro tvorbu MorphCategory z lntrf hodnoty s ohledem na aktuální použitou hodnotu z MorphCategories."""