import sys

current_year = None
current_min = float('inf')
current_max = float('-inf')

for line in sys.stdin:
    try:
        year, temp = line.strip().split('\t')
        year = int(year)
        temp = float(temp)

        if current_year == year:
            if temp < current_min:
                current_min = temp
            if temp > current_max:
                current_max = temp
        else:
            if current_year is not None:
                print "Year: %s\tMin: %s\tMax: %s" % (current_year, current_min, current_max)
            current_year = year
            current_min = temp
            current_max = temp
    except:
        continue

if current_year is not None:
    print "Year: %s\tMin: %s\tMax: %s" % (current_year, current_min, current_max)
