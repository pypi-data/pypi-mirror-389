import sys

skip_header = True

for line in sys.stdin:
    if skip_header:
        skip_header = False
        continue
    try:
        parts = line.strip().split(',')
        user_name = parts[7].strip()  # assuming 8th column is user name
        if not user_name:
            continue
        binary = bin(abs(hash(user_name)))[2:]
        t_zeros = len(binary) - len(binary.rstrip('0'))
        print "%d" % t_zeros
    except:
        continue
