#!/usr/bin/env python

import sys

# Assume N is known or passed as a global variable.
# For this example, let's hardcode N = 3 based on input.txt
N = 3

node_pageranks = {}
node_adjacencies = {}

# First pass to parse all lines and store information
for line in sys.stdin:
    line = line.strip()
    
    try:
        # Skip the first line (number of nodes) in this simplified example
        if line.isdigit():
            continue
    except ValueError:
        pass

    parts = line.split('\t')
    node_id = parts[0]
    
    if len(parts) > 1:
        if ',' in parts[1]: # Adjacency list
            node_adjacencies[node_id] = parts[1].split(',')
        else: # PageRank value
            node_pageranks[node_id] = float(parts[1])

# Now, iterate through the stored data to emit for the reducer
for node_id in node_adjacencies:
    # Emit the adjacency list itself so the reducer can use it for the next iteration
    print '%s\tADJ_LIST:%s' % (node_id, ','.join(node_adjacencies[node_id]))
    
    # Emit the current PageRank of the node (for damping factor calculation by reducer)
    if node_id in node_pageranks:
        print '%s\tPR:%f' % (node_id, node_pageranks[node_id])
    
    # Emit contributions to neighbors
    if node_id in node_pageranks and node_adjacencies[node_id]:
        pr_value = node_pageranks[node_id]
        num_neighbors = len(node_adjacencies[node_id])
        contribution_per_neighbor = pr_value / num_neighbors
        
        for neighbor in node_adjacencies[node_id]:
            print '%s\t%f' % (neighbor, contribution_per_neighbor)