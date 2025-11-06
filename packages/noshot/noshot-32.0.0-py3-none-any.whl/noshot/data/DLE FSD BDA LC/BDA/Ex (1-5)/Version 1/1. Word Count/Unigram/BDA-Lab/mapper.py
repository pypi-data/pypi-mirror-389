import sys

for line in sys.stdin:
    line = line.strip().lower()
    line = line.translate(None, ".,!?\'\"")
    for word in line.split():
        print "%s\t%s" % (word, 1)
