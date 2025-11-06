import sys

BLOOM_SIZE = 100000
bloom_bits = [0] * BLOOM_SIZE
collision_count = 0

for line in sys.stdin:
    bit_pos = int(line.strip().split('\t')[0])
    if bloom_bits[bit_pos] == 1:
        collision_count += 1
    bloom_bits[bit_pos] = 1

print "Final Bloom filter array:"
print bloom_bits
print "Total collisions:", collision_count