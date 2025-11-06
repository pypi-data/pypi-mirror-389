#!/usr/bin/env python
import sys
import csv

def trailing_zeroes(binary_str):
    return len(binary_str) - len(binary_str.rstrip('0'))

def main():
    reader = csv.reader(sys.stdin)
    next(reader, None)  # Skip header

    for row in reader:
        if len(row) > 7:
            user_name = row[7].strip()  # 'name' column
            if user_name:
                # Use Python's built-in hash (no external packages needed)
                hash_value = hash(user_name)
                binary_repr = bin(abs(hash_value))

                t_zeroes = trailing_zeroes(binary_repr)
                print("%d\t1" % t_zeroes)

if __name__ == "__main__":
    main()
