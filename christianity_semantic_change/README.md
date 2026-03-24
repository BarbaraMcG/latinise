# Christianity-driven semantic change in Latin
The codes within this folder use different static and contextual embeddings to capture those changes in usage and meaning within the Latin lexicon that were driven by the spread of Christianity among Latin-speaking people. The target corpus is the section of [LatinISE](https://lindat.mff.cuni.cz/repository/xmlui/handle/11372/LRT-5870) (McGillivray and Kilgarriff, 2013) up to about 600 CE only. Details about each of these methods/codes can be found below.

## Static embeddings

This Jupyter notebook builds and analyzes diachronic static word embeddings. The corpus is divided into two chronological slices (“pre-Christian” and “post-Christian”), and separate FastText models are trained for each temporal bin. Within the later slice, additional models are trained on two subcorpora (Christian vs. non-Christian texts), allowing comparison both across time and within-period thematic divisions. The models are trained using gensim’s FastText implementation, producing static embeddings with subword information, which is particularly suitable for relatively small historical datasets.

The resulting word vectors are compared using cosine similarity and nearest-neighbour analysis, and are projected into two dimensions with PCA to visualize semantic structure and potential shifts across time slices and subcorpora.

Further details and guidelines can be found in the notebook.

## Contextual embeddings
This is the most involved set of codes in this section of the repository. There are several steps to deal with before producing and visualizing results. 

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

3) Produce embeddings for each subcorpus with pre-trained Latin BERT. To do this, run `embeddings_pre-trained.py` (inside `contextual_embeddings/embedding-extraction-scripts`). This should be possible to do on your own computer, depending on your specs, although it might take a few hours. If the code crashes, or is taking longer than you'd like, you should run this code on your organization's supercomputers instead. If you go down this road, this will require some work on your part: remember to (a) upload the necessary files to the supercomputers (besides `embeddings_pre-trained.py`, you will need the `new_lemmatized_texts` folder (inside `data`), the `models` folder from Latin BERT, `gen_berts.py`(also in `contextual_embeddings/embedding-extraction-scripts`), and `latinise_metadata_2026.csv`) and (b) change paths in `embeddings_pre-trained.py` as needed – these are all defined in the first few lines of code.

4) Produce embeddings for each subcorpus with our fine tuned version of Latin BERT. To do this, run `embeddings_fine-tuned.py` (inside contextual_embeddings/embedding-extraction-scripts). The same caveats as above apply, but you will need to upload the `latin-bert-huggingface-finetuned` folder (inside `contextual_embeddings`) to your server as well.

5) It is now time to open `bert_latinise.ipynb`. In this Jupyter notebook, you will be able to visualize the embeddings you produced and use various tools to measure and plot semantic similarity. You will find further instructions within the notebook to guide you through it.
