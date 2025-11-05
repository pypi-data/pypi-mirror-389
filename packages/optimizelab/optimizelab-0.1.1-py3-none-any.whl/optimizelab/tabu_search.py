"""
Tabu Search for job scheduling (simplified).
Provides TS class which can be used to run a tabu search on an instance Excel (or dict).
"""
import pandas as pd
import random as rd
from itertools import combinations
import math

class TS:
    def __init__(self, Path, seed, tabu_tenure):
        self.Path = Path
        self.seed = seed
        self.tabu_tenure = tabu_tenure
        self.instance_dict = self.input_data()
        self.Initial_solution = self.get_InitialSolution()
        self.tabu_str, self.Best_solution, self.Best_objvalue = self.TSearch()

    def input_data(self):
        return pd.read_excel(
            self.Path,
            names=['Job', 'weight', 'processing_time', 'due_date'],
            index_col=0
        ).to_dict('index')

    def get_tabuestructure(self):
        tabu_dict = {}
        for swap in combinations(self.instance_dict.keys(), 2):
            tabu_dict[swap] = {'tabu_time': 0, 'MoveValue': 0}
        return tabu_dict

    def get_InitialSolution(self):
        n_jobs = len(self.instance_dict)
        initial_solution = list(range(1, n_jobs + 1))
        rd.seed(self.seed)
        rd.shuffle(initial_solution)
        return initial_solution

    def Objfun(self, solution):
        data = self.instance_dict
        t = 0
        objfun_value = 0
        for job in solution:
            C_i = t + data[job]["processing_time"]  # completion time
            d_i = data[job]["due_date"]             # due date
            T_i = max(0, C_i - d_i)                 # tardiness
            W_i = data[job]["weight"]               # job weight
            objfun_value += W_i * T_i
            t = C_i
        return objfun_value

    def SwapMove(self, solution, i, j):
        solution = solution.copy()
        i_index = solution.index(i)
        j_index = solution.index(j)
        solution[i_index], solution[j_index] = solution[j_index], solution[i_index]
        return solution

    def TSearch(self):
        tenure = self.tabu_tenure
        tabu_structure = self.get_tabuestructure()
        best_solution = self.Initial_solution
        best_objvalue = self.Objfun(best_solution)
        current_solution = self.Initial_solution
        current_objvalue = self.Objfun(current_solution)
        iter = 1
        Terminate = 0

        while Terminate < 100:
            if iter <= 10:
                print(f"Iteration {iter}: Best_objvalue: {best_objvalue}")

            # Evaluate neighborhood
            for move in tabu_structure:
                candidate_solution = self.SwapMove(current_solution, move[0], move[1])
                candidate_objvalue = self.Objfun(candidate_solution)
                tabu_structure[move]['MoveValue'] = candidate_objvalue

            while True:
                # Select best move (minimization)
                best_move = min(tabu_structure, key=lambda x: tabu_structure[x]['MoveValue'])
                MoveValue = tabu_structure[best_move]['MoveValue']
                tabu_time = tabu_structure[best_move]['tabu_time']

                # If move is not tabu
                if tabu_time < iter:
                    current_solution = self.SwapMove(current_solution, best_move[0], best_move[1])
                    current_objvalue = self.Objfun(current_solution)

                    # Best improving move
                    if MoveValue < best_objvalue:
                        best_solution = current_solution
                        best_objvalue = current_objvalue
                        Terminate = 0
                    else:
                        Terminate += 1

                    # Update tabu time
                    tabu_structure[best_move]['tabu_time'] = iter + tenure
                    iter += 1
                    break

                else:
                    # Aspiration criteria
                    if MoveValue < best_objvalue:
                        current_solution = self.SwapMove(current_solution, best_move[0], best_move[1])
                        current_objvalue = self.Objfun(current_solution)
                        best_solution = current_solution
                        best_objvalue = current_objvalue
                        Terminate = 0
                        iter += 1
                        break
                    else:
                        tabu_structure[best_move]["MoveValue"] = float('inf')
                        continue

        print("\nTabu search completed")
        print("\nPerformed iterations: {}".format(iter),
              "Best found Solution: {} , Objvalue: {}".format(best_solution, best_objvalue),
              sep="\n")

        return tabu_structure, best_solution, best_objvalue


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting Tabu Search...\n")
    test = TS(Path="Instance_10.xlsx", seed=2012, tabu_tenure=3)
    print("\nTabu Search Completed.")
    print("Best Solution:", test.Best_solution)
    print("Best Objective Value:", test.Best_objvalue)


# --- IMPORT SAFE MODE ---
if __name__ != "__main__":
    with open(__file__, "r", encoding="utf-8") as f:
        tabu_search_code = f.read()
