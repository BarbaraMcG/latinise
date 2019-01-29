## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 23/01/2019
# Python version: 3
# Script for extracting form – lemma – PoS - freq quadruples from LatinISE


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

now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")
dir_in = os.path.join(directory, "v2")
dir_out = os.path.join(directory, "LatinISE gaps", "output")

# create output directory if it doesn't exist:
if not os.path.exists(os.path.join(directory, "LatinISE gaps", "output")):
    os.makedirs(os.path.join(directory, "LatinISE gaps", "output"))

# Input files:
latinise_file_name = "latin9.txt"
quadruple_file_name = "latinISE_quadruples_" + str(today_date) + ".csv"

if istest == "yes":
    quadruple_file_name = quadruple_file_name.replace(".csv", "_test.csv")


# Read corpus file:

latinise_file = open(os.path.join(dir_in, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

locale.setlocale(locale.LC_ALL, 'en_GB')
row_count_latinise_readable = locale.format('%d', row_count_latinise, grouping=True)


print("There are " + str(row_count_latinise_readable) + " lines in the corpus.")
latinise_file.close()

# read corpus lines containing a word form, PoS, and lemma

latinise_file = open(os.path.join(dir_in, latinise_file_name), 'r', encoding="utf-8")

count_n = 0
#pairs = Counter()

triple2freq = dict()  # maps a triple (form, PoS, lemma) to its frequency in the corpus

for line in latinise_file:
    count_n += 1
    if istest == "yes":
        if count_n < 1000:
            print("Corpus line", str(count_n), "out of",
                  str(row_count_latinise_readable), "lines")
            if not line.startswith("<"):
                fields = line.rstrip('\n').split("\t")
                form = fields[0]
                pos = fields[1]
                lemma = fields[2]
                if (form, pos, lemma) in triple2freq:
                    triple2freq[(form, pos, lemma)] = triple2freq[(form, pos, lemma)] + 1
                else:
                    triple2freq[(form, pos, lemma)] = 1
                print("\t", form , pos, lemma + ":" + str(triple2freq[(form, pos, lemma)]))
    else:
        print("Corpus line", str(count_n), "out of",
              str(row_count_latinise_readable), "lines")
        if not line.startswith("<"):
            fields = line.rstrip('\n').split("\t")
            form = fields[0]
            pos = fields[1]
            lemma = fields[2]
            if (form, pos, lemma) in triple2freq:
                triple2freq[(form, pos, lemma)] = triple2freq[(form, pos, lemma)] + 1
            else:
                triple2freq[(form, pos, lemma)] = 1
                #print("\t", form, pos, lemma + ":" + str(triple2freq[(form, pos, lemma)]))

latinise_file.close()

# -----------------------------------------
# Write to output
# -----------------------------------------

print("Writing to output file...")
with open(os.path.join(dir_out, quadruple_file_name), "w") as output_file:
    writer_output = csv.writer(output_file, delimiter='\t')#, lineterminator='\n')
    writer_output.writerow(['form', 'pos', 'lemma', 'freq'])

    for (form, pos, lemma) in sorted(triple2freq.keys()):
        freq = int(triple2freq[(form, pos, lemma)])
        writer_output.writerow([form, pos, lemma, freq])
