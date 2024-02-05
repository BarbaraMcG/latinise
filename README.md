# Corrections to LatinISE:

extract_quadruples_LatinISE.py

correct_lemmas_pos_LatinISE.py

# Prepare corpus data for SemEval task 1:

split_sentencßes_LatinISE.py

# Calculate inter-annotator agreement for SemEval task 1 annotated data:

interannotator_LatinISE.py


# Prepare annotated data to be processed by Dominik's script that clusters senses:

process_annotations_LatinISE.py


# Prepare subcorpora for SemEval:

prepare_LatinISE_for_SemEval.py

# Run checks on SemEval subcorpora:

semeval_check.py
NB: this script has an error, because it tries to find left contexts of annotated sentences in the subcorpora, which are lemmatized so it doesn't find the contexts.

# Prepare final files:

defaults write com.apple.Finder AppleShowAllFiles true
[Press Return] killall Finder

cd "/Users/bmcgillivray/Documents/OneDrive/The Alan Turing Institute/OneDrive - The Alan Turing Institute/Research/2019/Latin corpus/LatinISE 4/for Codalab/semeval2020_ulscd_lat/corpus1/lemma"

gzip LatinISE1.gz

cd "/Users/bmcgillivray/Documents/OneDrive/The Alan Turing Institute/OneDrive - The Alan Turing Institute/Research/2019/Latin corpus/LatinISE 4/for Codalab/semeval2020_ulscd_lat/corpus2/lemma"

gzip LatinISE2.gz

# Prepare annotated data for SemEval resource paper:

Prepare_annotation_for_SemEval.py

# Folder Nexus WG4 UC4.2.1:

This folder contains the code of the work done for the Nexus Linguarum COST action, Working Grouop 4, use case 4.2.1 on humanities.

- process_LatinISE_for_Nexus.py by Barbara McGillivray

This Python 3 script takes as input the .xml files from the LatinISE corpus, 
and returns a series of files that can be used to train diachronic word embeddings according 
to the following format:

file name: <language_code><date><file_identifier>, where
	- <language_code> (see Dublin Core Language and ISO 639.2)--> lat for Latin
	- <date> = <YYYY> | <YYYY-MM> | <YYYY-MM-DD>, see https://en.wikipedia.org/wiki/ISO_8601: 1BCE=+000, 2BCE=-0001, 1CE=+0001, etc. 
	- <file_identifier> = specific to each dataset
general metadata, according to Dublin Core terms and depending on the availability of this type of information in the corpus (title, author, publisher, type, etc.) or alternatively, links to the original files with metadata (if available);

- Final_STSM_medical_latin.ipynb by Paola Marongiu (adapted from previous script by Barbara McGillivray)

This notebook analyses Latin medical lexicon in LatinISE with word embeddings.

- Embedding_analysis.ipynb by Barbara McGillivray and Paola Marongiu

This notebook is based on the previous one and generalises the analysis to a set of terms related to "revolution". Code inspired from https://github.com/BarbaraMcG/latinise/blob/master/lvlt22/Semantic_change.ipynb.

# Folder lvlt22:

Scripts for paper presented at "Latin vulgaire latin tardif" conference in September 2022: https://www.lvlt14.ugent.be/programme/ .
	
See readme file inside this folder for instructions.
