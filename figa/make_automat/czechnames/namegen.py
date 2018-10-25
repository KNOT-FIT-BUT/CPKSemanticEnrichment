#!/usr/bin/env python3
# encoding: utf-8
"""
namegen -- Generátor tvarů jmen.

namegen je program pro generování tvarů jmen osob a lokací.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""

import sys
import os
from argparse import ArgumentParser
import traceback
from namegenPack import Errors
import logging
import namegenPack.Grammar
import namegenPack.morpho.MorphoAnalyzer
import namegenPack.morpho.MorphCategories
import configparser

from namegenPack.Name import *

outputFile = sys.stdout



class ConfigManagerInvalidException(Errors.ExceptionMessageCode):
    """
    Nevalidní konfigurace
    """
    pass

class ConfigManager(object):
    """
    Tato třída slouží pro načítání konfigurace z konfiguračního souboru.
    """

    sectionDataFiles="DATA_FILES"
    sectionMorphoAnalyzer="MA"
    
    
    
    
    def __init__(self):
        """
        Inicializace config manažéru.
        """
        
        self.configParser = configparser.ConfigParser()
    
        
    def read(self, filesPaths):
        """
        Přečte hodnoty z konfiguračních souborů. Také je validuje a převede do jejich datových typů.
        
        :param filesPaths: list s cestami ke konfiguračním souborům.
        :returns: Konfigurace.
        :raise ConfigManagerInvalidException: Pokud je konfigurační soubor nevalidní.
        """
        try:
            self.configParser.read(filesPaths)
        except configparser.ParsingError as e:
            raise ConfigManagerInvalidException(Errors.ErrorMessenger.CODE_INVALID_CONFIG, "Nevalidní konfigurační soubor: "+str(e))
                                       
        
        return self.__transformVals()
        
        
    def __transformVals(self):
        """
        Převede hodnoty a validuje je.
        
        :returns: dict -- ve formátu jméno sekce jako klíč a k němu dict s hodnotami.
        :raise ConfigManagerInvalidException: Pokud je konfigurační soubor nevalidní.
        """
        result={}

        result[self.sectionDataFiles]=self.__transformDataFiles()
        result[self.sectionMorphoAnalyzer]=self.__transformMorphoAnalyzer()
        
        return result
    
    def __transformMorphoAnalyzer(self):
        """
        Převede hodnoty pro MA a validuje je.
        
        :returns: dict -- ve formátu jméno prametru jako klíč a k němu hodnota parametru
        :raise ConfigManagerInvalidException: Pokud je konfigurační soubor nevalidní.
        """

        result={
            "PATH_TO":self.configParser[self.sectionMorphoAnalyzer]["PATH_TO"]
            }

        return result
    
    def __transformDataFiles(self):
        """
        Převede hodnoty pro DATA_FILES a validuje je.
        
        :returns: dict -- ve formátu jméno prametru jako klíč a k němu hodnota parametru
        :raise ConfigManagerInvalidException: Pokud je konfigurační soubor nevalidní.
        """

        result={
            "GRAMMAR_MALE":None,
            "GRAMMAR_FEMALE":None,
            "GRAMMAR_LOCATIONS":None
            }
        self.__loadPathArguments(self.configParser[self.sectionDataFiles], result)

        return result
    
    def __loadPathArguments(self, parConf, result):
        """
        Načtení argumentů obsahujícíh cesty.

        :param parConf: Sekce konfiguračního souboru v němž hledáme naše hodnoty.
        :type parConf: dict
        :param result: Zde se budou načítat cesty. Názvy klíčů musí odpovídat názvům argumentů.
        :type result: dict
        :raise ConfigManagerInvalidException: Pokud je konfigurační soubor nevalidní.
        """
        
        for k in result.keys():
            if parConf[k]: 
                if parConf[k][0]!="/":
                    result[k]=os.path.dirname(os.path.realpath(__file__))+"/"+parConf[k]
                else:
                    result[k]=parConf[k]
            else:
                raise ConfigManagerInvalidException(Errors.ErrorMessenger.CODE_INVALID_CONFIG, "Nevalidní konfigurační soubor. Chybí "+self.sectionDataFiles+" -> "+k)


class ArgumentParserError(Exception): pass
class ExceptionsArgumentParser(ArgumentParser):
    def error(self, message):
        raise ArgumentParserError(message)
    
class ArgumentsManager(object):
    """
    Arguments manager pro namegen.
    """
    
    @classmethod
    def parseArgs(cls):
        """
        Parsování argumentů.
        
        :param cls: arguments class
        :returns: Parsované argumenty.
        """
        
        parser = ExceptionsArgumentParser(description="namegen je program pro generování tvarů jmen osob a lokací.")
        
        parser.add_argument("-o", "--output", help="Výstupní soubor.", type=str, required=True)
        parser.add_argument("-ew", "--error-words", help="Cesta k souboru, kde budou uložena slova, pro která se nepovedlo získat informace (tvary, slovní druh...). Výsledek je v lntrf formátu s tím, že provádí odhad značko-pravidel pro ženská a mužská jména.", type=str)
        parser.add_argument("-gn", "--given-names", help="Cesta k souboru, kde budou uložena slova označená jako křestní. Výsledek je v lntrf formátu.", type=str)
        parser.add_argument("-sn", "--surnames", help="Cesta k souboru, kde budou uložena slova označená jako příjmení. Výsledek je v lntrf formátu.", type=str)
        parser.add_argument("-l", "--locations", help="Cesta k souboru, kde budou uložena slova označená jako lokace. Výsledek je v lntrf formátu.", type=str)
        parser.add_argument('input', nargs=1, help='Vstupní soubor se jmény.')

        try:
            parsed=parser.parse_args()
            
        except ArgumentParserError as e:
            parser.print_help()
            print("\n"+str(e), file=sys.stderr)
            Errors.ErrorMessenger.echoError(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_INVALID_ARGUMENTS), Errors.ErrorMessenger.CODE_INVALID_ARGUMENTS)

        return parsed
 
def main():
    """
    Vstupní bod programu.
    """
    try:
        
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        #zpracování argumentů
        args=ArgumentsManager.parseArgs()
        
        #načtení konfigurace
        configManager=ConfigManager()
        configAll=configManager.read(os.path.dirname(os.path.realpath(__file__))+'/namegen_config.ini')
        
        
        logging.info("načtení gramatik")
        #načtení gramatik
        try:
            grammarMale=namegenPack.Grammar.Grammar(configAll[configManager.sectionDataFiles]["GRAMMAR_MALE"])
        except Errors.ExceptionMessageCode as e:
            raise Errors.ExceptionMessageCode(e.code, configAll[configManager.sectionDataFiles]["GRAMMAR_MALE"]+": "+e.message)
        
        try:
            grammarFemale=namegenPack.Grammar.Grammar(configAll[configManager.sectionDataFiles]["GRAMMAR_FEMALE"])
        except Errors.ExceptionMessageCode as e:
            raise Errors.ExceptionMessageCode(e.code, configAll[configManager.sectionDataFiles]["GRAMMAR_FEMALE"]+": "+e.message)
        
        try:
            grammarLocations=namegenPack.Grammar.Grammar(configAll[configManager.sectionDataFiles]["GRAMMAR_LOCATIONS"])
        except Errors.ExceptionMessageCode as e:
            raise Errors.ExceptionMessageCode(e.code, configAll[configManager.sectionDataFiles]["GRAMMAR_LOCATIONS"]+": "+e.message)
        logging.info("\thotovo")
        logging.info("čtení jmen")
        #načtení jmen pro zpracování
        namesR=NameReader(args.input[0])
        logging.info("\thotovo")
        logging.info("analýza slov")
        #přiřazení morfologického analyzátoru

        Word.setMorphoAnalyzer(
            namegenPack.morpho.MorphoAnalyzer.MorphoAnalyzerLibma(
                configAll[configManager.sectionMorphoAnalyzer]["PATH_TO"], 
                namesR.allWords(True)))
        
        logging.info("\thotovo")
        logging.info("\tgenerování tvarů")
        
        #čítače chyb
        errorsOthersCnt=0   
        errorsGrammerCnt=0  #není v gramatice
        errorsUnknownNameType=0  #není v gramatice
        errorsWordInfoCnt=0   #nemůže vygenrovat tvary, zjistit POS...
        errorsDuplicity=0   #více stejných jmen (včetně typu)

        errorWordsShouldSave=True if args.error_words is not None else False
        
        #slova ke, kterým nemůže vygenerovat tvary, zjistit POS... 
        #Jedná se o trojice ( druh názvu (mužský, ženský, lokace),druhu slova ve jméně, dané slovo)
        errorWords=set()    
        
        givenNamesF,surnamesF,locationsF=None,None,None
        

        #slouží pro výpis křestních jmen, příjmení atd.
        wordRules={}
        writeWordsOfTypeTo={}
        if args.given_names is not None:
            #uživatel chce vypsat křestní jména do souboru
            wordRules[WordTypeMark.GIVEN_NAME]={}
            writeWordsOfTypeTo[WordTypeMark.GIVEN_NAME]=args.given_names
            
        if args.surnames is not None:
            #uživatel chce příjmení jména do souboru
            wordRules[WordTypeMark.SURNAME]={}
            writeWordsOfTypeTo[WordTypeMark.SURNAME]=args.surnames
            
        if args.locations is not None:
            #uživatel chce vypsat slova odpovídají lokacím do souboru
            wordRules[WordTypeMark.LOCATION]={}
            writeWordsOfTypeTo[WordTypeMark.LOCATION]=args.locations
            
        
         
        cnt=0   #projito slov
        
        #nastaveni logování
        duplicityCheck=set()    #zde se budou ukládat jména pro zamezení duplicit
        
        grammarsForTypeGuesser={Name.Type.FEMALE: grammarFemale,Name.Type.MALE:grammarMale}
        
        tokenTypesThatNeedsMA={namegenPack.Grammar.Token.Type.ANALYZE, namegenPack.Grammar.Token.Type.ROMAN_NUMBER}
        
        
        
        with open(args.output, "w") as outF:
            
            for name in namesR:
                try:
                    tokens=namegenPack.Grammar.Lex.getTokens(name)
                    wNoInfo=set()
                    for t in tokens:
                        #zkontrolujeme zda-li máme pro všechny tokeny,které to potřebují, dostupnou analýzu.
                        if t.type in tokenTypesThatNeedsMA:
                            try:
                                _=t.word.info
                            except Word.WordCouldntGetInfoException:
                                wNoInfo.add(t.word)
                    if len(wNoInfo)>0:
                        wordsMarks=name.simpleWordsTypesGuess(tokens)
                        print(str(name)+"\t"+Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_WORD_ANALYZE)+"\t"+(", ".join(str(w)+"#"+str(wordsMarks[name.words.index(w)]) for w in wNoInfo)), file=sys.stderr)
                        errorsWordInfoCnt+=1

                        if errorWordsShouldSave:
                            
                            for w in wNoInfo:
                                #přidáme informaci o druhu slova ve jméně a druh jména
                                errorWords.add((name.type, wordsMarks[name.words.index(w)], w))
                        #nemá cenu pokračovat, jdeme na další
                        continue
                            
                        
                    #zpochybnění odhad typu jména
                    #protože guess type používá také gramatky
                    #tak si případný výsledek uložím, abychom nemuseli dělat 2x stejnou práci
                    aTokens=name.guessType(grammarsForTypeGuesser, tokens)
                    if name.type is None:
                        #Nemáme informaci o druhu jména, jdeme dál.
                        print(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_NAME_WITHOUT_TYPE).format(str(name)), file=sys.stderr)
                        errorsUnknownNameType+=1
                        continue
                    #Vybrání a zpracování gramatiky na základě druhu jména.
                    #získáme aplikovatelná pravidla, ale hlavně analyzované tokeny, které mají v sobě informaci,
                    #zda-li se má dané slovo ohýbat, či nikoliv a další
                    
                    if name in duplicityCheck:
                        #již jsme jednou generovali
                        errorsDuplicity+=1
                        continue
                    
                    duplicityCheck.add(name)
                    
                    
                    if aTokens is None: #Nedostali jsme aTokeny při určování druhu slova?
                        
                        #rules a aTokens může obsahovat více než jednu možnou derivaci
                        if name.type==Name.Type.LOCATION:
                            _, aTokens=grammarLocations.analyse(tokens)
                        elif name.type==Name.Type.MALE:
                            _, aTokens=grammarMale.analyse(tokens)
                        elif name.type==Name.Type.FEMALE:
                            _, aTokens=grammarFemale.analyse(tokens)
                        else:
                            #je cosi prohnilého ve stavu tohoto programu
                            raise Errors.ExceptionMessageCode(Errors.ErrorMessenger.CODE_ALL_VALUES_NOT_COVERED)

                    completedMorphs=set()    #pro odstranění dualit používáme set
                    noMorphsWords=set()
                    missingCaseWords=set()
                    for aT in aTokens:
                        try:
                            morphs=name.genMorphs(aT)
                            completedMorphs.add(str(name)+"\t"+str(name.type)+"\t"+("|".join(morphs)))
                        except Word.WordNoMorphsException as e:
                            #chyba při generování tvarů slova
                            #odchytáváme již zde, jeikož pro jedno slovo může být více alternativ
                            for x in aT:
                                #hledáme AnalyzedToken pro naše problémové slovo, abychom mohli ke slovu
                                #přidat i odhadnutý druh slova ve jméně (křestní, příjmení, ...)
                                if x.token.word==e.word:
                                    noMorphsWords.add((x.matchingTerminal,e.word))
                                    break
                        except Word.WordMissingCaseException as e:
                            #nepodařilo se získat některý pád slova
                            #odchytáváme již zde, jeikož pro jedno slovo může být více alternativ
                            for x in aT:
                                #hledáme AnalyzedToken pro naše problémové slovo, abychom mohli ke slovu
                                #přidat i odhadnutý druh slova ve jméně (křestní, příjmení, ...)
                                if x.token.word==e.word:
                                    missingCaseWords.add((x.matchingTerminal.getAttribute(namegenPack.Grammar.Terminal.Attribute.Type.TYPE).value ,e))
                                    break
                        
                    if len(noMorphsWords)>0 or len(missingCaseWords)>0:
                        #chyba při generování tvarů jména
                        #nepodařilo se vygenerovat ani jeden
                        errorsWordInfoCnt+=1
                        if len(noMorphsWords)>0:
                            print(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_NAME_NO_MORPHS_GENERATED).format(str(name),", ".join(str(w)+" "+str(m) for m,w in noMorphsWords)), file=sys.stderr)
                            if errorWordsShouldSave:
                                for m, w in noMorphsWords:
                                    errorWords.add((name.type,m.getAttribute(namegenPack.Grammar.Terminal.Attribute.Type.TYPE).value, w))
                                    
                        for m, e in missingCaseWords:
                            print(str(name)+"\t"+e.message, file=sys.stderr)
                            if errorWordsShouldSave:
                                errorWords.add((name.type, m, e.word))
                        
                    #vytiskneme
                    for m in completedMorphs:
                        print(m, file=outF)
                        
                    
                    #zjistíme, zda-li uživatel nechce vypsat nějaké typy jmen do souborů
    
                    for wordType in wordRules:
                        #chceme získat včechny slova daného druhu a k nim příslušná pravidla

                        #sjednotíme všechny derivace
                        for aT in aTokens:
                            for w, rules in Name.getWordsOfType(wordType, aT):
                                try:
                                    wordRules[wordType][str(w)]=wordRules[wordType][str(w)]|rules
                                except KeyError:
                                    wordRules[wordType][str(w)]=rules
  
                        
                except (Word.WordException) as e:
                    print(str(name)+"\t"+e.message, file=sys.stderr)
                    errorsWordInfoCnt+=1
    
                    if errorWordsShouldSave:
                        wordsMarks=name.simpleWordsTypesGuess(tokens)
                        for i, w in enumerate(name.words):
                            if w == e.word:
                                errorWords.add((name.type, wordsMarks[i], e.word))
                                break
                        
                except namegenPack.Grammar.Grammar.NotInLanguage:
                    errorsGrammerCnt+=1
                    print(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_NAME_IS_NOT_IN_LANGUAGE_GENERATED_WITH_GRAMMAR)+\
                              "\t"+str(name)+"\t"+str(name.type), file=sys.stderr)

                except Errors.ExceptionMessageCode as e:
                    #chyba při zpracování slova
                    errorsOthersCnt+=1
                    print(str(name)+"\t"+e.message, file=sys.stderr)
                    
                cnt+=1
                if cnt%100==0:
                    logging.info("Projito slov: "+str(cnt))
                    
        logging.info("\thotovo")
        #vypíšeme druhy slov, pokud to uživatel chce
        
        for wordType, pathToWrite in writeWordsOfTypeTo.items():
            logging.info("\tVýpis slov typu: "+str(wordType))
            with open(pathToWrite, "w") as fileW:
                for w, rules in wordRules[wordType].items():
                    print(str(w)+"\t"+"j"+str(wordType)+"\t"+(" ".join(sorted(r.lntrf+"::" for r in rules))), file=fileW)
            logging.info("\thotovo")
            
                
        
        print("-------------------------")
        print("Celkem jmen: "+ str(namesR.errorCnt+len(namesR.names)))
        print("\tNenačtených jmen: "+ str(namesR.errorCnt))
        print("\tDuplicitních jmen: "+ str(errorsDuplicity))
        print("\tNačtených jmen/názvů celkem: ", len(namesR.names))
        print("\tNeznámý druh jména: ", errorsUnknownNameType)
        print("\tNepokryto gramatikou: ", errorsGrammerCnt)
        print("\tNepodařilo se získat informace o slově (tvary, slovní druh...): ", errorsWordInfoCnt)
        
        
        if errorWordsShouldSave:
            #save words with errors into a file
            with open(args.error_words, "w") as errWFile:
                for nT, m, w in errorWords:#druh názvu (mužský, ženský, lokace),označení typu slova ve jméně(jméno, příjmení), společně se jménem
                    #u ženských a mužských jmen přidáme odhad lntrf značky
                    if m in {WordTypeMark.GIVEN_NAME, WordTypeMark.SURNAME}:
                        if nT == Name.Type.FEMALE:
                            print(str(w)+"\t"+"j"+str(m)+"\tk1gFnSc1::", file=errWFile)
                            continue
                        if nT == Name.Type.MALE:
                            print(str(w)+"\t"+"j"+str(m)+"\tk1gMnSc1::", file=errWFile)
                            continue
                        
                    print(str(w)+"\t"+"j"+str(m), file=errWFile)
  

    except Errors.ExceptionMessageCode as e:
        Errors.ErrorMessenger.echoError(e.message, e.code)
    except IOError as e:
        Errors.ErrorMessenger.echoError(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_COULDNT_WORK_WITH_FILE)+"\n"+str(e), 
                                 Errors.ErrorMessenger.CODE_COULDNT_WORK_WITH_FILE)

    except Exception as e: 
        print("--------------------", file=sys.stderr)
        print("Detail chyby:\n", file=sys.stderr)
        traceback.print_tb(e.__traceback__)
        
        print("--------------------", file=sys.stderr)
        print("Text: ", end='', file=sys.stderr)
        print(e, file=sys.stderr)
        print("--------------------", file=sys.stderr)
        Errors.ErrorMessenger.echoError(Errors.ErrorMessenger.getMessage(Errors.ErrorMessenger.CODE_UNKNOWN_ERROR), Errors.ErrorMessenger.CODE_UNKNOWN_ERROR)

    

if __name__ == "__main__":
    main()
