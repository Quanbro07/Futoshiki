import time
import tracemalloc
from fol.KnowledgeBase import KnowledgeBase
from fol.Literal import Literal
from fol.Predicate import Val, Less
from helperFunction.ParseInput import parse_input
from helperFunction.GenerateKB import generate_KB
from helperFunction.GenerateRowColUsed import get_row_col_used
from algorithm.PerformanceMetrics import PerformanceMetrics

class BackwardChainingSolver(PerformanceMetrics):
    def __init__(self, kb: KnowledgeBase, N: int, given: dict, 
                 less_h: set, greater_h: set, less_v: set, greater_v: set):
        super().__init__()
        
        self.kb = kb
        self.N = N
        self.assignment = given.copy()
        
        for (r, c), v in given.items():
            self.kb.add_fact(Literal(Val(r, c, v)))
            
        self.row_used, self.col_used = get_row_col_used(N, given)
        self.expanded_nodes = 0

    def find_empty_cell(self):
        for i in range(1, self.N + 1):
            for j in range(1, self.N + 1):
                if (i, j) not in self.assignment:
                    return (i, j)
        return None

    def is_consistent_with_kb(self, i, j, v) -> bool:
        if v in self.row_used[i] or v in self.col_used[j]:
            return False

        temp_fact = Literal(Val(i, j, v))
        self.kb.facts.add(temp_fact)

        for clause in self.kb.definite_clauses:
            if clause.is_conditions_satified(self.kb.facts):
                conc = clause.conclusion.predicate
                if isinstance(conc, Less):
                    v1, v2 = conc.args
                    if not (v1 < v2):
                        self.kb.facts.remove(temp_fact)
                        return False

        self.kb.facts.remove(temp_fact)
        return True

    def _solve_recursive(self) -> bool:
        self.expanded_nodes += 1
        empty_cell = self.find_empty_cell()
        if not empty_cell:
            return True

        r, c = empty_cell
        for v in range(1, self.N + 1):
            if self.is_consistent_with_kb(r, c, v):
                self.assignment[(r, c)] = v
                self.row_used[r].add(v)
                self.col_used[c].add(v)
                fact = Literal(Val(r, c, v))
                self.kb.add_fact(fact)

                if self._solve_recursive():
                    return True
                
                self.kb.facts.remove(fact)
                self.row_used[r].remove(v)
                self.col_used[c].remove(v)
                del self.assignment[(r, c)]
        return False

    def solve(self) -> bool:
        tracemalloc.start()

        start_time = time.perf_counter()
        success = self._solve_recursive()
        self.time = time.perf_counter() - start_time
        _, peak_mem = tracemalloc.get_traced_memory()
        self.memory = peak_mem / 1024 
        
        tracemalloc.stop()
        
        return success


def main():
    input_file = "Inputs/test.txt" 
    N, given, less_h, greater_h, less_v, greater_v = parse_input(input_file)
    
    print(f"Initializing {N}x{N} Grid - Given cells: {len(given)}")
    
    kb = generate_KB(input_file)
    
    solver = BackwardChainingSolver(kb, N, given, less_h, greater_h, less_v, greater_v)

    success = solver.solve()

    print("\n" + "="*40)
    if success:
        print("SOLUTION FOUND!")
        grid_result = [[0 for _ in range(N)] for _ in range(N)]
        for (r, c), v in solver.assignment.items():
            grid_result[r-1][c-1] = v
        
        for row in grid_result:
            print(" ".join(str(val) for val in row))
    else:
        print("NO SOLUTION EXISTS.")
    print("="*40)
    print(f"Execution Time: {solver.time:.4f} seconds")
    print(f"Peak Memory:    {solver.memory:.2f} KB")
    print(f"Expanded Nodes: {solver.expanded_nodes}")

if __name__ == "__main__":
    main()