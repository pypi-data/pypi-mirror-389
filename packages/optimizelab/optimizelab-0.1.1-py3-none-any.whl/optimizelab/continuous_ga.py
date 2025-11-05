"""
Genetic Algorithm for continuous optimization (simple bitstring GA -> real variables).
Provides `genetic_algorithm_continuous` and `decode` helpers.
"""
from numpy.random import randint, rand

# Objective function
def objective(x):
    return x[0]**2.0 + x[1]**2.0

# Decode bitstring to numbers
def decode(bounds, n_bits, bitstring):
    decoded = []
    largest = 2**n_bits
    for i in range(len(bounds)):
        # Extract the substring
        start, end = i * n_bits, (i * n_bits) + n_bits
        substring = bitstring[start:end]
        # Convert bitstring to string of chars
        chars = ''.join([str(s) for s in substring])
        # Convert string to integer
        integer = int(chars, 2)
        # Scale integer to desired range
        value = bounds[i][0] + (integer / largest) * (bounds[i][1] - bounds[i][0])
        decoded.append(value)
    return decoded

# Tournament selection
def selection(pop, scores, k=3):
    selection_ix = randint(len(pop))
    for ix in randint(0, len(pop), k - 1):
        if scores[ix] < scores[selection_ix]:
            selection_ix = ix
    return pop[selection_ix]

# Crossover two parents to create two children
def crossover(p1, p2, r_cross):
    c1, c2 = p1.copy(), p2.copy()
    if rand() < r_cross:
        # Select crossover point that is not on the end of the string
        pt = randint(1, len(p1) - 2)
        # Perform crossover
        c1 = p1[:pt] + p2[pt:]
        c2 = p2[:pt] + p1[pt:]
    return [c1, c2]

# Mutation operator
def mutation(bitstring, r_mut):
    for i in range(len(bitstring)):
        if rand() < r_mut:
            # Flip the bit
            bitstring[i] = 1 - bitstring[i]

# Genetic algorithm
def genetic_algorithm_continuous(objective, bounds, n_bits, n_iter, n_pop, r_cross, r_mut):
    # Initial population of random bitstrings
    pop = [randint(0, 2, n_bits * len(bounds)).tolist() for _ in range(n_pop)]
    # Keep track of best solution
    best, best_eval = pop[0], objective(decode(bounds, n_bits, pop[0]))
    # Enumerate generations
    for gen in range(n_iter):
        # Decode population
        decoded = [decode(bounds, n_bits, p) for p in pop]
        # Evaluate all candidates in the population
        scores = [objective(d) for d in decoded]
        # Check for new best solution
        for i in range(n_pop):
            if scores[i] < best_eval:
                best, best_eval = pop[i], scores[i]
                print(f"> iteration {gen}, new best f({decoded[i]}) = {scores[i]:.5f}")
        # Select parents
        selected = [selection(pop, scores) for _ in range(n_pop)]
        # Create the next generation
        children = []
        for i in range(0, n_pop, 2):
            p1, p2 = selected[i], selected[(i + 1) % n_pop]
            for c in crossover(p1, p2, r_cross):
                mutation(c, r_mut)
                children.append(c)
        pop = children
    return best, best_eval

if __name__ == "__main__":
    bounds = [[-5.0, 5.0], [-5.0, 5.0]]
    n_iter = 100
    n_bits = 16
    n_pop = 100
    r_cross = 0.9
    r_mut = 1.0 / (n_bits * len(bounds))

    print("Starting continuous GA...\n")
    best, score = genetic_algorithm_continuous(objective, bounds, n_bits, n_iter, n_pop, r_cross, r_mut)
    decoded = decode(bounds, n_bits, best)
    print("\nContinuous GA completed.")
    print(f"Best solution: {decoded}")
    print(f"Fitness score: {score:.5f}")

# Expose code as string when imported
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        continuous_ga_code = f.read()