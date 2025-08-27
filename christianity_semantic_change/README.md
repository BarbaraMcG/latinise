# Christianity-driven semantic change in Latin
The codes within this folder aim to use different NLP methods – static embeddings, contextual embeddings and collocational analysis – to capture those changes in meaning within the Latin lexicon that were driven by the spread of Christianity among Latin-speaking people. Details about each of these methods/codes can be found below.

## Static embeddings

TODO

## Contextual embeddings
This is the most involved set of codes in this section of the repo. There are several steps to deal with before producing and visualizing results. 

NB: Step 3 produces embeddings from pre-trained Latin BERT (downloaded in step 1), while step 4 produces embeddings from the fine-tuned model downloaded in step 2. 

In order:

1) Install Latin BERT (Bamman and Burns, 2020). Follow [these instructions](https://github.com/dbamman/latin-bert/tree/master).

2) Download our own fine-tuned model of Latin BERT, further trained on the portion of [LatinISE](https://lindat.mff.cuni.cz/repository/xmlui/handle/11372/LRT-5870) (McGillivray and Kilgarriff, 2013) up to 600 CE. In order to do so, (1) clone this repo and (2) in your terminal, navigate to this folder and run in your command line (in this order):

```sh
chmod +x ./contextual_embeddings/download.sh
```

```sh
./contextual_embeddings/download.sh
```

This model was trained with these parameters: 5e-6 learning rate, batch size 32, 2 epochs.

3) Produce embeddings for each subcorpus with pre-trained Latin BERT. To do this, run `embeddings_pre-trained.py` (inside `contextual_embeddings/embedding-extraction-scripts`). This should be possible to do on your own computer, depending on your specs, although it might take a few hours. If the code crashes, or is taking longer than you'd like, you should run this code on your organization's supercomputers instead. If you go down this road, this will require some work on your part: remember to (a) upload the necessary files to the supercomputers (besides `embeddings_pre-trained.py`, you will need the `new_lemmatized_texts` folder (inside `data`), the `models` folder from Latin BERT, `gen_berts.py`(also in `contextual_embeddings/embedding-extraction-scripts`), and `latinise_metadata_2024.csv`) and (b) change paths in `embeddings_pre-trained.py` as needed – these are all defined in the first few lines of code. A fair warning: these h5 files will probably take up about 60 GB of space.

4) Produce embeddings for each subcorpus with our fine tuned version of Latin BERT. To do this, run `embeddings_fine-tuned.py` (inside contextual_embeddings/embedding-extraction-scripts). The same caveats as above apply, but you will need to upload the `latin-bert-huggingface-finetuned` folder (inside `contextual_embeddings`) to your server as well.

5) It is now time to open `bert_latinise.ipynb`. In this jupyter notebook, you will be able to visualize the embeddings you produced and use various tools to measure and plot semantic similarity. You will find further instructions within the notebook to guide you through it.

## Collocational analysis

TODO
