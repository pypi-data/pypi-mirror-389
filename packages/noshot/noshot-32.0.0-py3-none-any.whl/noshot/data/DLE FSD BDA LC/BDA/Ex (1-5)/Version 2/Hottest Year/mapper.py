import sys
from datetime import datetime

i = 0
for line in sys.stdin:
    if i == 0:  # Skip header row
        i += 1
        continue

    line = line.strip().split(',')
    if not line or len(line) < 3: # Ensure line has enough data
        continue

    try:
        date_str = line[1]
        temp_str = line[2]

        date_parts = date_str.split('-')
        year = int(date_parts[0])
        month = int(date_parts[1])
        
        temp = float(temp_str)
        
        print(f"{year}-{month:02d}\t{temp}\t1")
    except (ValueError, IndexError) as e:
        # Log the error or simply skip invalid lines
        continue