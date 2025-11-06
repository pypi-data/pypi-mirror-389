import subprocess

input_file = "input.txt"
mapper_file = "mapper.py"
reducer_file = "reducer.py"

max_iter = 4
tol = 1e-6

def read_ranks_from_string(data):
    ranks = {}
    outlinks_map = {}
    for line in data.strip().split('\n'):
        parts = line.strip().split('\t')
        if len(parts) == 3:
            page, outlinks, rank = parts
            ranks[page] = float(rank)
            outlinks_map[page] = outlinks
    return ranks, outlinks_map

def format_output(ranks, outlinks_map):
    lines = ["Node\tOutlinks\tRank"]
    for page in sorted(ranks.keys()):
        lines.append("%-7s %-15s %.6f" % (page, outlinks_map[page], ranks[page]))
    return "\n".join(lines)

def has_converged(old_ranks, new_ranks, tol):
    for k in old_ranks:
        if abs(old_ranks[k] - new_ranks[k]) > tol:
            return False
    return True

with open(input_file) as f:
    current_data = f.read()

print "="*32
print "PageRank Simulation Starting"
print "="*32

old_ranks = {}

for i in range(1, max_iter+1):
    # Run mapper
    mapper = subprocess.Popen(
        ["python", mapper_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    mapper_output, _ = mapper.communicate(current_data)

    # Sort mapper output
    sort_proc = subprocess.Popen(
        ["sort"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    sorted_output, _ = sort_proc.communicate(mapper_output)

    # Run reducer
    reducer = subprocess.Popen(
        ["python", reducer_file],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True
    )
    reduced_output, _ = reducer.communicate(sorted_output)

    # Convert output to ranks
    new_ranks, outlinks_map = read_ranks_from_string(reduced_output)

    # Print iteration result
    print "Iteration %d completed" % i
    print format_output(new_ranks, outlinks_map)
    print "-"*32

    # Check convergence
    if i > 1 and has_converged(old_ranks, new_ranks, tol):
        print "Convergence reached at iteration %d" % i
        break

    old_ranks = new_ranks
    current_data = reduced_output

print "\n\n\n"
print "="*32
print "Final PageRank Values"
print format_output(new_ranks, outlinks_map)
print "="*32
