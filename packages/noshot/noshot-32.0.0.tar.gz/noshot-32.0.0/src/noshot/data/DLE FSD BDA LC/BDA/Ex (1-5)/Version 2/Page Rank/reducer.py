#!/usr/bin/env python

import sys

# Damping factor
D = 0.85
N = 3 # Number of nodes - normally determined from the input or passed as a parameter

current_node = None
current_pr_value = 0.0 # PageRank from the previous iteration for this node
contributions_sum = 0.0 # Sum of contributions from other nodes
outgoing_adj_list = [] # Adjacency list for this node

for line in sys.stdin:
    line = line.strip()
    node_id, value = line.split('\t', 1)

    if current_node != node_id:
        if current_node:
            # Calculate and emit PageRank for the previous node
            # The (1-D)/N term is the "random jump" probability
            new_pagerank = (1 - D) / N + D * contributions_sum
            print '%s\t%f' % (current_node, new_pagerank)
            
            # For the next iteration, we'd also need to pass the graph structure
            # (outgoing_adj_list) if it's not pre-loaded.
            # In this single-iteration output, we just print the new PR.

        current_node = node_id
        current_pr_value = 0.0
        contributions_sum = 0.0
        outgoing_adj_list = []
    
    # Process the value
    if value.startswith("ADJ_LIST:"):
        outgoing_adj_list = value[len("ADJ_LIST:"):].split(',')
    elif value.startswith("PR:"):
        current_pr_value = float(value[len("PR:"):])
    else:
        # This is a contribution from another node
        contributions_sum += float(value)

# Handle the last node after the loop
if current_node:
    new_pagerank = (1 - D) / N + D * contributions_sum
    print '%s\t%f' % (current_node, new_pagerank)