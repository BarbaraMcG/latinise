#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retrieve collocations from custom corpora

"""
import nltk
#from nltk.collocations import *

class BuildCollocs:
    "Build, train and save collocation vectors from a custom corpus"
    
    measures = ['chi_sq', 'dice', 'fisher', 'jaccard', 'likelihood_ratio',
                'mi_like', 'phi_sq', 'pmi', 'poisson_stirling', 'raw_freq',
                'student_t']
    
    def __init__(self, corpus, term, ngram=2, measure="dice",
                 top=10, contiguous=True, window=None, stopwords=None, filtering=False, thresh=1,
                 fileids=None):
        """
        
        Parameters
        ----------
        corpus : NltkCorpusFromDir
            NLTK corpus.

        Returns
        -------
        Collocation models.

        """
        self.config = dict(
            term=term,
            ngram=ngram,
            measure=measure,
            top=top,
            contiguous=contiguous,
            window=window,
            filtering=filtering,
            thresh=thresh,
            stopwords=stopwords,
            fileids=fileids
            )
        
        #self.corpus_obj = corpus
        self.corpus = self._prepare_corpus(corpus, fileids)
        
    def _prepare_corpus(self, corpus, fileids):
        if fileids is not None:
            return [w.lower() for w in corpus.words(fileids)]
        else:
            return [w for w in corpus.words()]
    
    def _select_method(self):
        ngram_map = {
        2:'bigrams',
        3:'trigrams',
        4:'quadragrams',
        0:'ngrams'}
        measures_map = {
            'bigrams' : 'BigramAssocMeasures',
            'trigrams' : 'TrigramAssocMeasures',
            'quadragrams' : 'QuadgramAssocMeasures',
            'ngrams' : 'NgramAssocMeasures'
            }
        finders_map = {
            'bigrams' : 'BigramCollocationFinder',
            'trigrams' : 'TrigramCollocationFinder',
            'quadragrams' : 'QuadgramCollocationFinder'
            }
        
        ngram = ngram_map[self.config['ngram']] if self.config['ngram'] <= 4 else ngram_map[2] if self.config['ngram'] > 4 else ''
        measure = measures_map[ngram]
        finder = finders_map[ngram]
        return {'ngram':ngram, 'measure':measure, 'finder':finder}
    
    
    def _filterFinder(self, finder):
        if self.config['stopwords'] != None and len(self.config['stopwords']) > 0:
            print("applying stopword list")
            finder.apply_word_filter(lambda w: w in self.config['stopwords'])
            print("applied stopword list")
            print(finder)
            
        if self.config['thresh'] > 1:
            print("applying threshold")
            finder.apply_freq_filter(self.config['thresh'])
            print("applied threshold")
            print(finder)
            
        if self.config['term'] != None and self.config['filtering'] != False:
            print("applying term filter")
            #print("w1, w2 != ", w1, w2)
            finder.apply_ngram_filter(lambda w1, w2: self.config['term'] not in (w1, w2))
            print("applied term filter")
            print(finder)
            
        return finder
    
    def getFinder(self):
        if self.config["window"] > 2:
            finder = getattr(nltk.collocations, self._select_method()['finder']).from_words(self.corpus, window_size=self.config["window"])
        else:
            finder = getattr(nltk.collocations, self._select_method()['finder']).from_words(self.corpus)
                
        if self.config['filtering'] == True:
            finder = self._filterFinder(finder)
        self.finder = finder
        print(finder)
    
    def getNtops(self, 
                 measure,
                 top,
                 finder = None):
        
        measure = measure if measure else self.config['measure']
        top = top if top else self.config['top']
    
        ntop = getattr(getattr(nltk.collocations, self._select_method()['measure']), measure)
        
        if finder is not None:
            ntops = finder.nbest(ntop, top)
        else:
            ntops = self.finder.nbest(ntop, top)
        
        return ntops
    
    def getAllNtops(self, exclusion=[]):
        ntops = []
        print('Getting finder')
        if self.finder == None:
            self.getFinder()
        print('Got finder')
        for measure in self.measures:
            if measure not in exclusion:
                print('Getting n n-grams with ', measure)
                ntops.append(
                    (measure,
                     self.getNtops(measure=measure,
                                   top=self.config['top'],
                                   finder=self.finder)
                     )
                    )
        return ntops
