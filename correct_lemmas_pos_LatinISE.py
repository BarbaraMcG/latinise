## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 9/12/2019
# Python version: 3
# Script for correcting lemmas and pos in LatinISE


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
number_test = 1000 # number of lines read when testing

if istest == "":
    istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")

dir_corpus = os.path.join(directory, "v2")
dir_corrections = os.path.join(directory, "LatinISE gaps", "output")

# create output directory if it doesn't exist:
if not os.path.exists(os.path.join(directory, "LatinISE gaps", "output")):
    os.makedirs(os.path.join(directory, "LatinISE gaps", "output"))

# Input files:
latinise_file_name = "latin10.txt"
#quadruple_file_name = "latinISE_quadruples_" + str(today_date) + ".csv"
corrections_file_name = "latinISE_quadruples_2019-02-18_corrections.xlsx"
latinise_corrected_file_name = "latin11.txt"

if istest == "yes":
    latinise_corrected_file_name = latinise_corrected_file_name.replace(".txt", "_test.txt")


# Read corpus file:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

locale.setlocale(locale.LC_ALL, 'en_GB')
row_count_latinise_readable = locale.format('%d', row_count_latinise, grouping=True)


print("There are " + str(row_count_latinise_readable) + " lines in the corpus.")
latinise_file.close()


# Read corrections file:

form_lemma_pos2correctedlemma = dict() # maps a form, lemma, pos triple to its corrected lemma
form_lemma_pos2correctedpos = dict() # maps a form, lemma, pos triple to its corrected pos

corrections_workbook = xlrd.open_workbook(os.path.join(dir_corrections, corrections_file_name))
corrections_worksheet = corrections_workbook.sheet_by_index(0)

print("There are " + str(corrections_worksheet.nrows) + " lines in the list of corrections.")

count = 0
for row in range(1, corrections_worksheet.nrows):
    count += 1
    if (istest == "yes" and count < number_test) or istest != "yes":
        if count % 1000 == 0:
            print("Reading corrections line number", str(count))
        form = corrections_worksheet.cell_value(row,0)
        pos = corrections_worksheet.cell_value(row,1)
        lemma = corrections_worksheet.cell_value(row,2)
        freq = corrections_worksheet.cell_value(row,3)
        corrected_pos = corrections_worksheet.cell_value(row,4)
        corrected_lemma = corrections_worksheet.cell_value(row,5)
        #print("corrections:", "form:", form, "pos:", pos, "lemma:", lemma, "corrected pos:", corrected_pos, "corrected lemma:", corrected_lemma)
        if corrected_lemma is not '':
            form_lemma_pos2correctedlemma[(form, lemma, pos)] = corrected_lemma
            print("Correction! ", corrected_lemma)
        if corrected_pos is not '':
            form_lemma_pos2correctedpos[(form, lemma, pos)] = corrected_pos
            print("Correction! ", corrected_pos)

corrections_workbook.release_resources()
del corrections_workbook

#print(str(form_lemma_pos2correctedlemma))

# read corpus and correct it:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")
latinise_corrected_file = open(os.path.join(dir_corpus, latinise_corrected_file_name), 'w', encoding="utf-8")

count_n = 0
#pairs = Counter()

triple2freq = dict()  # maps a triple (form, PoS, lemma) to its frequency in the corpus

for line in latinise_file:
    count_n += 1
    if ((istest == "yes" and count_n < number_test) or istest != "yes"):
        if count_n % 1000 == 0:
            print("Corpus line", str(count_n), "out of", str(row_count_latinise_readable), "lines")
        #print("line:", str(line))
        if "<doc" in line or line.startswith("<"):
            latinise_corrected_file.write(line)
        else:
            fields = line.rstrip('\n').split("\t")
            if len(fields) == 3:
                form = fields[0]
                pos = fields[1]
                lemma = fields[2]
                new_pos = pos
                new_lemma = lemma

                if (form, lemma, pos) in form_lemma_pos2correctedlemma:
                    new_lemma = form_lemma_pos2correctedlemma[(form, lemma, pos)]
                    #print("New lemma!" + new_lemma)
                if (form, lemma, pos) in form_lemma_pos2correctedpos:
                    new_pos = form_lemma_pos2correctedpos[(form, lemma, pos)]
                    #print("New pos!" + new_pos)
                if new_lemma is not lemma or new_pos is not pos:
                    #print("\t", form , pos, lemma, " corrected: ", new_pos, new_lemma)
                    line = form + "\t" + new_pos + "\t" + new_lemma + "\n"

                # Normalize homographs: dico2 and dico#2 –> dico#2
                if len(new_lemma) > 2 and new_lemma[-1].isdigit() and new_lemma[-2] is not "#":
                    #print("#!", new_lemma)
                    new_lemma = re.sub(r'^(.+?)(\d)$', r'\1#\2', new_lemma)
                    #print("\t-->", new_lemma)
                    line = form + "\t" + new_pos + "\t" + new_lemma + "\n"
                    #print("line1:", str(line))

            else:
                print("Error!" + str(line))

            latinise_corrected_file.write(line)
            #print("line2:", str(line))

latinise_file.close()
latinise_corrected_file.close()
