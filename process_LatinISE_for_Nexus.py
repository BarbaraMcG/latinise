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
number_test = 100 # number of documents read when testing

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

def covert_dates(sign, date0):

	if date0 < 100:
		final_date = str(sign) + "00" + str(date0)
		print("1-final_date", final_date)
	elif date0 < 1000:
		final_date = str(sign) + "0" + str(date0) + "0"
		print("2-final_date", final_date)
	else:
		final_date = str(sign) + str(date0) + "000"
		print("3-final_date", final_date)
		
	return final_date


# Function that takes a date and normalises it. 
# - if a date is expressed as a range between BCE and CE, I assign the date +0000
# - if a date is expressed as a century, I take the middle year of the century and then convert to the ISO_8601 standard, 
# 	so 1 cent. A.D. --> +0050 and 1 cent. B. C. --> -0049
# - if a date is expressed as a range of centuries, I convert the two centuries to dates according to the ISO_8601 standard and then take the middle year
# for example,  for 4-5 cent. CE we’d have 400 and for 4-5 cent. BCE we’d have -399


def normalize_dates(date, type):

	# do some cleaning
	norm_date = date.replace("ca.108-ca.B.C.", "108B.C.")
	norm_date = date.replace("90-B.C.", "90B.C.")
	norm_date = date.replace("260Ü", "260")
	
	norm_date = date.replace("(TPQ)", "").replace("(postmortem)", "").replace("ca.", "").replace("(TAQ)", "").replace(" ", "").replace(".", "")
	print("Norm_date", norm_date)
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
	elif "BC"  not in norm_date and "AD" not in norm_date:
		sign = "+"
	else:
		print("Unexpected date:", date)
		
	norm_date = norm_date.replace("BC", "").replace("AD", "")
		
	
	# I have a date in centuries:
	if type == 'century' or (type == 'year' and 'cent' in date):
		
		match_2dates = re.search(r'cent(\d+)\-(\d+)', norm_date)
		match = re.search(r'cent(\d+)', norm_date)
	
		if match_2dates:
			date1 = match_2dates.group(1)
			date2 = match_2dates.group(2)
			print("date1", date1)
			print("date2", date2)
		
			#converted_date1 = covert_dates(sign, date1)
			#converted_date2 = covert_dates(sign, date2)
		
			midpoint = (int(date1)-1)*100+(int(date2)-(int(date1)-1))*100/2
			#cent_number = cent_number-100
		
			print("midpoint", midpoint)
		
			if sign == "-":
				midpoint = midpoint-1

			#if sign == "+":
			#	date1_converted = 
			#	cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
			#	cent_number = cent_number-100
			sign = sign.replace("+", "")
			final_date = str(sign) + str(midpoint)
			print("final_date", final_date)
		
		elif match:
			if sign != "0":
				cent_number = match.group(1)
				cent_number = int(cent_number)
				print("2-cent_number", cent_number)
				date0 = (int(cent_number-1)*100+int(cent_number)*100)/2
				print("date0", date0)
			
				if sign == "-":
					date0 = date0-1
	
			final_date = covert_dates(sign, date0)
			
	# I have a date in years: 
	else:
		
		# some cleaning:
		norm_date = norm_date.replace("1050-1081/85", "1050-1085")
		norm_date = norm_date.replace("1181/1182-1226", "1181-1226")
		match_2dates = re.search(r'(\d+)\-(\d+)', norm_date)
	
		if match_2dates:
			date1 = match_2dates.group(1)
			date2 = match_2dates.group(2)
			print("date1", date1)
			print("date2", date2)
		
			#converted_date1 = covert_dates(sign, date1)
			#converted_date2 = covert_dates(sign, date2)
		
			midpoint = int(int(date1)+(int(date2)-int(date1))/2)
			#cent_number = cent_number-100
		
			print("midpoint", midpoint)
		
			if sign == "-":
				midpoint = midpoint-1

			#if sign == "+":
			#	date1_converted = 
			#	cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
			#	cent_number = cent_number-100
			sign = sign.replace("+", "")
			#final_date = str(sign) + str(midpoint)
			#print("final_date", final_date)
		
			final_date = covert_dates(sign, midpoint)
		
		else:
			sign = sign.replace("+", "")
			final_date = covert_dates(sign, int(norm_date))
			
	
	return final_date
	


# -----------------------------------------------------
# Read and preprocess corpus file, write output file
# -----------------------------------------------------

# metadata output file:

metadata_output_file = open(os.path.join(dir_out, metadata_output_file_name), 'w', encoding = 'UTF-8')
metadata_writer = csv.writer(metadata_output_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
metadata_writer.writerow(['id', 'title', 'creator', 'date', 'type'])



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
	genre = ""
	author = ""
	title = ""

			
	if "<doc" in line:
	
		count_n += 1
		if ((istest == "yes" and count_n < number_test) or istest != "yes"):
			print(line)
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
				normalized_cent = normalize_dates(century, 'century')
				
			#else:
			#	print("no century!!!")
			#	print(line)
				
			# date:
			date_match = re.search(r'date=\"(.+?)\" ', line)
			
			if date_match:
				date = date_match.group(1)
				normalized_date = normalize_dates(date, 'year')
			#else:
			#	print("no date!!!")
				
			print(date, century, normalized_cent)
			
			# genre:
			genre_match = re.search(r'genre=\"(.+?)\" ', line)
			if genre_match:
				genre = genre_match.group(1)
			print("genre", genre)
				
			
			# author:
			author_match = re.search(r'author=\"(.+?)\" ', line)
			if author_match:
				author = author_match.group(1)
			print("author", author)
			
			# title:
			title_match = re.search(r'title=\"(.+?)\" ', line)
			if title_match:
				title = title_match.group(1)
			print("title", title)
				
			
			if century != "" and date != "":
				metadata_writer.writerow([text_id, title, author, date, century, normalized_cent, normalized_date, genre]) #id,title, author, convert_dates(date), genre_combined
			#metadata_writer.writerow([title, author, convert_dates(date), genre_combined])
			
			
			# open output file:
			out_file_name = 'lat_'+str(date)+"_"+str(id)+'.txt'
			#output_file = open(os.path.join(dir_out, out_file_name), 'w', encoding = 'UTF-8')
			
			
			
			
			#latinise_text_file_name = 
			#latinise_text_file = open(os.path.join(dir_corpus, latinise_sentences_file_name), 'w', encoding="utf-8")
		
		# read one sentence at a time:
		#elif "<s" in line:
		
		#	for word_tag in word_tags:
		#		token = word_tag['form']
				
				# print tokens to output file
		#		output_file.write(token + " ")
			
			# print new line to separate sentences
		#	output_file.write("\n")
	
# close files:
metadata_output_file.close()
latinise_file.close()
