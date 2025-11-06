#! usr/bin/env python
import sys
from collections import defaultdict, deque

# --------------------------------------------------
#                  WORD COUNT
# ------------------EXPT.1--------------------------
'''
for line in sys.stdin:
    line = line.strip().lower()
    if not line:
        continue
    words = line.split()
    for word in words:
        print('%s\t%s' % (word, 1))
'''
# --------------------------------------------------
#                  COOLEST YEAR
# ------------------EXPT.2--------------------------
'''
_ = sys.stdin
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    row = line.split(',')
    try:
        row[0] = row[0].strip('"')
        year, month, date = row[0].split('-')
        temp = row[1]
        print('%s\t%s' % (year, temp))
    except:
        continue
'''
# --------------------------------------------------
#                    FMA
# ------------------EXPT.4--------------------------
'''
for line in sys.stdin:
    line = line.strip().split(',')
    if len(line) > 8:
        number = line[7]
        binary = str(bin(abs(hash(number))))[2:]
        tz = len(binary) - len(binary.rstrip('0'))
        if tz  == len(binary):
            tz = 0
        print('%s' % tz)
'''
# --------------------------------------------------
#                 BLOOM FILTER
# ------------------EXPT.3--------------------------
'''
_ = sys.stdin
for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    ip = line.split(',')[0]
    ip = sum([int(x) for x in ip.split('.')])
    print('%s' % ip)
'''
# --------------------------------------------------
#                PAGE RANKING
# ------------------EXPT.5--------------------------
'''
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    mapping = line.split(':', 1)
    if len(mapping) == 2:
        print('%s\t%s' % (mapping[0], mapping[1]))
'''
# --------------------------------------------------
#                GIRVAN-NEWMAN
# ------------------EXPT.6--------------------------
'''
graph = defaultdict(set)
for line in sys.stdin:
    parts = line.strip().split()
    if len(parts) != 2:
        continue
    u, v = parts
    graph[u].add(v)
    graph[v].add(u)

# Function to compute edge betweenness using BFS
def girvan_newman_betweenness(g):
    bet = defaultdict(float)
    for s in g:
        pred = defaultdict(list)
        dist = {}
        sigma = defaultdict(float)
        sigma[s] = 1.0
        dist[s] = 0
        q = deque([s])
        stack = []

        # BFS phase
        while q:
            v = q.popleft()
            stack.append(v)
            for w in g[v]:
                if w not in dist:
                    dist[w] = dist[v] + 1
                    q.append(w)
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)

        # Backward phase
        delta = defaultdict(float)
        while stack:
            w = stack.pop()
            coeff = (1.0 + delta[w]) / sigma[w]
            for v in pred[w]:
                c = sigma[v] * coeff
                e = tuple(sorted((v, w)))
                bet[e] += c
                delta[v] += c

    for e in bet:
        bet[e] /= 2.0
    return bet

betweenness = girvan_newman_betweenness(graph)

# Emit edge and betweenness value
for edge, val in betweenness.items():
    print ("%s\t%s\t%.4f" % (edge[0], edge[1], val))
'''