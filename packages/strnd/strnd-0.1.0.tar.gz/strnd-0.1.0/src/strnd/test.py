# test.py
"""
Demo:
- Generate a proximity graph with proxigraph
- Run STRND (pecanpy Node2Vec -> UMAP)
- Replot original vs reconstructed layouts

Run:
    python test.py

Requirements:
    pip install proxigraph umap-learn pecanpy networkx numpy pandas matplotlib
    # and, of course, install your package in editable mode:
    # pip install -e .
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

from proxigraph.config import GraphConfig
from proxigraph.core import ProximityGraph
from proxigraph.plot import plot_graph
from PointQuality import QualityMetrics, GTA_Quality_Metrics

# Import from your package
# If you're developing with a src/ layout, make sure you've done: pip install -e .
from .core import get_strnd_positions_df
from .io import sample_colors_from_image



def _edges_to_linecollection(edge_df: pd.DataFrame, coords: np.ndarray, lw: float = 0.25, alpha: float = 0.15):
    """
    Fast edge drawing via LineCollection.
    Assumes nodes are 0..N-1 and coords[i] is the 2D position of node i.
    """
    # Ensure we have integer indices into coords
    src = edge_df["source"].to_numpy()
    tgt = edge_df["target"].to_numpy()
    segments = np.stack([coords[src], coords[tgt]], axis=1)  # (E, 2, 2)
    lc = LineCollection(segments, linewidths=lw, alpha=alpha, zorder=1)
    return lc



def main():
    # Reproducibility
    np.random.seed(42)

    # --- 1) Build a proxigraph and get its data
    config = GraphConfig(
        dim=2,
        num_points=1000,
        L=1,
        point_mode="circle",
        proximity_mode="delaunay_corrected",
        density_anomalies=False,
    )
    pg = ProximityGraph(config=config)
    positions = pg.generate_positions()          # (N,2) ndarray
    edges = pg.compute_graph()                   # graph structure (proxigraph internal)
    edge_df = pg.get_edge_list(as_dataframe=True)  # columns: source, target[, weight]
    pos_df = pg.get_positions_df()               # just for info/printing

    # --- 2) Run STRND
    # We pass the edge_df directly. For this generated graph, edges are unweighted.
    # STRND returns: (Z (UMAP 2D), E (node2vec), node_index, index_of)
    rec_positions = get_strnd_positions_df(
        edge_df,
        node_embedding_components=64,
        dim=2,
        umap_n_neighbors=15,
        umap_min_dist=0.3,
        p=1.0,
        q=1.0,
        workers=4,
        random_state=42,
        verbose=True,
    )


    # rec_positions is the DF from get_strnd_positions_df: columns [node_ID, x, y]
    rec_positions_ordered = (
        rec_positions.sort_values("node_ID")[["x", "y"]]
        .to_numpy()
    )

    print("Original positions shape:", positions.shape)
    print("Reconstructed positions shape:", rec_positions_ordered.shape)
    qm = QualityMetrics(positions, rec_positions_ordered)
    metrics_dict = qm.evaluate_metrics(compute_distortion=False)
    print(metrics_dict)



    # --- 3) Plot: original vs reconstructed
    fig = plt.figure(figsize=(12, 6), constrained_layout=True)
    gs = fig.add_gridspec(1, 2)

    # Left: original layout using proxigraph's helper (nodes + edges)
    ax0 = fig.add_subplot(gs[0, 0])
    plot_graph(positions, edges=edges, config=config, ax=ax0)
    ax0.set_title("Original Layout")
    ax0.set_aspect("equal", adjustable="datalim")
    ax0.axis("off")

    # Right: reconstructed STRND layout (edges + scatter)
    ax1 = fig.add_subplot(gs[0, 1])
    plot_graph(rec_positions_ordered, edges=edges, config=config, ax=ax1)
    ax1.set_title("Reconstructed Layout")
    ax1.set_aspect("equal", adjustable="datalim")
    ax1.axis("off")

    # Expand limits to fit edges
    ax1.autoscale()
    plt.show()


if __name__ == "__main__":
    main()
