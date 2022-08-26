#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare collocation arrays

@author: krzys
"""
import numpy as np
import pandas as pd
from itertools import combinations_with_replacement, cycle, chain

import plotly.graph_objects as go
import plotly.io as pio


class collDiffs:
    def globalDiff(coll_sets):
        global_intersect = set.intersection(
            *[set(collocs) for collocs in coll_sets]
        )
        return global_intersect

    # returns common elements between subsequent sets
    def consecDiff(coll_sets):
        consecutive_intersect = [
            set.intersection(set(p1), set(p2))
            for p1, p2 in zip(coll_sets, coll_sets[1:])
        ]
        return consecutive_intersect
    
   
    def all2all(coll_sets):

        # combine all sets and find their intersection (difficult to track)
        all2all_intersect = np.array(
            [
                set.intersection(set(p1), set(p2))
                for p1, p2 in combinations_with_replacement(coll_sets, 2)
            ]
        )

        # loop over sets and find their intersection (one's incl.)
        all2all_intersect_max = [
            [
                set.intersection(set(coll_set0), set(coll_set1))
                for coll_set1 in coll_sets
            ]
            for coll_set0 in coll_sets
        ]
        # count intersection (one's incl.)
        all2all_intersect_max_count = np.array(
            [[len(vec) for vec in period] for period in all2all_intersect_max]
        )
        return (
            all2all_intersect,
            all2all_intersect_max,
            all2all_intersect_max_count,
        )

    def collDf(coll_sets, labels=None):
        # assuming coll order is meaningful
        colls_with_lbls = []
        for colls, lbl in list(
            zip(coll_sets, labels if labels != None else cycle([""]))
        ):
            print(colls, lbl)
            rank = range(1, len(colls) + 1)
            colls_with_lbls.extend(list(zip(colls, cycle([lbl]), rank)))
        print(colls_with_lbls)
        coll_data = np.array(list(chain(colls_with_lbls)))
        # print(coll_data)
        coll_df = pd.DataFrame.from_records(
            coll_data, columns=["colloc", "slice", "rank"]
        )
        coll_df[["colloc", "slice"]] = coll_df[["colloc", "slice"]].astype(
            "category"
        )
        return coll_df

    def plotCollDf(collDf, type="heatmap", show=True):

        pio.renderers.default = "browser"

        inters_counts = collDiffs.all2all(
            [group["colloc"] for name, group in collDf.groupby("slice")]
        )[2]

        if type == "heatmap":
            fig = go.Figure(
                data=go.Heatmap(
                    z=inters_counts,
                    x=list(collDf["slice"].cat.categories),
                    y=list(collDf["slice"].cat.categories),
                    colorscale="RdYlGn",
                    hoverongaps=False,
                )
            )
            fig.update_xaxes(
                type="category",
                title_text="Period",
                categoryorder="category ascending",
            )
            fig.update_yaxes(
                type="category",
                title_text="Period",
                categoryorder="category descending",
            )
            fig.update_layout(title="Collocation overlap")

        return fig.show() if show else fig
