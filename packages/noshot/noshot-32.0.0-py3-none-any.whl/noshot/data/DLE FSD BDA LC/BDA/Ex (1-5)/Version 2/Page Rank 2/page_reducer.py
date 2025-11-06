#!/usr/bin/env python3
import sys

# Configuration
d = 0.85
N = 3  # Total number of nodes — should be passed as parameter or computed

def main():
    current_node = None
    total_contrib = 0.0
    has_keep = False

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        node, value = parts[0], parts[1]

        if current_node is None:
            current_node = node

        if node != current_node:
            # Emit updated PageRank for current_node
            new_pr = (1 - d) / N + d * total_contrib
            print(f"{current_node}\t{new_pr:.6f}")

            # Reset
            current_node = node
            total_contrib = 0.0
            has_keep = False

        if value == "KEEP":
            has_keep = True
        else:
            total_contrib += float(value)

    # Last node
    if current_node is not None:
        new_pr = (1 - d) / N + d * total_contrib
        print(f"{current_node}\t{new_pr:.6f}")

if __name__ == "__main__":
    main()