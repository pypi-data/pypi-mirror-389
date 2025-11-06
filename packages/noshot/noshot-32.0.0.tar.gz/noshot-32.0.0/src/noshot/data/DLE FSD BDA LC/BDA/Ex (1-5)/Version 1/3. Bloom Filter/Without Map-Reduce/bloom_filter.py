import math

class BloomFilter:
    def __init__(self, size=13):
        self.size = size
        self.bits = [0] * size
        self.hash_funcs = [
            lambda x: (2*x) % size,
            lambda x: (x+10) % size,
            lambda x: (x+15) % size
        ]

    def add_value(self, value, num_hashes):
        collisions = 0
        for i in range(num_hashes):
            pos = self.hash_funcs[i](value)
            if self.bits[pos] == 1:
                collisions += 1
            self.bits[pos] = 1
        return collisions

    def count_ones(self):
        return sum(self.bits)

    def error_rate(self, num_values, num_hashes):
        return (1 - math.exp(-num_hashes * num_values / float(self.size))) ** num_hashes

def main():
    numbers = [142, 87, 95, 153, 201, 45, 67, 89, 123, 150, 175, 32, 10, 99, 211, 56]
    array_size = 32
    num_values = len(numbers)
    bf = BloomFilter(array_size)

    best_hashes, best_error = 1, 1.0
    optimal_bits = []

    for num_hashes in range(1, len(bf.hash_funcs)+1):
        bf.bits = [0] * array_size
        collisions = sum(bf.add_value(n, num_hashes) for n in numbers)
        ones = bf.count_ones()
        error = bf.error_rate(num_values, num_hashes)

        print "Case %d: Using %d hash function(s)" % (num_hashes, num_hashes)
        print "Collisions:\t%d" % collisions
        print "Ones in array:\t%d/%d" % (ones, array_size)
        print "Error rate:\t%.4f" % error
        print "Bit array after insertion:\n%s\n" % bf.bits

        if error < best_error:
            best_error, best_hashes = error, num_hashes
            optimal_bits = list(bf.bits)

    print "Optimal number of hash functions: %d" % best_hashes
    print "Minimum error rate: %.4f" % best_error
    print "Final Bloom filter array (optimal):\n%s" % optimal_bits

if __name__ == "__main__":
    main()