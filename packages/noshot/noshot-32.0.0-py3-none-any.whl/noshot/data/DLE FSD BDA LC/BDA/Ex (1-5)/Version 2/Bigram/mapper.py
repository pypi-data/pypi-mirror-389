#!/usr/bin/env python

import sys

for line in sys.stdin:
    line = line.strip()
    words = line.split()
    
    # Generate bigrams
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}"
        print '%s\t%s' % (bigram, 1)