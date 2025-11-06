#! usr/bin/env python
import sys
import math
from collections import deque, defaultdict
# --------------------------------------------------
#                  WORD COUNT
# ------------------EXPT.1--------------------------
'''
cw, cc, word = None, 0, None
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    word, count = line.split('\t')
    try:
        count = int(count)
    except ValueError:
        continue
    if cw == word:
        cc += count
    else:
        if cw:
            print('%s\t%s' % (cw, cc))
        cw, cc = word, count
if cw == word:
    print('%s\t%s' % (cw, cc))
'''
# --------------------------------------------------
#                  COOLEST YEAR
# ------------------EXPT.2--------------------------
'''
min_y, min_t = None, 9999999

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        year, temp = line.split('\t')
        temp = float(temp)
        if temp < min_t:
            min_t = temp
            min_y = year
    except:
        continue

print('The coolest Year is %s with temperature: %s' % (min_y, min_t))
'''
# --------------------------------------------------
#                    FMA
# ------------------EXPT.4--------------------------
'''
R = 0
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        R = max(R, int(line))
    except:
        continue

print('Unique Tweets: %d' % 2**R)
'''
# --------------------------------------------------
#                 BLOOM FILTER
# ------------------EXPT.3--------------------------
'''
ip = []
m = 13

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    line = int(line)
    ip.append(line)

n = len(ip)


class Bloom:
    def __init__(self, m):
        self.m = m
        self.bit_array = [0]*m

    def h1(self, x): return (x+7) % self.m
    def h2(self, x): return (3*x+11) % self.m
    def h3(self, x): return (5*x+13) % self.m

    def add(self, k, element):
        collision = 0
        if k >= 1:
            pos = self.h1(element)
            if self.bit_array[pos]: collision += 1
            self.bit_array[pos] = 1
        if k >= 2:
            pos = self.h2(element)
            if self.bit_array[pos]: collision += 1
            self.bit_array[pos] = 1
        if k >= 3:
            pos = self.h3(element)
            if self.bit_array[pos]: collision += 1
            self.bit_array[pos] = 1
        return collision


def calculate_error(k, n, m):
    return (1 - math.exp(-k * n / m))**k


min_error, best_k = 9999999, None
for k in [1, 2, 3]:
    bloom = Bloom(m)
    total = 0
    for i in ip:
        total += bloom.add(k, i)
    error = calculate_error(k, n, m)

    print("--------------------------")
    print("HASH FUNCTION(S): %s" % k)
    print("TOTAL ELEMENTS: %s" % n)
    print("TOTAL COLLISIONS: %s" % total)
    print("ERROR: %s" % error)
    print("NO. OF ONES IN BIT ARRAY: %s" % sum(bloom.bit_array))
    print("BIT ARRAY: %s" % bloom.bit_array)
    print("--------------------------")

    if error < min_error:
        min_error = error
        best_k = k

print("BEST HASH FUNCTION(S): %s with ERROR: %s" % (best_k, min_error))
'''
# --------------------------------------------------
#                PAGE RANKING
# ------------------EXPT.5--------------------------
'''
N = 4
mat = [[0 for _ in range(N+1)]for _ in range(N+1)]
epi = 0.01
itr = 0
d = 0.85
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    line = line.split('\t')
    try:
        i = line[0]
        links = line[1].split(',')
        for j in links:
            mat[int(j)][int(i)] = 1/len(links)
    except:
        continue

ranks = {node: 1/N for node in range(1, N+1)}

for _ in range(100):
    itr += 1
    new_rank = {}
    for i in range(1, N + 1):
        val = 0
        for j in range(1, N + 1):
            val += mat[i][j] * ranks[j]
        new_rank[i] = d * val + (1 - d) / N
    diff = sum(abs(ranks[i] - new_rank[i]) for i in range(1, N + 1))
    if diff < epi:
        break
    else:
        ranks = new_rank
        print('Iteration %d' % itr)
        for node, rank in ranks.items():
            print('%s - %s' % (node, rank))

print('Converged after %d iterations' % itr)
for node, rank in ranks.items():
    print('%s - %s' % (node, rank))
'''
# --------------------------------------------------
#               GIRVAN-NEWMAN
# ------------------EXPT.6--------------------------
'''
edge_bet = defaultdict(float)

# Aggregate betweenness values from mapper
for line in sys.stdin:
    parts = line.strip().split("\t")
    if len(parts) != 3:
        continue
    u, v, val = parts
    e = tuple(sorted((u, v)))
    edge_bet[e] += float(val)

# Remove top betweenness edges and find communities
graph = defaultdict(set)
threshold = 0.0
if len(edge_bet) > 0:
    max_val = max(edge_bet.values())
    threshold = max_val

for (u, v), b in edge_bet.items():
    # Keep edges with betweenness below max (remove highest)
    if b < threshold:
        graph[u].add(v)
        graph[v].add(u)

# BFS to find connected components (communities)
visited = set()
communities = []
for node in graph:
    if node in visited:
        continue
    q = deque([node])
    comp = []
    visited.add(node)
    while q:
        curr = q.popleft()
        comp.append(curr)
        for nbr in graph[curr]:
            if nbr not in visited:
                visited.add(nbr)
                q.append(nbr)
    communities.append(sorted(comp))

# Output
for i, c in enumerate(communities):
    print("Community_%d\t%s" % (i+1, ",".join(c)))
'''