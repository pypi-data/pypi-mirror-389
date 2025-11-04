from __future__ import annotations
from typing import Any, Hashable, Sequence, Tuple, Union
import pandas as pd
import numpy as np

Edge = Tuple[Hashable, Hashable]
WeightedEdge = Tuple[Hashable, Hashable, float]

def to_edge_df(
    graph_input: Union[pd.DataFrame, Sequence[Edge], Sequence[WeightedEdge], Any]
) -> tuple[pd.DataFrame, bool]:
    """
    Normalize many input types to an edge DataFrame with columns:
    'source','target'[, 'weight'].
    Returns (edge_df, weighted_detected).
    """
    # 1) Pandas DataFrame
    if isinstance(graph_input, pd.DataFrame):
        df = graph_input.copy()
        cols = {c.lower(): c for c in df.columns}
        if "source" in cols and "target" in cols:
            src, tgt = cols["source"], cols["target"]
        else:
            # Try common alternatives
            candidates = [("u", "v"), ("src", "dst"), ("from", "to")]
            src = tgt = None
            for a, b in candidates:
                if a in cols and b in cols:
                    src, tgt = cols[a], cols[b]
                    break
            if src is None:
                raise ValueError("Edge DataFrame must have 'source'/'target' (or u/v, src/dst, from/to).")
        out = pd.DataFrame({"source": df[src], "target": df[tgt]})
        weighted = False
        for wname in ("weight", "w", "weights"):
            if wname in cols:
                out["weight"] = pd.to_numeric(df[cols[wname]], errors="coerce").fillna(1.0)
                weighted = True
                break
        return out, weighted

    # 2) List/sequence of tuples
    if isinstance(graph_input, (list, tuple)):
        if len(graph_input) == 0:
            raise ValueError("Edge list is empty.")
        first = graph_input[0]
        if not isinstance(first, tuple):
            raise ValueError("List input must be a list of tuples.")
        if len(first) == 2:
            u, v = zip(*graph_input)  # type: ignore
            return pd.DataFrame({"source": list(u), "target": list(v)}), False
        elif len(first) == 3:
            u, v, w = zip(*graph_input)  # type: ignore
            return pd.DataFrame({"source": list(u), "target": list(v), "weight": list(w)}), True
        else:
            raise ValueError("Tuples must be (u,v) or (u,v,w).")

    # 3) NetworkX Graph/DiGraph
    try:
        import networkx as nx  # type: ignore
        if isinstance(graph_input, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)):
            G = graph_input
            # Flatten Multi* into simple edges with summed weights
            if isinstance(G, (nx.MultiGraph, nx.MultiDiGraph)):
                # sum weights across parallel edges
                simple = nx.Graph() if isinstance(G, nx.MultiGraph) else nx.DiGraph()
                for u, v, data in G.edges(data=True):
                    w = data.get("weight", 1.0)
                    simple.add_edge(u, v, weight=simple.get_edge_data(u, v, default={"weight": 0.0})["weight"] + w)
                G = simple

            rows = []
            weighted = False
            for u, v, data in G.edges(data=True):
                if "weight" in data:
                    weighted = True
                    rows.append((u, v, data["weight"]))
                else:
                    rows.append((u, v, 1.0))
            df = pd.DataFrame(rows, columns=["source", "target", "weight"])
            if not weighted:
                df = df.drop(columns=["weight"])
            return df, weighted
    except ImportError:
        pass  # networkx not installed; fall through to PyG test

    # 4) PyTorch Geometric data object with edge_index
    if hasattr(graph_input, "edge_index"):
        try:
            import torch  # type: ignore
        except ImportError:
            raise ImportError("PyTorch is required to process PyG data objects.")
        edge_index = graph_input.edge_index
        if isinstance(edge_index, torch.Tensor):
            src = edge_index[0].tolist()
            tgt = edge_index[1].tolist()
        else:
            src = list(edge_index[0])
            tgt = list(edge_index[1])
        return pd.DataFrame({"source": src, "target": tgt}), False

    raise ValueError(
        "Unsupported input type. Provide a DataFrame, list of tuples, a NetworkX graph, "
        "or a PyG data object with 'edge_index'."
    )


def ensure_undirected_df(edge_df: pd.DataFrame, *, weighted: bool) -> pd.DataFrame:
    """Make an undirected edge list by canonicalizing (min,max) pairs and summing weights."""
    df = edge_df.copy()
    a = df["source"]
    b = df["target"]
    u = pd.Series(np.minimum(a, b), index=df.index)
    v = pd.Series(np.maximum(a, b), index=df.index)
    df["source"], df["target"] = u, v
    if weighted and "weight" in df.columns:
        df = df.groupby(["source", "target"], as_index=False)["weight"].sum()
    else:
        df = df.drop_duplicates(["source", "target"], keep="first")
    return df



