## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 29/1/2020
# Python version: 3
# Script for calculating inter-annotator agreement for the Latin semantic annotation for SemEval 2020 task 1;
# The word that all annotators worked on is "virtus"

# How many times do all annotators agree?
# How many times do 3 out of 4 annotators agree?
# group together (1 and 2) and (3 and 4), how many times do all annotators agree?
# Visualize any outliers

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
number_test = 2 # number of annotators considered when testing

annotators = ["Annie", "Daria",  "Hugo", "Rozi"]#, "Hege"]

if istest == "":
    istest = istest_default

if istest == "yes":
    annotators = annotators[:2]

# Directory and file names:

directory = os.path.join("/Users", "bmcgillivray", "Documents", "OneDrive", "The Alan Turing Institute", "OneDrive - The Alan Turing Institute",
                         "Research", "2019", "Latin corpus")

dir_annotation = os.path.join(directory, "Semantic annotation", "Annotated data", "selected", "target words", "virtus")

# Output file:
agreement_file_name = "inter-annotator.txt"

if istest == "yes":
    agreement_file_name = agreement_file_name.replace(".txt", "_test.txt")


# This function normalizes the annotators' ratings, because sometimes they marked a number (e.g. "1")
#  and sometimes a string (e.g. "1: Identical":

def normalize_ratings(ratings):
    #print("shape:", str(ratings.shape))
    if len(str(ratings.iloc[1,3])) > 1:
        for column in range(ratings.shape[1]):
            #print("column", str(column))
            #print("old:\n", ratings.iloc[column])
            ratings.iloc[:,column] = ratings.iloc[:,column].str.split(': ').str[0]
            #print("new:", ratings.iloc[column])
    #print(str(ratings))
    return ratings

output = open(os.path.join(dir_annotation, agreement_file_name), 'w')

# Read annotation files:


annotator2ratings = dict() # maps an annotator to the data frame of their ratings

for annotator in annotators:
    my_sheet = 'Annotation'
    ann = read_excel(os.path.join(dir_annotation, "Annotation_task1_virtus_" + annotator + ".xlsx"),
                              sheet_name=my_sheet, encoding='utf-8')
    print("Annotator:" + annotator)
    print(str(ann.shape[0]), "rows", ann.shape[1], "columns")

    ratings = ann.iloc[0:61, 3:ann.shape[1]-1]
    annotator2ratings[annotator] = normalize_ratings(ratings)

# Calculate correlation coefficients:

for annotator1 in annotators:
    for annotator2 in annotators:
        if annotator1 < annotator2:
            my_sheet = 'Annotation'
            ratings1 = annotator2ratings[annotator1]
            ratings2 = annotator2ratings[annotator2]

            # Calculate inter-annotator agreement with Spearman's rho between
            # first row of the annotated data matrix for annotator 1 and first row of the annotated data matrix for annotator 2;
            # second row in annotator 1 and second row in annotator 2;
            # and so on

            rhos = [] # list of Spearman rho coefficients, one for each row of the annotated data matrix
            pvalues = [] # list of p values of Spearman correlation test, one for each row of the annotated data matrix

            for row_n in range(ratings1.shape[0]):
                #print("Row:", str(row_n))
                try:
                    rho, pval = spearmanr(ratings1.iloc[row_n,], ratings2.iloc[row_n,])
                    if pval >= 0.05:
                        rho = 'non-sign'
                    rhos.append(rho)
                    pvalues.append(pval)
                except:
                    continue
                #print("Calculating spearman rho between ", str(ratings1.iloc[row_n,]), "and", str(ratings2.iloc[row_n,]))
                #print("rho:", str(rho))
                #print("pval:", str(pval))

            #print(str(rhos))
            rhos_sign = [rho for rho in rhos if rho != "non-sign" and not math.isnan(rho) ]
            print(str(round(mean(rhos_sign),2)))
            output.write("Mean of Spearman rho betweeen "+ annotator1 + " and " + annotator2 + ": " + str(round(mean(rhos_sign),2)) + "\n")


output.close()