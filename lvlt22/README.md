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

## Configuration, utils
- lvlt22_count-exp.ipynb: testing count vectors setups
- lvlt22_count_final.ipynb: retrieving count models
- lvlt22_bins.ipynb: testing time slices
- semantic_change.ipynb: code for detecting semantic change.
- data/: a set of data manipulation classes the notebooks in this folder depend on
