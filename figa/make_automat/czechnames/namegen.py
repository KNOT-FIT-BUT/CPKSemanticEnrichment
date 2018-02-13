import sys
from collections import defaultdict
import argparse
import fileinput
import re
import os
# path to gen_wordform
sys.path.insert(0, '/mnt/minerva1/nlp/projects/ma/data/morph/scripts/')
import gen_wordform

paradigms = "/mnt/minerva1/nlp/projects/ma/data/morph/czech.paradigms"
lpn =          "/mnt/minerva1/nlp/projects/ma/data/morph/czech_vc_prijmeni_navic.lpn"

output_file = sys.stdout
nozk = False

unknowns = set()

trs4p = None
pns4l = None

class name:

	def __init__(self, line):
		gettype.prep_phrase = False
		self.parts = list() # list of lists (im too lazy to make a dict here) (slovo, oddelovac, znacka, tvary)
		self.gender = None
		
		words = line.split()
		
		
		if words[-1] in ["M", "F"]:
			self.gender = words.pop()
		
		for word in words:
			if word.find("-") > 0:
				for i, wrd in enumerate(word.split("-")):
					kategorie = gettype(wrd)
					if kategorie == "d'S":
						wrd = wrd[2:]
					if i == 0:
						self.parts.append([wrd, " ", kategorie, None])
					else:
						self.parts.append([wrd, "-", kategorie, None])
				
			else:
				kategorie = gettype(word)
				if kategorie == "d'S":
					word= word[2:]
					
				self.parts.append([word, " ", kategorie, None])
			if gettype.prep_phrase == True:
				self.parts[-1][2] = ""
		
		if not self.gender:
			self.gender = get_gender(words)
		
		if not self.gender:
			out = ""
			for word in self.parts:
				out += word[1] + word[0]
			raise Exception("Unknown gender, skipping: " + out +"\n")
			
			
		for item in self.parts[::-1]:
			if item == self.parts[0]:
				break
			if item[2] == "G":
				item[2] = "S"
				break
			
	def get_unknowns(self, unknowns):
		for i, part in enumerate(self.parts):
			try:
				if part[0] not in pns4l:
					unknowns.add((part[0], self.gender, "s"+self.gender))
				else:
					for pair in pns4l[part[0]]:
						if "s"+self.gender != pair[1]:
							unknowns.add((part[0], self.gender, "s"+self.gender))
			except Exception as e:
				sys.stderr.write(str(e))
				
	def generate(self):
		for i, part in enumerate(self.parts):
			if part[2] in ["T", "P", "C", "N", ""]:
				self.parts[i][3] = [[part[0]] for i in range(7)]
			else:
				self.parts[i][3] = [flex_word(part[0], self.gender, pad) for pad in range(1, 8)]
				
	def __str__(self):
		tvary = list()
		
		for pad in range(7):
			tvary.append(set())
			for word in self.parts:
				tvary[-1] = add_next_word(tvary[-1], word[3][pad], word[1], word[2])
		out = ""
		for word in self.parts:
			if word[2] == "d'S":
				out += word[1] + "d'" + word[0]
			else:		
				out += word[1] + word[0]
		
		out += "\t" + self.gender + "\t"

		out = out[1:]
		
		if nozk:
			out_set = set()
			for tvary_pad in tvary:
				for tvar in tvary_pad:
					out_set.add(tvar)
			out += "|".join(out_set)
			return out
			
		else:
			out_arr = list()
			for pad in range(7):
				for tvar in tvary[pad]:
					kategorie = ""
					for part in self.parts:
						if part[1] != " ":
							kategorie += part[1]
						if part[2] == "d'":
							kategorie += "d'"
						if part[2]:
							kategorie += part[2]
						
					out_arr.append(tvar+"#" + "k1g" + self.gender + "nSc" + str(pad+1) + "#" + kategorie)
			
			out += "|".join(out_arr)
			return out

			
def load_trs4p_pns4l (para_filename, lpn_filename):
    trs4p={}
    with open(para_filename) as parafile:
        for line in parafile:
            line = line.rstrip()
            paradigm, tag_of_lemma, longest_remove, tags_and_rules, *_ = line.split('\t')
            # exclude paradigms for surnames
            if not ('gR' in paradigm):
                trs4p[paradigm] = tags_and_rules

    # known paradigms (and notes) corresponding to a given lemma
    pns4l = defaultdict(set)
    with open(lpn_filename) as lpnfile:
        for line in lpnfile:
            line = line.rstrip()
            lemma, paradigm, note = line.split('#')
            if paradigm in trs4p:
                pns4l[lemma].add((paradigm,note))

    return trs4p, pns4l
	

def add_next_word(seznam, seznam2, separator, znacka):
	combinations = set()
	if seznam:
		for a in seznam:
			for b in seznam2:
				if znacka == "d'S":
					b = "d'" + b
				combinations.add(a+separator+b)
	else:
		return set(seznam2)
	return combinations

	
def flex_word(word, rod, pad):
	operation = "k1g" + rod + "nSc" + str(pad)
	return list(set(gen_wrap(lemma = word, tag_filter = operation, trs4p = trs4p, pns4l = pns4l)))

#funkce přebrána ze skriptu gen_wordform, a upravena o to if s wH tagem
def gen_wrap(lemma, tag_filter, pns4l, trs4p):
	for (paradigm,note) in pns4l[lemma]:
		for tag_and_rule in trs4p[paradigm].split(' '):
			tag, remove, prefix_suffix = tag_and_rule.split(':')
			if re.search(tag_filter,tag): 
				if not re.search("wH", tag):
					yield gen_wordform.wordform_from_lemma_and_rule(lemma, remove, prefix_suffix)
	
		
def gettype(word):
	if gettype.prep_phrase:
		return
	
	if word[-3:] == "ová":
		return "S"
	
	if word[:2] == "d'" or word[:2] == "D'":
		return "d'S"
	if word[-1:] == ".":
		return "T"
	
	if word not in pns4l:
		return "G"
		
	else :
		if pns4l[word]:
			rozbor = [para for para, note in pns4l[word]]
		else:
			return "G"
	
	slovni_druh = [trs4p[para].split(' ')[0][:2] for para in rozbor]

	if "k1" in slovni_druh:
		return "G"
	if "k2" in slovni_druh:
		return "S"
	if "k4"in slovni_druh:
		return "N"
	if "k6" in slovni_druh:
		return "S"
	if "k7" in slovni_druh:
		gettype.prep_phrase = True
		return "P"
	if "k8" in slovni_druh:
		gettype.prep_phrase = True
		return "C"
	if "kA" in slovni_druh:
		return "T"
	else:
		return slovni_druh[0]

def init(args):
	global trs4p
	global pns4l
	global output_file
	global nozk
	global paradigms
	global lpn
	
	if args.parafile:
		paradigms = args.parafile
	if args.lpnfile:
		lpn = args.lpnfile
	
	nozk = args.short
	trs4p, pns4l = load_trs4p_pns4l (paradigms, lpn)
		
	gettype.prep_phrase = False
	
	try: 
		if args.output:
			output_file =  open(args.output, 'w')
	except Exception as e:
		sys.stderr.write(str(e))
		close_IO()
		exit(2)

def add_lpn(lpn):
	global pns4l
	
	with open(lpn) as lpnfile:
		for line in lpnfile:
			line = line.rstrip()
			lemma, paradigm, note = line.split('#')
			
			if paradigm in trs4p:
				pns4l[lemma].add((paradigm,note))
			
# urceni pohlavi jmena	
def get_gender(jmeno):
	gender = None
	for word in jmeno:
		if word in pns4l:
			p = next(iter(pns4l[word]))[0]
			g = trs4p[p][3]
			if not gender:
				gender = g
			elif gender != g:
				sys.stderr.write("Warning, inconsistent gender (" + jmeno[-1] + ") for name: " + ' '.join(jmeno[:-1]) + "\n")
		elif word[-3:] == "ová":
			return "F"
	if not gender:
		return None
	
	return gender[-1]
		
# uklid
def close_IO():
		try:
			output_file.close()
		except Exception:
			pass

def load(unknownargs):
	names = list()
	for line in fileinput.input(unknownargs):
		try:
			line = line.strip()
			if line:
				names.append(name(line))
		except Exception as e:
			print("Load")
			sys.stderr.write(str(e)+"\n")
	return names
	
def make_lntrf(names):
	global unknowns
	
	for n in names:
		n.get_unknowns(unknowns)

	with open("namegen.unknown.lntrf", 'w') as lntrf:
		if unknowns:
			for word in unknowns:
				lntrf.write(word[0] + "\t" + word[2] + "\t" + "k1g"+word[1]+"nSc1::\n")

def generate(names):
	for n in names:
		n.generate()

def print_names(names):
	for n in names:
		output_file.write(str(n) + "\n")

def make_lpn():
	os.system("/mnt/minerva1/nlp/projects/ma/data/morph/scripts/lntrf2lpn.py -l /mnt/minerva1/nlp/projects/ma/data/morph/prijmeni_navic.lpn -g guesser -e explainer namegen.unknown.lntrf > namegen.unknown.lpn 2> namegen.unknown.guess_err")
	
	
	
def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--output", help="Vystupni soubor", type=str)
	parser.add_argument("-p", "--parafile", help="Soubor se vzory", type=str)
	parser.add_argument("-l", "--lpnfile", help="Soubor obsahující vzory slov", type=str)
	parser.add_argument("-s","--short",  help="Moznost vypisu bez znacek", action="store_true")
   
	return parser.parse_known_args()
	
def main(argv):
	args, unknownargs = get_args()
	init(args)
	names = load(unknownargs)
	make_lntrf(names)
	make_lpn()
	add_lpn("namegen.unknown.lpn")
	generate(names)
	print_names(names)
	close_IO()

def get_alternatives(name_list):
	args, unknownargs = get_args()
	init(args)
	names = list()
	for line in name_list:
		names.append(name(line))

	make_lntrf(names)
	make_lpn()
	add_lpn("namegen.unknown.lpn")
	generate(names)

	output = '\n'.join([str(n) for n in names])
	#print_names(names)
	close_IO()
	return output

if __name__ == "__main__":
	sys.exit(main(sys.argv))
