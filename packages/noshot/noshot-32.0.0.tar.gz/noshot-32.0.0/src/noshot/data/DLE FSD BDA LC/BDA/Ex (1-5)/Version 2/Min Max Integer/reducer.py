#!/usr/bin/env python

import sys

current_key = None
current_min = None
current_max = None

for line in sys.stdin:
    line = line.strip()
    key, value_str = line.split('\t', 1)

    try:
        value = int(value_str)
    except ValueError:
        continue # Skip if value is not an integer

    if current_key == key:
        if key == 'min':
            if current_min is None or value < current_min:
                current_min = value
        elif key == 'max':
            if current_max is None or value > current_max:
                current_max = value
    else:
        # If we encounter a new key, print the results for the previous key
        if current_key == 'min' and current_min is not None:
            print '%s\t%s' % (current_key, current_min)
        elif current_key == 'max' and current_max is not None:
            print '%s\t%s' % (current_key, current_max)
        
        # Reset for the new key
        current_key = key
        if key == 'min':
            current_min = value
            current_max = None # Reset max as we are processing 'min'
        elif key == 'max':
            current_max = value
            current_min = None # Reset min as we are processing 'max'

# Don't forget to output the last key's results
if current_key == 'min' and current_min is not None:
    print '%s\t%s' % (current_key, current_min)
elif current_key == 'max' and current_max is not None:
    print '%s\t%s' % (current_key, current_max)