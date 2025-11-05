"""
Particle Swarm Optimization (basic) for continuous functions.
Provides pso(fitness, max_iter, n_particles, dim, minx, maxx)
"""
import random
import copy
import sys

# Sphere function
def fitness_sphere(position):
    fitnessVal = 0.0
    for i in range(len(position)):
        Xi = position[i]
        fitnessVal += (Xi * Xi)
    return fitnessVal


# Particle class
class Particle:
    def __init__(self, fitness, dim, minx, maxx, seed):
        self.rnd = random.Random(seed)
        # initialize position and velocity
        self.position = [0.0 for _ in range(dim)]
        self.velocity = [0.0 for _ in range(dim)]
        # initialize best known position
        self.best_part_pos = [0.0 for _ in range(dim)]
        # random initialization
        for i in range(dim):
            self.position[i] = ((maxx - minx) * self.rnd.random() + minx)
            self.velocity[i] = ((maxx - minx) * self.rnd.random() + minx)
        # compute initial fitness
        self.fitness = fitness(self.position)
        # initialize best known fitness
        self.best_part_pos = copy.copy(self.position)
        self.best_part_fitnessVal = self.fitness


# Particle Swarm Optimization
def pso(fitness, max_iter, n, dim, minx, maxx):
    # Hyperparameters
    w = 0.729       # inertia
    c1 = 1.49445    # cognitive (particle)
    c2 = 1.49445    # social (swarm)

    rnd = random.Random(0)

    # Create n random particles
    swarm = [Particle(fitness, dim, minx, maxx, i) for i in range(n)]

    # Initialize global best
    best_swarm_pos = [0.0 for _ in range(dim)]
    best_swarm_fitnessVal = sys.float_info.max

    # Find initial best
    for i in range(n):
        if swarm[i].fitness < best_swarm_fitnessVal:
            best_swarm_fitnessVal = swarm[i].fitness
            best_swarm_pos = copy.copy(swarm[i].position)

    # Main PSO loop
    Iter = 0
    while Iter < max_iter:
        if Iter % 10 == 0 and Iter > 1:
            print("Iter = " + str(Iter) +
                  " best fitness = %.3f" % best_swarm_fitnessVal +
                  " Best position: " + str(["%.6f" % best_swarm_pos[k] for k in range(dim)]))

        for i in range(n):
            for k in range(dim):
                r1 = rnd.random()
                r2 = rnd.random()
                swarm[i].velocity[k] = (
                    w * swarm[i].velocity[k] +
                    (c1 * r1 * (swarm[i].best_part_pos[k] - swarm[i].position[k])) +
                    (c2 * r2 * (best_swarm_pos[k] - swarm[i].position[k]))
                )
                # clip velocity
                if swarm[i].velocity[k] < minx:
                    swarm[i].velocity[k] = minx
                elif swarm[i].velocity[k] > maxx:
                    swarm[i].velocity[k] = maxx

            # Update position
            for k in range(dim):
                swarm[i].position[k] += swarm[i].velocity[k]

            # Compute new fitness
            swarm[i].fitness = fitness(swarm[i].position)

            # Update personal best
            if swarm[i].fitness < swarm[i].best_part_fitnessVal:
                swarm[i].best_part_fitnessVal = swarm[i].fitness
                swarm[i].best_part_pos = copy.copy(swarm[i].position)

            # Update global best
            if swarm[i].fitness < best_swarm_fitnessVal:
                best_swarm_fitnessVal = swarm[i].fitness
                best_swarm_pos = copy.copy(swarm[i].position)

        Iter += 1

    return best_swarm_pos


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    dim = 3
    fitness = fitness_sphere
    num_particles = 50
    max_iter = 100

    print("\nStarting PSO algorithm\n")
    best_position = pso(fitness, max_iter, num_particles, dim, -10.0, 10.0)
    print("\nPSO completed\n")
    print("\nBest solution found:")
    print(["%.6f" % best_position[k] for k in range(dim)])
    fitnessVal = fitness(best_position)
    print("Fitness of best solution = %.6f" % fitnessVal)


# --- IMPORT SAFE MODE ---
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        particle_swarm_code = f.read()
