"""
Genetic Algorithm for binary optimization (onemax example).
Provides genetic_algorithm_binary.
"""
from numpy.random import randint, rand

# Objective function (maximize number of ones)
def onemax(x):
    # Negative because we minimize in this GA
    return -sum(x)

# Tournament selection
def selection(pop, scores, k=3):
    # First random selection
    selection_ix = randint(len(pop))
    for ix in randint(0, len(pop), k - 1):
        # Check if better (perform a tournament)
        if scores[ix] < scores[selection_ix]:
            selection_ix = ix
    return pop[selection_ix]

# Crossover two parents to create two children
def crossover(p1, p2, r_cross):
    c1, c2 = p1.copy(), p2.copy()
    # Check for recombination
    if rand() < r_cross:
        # Select crossover point (not on the end)
        pt = randint(1, len(p1) - 2)
        # Perform crossover
        c1 = p1[:pt] + p2[pt:]
        c2 = p2[:pt] + p1[pt:]
    return [c1, c2]

# Mutation operator
def mutation(bitstring, r_mut):
    for i in range(len(bitstring)):
        # Check for a mutation
        if rand() < r_mut:
            # Flip the bit
            bitstring[i] = 1 - bitstring[i]

# Genetic algorithm
def genetic_algorithm_binary(objective, n_bits, n_iter, n_pop, r_cross, r_mut):
    # Initial population of random bitstrings
    pop = [randint(0, 2, n_bits).tolist() for _ in range(n_pop)]
    # Keep track of best solution
    best, best_eval = pop[0], objective(pop[0])
    # Enumerate generations
    for gen in range(n_iter):
        # Evaluate all candidates
        scores = [objective(c) for c in pop]
        # Check for new best solution
        for i in range(n_pop):
            if scores[i] < best_eval:
                best, best_eval = pop[i], scores[i]
                print(f"> iteration {gen}, new best f({pop[i]}) = {scores[i]:.3f}")
        # Select parents
        selected = [selection(pop, scores) for _ in range(n_pop)]
        # Create the next generation
        children = []
        for i in range(0, n_pop, 2):
            p1, p2 = selected[i], selected[(i + 1) % n_pop]
            for c in crossover(p1, p2, r_cross):
                mutation(c, r_mut)
                children.append(c)
        # Replace population
        pop = children
    return best, best_eval


if __name__ == "__main__":
    n_iter = 100
    n_bits = 20
    n_pop = 100
    r_cross = 0.9
    r_mut = 1.0 / n_bits

    print("Starting genetic algorithm (Onemax)...\n")
    best, score = genetic_algorithm_binary(onemax, n_bits, n_iter, n_pop, r_cross, r_mut)
    print("\nGenetic algorithm completed.")
    print(f"Best solution: {best}")
    print(f"Fitness score: {score:.5f}")

# Expose code as string when imported
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        binary_ga_code = f.read()