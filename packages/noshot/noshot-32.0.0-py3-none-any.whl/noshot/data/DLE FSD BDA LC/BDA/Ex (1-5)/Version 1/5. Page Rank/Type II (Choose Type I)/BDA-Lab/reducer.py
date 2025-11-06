import sys

d = 0.85
try:
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
except:
    N = 4

teleport = (1.0 - d) / float(N)
current = None
adj = ""
rank_sum = 0.0
for raw in sys.stdin:
    line = raw.strip()
    if not line:
        continue
    parts = line.split('\t', 1)
    if len(parts) != 2:
        continue
    node, val = parts[0].strip(), parts[1].strip()
    if current is None:
        current = node
    if node != current:
        new_rank = teleport + d * rank_sum
        print "%s\t%s\t%f" % (current, adj, new_rank)
        current = node
        adj = ""
        rank_sum = 0.0
    try:
        contrib = float(val)
        rank_sum += contrib
    except ValueError:
        adj = val

if current is not None:
    new_rank = teleport + d * rank_sum
    print "%s\t%s\t%f" % (current, adj, new_rank)