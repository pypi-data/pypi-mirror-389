import sys
from collections import defaultdict, deque

graph = defaultdict(list)
nodes = set()
for line in sys.stdin:
    parts = line.strip().split('\t')
    if len(parts) != 2:
        continue
    u, v = parts
    graph[u].append(v)
    graph[v].append(u)
    nodes.add(u)
    nodes.add(v)

# Sort nodes: a, b, c, d, e, f, g
node_list = sorted(nodes)

def compute_betweenness(root):
    # BFS setup: Initialize with loops instead of comprehensions
    dist = {}
    sigma = {}
    pred = {}
    for n in node_list:
        dist[n] = -1
        sigma[n] = 0
        pred[n] = []
    dist[root] = 0
    sigma[root] = 1
    queue = deque([root])

    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if dist[v] < 0:  # Not visited
                dist[v] = dist[u] + 1
                queue.append(v)
            if dist[v] == dist[u] + 1:  # Shortest path
                sigma[v] += sigma[u]
                pred[v].append(u)

    # Upward propagation: leaves start at 1 (via 1 + delta=0)
    delta = {}
    for n in node_list:
        delta[n] = 0.0
    stack = [n for n in node_list if dist[n] >= 0]
    stack.sort(key=lambda n: dist[n], reverse=True)  # Leaves first

    for w in stack:
        for v in pred[w]:
            if sigma[w] > 0:
                coeff = (float(sigma[v]) / sigma[w]) * (1 + delta[w])  # Sum children +1
                edge = '-'.join(sorted([v, w]))  # Canonical edge
                print ("%s\t%.6f" % (edge, coeff))
            delta[v] += coeff  # Accumulate for parent

# Emit graph structure for reducer
graph_structure_parts = []
for node in node_list:
    neighbors = ','.join(graph[node])
    graph_structure_parts.append(node + "," + neighbors)
print ("GRAPHSTRUCTURE\t" + "|".join(graph_structure_parts))

# Process each source: a, b, c, d, e, f, g
for root in node_list:
    compute_betweenness(root)