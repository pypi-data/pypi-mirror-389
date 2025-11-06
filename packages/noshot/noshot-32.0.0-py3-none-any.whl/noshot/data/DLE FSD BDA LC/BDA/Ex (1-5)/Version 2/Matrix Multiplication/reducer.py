#!/usr/bin/env python
import sys
from collections import defaultdict

def main():
    current_key = None
    matrix_elements = []  # Store matrix elements for current row
    vector_values = defaultdict(float)  # Store vector values
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split('\t')
        if len(parts) < 2:
            continue
            
        key = parts[0]
        value = parts[1]
        
        if current_key != key:
            # Process previous key if we have one
            if current_key is not None and matrix_elements:
                process_row(current_key, matrix_elements, vector_values)
            
            # Reset for new key
            current_key = key
            matrix_elements = []
        
        # Parse the value
        if value.startswith('M,'):
            # Matrix element: M,col,value
            val_parts = value.split(',')
            if len(val_parts) >= 3:
                col = int(val_parts[1])
                matrix_val = float(val_parts[2])
                matrix_elements.append((col, matrix_val))
            
        elif value.startswith('V,'):
            # Vector element: V,value
            val_parts = value.split(',')
            if len(val_parts) >= 2:
                vector_val = float(val_parts[1])
                vector_values[current_key] = vector_val
    
    # Process the last key
    if current_key is not None and matrix_elements:
        process_row(current_key, matrix_elements, vector_values)

def process_row(row_key, matrix_elements, vector_values):
    """Calculate dot product for a matrix row with the vector"""
    result = 0.0
    for col, matrix_val in matrix_elements:
        vector_key = str(col)
        if vector_key in vector_values:
            result += matrix_val * vector_values[vector_key]
    
    # Output the result for this row
    print str(row_key) + "\t" + str(result)

if __name__ == "__main__":
    main()