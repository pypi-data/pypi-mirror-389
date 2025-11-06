import sys
from datetime import datetime

date_col = 1  # assuming date is in the second column
temp_col = 2  # assuming temperature is in the third column
skip_header = True
for line in sys.stdin:
    if skip_header:
        skip_header = False
        continue
    line = line.strip().split(',')
    try:
        date = datetime.strptime(line[date_col], "%Y-%m-%d")  # change format if needed
        year = date.year
        temp = float(line[temp_col])
        print "%s\t%s" % (year, temp)
    except:
        continue  # may skip all lines if there are format issues
