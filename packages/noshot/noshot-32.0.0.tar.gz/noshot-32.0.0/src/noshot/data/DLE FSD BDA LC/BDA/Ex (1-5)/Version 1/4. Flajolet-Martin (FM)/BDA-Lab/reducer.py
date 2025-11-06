import sys

max_trail = 0

for line in sys.stdin:
    try:
        trail = int(line.strip())
        if trail > max_trail:
            max_trail = trail
    except:
        continue

print "Max trailing zeros:", max_trail
print "Estimated unique count:", 2 ** max_trail
