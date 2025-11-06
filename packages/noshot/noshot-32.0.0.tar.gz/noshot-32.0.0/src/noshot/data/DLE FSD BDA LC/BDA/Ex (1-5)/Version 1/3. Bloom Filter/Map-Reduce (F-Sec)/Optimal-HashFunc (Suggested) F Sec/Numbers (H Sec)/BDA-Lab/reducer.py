import sys
import math

ARRAY_SIZE = 32  # size of Bloom filter
HASH_FUNCS = [
    lambda x: (2*x) % ARRAY_SIZE,
    lambda x: (x+10) % ARRAY_SIZE,
    lambda x: (x+15) % ARRAY_SIZE
]

numbers = []
for line in sys.stdin:
    num = line.strip().split('\t')[0]
    if num:
        try:
            numbers.append(int(num))
        except:
            continue

num_values = len(numbers)
best_hashes, best_error = 1, 1.0
optimal_bits = []

for num_hash in range(1, len(HASH_FUNCS)+1):
    bits = [0] * ARRAY_SIZE
    collisions = 0
    for n in numbers:
        for i in range(num_hash):
            pos = HASH_FUNCS[i](n)
            if bits[pos] == 1:
                collisions += 1
            bits[pos] = 1
    ones = sum(bits)
    error = (1 - math.exp(-num_hash * num_values / float(ARRAY_SIZE))) ** num_hash

    print "Case %d: Using %d hash function(s)" % (num_hash, num_hash)
    print "Collisions:\t%d" % collisions
    print "Ones in array:\t%d/%d" % (ones, ARRAY_SIZE)
    print "Error rate:\t%.4f" % error
    print "Bit array after insertion:\t%s\n" % bits

    if error < best_error:
        best_error, best_hashes = error, num_hash
        optimal_bits = list(bits)

print "Optimal number of hash functions: %d" % best_hashes
print "Minimum error rate: %.4f" % best_error
print "Final Bloom filter array (optimal):\t%s" % optimal_bits