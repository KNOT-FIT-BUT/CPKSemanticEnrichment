#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Author: Matej Magdolen, xmagdo00@stud.fit.vutbr.cz
# Author: Jan Cerny, xcerny62@stud.fit.vutbr.cz
# Author: Lubomir Otrusina, iotrusina@fit.vutbr.cz
# Author: David Prexta, xprext00@stud.fit.vutbr.cz
#

import sys
import re
import argparse
import natToKB
import figa.sources.marker as figa
import ner_knowledge_base
import os
import unicodedata
import uuid
import collections
import dates
import name_recognizer.data_row as module_data_row
import name_recognizer.name_recognizer as name_recognizer

# Pro debugování:
import difflib, linecache, inspect

import logging
module_logger = logging.getLogger("ner")
#module_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s: %(name)s: %(context)s:\n'''\n%(message)s\n'''")
console_handler.setFormatter(formatter)
module_logger.addHandler(console_handler)

reload(sys)
sys.setdefaultencoding("utf-8")

# pronouns along with their type they refer to
PRONOUNS = {"on" : "M",
            "ho" : "M",
            "mu" : "M",
         "o něm" : "M",
           "jím" : "M",
           "ona" : "F",
            "jí" : "F",
          "o ní" : "F",}

VERBS = {" byl ", " byla ", " je "}


MENTIONS_TYPE = {
    'person' : {},
    'organisation' : {},
    'geo:geoplace' : {},
    'geoplace:populatedPlace' : {},
    'event' : {},
    'geoplace:protectedArea' : {},
    'geoplace:conservationArea' : {},
    'geoplace:mountain' : {},
    'geoplace:mountain' : {},
    'geoplace:castle' : {},
    'geoplace:lake' : {},
    'geoplace:forest' : {},
    'geoplace:mountainPass' : {},
    'geo:mountainRange' : {},
    'geo:river' : {},
    'geoplace:observationTower' : {},
    'geo:waterfall' : {}
}

display_entity_score = False

ACCENT_REGEX = re.compile(r"COMBINING|HANGUL JUNGSEONG|HANGUL JONGSEONG")

nationalities_forms = natToKB.NatToKB().get_nationalities()

# same as in ner.py
def unicodedata_name(c):
    """ Workaround for unicodedata.name(c) in order to deal with ValueError reising for characters without names (all control characters)."""
    
    try:
        return unicodedata.name(c)
    except ValueError:
        return ""

# same as in ner.py
def remove_accent(_string):
    """ Removes accents from a string. For example, Eduard Ovčáček -> Eduard Ovcacek. """
    # BUG: Toto nemůže fungovat je-li isinstance(_string, str), protože odstranením diakritiky se jistě změní délka u typu str!
    
    nfkd_form = unicodedata.normalize('NFKD', unicode(_string))
    result = str("".join([c for c in nfkd_form if not ACCENT_REGEX.search(unicodedata_name(c))]))
    result = result.decode("utf8", "replace")
    if len(_string) == len(result):
        return result
    else:
        return _string

# same as in ner.py
def ncr2unicode(s):
	"""
	Translates hexadecimal NCRs (https://en.wikipedia.org/wiki/Numeric_character_reference) to the Unicode and then encode to default encoding. For example, '&#x957F;&#x5EA6;' (长度) -> '\xe9\x95\xbf\xe5\xba\xa6' (utf-8).
	"""
	def replaceEntities(s):
		s = s.groups()[0]
		try:
			if s[0] in ['x','X']:
				c = int(s[1:], 16)
			else:
				c = int(s)
			return unichr(c)
		except ValueError:
			return '&#'+s+';'
	
	return re.sub(r"&#([xX]?(?:[0-9a-fA-F]+));", replaceEntities, s).encode(sys.getdefaultencoding())


# same as in ner.py
class EntityRegister(object):
    """ A class containing the index of all disambiguated entities. """

    def __init__(self):
        self.id2entity = {}
        self.entity2id = {}

    def insert_entity(self, _entity, _id):
        """ Insterts a preferred sense for a given entity into to the entity register. """
        assert isinstance(_entity, Entity)
        assert isinstance(_id, int) or _id == None

        if _entity in self.entity2id:
            sense = self.entity2id[_entity]
            self.id2entity[sense].discard(_entity)
        self.entity2id[_entity] = _id
        if _id not in self.id2entity:
            self.id2entity[_id] = set()
        self.id2entity[_id].add(_entity)

    def __str__(self):
        return str(self.id2entity)


class Entity(object):
    """ A text entity referring to a knowledge base item. """

    def __init__(self, entity_attributes, kb, input_string, input_string_in_unicode, register):
        """
        Creates an entity by parsing a line of figa output from entity_str.
        Entity will be referring to an item of the knowledge base kb.

        entity_attributes - entity data from figa
        kb - Knowledge Base
        input_string - input string
        input_string_in_unicode - input string in Unicode
        register - entity register
        """
        assert isinstance(entity_attributes, list)
        assert isinstance(kb, ner_knowledge_base.KnowledgeBaseCZ)
        assert isinstance(input_string, str)
        assert isinstance(input_string_in_unicode, unicode)
        assert isinstance(register, EntityRegister)
        
        self.next_to_same_type = False
        self.display_score = False
        self.poorly_disambiguated = True
        self.is_coreference = False
        self.is_name = False
        self.is_nationality = False

        self.preferred_sense = None
        self.next_word_begin = None
        self.next_word_end = None
        self.previous_word = None
        self.before_previous = None
        self.candidates = []
        self.score = []
        self.static_score = []
        self.context_score = []
        self.coreferences = set()

        self.input_string = input_string
        self.input_string_in_unicode = input_string_in_unicode

        self.kb = kb
        self.register = register

        # getting possible senses (sense 0 marks a coreference)
        self.senses = set([int(s) for s in entity_attributes[0].split(';') if s != '0'])
        
        # Ofsety jsou vztaženy k unicode.
        # start offset is indexed differently from figa
        self.start_offset = int(entity_attributes[1]) - 1
        self.end_offset = int(entity_attributes[2])
        self.begin_of_paragraph = None

        # the source text of the entity
        self.source = ncr2unicode(entity_attributes[3])

        if len(self.senses) == 0:
            global nationalities_forms
            if self.source in nationalities_forms:
                self.is_nationality = True

        # possible coreferences - people whose names are supersets of an entity
        self.partial_match_senses = self.kb.people_named(remove_accent(self.source).lower())

    @classmethod
    def from_data_row(cls, kb, dr, input_string, input_string_in_unicode, register):
        assert isinstance(kb, ner_knowledge_base.KnowledgeBaseCZ)
        assert isinstance(dr, module_data_row.DataRow)
        assert isinstance(input_string, str)
        assert isinstance(input_string_in_unicode, unicode)
        assert isinstance(register, EntityRegister)
        
        entity = cls(str(dr).split('\t'), kb, input_string, input_string_in_unicode, register)
        entity.is_name = True
        return entity

    def set_preferred_sense(self, _sense):
        assert isinstance(_sense, (int, Entity)) or _sense == None
        
        self.preferred_sense = _sense

        if not isinstance(_sense, Entity):
            self.register.insert_entity(self, _sense)

    def has_preferred_sense(self):
        return self.preferred_sense

    def get_preferred_sense(self):
        if isinstance(self.preferred_sense, Entity):
            return self.preferred_sense.preferred_sense
        else:
            return self.preferred_sense

    def get_preferred_entity(self):
        if not isinstance(self.preferred_sense, Entity):
            return self
        else:
            return self.preferred_sense

    def disambiguate_without_context(self):
        """ Chooses the correct sense of the entity as the preferred one (without context). """

        # we don't resolve coreference in this step
        if self.source.lower() in PRONOUNS or self.partial_match_senses:
            self.is_coreference = True
            return


        # only event can start with word během
        if(self.left_context(" během ")):
        	self.senses = [s for s in self.senses if self.kb.get_ent_type(s) == "event"]

        # search for one of verbs in rest of the sentence
        sentence = self.right_sentence()
        verb_index = -1
        for verb in VERBS:
            verb_index = sentence.find(verb) 
            if(verb_index != -1):
                break
        
        # if verb is behind entity in sentence try to disambiguate
        # Example: sentence: Washington byl první prezident USA.
        #          possible entities: George Washington - person
        #                             Washington D. C. - location
        #          verb after entity - byl
        #          proffesion mentioned after verb - prezident
        #          Location entity eliminated
        if(verb_index != -1):
            proffesions = []
            for s in self.senses:
                if(self.kb.get_ent_type(s) in ["person", "person:artist"]):
                    proffesions = self.kb.get_data_for(s, "POVOLANI")
                    if(proffesions):
                        proffesions = proffesions.split('|')
                        proffesions = [p for p in proffesions if sentence.find(" " + p + " ", verb_index) != -1]
                        if(proffesions):
                            break
            
            if(proffesions):
                new_senses = []
                for s in self.senses:
                    if self.kb.get_ent_type(s) in ["person", "person:artist"]:
                        for proffesion in self.kb.get_data_for(s, "POVOLANI").split('|'):
                            if(proffesion in proffesions):
                                new_senses.append(s)
                                break
                self.senses = new_senses

        self.senses = set(self.senses)
        self.candidates = list(self.senses)


        # entity doesnt have any candidates
        if not self.candidates:
            return
        #entity has exactly one candidate
        elif len(self.candidates) == 1:
            self.set_preferred_sense(self.candidates[0])
            self.poorly_disambiguated = False

        # the entity has to be disambiguated
        if not self.has_preferred_sense():
            for i in self.candidates:
                static_score = self.kb.get_score(i)
                self.static_score.append(static_score)
                self.score.append(static_score)

            self.set_preferred_sense(self.candidates[self.score.index(max(self.score))])

    def disambiguate_with_context(self, context):
        """ Chooses the correct sense of the entity as the preferred one (with context). """
        assert isinstance(context, Context)
        
        # we don't resolve coreference in this step
        if self.is_coreference or not self.candidates:
            return

        # recomputing paragraph offset
        context.recompute_paragraph_offset(self.start_offset)

        # the entity has to be disambiguated
        self.score = []
        self.static_score = []
        self.context_score = []

        for i in self.candidates:
            ent_type = self.kb.get_ent_type(i)
            static_score = self.kb.get_score(i)
            context_score = 0
            if ent_type == 'geoplace:populatedPlace':
                context_score = context.country_percentile(self.kb.get_data_for(i, "LOKACE"))
            elif ent_type in ["person", "person:artist"]:
                context_score = context.person_percentile(i)
            elif ent_type == 'organisation' or ent_type == 'event':
                context_score = context.organisation_percentile(i, ent_type)
            elif ent_type == 'geoplace:protectedArea':
                context_score = context.prot_area_percentile(i)
            elif ent_type == 'geoplace:conservationArea':
                context_score = context.con_area_percentile(i)
            elif ent_type == 'geoplace:mountain':
                context_score = context.mountain_percentile(i)
            elif ent_type == 'geoplace:castle':
                context_score = context.castle_percentile(i)
            elif ent_type == 'geoplace:lake':
                context_score = context.lake_percentile(i)
            elif ent_type == 'geoplace:forest':
                context_score = context.forest_percentile(i)
            elif ent_type == 'geoplace:mountainPass':
                context_score = context.mountain_pass_percentile(i)
            elif ent_type == 'geo:mountainRange':
                context_score = context.mountain_range_percentile(i)
            elif ent_type == 'geo:river':
                context_score = context.river_percentile(i)
            elif ent_type == 'geoplace:observationTower':
                context_score = context.observation_tower_percentile(i)
            elif ent_type == 'geo:waterfall':
                context_score = context.waterfall_percentile(i)
            if context_score > 0:
                self.poorly_disambiguated = False
            self.static_score.append(static_score)
            self.context_score.append(context_score)
            self.score.append(static_score + context_score)

        self.set_preferred_sense(self.candidates[self.score.index(max(self.score))])
        
        # if preffered sense for entity is person, increase number of mentions of that person in paragraph
        if self.kb.get_ent_type(self.get_preferred_sense()) in ["person", "person:artist"] and len(self.candidates) != 1:
            name = self.kb.get_data_for(self.get_preferred_sense(), "JMENO")
            if name not in context.mentions[context.paragraphs[context.paragraph_index]]['person']:
                context.mentions[context.paragraphs[context.paragraph_index]]['person'][name] = 0
            
            context.mentions[context.paragraphs[context.paragraph_index]]['person'][name] += 1

    
    def resolve_pronoun_coreference(self, context):
        """ Resolves a pronoun coreference using context. """
        assert isinstance(context, Context)

        pronoun_type = PRONOUNS[self.source.lower()]

        if pronoun_type == 'M':
            
            #on - point to last male
            if self.source == "on":
                if context.last_unknown_gender:
                    context.before_last_male = context.last_male
                    context.last_male = context.last_unknown_gender
                    context.last_person = context.last_unknown_gender
                    context.last_unknown_gender = None
                if context.last_male and context.last_male.start_offset >= self.begin_of_paragraph:
                    self.set_preferred_sense(context.last_male.get_preferred_entity())
            else:
                # other pronoun for male
                if context.last_person:
                    #get gender of person mentioned last
                    gender = self.kb.get_data_for(context.last_person.get_preferred_sense(), "POHLAVI")
                    # last person mentioned - female
                    # point to last male if there is any in current paragraph
                    if gender == "F":
                        if context.last_male and context.last_male.start_offset >= self.begin_of_paragraph:
                            self.set_preferred_sense(context.last_male.get_preferred_entity())
                    # last person mentioned - male
                    elif gender == "M":
                        # point to before last male if there is any in current paragraph
                        if context.before_last_male and context.before_last_male.start_offset >= self.begin_of_paragraph:
                            self.set_preferred_sense(context.before_last_male.get_preferred_entity())
                        elif context.last_male.start_offset >= self.begin_of_paragraph:
                            self.set_preferred_sense(context.last_male.get_preferred_entity())
                    else:
                        # last person gender unknown - set to male and point to it
                        if context.last_male and not context.last_male.start_offset >= self.begin_of_paragraph:
                            context.before_last_male = context.last_male
                            context.last_male = context.last_unknown_gender
                            context.last_unknown_gender = None

                        if context.last_male and context.last_male.start_offset >= self.begin_of_paragraph:  
                            self.set_preferred_sense(context.last_male.get_preferred_entity())


        elif pronoun_type == 'F':
            #ona - point to last female
            if self.source == "ona":
                if context.last_unknown_gender:
                    context.before_last_female = context.last_female
                    context.last_female = context.last_unknown_gender
                    context.last_person = context.last_unknown_gender
                    context.last_unknown_gender = None
                if context.last_female and context.last_female.start_offset >= self.begin_of_paragraph:
                    self.set_preferred_sense(context.last_female.get_preferred_entity())
            else:
                # other pronoun for female
                if context.last_person:
                    #get gender of person mentioned last
                    gender = self.kb.get_data_for(context.last_person.get_preferred_sense(), "POHLAVI")
                    # last person mentioned - male
                    # point to last female if there is any in current paragraph
                    if gender == "M":
                        if context.last_female and context.last_female.start_offset >= self.begin_of_paragraph:
                            self.set_preferred_sense(context.last_female.get_preferred_entity())
                    # last person mentioned - female
                    elif gender == "F":
                        # point to before last female if there is any in current paragraph
                        if context.before_last_female and context.before_last_female.start_offset >= self.begin_of_paragraph:
                            self.set_preferred_sense(context.before_last_female.get_preferred_entity())
                        elif context.last_female.start_offset >= self.begin_of_paragraph:
                            self.set_preferred_sense(context.last_female.get_preferred_entity())
                    else:
                        # last person gender unknown - set to female and point to it
                        if context.last_female and not context.last_female.start_offset >= self.begin_of_paragraph:
                            context.before_felast_male = context.last_female
                            context.last_female = context.last_unknown_gender
                            context.last_unknown_gender = None

                        if context.last_female and context.last_female.start_offset >= self.begin_of_paragraph:  
                            self.set_preferred_sense(context.last_female.get_preferred_entity())

    def __str__(self):
        """ Converts an entity into an output format. """

        result = str(self.start_offset) + "\t" + str(self.end_offset) + "\t"
        if self.is_coreference:
            result += "coref"
        elif self.is_name:
            result += "name"
        else:
            result += "kb"
        result += "\t" + self.input_string_in_unicode[self.start_offset:self.end_offset] + "\t"
        if display_entity_score and self.candidates:
            candidates_str = []
            i = 0
            for cand in self.candidates:
                candidates_str.append(str(cand))
                if i < len(self.score):
                    candidates_str[-1] += " " + str(self.score[i])
                i += 1
            result += ";".join(candidates_str)
        elif self.has_preferred_sense():
            result += str(self.get_preferred_sense())
        else:
            if self.is_coreference:
                senses_list = sorted(self.partial_match_senses)
            else:
                senses_list = sorted(self.senses)
            for i in senses_list:
                result += str(i)
                if i != senses_list[-1]:
                    result += ';'
        return result

    def right_context(self, right):
        assert isinstance(right, basestring)
        if not isinstance(right, unicode):
            right = right.decode(sys.getdefaultencoding())
        
        length = len(right)
        text = self.input_string_in_unicode
        if self.end_offset + length > len(text):
            return False
        return text[self.end_offset:self.end_offset + length] == right
    
    def right_sentence(self):
        text = self.input_string_in_unicode[self.end_offset:]
        collum_count = 0
        sentence = ""

        for index in range(0, len(text)):
            if(text[index] ==")"):
                collum_count -= 1
            elif(text[index] =="("):
                collum_count += 1
            elif(not collum_count):
                sentence += text[index]
                if(text[index] == "." ):
                    break
        return sentence

    def left_context(self, left):
        assert isinstance(left, basestring)
        if not isinstance(left, unicode):
            left = left.decode(sys.getdefaultencoding())
        
        length = len(left)
        text = self.input_string_in_unicode
        if self.start_offset - length < 0:
            return False
        return text[self.start_offset - length:self.start_offset] == left

    def is_equal(self, other):
        if self.start_offset == other.start_offset and \
        self.end_offset == other.end_offset and \
        self.source == other.source:
            return True
        return False

    def is_overlapping(self, other):
        if self.start_offset <= other.start_offset and \
        self.end_offset >= other.end_offset and \
        len(self.source) > len(other.source) and \
        other.source in self.source:
            return True
        return False

    def is_person(self):
        if self.is_name:
            return True
        if not self.is_coreference and self.senses:
            kb_type = self.kb.get_ent_type(list(self.senses)[0])
            if kb_type in ['person', 'artist']:
                return True
        return False

class Context(object):
    """ Information about a context of a processed text. """

    def __init__(self, entities, kb, paragraphs, nationalities):
        """ Prepares the context from the list of entities disambiguated without the context. """
        assert isinstance(entities, list) # list of Entity and dates.Date
        assert isinstance(kb, ner_knowledge_base.KnowledgeBaseCZ)
        assert isinstance(paragraphs, list)

        self.entities = entities
        self.kb = kb
        self.paragraphs = paragraphs

        # max score for each candidate
        self.people_max_scores = {}
        # number of locations in each country mentioned in each paragraph (+ sorted version)
        self.mentions = {}
        self.countries = {}
        self.country_sum = {}
        self.countries_sorted = {}
        # people mentioned by full name in whole text
        self.people_in_text = set()
        # people mentioned by full name in paragraph
        self.people = {}
        self.organisations = {}
        # list of nationalities mentioned in each paragraph 
        self.people_nationalities = {}
        # list of dates mentioned in each paragraph
        self.people_dates = {}
        # list of proffestions mentioned in paragraph
        self.people_professions = {}
        # initializing pronoun variables
        self.init_pronouns()
        # initializing the paragraph index
        self.paragraph_index = 0
        self.events = {}

        # initializing index variables
        par_index = 0
        ent_index = 0
        nat_index = 0

        # adding one artificial paragraph, otherwise self.paragraphs[par_index + 1] will fail
        self.paragraphs.append(sys.maxint)

        # computing statistics for each paragraph
        for par in self.paragraphs:
            self.mentions[par] = MENTIONS_TYPE
            self.countries[par] = {}
            self.people_nationalities[par] = []
            self.people_dates[par] = []
            self.people[par] = {}
            self.events[par] = {}
            self.country_sum[par] = 0
            self.people_professions[par] = []
            self.organisations[par] = {}
            par_text = ""

            while (nat_index < len(nationalities) and nationalities[nat_index].start_offset < self.paragraphs[par_index + 1]):
                nat = nationalities[nat_index]
                name = nat.source
                if name not in self.people_nationalities[par]:
                    self.people_nationalities[par].append(name)

                nat_index += 1

            while (ent_index < len(entities) and entities[ent_index].start_offset < self.paragraphs[par_index + 1]):
                ent = self.entities[ent_index]

                if isinstance(ent, Entity):
                    par_text = ent.input_string_in_unicode[self.paragraphs[par_index] : self.paragraphs[par_index + 1]]
                    ent.begin_of_paragraph = par

                    # entities with only 1 candidate
                    if not ent.poorly_disambiguated:
                        ent_type = ent.kb.get_ent_type(ent.get_preferred_sense())

                        if(ent_type == "geoplace:populatedPlace"):
                            # get location country name and aliases
                            name = ent.kb.get_data_for(ent.get_preferred_sense(), "NAZEV")
                            country = ent.kb.get_data_for(ent.get_preferred_sense(), "LOKACE")
                       
                            if name not in self.mentions[par][ent_type]:
                                self.mentions[par][ent_type][name] = 1
                            else:
                                self.mentions[par][ent_type][name] += 1
                            self.country_sum[par] += 1

                            if country:
                                if country not in self.mentions[par][ent_type]:
                                    self.mentions[par][ent_type][country] = 1
                                else:
                                    self.mentions[par][ent_type][country] += 1
                                self.country_sum[par] += 1
                            '''
                            # check if country is already in dictionary
                            name_in_dict = None
                            for c in self.countries[par]:
                    
                                if(country == c or country in self.countries[par][c]["aliases"]):
                                    name_in_dict = c
                                else:
                                    for alias in aliases:
                                        if(alias == c or alias in self.countries[par][c]["aliases"]):
                                            name_in_dict = c
                                            break
                                if(name_in_dict):
                                    break

                            # if country isnt in dictionary create new entry for him
                            if(not name_in_dict):
                                self.countries[par][country] = {}
                                self.countries[par][country]["score"] = 1
                                self.countries[par][country]["aliases"] = aliases
                                name_in_dict = country
                            # country is in dictinoary
                            # update values and add aliases
                            else:
                                self.countries[par][name_in_dict]["score"] += 1
                                aliases_in_dict = self.countries[par][name_in_dict]["aliases"]
                                for alias in aliases:
                                    if not (alias == name_in_dict or alias in aliases_in_dict):
                                        self.countries[par][name_in_dict]["aliases"].append(alias)
                                if not (country == name_in_dict or country in aliases_in_dict):
                                    self.countries[par][name_in_dict]["aliases"].append(country)

                            # possible nationality mentioned - add entity source to aliases
                            # example: Váh je nejdelší řeka Slovenska .
                            #               Slovenska - entity: Slovenská republika, location
                            #               persons nationality in KB - slovenská
                            '''
                            #if ent.source not in self.countries[par]:
                            #    self.countries[par][ent.source] = 0
                            #else:
                            #    self.countries[par][ent.source] += 1

                        # if entity is person update number of her mentions in dictionary
                        else:
                            if ent_type == "person:artist":
                                ent_type = "person"

                            name_tag = "JMENO"
                            if not ent_type in ["person:artist", "person"]:
                                name_tag = "NAZEV"


                            name = ent.kb.get_data_for(ent.get_preferred_sense(), name_tag)
                            #print(ent.get_preferred_sense())
                            if name not in self.mentions[par][ent_type]:
                                self.mentions[par][ent_type][name] = 0
                            self.mentions[par][ent_type][name] += 1

                    elif ent.has_preferred_sense():
                        for c in ent.candidates:
                            ent_type = ent.kb.get_ent_type(c)
                            if ent_type in ["person", "person:artist"]:
                                professions = ent.kb.get_data_for(c, "POVOLANI")
                                if(professions):
                                    professions = professions.split('|')
                                    [self.people_professions[par].append(p) for p in professions if par_text.find(p) != -1 and p not in self.people_professions[par]]

                elif isinstance(ent, dates.Date):
                    if ent.class_type == ent.Type.DATE:
                        self.people_dates[par].append(ent.iso8601.showWithoutZeros())
                    elif ent.class_type == ent.Type.INTERVAL:
                        self.people_dates[par].append(ent.date_from.showWithoutZeros())
                        self.people_dates[par].append(ent.date_to.showWithoutZeros())

                ent_index += 1
            par_index += 1

        # removing the artificial paragraph
   
    def recompute_paragraph_offset(self, start_offset):
        """
        Recomputes paragraph offset, if the entity at the start_offset belongs
        to the different paragraph.
        """
        assert isinstance(start_offset, int)
        
        # we are in the last paragraph -> no change in paragraph offsets
        if self.paragraph_index + 1 >= len(self.paragraphs):
            return
        # the entity belongs to the current paragraph -> no change in paragraph offsets
        elif start_offset >= self.paragraphs[self.paragraph_index] and start_offset < self.paragraphs[self.paragraph_index + 1]:
            return
        # the entity belongs to the different paragraph -> we have to recompute paragraph offsets
        else:
            par_i = self.paragraph_index
            while par_i + 1 < len(self.paragraphs) and self.paragraphs[par_i + 1] <= start_offset:
                par_i += 1
            self.paragraph_index = par_i

    def update(self, entity):
        """ Updates context (last person, last male, last female, last location etc.). """
        assert isinstance(entity, Entity)
        
        # keep the last entity of each pronoun type for pronoun coreference resolution
        ent_type = self.kb.get_ent_type(entity.get_preferred_sense())

        if ent_type in ['person', 'artist']:
            self.before_last_person = self.last_person
            self.last_person = entity
            gender = self.kb.get_data_for(entity.get_preferred_sense(), "POHLAVI")
            if gender == 'M':
                self.before_last_male = self.last_male
                self.last_male = entity
                self.last_unknown_gender = None
            elif gender == 'F':
                self.before_last_female = self.last_female
                self.last_female = entity
                self.last_unknown_gender = None
            else:
                self.last_unknown_gender = entity
        elif ent_type == "location":
            self.last_location = entity

    def mentioned_in_par(self, candidates, field):
        par_index = self.paragraphs[self.paragraph_index]

        mentioned_in_par_score = 0
        for c in candidates:
            if c in self.mentions[par_index][field]:
                mentioned_in_par_score =  self.mentions[par_index][field][c]
                break

        if mentioned_in_par_score:
            mentioned_in_par_score = mentioned_in_par_score * 100 / sum(self.mentions[par_index][field].values())

        return mentioned_in_par_score
          

    def person_percentile(self, candidate):
        """
        Returns a percentile of references to a candidate person from
        knowledge base amongst other people.
        """
        assert isinstance(candidate, int)
        par_index = self.paragraphs[self.paragraph_index]

        # computing people_nation_score
        people_nationality_score = 0
        # getting the nationality for a given person
        person_nationality = self.kb.get_nationalities(candidate)
        for nat in person_nationality:
            if nat in self.people_nationalities[par_index]:
                people_nationality_score += 1
            #for c in self.countries[par_index]:
            #    if nat == c or nat in self.countries[par_index][c]["aliases"]:
            #    # the person has the same nationality like other persons in this paragraph
            #        people_nationality_score += 1
        if self.people_nationalities[par_index]:
           # normalizing people_nationality_score
           people_nationality_score = people_nationality_score * 100 / len(self.people_nationalities[par_index])

        # computing people_date_score
        people_date_score = 0
        # getting the dates for a given person
        person_dates = self.kb.get_dates(candidate)
        for context_date in self.people_dates[par_index]:
            for person_date in person_dates:
                if context_date.find(person_date) > -1 or person_date.find(context_date) > -1:
                    # the person has the date mentioned in this paragraph
                    people_date_score += 1
        if self.people_dates[par_index]:
           # normalizing people_date_score
            people_date_score = people_date_score * 100 / len(self.people_dates[par_index])

        # computing people_profession_score
        people_profession_score = 0

        person_professions = self.kb.get_data_for(candidate, "POVOLANI").split('|')
        for prof in person_professions:
            if prof in self.people_professions[par_index]:
                people_profession_score += 1
        if self.people_professions[par_index]:
            people_profession_score = people_profession_score * 100 / len(self.people_professions[par_index])


        person_name = [self.kb.get_data_for(candidate, "JMENO")]
        mentioned_in_par_score = self.mentioned_in_par(person_name, 'person')
#        if person_name in self.mentions[par_index]['person']:
#            mentioned_in_par_score = self.mentions[par_index]['person'][person_name] * 100 / sum(self.mentions[par_index]['person'].values())

        # summing up the scores
        result = (people_nationality_score + people_date_score + people_profession_score + mentioned_in_par_score) / 4

        # storing new max score
        if candidate in self.people_max_scores and result > self.people_max_scores[candidate]:
                self.people_max_scores[candidate] = result
        else:
            self.people_max_scores[candidate] = result

        return result

    def country_percentile(self, country):
        """ Returns a percentile of a number of location belonging to a country identified by code. """
        assert isinstance(country, str)

        country_score = self.mentioned_in_par(country, 'geoplace:populatedPlace')
        #if country in self.mentions[par_index]["geoplace:populated_place"]:
        #   country_score = self.mentions[par_index]["geoplace:populated_place"][country]

        #if country_score:
        #    return country_score * 100 / self.country_sum[par_index]
              
        return 0

    def organisation_percentile(self, candidate, ent_type):

        par_index = self.paragraphs[self.paragraph_index]

        #mentioned_in_par_score = 0
        name = [self.kb.get_data_for(candidate, "NAZEV")]
        mentioned_in_par_score = self.mentioned_in_par(name, ent_type)
        #if ent_type == 'organistaion':
        #    if name in self.mentions[par_index][ent_type]:
        #        mentioned_in_par_score = self.mentions[par_index][ent_type][name] * 100 / sum(self.mentions[par_index][ent_type].values())
        #else:
        #    if name in self.mentions[par_index][ent_type]:
        #        mentioned_in_par_score = self.mentions[par_index][ent_type][name] * 100 / sum(self.mentions[par_index][ent_type].values())

 
        #place_score = 0
        place = [self.kb.get_data_for(candidate, "MISTO")]
        place_score = self.mentioned_in_par(place, 'geoplace:populatedPlace')

       #if place in self.mentions[par_index]["geoplace:populated_place"]:
        #    place_score = self.mentions[par_index]["geoplace:populated_place"][place]

       # if place_score:
        #    place_score = place_score * 100 / self.country_sum[par_index]

        org_date_score = 0
        if ent_type == "organisation":
            org_dates = [self.kb.get_data_for(candidate, "ZALOZENI"), self.kb.get_data_for(candidate, "ZRUSENI")]
        else:
            org_dates = [self.kb.get_data_for(candidate, "ZACATEK"), self.kb.get_data_for(candidate, "KONEC")]
   
        for context_date in self.people_dates[par_index]:
            for org_date in org_dates:
                if (context_date.find(org_date) > -1 or org_date.find(context_date) > -1) and org_date:
                    # the person has the date mentioned in this paragraph
                    org_date_score += 1
        if self.people_dates[par_index]:
            # normalizing people_date_score
            org_date_score = org_date_score * 100 / len(self.people_dates[par_index])
        
        
        result = (mentioned_in_par_score + place_score + org_date_score) / 3

        return result

    def prot_area_percentile(self, candidate):
   
        area_name = [self.kb.get_data_for(candidate, "NAZEV")]
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:protectedArea')

        #if area_name in self.mentions[par_index]['geoplace:protectedArea']:
        #    mentioned_in_par_score = self.mentions[par_index]['geoplace:protectedArea'][area_name] * 100 / sum(self.mentions[par_index]['geoplace:protectedArea'].values())

        place_score = 0
        places = self.kb.get_data_for(candidate, "LOKALITA")
        if(places):
            places = places.split('|')
            place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')
            
        #    print(places)
        #    for place in places:
        #        if place in self.mentions[par_index]["geoplace:populated_place"]:
        #            place_score = self.mentions[par_index]["geoplace:populated_place"][place]
        #            break
        #
        #if place_score:
        #    place_score = place_score * 100 / self.country_sum[par_index]

        result = (mentioned_in_par_score + place_score) / 2

        return result

    def con_area_percentile(self, candidate):

        
        area_name = [self.kb.get_data_for(candidate, "NAZEV")]
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:conservationArea')

        #if area_name in self.mentions[par_index]['geoplace:conservation_area']:
        #    mentioned_in_par_score = self.mentions[par_index]['geoplace:conservation_area'][area_name] * 100 / sum(self.mentions[par_index]['geoplace:conservation_area'].values())

        place_score = 0
        places = [self.kb.get_data_for(candidate, "OKRES")]
        locations = self.kb.get_data_for(candidate, "UMISTENI")
        if locations:
            places.extend(locations.split('|'))
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

       #if places:
       #    for place in places:
       #        if place in self.mentions[par_index]["geoplace:populated_place"]:
       #            place_score = self.mentions[par_index]["geoplace:populated_place"][place]
       #            break
       #if place_score:
       #    place_score = place_score * 100 / self.country_sum[par_index]

        result = (mentioned_in_par_score + place_score) / 2

        return result

    def mountain_percentile(self, candidate):

        area_name = [self.kb.get_data_for(candidate, "NAZEV")]
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:mountain')

        #if area_name in self.mentions[par_index]['geoplace:mountain']:
        #    mentioned_in_par_score = self.mentions[par_index]['geoplace:mountain'][area_name] * 100 / sum(self.mentions[par_index]['geoplace:mountain'].values())

        place_score = 0
        places = [self.kb.get_data_for(candidate, "SVETADIL")]
        locations = self.kb.get_data_for(candidate, "STAT")
        if locations:
            places.extend(locations.split('|'))
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        #if places:
        #    for place in places:
        #        if place in self.mentions[par_index]["geoplace:populated_place"]:
        #            place_score = self.mentions[par_index]["geoplace:populated_place"][place]
        #            break
#
        #if place_score:
        #    place_score = place_score * 100 / self.country_sum[par_index]

        result = (mentioned_in_par_score + place_score) / 2

        return result

    def castle_percentile(self, candidate):

        area_name = [self.kb.get_data_for(candidate, "NAZEV")]
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:castle')

        #if area_name in self.mentions[par_index]['geoplace:castle']:
         #   mentioned_in_par_score = self.mentions[par_index]['geoplace:castle'][area_name] * 100 / sum(self.mentions[par_index]['geoplace:castle'].values())

        place_score = 0
        places = [self.kb.get_data_for(candidate, "STAT")]
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')
        #if places:
        #    for place in places:
        #        if place in self.mentions[par_index]["geoplace:populated_place"]:
        #            place_score = self.mentions[par_index]["geoplace:populated_place"][place]
        #            break
        #            
        #if place_score:
        #    place_score = place_score * 100 / self.country_sum[par_index]
#
        result = (mentioned_in_par_score + place_score) / 2

        return result

    def lake_percentile(self, candidate):

        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:lake')

        #if area_name in self.mentions[par_index]['geoplace:lake']:
        #   mentioned_in_par_score = self.mentions[par_index]['geoplace:lake'][area_name] * 100 / sum(self.mentions[par_index]['geoplace:lake'].values())

        place_score = 0
        places = []
        locations = self.kb.get_data_for(candidate, "OBEC")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "OKRES")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "STAT")
        if locations:
            places.extend(locations.split('|')) 
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        #if places:
        #    for place in places:
        #        if place in self.mentions[par_index]["geoplace:populated_place"]:
        #            place_score = self.mentions[par_index]["geoplace:populated_place"][place]
        #            break
        #            
        #if place_score:
        #    place_score = place_score * 100 / self.country_sum[par_index]
#
        result = (mentioned_in_par_score + place_score) / 2

        return result

    def forest_percentile(self, candidate):
        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:forest')

        places = []
        locations = self.kb.get_data_for(candidate, "OBEC")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "OKRES")
        if locations:
            places.extend(locations.split('|'))
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        result = (mentioned_in_par_score + place_score) / 2
        return result

    def mountain_pass_percentile(self, candidate):
        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:mountainPass')

        places = []
        locations = self.kb.get_data_for(candidate, "1_STAT")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "2_STAT")
        if locations:
            places.extend(locations.split('|'))
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        result = (mentioned_in_par_score + place_score) / 2
        return result


    def mountain_range_percentile(self, candidate):
        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geo:mountainRange')

        places = [self.kb.get_data_for(candidate, "STAT")]
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        result = (mentioned_in_par_score + place_score) / 2
        return result

    def river_percentile(self, candidate):
        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geo:river')

        result = mentioned_in_par_score
        return result

    def observation_tower_percentile(self, candidate):
        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geoplace:observationTower')

        places = []
        locations = self.kb.get_data_for(candidate, "KRAJ")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "OKRES")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "STAT")
        if locations:
            places.extend(locations.split('|'))
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        result = (mentioned_in_par_score + place_score) / 2
        return result

    def waterfall_percentile(self, candidate):
        area_name = self.kb.get_data_for(candidate, "NAZEV")
        mentioned_in_par_score = self.mentioned_in_par(area_name, 'geo:waterfall')

        places = []
        locations = self.kb.get_data_for(candidate, "OBECK")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "OKRES")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "KRAJ")
        if locations:
            places.extend(locations.split('|'))
        locations = self.kb.get_data_for(candidate, "STAT")
        if locations:
            places.extend(locations.split('|'))
        place_score = self.mentioned_in_par(places, 'geoplace:populatedPlace')

        result = (mentioned_in_par_score + place_score) / 2
        return result


    def init_pronouns(self):
        """ Initializes pronoun variables. """

        self.before_last_person = None
        self.last_person = None
        self.last_male = None
        self.last_female = None
        self.last_unknown_gender = None
        self.last_location = None
        self.before_last_male = None
        self.before_last_female = None

def offsets_of_paragraphs(input_string):
    """ Returns a list of starting offsets of each paragraph in input_string. """
    assert isinstance(input_string, unicode)
    
    result = [0]
    result.extend((par_match.end() for par_match in re.finditer(r"\r\n[\r\n]+", input_string)))
    return result

#example:
    """
    Martin Havelka je ........ M. Havelka bol ....... .

    
    Maros Havelka .................


    ..... M. Havelka ......


    """

def fix_poor_disambiguation(entities, context):
    """ Fixes the entity sense if poorly_disambiguated is set to True. """
    assert isinstance(entities, list) # list of Entity
    assert isinstance(context, Context)

    strong_entities = {}
    strong_entities_by_id = {}
    entities = [e for e in entities if isinstance(e, Entity) and not e.is_coreference]

    for e in entities:
        if not e.poorly_disambiguated:
            if e.source not in strong_entities:
                strong_entities[e.source] = []
            strong_entities[e.source].append(e.get_preferred_entity())

            if e.get_preferred_sense() not in strong_entities_by_id:
                strong_entities_by_id[e.get_preferred_sense()] = []
            strong_entities_by_id[e.get_preferred_sense()].append(e.get_preferred_entity())

    for e in entities:
        if e.poorly_disambiguated:
            candidates = []   
            for s in e.senses:
                if s in strong_entities_by_id:
                    candidates += strong_entities_by_id[s]
            
            if candidates != []:
                e.set_preferred_sense(get_nearest_entity(e, candidates))
                e.poorly_disambiguated = False
            elif e.source in strong_entities:
                e.set_preferred_sense(get_nearest_entity(e, strong_entities[e.source]))
                e.poorly_disambiguated = False

def add_unknown_names(kb, entities_and_dates, input_string, input_string_in_unicode, register):
    """ Finding unknown names. """
    assert isinstance(kb, ner_knowledge_base.KnowledgeBaseCZ)
    assert isinstance(entities_and_dates, list) # list of Entity and dates.Date
    assert isinstance(input_string, str)
    assert isinstance(input_string_in_unicode, unicode)
    assert isinstance(register, EntityRegister)

    global output

    nr = name_recognizer.NameRecognizer()
    try:
        data_rows = nr.recognize_names(input_string, figa_out=output)
    except Exception:
        return

    name_entities = []

    for dr in data_rows:
        name_entities.append(Entity.from_data_row(kb, dr, input_string,
            input_string_in_unicode, register))

    new_name_entities = []

    for i in range(len(name_entities)):
        assigned = None
        for j in range(0, i):
            if name_entities[i].source == name_entities[j].source:
                assigned = name_entities[j].senses
                break

        if assigned:
            name_entities[i].senses = assigned.copy()
        else:
            name_entities[i].senses = set([-(i+1)])

    # resolving overlapping names
    for ne in name_entities:
        substring   = False
        overlapping = False
        overlaps    = []
        for ed in entities_and_dates:
            if not isinstance(ed, Entity):
                continue

            if ne.is_equal(ed) or  ed.is_overlapping(ne):
                substring = True
                break
            elif ne.is_overlapping(ed):
                overlapping = True
                overlaps.append(ed)
        if not (substring or overlapping):
            new_name_entities.append(ne)
        elif overlapping:
            senses = set()
            for o in overlaps:
                senses = senses | o.senses
                entities_and_dates.remove(o)
            ne.senses = senses.copy()
            new_name_entities.append(ne)

    # inserting names into entity list
    for nne in new_name_entities:
        for i in range(len(entities_and_dates)):
            if i == len(entities_and_dates)-1:
                entities_and_dates.append(nne)
                break
            elif nne.start_offset >= entities_and_dates[i].start_offset and \
            nne.start_offset < entities_and_dates[i+1].start_offset:
                entities_and_dates.insert(i+1, nne)
                break
            elif nne.start_offset < entities_and_dates[0].start_offset:
                entities_and_dates.insert(0, nne)
                break

    adjust_coreferences(entities_and_dates, new_name_entities)

def adjust_coreferences(entities_and_dates, new_name_entities):
    ed            = entities_and_dates
    names         = new_name_entities
    wanted_corefs = ["on", "ho", "mu", "o něm", "jím", "ona", "jí", "o ní"]

    ed_size       = len(ed)

    if not ed:
        return

    for n in names:
        i_prev = None
        i_next = None
        index  = None

        for i in range(ed_size):
            if ed[i] == n:
                index = i
                break

        for i in range(index+1, ed_size):
            if isinstance(ed[i], Entity) and ed[i].is_person():
                i_next = i
                break

        for i in range(index-1, -1, -1):
            if isinstance(ed[i], Entity) and ed[i].is_person():
                i_prev = i
                break

        # Nothing to do here
        if i_next == None: break
        if ed[i_next].is_name: continue

        for i in range(index+1, i_next or ed_size):
            if isinstance(ed[i], Entity) and ed[i].is_coreference and \
            ed[i].source.lower() in wanted_corefs:
                if len(n.senses) == 0:
                    continue
                sense   = ed[i].get_preferred_sense()
                n_sense = list(n.senses)[0]
                if not i_prev:
                    ed[i].set_preferred_sense(n_sense)
                elif len(ed[i_prev].senses) > 0 and \
                sense == list(ed[i_prev].senses)[0] and sense != n_sense:
                        ed[i].set_preferred_sense(n_sense)

def resolve_coreferences(entities, context, print_all, register):
    """ Resolves coreferences. """
    assert isinstance(entities, list) # list of Entity
    assert isinstance(context, Context)
    assert isinstance(print_all, bool)
    assert isinstance(register, EntityRegister)
    
    for e in entities:
        # adding propriate candidates into people set
        if not e.is_coreference and e.has_preferred_sense():
            ent_type = e.kb.get_ent_type(e.get_preferred_sense())
            if ent_type in ['person']:
                context.people_in_text.add(e.get_preferred_sense())

    for e in entities:   
        if e.is_coreference:
            # coreferences by a name to p eople out of context are discarded
            if not print_all:
                e.partial_match_senses = set([s for s in e.partial_match_senses if s in context.people_in_text])
                if e.partial_match_senses:
                    # choosing the candidate with the highest confidence score
                    #sense = sorted(list(e.partial_match_senses), key=lambda candidate: context.kb.get_score(candidate), reverse=True)[0]
                    candidates = []
                    for sense in e.partial_match_senses:
                        candidates += list(register.id2entity[sense])
                    
                    # each candidate has to contain the text of a given entity
                    candidates = (c for c in candidates if remove_accent(e.source).lower() in remove_accent(c.source).lower())
                    # choosing the nearest predecessor candidate for a coreference
                    entity = get_nearest_predecessor(e, candidates)
                    if entity:
                        e.set_preferred_sense(entity)
                elif e.source.lower() in PRONOUNS:
                	e.resolve_pronoun_coreference(context)
                elif e.senses:
                    e.is_coreference = False
                    e.disambiguate_without_context()
                    e.disambiguate_with_context(context)
        if e.has_preferred_sense():
            context.update(e)


def get_nearest_predecessor(_entity, _candidates):
    """ Returns the nearest predecessor for a given entity from a given list of candidates. """
    assert isinstance(_entity, Entity)
    assert isinstance(_candidates, collections.Iterable) # iterable of Entity
    
    # sorting candidates according to the distance from a given entity # NOTE: Nešlo by to napsat lépe?
    candidates = sorted(_candidates, key=lambda candidate: _entity.start_offset - candidate.start_offset)
    for candidate in candidates:
        if _entity.start_offset - candidate.start_offset > 0:
            return candidate

def get_nearest_entity(_entity, _candidates):
    """ Returns the nearest entity for a given entity from a given list of candidates. """
    assert isinstance(_entity, Entity)
    assert isinstance(_candidates, collections.Iterable) # iterable of Entity
    
    # sorting candidates according to the distance from a given entity
    candidates = sorted(_candidates, key=lambda candidate: abs(_entity.start_offset - candidate.start_offset))
    
    return candidates[0].preferred_sense

seek_names = None
output = None

def get_entities_from_figa(kb, input_string, input_string_in_unicode, lowercase, global_senses, register):
    """ Returns the list of Entity objects from figa. """ # TODO: Možná by nebylo od věci toto zapouzdřit do třídy jako v "get_entities.py".
    assert isinstance(kb, ner_knowledge_base.KnowledgeBaseCZ)
    assert isinstance(input_string, str)
    assert isinstance(input_string_in_unicode, unicode)
    assert isinstance(lowercase, bool)
    assert isinstance(global_senses, set)
    assert isinstance(register, EntityRegister)

    global seek_names
    global output

    if not seek_names:
        seek_names = figa.marker()

        lower = ""
        if lowercase:
            lower = "-lower"

        seek_names.load_dict(os.path.dirname(os.path.realpath(__file__)) + "/figa/automata" + lower + ".ct")

    # getting data from figa
    if lowercase:
    	output = seek_names.lookup_string(input_string.lower())
    else:
    	output = seek_names.lookup_string(input_string)
    entities = []

    # processing figa output and creating Entity objects
    #print(output)
    for line in output.split("\n")[:-1]:
        entity_attributes = line.split('\t')
    	e = Entity(entity_attributes, kb, input_string, input_string_in_unicode, register)
    	global_senses.update(e.senses)
    	entities.append(e)
    
    return entities

def remove_shorter_entities(entities):
    """ Removing shorter entity from overlapping entities. """
    assert isinstance(entities, list) # list of Entity
    
    # figa should always return the longest match first
    entity_offsets = set()
    new_entities = []
    for e in entities:
        current_offset = set(range(e.start_offset, e.end_offset + 1))
        if current_offset & entity_offsets == set():
            entity_offsets.update(current_offset)
            new_entities.append(e)
    return new_entities

def recognize(kb, input_string, print_all=False, print_result=True, print_score=False, lowercase=False, remove=False, split_interval=True, find_names=False):
    """
    Prints a list of entities found in input_string.

    kb - a knowledge base
    print_all - if false, all entities are disambiguated
    print_result - if True, the result is both returned as a list of entities and printed to stdout; otherwise, it is only returned
    print_score - similar to print_all, but also prints the score for each entity alternative
    lowercase - the input string is lowercased
    remove - removes accent from the input string
    split_interval - split dates intervals in function dates.find_dates()
    """
    assert isinstance(kb, ner_knowledge_base.KnowledgeBaseCZ)
    assert isinstance(input_string, str)
    assert isinstance(print_all, bool)
    assert isinstance(print_result, bool)
    assert isinstance(print_score, bool)
    assert isinstance(lowercase, bool)
    assert isinstance(remove, bool)
    assert isinstance(split_interval, bool)
    assert isinstance(find_names, bool)
    
    def debugChangesInEntities(entities, responsible_line):
        if debug.DEBUG_EN:
            global debug_last_status_of_entities
            if "debug_last_status_of_entities" in globals():
                new_status_of_entities = [e+"\n" for e in map(str, sorted(entities, key=lambda ent: ent.start_offset))]
                print_dbg_en(responsible_line, "".join(difflib.unified_diff(debug_last_status_of_entities, new_status_of_entities, fromfile='before', tofile='after', n=0))[:-1], delim="\n", stack_num=2)
                debug_last_status_of_entities = new_status_of_entities
            else:
                debug_last_status_of_entities = [e+"\n" for e in map(str, sorted(entities, key=lambda ent: ent.start_offset))]
    
    # replacing non-printable characters and semicolon with space characters
    input_string = re.sub("[;\x01-\x08\x0e-\x1f\x0c\x7f]", " ", input_string)
    # input_string in Unicode
    input_string_in_unicode = input_string.decode("utf8", "replace")
    # running with parametr --remove_accent
    if remove:
        input_string = remove_accent(input_string)

    # creating entity register
    register = EntityRegister()
    # a set of all possible senses
    global_senses = set()
    # getting entities from figa
    figa_entities = get_entities_from_figa(kb, input_string, input_string_in_unicode, lowercase, global_senses, register)
     
    # retaining only possible coreferences for each entity
    for e in figa_entities:
        e.partial_match_senses = e.partial_match_senses & global_senses

    # removing shorter entity from overlapping entities
    figa_entities = remove_shorter_entities(figa_entities)
    #debugChangesInEntities(entities, linecache.getline(__file__, inspect.getlineno(inspect.currentframe())-1))

    # removing entities without any sense
    nationalities = []
    entities = []
    for e in figa_entities:
        if e.is_nationality:
            nationalities.append(e)
        elif e.senses or e.partial_match_senses or e.source.lower() in PRONOUNS:
            entities.append(e)

    #entities = [e for e in entities if e.senses or e.partial_match_senses or e.source.lower() in PRONOUNS]
    #debugChangesInEntities(entities, linecache.getline(__file__, inspect.getlineno(inspect.currentframe())-1))

    # searches for dates and intervals in the input
    dates_and_intervals = dates.find_dates(input_string_in_unicode, split_interval=split_interval)

    # resolving overlapping dates and entities
    entity_offsets = set()
    for e in entities:
        entity_offsets.update(set(range(e.start_offset, e.end_offset + 1)))
    dates_and_intervals = [d for d in dates_and_intervals if set(range(d.start_offset, d.end_offset + 1)) & entity_offsets == set()]

    # merges entities with dates
    entities_and_dates = []
    entities_and_dates.extend(dates_and_intervals)
    entities_and_dates.extend(entities)

    # sorts entities and dates according to their start offsets
    entities_and_dates.sort(key=lambda ent : ent.start_offset)

    #for e in entities:
    #    for s in e.senses:
    #        print(e.kb.get_ent_type(s) + "  " + str(e.kb.get_data_for(s,'NAZEV')) + "  " + e.source)

    # disambiguates without context
    [e.disambiguate_without_context() for e in entities]

    paragraphs = offsets_of_paragraphs(input_string_in_unicode)
    context = Context(entities_and_dates, kb, paragraphs, nationalities)

    # disambiguates with context
    [e.disambiguate_with_context(context) for e in entities]
    #debugChangesInEntities(entities, linecache.getline(__file__, inspect.getlineno(inspect.currentframe())-1))
    fix_poor_disambiguation(entities, context)
    #debugChangesInEntities(entities, linecache.getline(__file__, inspect.getlineno(inspect.currentframe())-1))

    name_coreferences = [e for e in entities if e.source.lower() not in PRONOUNS]
    #resolve_coreferences(name_coreferences, context, print_all, register) # Zde se ověřuje, zda-li části jmen jsou odkazy nebo samostatné entity.
    resolve_coreferences(entities, context, print_all, register)

    # updating entities_and_dates
    entities_and_dates = [e for e in entities_and_dates if isinstance(e, dates.Date) or e in entities]

    # finding unknown names
    if find_names:
        add_unknown_names(kb, entities_and_dates, input_string, input_string_in_unicode, register)

    # omitting entities whithout a sense
    if entities_and_dates:
        if not print_all:
            entities_and_dates = [e for e in entities_and_dates if isinstance(e, dates.Date) or e.has_preferred_sense() or e.is_name]
        else:
            for e in entities_and_dates:
                if isinstance(e, Entity):
                    e.set_preferred_sense(None)
            entities_and_dates = [e for e in entities_and_dates if isinstance(e, dates.Date) or (e.is_coreference and e.partial_match_senses) or (not e.is_coreference and e.senses) or e.is_name]

    if print_score:
        global display_entity_score
        display_entity_score = True

    if print_result:
        print("\n".join(map(str, entities_and_dates)))

    return entities_and_dates
	

def main():
    # argument parsing
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-a', '--all', action='store_true', default=False, dest='all', help='Prints all entities without disambiguation.')
    group.add_argument('-s', '--score', action='store_true', default=False, dest='score', help='Prints all possible senses with respective score values.')
    parser.add_argument('-d', '--daemon-mode', action='store_true', default=False, help='Runs ner.py in daemon mode.')
    parser.add_argument('-f', '--file',  help='Uses a given file as as an input.')
    parser.add_argument('-r', '--remove-accent', action='store_true', default=False, help="Removes accent in input.")
    parser.add_argument('-l', '--lowercase', action='store_true', default=False, help="Changes all characters in input to the lowercase characters.")
    parser.add_argument('-n', '--names', action='store_true', default=False, help="Recognizes and prints all names with start and end offsets.")
    parser.add_argument("--own_kb_daemon", action="store_true", dest="own_kb_daemon", help=("Run own KB daemon although another already running."))

    arguments = parser.parse_args()
    # allowed tokens for daemon mode
    tokens = set(["NER_NEW_FILE", "NER_END", "NER_NEW_FILE_ALL", "NER_END_ALL", "NER_NEW_FILE_SCORE", "NER_END_SCORE", "NER_NEW_FILE_NAMES", "NER_END_NAMES"])

    # loading knowledge base
    if arguments.own_kb_daemon:
        kb_daemon_run = True
        while kb_daemon_run:
            kb_shm_name = "/decipherKB-CZ-daemon_shm-%s" % uuid.uuid4()
            kb = ner_knowledge_base.KnowledgeBaseCZ(kb_shm_name=kb_shm_name)
            kb_daemon_run = kb.check()
    else:
        kb_shm_name = "/decipherKB-CZ-daemon_shm-999"
        kb = ner_knowledge_base.KnowledgeBaseCZ(kb_shm_name=kb_shm_name)

    try:
        kb.start()
        kb.initName_dict()

        if arguments.daemon_mode:
            input_string = ""
            while True:
                line = sys.stdin.readline().rstrip()
                if line in tokens:
                    if "ALL" in line:
                        recognize(kb, input_string, print_all=True, lowercase=arguments.lowercase, remove=arguments.remove_accent)
                    elif "SCORE" in line:
                        recognize(kb, input_string, print_score=True, lowercase=arguments.lowercase, remove=arguments.remove_accent)
                    elif "NAMES" in line:
                        recognize(kb, input_string, find_names=True, lowercase=arguments.lowercase, remove=arguments.remove_accent)
                    else:
                        recognize(kb, input_string, print_all=False, lowercase=arguments.lowercase, remove=arguments.remove_accent)
                    print(line)
                    sys.stdout.flush()
                    input_string = ""
                    if "END" in line:
                        break
                else:
                    input_string += line + "\n"
        else:
            # reading input data from file
            if arguments.file:
                with open(arguments.file) as f:
                    input_string = f.read()
            # reading input data from stdin
            else:
                input_string = sys.stdin.read()
            input_string = input_string.strip()
            recognize(kb, input_string, print_all=arguments.all, print_score=arguments.score, lowercase=arguments.lowercase, remove=arguments.remove_accent, find_names=arguments.names)
    finally:
        kb.end()

if __name__ == "__main__":

    main()
