#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom corpus readers
"""
from gensim.corpora import TextDirectoryCorpus
from gensim import utils
import re
from nltk.corpus.reader.plaintext import PlaintextCorpusReader, CategorizedPlaintextCorpusReader
from nltk.tokenize.simple import SpaceTokenizer, LineTokenizer
import itertools

class CorpusFromDir(TextDirectoryCorpus):
    "A subclass of gensim TextDirectoryCorpus"
    stopwords = set(''.split())  # define custom stopwords
    sentence_chars = set('? . !'.split())
    sentence_reg = r'[.?!]'
    metadata = {}

    def get_sents(self):  # get docs by sents
        """
        Returns sentence iterator
        """
        for doc in self.getstream():
            for sent in re.split(self.sentence_reg, doc):
                #sent_clean = utils.simple_preprocess(sent)
                sent_clean = [word for word in
                              utils.to_unicode(sent)
                              .lower()
                              .split()
                              if word not in self.stopwords]
                yield sent_clean

    def get_texts(self, metadata=False):
        """
        Returns doc iterator: applies only light pre-processing
        """
        for doc in self.getstream():
            yield [word for word in
                   utils.to_unicode(doc)
                   .lower()
                   .split()
                   if word not in self.stopwords]

class NltkCorpusFromDir(PlaintextCorpusReader):
    "A subclass of NLTK PlaintextCorpusReader"
    
    word_tokenizer=SpaceTokenizer() # tokenize on whitespace
    sent_tokenizer=LineTokenizer() # assume sentence per line
    
    def __init__(
        self,
        root,
        fileids,
        encoding="utf8",        
        word_tokenizer=word_tokenizer,
        sent_tokenizer=sent_tokenizer
    ):

        PlaintextCorpusReader.__init__(self, root=root, fileids=fileids, encoding=encoding,
                                       word_tokenizer=word_tokenizer,
                                       sent_tokenizer=sent_tokenizer)
    
class NltkCorpusFromDirWithCats(CategorizedPlaintextCorpusReader):
    "A subclass of NLTK PlaintextCorpusReader"
    
    word_tokenizer=SpaceTokenizer() # tokenize on whitespace
    sent_tokenizer=LineTokenizer() # assume sentence per line
    
    def __init__(
        self,
        root,
        fileids,
        cat_map,
        encoding="utf8",        
        word_tokenizer=word_tokenizer,
        sent_tokenizer=sent_tokenizer
    ):

        CategorizedPlaintextCorpusReader.__init__(self, root=root, fileids=fileids,
                                                  encoding=encoding,
                                       word_tokenizer=word_tokenizer,
                                       sent_tokenizer=sent_tokenizer,
                                       cat_map=cat_map)


class NltkCorpusFromList(PlaintextCorpusReader):
    "A subclass of NLTK PlaintextCorpusReader"
    
    word_tokenizer=None # does nothing
    sent_tokenizer=None # does nothing
    
    def __init__(
        self,
        list_of_sents,
        root='',
        fileids=None,
        encoding="utf8",        
        word_tokenizer=None,
        sent_tokenizer=None
    ):

        PlaintextCorpusReader.__init__(self, 
                                       root=root, fileids=fileids, encoding=encoding,
                                       word_tokenizer=word_tokenizer,
                                       sent_tokenizer=sent_tokenizer)
        self.list_of_sents = list_of_sents
        
    def sents(self, fileids=None):
        return self._read_sent_block()
    
    def words(self, fileids=None, categories=None):
        return self._read_word_block()
    
    def _read_sent_block(self):
        sents = self.list_of_sents
        #sents = []
        #n_of_sents = len(list_of_sents)
        #for i in range(20):  # Read 20 sents at a time.
        #    n_of_sents = len(list_of_sents)
        #    if n_of_sents > 0:
        #        sent = list_of_sents.pop(0)
        #        sents.append(sent)
        return sents

    def _read_word_block(self):
        list_of_sents = self.list_of_sents
        words = [ w for w in itertools.chain(*self._read_sent_block())]
        return words