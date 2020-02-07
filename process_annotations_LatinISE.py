## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 4/2/2020
# Python version: 3
# Script for preparing annotated data to be processed by Dominik's script that clusters senses.

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
from pandas import read_excel
import numpy as np
import math
from statistics import mean
from scipy.stats import spearmanr


now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 2 # number of words considered when testing

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")

dir_annotation = os.path.join(directory, "Semantic annotation", "Annotated data", "selected")


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

print("There are", str(len(words)), "annotated words", "of which", str(len(target_words)), "target words and ", str(len(control_words)), "control words")

# Read annotation files:
sentence_id = ""
words_read = 0


for word in words:
    print("Word", word)
    path = ""
    if word in target_words:
        path = os.path.join(dir_annotation, "target words")
    else:
        path = os.path.join(dir_annotation, "control words")

    # Output file:
    output = open(os.path.join(os.path.join(directory, "Semantic annotation", "Codalab data", "For clustering"), word), 'w')

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
        index_first = columns_lc.index("right context")+1
        index_last = columns_lc.index("comments")
        index_era = columns_lc.index("era")

        ratings = ann.iloc[0:61, index_first:index_last]
        eras = ann.iloc[0:61, index_era]
        eras = eras.dropna()
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
            normalize_ratings(ratings)
            #print(str(ratings))
            senses = ratings.columns.tolist()
            #print("senses:", senses)
            sense_ids = [word + str(senses.index(s)) for s in senses]
            #print("sense ids:", sense_ids)

            for index, row in ratings.iterrows():
                #print(sense_ids[0], str(index), str(row[0]), str(eras[index]))
                sentence_id = str(words_read) + "_" + str(index)

                for i in range(len(senses)):
                    #if str(ratings.iloc[index, i]) == "0.0" or str(ratings.iloc[index, i]) == "0":
                    #    ratings.iloc[index, i] = np.nan
                    era = ""
                    #print(str(eras[index]))
                    if "BC" in str(eras[index]):
                        era = "old"
                    else:
                        era = "new"
                    output.write(sentence_id + "\t" + str(sense_ids[i]) + "\t" + str(int(float(ratings.iloc[index, i]))) + "\t" + era + "\n")

output.close()