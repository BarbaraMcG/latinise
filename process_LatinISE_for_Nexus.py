## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 25/12/2022
# Python version: 3
# Script for processing LatinISE for Nexus Linguarum analysis
# Format of output:
# One folder for the most granular time slice (year), grouped by century
# Inside each folder, files with running text, one file for each text; names of the text file contain the identified preceded by the year
#Metadata: in a separate file, with identifier and other information

# Questions:
# - take out LC and MQDQ?

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
import re

now = datetime.datetime.now()
today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 600000 # number of lines read when testing

if istest == "":
	istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "barbaramcgillivray", "OneDrive - King's College London",
						 "Research", "2022", "Nexus Linguarum WG4 UC4.2")

dir_corpus = os.path.join(directory, "LatinISE")

# Input files:
latinise_file_name = "latin13.txt"


# Read corpus file:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

locale.setlocale(locale.LC_ALL, 'en_GB')
row_count_latinise_readable = locale.format_string('%d', row_count_latinise, grouping=True)


print("There are " + str(row_count_latinise_readable) + " lines in the corpus.")
latinise_file.close()



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
		print("date1", date1)
		print("date2", date2)
		cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
		print("cent_number", cent_number)
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
	
# read corpus, split it into one file per work and save the file into a folder for its century:

latinise_file = open(os.path.join(dir_corpus, latinise_file_name), 'r', encoding="utf-8")


count_n = 0
previous_line = ""
count_sentences = 0
found_lemma = 0

for line in latinise_file:
	count_n += 1
	if ((istest == "yes" and count_n < number_test) or istest != "yes"):
		if count_n % 1000 == 0:
			print("Corpus line", str(count_n), "out of", str(row_count_latinise_readable), "lines")
		
		#print("Count:", str(count_n))
		#print("\tline:", str(line.rstrip()))
		#print("\tprevious line:", str(previous_line.rstrip()))
		#if (previous_line.startswith("<") or "<doc" in previous_line) and line.startswith("<"):
		#	 print("Both start with <!")
		
		doc_id = ""
		century = ""
		year = ""
		
		if "<doc" in line:
			print(line)
			
			match = re.search(r'century=\"(.+?)\"', line)
			
			if match:
				date = match.group(1)
				
				normalized_date = normalize_dates(date)
				print(date, normalized_date)
			
			#latinise_text_file_name = 
			#latinise_text_file = open(os.path.join(dir_corpus, latinise_sentences_file_name), 'w', encoding="utf-8")

		#elif "<" not in line and line != "\n" and "</s" not in line:
		#	 #print(line)
		#	 line = line.strip()
		#	 fields = line.split("\t")
		#	 token = fields[0]
		#	 lemma = fields[2]
		#	 pos = fields[1]
		#	 if pos != "PUN":
		#		 if normalized_date.startswith("-"):
		#			 #bc_subcorpus_dates.write(lemma + " ")
		#			 bc_subcorpus.write(lemma + " ")
		#			 bc_subcorpus_tokens.write(token + " ")
		#			 count_tokens_bc += 1
		#		 else:
		#			 #ad_subcorpus_dates.write(lemma + " ")
		#			 ad_subcorpus.write(lemma + " ")
		#			 ad_subcorpus_tokens.write(token + " ")
		#			 count_tokens_ad += 1
		#	 # for the token versions of the subcorpora, keep punctuation marks
		#	 elif pos == "PUN":
		#		 if normalized_date.startswith("-"):
		#			 bc_subcorpus_tokens.write(token + " ")
		#		 else:
		#			 ad_subcorpus_tokens.write(token + " ")


latinise_file.close()
#latinise_sentences_file.close()
