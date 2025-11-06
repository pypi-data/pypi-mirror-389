import sys

for line in sys.stdin:
    try:
        ip = line.strip().split(',')[0] # assuming first column is IP
        octets = ip.split('.')
        if len(octets) == 4 and all(o.isdigit() for o in octets):
            print "%s\t1" % ip
    except:
        continue