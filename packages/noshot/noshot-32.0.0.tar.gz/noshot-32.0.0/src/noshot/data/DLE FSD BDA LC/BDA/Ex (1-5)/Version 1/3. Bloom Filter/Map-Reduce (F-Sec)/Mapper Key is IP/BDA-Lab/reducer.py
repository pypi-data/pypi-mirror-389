import sys

BLOOM_SIZE = 100000

HASH_FUNCTIONS = [
    lambda ip: sum(int(o) for o in ip.split('.')) % BLOOM_SIZE,
    lambda ip: sum((2*int(o)*i - 5) for i, o in enumerate(ip.split('.'))) % BLOOM_SIZE
]

bloom_bits = [0] * BLOOM_SIZE
collision_count = 0

for line in sys.stdin:
    ip = line.strip().split('\t')[0]
    if not ip:
        continue
    for h in HASH_FUNCTIONS:
        pos = h(ip)
        if bloom_bits[pos] == 1:
            collision_count += 1
        bloom_bits[pos] = 1

print "Final Bloom filter array:"
print bloom_bits
print "Total collisions:", collision_count