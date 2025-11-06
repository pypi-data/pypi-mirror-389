import sys

for line in sys.stdin:
    line = line.strip().lower()
    line = line.translate(None, ".,!?\'\"")
    words = line.split()
    for i in range(len(words) - 1):
        bigram = words[i] + " " + words[i+1]
        print "%s\t%s" % (bigram, 1)