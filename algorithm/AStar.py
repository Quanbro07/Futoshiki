from state.Board import Board
from state.PuzzleContext import PuzzleContext

from helperFunction.WriteOutput import parse_output
from helperFunction.ParseInput import parse_input

import math
import heapq
import time
import tracemalloc


class AStar:
    expanded_nodes: int

    def __init__(self):
        super().__init__()
        self.expanded_nodes = 0

    # h1 = số ô trống
    def compute_h1(self, N, assignment: dict[tuple[int,int]: set[int]]) -> int:
        return N * N - len(assignment)
    
    # h2 = các ô chưa điền + thuộc inequality chain
    def compute_h2(self, assignment: dict[tuple[int,int]: set[int]],
                   ctx: PuzzleContext) -> int:
        unresolved = set()

        for (i, j) in ctx.less_h | ctx.greater_h:
            if (i, j) not in assignment:
                unresolved.add((i, j))
            if (i, j+1) not in assignment:
                unresolved.add((i, j+1))

        for (i, j) in ctx.less_v | ctx.greater_v:
            if (i, j) not in assignment:
                unresolved.add((i, j))
            if (i+1, j) not in assignment:
                unresolved.add((i+1, j))
        
        return len(unresolved)
    def is_consistent(self, xi, xj, vx, yi, yj, vy, 
                    context: PuzzleContext) -> bool:

        # LessH
        if (xi,xj) in context.less_h and (yi,yj) == (xi,xj+1):
            return vx < vy
        if (yi,yj) in context.less_h and (xi,xj) == (yi,yj+1):
            return vy < vx
        
        # GreaterH
        if (xi,xj) in context.greater_h and (yi,yj) == (xi,xj+1):
            return vx > vy
        if (yi,yj) in context.greater_h and (xi,xj) == (yi,yj+1):
            return vy > vx
        
        # LessV
        if (xi,xj) in context.less_v and (yi,yj) == (xi+1,xj):
            return vx < vy
        if (yi,yj) in context.less_v and (xi,xj) == (yi+1,yj):
            return vy < vx
        
        # GreaterV
        if (xi,xj) in context.greater_v and (yi,yj) == (xi+1,xj):
            return vx > vy
        if (yi,yj) in context.greater_v and (xi,xj) == (yi+1,yj):
            return vy > vx
        
        # Row/col uniqueness
        if xi == yi:  return vx != vy
        if xj == yj:  return vx != vy
        
        return True
    
    def revise(self, domain: dict, xi, xj, yi, yj, context: PuzzleContext, assignment: dict) -> set:
        to_remove = set()
        
        # Nếu biến (xi, xj) đã được gán (không có trong domain), bỏ qua không revise
        if (xi,xj) not in domain:
            return set()
            
        # Xác định domain của biến (yi, yj)
        if (yi,yj) in domain:
            domain_y = domain[(yi,yj)]
        elif (yi,yj) in assignment:
            # Nếu đã gán, domain của nó chính là giá trị duy nhất đó
            domain_y = {assignment[(yi,yj)]}
        else:
            domain_y = set()

        for vx in list(domain[(xi,xj)]):
            has_support = any(
                self.is_consistent(xi, xj, vx, yi, yj, vy, context)
                for vy in domain_y
            )
            if not has_support:
                to_remove.add(vx)
        
        domain[(xi,xj)].difference_update(to_remove)
    
        return to_remove

    
    # Tổng hợp Heuristic
    def compute_h(self, N: int, assignment: dict, current_domain: dict, context: PuzzleContext) -> float:
        h1 = self.compute_h1(N, assignment)

        return h1
    
    def propagate(self, domain, i, j, v, context) -> dict | None:
        new_domain = {cell: vals.copy() for cell, vals in domain.items()}

        # Xóa ô vừa gán
        if (i,j) in new_domain:
            del new_domain[(i,j)]

        # Loại v khỏi cùng row
        for j2 in range(1, context.N+1):
            if (i,j2) in new_domain:
                new_domain[(i,j2)].discard(v)
                if not new_domain[(i,j2)]:
                    return None

        # Loại v khỏi cùng col
        for i2 in range(1, context.N+1):
            if (i2,j) in new_domain:
                new_domain[(i2,j)].discard(v)
                if not new_domain[(i2,j)]:
                    return None

        # LessH: cell(i,j) < cell(i,j+1)
        if (i,j) in context.less_h and (i,j+1) in new_domain:
            new_domain[(i,j+1)] = {x for x in new_domain[(i,j+1)] if x > v}
            if not new_domain[(i,j+1)]: return None

        if (i,j-1) in context.less_h and (i,j-1) in new_domain:
            new_domain[(i,j-1)] = {x for x in new_domain[(i,j-1)] if x < v}
            if not new_domain[(i,j-1)]: return None

        # GreaterH: cell(i,j) > cell(i,j+1)
        if (i,j) in context.greater_h and (i,j+1) in new_domain:
            new_domain[(i,j+1)] = {x for x in new_domain[(i,j+1)] if x < v}
            if not new_domain[(i,j+1)]: return None

        if (i,j-1) in context.greater_h and (i,j-1) in new_domain:
            new_domain[(i,j-1)] = {x for x in new_domain[(i,j-1)] if x > v}
            if not new_domain[(i,j-1)]: return None

        # LessV: cell(i,j) < cell(i+1,j)
        if (i,j) in context.less_v and (i+1,j) in new_domain:
            new_domain[(i+1,j)] = {x for x in new_domain[(i+1,j)] if x > v}
            if not new_domain[(i+1,j)]: return None

        if (i-1,j) in context.less_v and (i-1,j) in new_domain:
            new_domain[(i-1,j)] = {x for x in new_domain[(i-1,j)] if x < v}
            if not new_domain[(i-1,j)]: return None

        # GreaterV: cell(i,j) > cell(i+1,j)
        if (i,j) in context.greater_v and (i+1,j) in new_domain:
            new_domain[(i+1,j)] = {x for x in new_domain[(i+1,j)] if x < v}
            if not new_domain[(i+1,j)]: return None

        if (i-1,j) in context.greater_v and (i-1,j) in new_domain:
            new_domain[(i-1,j)] = {x for x in new_domain[(i-1,j)] if x > v}
            if not new_domain[(i-1,j)]: return None

        return new_domain
    
    def init_domain(self, board: Board) -> dict:
        domain = {
            (i,j): set(range(1, board.N+1))
            for i in range(1, board.N+1)
            for j in range(1, board.N+1)
            if (i,j) not in board.assignment
        }
        # Propagate given clues
        for (i,j), v in board.assignment.items():
            domain = self.propagate(domain, i, j, v, board.context)
            if domain is None:
                return None
        return domain


    def solve(self, board: Board) -> bool:
        self.time = 0
        self.memory = 0
        self.expanded_nodes = 0
        
        MAX_NODE = 100000

        tracemalloc.start()
        start_time = time.time()
        

        result = self.run_aStar(board)

        self.time = time.time() - start_time
        
        _, peak = tracemalloc.get_traced_memory()
    
        self.memory = peak / 1024  # KB
        
        tracemalloc.stop()

        return result
    
    def select_cell(self, domain: dict[tuple[int,int]: set[int]]) -> tuple:
        # MRV + Degree tiebreaker
        def degree(cell):
            i, j = cell
            count = 0
            for nb in [(i,j-1),(i,j+1),(i-1,j),(i+1,j)]:
                if nb in domain: count += 1
            return -count

        return min(domain.keys(), key=lambda c: (len(domain[c]), degree(c)))

    def run_aStar(self, board: Board) -> bool:
        domain = self.init_domain(board)

        if domain is None:
            return False
        
        init_g = 0
        init_h = self.compute_h(board.N, board.assignment, domain, board.context)
        counter = 0

        open_set = [(init_g + init_h, -init_g, counter, board.assignment.copy(), domain)]
        
        result = False

        while open_set:
            f, g, _, assignment, current_domain = heapq.heappop(open_set)
            self.expanded_nodes += 1

            if not current_domain:  # current domain rỗng = điền hết
                board.assignment = assignment
                result = True
                break

            i,j = self.select_cell(current_domain)

            for v in current_domain[(i,j)]:
                new_domain = self.propagate(current_domain, i, j, v, board.context)
                if new_domain is None:
                    continue

                new_assignment = assignment.copy()
                new_assignment[(i,j)] = v

                new_h = self.compute_h(board.N, new_assignment, new_domain, board.context)
                if new_h == math.inf:
                    continue
                
                new_g = g + 1
                
                new_f = new_g + new_h

                counter += 1
                heapq.heappush(open_set, (new_f, -new_g, counter, new_assignment, new_domain))

        return result
    
def main():
    input = r"Inputs\test.txt"
    
    N, given, less_h, greater_h, less_v, greater_v = parse_input(input)
    print(given)
    
    context = PuzzleContext(N, given, less_h, greater_h, less_v, greater_v)
    board = Board(given, context)
    

    solver = AStar()
    result = solver.solve(board)
    print(result)
    if result:
        grid = board.to_grid()
        output = parse_output(grid,context)
        print(output)


    print(f"Time:     {solver.time:.4f}s")
    print(f"Memory:   {solver.memory:.2f}KB")
    print(f"Expanded: {solver.expanded_nodes} nodes")

if __name__ == "__main__":
    main()