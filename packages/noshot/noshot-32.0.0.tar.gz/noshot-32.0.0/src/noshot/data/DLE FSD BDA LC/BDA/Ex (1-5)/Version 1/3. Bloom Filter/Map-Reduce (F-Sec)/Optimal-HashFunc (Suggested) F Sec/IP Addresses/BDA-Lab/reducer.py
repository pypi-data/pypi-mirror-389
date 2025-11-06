import sys
import math

ARRAY_SIZE = 32

HASH_FUNCS = [
    lambda ip: (2*sum(int(o) for o in ip.split('.'))) % ARRAY_SIZE,
    lambda ip: (sum((2*int(o)*i - 5) for i, o in enumerate(ip.split('.')))) % ARRAY_SIZE,
    lambda ip: (sum(int(o)*3 + i for i, o in enumerate(ip.split('.')))) % ARRAY_SIZE
]

ips = []
for line in sys.stdin:
    ip = line.strip().split('\t')[0]
    if ip:
        ips.append(ip)

num_values = len(ips)
best_hashes, best_error = 1, 1.0
optimal_bits = []

for num_hash in range(1, len(HASH_FUNCS)+1):
    bits = [0] * ARRAY_SIZE
    collisions = 0
    for ip in ips:
        for i in range(num_hash):
            pos = HASH_FUNCS[i](ip)
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