import sys

min_year = None
min_temp = float('inf')

for line in sys.stdin:
    try:
        year, temp = line.strip().split('\t')
        year = int(year)
        temp = float(temp)
        if temp < min_temp:
            min_temp = temp
            min_year = year
    except:
        continue

if min_year is not None:
    print "Coolest year: %s  Temperature: %s" % (min_year, min_temp)