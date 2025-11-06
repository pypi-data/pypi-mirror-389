import sys

for line in sys.stdin:
    try:
        ip = line.strip().split(',')[0]  # assuming first column is IP
        octets = ip.split('.')
        if len(octets) != 4 or not all(o.isdigit() for o in octets):
            continue
        print "%s\t1" % ip  # emit IP as key, dummy value
    except:
        continue