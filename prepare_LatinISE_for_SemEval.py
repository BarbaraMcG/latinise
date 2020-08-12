## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 29/1/2020
# Python version: 3
# Script for preparing two subcorpora from LatinISE to be released as part of the SemEval 2020 Task 1
# Steps:
# remove punctuation marks from sentences
# only keep lemmas
# split by sentences
# convert century to dates like "100" for "1 cent A D" and "-100" for "1 cent B C"
# create subcorpus1 for BC and subcorpus2 for AD, format: [normalized dates] TAB [pre-processed lemmatized sentence]
# shuffle lines in subcorpus1 and subcorpus2

# New version (11/8/2020): add version of the corpora with tokens rather than lemmas


# ----------------------------
# Initialization
# ----------------------------


# Import modules:

# import requests
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

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")
dir_annotation = os.path.join(directory, "Semantic annotation", "Annotated data", "selected")
dir_corpus = os.path.join(directory, "LatinISE 4")
dir_corpus2 = os.path.join(directory, "LatinISE 4", "for Codalab")
#dir_corpus2_tokens = os.path.join(directory, "LatinISE 4", "tokens")
dir_corpus3 = os.path.join(dir_corpus2, "semeval2020_ulscd_lat") # this version contains the lemmas
#dir_corpus3_tokens = os.path.join(dir_corpus2, "semeval2020_ulscd_lat_tokens") # this version contains the tokens
if not os.path.exists(dir_corpus2):
    os.mkdir(dir_corpus2)
#if not os.path.exists(dir_corpus2_tokens):
#    os.mkdir(dir_corpus2_tokens)
if not os.path.exists(dir_corpus3):
    os.mkdir(dir_corpus3)
#if not os.path.exists(dir_corpus3_tokens):
#    os.mkdir(dir_corpus3_tokens)
dir_corpus_bc = os.path.join(dir_corpus3, "corpus1")
dir_corpus_ad = os.path.join(dir_corpus3, "corpus2")
if not os.path.exists(dir_corpus_bc):
    os.mkdir(dir_corpus_bc)
if not os.path.exists(dir_corpus_ad):
    os.mkdir(dir_corpus_ad)

#dir_corpus_bc_tokens = os.path.join(dir_corpus3_tokens, "corpus1")
#dir_corpus_ad_tokens = os.path.join(dir_corpus3_tokens, "corpus2")
#if not os.path.exists(dir_corpus_bc_tokens):
#    os.mkdir(dir_corpus_bc_tokens)
#if not os.path.exists(dir_corpus_ad_tokens):
#    os.mkdir(dir_corpus_ad_tokens)


# Files:
latinise_file_name = "latin13.txt"
#dates_file_name = "LatinISE_dates.txt"
bc_subcorpus_name = "LatinISE_subcorpus1_non-shuffled.txt"
ad_subcorpus_name = "LatinISE_subcorpus2_non-shuffled.txt"
bc_subcorpus_tokens_name = "LatinISE_subcorpus1_non-shuffled_tokens.txt"
ad_subcorpus_tokens_name = "LatinISE_subcorpus2_non-shuffled_tokens.txt"
#bc_subcorpus_dates_name = "LatinISE_subcorpus1_dates.txt"
#ad_subcorpus_dates_name = "LatinISE_subcorpus2_dates.txt"
#bc_subcorpus_dates_shuffled_name = "LatinISE_subcorpus1_dates_shuffled.txt"
#ad_subcorpus_dates_shuffled_name = "LatinISE_subcorpus2_dates_shuffled.txt"
bc_subcorpus_shuffled_name = "LatinISE1.txt"
ad_subcorpus_shuffled_name = "LatinISE2.txt"
bc_subcorpus_shuffled_tokens_name = "LatinISE1_tokens.txt"
ad_subcorpus_shuffled_tokens_name = "LatinISE2_tokens.txt"
words_name = "targets.txt"

if istest == "yes":
    bc_subcorpus_name = bc_subcorpus_name.replace(".txt", "_test.txt")
    ad_subcorpus_name = ad_subcorpus_name.replace(".txt", "_test.txt")
    #bc_subcorpus_dates_name = bc_subcorpus_dates_name.replace(".txt", "_test.txt")
    #ad_subcorpus_dates_name = ad_subcorpus_dates_name.replace(".txt", "_test.txt")
    #bc_subcorpus_dates_shuffled_name = bc_subcorpus_dates_shuffled_name.replace(".txt", "_test.txt")
    #ad_subcorpus_dates_shuffled_name = ad_subcorpus_dates_shuffled_name.replace(".txt", "_test.txt")
    bc_subcorpus_shuffled_name = bc_subcorpus_shuffled_name.replace(".txt", "_test.txt")
    ad_subcorpus_shuffled_name = ad_subcorpus_shuffled_name.replace(".txt", "_test.txt")


# Read corpus file:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

locale.setlocale(locale.LC_ALL, 'en_GB')
row_count_latinise_readable = locale.format('%d', row_count_latinise, grouping=True)


print("There are " + str(row_count_latinise_readable) + " lines in the corpus.")
latinise_file.close()

# Normalize dates:

def normalize_dates(date):
    norm_date = date.replace(" ", "").replace(".", "")
    sign = ""
    hundred = ""
    #print("norm_date", norm_date)
    if "AD" in norm_date and "BC" not in norm_date:
        sign = "+"
    elif "BC" in norm_date and "AD" not in norm_date:
        sign = "-"
    elif "BC" in norm_date and "AD" in norm_date:
        sign = "0"
        hundred = "0"
    else:
        print("Unexpected date:", date)
    match_2dates = re.search(r'cent(\d+)\-(\d+)', norm_date)
    match = re.search(r'cent(\d+)', norm_date)
    if match_2dates:
        date1 = match_2dates.group(1)
        date2 = match_2dates.group(2)
        cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
        if sign == "+":
            cent_number = cent_number-100
        sign = sign.replace("+", "")
        hundred = str(sign) + str(cent_number)
    elif match:
        if sign != "0":
            cent_number = match.group(1)
            if sign == "+":
                cent_number = int(cent_number)-1
            sign = sign.replace("+", "")
            hundred = str(sign) + str(cent_number) + "00"
        else:
            hundred = "000"

    return hundred

# read corpus, keep lemmas only, remove punctuation marks, split by sentence, normalize dates:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")
#dates_file = open(os.path.join(dir_corpus2, dates_file_name), 'w')
#bc_subcorpus_dates = open(os.path.join(dir_corpus2, bc_subcorpus_dates_name), 'w')
#ad_subcorpus_dates = open(os.path.join(dir_corpus2, ad_subcorpus_dates_name), 'w')

if not os.path.exists(os.path.join(dir_corpus_bc, "lemma")):
    os.mkdir(os.path.join(dir_corpus_bc, "lemma"))
if not os.path.exists(os.path.join(dir_corpus_ad, "lemma")):
    os.mkdir(os.path.join(dir_corpus_ad, "lemma"))

if not os.path.exists(os.path.join(dir_corpus_bc, "token")):
    os.mkdir(os.path.join(dir_corpus_bc, "token"))
if not os.path.exists(os.path.join(dir_corpus_ad, "token")):
    os.mkdir(os.path.join(dir_corpus_ad, "token"))

bc_subcorpus = open(os.path.join(dir_corpus2, bc_subcorpus_name), 'w')
ad_subcorpus = open(os.path.join(dir_corpus2, ad_subcorpus_name), 'w')
bc_subcorpus_tokens = open(os.path.join(dir_corpus2, bc_subcorpus_tokens_name), 'w')
ad_subcorpus_tokens = open(os.path.join(dir_corpus2, ad_subcorpus_tokens_name), 'w')

count_n = 0
normalized_date = ""
sentence_n = ""
lemma = ""
printed_something = 0
count_tokens_bc = 0
count_tokens_ad = 0

for line in latinise_file:

    count_n += 1
    #print(str(count_n))
    if ((istest == "yes" and count_n < number_test) or istest != "yes"):
        #print(str(count_n),line)
        if count_n % 100 == 0:
            print("Corpus line", str(count_n), "out of", str(row_count_latinise_readable), "lines")
        if "<doc" in line:
            #print("doc!","ecco",str(line))
            match = re.search(r'century=\"(.+?)\"', line)
            if match:
                date = match.group(1)
                normalized_date = normalize_dates(date)
            #    #print(date, "\t",normalized_date)
            #    #dates_file.write(line.strip() + "\t" + date + "\t" + normalized_date + "\n")
            #    if "cent" in date:
            #        dates_file.write(date + "\t" + normalized_date + "\n")
            #    else:
            #        print("Date error", line)
            #        normalized_date = ""
            #else:
            #    print("Date error", line)
            #    normalized_date = ""

            # print date:
            #if normalized_date.startswith("-"):
            #    bc_subcorpus_dates.write(normalized_date + "\t")
            #else:
            #    ad_subcorpus_dates.write(normalized_date + "\t")

        #elif "<s " in line:
        #    print(line)
        #    match_s = re.search(r'n=(.+?)\>', line)
        #    sentence_n = match_s.group(1)
        #    print("sentence", str(sentence_n), str(normalized_date))
        #    if normalized_date.startswith("-"):
                #if printed_something == 0:
        #        bc_subcorpus_dates.write(normalized_date + "\t")
                #printed_something = 1
                #else:
                #    bc_subcorpus_dates.write("\n" + normalized_date + "\t")
                #    bc_subcorpus.write("\n" )
        #    else:
                #if printed_something == 0:
        #        ad_subcorpus_dates.write(normalized_date + "\t")
                #    printed_something = 1
                #else:
                #    ad_subcorpus_dates.write("\n" + normalized_date + "\t")
                #    ad_subcorpus.write("\n")

        if "<" not in line and line != "\n" and "</s" not in line:
            #print(line)
            line = line.strip()
            fields = line.split("\t")
            token = fields[0]
            lemma = fields[2]
            pos = fields[1]
            if pos != "PUN":
                if normalized_date.startswith("-"):
                    #bc_subcorpus_dates.write(lemma + " ")
                    bc_subcorpus.write(lemma + " ")
                    bc_subcorpus_tokens.write(token + " ")
                    count_tokens_bc += 1
                else:
                    #ad_subcorpus_dates.write(lemma + " ")
                    ad_subcorpus.write(lemma + " ")
                    ad_subcorpus_tokens.write(token + " ")
                    count_tokens_ad += 1

        elif "</s" in line:
            if normalized_date.startswith("-"):
                #bc_subcorpus_dates.write("\n")
                bc_subcorpus.write("\n")
                bc_subcorpus_tokens.write("\n")
            else:
                #ad_subcorpus_dates.write("\n")
                ad_subcorpus.write("\n")
                ad_subcorpus_tokens.write("\n")



latinise_file.close()
#dates_file.close()
#bc_subcorpus_dates.close()
#ad_subcorpus_dates.close()
bc_subcorpus.close()
ad_subcorpus.close()
bc_subcorpus_tokens.close()
ad_subcorpus_tokens.close()

# function that reads a subcorpus file, eliminates sentences with just one word, and shuffles lines:
def shuffle_corpus(dir_corpus, subcorpus_file_name, subcorpus_file_shuffled_name, dates_yes, lemma_or_token):
    print("Shuffling ", subcorpus_file_name, subcorpus_file_shuffled_name, dates_yes)
    subcorpus_file = open(os.path.join(dir_corpus2, subcorpus_file_name), 'r')
    lines = subcorpus_file.readlines()
    random.shuffle(lines)
    subcorpus_file_shuffled = open(os.path.join(dir_corpus, lemma_or_token, subcorpus_file_shuffled_name), 'w')
    for line in lines:
        #print(str(line))
        if dates_yes == "yes":
            sentence = line.split("\t")[1]
        else:
            sentence = line.split("\t")[0]
        words = sentence.split(" ")
        if len(words) > 2:
            subcorpus_file_shuffled.write(line)

    subcorpus_file.close()
    subcorpus_file_shuffled.close()

# create final shuffled subcorpus files:

#shuffle_corpus(bc_subcorpus_dates_name, bc_subcorpus_dates_shuffled_name, "yes")
#shuffle_corpus(ad_subcorpus_dates_name, ad_subcorpus_dates_shuffled_name, "yes")
shuffle_corpus(dir_corpus_bc, bc_subcorpus_name, bc_subcorpus_shuffled_name, "no", "lemma")
shuffle_corpus(dir_corpus_ad, ad_subcorpus_name, ad_subcorpus_shuffled_name, "no", "lemma")
shuffle_corpus(dir_corpus_bc, bc_subcorpus_name, bc_subcorpus_shuffled_name, "no", "token")
shuffle_corpus(dir_corpus_ad, ad_subcorpus_name, ad_subcorpus_shuffled_name, "no", "token")


# Print list of words:

words_list = [] # list of annotated words

# target words:
for word in os.listdir(os.path.join(dir_annotation, "target words")):
    if os.path.isdir(os.path.join(dir_annotation, "target words", word)):
        for file in os.listdir(os.path.join(dir_annotation, "target words", word)):
            if os.path.isfile(os.path.join(os.path.join(dir_annotation, "target words", word), file)) \
                    and file.lower().startswith("annotation_task") and file.endswith("_metadata.xlsx"):
                print(word)
                words_list.append(word)

for word in os.listdir(os.path.join(dir_annotation, "control words")):
    if os.path.isdir(os.path.join(dir_annotation, "control words", word)):
        for file in os.listdir(os.path.join(dir_annotation, "control words", word)):
            if os.path.isfile(os.path.join(os.path.join(dir_annotation, "control words", word), file)) \
                    and file.lower().startswith("annotation_task") and file.endswith("_metadata.xlsx"):
                print(word)
                words_list.append(word)

words = open(os.path.join(dir_corpus3, words_name), 'w')

for w in words_list:
    words.write(w + "\n")

words.close()

print(str(count_tokens_bc), "tokens in BC corpus")
print(str(count_tokens_ad), "tokens in AD corpus")

