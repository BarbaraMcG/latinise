## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 9/12/2019
# Python version: 3
# Script for adding sentence markers in LatinISE whenever there is a strong punctuation mark (.?!)


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

now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 60 # number of lines read when testing

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")

dir_corpus = os.path.join(directory, "v2")

# Input files:
latinise_file_name = "latin11.txt"
latinise_sentences_file_name = "latin12.txt"

if istest == "yes":
    latinise_sentences_file_name = latinise_sentences_file_name.replace(".txt", "_test.txt")


# Read corpus file:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

locale.setlocale(locale.LC_ALL, 'en_GB')
row_count_latinise_readable = locale.format('%d', row_count_latinise, grouping=True)


print("There are " + str(row_count_latinise_readable) + " lines in the corpus.")
latinise_file.close()


# read corpus and add sentence markers to it:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")
latinise_sentences_file = open(os.path.join(dir_corpus, latinise_sentences_file_name), 'w', encoding="utf-8")

count_n = 0
previous_line = ""
count_sentences = 0
found_lemma = 0

for line in latinise_file:
    count_n += 1
    if ((istest == "yes" and count_n < number_test) or istest != "yes"):
        if count_n % 100 == 0:
            print("Corpus line", str(count_n), "out of", str(row_count_latinise_readable), "lines")
        #print("Count:", str(count_n))
        #print("\tline:", str(line.rstrip()))
        #print("\tprevious line:", str(previous_line.rstrip()))
        #if (previous_line.startswith("<") or "<doc" in previous_line) and line.startswith("<"):
        #    print("Both start with <!")

        # add final closing sentence tag at the very end of the corpus:
        if line == "</doc>":
            latinise_sentences_file.write("</s>\n")
        elif count_n == 1 or ((previous_line.startswith("<") or "<doc" in previous_line) and line.startswith("<")) and previous_line != "<g/>\n":
                latinise_sentences_file.write(line)
                #print("Same")
        else:
            # add first sentence tag after first tags at the very beginning of the corpus:
            # add closing and opening sentence tags in the rest of the corpus:
            if not line.startswith("<") and (previous_line.startswith("<") or "<doc" in previous_line) and previous_line != "<g/>\n":
                count_sentences += 1
                found_lemma += 1
                if found_lemma == 1:
                    latinise_sentences_file.write("<s n=" + str(count_sentences) + ">\n")
                    #print("open first sentence ", str(count_sentences))
            if previous_line == "<g/>\n" and line in [".\tPUN\t.\n", "?\tPUN\t?\n", "!\tPUN\t!\n"]:
                #latinise_sentences_file.write(previous_line)
                latinise_sentences_file.write(line)
                latinise_sentences_file.write("</s>\n")
                #print("close sentence ", str(count_sentences))
                latinise_sentences_file.write("<s n=" + str(count_sentences) + ">\n")
                #print("open sentence ", str(count_sentences))
            else:
                latinise_sentences_file.write(line)
                #print("Same")

        previous_line = line

latinise_file.close()
latinise_sentences_file.close()
