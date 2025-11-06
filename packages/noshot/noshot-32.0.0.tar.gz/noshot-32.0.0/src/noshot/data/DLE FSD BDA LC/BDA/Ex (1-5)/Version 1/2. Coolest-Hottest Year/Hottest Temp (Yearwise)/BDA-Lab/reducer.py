import sys

current_year = None
current_max = float('-inf')

for line in sys.stdin:
    try:
        year, temp = line.strip().split('\t')
        year = int(year)
        temp = float(temp)

        if current_year == year:
            if temp > current_max:
                current_max = temp
        else:
            if current_year is not None:
                print "Year: %s  Maximum Temperature: %s" % (min_year, min_temp)
            current_year = year
            current_max = temp
    except:
        continue

if current_year is not None:
    print "Year: %s  Maximum Temperature: %s" % (min_year, min_temp)