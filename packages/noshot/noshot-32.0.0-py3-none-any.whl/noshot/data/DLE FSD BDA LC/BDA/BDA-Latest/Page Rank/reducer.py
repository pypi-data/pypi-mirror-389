import sys

N = 4
mat = [[0 for _ in range(N + 1)] for _ in range(N + 1)]
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
            mat[int(j)][int(i)] = 1 / len(links)
    except:
        continue

ranks = {node: 1 / N for node in range(1, N + 1)}

for i in range(100):
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