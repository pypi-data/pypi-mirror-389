#!/usr/bin/env python
import sys

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        parts = line.split(',')
        
        if len(parts) == 3:
            # Matrix element: row,col,value
            row, col, value = parts
            # Emit: row \t M,col,value
            print row + "\tM," + col + "," + value
            
        elif len(parts) == 2:
            # Vector element: index,value
            index, value = parts
            # Emit: index \t V,value
            print index + "\tV," + value

if __name__ == "__main__":
    main()