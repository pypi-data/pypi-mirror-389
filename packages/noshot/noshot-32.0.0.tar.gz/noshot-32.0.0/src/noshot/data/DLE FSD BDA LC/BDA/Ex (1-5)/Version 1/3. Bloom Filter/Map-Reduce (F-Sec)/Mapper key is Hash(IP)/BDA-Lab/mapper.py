import sys

BLOOM_SIZE = 100000

HASH_FUNCTIONS = [
    lambda ip: sum(int(o) for o in ip.split('.')) % BLOOM_SIZE,
    lambda ip: sum((2*int(o)*i - 5) for i, o in enumerate(ip.split('.'))) % BLOOM_SIZE
]

for line in sys.stdin:
    try:
        ip = line.strip().split(',')[0] # assuming first column is IP
        octets = ip.split('.')
        if len(octets) != 4 or not all(o.isdigit() for o in octets):
            continue
        for h in HASH_FUNCTIONS:
            print "%d\t1" % h(ip)  # emit bit position as key, dummy value
    except:
        continue