from state.Board import Board
from state.PuzzleContext import PuzzleContext

from algorithm.PerformanceMetrics import PerformanceMetrics
from helperFunction.ParseInput import parse_input

import time
import tracemalloc

class Backtracking(PerformanceMetrics):
    expanded_nodes: int

    def __init__(self):
        super().__init__()
        self.expanded_nodes = 0


    def solve(self,board: Board) -> bool:
        self.time = 0.0
        self.memory = 0.0
        self.expanded_nodes = 0

        tracemalloc.start()
        start_time = time.time()
        
        # Tạo 1 lần duy nhất
        empty_cells = board.get_empty_cells()

        result = self.run_backtracking(board, empty_cells, 0)

        self.time = time.time() - start_time
        
        _, peak = tracemalloc.get_traced_memory()
        self.memory = peak / 1024  # KB
        
        tracemalloc.stop()

        return result

    def run_backtracking(self,board: Board, empty_cells: list, idx:int):
        if idx == len(empty_cells):
            return True
        
        i,j = empty_cells[idx]
        self.expanded_nodes += 1

        for v in board.get_valid_values(i, j):
            board.assign_value(i, j, v)

            if self.run_backtracking(board, empty_cells, idx + 1):
                return True
        
            board.unassign_value(i, j)
        
        return False

def main():
    input = r"Inputs\test.txt"
    
    N, given, less_h, greater_h, less_v, greater_v = parse_input(input)
    print(given)
    
    context = PuzzleContext(N, given, less_h, greater_h, less_v, greater_v)
    board = Board(given, context)

    bt = Backtracking()
    if bt.solve(board):
        print(board.to_grid())


    print(f"Time:     {bt.time:.4f}s")
    print(f"Memory:   {bt.memory:.2f}KB")
    print(f"Expanded: {bt.expanded_nodes} nodes")

if __name__ == "__main__":
    main()