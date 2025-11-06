#!/usr/bin/env python
import sys

def main():
    unique_count = 0
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            # Split by tab to get IP and full record
            parts = line.split('\t', 1)
            if len(parts) == 2:
                ip, full_record = parts
                # Output the unique record
                print(full_record)
                unique_count += 1
            else:
                # Handle cases where tab separator might be missing
                print(line)
                unique_count += 1
                
        except Exception as e:
            sys.stderr.write("Error processing line: {0} - {1}\n".format(line, str(e)))
            continue
    
    # Output statistics
    sys.stderr.write("Total unique IP records: {0}\n".format(unique_count))

if __name__ == "__main__":
    main()