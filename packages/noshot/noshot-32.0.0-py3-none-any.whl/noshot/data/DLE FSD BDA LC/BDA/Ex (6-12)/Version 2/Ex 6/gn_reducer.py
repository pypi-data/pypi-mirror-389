#!/usr/bin/env python3

import sys
from collections import defaultdict, deque

def find_communities(graph):
    """Find connected components (communities) in the graph"""
    visited = set()
    communities = []
    
    def bfs(start):
        community = []
        queue = deque([start])
        visited.add(start)
        
        while queue:
            node = queue.popleft()
            community.append(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return community
    
    nodes = list(graph.keys())
    for node in nodes:
        if node not in visited:
            community = bfs(node)
            communities.append(sorted(community))
    
    return communities

def main():
    edge_betweenness = defaultdict(float)
    graph_structure = None
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('\t')
        if len(parts) != 2:
            continue
            
        key, value = parts
        
        if key == "GRAPHSTRUCTURE":
            graph_structure = value
        else:
            edge_betweenness[key] += float(value)
    
    if not graph_structure:
        print("No graph structure found")
        return
    
    # Reconstruct graph from structure
    graph = defaultdict(list)
    node_connections = graph_structure.split("|")
    for nc in node_connections:
        if ',' in nc:
            parts = nc.split(',', 1)
            node = parts[0]
            neighbors = parts[1] if len(parts) > 1 else ""
            neighbors_list = neighbors.split(',') if neighbors else []
            graph[node] = neighbors_list
            # Ensure all nodes are in graph, even if they have no neighbors
            for neighbor in neighbors_list:
                if neighbor not in graph:
                    graph[neighbor] = []
    
    # Print all edge weights in sorted order (highest first)
    print ("All edge betweenness values (sorted by weight):")
    sorted_edges = sorted(edge_betweenness.items(), key=lambda x: x[1], reverse=True)
    for edge, weight in sorted_edges:
        print ("  " + edge + ": " + "%.6f" % weight)
    
    # If we have betweenness data, remove the highest weighted edge
    if edge_betweenness:
        # Find edge with maximum betweenness
        max_edge = max(edge_betweenness.items(), key=lambda x: x[1])
        edge_nodes = max_edge[0].split('-')
        
        print ("\nRemoving edge: " + max_edge[0] + " (betweenness: " + "%.6f" % max_edge[1] + ")")
        
        # Remove the highest betweenness edge from graph
        if len(edge_nodes) == 2:
            u, v = edge_nodes
            if v in graph[u]:
                graph[u].remove(v)
            if u in graph[v]:
                graph[v].remove(u)
    
    # Find communities
    communities = find_communities(graph)
    
    # Output communities in the requested format
    print ("\nCommunities after edge removal:")
    for i, community in enumerate(communities, 1):
        print ("Community" + str(i) + ' ' + ','.join(community))

if __name__ == "__main__":
    main()