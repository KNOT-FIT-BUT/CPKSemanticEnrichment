"""
Created on 7. 6. 2018
Modul zastřešující chybové zprávy, kódy a práci s nimi.

:author:     Martin Dočekal
:contact:    xdocek09@stud.fit.vubtr.cz
"""

import sys

class ExceptionMessageCode(Exception):
    """
    Vyjímka se zprávou a kódem.
    """
    def __init__(self, code, message=None):
        """
        Konstruktor pro vyjímku se zprávou a kódem.
        
        :param code: Kód chyby. Pokud je uveden pouze kód, pak se zpráva automaticky na základě něj doplní.
        :param message: zpráva popisující chybu
        """
        self.message = message if message is not None else ErrorMessenger.getMessage(code)
        self.code = code
        
        

class ErrorMessenger(object):
    """
    Obstarává chybové kódy a příslušné zprávy k těmto kódům.
    Píše zprávy do stderr a ukončuje skript s daným chybovým kódem.
    """

    CODE_ALL_OK=0;
    CODE_INVALID_ARGUMENTS=1
    CODE_COULDNT_WORK_WITH_FILE=2
    CODE_COULDNT_READ_INPUT_FILE=3
    CODE_INVALID_INPUT_FILE=4
    CODE_INVALID_INPUT_FILE_UNKNOWN_NAME_TYPE=5
    CODE_NO_DATA=6
    CODE_WORD_ANALYZE=7
    CODE_INVALID_CONFIG=8
    CODE_GRAMMAR_NO_START_SYMBOL=9
    CODE_GRAMMAR_NO_RULES=10
    CODE_GRAMMAR_INVALID_FILE=11
    CODE_GRAMMAR_START_SYMBOL=12
    CODE_GRAMMAR_SETS_TERM_NONTERM_NON_DIS=13
    CODE_INVALID_NAME=14
    CODE_WORD_NO_MORPHS_GENERATED=15
    CODE_NAME_IS_NOT_IN_LANGUAGE_GENERATED_WITH_GRAMMAR=16
    CODE_WORD_MISSING_MORF_FOR_CASE=17
    CODE_GRAMMAR_NOT_IN_LANGUAGE=18
    CODE_MA_FAILURE=19
    CODE_MORPH_ENUM_INVALID_CATEGORY=20
    CODE_MORPH_ENUM_INVALID_VALUE=21
    CODE_GRAMMAR_INVALID_ARGUMENT=22
    CODE_GRAMMAR_ARGUMENT_REPEAT=23
    CODE_NAME_WITHOUT_TYPE=24
    CODE_NAME_NO_MORPHS_GENERATED=25
    
    CODE_ALL_VALUES_NOT_COVERED=99
    CODE_UNKNOWN_ERROR=100

    """
    Obsahuje chybové zpráva. Indexy korespondují s chybovými kódy.
    """
    __ERROR_MESSAGES={
            CODE_ALL_OK:"Vše v pořádku.",
            CODE_INVALID_ARGUMENTS:"Nevalidní argumenty.",
            CODE_COULDNT_WORK_WITH_FILE: "Nemohu pracovat se souborem.",
            CODE_COULDNT_READ_INPUT_FILE:"Nemohu číst vstupní soubor.",
            CODE_INVALID_INPUT_FILE:"Nevalidní vstupní soubor.",
            CODE_INVALID_INPUT_FILE_UNKNOWN_NAME_TYPE:"Nevalidní vstupní soubor. Neznámý druh jména.",
            CODE_WORD_ANALYZE:"Nepodařilo se analyzovat slovo/a.",
            CODE_INVALID_CONFIG:"Nevalidní hodnota v konfiguračním souboru.",
            CODE_GRAMMAR_NO_START_SYMBOL:"Není uveden startovací symbol.",
            CODE_GRAMMAR_NO_RULES:"Nejsou uvedena pravidla.",
            CODE_GRAMMAR_INVALID_FILE:"Nevalidní soubor s gramatikou.",
            CODE_GRAMMAR_START_SYMBOL:"Startovací symbol není v množině neterminálů.",
            CODE_GRAMMAR_SETS_TERM_NONTERM_NON_DIS:"Množina terminálů a neterminálů má neprázdný průnik.",
            CODE_INVALID_NAME:"Nevalidní jméno.",
            CODE_WORD_NO_MORPHS_GENERATED:"Pro slovo se nepodařilo vygenerovat tvary.",
            CODE_NAME_IS_NOT_IN_LANGUAGE_GENERATED_WITH_GRAMMAR:"Název není v jazyce generovaným poskytnutou gramatikou.",
            CODE_WORD_MISSING_MORF_FOR_CASE:"Nepovedlo se vygenerovat tvar pro pád.",
            CODE_GRAMMAR_NOT_IN_LANGUAGE:"Selhání na příslušnosti do jazyka.",
            CODE_MA_FAILURE:"Morfologický analyzátor selhal.",
            CODE_MORPH_ENUM_INVALID_CATEGORY:"Neznámá morfologická kategorie: {}",
            CODE_MORPH_ENUM_INVALID_VALUE:"Neznámá hodnota pro morfologickou kategorii {}: {}",
            CODE_GRAMMAR_INVALID_ARGUMENT:"V souboru s gramatikou je nevalidní argument: {}.",
            CODE_GRAMMAR_ARGUMENT_REPEAT:"V souboru s gramatikou se vícekrát opakuje argument u jednoho terminálu: {}.",
            CODE_NAME_WITHOUT_TYPE:"U {} se nepodařilo zjistit druh jména/názvu.",
            CODE_NAME_NO_MORPHS_GENERATED:"Pro jméno {} se nepodařilo vygenerovat tvary u některých slov: {}",
            
            CODE_ALL_VALUES_NOT_COVERED: "Nejsou pokryty všechny hodnoty.",
            CODE_UNKNOWN_ERROR:"Neznámá chyba."  ,
    }

    @staticmethod
    def echoError(message, code):
        """
        Vypíše chybovou zprávu do stderr a ukončí skript s poskytnutým kódem.

        :param message: Text chybové zprávy.
        :param code: ukončující kód
        """
        print(message, file=sys.stderr)
        sys.exit(code);
        

    @classmethod
    def getMessage(cls, code):
        """
        Getter pro chybovou zprávu, která odpovídá danému chybovému kódu.

        :param cls: Class
        :param code: Chybový kód.
        :return: Chybová zpráva.
        """
        return cls.__ERROR_MESSAGES[code];
