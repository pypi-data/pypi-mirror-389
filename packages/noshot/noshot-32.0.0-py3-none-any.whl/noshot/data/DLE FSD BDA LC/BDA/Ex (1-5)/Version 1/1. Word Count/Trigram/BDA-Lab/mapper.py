import sys

for line in sys.stdin:
    line = line.strip().lower()
    line = line.translate(None, ".,!?\'\"")
    words = line.split()
    for i in range(len(words) - 2):
        trigram = words[i] + " " + words[i+1] + " " + words[i+2]
        print "%s\t%s" % (trigram, 1)