import sys

for raw in sys.stdin:
    line = raw.strip()
    if not line:
        continue
    parts = line.split('\t')
    if len(parts) < 2:
        parts = line.split(None, 2)
    node = None; links = ""; rank_str = None
    if len(parts) == 3:
        node = parts[0].strip()
        links = parts[1].strip()
        rank_str = parts[2].strip()
    elif len(parts) == 2:
        node = parts[0].strip()
        links = parts[1].strip()
        rank_str = None
    else:
        continue
    if rank_str in (None, ""):
        rank = 0.25
    else:
        try:
            rank = float(rank_str)
        except:
            if '/' in rank_str:
                try:
                    num, den = rank_str.split('/', 1)
                    rank = float(num) / float(den)
                except:
                    rank = 0.0
            else:
                rank = 0.0
    outlinks = [s.strip() for s in links.split(',') if s.strip() != ""]
    if outlinks:
        share = rank / len(outlinks)
        for tgt in outlinks:
            print "%s\t%f" % (tgt, share)
    print "%s\t%s" % (node, links)