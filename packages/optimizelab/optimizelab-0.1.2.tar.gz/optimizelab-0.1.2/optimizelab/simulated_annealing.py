"""
Simulated Annealing implementation.
Provides simulated_annealing(objective, bounds, n_iterations, step_size, temp)
"""
from numpy import asarray, exp
from numpy.random import randn, rand, seed

# Objective function
def objective(x):
    return x[0]**2.0

# Simulated annealing algorithm
def simulated_annealing(objective, bounds, n_iterations, step_size, temp):
    # Generate an initial point
    best = bounds[:, 0] + rand(len(bounds)) * (bounds[:, 1] - bounds[:, 0])
    # Evaluate the initial point
    best_eval = objective(best)
    # Current working solution
    curr, curr_eval = best, best_eval
    # Run the algorithm
    for i in range(n_iterations):
        # Take a step
        candidate = curr + randn(len(bounds)) * step_size
        # Evaluate candidate point
        candidate_eval = objective(candidate)
        # Check for new best solution
        if candidate_eval < best_eval:
            best, best_eval = candidate, candidate_eval
            print(f"> iteration {i}: f({best}) = {best_eval:.5f}")
        # Difference between candidate and current
        diff = candidate_eval - curr_eval
        # Calculate temperature for current epoch
        t = temp / float(i + 1)
        # Calculate Metropolis acceptance criterion
        metropolis = exp(-diff / t)
        # Check if we should keep the new point
        if diff < 0 or rand() < metropolis:
            curr, curr_eval = candidate, candidate_eval
    return best, best_eval


# --- Run the algorithm ---

if __name__ == "__main__":
    # Seed the pseudorandom number generator
    seed(1)
    # Define range for input
    bounds = asarray([[-5.0, 5.0]])
    # Define the total iterations
    n_iterations = 1000
    # Define the maximum step size
    step_size = 0.1
    # Initial temperature
    temp = 10

    print("Starting simulated annealing algorithm...\n")
    best, score = simulated_annealing(objective, bounds, n_iterations, step_size, temp)
    print("\nSimulated annealing completed.")
    print(f"Best solution: {best}")
    print(f"Fitness score of the best solution: {score:.5f}")

# Expose code as string when imported
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        simulated_annealing_code = f.read()
