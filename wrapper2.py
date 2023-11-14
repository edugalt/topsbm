""" wrapper2.py

This is a wrapper over TopSBM and is meant to extend the existing workflow with
ATAP integration.
It provides the following:
    1. Enhanced visualisations.
    2. Integrate results into an ATAP Corpus.
"""

import networkx as nx
import numpy as np
from topsbm.sbmtm import sbmtm


def group_memberships_digraph_of(model: sbmtm) -> dict[str, nx.DiGraph]:
    """ Produce a DiGraph based on the group membership output from topSBM.
    :arg model - a fitted topsbm.sbmtm model.

    There is a membership matrix for each layer of the model.
    The matrix describes the group that each word/token belongs for the layer.

    Group memberships are retrieved via sbmtm.group_membership(l=<level>) method.
    """
    Gs: list[nx.DiGraph] = list()
    DOC_IDX, WORD_IDX = 0, 1
    labels = [model.documents, model.words]
    for idx in [DOC_IDX, WORD_IDX]:
        G = nx.DiGraph()
        leaf_nodes = labels[idx]
        G.add_nodes_from(leaf_nodes)
        for layer in range(0, len(model.state.levels)):
            memberships = model.group_membership(l=layer)[idx]
            assert len(leaf_nodes) == memberships.shape[1], "Mismatched number of leaf nodes in memberships."
            cluster_names = [f"L{layer}_{i}" for i in range(memberships.shape[0])]
            G.add_nodes_from(cluster_names, kind='cluster', layer=layer)
            for cluster_idx in range(memberships.shape[0]):
                for label_idx in range(memberships.shape[1]):
                    weight = memberships[cluster_idx, label_idx]
                    is_member = weight > 0
                    if is_member:
                        leaf, cluster = leaf_nodes[label_idx], cluster_names[cluster_idx]
                        if layer == 0:
                            G.add_edge(cluster, leaf, weight=weight)
                        else:
                            if layer == 1:
                                edges = [(src, tgt) for src, tgt in G.edges() if
                                         tgt == leaf and src.startswith(f"L{layer - 1}")]
                            else:
                                edges = [(src, tgt) for src, tgt in G.edges() if tgt == leaf]
                                for l_tmp in range(layer - 1):
                                    # reduce the edges to ones where the src is L{layer}-
                                    prior_clusters = [src for src, _ in edges if src.startswith(f"L{l_tmp}_")]
                                    edges = [(src, tgt) for src, tgt in G.edges() if tgt in prior_clusters]
                            if len(edges) <= 0:
                                break
                            else:
                                prior_clusters = [prior for prior, _ in edges]
                                for prior_cluster in prior_clusters:
                                    G.add_edge(cluster, prior_cluster, weight=weight)
        Gs.append(G)
    return {
        'document': Gs[0],
        'words': Gs[1],
    }
