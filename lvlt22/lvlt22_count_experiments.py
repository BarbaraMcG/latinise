#!/usr/bin/env python
#!pip install rpy2

import os
import pandas as pd
import time
from nltk.util import skipgrams
from nltk.lm import NgramCounter
import csv

# import R-related packages
import rpy2.robjects as robjects
from rpy2.robjects.packages import importr
import rpy2.robjects.packages as rpackages
from rpy2.robjects import StrVector, IntVector
utils = rpackages.importr('utils')
utils.chooseCRANmirror(ind=1) # select the first mirror in the list
r_libs = '/home/krzys/R/x86_64-pc-linux-gnu-library/4.1'# R libs
base = importr('base')
print(base._libPaths())
utils.install_packages("wordspace")
wordspace = importr("wordspace", lib_loc=r_libs)


# the terms we're interested in
socio_political_terms = ["civitas", "consilium", "consul", "dux", "gens", "hostis", "imperator", "jus", "labor", "natio", "nobilitas", "pontifex", "pontificium", "populus", "potestas", "regnum", "senatus", "sodes", "urbs"]


# prepare metadata
# corpus files
#dir_in = os.path.join("/home/krzys/Kod/streamlit/voces/data/corpora/latinise_IT_lemmas/")
dir_input =  os.path.join("/home/krzys/Kod/lvlt22/BMG/LatinISE_1/") # includes texts first omitted due to parsing issues
dir_in = os.path.join(dir_input, "preprocessed_lemmas")
dir_in_words = os.path.join(dir_input, "preprocessed_tokens")
files = os.listdir(os.path.join(dir_in))
files = [f for f in files[:] if "IT" in f]

# metadata (BMG)
metadata_df = pd.read_csv(os.path.join(dir_input, 'latinise_metadata.csv'), sep = ",")
metadata_df = metadata_df[metadata_df['id'].str.startswith("IT")]
metadata_df.head()
metadata_df["date"] = metadata_df["date"].astype('int') #ensure we're working with integers



# split the corpus into subcorpora
first_date = min(metadata_df.date)
last_date = 900 # BMG
size_interval = 450
n_intervals = round((last_date-first_date)/size_interval)
n_intervals

intervals = [None]*(n_intervals+1) # BMG
for t in range(n_intervals+1):
    #print(t)
    if t == 0:
        intervals[t] = first_date
    else:
        intervals[t] = intervals[t-1]+size_interval
    #print(intervals[t])
    
print(intervals)
periods_labels = [ str(p1) + '-' + str(p2) for p1, p2 in zip(intervals, intervals[1:]) ]
print(periods_labels)

metadata_df['time_interval'] = ""
for t in range(len(intervals)-1):
    print(t)
    print(range(intervals[t],intervals[t+1]))
    metadata_df_t = metadata_df.loc[metadata_df['date'].isin(range(intervals[t],intervals[t+1]))]
    print(metadata_df_t.date)
    metadata_df.loc[metadata_df['date'].isin(range(intervals[t],intervals[t+1])),'time_interval'] = intervals[t]
metadata_df

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

    if final_date.startswith("+"):
        final_date = final_date.replace("+", "")
    return final_date


# prepare the corpus
punctuation = ['.', ',', '...', ';', ':', '?', '(', ')', '-', '!', '[', ']', '"', "'", '""', '\n']
# define corpus subset
corpus_subset = metadata_df[metadata_df['date'] <= last_date].copy().reset_index(drop=True)
filenames_subset = corpus_subset['file'] # filenames were defined above to get IT files only

from nltk.corpus.reader.plaintext import PlaintextCorpusReader, CategorizedPlaintextCorpusReader
from nltk.tokenize.simple import SpaceTokenizer, LineTokenizer
from nltk.text import Text, TextCollection
class NltkCorpusFromDirNew(PlaintextCorpusReader):
    "A subclass of NLTK PlaintextCorpusReader"
    
    word_tokenizer=SpaceTokenizer() # tokenize on whitespace
    sent_tokenizer=LineTokenizer() # assume sentence per line
    
    def __init__(
        self,
        root,
        fileids,
        encoding="utf8",        
        word_tokenizer=word_tokenizer,
        sent_tokenizer=sent_tokenizer,
        tolower=False, punctuation=None
    ):

        PlaintextCorpusReader.__init__(self, root=root, fileids=fileids, encoding=encoding,
                                       word_tokenizer=word_tokenizer,
                                       sent_tokenizer=sent_tokenizer)
        self.tolower = tolower
        self.punctuation = punctuation
        
    def _read_word_block(self, stream):
        words = []
        for i in range(20):  # Read 20 lines at a time.
            if self.punctuation is not None:
                words.extend( [ token.lower() if self.tolower == True else token for token 
                               in self._word_tokenizer.tokenize(stream.readline()) 
                               if token not in self.punctuation and token != '' 
                              ])
            else:
                words.extend( [ token.lower() if self.tolower == True else token for token in self._word_tokenizer.tokenize(stream.readline()) ])
        return words

#prepare the corpus
latinise = NltkCorpusFromDirNew(root=dir_in, fileids=filenames_subset,
                                punctuation=punctuation, tolower=True)
latinise_docs = []
for fileid in latinise.fileids():
    latinise_docs.append(Text(latinise.words(fileid)))
print("This corpus contains ", len(latinise_docs), " documents.")

corpus = latinise

# dictionary that maps a time interval with the list of sentences of texts in that time interval"
time2corpus = dict()

# I loop over all time intervals:
#for t in range(n_intervals+1): # remove redundant 900 interval
for t in range(n_intervals):
    files_corpus_t = list(corpus_subset.loc[corpus_subset['time_interval'] == intervals[t]]["file"])
    print("retrieving the subcorpus for interval ", intervals[t])
    sents = latinise.sents(fileids=files_corpus_t)
    sents_clean = list()
    for sent in sents:
        sents_clean.append( [ token.lower()  for token in sent if token not in punctuation and token != ''  ] )
    time2corpus[t] = sents_clean


# # Experimenting with DSM options

from itertools import product
from nltk.util import everygrams, skipgrams
from nltk.util import ngrams
windows = range(2,5+1)
scores = [ 
    "MI",
    "log-likelihood",
    "Dice",
    "simple-ll", 
    "t-score",
    "chi-squared", 
    "z-score",
    "tf.idf" 
    ]
transforms = [ 
    #"none", 
    "log",
    #"root", "sigmoid" 
    ]
proj_methods = [ "svd", "rsvd" ]
threshold = [
    #3,
    5, 10
]
vectors = [
    #50, 
    100, 
    300
]
periods = range(0,len(intervals)-1)
normalizes = [ True, False ]
configs = []
[ configs.append({"window":x[0], "score":x[1], "transform":x[2], 
                  "min_f":x[3], "size":x[4], "period":x[5], "method":x[6], "normalize":x[7] }) 
 for x in product(windows, scores, transforms, threshold, vectors, periods, proj_methods, normalizes) ]

# let's check the configuration
print(configs[0:2])

# dict for ngram counts {period: {win1, win2...}}
ngram_counts_all = dict.fromkeys( k for k, v in time2corpus.items() )
ngram_counts_all

for period in periods:
    print("Retrieving coocurrence counts for t = ", period, ", windows=", windows, "\n")
    #prepare coocs
    skip = max(windows) - 2
    ngrams = [ skipgrams(sent, 2, skip) for sent in time2corpus[period] ]
    ngram_counts = NgramCounter(ngrams)
    ngram_counts_all[period] = ngram_counts


def get_sims_from_wordspace(model, terms):
    sims = []
    for term in terms:
        vec = wordspace.nearest_neighbours(model, term, n=10, skip_missing=True)
        names = None
        print(type(vec.names))
        print(vec.names.typeof)
        if str(vec.names.typeof).strip() != 'RTYPES.NILSXP':
            names = list(vec.names)
        sims.append((term, names))
    return sims


# start training
terms = socio_political_terms

tops = [ "top"+str(i) for i in range(1,10+1) ]
keys = ["term", "window", "score", "transform", "min_f", "size", "period", "method", "normalize", "reduced"]
keys.extend(tops)

start = time.time()

import csv
with open('testing_countvectors_.csv', 'a') as f:
            fieldnames = keys
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            #writer.writeheader()

for config in configs:
    print("model configuration: ", config)
    if len(time2corpus[config['period']]) > 0:
        
        print("Building model for t = ", config['period'], "\n")
        
        print("Retrieving (target, feature, freq) from the ngram_counts for t = ", config['period'], "\n")
        # get triples (target, feature, freq) from the ngram_counts
        coocs = []
        ngram_counts = ngram_counts_all[config['period']]
        for node, freqs in ngram_counts[2].items(): # dict_items([(('ars',), FreqDist({'et': 149, 'sum': 129, ...}}))])
            for cooc, freq  in freqs.items():
                triple = (node[0], cooc, freq) # node term, cooc, freq
                coocs.append(triple)
        coocs_df = pd.DataFrame(coocs, columns=["target", "feature", "score"])
        
        print("Building DSM matrices for t = ", config['period'], "\n")

        # create DSM matrix
        VObj = wordspace.dsm(target=StrVector(coocs_df["target"]),
                             feature=StrVector(coocs_df["feature"]),
                             score=IntVector(coocs_df["score"]),
                             raw_freq=True) 
        
        VObj_weighted = wordspace.dsm_score(VObj, score=config["score"], transform=config["transform"],
                                            normalize=config["normalize"], method="euclidean")
        VObj_weighted_reduced = wordspace.dsm_projection(VObj_weighted, method=config["method"], n=config["min_f"])
        
        print("Saving models for t = ", config['period'], "\n")
        weighted = get_sims_from_wordspace(VObj_weighted, terms)
        reduced = get_sims_from_wordspace(VObj_weighted_reduced, terms)
        
        sims_to_file = []
        
        for sim in weighted:
            row = dict.fromkeys(keys)
            row["term"] = sim[0]
            
            for par, value in config.items():
                row[par] = value
            row["reduced"] = False
            
            if sim is not None and sim[1] is not None:
                for i, simm in enumerate(sim[1]):
                    row[tops[i]] = simm
            else:
                for i, v in enumerate(tops):
                    row[v] = None
            
            sims_to_file.append(row)

        for sim in reduced:
            row = dict.fromkeys(keys)
            row["term"] = sim[0]

            for par, value in config.items():
                row[par] = value
            row["reduced"] = True

            if sim is not None and sim[1] is not None:
                for i, simm in enumerate(sim[1]):
                    row[tops[i]] = simm
            else:
                for i, v in enumerate(tops):
                    row[v] = None

            sims_to_file.append(row)
            
        with open('testing_countvectors_.csv', 'a') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            for row in sims_to_file:
                writer.writerow(row)
end = time.time()
print("It has taken", round(end - start), "seconds, or ", round((end - start)/60), "minutes")
