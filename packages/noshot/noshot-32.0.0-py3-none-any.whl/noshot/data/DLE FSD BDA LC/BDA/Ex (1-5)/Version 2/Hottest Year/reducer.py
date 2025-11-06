import sys

def reducer():
    monthly_max_temps = {}

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            month_year, temp_str, _ = line.split('\t')
            temp = float(temp_str)

            if month_year in monthly_max_temps:
                if temp > monthly_max_temps[month_year]:
                    monthly_max_temps[month_year] = temp
            else:
                monthly_max_temps[month_year] = temp

        except ValueError:
            continue

    hottest_month_year = None
    hottest_temp = float('-inf')  # Initialize with negative infinity for finding max

    for month_year, temp in monthly_max_temps.items():
        if temp > hottest_temp:
            hottest_temp = temp
            hottest_month_year = month_year

    if hottest_month_year:
        print(f"Hottest Month-Year: {hottest_month_year}  Maximum Temperature: {hottest_temp}")

if __name__ == "__main__":
    reducer()