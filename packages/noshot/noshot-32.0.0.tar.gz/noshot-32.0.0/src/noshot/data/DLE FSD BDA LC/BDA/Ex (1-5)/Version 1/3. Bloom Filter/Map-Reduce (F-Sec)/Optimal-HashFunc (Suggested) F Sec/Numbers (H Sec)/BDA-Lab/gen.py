import random

random.seed(42)

with open("input.txt", "w") as f:
    for _ in range(20):
        f.write(str(random.randint(1, 300)) + "\n")
