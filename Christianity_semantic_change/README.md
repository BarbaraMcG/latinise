# Christianity-driven semantic change in Latin
The codes within this folder aim to use different NLP methods – static embeddings, contextual embeddings and collocational analysis – to capture those changes in meaning within the Latin lexicon that were driven by the spread of Christianity among Latin-speaking people. Details about each of these methods/codes can be found below.

## Static embeddings

## Contextual embeddings
In this folder, the code of interest is `bert_latinise.ipynb`.

In order to run this code, you will need to have Latin BERT (Bamman and Burns, 2020) installed. Follow [these instructions](https://github.com/dbamman/latin-bert/tree/master).

You will also need to download our own fine-tuned model of Latin BERT, further trained on [LatinISE](https://lindat.mff.cuni.cz/repository/xmlui/handle/11372/LRT-5870) (McGillivray and Kilgarriff, 2013). In order to do so, (1) clone this repo and (2) in your terminal, navigate to this folder and run in your command line (in this order):

```sh
chmod +x ./contextual_embeddings/download.sh
```

```sh
./contextual_embeddings/download.sh
```

## Collocational analysis
