## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 16/11/2020
# Python version: 3
# Script for preparing the annotated data from Latin SemEval annotations for SemEval resource paper
# Steps:
# 1) convert xlsx files of annotations into csv files for release
# 2) create 2 folders (for first and second time period respectively) containing one file per target word (named as target word) in the following format:
    #* identifier_sentence [tab] index_target [tab] text_date [tab] sentence_token
    #The identifier_sentence can be anything, but should be unique (e.g. 'word_use_#').
    # Similarly for identifier_sense (e.g. 'word_sense_#').
    # The index_target should be the index of the target word in sentence_token after splitting it at spaces.
    # The sentences should have tabs and linebreaks removed
# 3) create 1 folder containing the senses with one file per word (named as target word) in the following format:
   #* identifier_sense [tab] sense_description
# 4) create 1 folder containing the annotation with one file per word (named as target word) in the following format:
   #* identifier_sentence [tab] identifier_sense [tab] judgment [tab] comment [tab] annotator#
# The annotator# should be unique to this particular annotator (e.g. 'annotator1').
# If some annotators annotated more than one word, it would perhaps make sense to use the same tag for the annotator
# across these words to be able to match them later.
# 5) In additional columns you could add any further information (e.g. POS, author) which you would want to provide in the graphs.
# convert century to dates like "100" for "1 cent A D" and "-100" for "1 cent B C"
# This version creates the same word and sentence IDs as process_annotations_LatinISE.py, which generated the February 2020 data for SemEval. On the other hand, prepare_annotations_for_SemEval.py created the IDs differently and generated the data in November 2020.

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
import pandas as pd
from pandas import read_excel
import random
import math

now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 100 # number of lines read when testing

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "GitHub", "DWUG", "latin", )
dir_annotation_original = os.path.join(directory, "annotation_original")
dir_annotation = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus", "Semantic annotation", "Annotated data", "selected")

# output folders:
# folder with csv annotations
dir_csv = os.path.join(directory, "annotation_csv")
if not os.path.exists(dir_csv):
    os.mkdir(dir_csv)

dir_out = os.path.join(directory, "for_clustering_Aug2021")
if not os.path.exists(dir_out):
    os.mkdir(dir_out)

# folder with BC and AD data
dir_bc = os.path.join(dir_out, "corpus1")
dir_ad = os.path.join(dir_out, "corpus2")
if not os.path.exists(dir_bc):
    os.mkdir(dir_bc)
if not os.path.exists(dir_ad):
    os.mkdir(dir_ad)
# folder with senses:
dir_senses = os.path.join(dir_out, "senses")
if not os.path.exists(dir_senses):
    os.mkdir(dir_senses)
# folder with annotated sentences:
dir_ann = os.path.join(dir_out, "annotated_data")
if not os.path.exists(dir_ann):
    os.mkdir(dir_ann)


# Files:
#bc_subcorpus_tokens_name = "LatinISE_subcorpus1_non-shuffled_tokens.txt"
#ad_subcorpus_tokens_name = "LatinISE_subcorpus2_non-shuffled_tokens.txt"
#bc_subcorpus_shuffled_name = "LatinISE1.txt"
#ad_subcorpus_shuffled_name = "LatinISE2.txt"
#bc_subcorpus_shuffled_tokens_name = "LatinISE1_tokens.txt"
#ad_subcorpus_shuffled_tokens_name = "LatinISE2_tokens.txt"
#words_name = "targets.txt"

#if istest == "yes":
#    bc_subcorpus_name = bc_subcorpus_name.replace(".txt", "_test.txt")
#    ad_subcorpus_name = ad_subcorpus_name.replace(".txt", "_test.txt")
#    bc_subcorpus_shuffled_name = bc_subcorpus_shuffled_name.replace(".txt", "_test.txt")
#    ad_subcorpus_shuffled_name = ad_subcorpus_shuffled_name.replace(".txt", "_test.txt")

# ------------------------
# Functions:
# ------------------------


# This function normalizes the annotators' ratings, because sometimes they marked a number (e.g. "1")
#  and sometimes a string (e.g. "1: Identical")

def normalize_ratings(ratings):
    #print("shape:", str(ratings.shape))
    #if len(str(ratings.iloc[1,3])) > 1:
    for column in range(ratings.shape[1]):
        #print("column", str(column))
        #print("old:\n", ratings.iloc[:,column])
        ratings.iloc[:,column] = ratings.iloc[:,column].astype(str).str.split(': ').str[0]
        #print("new:", ratings.iloc[column])
    #print(str(ratings))
    return ratings


# Normalize dates:


def normalize_centuries(century_date):
    norm_cent = century_date.replace(" ", "").replace(".", "")
    sign = ""
    #hundred = ""
    #print("century_date", century_date)
    if "AD" in norm_cent and "BC" not in norm_cent:
        sign = "+"
    elif "BC" in norm_cent and "AD" not in norm_cent:
        sign = "-"
    elif "BC" in norm_cent and "AD" in norm_cent:
        sign = "0"
        #hundred = "0"
    else:
        print("Unexpected date:", date)
    match_2dates = re.match(r'^(\d+)\-(\d+)', norm_cent)
    match_2dates_bcad = re.match(r'^(\d+)BC\-(\d+)AD', norm_cent)
    match = re.match(r'^(\d+)', norm_cent)

    if match_2dates_bcad:
        #print("two centuries across 0 date")
        if sign == "0":
            cent_number1 = match_2dates_bcad.group(1)
            cent_number2 = match_2dates_bcad.group(2)
            cent_number_lower = (int(cent_number1)) * 100
            cent_number_upper = (int(cent_number2)) * 100
            norm_cent = "[-" + str(cent_number_lower) + "," + str(cent_number_upper) + "]"
        else:
            print("Extra case:", str(norm_cent))
    elif match_2dates:
        #print("two centuries date")
        if sign != "0":
            cent_number1 = match_2dates.group(1)
            cent_number2 = match_2dates.group(2)
            if sign == "+":
                cent_number_lower = (int(cent_number1)-1)*100
                cent_number_upper = (int(cent_number2))*100
                norm_cent = "[" + str(cent_number_lower) + "," + str(cent_number_upper) + "]"
            else:
                cent_number_lower = (int(cent_number1)) * 100
                cent_number_upper = (int(cent_number2)-1) * 100
                norm_cent = "[-" + str(cent_number_lower) + ",-" + str(cent_number_upper) + "]"
        else:
            print("Extra case:", str(norm_cent))
        #sign = sign.replace("+", "")
        #hundred = str(sign) + str(cent_number)
    elif match:
        #print("simple century date")
        if sign != "0":
            cent_number = match.group(1)
            if sign == "+":
                cent_number_lower = (int(cent_number) - 1) * 100
                cent_number_upper = (int(cent_number)) * 100
                # sign = sign.replace("+", "")
                norm_cent = "[" + str(cent_number_lower) + "," + str(cent_number_upper) + "]"
            else:
                cent_number_lower = (int(cent_number)) * 100
                cent_number_upper = (int(cent_number) - 1) * 100
                # sign = sign.replace("+", "")
                norm_cent = "[-" + str(cent_number_lower) + ",-" + str(cent_number_upper) + "]"
        else:
            print("Extra case:", str(norm_cent))
    else:
        print("Extra case:", str(norm_cent))

    norm_cent = norm_cent.replace("-0", "0")
    return norm_cent

# -----------------------------------------------------------------
# 1) convert xlsx files of annotations into csv files for release:
# -----------------------------------------------------------------

# Read annotation files and save them as csv:

for annotated_file_name in sorted(os.listdir(dir_annotation_original)):
    if annotated_file_name.endswith(".xlsx") and annotated_file_name.startswith("annotation"):
        annotated_file_name_csv = annotated_file_name.replace(".xlsx", ".csv")
        #print("Opening", os.path.join(dir_annotation_original, annotated_file_name))

        with open(os.path.join(dir_annotation_original, annotated_file_name), 'r') as ann: # open in readonly mode
            ann = read_excel(os.path.join(dir_annotation_original, annotated_file_name), 'Annotation').iloc[:60]
            ann.to_csv(os.path.join(dir_csv, annotated_file_name_csv), index=None, header=True, quoting=csv.QUOTE_MINIMAL)

# -----------------------------------------------------------------
# 2) create 2 folders (for first and second time period respectively) containing one file per target word (named as target word) in the following format:
# * identifier_sentence [tab] index_target [tab] text_date [tab] sentence_token
# The identifier_sentence can be anything, but should be unique (e.g. 'word_use_#').
# Similarly for identifier_sense (e.g. 'word_sense_#').
# The index_target should be the index of the target word in sentence_token after splitting it at spaces.
# The annotator# should be unique to this particular annotator (e.g. 'annotator1').
# If some annotators annotated more than one word, it would perhaps make sense to use the same tag for the annotator
# across these words to be able to match them later.
# The sentences should have tabs and linebreaks removed
# -----------------------------------------------------------------



# Found annotated words:

target_words = [] # list of annotated target words
control_words = [] # list of annotated control words
word2filename = dict() # maps an annotated word to its file name

# target words:
count = 0
for word in os.listdir(os.path.join(dir_annotation, "target words")):
    if os.path.isdir(os.path.join(dir_annotation, "target words", word)):
        for file in os.listdir(os.path.join(dir_annotation, "target words", word)):
            if os.path.isfile(os.path.join(os.path.join(dir_annotation, "target words", word), file)) \
                    and file.lower().startswith("annotation_task") and file.endswith("_metadata.xlsx"):
                # For some reason, virtus was read as the eigth word, but it should be the last of the list
                if "virtus" not in word:
                    count += 1
                    #print(str(count), "Target word:", word)
                    target_words.append(word)
                    word2filename[word] = file


for word in os.listdir(os.path.join(dir_annotation, "control words")):
    if os.path.isdir(os.path.join(dir_annotation, "control words", word)):
        for file in os.listdir(os.path.join(dir_annotation, "control words", word)):
            if os.path.isfile(os.path.join(os.path.join(dir_annotation, "control words", word), file)) \
                    and file.lower().startswith("annotation_task") and file.endswith("_metadata.xlsx"):
                # For some reason, salus  was read as the 37th word and sacramentum as the 38th word, and jus was missing
                #if "salus" not in word and "sacramentum" not in word and 'jus' not in word:
                count += 1
                #print(str(count), "Control word:", word)
                control_words.append(word)
                word2filename[word] = file

words = target_words + control_words
#words.append("salus")
#words.append("sacramentum")
#words.append("jus")
words.append("virtus")
#word2filename["salus"] = "annotation_task_salus_DARIA_metadata.xlsx"
#word2filename["sacramentum"] = "annotation_task_sacramentum_DARIA_metadata.xlsx"
word2filename["virtus"] = "annotation_task_virtus_Hugo_metadata.xlsx"


if istest == "yes":
    words = words[:2]
    target_words = target_words[:1]
    control_words = control_words[:1]

print("There are", str(len(words)), "annotated words", "of which", str(len(target_words)), "target words and ", str(len(control_words)), "control words")

# Read annotation files:
sentence_id = ""
words_read = 0

sentences_read = 0

print("Creating files with identifier_sentence [tab] index_target [tab] text_date [tab] sentence_token...")
for word in words:
    #print("Word", word)
    #path = ""
    #if word in target_words:
    #    path = os.path.join(dir_annotation, "target words")
    #else:
    #    path = os.path.join(dir_annotation, "control words")

#for annotated_file_name in sorted(os.listdir(dir_csv)):
#    if annotated_file_name.endswith(".csv") and annotated_file_name.startswith("annotation"):
#        #print("Opening", os.path.join(dir_csv, annotated_file_name))
#        word = annotated_file_name.split("_")[2] # annotation_task_regnum_ROZI_metadata.csv
    annotated_file_name = word2filename[word]
    annotated_file_name = annotated_file_name.replace(".xlsx", ".csv")
    #print(annotated_file_name)
    if os.path.isfile(os.path.join(dir_csv, annotated_file_name)) \
                and annotated_file_name.startswith("annotation_task") and annotated_file_name.endswith(
            "_metadata.csv"):
        #print("word:", word)
        #print(annotated_file_name)
        annotator = annotated_file_name.split("_")[3].lower()
        #print("annotator:", annotator)

        ann = pd.read_csv(os.path.join(dir_csv, annotated_file_name))
        words_read += 1
        #print("Words read so far:", str(words_read))
        if (istest == "yes" and words_read <=1) or istest == "no":
            #print(str(ann.shape[0]), "rows", ann.shape[1], "columns")
            columns = ann.columns.tolist()
            columns_lc = [c.lower() for c in columns]
            index_first = columns_lc.index("right context") + 1
            index_last = columns_lc.index("comments")
            index_era = columns_lc.index("era")
            index_metadata = index_era - 1
            index_left_context = columns_lc.index("left context")
            index_target = index_left_context + 1
            index_right_context = columns_lc.index("right context")

            ratings = ann.iloc[0:61, index_first:index_last]
            target_forms = ann.iloc[0:61, index_target]
            sentences_left_context = ann.iloc[0:61, index_left_context]
            sentences_right_context = ann.iloc[0:61, index_right_context]

            eras = ann.iloc[0:61, index_era]
            eras = eras.dropna()
            metadata = ann.iloc[0:61, index_metadata]
            #print(str(eras))
            ratings = ratings.dropna()
            #print(str(ratings))
            if ratings.shape[0] < 60 and "scriptura" not in word:
                print("Fewer than 60 annotated sentences for", word)
                break
            elif eras.shape[0] < 60 and "scriptura" not in word:
                print("Fewer than 60 eras for", word)
                break
            else:
                ratings = normalize_ratings(ratings)
                #print(str(ratings))
                senses = ratings.columns.tolist()
                #print("senses:", senses)

            # loop over the annotated sentences and assign them to BC or AD folder:
            # * identifier_sentence [tab] index_target [tab] text_date [tab] sentence_token
            bc_word_file = open(os.path.join(dir_bc, word), 'w')
            #bc_tsv_writer = csv.writer(bc_word_file, delimiter='\t')
            ad_word_file = open(os.path.join(dir_ad, word), 'w')
            #ad_tsv_writer = csv.writer(ad_word_file, delimiter='\t')
            #print("Metadata:", str(metadata))

            #print(str(sentences_left_context))

            for i, row in ratings.iterrows():
                #print("Index:", str(i))
                # for i in range(ratings.shape[0]):
                # print(str(i))
                # print(str(sentences_left_context[i] ))

                sentence_id = str(words_read) + "_" + str(i)

            #for i in range(ratings.shape[0]):
                #print(str(i))
                #print(str(sentences_left_context[i]))
                #print(str(type(sentences_left_context[i])))
                if isinstance(sentences_left_context[i], float) and math.isnan(sentences_left_context[i]):
                    #print(str(type(sentences_left_context[i])))
                    sentences_left_context[i] = " "
                    #print("!!!!", word, sentence_id)

                if (sentences_left_context[i] is not None) and ("\t" in sentences_left_context[i] or "\n" in sentences_left_context[i]):
                        print("Tab or newline in left context, line", str(i))
                if (sentences_right_context[i] is not None) and ("\t" in sentences_right_context[i] or "\n" in sentences_right_context[i]):
                        print("Tab or newline in right context, line", str(i))

                sentence_left_context = sentences_left_context[i]
                sentence_left_context_tokens = sentence_left_context.split(" ")


                target_form = target_forms[i]
                sentence_right_context = sentences_right_context[i]
                sentences_right_context[i] = sentences_right_context[i].lstrip()
                #print("right context is here:", str(sentences_right_context[i]))
                sentence_right_context_tokens = sentence_right_context.split(" ")
                all_sentence_tokens = sentence_left_context_tokens + [target_form] + sentence_right_context_tokens
                #print(str(all_sentence_tokens))
                #all_sentence = ' '.join(all_sentence_tokens)
                #all_sentence = all_sentence#.replace("  ", " ")
                #if (word == "fidelis") and (sentence_id == "2_44"):
                #    print("left context:", sentence_left_context, "end")
                #    print("target form:", target_form, "end")
                #    print("right context:", sentence_right_context, "end")
                if not sentence_left_context.endswith(" ") and not target_form.startswith(" "):
                    #if (word == "fidelis") and (sentence_id == "2_44"):
                    #    print("yes")
                    sentence_left_context = sentence_left_context + " "
                if not sentence_right_context.startswith(" ") and not target_form.endswith(" "):
                    #if (word == "fidelis") and (sentence_id == "2_44"):
                    #    print("yesss")
                    sentence_right_context = " " + sentence_right_context

                #if (word == "fidelis") and (sentence_id == "2_44"):
                #    print('1len(sentence_left_context.split(" ")):', len(sentence_left_context.split(" ")))
                #index_target = len(sentence_left_context_tokens)
                if sentence_left_context == " ":
                    sentence_left_context = ""
                    index_target = 0
                elif sentence_left_context.endswith(" ") and not sentence_left_context == " ":
                    #sentence_left_context = sentence_left_context.rstrip(" ")
                    index_target = len(sentence_left_context.split(" "))-1
                else:
                    index_target = len(sentence_left_context.split(" "))

                #if (word == "fidelis") and (sentence_id == "2_44"):
                #    print('2len(sentence_left_context.split(" ")):', len(sentence_left_context.split(" ")))

                #if (word == "fidelis") and (sentence_id == "2_44"):
                #    print("Index target:", str(index_target))

                all_sentence = sentence_left_context + target_form + sentence_right_context

                #if (word == "fidelis") and (sentence_id == "2_44"):
                #    print('3len(sentence_left_context.split(" ")):', len(sentence_left_context.split(" ")))

                #if (word == "fidelis") and (sentence_id == "2_44"):
                #    print("left context:", sentence_left_context, "end")
                #    print("target form:", target_form, "end")
                #    print("right context:", sentence_right_context, "end")
                #    print("All sentence:",all_sentence)
                    #for u in range(len(all_sentence.split(" "))):
                    #    print(str(u), all_sentence.split(" ")[u])
                #x = all_sentence.split(" ")[index_target].lower()
                #if x[:len(word)-4] != word.lower()[:len(word)-4]:
                print(str(index_target),"word=",word, "in sentence",sentence_id, ":", all_sentence.split(" ")[index_target])
                    #print("sentence=", all_sentence)

                #print("Metadata-i:", str(metadata[i]))
                match = re.search(r'\,cent\. (.+?)\,', metadata[i])
                if match:
                    cent_date = match.group(1)
                    #print("Cent date:", cent_date)
                    normalized_cent_date = normalize_centuries(cent_date)
                    #print("Normalised century date:", normalized_cent_date)

                #* identifier_sentence [tab] index_target [tab] text_date [tab] sentence_token
                if "BC" in eras[i]:
                    # write to BC file for this word:
                    # file_name_bc_word = os.path.join(dir_bc, word)
                    #sentence_id = "word_use_" + str(i)
                    #bc_tsv_writer.writerow([sentence_id])
                    bc_word_file.write(sentence_id + "\t")
                    bc_word_file.write(str(index_target) + "\t")
                    bc_word_file.write(str(normalized_cent_date) + "\t")
                    bc_word_file.write(all_sentence + "\n")
                elif "AD" in eras[i]:
                    # write to AD file for this word:
                    #sentence_id = "word_use_" + str(i)
                    #ad_tsv_writer.writerow([sentence_id])
                    ad_word_file.write(sentence_id + "\t")
                    ad_word_file.write(str(index_target) + "\t")
                    ad_word_file.write(str(normalized_cent_date) + "\t")
                    ad_word_file.write(all_sentence + "\n")
                else:
                    print("Error in era?")

            bc_word_file.close()
            ad_word_file.close()


# -----------------------------------------------------------------
# 3) create 1 folder containing the senses with one file per word (named as target word) in the following format:
   #* identifier_sense [tab] sense_description
# -----------------------------------------------------------------

words_read = 0
print("Creating files with identifier_sense [tab] sense_description...")

for word in words:
    #path = ""
    #if word in target_words:
    #    path = os.path.join(dir_csv, "target words")
    #else:
    #    path = os.path.join(dir_csv, "control words")

    annotated_file_name = word2filename[word]
    annotated_file_name = annotated_file_name.replace(".xlsx", ".csv")
    if os.path.isfile(os.path.join(dir_csv, annotated_file_name)) \
                and annotated_file_name.startswith("annotation_task") and annotated_file_name.endswith(
            "_metadata.csv"):

#for annotated_file_name in sorted(os.listdir(dir_csv)):
#    if annotated_file_name.endswith(".csv") and annotated_file_name.startswith("annotation"):
#        # print("Opening", os.path.join(dir_csv, annotated_file_name))
#        word = annotated_file_name.split("_")[2]  # annotation_task_regnum_ROZI_metadata.csv
        #print("word:", word)
        annotator = annotated_file_name.split("_")[3].lower()
        # print("annotator:", annotator)

        ann = pd.read_csv(os.path.join(dir_csv, annotated_file_name))
        words_read += 1
        # print("Words read so far:", str(words_read))
        if (istest == "yes" and words_read <= 1) or istest == "no":
            #print(str(ann.shape[0]), "rows", ann.shape[1], "columns")
            columns = ann.columns.tolist()
            columns_lc = [c.lower() for c in columns]
            index_first = columns_lc.index("right context") + 1
            index_last = columns_lc.index("comments")
            index_era = columns_lc.index("era")

            ratings = ann.iloc[0:61, index_first:index_last]

            senses = ratings.columns.tolist()
            # print("senses:", senses)
            sense_ids = [word + str(senses.index(s)) for s in senses]
            #print(str(os.path.join(dir_senses, word)))
            sense_word_file = open(os.path.join(dir_senses, word), 'w')

            for i in range(len(senses)):
                #print("senses:")
                #print(str(i))
                #print(senses[i])
                # print(str(sentences_left_context[i] ))
                #sentences_read += i

                #sense_tsv_writer = csv.writer(sense_word_file, delimiter='\t')
                sense_word_file.write(sense_ids[i] + "\t" + senses[i] + "\n")
            # print("Metadata:", str(metadata))

            sense_word_file.close()


# -----------------------------------------------------------------
# 4) create 1 folder containing the annotation with one file per word (named as target word) in the following format:
   #* identifier_sentence [tab] identifier_sense [tab] judgment [tab] comment [tab] annotator#
# -----------------------------------------------------------------

annotators = list()
words_read = 0
#for annotated_file_name in sorted(os.listdir(dir_csv)):
#    if annotated_file_name.endswith(".csv") and annotated_file_name.startswith("annotation"):
#        #print("Opening", os.path.join(dir_csv, annotated_file_name))
#        word = annotated_file_name.split("_")[2] # annotation_task_regnum_ROZI_metadata.csv
for word in words:
    #print("Word", word)
    #path = ""
    #if word in target_words:
    #    path = os.path.join(dir_annotation, "target words")
    #else:
    #    path = os.path.join(dir_annotation, "control words")

    annotated_file_name = word2filename[word]
    annotated_file_name = annotated_file_name.replace(".xlsx", ".csv")
    if os.path.isfile(os.path.join(dir_csv, annotated_file_name)) \
                and annotated_file_name.startswith("annotation_task") and annotated_file_name.endswith(
            "_metadata.csv"):

        annotator = annotated_file_name.split("_")[3].lower()
        #print("Annotator:", annotator)
        annotators.append(annotator)

annotators = list(set(annotators))

# assign an ID to each annotator:
annotators.sort()
#print("Annotators:", str(annotators))

words_read = 0
print("Creating files with identifier_sentence [tab] identifier_sense [tab] judgment [tab] comment [tab] annotator#")

#for annotated_file_name in sorted(os.listdir(dir_csv)):
#    if annotated_file_name.endswith(".csv") and annotated_file_name.startswith("annotation"):
#        #print("Opening", os.path.join(dir_csv, annotated_file_name))
#        word = annotated_file_name.split("_")[2] # annotation_task_regnum_ROZI_metadata.csv
for word in words:
    #print("Word", word)
    #path = ""
    #if word in target_words:
    #    path = os.path.join(dir_annotation, "target words")
    #else:
    #    path = os.path.join(dir_annotation, "control words")

#for annotated_file_name in sorted(os.listdir(dir_csv)):
#    if annotated_file_name.endswith(".csv") and annotated_file_name.startswith("annotation"):
#        print("Opening", os.path.join(dir_csv, annotated_file_name))
#        word = annotated_file_name.split("_")[2] # annotation_task_regnum_ROZI_metadata.csv
#        print("word:", word)
    annotated_file_name = word2filename[word]
    annotated_file_name = annotated_file_name.replace(".xlsx", ".csv")
    if os.path.isfile(os.path.join(dir_csv, annotated_file_name)) \
            and annotated_file_name.startswith("annotation_task") and annotated_file_name.endswith(
        "_metadata.csv"):

        annotator = annotated_file_name.split("_")[3].lower()
        annotator_id = annotators.index(annotator)

        ann = pd.read_csv(os.path.join(dir_csv, annotated_file_name))
        words_read += 1
        #print("Words read so far:", str(words_read))
        if (istest == "yes" and words_read <=1) or istest == "no":
            #print(str(ann.shape[0]), "rows", ann.shape[1], "columns")
            columns = ann.columns.tolist()
            columns_lc = [c.lower() for c in columns]
            index_first = columns_lc.index("right context") + 1
            index_last = columns_lc.index("comments")
            index_era = columns_lc.index("era")
            index_metadata = index_era - 1
            index_left_context = columns_lc.index("left context")
            index_target = index_left_context + 1
            index_right_context = columns_lc.index("right context")

            ratings = ann.iloc[0:61, index_first:index_last]
            target_form = ann.iloc[0:61, index_target]
            sentences_left_context = ann.iloc[0:61, index_left_context]
            sentences_right_context = ann.iloc[0:61, index_right_context]
            comments = ann.iloc[0:61, index_last]


            #print(str(eras))
            ratings = ratings.dropna()
            #print(str(ratings))
            if ratings.shape[0] < 60 and "scriptura" not in word:
                print("Fewer than 60 annotated sentences for", word)
                break
            elif eras.shape[0] < 60 and "scriptura" not in word:
                print("Fewer than 60 eras for", word)
                break
            else:
                ratings = normalize_ratings(ratings)
                #print(str(ratings))

            senses = ratings.columns.tolist()
            #print("senses:", senses)

            sense_ids = [word + str(senses.index(s)) for s in senses]
            # loop over the annotated sentences and assign them to BC or AD folder:
            # * identifier_sentence [tab] index_target [tab] text_date [tab] sentence_token
            annotation_word_file = open(os.path.join(dir_ann, word), 'w')

            #print(str(sentences_left_context))

            for index, row in ratings.iterrows():

            #for i in range(ratings.shape[0]):
                #print(str(i))
                #print(str(sentences_left_context[i] ))

                sentence_id = str(words_read) + "_" + str(index)
    
                for i in range(len(senses)):

                    sense_id = sense_ids[i]
                    rating_this_sense_this_sentence = int(float(ratings.iloc[index, i]))
                    comment = comments[index]
                    annotation_word_file.write(str(sentence_id) + "\t" + str(sense_id) + "\t" + str(rating_this_sense_this_sentence) + "\t" + str(comment) + "\t" + str(annotator_id) + "\n")

            annotation_word_file.close()

# -----------------------------------------------------------------
# 5) In additional columns you could add any further information (e.g. POS, author) which you would want to provide in the graphs.
# convert century to dates like "100" for "1 cent A D" and "-100" for "1 cent B C"
# -----------------------------------------------------------------




