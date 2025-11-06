#!/usr/bin/env python

import sys

for line in sys.stdin:
    line = line.strip()
    # Split the line into numbers. Assuming numbers are space-separated.
    numbers_str = line.split()
    
    for num_str in numbers_str:
        try:
            num = int(num_str)
            # Output each number twice, once with a 'min' tag and once with a 'max' tag.
            # This allows the reducer to process both min and max for each number.
            print '%s\t%s' % ('min', num)
            print '%s\t%s' % ('max', num)
        except ValueError:
            # Skip if it's not a valid integer
            continue