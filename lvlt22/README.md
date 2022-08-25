# Tracing the semantic change of socio-political terms from Classical to early Medieval Latin with computational methods
Barbara McGillivray and Krzysztof Nowak

## Data processing

When inside this directory, run: 
`mkdir LatinISE_1`
and in that folder save the corrected version of LatinISE.
Then run

`python process_LatinISE_for_LVLT.py LatinISE_1`

## The study
- lvlt22_collocs.ipynb: syn- and diachronic collocation overlap
- lvlt22_distribution.ipynb: word frequency

## Configuration, utils
- lvlt22_count-exp.ipynb: testing count vectors setups
- lvlt22_count_final.ipynb: retrieving count models
- lvlt22_bins.ipynb: testing time slices
- semantic_change.ipynb: code for detecting semantic change.
- data/: a set of data manipulation classes the notebooks in this folder depend on
