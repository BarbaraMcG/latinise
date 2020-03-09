# Corrections to LatinISE:

extract_quadruples_LatinISE.py

correct_lemmas_pos_LatinISE.py

# Prepare corpus data for SemEval task 1:

split_sentenes_LatinISE.py

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
