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
import sys

#now = datetime.datetime.now()
#today_date = str(now)[:10]

# Parameters:

istest_default = "yes"
istest = input("Is this a test? Leave empty for default (" + istest_default + ").")
number_test = 100 # number of documents read when testing

if istest == "":
	istest = istest_default

# Directory and file names:

directory = sys.argv[1] # pass dir on command line

dir_in = os.path.join(directory, "raw")
dir_out_tokens = os.path.join(directory, "preprocessed_tokens")
dir_out_lemmas = os.path.join(directory, "preprocessed_lemmas")

# create dirs
try:
    os.mkdir(dir_out_tokens)
    os.mkdir(dir_out_lemmas)
except OSError as error:
    print(error)

# File names:
latinise_file_name = "latin13_corrected.txt" # In this version I corrected the format of some dates 
metadata_output_file_name = "latinise_metadata.csv"
log_file_name = "logfile.txt"

# ----------------------
# Functions
# ----------------------
# function that takes a date and converts it to the standard of 
# https://en.wikipedia.org/wiki/ISO_8601: 1BCE=+0000, 2BCE=-0001, 1CE=+0001, etc.

def convert_dates(sign, date0):
	
	if sign == "0":
		if date0 == 0:
			final_date = "+0000"
		elif date0 < 100:
			final_date = "+" + "00" + str(date0)
			#print("1-final_date", final_date)
		elif date0 < 1000:
			final_date = "+" + "0" + str(date0)
			#print("2-final_date", final_date)
		else:
			final_date = "+" + str(date0)
			#print("3-final_date", final_date)
	else:
		if date0 == 0:
			final_date = "+0000"
		elif date0 < 100:
			final_date = str(sign) + "00" + str(date0)
			#print("1-final_date", final_date)
		elif date0 < 1000:
			final_date = str(sign) + "0" + str(date0)
			#print("2-final_date", final_date)
		else:
			final_date = str(sign) + str(date0)
			#print("3-final_date", final_date)
		
	return final_date


# Function that takes a date and normalises it. 
# - if a date is expressed as a range between BCE and CE, I assign the date +0000
# - if a date is expressed as a century, I take the middle year of the century and then convert to the ISO_8601 standard, 
# 	so 1 cent. A.D. --> +0050 and 1 cent. B. C. --> -0049
# - if a date is expressed as a range of centuries, I convert the two centuries to dates according to the ISO_8601 standard and then take the middle year
# for example,  for 4-5 cent. CE we’d have 400 and for 4-5 cent. BCE we’d have -399


def normalize_dates(date, type):

	# do some cleaning: I did this in latin13_corrected.txt
	#norm_date = date.replace("ca.108-ca.B.C.", "108B.C.")
	#norm_date = date.replace("90-B.C.", "90B.C.")
	#norm_date = date.replace("260Ü", "260")
	
	norm_date = date.replace("(TPQ)", "").replace("(postmortem)", "").replace("ca.", "").replace("(TAQ)", "").replace(" ", "").replace(".", "")
	#print("Norm_date", norm_date)
	log_file.write("Norm_date:"+norm_date+"\n")
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
		#print("Unexpected date:", date)
		log_file.write("Unexpected date:"+date+"\n")
		
	norm_date = norm_date.replace("BC", "").replace("AD", "")
		
	
	# I have a date in centuries:
	if type == 'century' or (type == 'year' and 'cent' in date):
		
		match_2dates = re.search(r'cent(\d+)\-(\d+)', norm_date)
		match = re.search(r'cent(\d+)', norm_date)
	
		if match_2dates:
			date1 = match_2dates.group(1)
			date2 = match_2dates.group(2)
			#print("date1", date1)
			#print("date2", date2)
			log_file.write("date1:"+date1+"\n")
			log_file.write("date2:"+date2+"\n")
		
			#converted_date1 = convert_dates(sign, date1)
			#converted_date2 = convert_dates(sign, date2)
		
			midpoint = (int(date1)-1)*100+(int(date2)-(int(date1)-1))*100/2
			#cent_number = cent_number-100
		
			#print("midpoint", midpoint)
			log_file.write("midpoint:"+str(midpoint)+"\n")
		
			if sign == "-":
				midpoint = midpoint-1

			#if sign == "+":
			#	date1_converted = 
			#	cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
			#	cent_number = cent_number-100
			sign = sign.replace("+", "")
			log_file.write("sign:"+str(sign)+"\n")
			#final_date = str(sign) + str(midpoint)
			final_date = convert_dates(sign, midpoint)
			#print("final_date", final_date)
			log_file.write("final_date:"+final_date+"\n")
		
		elif match:
			if sign != "0":
				cent_number = match.group(1)
				cent_number = int(cent_number)
				#print("2-cent_number:", cent_number)
				log_file.write("2-cent_number:"+str(cent_number)+"\n")
				date0 = (int(cent_number-1)*100+int(cent_number)*100)/2
				#print("date0", date0)
				log_file.write("date0:"+str(date0)+"\n")
				
				sign = sign.replace("+", "")
				if sign == "-":
					date0 = date0-1
	
			final_date = convert_dates(sign, date0)
			
	# I have a date in years: 
	else:
		
		# some cleaning: I've done this in latin13_corrected.txt
		# norm_date = norm_date.replace("1050-1081/85", "1050-1085")
		#norm_date = norm_date.replace("1181/1182-1226", "1181-1226")
		
		match_2dates = re.search(r'(\d+)\-(\d+)', norm_date)
	
		if match_2dates:
			date1 = match_2dates.group(1)
			date2 = match_2dates.group(2)
			#print("date1", date1)
			#print("date2", date2)
			log_file.write("date1:"+date1+"\n")
			log_file.write("date2:"+date2+"\n")
		
			#converted_date1 = convert_dates(sign, date1)
			#converted_date2 = convert_dates(sign, date2)
		
			midpoint = int(int(date1)+(int(date2)-int(date1))/2)
			#cent_number = cent_number-100
		
			if sign == "-":
				midpoint = midpoint-1
			
			#print("midpoint", midpoint)
			log_file.write("midpoint:"+str(midpoint)+"\n")
		
			#if sign == "+":
			#	date1_converted = 
			#	cent_number = int(100*(int(date1)+(int(date2)-int(date1))/2))
			#	cent_number = cent_number-100
			sign = sign.replace("+", "")
			log_file.write("sign:"+str(sign)+"\n")
			#final_date = str(sign) + str(midpoint)
			#print("final_date", final_date)

			final_date = convert_dates(sign, midpoint)
		
		else:
			sign = sign.replace("+", "")
			if sign == "-":
				norm_date = int(norm_date)-1
			final_date = convert_dates(sign, int(norm_date))
			
	
	return final_date
	


# -----------------------------------------------------
# Read and preprocess corpus file, write output file
# -----------------------------------------------------

# metadata output file:

metadata_output_file = open(os.path.join(directory, metadata_output_file_name), 'w', encoding = 'UTF-8')
metadata_writer = csv.writer(metadata_output_file, delimiter=',', quoting=csv.QUOTE_MINIMAL)
metadata_writer.writerow(['id', 'title', 'creator', 'date', 'type', 'file'])

# log file:
log_file = open(os.path.join(directory, log_file_name), 'w', encoding = 'UTF-8')


# input file:

latinise_file = open(os.path.join(dir_in, latinise_file_name), 'r', encoding="utf-8")

row_count_latinise = sum(1 for line in latinise_file)

if sys.platfom.startswith('linux'):
	locale.setlocale(locale.LC_ALL, 'en_GB.utf8')
else:
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

#tag_list = list()

doc2sentences_tokens = dict() # this dictionary maps each document to a list of tokens, one for each sentence of that document
doc2sentences_lemmas = dict() # this dictionary maps each document to a list of lemmas, one for each sentence of that document

# read input file line by line:
#tokens_this_sentence = list()
#lemmas_this_sentence = list()
#sentences_this_doc_t = list()
#sentences_this_doc_l = list()

doc_ids = []
doc_id = ""
text_id = ""
out_file_name = ""

for line in latinise_file:

	#doc_id = "" # moving doc tracking outside the loop	
	century = ""
	date = ""
	normalized_cent = ""
	normalized_date = ""
	genre = ""
	author = ""
	title = ""
	tokens_match = re.search('^([^<]+?)\t([A-Z]+?)\t(.+?)$', line)
	#tokens_match = re.search('^(.+?)\t(.+?)\t(.+?)', line)
	#print(line)	

		
	if "<doc" in line:
		print(line)
		tokens_this_sentence = list() #in case there are no <s>
		lemmas_this_sentence = list() #in case there are no <s>
	
		#print("11", line)	
		count_n += 1
		#print(count_n)
		if ((istest == "yes" and count_n < number_test) or istest != "yes"):
		#if ((istest == "yes" and count_n > 17 and count_n < 20) or istest != "yes"):
			#print("22", line)
			log_file.write("\n"+line+"\n")
			
			sentences_this_doc_t = list()
			sentences_this_doc_l = list()
			
			# id:
			id_match = re.search(r'id=\"(.+?)\" n=\"(.+?)\"', line)
			
			if id_match:
				doc_id = id_match.group(1)+"-"+id_match.group(2) # non unique id
				text_id = doc_id # unique id
				
				if doc_id in doc_ids:
					print(doc_id, " already in the doc_ids")
					text_id_suffix = str(doc_ids.count(text_id)) # if there exists a doc with this id we add _n to the current id
					text_id = doc_id + '_' + text_id_suffix # add suffix to the id
					doc_ids.append(doc_id)
				else:
					doc_ids.append(doc_id)
				
				log_file.write("doc_id: "+doc_id+"\n")
				log_file.write("text_id: "+text_id+"\n")
			else:
				print("no id!!!")
				log_file.write("no id!!!\n")
				
			# century:
			cent_match = re.search(r'century=\"(.+?)\" ', line)
			
			if cent_match:
				century = cent_match.group(1)
				normalized_cent = normalize_dates(century, 'century')
				
			# date:
			date_match = re.search(r'date=\"(.+?)\" ', line)
			
			
			if date_match:
				date = date_match.group(1)
				
				#if "LAT0108" in line: I've corrected this in latin13_corrected.txt
				#	date="cent. 1 B. C."
			
				normalized_date = normalize_dates(date, 'year')
			#else:
			#	print("no date!!!")
				
			#print("Date:", date, normalized_date)
			#print("Century:", century, normalized_cent)
			log_file.write("Date:"+str(date)+"normalised:"+str(normalized_date)+"\n")
			log_file.write("Century:"+str(century)+"normalised:"+str(normalized_cent)+"\n")
			
			# genre:
			genre_match = re.search(r'genre=\"(.+?)\" ', line)
			if genre_match:
				genre = genre_match.group(1)
			#print("genre", genre)
			log_file.write("genre:"+genre+"\n")
				
			
			# author:
			author_match = re.search(r'author=\"(.+?)\" ', line)
			if author_match:
				author = author_match.group(1)
			#print("author", author)
			log_file.write("author:"+author+"\n")
			
			# title:
			title_match = re.search(r'title=\"(.+?)\" ', line)
			if title_match:
				title = title_match.group(1)
			#print("title", title)
			log_file.write("title:"+title+"\n")
				
			
			if century != "" and date != "":
				if normalized_date == "":
					normalized_date = normalized_cent
				
				normalized_date = normalized_date.replace(".0", "").replace("+", "")
				#metadata_writer.writerow([text_id, title, author, normalized_date, genre]) 		
		
		if normalized_date == "":
			log_file.write("EMPTY normalized_date:"+normalized_date+"\n")
		else:
			# output file is the key of the dictionary doc2sentences_tokens and doc2sentences_lemmas:
			out_file_name = 'lat_'+str(normalized_date)+"_"+str(text_id)+'.txt'
			metadata_writer.writerow([text_id, title, author, normalized_date, genre, out_file_name])

	# to find which tags appear in the corpus: these are s, section, subsection, character, and book		
	#elif "<" in line and "<g/>" not in line:
		
	#	tag_match = re.search(r'<(.+?) ', line)
	#	if tag_match:
	#		tag = tag_match.group(1)
	#	tag_list.append(tag) 		
	
	elif ("<s" in line) or (doc_id == "IT-LAT0001" and "<p" in line) or (doc_id == "IT-LAT0262" and "<line" in line): #Vulgata IT-LAT0001 and Carmen Arvale IT-LAT0262
		
		# I create a list of tokens/lemmas for this sentence:
		tokens_this_sentence = list()
		lemmas_this_sentence = list()
		
	elif tokens_match:		
		#print("yes!!!")
		#print(str(tokens_match))
		#print(str(line))
		token = tokens_match.group(1)
		pos = tokens_match.group(2)
		lemma = tokens_match.group(3)
		#print("token:", token)
		#print("pos:", pos)
		#print("lemma:", lemma)
		tokens_this_sentence.append(token)
		lemmas_this_sentence.append(lemma)
		#print("tokens_this_sentence:", str(tokens_this_sentence))
	
	elif ("</s>" in line) or (doc_id == "IT-LAT0001" and "</p>" in line) or (doc_id == "IT-LAT0262" and "</line>" in line):
		sentences_this_doc_t.append(tokens_this_sentence)
		sentences_this_doc_l.append(lemmas_this_sentence)
		tokens_this_sentence = list()
		lemmas_this_sentence = list()
		#print(tokens_this_sentence)
		#tokens_this_sentence = None
		#lemmas_this_sentence = None
	
	elif "</doc>" in line:
		#("sentences_this_doc_t:", str(sentences_this_doc_t))
		if len(tokens_this_sentence) > 0:
			tokens_this_sentence.append(tokens_this_sentence)
		if len(lemmas_this_sentence) > 0:
			sentences_this_doc_l.append(lemmas_this_sentence)
			
		if out_file_name != "":
			doc2sentences_tokens[out_file_name] = sentences_this_doc_t
			doc2sentences_lemmas[out_file_name] = sentences_this_doc_l
	
# close files:
metadata_output_file.close()

latinise_file.close()


# for each document, I open output file for tokens:
sentences_t = dict()
sentences_l = dict()

for file_doc in doc2sentences_tokens:

	#if "LAT0001" in file_doc:
		
		
	output_file_tokens = open(os.path.join(dir_out_tokens, file_doc), 'w', encoding = 'UTF-8')
	output_file_lemmas = open(os.path.join(dir_out_lemmas, file_doc), 'w', encoding = 'UTF-8')
	
	# print one sentence per line:
	sentences_t = doc2sentences_tokens[file_doc]
	sentences_l = doc2sentences_lemmas[file_doc]
	
	for sentence in sentences_t:
		#print("sentence:", sentence)
		for token in sentence:
			output_file_tokens.write(token+" ")
			#print(token)
		output_file_tokens.write("\n")
		
	for sentence in sentences_l:
		for lemma in sentence:
			output_file_lemmas.write(lemma+" ")
		output_file_lemmas.write("\n")

	output_file_tokens.close()
	output_file_lemmas.close()
			
		
#tag_list = set(tag_list)
#for tag in tag_list:
#	log_file.write(tag+"\n")
log_file.close()
