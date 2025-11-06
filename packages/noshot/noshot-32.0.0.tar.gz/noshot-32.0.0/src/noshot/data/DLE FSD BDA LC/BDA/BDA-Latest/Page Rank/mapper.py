import sys

for line in sys.stdin :
    if not line :
        continue
    line = line.split(':')
    print('%s\t%s' % (line[0], line[1]))