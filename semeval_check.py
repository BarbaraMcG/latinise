# This script runs some checks on the subcorpora prepared for SemEval 2020 task 1
# Initial version by Simon Hengchen
# Python version: 3

import os
import sys

print("you need to run this from a folder that contains other folders: 'sem_eval_ger', 'sem_eval_swe' etc")
print("add any combination of [ger|swe|lat|eng] in argv\n")

import os
import csv
import datetime
import re
from collections import Counter
import locale
import xlrd
from pandas import read_excel
import random

now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 10000 # number of lines read when testing

langs = sys.argv[1:]
corpora = ["corpus1","corpus2"]

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")
dir_annotation = os.path.join(directory, "Semantic annotation", "Annotated data", "selected")
dir_corpus = os.path.join(directory, "LatinISE 4")
dir_corpus2 = os.path.join(directory, "LatinISE 4", "for Codalab")

# Files:
latinise_file_name = "latin13.txt"
dates_file_name = "LatinISE_dates.txt"
bc_subcorpus_name = "LatinISE_subcorpus1.txt"
ad_subcorpus_name = "LatinISE_subcorpus2.txt"
bc_subcorpus_dates_name = "LatinISE_subcorpus1_dates.txt"
ad_subcorpus_dates_name = "LatinISE_subcorpus2_dates.txt"
bc_subcorpus_dates_shuffled_name = "LatinISE_subcorpus1_dates_shuffled.txt"
ad_subcorpus_dates_shuffled_name = "LatinISE_subcorpus2_dates_shuffled.txt"
bc_subcorpus_shuffled_name = "LatinISE_subcorpus1_shuffled.txt"
ad_subcorpus_shuffled_name = "LatinISE_subcorpus2_shuffled.txt"


if istest == "yes":
    bc_subcorpus_name = bc_subcorpus_name.replace(".txt", "_test.txt")
    ad_subcorpus_name = ad_subcorpus_name.replace(".txt", "_test.txt")
    bc_subcorpus_dates_name = bc_subcorpus_dates_name.replace(".txt", "_test.txt")
    ad_subcorpus_dates_name = ad_subcorpus_dates_name.replace(".txt", "_test.txt")
    bc_subcorpus_dates_shuffled_name = bc_subcorpus_dates_shuffled_name.replace(".txt", "_test.txt")
    ad_subcorpus_dates_shuffled_name = ad_subcorpus_dates_shuffled_name.replace(".txt", "_test.txt")
    bc_subcorpus_shuffled_name = bc_subcorpus_shuffled_name.replace(".txt", "_test.txt")
    ad_subcorpus_shuffled_name = ad_subcorpus_shuffled_name.replace(".txt", "_test.txt")


# -----------------
# Initial checks:
# -----------------

def check_file(path_in):
	dic_tokens = {}
	print("checking",path_in)
	with open(path_in) as f:
		x = 0
		y = 0
		for line in f.readlines():
			x += 1 
			tokens = line.split()
			if len(tokens) < 10:
				#print("SENTENCE SHORTER THAN TEN", line)
				y +=1
			for token in tokens:
				try:
					dic_tokens[token] += 1
				except KeyError:
					dic_tokens[token] = 1

		total_tokens = 0
		for key in dic_tokens:
			total_tokens += dic_tokens[key]

		print(x,"lines")
		print(len(list(dic_tokens.keys())),"types")
		print(total_tokens,"tokens")
		print(y,"sentences shorter than 10, or",y/x*100,"%")
		print("\n")


for lang in langs:
	for corpus in corpora:
		files = []
		for file in os.listdir(os.path.join("sem_eval_"+lang,corpus,"lemma")):
			if file.endswith(".txt"):
				files.append(os.path.join("sem_eval_"+lang,corpus,"lemma",file))
		print("Dealing with",lang,corpus)
		
		for file in sorted(files):
			check_file(file)


# ----------------------------------------------------------
# Check that all annotated sentences are in the subcorpora:
# ----------------------------------------------------------


# Found annotated words:

target_words = [] # list of annotated target words
control_words = [] # list of annotated control words
word2filename = dict() # maps an annotated word to its file name

# target words:
for word in os.listdir(os.path.join(dir_annotation, "target words")):
    if os.path.isdir(os.path.join(dir_annotation, "target words", word)):
        for file in os.listdir(os.path.join(dir_annotation, "target words", word)):
            if os.path.isfile(os.path.join(os.path.join(dir_annotation, "target words", word), file)) \
                    and file.lower().startswith("annotation_task") and file.endswith("_metadata.xlsx"):
                print(word)
                target_words.append(word)
                word2filename[word] = file


for word in os.listdir(os.path.join(dir_annotation, "control words")):
    if os.path.isdir(os.path.join(dir_annotation, "control words", word)):
        for file in os.listdir(os.path.join(dir_annotation, "control words", word)):
            if os.path.isfile(os.path.join(os.path.join(dir_annotation, "control words", word), file)) \
                    and file.lower().startswith("annotation_task") and file.endswith("_metadata.xlsx"):
                print(word)
                control_words.append(word)
                word2filename[word] = file

words = target_words + control_words

if istest == "yes":
    words = words[:2]
    target_words = target_words[:1]
    control_words = control_words[:1]

words_read = 0

left_contexts_bc = list() # list of all BC left contexts of annotated sentences
left_contexts_ad = list() # list of all AD left contexts of annotated sentences

for word in words:
    print("Word", word)
    path = ""
    if word in target_words:
        path = os.path.join(dir_annotation, "target words")
    else:
        path = os.path.join(dir_annotation, "control words")

    annotated_file_name = word2filename[word]
    #print("checking ", os.path.join(path, word, annotated_file_name))
    if os.path.isfile(os.path.join(path, word, annotated_file_name)) \
        and annotated_file_name.startswith("annotation_task") and annotated_file_name.endswith("_metadata.xlsx"):

        ann = read_excel(os.path.join(path, word, annotated_file_name), 'Annotation', encoding='utf-8')
        print(word)
        words_read += 1
        print(str(ann.shape[0]), "rows", ann.shape[1], "columns")
        columns = ann.columns.tolist()
        columns_lc = [c.lower() for c in columns]
        index_leftcontext = columns_lc.index("left context")
        index_era = columns_lc.index("era")

        eras = ann.iloc[0:61, index_era]
        eras = eras.dropna()
        left_contexts = ann.iloc[0:61, index_leftcontext]


        for index, row in left_contexts.iterrows():
            print(str(index), str(row[0]), str(left_contexts[index]), str(eras[index]))
            #left_contexts.append(left_context)
