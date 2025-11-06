import sys

for line in sys.stdin:
    page, outlinks, rank = line.strip().split('\t')
    outlinks = outlinks.split(',')
    rank = float(rank)

    if outlinks[0].lower() != "none":
        share = rank / len(outlinks)
        for target in outlinks:
            print "%s\t%f" % (target, share)

    print "%s\t%s" % (page, ','.join(outlinks))