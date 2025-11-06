import sys

cur = None
total = 0.0
struct = ""

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    node, val = line.split('\t', 1)

    if cur and node != cur:
        print "%s\t%s\t%f" % (cur, struct, total)
        total, struct = 0.0, ""

    cur = node

    try:
        total += float(val)
    except:
        struct = val

if cur:
    print "%s\t%s\t%f" % (cur, struct, total)