## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 29/1/2020
# Python version: 3
# Script for calculating inter-annotator agreement for the Latin semantic annotation for SemEval 2020 task 1;
# The word that all annotators worked on is "virtus"


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


now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 2 # number of annotators considered when testing

annotators = ["Annie", "Daria",  "Hugo", "Rozi"]#, "Hege"]

if istest == "":
    istest = istest_default

if istest == "yes":
    annotators = annotators[1:2]

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")

dir_annotation = os.path.join(directory, "Semantic annotation", "Annotated data", "selected", "target words", "virtus")

# Output file:
agreement_file_name = "inter-annotator.csv"

if istest == "yes":
    agreement_file_name = agreement_file_name.replace(".csv", "_test.csv")


# Read annotation files:

for annotator1 in annotators:
    for annotator2 in annotators:
        if annotator1 != annotator2:

            annotated_file1 = open(os.path.join(dir_annotation, "Annotation_task1_virtus_" + annotator1 + ".xlsx"), 'r', encoding="utf-8")
            annotated_file2 = open(os.path.join(dir_annotation, "Annotation_task2_virtus_" + annotator2 + ".xlsx"), 'r',
                                   encoding="utf-8")

            my_sheet = 'Annotation'
            ann1 = read_excel(annotated_file1, sheet_name=my_sheet)
            ann2 = read_excel(annotated_file2, sheet_name=my_sheet)
            print(ann1.head())  # shows headers with top 5 rows
            print(str(ann1.shape))
            print(ann2.head())  # shows headers with top 5 rows
            print(str(ann2.shape))

            annotated_file1.close()
            annotated_file2.close()

