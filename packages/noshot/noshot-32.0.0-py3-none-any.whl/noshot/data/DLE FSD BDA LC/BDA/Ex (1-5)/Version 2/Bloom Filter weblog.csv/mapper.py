#!/usr/bin/env python
import sys
import re

# Bloom filter size - adjust based on expected unique IPs
M = 1000000  # 1 million bits

def is_valid_ip(ip):
    """Check if the string is a valid IP address"""
    ip_pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    return re.match(ip_pattern, ip) is not None

def ip_to_number(ip):
    """Convert IP address to a numerical value for hashing"""
    parts = ip.split('.')
    if len(parts) != 4:
        return 0
    try:
        return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
    except:
        return 0

def main():
    # Initialize Bloom filter
    bloom_filter = [0] * M
    
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
            
        try:
            # Extract IP address (first column)
            parts = line.split(',')
            if len(parts) < 1:
                continue
                
            ip_address = parts[0].strip()
            
            # Validate IP address format
            if not is_valid_ip(ip_address):
                sys.stderr.write("Invalid IP format: {0}\n".format(ip_address))
                continue
            
            # Convert IP to numerical value for hashing
            ip_num = ip_to_number(ip_address)
            if ip_num == 0:
                continue
            
            # Apply your Bloom filter hash functions
            h1 = ip_num % M
            h2 = (3 * ip_num + 2) % M
            
            # Check if IP is duplicate
            if bloom_filter[h1] == 0:
                bloom_filter[h1] = 1
                # IP is new, emit it
                print("{0}\t{1}".format(ip_address, line))
            elif bloom_filter[h1] == 1:
                if bloom_filter[h2] == 0:
                    bloom_filter[h2] = 1
                    # IP is new (second hash), emit it
                    print("{0}\t{1}".format(ip_address, line))
                else:
                    # Both hash positions are set - duplicate detected
                    sys.stderr.write("Duplicate detected: {0}\n".format(ip_address))
            else:
                sys.stderr.write("Duplicate detected: {0}\n".format(ip_address))
                
        except Exception as e:
            sys.stderr.write("Error processing line: {0} - {1}\n".format(line, str(e)))
            continue
    
    # Output final Bloom filter state for monitoring
    sys.stderr.write("Final Bloom's filter size: {0}\n".format(M))

if __name__ == "__main__":
    main()