# -*- coding: utf-8 -*-

"""
Copyright 2014 Brno University of Technology

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import re
import dateutil.parser as dparser

class ISO_date(object):
	'''
	Třída uchovávající datum (tedy rok, měsíc a den).
	Obsahuje atributy day, month a year.
	'''
	def __init__(self, year=0, month=0, day=0):
		'''
		Inicializace.
		:type year: **int**
		:type month: **int**
		:type day: **int**
		'''
		self.year = year
		self.month = month
		self.day = day
	
	def __str__(self):
		'''
		Převede self na řetězec ve formátu ISO 8601 (např. 2013-07-16).
		:returns:  str -- Vrací datum ve formátu ISO 8601.
		'''
		year = str(self.year).zfill(4)
		month = str(self.month).zfill(2)
		day = str(self.day).zfill(2)
		
		return "%s-%s-%s" % (year, month, day)
	
	def showWithoutZeros(self):
		'''
		Převede self na řetězec ve formátu ISO 8601 a případně odstraní nulový den a měsíc (např. 2013-07).
		:returns:  str -- Vrací datum ve formátu ISO 8601.
		'''
		year = str(self.year).zfill(4)
		month = ""
		day = ""
		
		if self.month:
			month = "-" + str(self.month).zfill(2)
			if self.day:
				day = "-" + str(self.day).zfill(2)
		
		return "".join((year, month, day))
	
	def from_isostr(self, input_str):
		'''
		Inicializace z řetězce (např. 2013-07-16).
		'''
		if (input_str == None) or (input_str == ""):
			self.year = 0
			self.month = 0
			self.day = 0
			return
		
		numbers = input_str.split("-")
		if len(numbers) > 0:
			self.year = int(numbers[0])
			if len(numbers) > 1:
				self.month = int(numbers[1])
				if len(numbers) > 2:
					self.day = int(numbers[2])
				else:
					self.day = 0
			else:
				self.month = 0
				self.day = 0
	
	def is_empty(self):
		'''
		Vrací True, pokud všechny hodnoty obsahují nulu.
		'''
		if (self.year == 0) and (self.month == 0) and (self.day == 0):
			return True
		return False
#

class Date(object):
	'''
	Třída pro nalezená data. Kromě roku, měsíce a dnu obsahuje také místo nalezení ve zdrojovém řetězci
	a řetězec, ze kterého bylo toto datum převedeno.
	
	Po vytvoření nové instance je nutné zavolat init_date() nebo init_interval() pro inicializaci atributů.
	'''
	regex_split_interval = None
	
	class Type:
		NONE=-1
		DATE=0
		INTERVAL=1
	
	def __init__(self):
		self.class_type = self.Type.NONE # Atribut značící typ nalezeného data (prosté datum či interval).
		pass
	
	def init_date(self, source, iso8601, start_offset=0, confidence=100):
		'''
		Inicializace data.
		:type source: **unicode**
		:type iso8601: **ISO_date**
		:type start_offset: **int**
		:type confidence: **int**
		'''
		self.class_type = self.Type.DATE
		
		self.source = source     # Řetězec source ze zdrojového textu
		self.iso8601 = iso8601   # Datum v **ISO_date**
		self.start_offset = start_offset # Začátek řetězce source ve zdrojovém textu
		self.end_offset = start_offset + len(source) # Konec řetězce source ve zdrojovém textu
		self.confidence = confidence # Míra spolehlivosti informace
	
	def init_interval(self, source, date_from, date_to, start_offset=0, confidence=100):
		'''
		Inicializace datového intervalu.
		:type source: **unicode**
		:type date_from: **ISO_date**
		:type date_to: **ISO_date**
		:type start_offset: **int**
		:type confidence: **int**
		'''
		self.class_type = self.Type.INTERVAL
		
		self.source = source
		self.date_from = date_from # Počáteční datum v **ISO_date**
		self.date_to = date_to     # Koncové datum v **ISO_date**
		self.start_offset = start_offset
		self.end_offset = start_offset + len(source)
		self.confidence = confidence
	
	def split_interval(self):
		'''
		Rozdělí interval do dvou datumů, které vrátí v list().
		'''
		if (self.class_type == self.Type.INTERVAL):
			if not Date.regex_split_interval:
				Date.regex_split_interval = re.compile("(?i)[ ]*"+long_interval_delim+"[ ]*")
			match = Date.regex_split_interval.search(self.source)
			date_from = Date()
			date_from.init_date( self.source[:match.start()], self.date_from, self.start_offset, self.confidence )
			date_to = Date()
			date_to.init_date( self.source[match.start()+len(match.group()):], self.date_to, self.start_offset+( match.start()+len(match.group()) ), self.confidence )
			return [date_from, date_to]
		else:
			return [self]
	
	def __unicode__(self):
		'''
		Převede atributy self na řetězec pro testovací výpisy.
		:returns:  unicode -- Vrací řetězec pro testovací výpisy.
		'''
		result = u""
		
		if self.class_type == self.Type.DATE:
			result = map(unicode, (self.start_offset, self.end_offset, u"date", self.source, self.iso8601))
			result = u"\t".join(result)
		elif self.class_type == self.Type.INTERVAL:
			result = map(unicode, (self.start_offset, self.end_offset, u"interval", self.source))
			result = u"%s\t%s -- %s" % (u"\t".join(result), self.date_from, self.date_to)
		else:
			result = u"class_type: NONE"
		
		return result
	
	def __str__(self):
		'''
		Převede atributy self na řetězec pro testovací výpisy.
		:returns:  str -- Vrací řetězec pro testovací výpisy.
		'''
		return unicode(self).encode("utf-8")
#

def addRegexParentheses(list):
	'''
	Přidá non-grouping verzi regulárních závorek na každou položku listu *IN PLACE*.
	'''
	i = 0
	while i < len(list):
		list[i] = "(?:"+list[i]+")"
		i = i + 1
#

MAX_ONLY_YEAR = 2999
dash_or_hyphen = u'-\u2010\u2011\u2012\u2013\u2012\u2013\u2014\u2015\u2043'

months = [
	u"led(?:(?:na)|(?:en))?",
	u"úno(?:(?:ra)|(?:r))?",
	u"bře(?:(?:zen)|(?:zna))?",
	u"dub(?:(?:en)|(?:na))?",
	u"kvě(?:(?:ten)|(?:tna))?",
	u"čer(?:(?:ven)|(?:vna))?",
	u"červenec",
	u"července",
	u"čec",
	u"srp(?:(?:en)|(?:na))?",
	u"zář(?:í)?",
	u"ríj(?:(?:en)|(?:na))?",
	u"lis(?:(?:topadu)|(?:topad))?",
	u"pro(?:(?:sinec)|(?:since))?"
]

addRegexParentheses(months)
allMonthsOR = "(?:"+"|".join(months)+")"

mnt2int = {
	u"01" : [u"led", u"leden", u"ledna"],
	"02" : ["úno", "únor", "února"],
	"03" : ["bře", "březen", "března"],
	"04" : ["dub", "duben", "dubna"],
	"05" : ["kvě", "květen", "května"],
	"06" : ["čer", "červen", "června"],
	"07" : ["červenec", "července", "čec"],
	"08" : ["srp", "srpen", "srpna"],
	"09" : ["zář", "září"],
	"10" : ["ríj", "ríjen", "ríjna"],
	"11" : ["lis", "listopad", "listopadu"],
	"12" : ["pro", "prosinec", "prosince"],
}

delim = "(?:[/_\-\\\]|["+dash_or_hyphen+"])"
long_interval_delim = "(?:["+dash_or_hyphen+"]|(?:[ ]do[ ]))"
desh_or_hypen_or_space_delim = "(?:(?:[ ]*["+dash_or_hyphen+"][ ]*)|[ ]+)"

url_char = "(?:\w|\d|[-._~!$&'()*+,;=:/?#\\[\\]%])"

start_delim = "(?:^|\W)"
end_delim = "(?:$|\W)"
not_start_delim = "(?<!\w[$/-_])"
not_end_delim = "(?![$/_%]\w)"
anno_domini = "(?:(?:[ ]+(?:AD|A\.D\.))|(?![ ]+(?:BC|B\.C\.)"+end_delim+"))"

# regulární výrazy pro match datumů

patterns = [
	# intervaly
	allMonthsOR + "[.]?[ ]+" + "\d\d?" + "[,][ ]+" + "\d{3,4}" + "[ ]*"+long_interval_delim+"[ ]*" + allMonthsOR + "[.]?[ ]+" + "\d\d?" + "[,][ ]+" + "\d{3,4}", # June. 6, 2005 – Sept. 12, 2007
	"\d\d?" + "[.]?" + "[ ]+" + allMonthsOR + "[.]?[,]?[ ]+" + "\d{3,4}" + "[ ]*"+long_interval_delim+"[ ]*" + "\d\d?" + "[.]?" + "[ ]+" + allMonthsOR + "[.]?[,]?[ ]+" + "\d{3,4}", # 20 March, 1856 – 10 January 1941
	# intervaly ((den\?, měsíc\?, rok) a (den\?, měsíc, rok)) a ((den\?, měsíc, rok) a (den\?, měsíc\?, rok))
	"\d{4}" + "[ ]*"+long_interval_delim+"[ ]*" + "\d\d?" + "[.]?" + "[ ]+" + allMonthsOR + "[.]?[,]?[ ]+" + "\d{3,4}", # 1856 - 20 March, 1856
	"\d\d?" + "[.]?" + "[ ]+" + allMonthsOR + "[.]?[,]?[ ]+" + "\d{3,4}" + "[ ]*"+long_interval_delim+"[ ]*" + "\d{4}", # Mar. 30, 1853 - 1888
	"(?:(?:\d\d?" + "[.]?" + "[ ]+)?" + allMonthsOR + "[.]?[,]?[ ]+" + ")?\d{4}" + "[ ]*"+long_interval_delim+"[ ]*" + "(?:\d\d?" + "[.]?" + "[ ]+)?" + allMonthsOR + "[.]?[,]?[ ]+" + "\d{4}", # March, 1856 - 1941; March, 1856 – January 1941
	"(?:\d\d?" + "[.]?" + "[ ]+)?" + allMonthsOR + "[.]?[,]?[ ]+" + "\d{4}" + "[ ]*"+long_interval_delim+"[ ]*" + "(?:(?:\d\d?" + "[.]?" + "[ ]+)?" + allMonthsOR + "[.]?[,]?[ ]+" + ")?\d{4}", # 1856 – January 1941; 1740 - 10 February 1808
	"\d\d?" + "[.][ ]*" + "\d\d?" + "[.][ ]*" + "\d{3,4}" + "[ ]*"+long_interval_delim+"[ ]*" + "\d\d?" + "[.][ ]*" + "\d\d?" + "[.][ ]*" + "\d{3,4}",
	"\d{4}" + "[ ]*"+long_interval_delim+"[ ]*" + "\d{4}", # 1693-1734, 1693 to 1734
	# datumy
	allMonthsOR + "[.]?[ ]+" + "\d\d?" + "[,][ ]+" + "\d{3,4}", # lis. 12, 2007
	"\d\d\d\d["+dash_or_hyphen+"]\d\d["+dash_or_hyphen+"]\d\d", # 1999-12-28
	"\d\d\d\d[-]?\s*" + allMonthsOR + "[-]?\s*\d\d", # 2010 listopad 16
	"\d\d?"+delim+"\d\d?"+delim+"\d{3,4}", # 12-11-1694, 12/11/1694
	"\d\d?" + "[.][ ]*" + "\d\d?" + "[.][ ]*" + "\d{3,4}", # 12.11.1694, 12. 11. 1694
	"\d\d?" + "[.]?[ ]+" + allMonthsOR + "[.]?[ ]+" + "\d{3,4}", # 16. listopadu 2003
	# Pouze měsíc a rok:
	allMonthsOR + "[.]?[ ]+" + "\d{4}", # November 2003
	# Speciální fuzzy slovní formáty:
	#"\d{1,2}(?:th|st|rd|nd)?" + desh_or_hypen_or_space_delim + "century" + anno_domini, # "17th-century", "4th century AD" # "15th century" => "1401-01-01 -- 1500-12-31"
	#allNthOR + desh_or_hypen_or_space_delim + "century" + anno_domini, # "fourth-century" => "0301-01-01 -- 0400-12-31"
	# Pouze rok:
	"\d\d\d\d", # 1694-99
	"\d{4}[s]?", # 1694, 1690s
]

addRegexParentheses(patterns)
allPatternsOR = u"(?i)"+start_delim+not_start_delim+"("+"|".join(patterns)+")"+not_end_delim+"(?="+end_delim+")"
#allPatternsOR = u"(?i)(?:^|(?<!\w[$€/-_:]))("+"|".join(patterns)+")(?:(?=$)|(?![$€°/_%]\w))"
# konec: regulární výrazy pro match datumů

# regulární výrazy pro rozpoznání datumů s nižším confidence
unsureDates = [
	"\d\d?"+delim+"\d\d?"+delim+"\d{3,4}", # 12-11-1694, 12/11/1694
	"\d\d?" + "[.][ ]*" + "\d\d?" + "[.][ ]*" + "\d{3,4}", # 12.11.1694, 12. 11. 1694
	"\d\d\d\d-\d\d", # 1694-99
	"\d{4}" + "[ ]*"+long_interval_delim+"[ ]*" + "\d{4}", # 1693-1734, 1693 to 1734
	"\d{4}", # 1694
]

addRegexParentheses(unsureDates)
allUnsureDatesOR = u"(?:"+"|".join(unsureDates)+")"
# konec: regulární výrazy pro rozpoznání datumů s nižším confidence

def not_czech_form(month, string):

	try:
		int(string[:4])
		return True
	except Exception:
		if string.startswith(month):
			return True

		return False

def get_date(string):
	isOnlyYear = bool( re.search("(?i)^\d{3,4}$", string) )
	if isOnlyYear:
		ISO = ISO_date( int(string) )
	else:
		dayfirst= True
		month = re.search(allMonthsOR, string)
		if month:
			month = month.group()
			month_number = None
			for key in mnt2int:
				if month in mnt2int[key]:
					month_number = key
					break
			if not_czech_form(month, string):
				dayfirst = False
			string = string.replace(month, month_number)

		try:
			date = dparser.parse(string, dayfirst=dayfirst)
			# Pokud je znám pouze rok a měsíc, pak se za den doplní nula
			if re.search("(?i)^\d\d[.]?[ ]+" + "\d{3,4}$", string):
				ISO = ISO_date(date.year, date.month)
			else:
				ISO = ISO_date(date.year, date.month, date.day)
		except ValueError:
			return None # nesprávné formáty datumů se nebudou brát

	return ISO

def specIntervalsMatch(text):
	result = {}
	for regex in specIntervals:
		result[regex] = specIntervals[regex].match(text)
	return result

# konec: regulární výrazy pro rozpoznání speciálních fuzzy slovních formátů

def find_dates(text, split_interval=True):
	'''
	Nalezne datumy v řetězci předaném pomocí parametru text.
	:param text: Řetězec se zdrojovými daty.
	:type text: **unicode**
	:param split_interval: Pokud je True, všechny intervaly se rozpadnou na dva datumy.
	:type split_interval: **bool**
	:returns:  list -- Vrací list všech nalezených datumů.
	'''
	assert isinstance(text, basestring)
	assert isinstance(split_interval, bool)
	
	if not isinstance(text, unicode):
		text = text.decode("utf-8", "replace")
	

	regexIntervals = re.compile("[ ]*"+long_interval_delim+"[ ]*")
	regexUnsureDates = re.compile("(?i)^"+allUnsureDatesOR+"$")
	dates = []
	
	for match in re.finditer(allPatternsOR, text):
		string = match.group(1)
		
		isUnsure = bool( regexUnsureDates.search(string) )	
		isInterval = bool( regexIntervals.search(string) )
		if len(re.findall("[" + dash_or_hyphen + "]", string)) > 1:
			isInterval = False
		
		if isInterval:
			interval = regexIntervals.split( string )
			string_from= interval[0]
			string_to= interval[1]

			ISO_from = get_date(string_from)
			ISO_to = get_date(string_to)
			
			if not ISO_from or not ISO_to:
				continue
		else:
			ISO = get_date(string)
			if not ISO:
				continue

		# Získané datum se uloží do třídy Date
		date = Date()
		
		if isUnsure:
			confidence = 80
		else:
			confidence = 100
		
		if isInterval:
			date.init_interval( match.group(1), ISO_from, ISO_to, match.start(1), confidence )
		else:
			date.init_date( match.group(1), ISO, match.start(1), confidence )
		
		# Zpracované datum se přidá do seznamu
		if split_interval:
			dates += date.split_interval()
		else:
			dates += [date]
	
	return dates

# TEST
if __name__ == '__main__':
	f = open("inputfile")
	text = unicode(f.read(), "utf-8", "replace")

	delimiter = "-"*33
	#text = unicode(sys.stdin.read(), "utf-8", "replace")
	#text = sys.stdin.read()
	#result = find_dates(text)

	result = find_dates(text, False)
	for item in result:
		print( delimiter + "\n" + str(item) )
	pass

# konec souboru dates.py
