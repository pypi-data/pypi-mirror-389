import sys

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        num = int(line)
        print "%d\t1" % num
    except:
        continue