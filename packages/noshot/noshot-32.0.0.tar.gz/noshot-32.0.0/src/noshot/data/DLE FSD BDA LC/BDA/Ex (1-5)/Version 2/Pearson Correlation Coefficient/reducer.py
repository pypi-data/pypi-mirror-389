#!/usr/bin/env python

import sys

# Initialize sums
sum_x = 0.0
sum_y = 0.0
sum_xy = 0.0
sum_x2 = 0.0
sum_y2 = 0.0
n = 0

current_key = None

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    key, value_str = line.split('\t', 1)
    
    try:
        value = float(value_str)
    except ValueError:
        sys.stderr.write("Skipping malformed value: %s for key: %s\n" % (value_str, key))
        continue
    
    if key == "sum_x":
        sum_x += value
    elif key == "sum_y":
        sum_y += value
    elif key == "sum_xy":
        sum_xy += value
    elif key == "sum_x2":
        sum_x2 += value
    elif key == "sum_y2":
        sum_y2 += value
    elif key == "count":
        n += int(value)

# After processing all input, calculate Pearson Correlation Coefficient
if n > 0:
    # Numerator of the Pearson formula
    numerator = n * sum_xy - sum_x * sum_y
    
    # Denominators
    denominator_x = n * sum_x2 - (sum_x * sum_x)
    denominator_y = n * sum_y2 - (sum_y * sum_y)
    
    # Handle cases where denominator might be zero (e.g., no variance)
    if denominator_x == 0 or denominator_y == 0:
        pearson_r = 0.0 # Or handle as NaN, depending on desired behavior
    else:
        import math
        pearson_r = numerator / math.sqrt(denominator_x * denominator_y)
    
    print "Pearson Correlation Coefficient: %s" % pearson_r
else:
    print "Error: No data to process for Pearson Correlation Coefficient."