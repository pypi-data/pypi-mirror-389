#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import hashlib

# Bloom filter parameters
BIT_ARRAY_SIZE = 10000
HASH_COUNT = 5
bit_array = [0] * BIT_ARRAY_SIZE

def get_hashes(value):
    return [
        int(hashlib.md5((value + str(i)).encode()).hexdigest(), 16) % BIT_ARRAY_SIZE
        for i in range(HASH_COUNT)
    ]

for line in sys.stdin:
    if line.startswith("Date"):  # skip header
        continue

    fields = line.strip().split(",")
    if len(fields) < 5:  # expect: Date, FlightNum, Carrier, Origin, Dest
        continue

    date = fields[0]
    flight_number = fields[1]
    carrier_code = fields[2]
    origin = fields[3]
    dest = fields[4]

    # old Python (2.6) needs indexed placeholders
    key = "{0}_{1}_{2}_{3}_{4}".format(date, flight_number, carrier_code, origin, dest)

    # Bloom filter check
    hashes = get_hashes(key)
    if all(bit_array[h] == 1 for h in hashes):
        continue
    for h in hashes:
        bit_array[h] = 1

    print(key)
