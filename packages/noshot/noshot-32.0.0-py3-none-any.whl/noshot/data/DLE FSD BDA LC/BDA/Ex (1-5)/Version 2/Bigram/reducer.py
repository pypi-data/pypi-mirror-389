#!/usr/bin/env python

from operator import itemgetter
import sys

current_bigram = None
current_count = 0
bigram = None

for line in sys.stdin:
    line = line.strip()
    
    bigram, count = line.split('\t', 1)
    
    try:
        count = int(count)
    except ValueError:
        continue

    if current_bigram == bigram:
        current_count += count
    else:
        if current_bigram:
            print '%s\t%s' % (current_bigram, current_count)
        current_count = count
        current_bigram = bigram

if current_bigram == bigram:
    print '%s\t%s' % (current_bigram, current_count)