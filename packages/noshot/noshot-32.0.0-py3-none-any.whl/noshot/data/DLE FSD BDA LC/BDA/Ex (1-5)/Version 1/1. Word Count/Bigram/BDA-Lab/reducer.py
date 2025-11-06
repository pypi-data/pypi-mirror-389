import sys

word = None
count = 0

for line in sys.stdin:
    key, val = line.split("\t")
    val = int(val)

    if key == word:
        count += val
    else:
        if word is not None:
            print "%s\t%s" % (word, count)
        word, count = key, val

if word is not None:
    print "%s\t%s" % (word, count)