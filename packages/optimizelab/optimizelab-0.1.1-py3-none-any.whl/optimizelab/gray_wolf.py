"""
Gray Wolf Optimization (GWO) simplified implementation.
Provides gwo(fitness, max_iter, n, dim, minx, maxx)
"""
import random
import copy

# Sphere function
def fitness_sphere(position):
    fitness_value = 0.0
    for i in range(len(position)):
        Xi = position[i]
        fitness_value += (Xi * Xi)
    return fitness_value


# Wolf class
class Wolf:
    def __init__(self, fitness, dim, minx, maxx, seed):
        self.rnd = random.Random(seed)
        self.position = [0.0 for _ in range(dim)]
        for i in range(dim):
            self.position[i] = ((maxx - minx) * self.rnd.random() + minx)
        self.fitness = fitness(self.position)  # current fitness


# Gray Wolf Optimization (GWO)
def gwo(fitness, max_iter, n, dim, minx, maxx):
    rnd = random.Random(0)

    # Create n random wolves
    population = [Wolf(fitness, dim, minx, maxx, i) for i in range(n)]

    # Sort population based on fitness (ascending)
    population = sorted(population, key=lambda temp: temp.fitness)

    # Best three wolves: alpha, beta, gamma
    alpha_wolf, beta_wolf, gamma_wolf = copy.copy(population[:3])

    # Main loop
    Iter = 0
    while Iter < max_iter:
        # Print status every 10 iterations
        if Iter % 10 == 0 and Iter > 1:
            print("Iter =", Iter, "best fitness = %.3f" % alpha_wolf.fitness,
                  "Best position =", ["%.6f" % alpha_wolf.position[k] for k in range(dim)])

        # Linearly decreased from 2 to 0
        a = 2 * (1 - Iter / max_iter)

        # Update each population member
        for i in range(n):
            A1 = a * (2 * rnd.random() - 1)
            A2 = a * (2 * rnd.random() - 1)
            A3 = a * (2 * rnd.random() - 1)
            C1 = 2 * rnd.random()
            C2 = 2 * rnd.random()
            C3 = 2 * rnd.random()

            X1 = [0.0 for _ in range(dim)]
            X2 = [0.0 for _ in range(dim)]
            X3 = [0.0 for _ in range(dim)]
            Xnew = [0.0 for _ in range(dim)]

            for j in range(dim):
                X1[j] = alpha_wolf.position[j] - A1 * abs(C1 * alpha_wolf.position[j] - population[i].position[j])
                X2[j] = beta_wolf.position[j] - A2 * abs(C2 * beta_wolf.position[j] - population[i].position[j])
                X3[j] = gamma_wolf.position[j] - A3 * abs(C3 * gamma_wolf.position[j] - population[i].position[j])
                Xnew[j] = (X1[j] + X2[j] + X3[j]) / 3.0

            # Fitness calculation of new solution
            fnew = fitness(Xnew)

            # Greedy selection
            if fnew < population[i].fitness:
                population[i].position = Xnew
                population[i].fitness = fnew

        # Sort wolves again and update alpha, beta, gamma
        population = sorted(population, key=lambda temp: temp.fitness)
        alpha_wolf, beta_wolf, gamma_wolf = copy.copy(population[:3])

        Iter += 1

    # Return best solution (alpha wolf)
    return alpha_wolf.position


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    dim = 3
    fitness = fitness_sphere
    num_particles = 10
    max_iter = 50

    print("Starting Gray Wolf Optimization algorithm...\n")
    best_position = gwo(fitness, max_iter, num_particles, dim, -10.0, 10.0)
    print("\nGray Wolf Optimization completed.\n")

    print("Best solution found:")
    print(["%.6f" % best_position[k] for k in range(dim)])
    err = fitness(best_position)
    print("Fitness of best solution = %.6f" % err)


# --- IMPORT SAFE MODE ---
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        gray_wolf_code = f.read()
