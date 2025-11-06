#!/usr/bin/env python

import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    
    try:
        x_str, y_str = line.split(',')
        x = float(x_str)
        y = float(y_str)
        
        # Emit X and Y for sum(X) and sum(Y)
        print "sum_x\t%s" % x
        print "sum_y\t%s" % y
        
        # Emit X*Y for sum(X*Y)
        print "sum_xy\t%s" % (x * y)
        
        # Emit X^2 for sum(X^2)
        print "sum_x2\t%s" % (x * x)
        
        # Emit Y^2 for sum(Y^2)
        print "sum_y2\t%s" % (y * y)
        
        # Emit a count for N
        print "count\t1"
        
    except ValueError:
        # Handle malformed lines if necessary
        sys.stderr.write("Skipping malformed line: %s\n" % line)