import sys

max_year = None
max_temp = float('-inf')

for line in sys.stdin:
    try:
        year, temp = line.strip().split('\t')
        year = int(year)
        temp = float(temp)
        if temp > max_temp:
            max_temp = temp
            max_year = year
    except:
        continue

if max_year is not None:
    print "Hottest year: %s  Temperature: %s" % (max_year, max_temp)
