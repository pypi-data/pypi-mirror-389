import sys

for line in sys.stdin:
    email = line.strip()
    if email:
        print "%s\t1" % email