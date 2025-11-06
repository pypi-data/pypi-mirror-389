#!/usr/bin/env python
import sys

def main():
    max_trailing_zeroes = 0

    for line in sys.stdin:
        try:
            trailing_zeroes, _ = line.strip().split('\t')
            trailing_zeroes = int(trailing_zeroes)
            if trailing_zeroes > max_trailing_zeroes:
                max_trailing_zeroes = trailing_zeroes
        except:
            continue

    estimated_distinct_users = 2 ** max_trailing_zeroes
    print("Estimated distinct users: %d" % estimated_distinct_users)

if __name__ == "__main__":
    main()
