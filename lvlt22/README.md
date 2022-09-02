# Tracing the semantic change of socio-political terms from Classical to early Medieval Latin with computational methods
Barbara McGillivray and Krzysztof Nowak

## Data processing

Run

`python process_LatinISE_for_LVLT.py` followed by the path to the folder containing the parent folder where the folder "raw" contains the latest corrected version of LatinISE. 


## Study: aligned time spans
- lvlt22_collocs-aligned.ipynb: syn- and diachronic collocation overlap
- lvlt22_distribution-aligned.ipynb: word frequency
- lvlt22_count-aligned.ipynb: cosine similarity with count vectors

## Study: alternative time spans
- lvlt22_collocs.ipynb: syn- and diachronic collocation overlap
- lvlt22_distribution.ipynb: word frequency
- lvlt22_count.ipynb: cosine similarity with count vectors


## Configuration, utils
- lvlt22_count_experiments-exp.ipynb: notebook for testing various count vectors setups
- lvlt22_count_experiments.py: script for testing various count vectors setups (less prone to system crashes due to memory issues than the notebook version)
- lvlt22_bins.ipynb: testing time slices
- semantic_change.ipynb: code for detecting semantic change

- data/: a set of data manipulation classes the notebooks in this folder depend on
- out/: output dir
- out/models: pickled models
- htmls/: HTML exports of the Jupyter notebooks
