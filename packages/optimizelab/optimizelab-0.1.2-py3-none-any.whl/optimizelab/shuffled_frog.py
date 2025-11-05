"""
Shuffled Frog Leaping Algorithm (SFLA) simplified implementation.
Provides sfla(opt_func, frogs=30, dimension=2, ...)
"""
import numpy as np

# Objective function
def opt_func(value):
    return np.sqrt((value ** 2).sum())


# Generate frogs around mean (mu) with standard deviation (sigma)
def gen_frogs(frogs, dimension, sigma, mu):
    return sigma * (np.random.randn(frogs, dimension)) + mu


# Sort frogs into memeplexes based on fitness
def sort_frogs(frogs, mplx_no, opt_func):
    # Find fitness of each frog
    fitness = np.array(list(map(opt_func, frogs)))

    # Sort indices by fitness (ascending)
    sorted_fitness = np.argsort(fitness)

    # Empty holder for memeplexes
    memeplexes = np.zeros((mplx_no, int(frogs.shape[0] / mplx_no)))

    # Sort into memeplexes
    for j in range(memeplexes.shape[1]):
        for i in range(mplx_no):
            memeplexes[i, j] = sorted_fitness[i + (mplx_no * j)]

    return memeplexes


# Local search within memeplex
def local_search(frogs, memeplex, opt_func, sigma, mu):
    # Select worst, best, and global-best frogs
    frog_w = frogs[int(memeplex[-1])]
    frog_b = frogs[int(memeplex[0])]
    frog_g = frogs[0]

    # Move worst frog toward best frog
    frog_w_new = frog_w + (np.random.rand() * (frog_b - frog_w))

    # If not improved, move worst toward global-best
    if opt_func(frog_w_new) > opt_func(frog_w):
        frog_w_new = frog_w + (np.random.rand() * (frog_g - frog_w))

    # If still not improved, random new worst frog
    if opt_func(frog_w_new) > opt_func(frog_w):
        frog_w_new = gen_frogs(1, frogs.shape[1], sigma, mu)[0]

    # Replace worst frog
    frogs[int(memeplex[-1])] = frog_w_new
    return frogs


# Shuffle memeplexes
def shuffle_memeplexes(frogs, memeplexes):
    temp = memeplexes.flatten()
    np.random.shuffle(temp)
    temp = temp.reshape((memeplexes.shape[0], memeplexes.shape[1]))
    return temp


# Shuffled Frog Leaping Algorithm (SFLA)
def sfla(opt_func, frogs=30, dimension=2, sigma=1, mu=0, mplx_no=5, mplx_iters=10, solun_iters=50):
    # Generate frogs
    frogs = gen_frogs(frogs, dimension, sigma, mu)

    # Arrange frogs into memeplexes
    memeplexes = sort_frogs(frogs, mplx_no, opt_func)

    # Best frog as global best
    best_solun = frogs[int(memeplexes[0, 0])]

    # Main iteration loop
    for i in range(solun_iters):
        if i % 10 == 0 and i > 1:
            print(f"Iteration {i}: best solution: {best_solun} score: {opt_func(best_solun):.5f}")

        # Shuffle memeplexes
        memeplexes = shuffle_memeplexes(frogs, memeplexes)

        # For each memeplex
        for memeplex in memeplexes:
            # Perform local search within memeplex
            for _ in range(mplx_iters):
                frogs = local_search(frogs, memeplex, opt_func, sigma, mu)

            # Rearrange memeplexes after local improvements
            memeplexes = sort_frogs(frogs, mplx_no, opt_func)

        # Check new global best frog
        new_best_solun = frogs[int(memeplexes[0, 0])]
        if opt_func(new_best_solun) < opt_func(best_solun):
            best_solun = new_best_solun

    return best_solun, frogs, memeplexes.astype(int)


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Shuffled Frog Leaping Algorithm (SFLA)...\n")
    solun, frogs, memeplexes = sfla(opt_func, frogs=100, dimension=2, sigma=1, mu=0,
                                    mplx_no=5, mplx_iters=25, solun_iters=50)
    print("\nShuffled Frog Leaping Algorithm completed.")
    print(f"\nBest solution: {solun}\nScore: {opt_func(solun):.5f}")


# --- IMPORT SAFE MODE ---
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        shuffled_frog_code = f.read()
