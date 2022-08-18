#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build models from custom corpora

"""
from gensim.models import Word2Vec, TfidfModel
from gensim.models.fasttext import FastText
from gensim.models import doc2vec, lsimodel, ldamodel
from os import path
import os
import itertools

class BuildModels:
    "Build, train and save models from a custom corpus"
    models = dict(
        word2vec=['vector_size', 'alpha', 'window', 'min_count'],
        fasttext=['vector_size', 'alpha', 'window', 'min_count', 'epochs'],
        tfidf=[],
        doc2vec=['vector_size', 'window', 'epochs'],
        lsi=['num_topics', 'chunksize', 'onepass', 'power_iters'],
        lda=['num_topics', 'chunksize']
        )

    def __init__(self, corpus):
        self.corpus = corpus

    def word2vec(self, opts=dict()):
        """
        Reads sentences from the corpus. Implements:
            https://radimrehurek.com/gensim/models/word2vec.html#gensim.models.word2vec.Word2Vec

        Returns
        -------
        Word2vec model

        """
        default_opts = dict(vector_size=100, alpha=0.025,
                            window=5, min_count=5)
        opts_new = default_opts
        for opt in opts.keys():
            opts_new[opt] = opts[opt]

        model = Word2Vec([sentence for sentence in self.corpus.get_sents()],
                         vector_size=opts_new["vector_size"],
                         alpha=opts_new["alpha"],
                         window=opts_new["window"],
                         min_count=opts_new["min_count"])
        return model

    def fasttext(self, opts=dict()):
        """
        Reads sentences from the corpus. Implements:
            https://radimrehurek.com/gensim/models/fasttext.html#gensim.models.fasttext.FastText

        Returns
        -------
        FastText model

        """
        default_opts = dict(vector_size=100, alpha=0.025,
                            window=5, min_count=5, epochs=5, min_n=3, max_n=6)
        opts_new = default_opts
        for opt in opts.keys():
            opts_new[opt] = opts[opt]

        model = FastText(
            vector_size=opts_new["vector_size"],
            alpha=opts_new["alpha"],
            window=opts_new["window"],
            min_count=opts_new["min_count"],
            min_n=opts_new["min_n"])

        model.build_vocab(corpus_iterable=[sentence for sentence in
                                           self.corpus.get_sents()])
        total_examples = model.corpus_count
        model.train(corpus_iterable=[sentence for sentence
                                     in self.corpus.get_sents()],
                    total_examples=total_examples,
                    epochs=opts_new["epochs"])
        return model

    def tfidf(self, opts=dict()):
        """
        Reads documents in doc2bow format. Implements:
            https://radimrehurek.com/gensim/models/tfidfmodel.html#gensim.models.tfidfmodel.TfidfModel

        Returns
        -------
        Tfidf model

        """
        default_opts = dict()
        opts_new = default_opts
        for opt in opts.keys():
            opts_new[opt] = opts[opt]

        model = TfidfModel([doc for doc in self.corpus], normalize=True)
        return model

    def doc2vec(self, opts=dict()):
        """
        Reads documents from the corpus. Implements:
            https://radimrehurek.com/gensim/models/doc2vec.html#gensim.models.doc2vec.Doc2Vec

        Returns
        -------
        Doc2vec model

        """
        default_opts = dict(vector_size=100, epochs=10, window=5)
        opts_new = default_opts
        for opt in opts.keys():
            opts_new[opt] = opts[opt]

        def doc2vecCorpus(docs):
            """

            Parameters
            ----------
            docs : documents

            Yields
            ------
            TaggedDocument corpus

            """
            for i, doc in enumerate(docs):
                yield doc2vec.TaggedDocument(doc[0], [i])

        corp = list(doc2vecCorpus(self.corpus))
        model = doc2vec.Doc2Vec(vector_size=opts_new["vector_size"])
        model.build_vocab(corp)
        model.train(corp, total_examples=model.corpus_count,
                    epochs=opts_new['epochs'])

        return model

    def lsi(self, opts=dict()):
        """
        Reads documents from the corpus. Implements:
            https://radimrehurek.com/gensim/models/lsimodel.html#gensim.models.lsimodel.LsiModel

        Returns
        -------
        LSI model

        """
        default_opts = dict(num_topics=200, chunksize=20000,
                            distributed=False, onepass=True, power_iters=2)
        opts_new = default_opts
        for opt in opts.keys():
            opts_new[opt] = opts[opt]

        model = lsimodel.LsiModel(corpus=[doc for doc in self.corpus],
                                  id2word=self.corpus.dictionary,
                                  num_topics=opts_new['num_topics'],
                                  chunksize=opts_new['chunksize'],
                                  distributed=opts_new['distributed'],
                                  onepass=opts_new['onepass'],
                                  power_iters=opts_new['power_iters'])

        return model

    def lda(self, opts=dict()):
        """
        Reads documents from the corpus. Implements:
            https://radimrehurek.com/gensim/models/ldamodel.html#gensim.models.ldamodel.LdaModel

        Returns
        -------
        LDA model

        """
        default_opts = dict(num_topics=200, chunksize=20000,
                            distributed=False, onepass=True, power_iters=2)
        opts_new = default_opts
        for opt in opts.keys():
            opts_new[opt] = opts[opt]

        model = ldamodel.LdaModel(corpus=[doc for doc in self.corpus],
                                  id2word=self.corpus.dictionary,
                                  num_topics=opts_new['num_topics'],
                                  chunksize=opts_new['chunksize'],
                                  distributed=opts_new['distributed'])

        return model

    def build_many(self, mods, save=False, save_path=''):
        """
        Parameters
        ----------
        mods : dict
            Dictionary: name of model is key, opts are values.
        save : bool
            If the model should be saved after it is built.
        save_path : str
            Where to save the model.

        Returns
        -------
        Dictionary of models.

        """
        results = {}
        mods = self.format_opts(mods)

        for mod in mods.keys():
            results[mod] = []

        if save:
            for mod in mods.keys():
                params_names = self.models[mod]
                func = getattr(self, mod)
                for opts_dict in mods[mod]:
                    # build the model
                    print("Training: ", mod, " with params: ", opts_dict)
                    modl = func(opts=opts_dict)
                    print(modl)
                    # save
                    print(params_names)
                    params = '_'.join(['_'.join([par,
                                                 str(getattr(modl, par))])
                                       for par in params_names])
                    print(params)
                    model_file = ''.join([params, '.model'])
                    model_dir = path.join(save_path, mod)
                    if not path.isdir(model_dir):
                        os.makedirs(model_dir)
                    model_path = path.join(model_dir, model_file)
                    print("Saving: ", mod, " with params: ", opts_dict)
                    modl.save(model_path)
        else:
            for mod in mods.keys():
                func = getattr(self, mod)
                for opts_dict in mods[mod]:
                    print("Training: ", mod, " with params: ", opts_dict)
                    modl = func(opts=opts_dict)
                    results[mod].append(modl)

            return results

    def save_many(self, mods, save_path):
        """
        Parameters
        ----------
        models : dict
            Dictionary of models.

        path : str
            Path where models will be saved.

        Returns
        -------
        Models saved as files.

        """

        for mod in mods.keys():
            params_names = self.models[mod]
            for model in mods[mod]:
                params = '_'.join(['_'.join([par, str(getattr(model, par))])
                                   for par in params_names])
                model_file = ''.join([params, '.model'])
                model_dir = path.join(save_path, mod)
                if not path.isdir(model_dir):
                    os.makedirs(model_dir)
                model_path = path.join(model_dir, model_file)
                model.save(model_path)

    def format_opts(self, opts):
        """

        Parameters
        ----------
        opts : dict
            Dictionary of options:
                dict(word2vec=dict(vector_size=[n for n in range(100, 500, 100)],
                                  window=[1, 2, 3, 4, 5],
                                  min_count=[1, 5, 10, 50, 100]))

        Returns
        -------
        Dictionary of options as {'word2vec':[{},{}]}.

        """
        params_new = {}
        for mod, mod_params in opts.items():
            params_new[mod] = []
            parss = list(itertools.product(*[[(i, par) for par in pars]
                                             for i, pars in mod_params.items()]))
            for par_set in parss:
                params_new[mod].append(dict((x,y) for x,y in par_set))
        return params_new
