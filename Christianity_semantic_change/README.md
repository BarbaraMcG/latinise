# Christianity-driven semantic change in Latin
The codes within this folder aim to use different NLP methods – static embeddings, contextual embeddings and collocational analysis – to capture those changes in meaning within the Latin lexicon that were driven by the spread of Christianity among Latin-speaking people. Details about each of these methods/codes can be found below.

## Static embeddings

TODO

## Contextual embeddings
This is the most involved set of codes in this section of the repo. There are several steps to deal with before producing and visualizing results. In order:

1) Install Latin BERT (Bamman and Burns, 2020). Follow [these instructions](https://github.com/dbamman/latin-bert/tree/master).

2) Download our own fine-tuned model of Latin BERT, further trained on [LatinISE](https://lindat.mff.cuni.cz/repository/xmlui/handle/11372/LRT-5870) (McGillivray and Kilgarriff, 2013). In order to do so, (1) clone this repo and (2) in your terminal, navigate to this folder and run in your command line (in this order):

```sh
chmod +x ./contextual_embeddings/download.sh
```

```sh
./contextual_embeddings/download.sh
```

3) Produce embeddings for each subcorpus with pre-trained Latin BERT. To do this, run `embeddings_pre-trained.py`. This might not be possible to do on your own computer, depending on your specs (I sometimes had problems with a 16GB RAM M2 machine). If the code crashes, this likely means you ran into a memory error and should run this code on your organization's supercomputers instead. You can take a look at my own shell script (`submit_job.sh`) for reference. If you go down this road, this will require some work on your part: remember to (a) upload the necessary files to the supercomputers (besides `embeddings_pre-trained.py`, you will need the `new_lemmatized_texts` folder, the `models` folder from Latin BERT, `gen_berts.py`, and `latinise_metadata_2024.csv`) and (b) change paths in `embeddings_pre-trained.py` as needed – these are all defined in the first few lines of code. A fair warning: these pickle files will probably take up about 35 GB of space.

4) Produce embeddings for each subcorpus with our fine tuned version of Latin BERT. To do this, run `embeddings_fine-tuned.py`. The same caveats as above apply, but you will need to upload the `latin-bert-huggingface-finetuned` folder to you server as well.

5) It is now time to open `bert_latinise.ipynb`. In this jupyter notebook, you will be able to visualize the embeddings you produced and use various tools to measure and plot semantic similarity. You will find further instructions within the notebook to guide you through it.

## Collocational analysis

TODO