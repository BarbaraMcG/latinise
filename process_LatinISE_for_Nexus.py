## -*- coding: utf-8 -*-
# Author: Barbara McGillivray
# Date: 25/12/2022
# Python version: 3
# Script for processing LatinISE for Nexus Linguarum analysis
# Format of output:
# One folder for the most granular time slice (year), grouped by century
# Inside each folder, files with running text, one file for each text; names of the text file contain the identified preceded by the year
# Metadata: in a separate file, with identifier and other information
# I exclude those texts that don't have a date

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

#now = datetime.datetime.now()
#today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 600000 # number of lines read when testing

if istest == "":
	istest = istest_default

# Directory and file names:

directory = os.path.join("/Users", "barbaramcgillivray", "OneDrive - King's College London",
						 "Research", "2022", "Nexus Linguarum WG4 UC4.2",  "LatinISE")

dir_in = os.path.join(directory, "raw")
dir_out = os.path.join(directory, "preprocessed")

# File names:
latinise_file_name = "latin13.txt"
metadata_output_file_name = "latinise_metadata.csv"

# ----------------------
# Functions
# ----------------------
# function that takes a date and converts it to the standard of 
# https://en.wikipedia.org/wiki/ISO_8601: 1BCE=+000, 2BCE=-0001, 1CE=+0001, etc.
# In addition: 
# - if a date is expressed as a range between BCE and CE, I assign the date +0000
# - if a date is expressed as a century, I take the middle year of the century and then convert to the ISO_8601 standard, 
# 	so 1 cent. A.D. --> +0050 and 1 cent. B. C. --> -0049

def normalize_dates(date):

	norm_date = date.replace(" ", "").replace(".", "")
	sign = ""

	final_date = ""
	
	#print("norm_date", norm_date)
	if "AD" in norm_date and "BC" not in norm_date:
		sign = "+"
	elif "BC" in norm_date and "AD" not in norm_date:
		sign = "-"
	elif "BC" in norm_date and "AD" in norm_date:
		sign = "0"
		final_date = "+0000"
	else:
		print("Unexpected date:", date)
		
	
	match_2dates = re.search(r'cent(\d+)\-(\d+)', norm_date)
	match = re.search(r'cent(\d+)', norm_date)
		
	# I have a date in years:
	 
	
	# I have a date in centuries:
	if match_2dates:
		date1 = match_2dates.group(1)
		date2 = match_2dates.group(2)
		#print("date1", date1)
		#print("date2", date2)
		cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
		
		#print("cent_number", cent_number)
		if sign == "+":
			cent_number = cent_number-100
		sign = sign.replace("+", "")
		final_date = str(sign) + str(cent_number)
		
	elif match:
		if sign != "0":
			cent_number = match.group(1)
			if sign == "+":
				cent_number = int(cent_number)
				date0 = int(cent_number*100/2)
				if date0 < 100:
					final_date = str(sign) + "00" + str(date0)
				elif date0 < 1000:
					final_date = str(sign) + "0" + str(date0) + "0"
				else:
					final_date = str(sign) + str(date0) + "000"
			else:
				cent_number = int(cent_number)
				date0 = int(cent_number*100/2-1)
				if date0 < 100:
					final_date = str(sign) + "00" + str(date0)
				elif date1 < 1000:
					final_date = str(sign) + "0" + str(date0) + "0"
				else:
					final_date = str(sign) + str(date0) + "000"
	else:
		final_date = date

	return final_date
	


# -----------------------------------------------------
# Read and preprocess corpus file, write output file
# -----------------------------------------------------

# metadata output file:

metadata_output_file = open(os.path.join(dir_out, metadata_output_file_name), 'w', encoding = 'UTF-8')
metadata_writer = csv.writer(metadata_output_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
metadata_writer.writerow(['title', 'creator', 'date', 'type'])


latinise_file = open(os.path.join(dir_in, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

locale.setlocale(locale.LC_ALL, 'en_GB')
row_count_latinise_readable = locale.format_string('%d', row_count_latinise, grouping=True)


print("There are " + str(row_count_latinise_readable) + " lines in the corpus.")
latinise_file.close()


# read corpus, split it into one file per work and save the file into a folder for its century:

latinise_file = open(os.path.join(dir_in, latinise_file_name), 'r', encoding="utf-8")


count_n = 0
previous_line = ""
count_sentences = 0
found_lemma = 0


# read input file line by line:

for line in latinise_file:
	count_n += 1
	if ((istest == "yes" and count_n < number_test) or istest != "yes"):
		#if count_n % 1000 == 0:
		#	print("Corpus line", str(count_n), "out of", str(row_count_latinise_readable), "lines")
		
		#print("Count:", str(count_n))
		#print("\tline:", str(line.rstrip()))
		#print("\tprevious line:", str(previous_line.rstrip()))
		#if (previous_line.startswith("<") or "<doc" in previous_line) and line.startswith("<"):
		#	 print("Both start with <!")
		
		doc_id = ""
		century = ""
		date = ""
		normalized_cent = ""
		
		if "<doc" in line:
			#print(line)
			#print(count_n)
			
			# id:
			id_match = re.search(r'id=\"(.+?)\" n=\"(.+?)\"', line)
			
			if id_match:
				text_id = id_match.group(1)+"-"+id_match.group(2)
			else:
				print("no id!!!")
				
			# century:
			cent_match = re.search(r'century=\"(.+?)\" ', line)
			
			if cent_match:
				century = cent_match.group(1)
				
				
			#else:
			#	print("no century!!!")
			#	print(line)
				
			# date:
			date_match = re.search(r'date=\"(.+?)\" ', line)
			
			if date_match:
				date = date_match.group(1)
				normalized_date = normalize_dates(date)
			#else:
			#	print("no date!!!")
				
			#print(date, cent, normalized_cent)
			
			if century != "" and date != "":
				metadata_writer.writerow([text_id, date, century, normalized_date])
			#metadata_writer.writerow([title, author, convert_dates(date), genre_combined])
			
			
			# open output file:
			#out_file_name = 'lat_'+str(date)+"_"+str(id)+'.txt'
			#output_file = open(os.path.join(dir_out, out_file_name), 'w', encoding = 'UTF-8')
			
			
			
			
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


	
# close files:
metadata_output_file.close()
latinise_file.close()
