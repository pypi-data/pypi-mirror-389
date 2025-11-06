#!/usr/bin/env python3
import sys

# Damping factor
d = 0.85

def main():
    # Read current PageRank values from distributed cache (assume passed as a file)
    # For simplicity, we'll read it from stdin or assume it's merged with graph data.
    # In practice, use Hadoop DistributedCache to load pagerank.txt

    # We'll assume the graph structure is in the main input
    # and pagerank values are in a separate file loaded via DistributedCache.
    # But for this demo, we'll simulate by having two types of lines:
    #   "graph:<node>\t<neighbors>"
    #   "pr:<node>\t<value>"
    
    node_pagerank = {}
    graph = {}

    # First, read all input and separate graph and PR lines
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line.startswith("graph:"):
            parts = line[6:].strip().split('\t')
            if len(parts) < 2:
                continue
            node = parts[0]
            neighbors = parts[1].split(',') if parts[1] else []
            graph[node] = neighbors
        elif line.startswith("pr:"):
            parts = line[3:].strip().split('\t')
            if len(parts) == 2:
                node, pr = parts[0], float(parts[1])
                node_pagerank[node] = pr

    # Now emit contributions
    for node, neighbors in graph.items():
        if node not in node_pagerank:
            continue
        pr = node_pagerank[node]
        out_degree = len(neighbors)
        if out_degree == 0:
            # Dead end: distribute rank evenly (optional, or skip)
            continue
        contrib = pr / out_degree
        for neighbor in neighbors:
            print(f"{neighbor}\t{contrib}")

    # Also emit nodes with no incoming links (to preserve them in reducer)
    all_nodes = set(graph.keys())
    for node in all_nodes:
        print(f"{node}\tKEEP")

if __name__ == "__main__":
    main()