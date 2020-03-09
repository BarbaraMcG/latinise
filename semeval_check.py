# This script runs some checks on the subcorpora prepared for SemEval 2020 task 1
# Initial version by Simon Hengchen
# Python version: 3

import os
import sys

# print("you need to run this from a folder that contains other folders: 'sem_eval_ger', 'sem_eval_swe' etc")
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
number_test = 10000  # number of lines read when testing

langs = sys.argv[1:]
corpora = ["corpus1", "corpus2"]

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute",
                         "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")
dir_annotation = os.path.join(directory, "Semantic annotation", "Annotated data", "selected")
dir_corpus = os.path.join(directory, "LatinISE 4")
dir_corpus2 = os.path.join(directory, "LatinISE 4", "for Codalab")
dir_corpus3 = os.path.join(dir_corpus2, "semeval2020_ulscd_lat")

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
output_file_name = "errors_annotation_corpus_sentences.txt"

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
    print("checking", path_in)
    with open(path_in) as f:
        x = 0
        y = 0
        for line in f.readlines():
            x += 1
            tokens = line.split()
            if len(tokens) < 3:
                # print("SENTENCE SHORTER THAN TEN", line)
                y += 1
            for token in tokens:
                try:
                    dic_tokens[token] += 1
                except KeyError:
                    dic_tokens[token] = 1

        total_tokens = 0
        for key in dic_tokens:
            total_tokens += dic_tokens[key]

        print(x, "lines")
        print(len(list(dic_tokens.keys())), "types")
        print(total_tokens, "tokens")
        print(y, "sentences shorter than 3, or", y / x * 100, "%")
        print("\n")


for lang in langs:
    for corpus in corpora:
        files = []
        for file in os.listdir(os.path.join(dir_corpus3, "corpus1", "lemma")):
            if file.endswith(".txt"):
                files.append(os.path.join(dir_corpus3, "corpus1", "lemma", file))
                print("Dealing with", lang, corpus)

        for file in os.listdir(os.path.join(dir_corpus3, "corpus2", "lemma")):
           if file.endswith(".txt"):
                files.append(os.path.join(dir_corpus3, "corpus2", "lemma", file))
                print("Dealing with", lang, corpus)

    for file in sorted(files):
        check_file(file)

# ----------------------------------------------------------
# Check that all annotated sentences are in the subcorpora:
# ----------------------------------------------------------


# Found annotated words:

target_words = []  # list of annotated target words
control_words = []  # list of annotated control words
word2filename = dict()  # maps an annotated word to its file name

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

left_contexts_bc = list()  # list of all BC left contexts of annotated sentences
left_contexts_ad = list()  # list of all AD left contexts of annotated sentences

for word in words:
    print("Word", word)
    path = ""
    if word in target_words:
        path = os.path.join(dir_annotation, "target words")
    else:
        path = os.path.join(dir_annotation, "control words")

    annotated_file_name = word2filename[word]
    # print("checking ", os.path.join(path, word, annotated_file_name))
    if os.path.isfile(os.path.join(path, word, annotated_file_name)) \
            and annotated_file_name.startswith("annotation_task") and annotated_file_name.endswith("_metadata.xlsx"):

        ann = read_excel(os.path.join(path, word, annotated_file_name), 'Annotation', encoding='utf-8')
        #print(word)
        words_read += 1
        #print(str(ann.shape[0]), "rows", ann.shape[1], "columns")
        columns = ann.columns.tolist()
        columns_lc = [c.lower() for c in columns]
        index_leftcontext = columns_lc.index("left context")
        index_era = columns_lc.index("era")

        eras = ann.iloc[0:61, index_era]
        eras = eras.dropna()
        left_contexts = ann.iloc[0:61, index_leftcontext]
        #print(str(left_contexts))

        count = 0
        for lc in left_contexts:
            if lc is not "":
                try:
                    era = eras[count]
                except:
                    print("error for era: word", word, str(count), lc)
                #print(str(lc), era)
                left_contexts_bc.append(lc)
                count += 1
                if era == "BC":
                    left_contexts_bc.append(lc)
                else:
                    left_contexts_ad.append(lc)
        #    print(str(index), str(row[0]), str(left_contexts[index]), str(eras[index]))
            # left_contexts.append(left_context)

# This functions checks if the left contexts from annotated sentences in a subcorpus are contained in the subcorpus file:

def check_annotated_sentences_in_corpus(era, left_contexts_list):
    lc2sentence = dict() # maps a left context to 1 if there is a sentence for it in the specific subcorpus, and 0 otherwise
    if era == "BC":
        path = "corpus1"
    else:
        path = "corpus2"
    for lc in left_contexts_list:
        found = 0
        for file in os.listdir(os.path.join(dir_corpus3, path, "lemma")):
            if file.endswith(".txt"):

                opened_file = open(os.path.join(dir_corpus3, path, "lemma", file), 'r', encoding="utf-8")

                for line in opened_file:
                    print("Checking line", str(line), "with", str(lc))
                    if lc in line:
                        found = 1

                opened_file.close()
            if found == 1:
                lc2sentence[lc] = 1
            else:
                lc2sentence[lc] = 0
    return lc2sentence

lc2sentence_bc = check_annotated_sentences_in_corpus("BC", left_contexts_bc)
lc2sentence_ad = check_annotated_sentences_in_corpus("AD", left_contexts_ad)

lc2sentence_all = dict() # maps a left context to 1 if there is a sentence for it in the corpus, and 0 otherwise
all_lc = list() # list of all left contexts
for lc in lc2sentence_bc:
    all_lc.append(lc)
for lc in lc2sentence_ad:
    all_lc.append(lc)

#all_lc = set(all_lc)
for lc in all_lc:
    found_bc = 0
    found_ad = 0
    if lc in lc2sentence_bc and lc2sentence_bc[lc] == 1:
        found_bc = 1
    if lc in lc2sentence_ad and lc2sentence_ad[lc] == 1:
        found_ad = 1
    if found_ad == 0 and found_ad == 0:
        lc2sentence_all[lc] = 0
    else:
        lc2sentence_all[lc] = 1

output_file = open(os.path.join(dir_corpus2, output_file_name), 'w', encoding="utf-8")
output_file.write("Left contexts from annotated sentences not found in subcorpora\n")
for lc in all_lc:
    if lc2sentence_all[lc] == 0:
        output_file.write(str(lc) + "\n")
output_file.close()