"""
TSP helpers: graph generation, nearest neighbour init, crossover, mutations (simplified).
"""
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from itertools import combinations
from collections import defaultdict

def generate_random_weighted_graph(n, low, high, seed=None):
    if seed is not None:
        np.random.seed(seed)
    g = nx.generators.complete_graph(n)
    g.add_weighted_edges_from([(a, b, int(np.random.randint(low, high))) for a, b in g.edges()])
    nx.set_node_attributes(g, nx.spring_layout(g), "pos")
    return g

def plot_graph(g, title="", highlight_edges=[]):
    pos = nx.get_node_attributes(g, "pos")
    plt.figure(figsize=(9, 9))
    plt.title(title)
    nx.draw(g, pos=pos, labels={x: x for x in g.nodes()}, width=2)
    weights = nx.get_edge_attributes(g, "weight")
    # draw labels for edges
    nx.draw_networkx_edge_labels(g, pos, edge_labels=weights, label_pos=0.4)
    # highlight highlighted_edges
    if highlight_edges:
        nx.draw_networkx_edges(g, pos, edgelist=highlight_edges, edge_color="r", width=3)
        # highlight labels of highlighted edges
        highlight_keys = {tuple(sorted(e)) for e in highlight_edges}
        nx.draw_networkx_edge_labels(
            g, pos,
            edge_labels={e: w for e, w in weights.items() if tuple(sorted(e)) in highlight_keys},
            font_color="r",
            label_pos=0.4
        )
    plt.show()

# Nearest neighbour initialization
def nearest_neighbour_initialization(g, closed_tour=False):
    curr_node = np.random.choice(list(g.nodes()))
    path = [curr_node]
    not_visited = set(g.nodes()) - {curr_node}
    while not_visited:
        not_visited_neighbours = not_visited & set(g.neighbors(curr_node))
        key = lambda x: g[curr_node][x]["weight"]
        curr_node = min(not_visited_neighbours, key=key)
        path.append(curr_node)
        not_visited.remove(curr_node)
    if closed_tour:
        path.append(path[0])
    return path

# Helpers for shortest-edge initialization
def has_cycle(g):
    try:
        nx.find_cycle(g)
        return True
    except nx.NetworkXNoCycle:
        return False

def get_path_from_edges(edges, closed_tour=False):
    path_graph = nx.Graph(list(edges))
    # start from a node with degree 1 if open tour, otherwise any node
    degrees = dict(path_graph.degree())
    curr = min(degrees, key=lambda x: degrees[x])
    path = [curr]
    visited = {curr}
    while len(path) < len(path_graph):
        neigh = set(path_graph.neighbors(curr)) - visited
        if not neigh:
            break
        curr = neigh.pop()
        visited.add(curr)
        path.append(curr)
    if closed_tour and path[0] not in path[-1:]:
        path.append(path[0])
    return path

def shortest_edge_initialization(g, closed_tour=False):
    edge_list = set(g.edges())
    times_visited = defaultdict(int)
    tour = set()
    max_tour_len = len(g) if closed_tour else len(g) - 1
    key = nx.get_edge_attributes(g, "weight").get
    while len(tour) < max_tour_len and edge_list:
        u, v = min(edge_list, key=key)
        times_visited[u] += 1
        times_visited[v] += 1
        tour.add((u, v))
        edge_list.remove((u, v))
        # remove edges that would create invalid tours
        for (a, b) in list(edge_list):
            if ((has_cycle(nx.Graph(list(tour) + [(a, b)])) and len(tour) != len(g) - 1)
                    or times_visited[a] == 2 or times_visited[b] == 2):
                edge_list.discard((a, b))
    return get_path_from_edges(tour, closed_tour=closed_tour)

# Simple path length and inverse path length for selection
def path_length(path, g):
    if not path:
        return float("inf")
    edge_weights = nx.get_edge_attributes(g, "weight")
    total = 0
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        total += edge_weights.get(tuple(sorted((a, b))), 0)
    return total

def inv_path_length(path, g):
    L = path_length(path, g)
    return 1.0 / (L + 1e-9)

# Roulette wheel selection (returns selected population)
def roulette_wheel_selection(fitness_func, population, g, k=None):
    if k is None:
        k = len(population)
    scores = np.array([fitness_func(p, g) for p in population], dtype=float)
    # convert to positive weights (higher fitness -> higher weight)
    weights = scores - scores.min() + 1e-9
    probs = weights / weights.sum()
    idx = np.random.choice(len(population), size=k, replace=True, p=probs)
    return [population[i] for i in idx]

# Make valid tour helper (fix duplicates)
def make_valid_tour(p, nodes):
    p = list(p)
    unvisited = list(set(nodes) - set(p))
    indices = defaultdict(list)
    for i in range(len(p)):
        indices[p[i]].append(i)
    visited_twice = [node for node, locs in indices.items() if len(locs) == 2]
    for node in visited_twice:
        change_index = np.random.choice(indices[node])
        if unvisited:
            p[change_index] = unvisited.pop()
    return p

# Partially matched crossover (PMX)
def partially_matched_crossover(p1, p2):
    pt = np.random.randint(1, len(p1) - 1)
    c1 = p1[:pt] + p2[pt:]
    c2 = p2[:pt] + p1[pt:]
    nodes = set(p1)
    return make_valid_tour(c1, nodes), make_valid_tour(c2, nodes)

# Order crossover (OX)
def order_crossover(p1, p2):
    start = np.random.randint(0, len(p1) - 1)
    end = np.random.randint(start + 1, len(p1)) if start != 0 else np.random.randint(start + 1, len(p1))
    def fill_blanks(a, b, s, e):
        unvisited = [x for x in b if x not in a[s:e]]
        c = a.copy()
        for i in range(len(a)):
            if i < s or i >= e:
                c[i] = unvisited.pop(0)
        return c
    c1 = fill_blanks(p1, p2, start, end)
    c2 = fill_blanks(p2, p1, start, end)
    return c1, c2

# Mutation by inversion
def inversion_mutation(p):
    start = np.random.randint(0, len(p) - 1)
    end = np.random.randint(start + 1, len(p) + 1)
    c = p.copy()
    c[start:end] = list(reversed(c[start:end]))
    return c

# Mutation by insertion
def insertion_mutation(p):
    i = np.random.randint(0, len(p))
    k = np.random.randint(0, len(p))
    c = p.copy()
    c.insert(k, c.pop(i))
    return c

# --- Example usage / demo ---
if __name__ == "__main__":
    np.random.seed(3)
    g = generate_random_weighted_graph(7, 1, 20, seed=3)
    plot_graph(g, "Graph for TSP")

    np.random.seed(1)
    print("Nearest neighbour (open):", nearest_neighbour_initialization(g))
    print("Nearest neighbour (closed):", nearest_neighbour_initialization(g, closed_tour=True))

    np.random.seed(1)
    print("Shortest edge init (open):", shortest_edge_initialization(g))
    print("Shortest edge init (closed):", shortest_edge_initialization(g, closed_tour=True))

    # population and selection demo
    np.random.seed(2)
    n_population = 8
    population = [shortest_edge_initialization(g, closed_tour=False) for _ in range(n_population)]
    selected_population = roulette_wheel_selection(lambda p, G: inv_path_length(p, G), population, g)
    parents = selected_population[:2]
    print("Parents:", parents)
    print("PMX:", partially_matched_crossover(*parents))
    print("OX:", order_crossover(*parents))

    # Mutation demos
    np.random.seed(3)
    subject = population[0]
    print("Inversion mutation:", subject, inversion_mutation(subject))
    np.random.seed(2)
    subject = population[0]
    print("Insertion mutation:", subject, insertion_mutation(subject))

# Expose code as string when imported
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        tsp_genetic_code = f.read()
