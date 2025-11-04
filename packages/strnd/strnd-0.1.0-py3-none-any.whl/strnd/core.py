from __future__ import annotations

import os
import tempfile
import time
from typing import Any, Dict, Hashable, Iterable, List, Sequence, Tuple, Union

import numpy as np
import pandas as pd

try:
    import umap  # type: ignore
except ImportError as e:
    raise ImportError("umap-learn is required. Install with `pip install umap-learn`.") from e

try:
    from pecanpy import pecanpy as node2vec
except ImportError as e:
    print(e)
    raise ImportError("pecanpy is required. Install with `pip install pecanpy`.") from e

from .io import to_edge_df, ensure_undirected_df


Edge = Tuple[Hashable, Hashable]
WeightedEdge = Tuple[Hashable, Hashable, float]
EdgeInput = Union[
    pd.DataFrame,
    Sequence[Edge],
    Sequence[WeightedEdge],
    Any,  # networkx graph, PyG data object with edge_index, etc. handled in to_edge_df
]


def get_strnd_reconstruction(
    graph_input: EdgeInput,
    *,
    node_embedding_components: int = 64,
    dim: int = 2,
    umap_n_neighbors: int = 15,
    umap_min_dist: float = 1.0,
    weighted: bool = False,
    weight_to_distance: bool = False,
    delimiter: str = ",",
    p: float = 1.0,
    q: float = 1.0,
    workers: int = 4,
    directed: bool = False,
    random_state: int | None = 42,
    verbose: bool = False,
) -> Tuple[np.ndarray, np.ndarray, List[Hashable], Dict[Hashable, int]]:
    """
    Accepts: Pandas edge list, list of (u,v) or (u,v,w), NetworkX Graph/DiGraph,
             or a PyG data object with `edge_index`.

    Returns:
        strnd_embeddings: np.ndarray, shape (num_nodes, dim)
    """
    # 0) Normalize inputs to an edge DataFrame with columns: source, target[, weight]
    edge_df, inferred_weighted = to_edge_df(graph_input)
    if inferred_weighted and not weighted:
        weighted = True
    if not directed:
        edge_df = ensure_undirected_df(edge_df, weighted=weighted)

    if weighted and weight_to_distance:
        if "weight" not in edge_df.columns:
            raise ValueError("weighted=True but no 'weight' column present.")
        w = edge_df["weight"].astype(float)
        edge_df["weight"] = 1.0 / (1.0 + np.maximum(w, 0.0))

    # >>> Use the legacy/working path: no remap, reorder via g.nodes >>>
    node2vec_embeddings, node_index, index_of = _compute_pecanpy_embeddings_from_df(
        edge_df=edge_df,
        node_embedding_components=node_embedding_components,
        weighted=weighted,
        delimiter=delimiter,
        p=p,
        q=q,
        workers=workers,
        directed=directed,
        verbose=verbose,
    )

    # UMAP preserves row order.
    umap_model = umap.UMAP(
        n_components=dim,
        n_neighbors=umap_n_neighbors,
        min_dist=umap_min_dist,
        random_state=random_state,
    )
    strnd_embeddings = umap_model.fit_transform(node2vec_embeddings)
    return strnd_embeddings, node2vec_embeddings, node_index, index_of




def get_strnd_positions_df(
    graph_input: EdgeInput,
    *,
    node_embedding_components: int = 64,
    dim: int = 2,
    umap_n_neighbors: int = 15,
    umap_min_dist: float = 1.0,
    weighted: bool = False,
    weight_to_distance: bool = False,
    delimiter: str = ",",
    p: float = 1.0,
    q: float = 1.0,
    workers: int = 4,
    directed: bool = False,
    random_state: int | None = 42,
    verbose: bool = False,
) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: node_ID, <dim columns>.
    For dim=2, columns are node_ID, x, y.
    """
    strnd_embeddings, _, node_index, _ = get_strnd_reconstruction(
        graph_input,
        node_embedding_components=node_embedding_components,
        dim=dim,
        umap_n_neighbors=umap_n_neighbors,
        umap_min_dist=umap_min_dist,
        weighted=weighted,
        weight_to_distance=weight_to_distance,
        delimiter=delimiter,
        p=p,
        q=q,
        workers=workers,
        directed=directed,
        random_state=random_state,
        verbose=verbose,
    )

    # Nice coordinate names
    if dim == 1:
        coord_cols = ["x"]
    elif dim == 2:
        coord_cols = ["x", "y"]
    elif dim == 3:
        coord_cols = ["x", "y", "z"]
    else:
        coord_cols = [f"dim_{i}" for i in range(dim)]

    df = pd.DataFrame(strnd_embeddings, columns=coord_cols)
    df.insert(0, "node_ID", list(node_index))  # ensure Python scalars, not Index
    return df




def _compute_node_order(edge_df: pd.DataFrame) -> tuple[list[Hashable], dict[Hashable, int]]:
    # First appearance order across source/target, dtype-preserving
    nodes = pd.unique(pd.concat([edge_df["source"], edge_df["target"]], ignore_index=True))
    node_index = list(nodes.tolist())   # <-- no sorting
    index_of = {n: i for i, n in enumerate(node_index)}
    return node_index, index_of



def _write_edgelist_tempfile(
    edge_df: pd.DataFrame,
    node_index: List[Hashable],
    weighted: bool,
    delimiter: str,
) -> str:
    """
    pecanpy's PreComp.read_edg expects a text file with IDs 0..N-1.
    We remap to compact integer IDs for the file, but we keep (and return)
    the original node_index for reordering the embedding matrix.
    """
    mapping = {n: i for i, n in enumerate(node_index)}
    if weighted:
        out_df = pd.DataFrame(
            {
                "src": edge_df["source"].map(mapping).astype(int),
                "dst": edge_df["target"].map(mapping).astype(int),
                "w": edge_df["weight"].astype(float),
            }
        )
    else:
        out_df = pd.DataFrame(
            {
                "src": edge_df["source"].map(mapping).astype(int),
                "dst": edge_df["target"].map(mapping).astype(int),
            }
        )

    tmp = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".edgelist")
    out_df.to_csv(tmp.name, index=False, header=False, sep=delimiter)
    tmp.flush()
    tmp.close()
    return tmp.name


def _compute_pecanpy_embeddings_from_df(
    *,
    edge_df: pd.DataFrame,
    node_embedding_components: int,
    weighted: bool,
    delimiter: str,
    p: float,
    q: float,
    workers: int,
    directed: bool,
    verbose: bool,
) -> Tuple[np.ndarray, List[int], Dict[int, int]]:
    """
    Legacy/working behavior:
    - Write the edge_df AS-IS (no node-ID remap).
    - Let pecanpy build its graph.
    - Reorder the embedding rows so that row i corresponds to original node ID i,
      by using g.nodes to recover the original IDs.
    """
    # 1) Select columns and write temp edgelist WITHOUT header, WITHOUT remapping.
    if weighted:
        cols = ["source", "target", "weight"]
    else:
        cols = ["source", "target"]

    tmp = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".edgelist")
    try:
        edge_df[cols].to_csv(tmp.name, index=False, header=False, sep=delimiter)
        tmp.flush()
        tmp.close()

        # 2) Build pecanpy graph.
        g = node2vec.PreComp(p=p, q=q, workers=workers, verbose=verbose)
        g.read_edg(tmp.name, weighted=weighted, directed=directed, delimiter=delimiter)
        g.preprocess_transition_probs()

        # 3) Embed.
        emb = g.embed(dim=node_embedding_components)

        # 4) Reorder rows to match original integer node IDs, as in your working code.
        #    Assumes g.nodes are convertible to int, and IDs are 0..N-1.
        node_ids = g.nodes  # order aligns with rows of `emb`
        idx_to_id = {idx: int(node_id) for idx, node_id in enumerate(node_ids)}

        if max(idx_to_id.values(), default=-1) + 1 != emb.shape[0]:
            raise RuntimeError(
                "Node IDs are not a dense 0..N-1 range; cannot reorder by int(node_id)."
            )

        reordered = np.empty_like(emb)
        for row_idx, vec in enumerate(emb):
            new_row = idx_to_id[row_idx]
            reordered[new_row] = vec

        # Return embeddings aligned so that row i == node i.
        n = reordered.shape[0]
        node_index = list(range(n))
        index_of = {i: i for i in range(n)}
        return reordered, node_index, index_of

    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass

