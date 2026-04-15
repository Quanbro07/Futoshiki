from algorithm.PerformanceMetrics import PerformanceMetrics

from state.PuzzleContext import PuzzleContext
from state.Board import Board

from helperFunction.ParseInput import parse_input
from helperFunction.WriteOutput import parse_output

import heapq
import time
import tracemalloc

class AC_3(PerformanceMetrics):
    expanded_nodes: int

    def __init__(self):
        super().__init__()
        self.expanded_nodes = 0

    def init_domain(self, board: Board) -> dict[tuple[int,int], set[int]]:
        domain = {
            (i,j): set(range(1, board.N+1))
            for i in range(1, board.N+1)
            for j in range(1, board.N+1)
            if (i,j) not in board.assignment
        }

        # Propagate các given value
        for (i,j), v in board.assignment.items():
            changes, success = self.propagate(domain, i, j, v, board.context)
            if not success:
                return None  # puzzle vô nghiệm
        
        return domain

    def propagate(self, domain: dict[tuple[int,int], set[int]]
                          , i, j, v, 
                          context: PuzzleContext) -> tuple[dict, bool]:
        changes = {}

        # Xóa ô vừa gán
        if (i,j) in domain:
            removed = domain.pop((i,j))
            changes[(i,j)] = removed

        # Loại v khỏi cùng row
        for j2 in range(1, context.N+1):
            if (i,j2) in domain and v in domain[(i,j2)]:
                domain[(i,j2)].remove(v)
                changes.setdefault((i,j2), set()).add(v)
                if not domain[(i,j2)]:
                    return changes, False

        # Loại v khỏi cùng col
        for i2 in range(1, context.N+1):
            if (i2,j) in domain and v in domain[(i2,j)]:
                domain[(i2,j)].remove(v)
                changes.setdefault((i2,j), set()).add(v)
                if not domain[(i2,j)]:
                    return changes, False

        # LessH: cell(i,j) < cell(i,j+1) → right phải > v
        if (i,j) in context.less_h and (i,j+1) in domain:
            to_remove = {x for x in domain[(i,j+1)] if x <= v}
            for x in to_remove:
                domain[(i,j+1)].remove(x)
                changes.setdefault((i,j+1), set()).add(x)
            if not domain[(i,j+1)]:
                return changes, False

        # LessH: cell(i,j-1) < cell(i,j) → left phải < v
        if (i,j-1) in context.less_h and (i,j-1) in domain:
            to_remove = {x for x in domain[(i,j-1)] if x >= v}
            for x in to_remove:
                domain[(i,j-1)].remove(x)
                changes.setdefault((i,j-1), set()).add(x)
            if not domain[(i,j-1)]:
                return changes, False

        # GreaterH: cell(i,j) > cell(i,j+1) → right phải < v
        if (i,j) in context.greater_h and (i,j+1) in domain:
            to_remove = {x for x in domain[(i,j+1)] if x >= v}
            for x in to_remove:
                domain[(i,j+1)].remove(x)
                changes.setdefault((i,j+1), set()).add(x)
            if not domain[(i,j+1)]:
                return changes, False

        # GreaterH: cell(i,j-1) > cell(i,j) → left phải > v
        if (i,j-1) in context.greater_h and (i,j-1) in domain:
            to_remove = {x for x in domain[(i,j-1)] if x <= v}
            for x in to_remove:
                domain[(i,j-1)].remove(x)
                changes.setdefault((i,j-1), set()).add(x)
            if not domain[(i,j-1)]:
                return changes, False

        # LessV: cell(i,j) < cell(i+1,j) → below phải > v
        if (i,j) in context.less_v and (i+1,j) in domain:
            to_remove = {x for x in domain[(i+1,j)] if x <= v}
            for x in to_remove:
                domain[(i+1,j)].remove(x)
                changes.setdefault((i+1,j), set()).add(x)
            if not domain[(i+1,j)]:
                return changes, False

        # LessV: cell(i-1,j) < cell(i,j) → above phải < v
        if (i-1,j) in context.less_v and (i-1,j) in domain:
            to_remove = {x for x in domain[(i-1,j)] if x >= v}
            for x in to_remove:
                domain[(i-1,j)].remove(x)
                changes.setdefault((i-1,j), set()).add(x)
            if not domain[(i-1,j)]:
                return changes, False

        # GreaterV: cell(i,j) > cell(i+1,j) → below phải < v
        if (i,j) in context.greater_v and (i+1,j) in domain:
            to_remove = {x for x in domain[(i+1,j)] if x >= v}
            for x in to_remove:
                domain[(i+1,j)].remove(x)
                changes.setdefault((i+1,j), set()).add(x)
            if not domain[(i+1,j)]:
                return changes, False

        # GreaterV: cell(i-1,j) > cell(i,j) → above phải > v
        if (i-1,j) in context.greater_v and (i-1,j) in domain:
            to_remove = {x for x in domain[(i-1,j)] if x <= v}
            for x in to_remove:
                domain[(i-1,j)].remove(x)
                changes.setdefault((i-1,j), set()).add(x)
            if not domain[(i-1,j)]:
                return changes, False

        return changes, True

    def undo_propagate(self, domain: dict[tuple[int,int], set[int]], 
                       changes: dict[tuple[int,int], set[int]]):
        for cell, vals in changes.items():
            if cell not in domain:
                domain[cell] = vals        # restore ô đã xóa
            else:
                domain[cell].update(vals)  # restore values đã remove

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
    
    def ac3(self, domain: dict[tuple[int,int], set[int]], 
            context: PuzzleContext,
            assignment: dict[tuple[int,int], set[int]]) -> tuple[dict, bool]:
        ac3_changes = {}   # track changes của AC-3
        
        queue = set()
        for (i,j) in context.less_h:
            queue.add(((i,j), (i,j+1)))
            queue.add(((i,j+1), (i,j)))
        for (i,j) in context.greater_h:
            queue.add(((i,j), (i,j+1)))
            queue.add(((i,j+1), (i,j)))
        for (i,j) in context.less_v:
            queue.add(((i,j), (i+1,j)))
            queue.add(((i+1,j), (i,j)))
        for (i,j) in context.greater_v:
            queue.add(((i,j), (i+1,j)))
            queue.add(((i+1,j), (i,j)))

        while queue:
            (xi,xj), (yi,yj) = queue.pop()
            removed = self.revise(domain, xi, xj, yi, yj, context, assignment)
            if removed:
                if not domain.get((xi,xj)):
                    return ac3_changes, False
                # Lưu changes
                ac3_changes.setdefault((xi,xj), set()).update(removed)
                for nb in [(xi,xj-1),(xi,xj+1),(xi-1,xj),(xi+1,xj)]:
                    if nb in domain and nb != (yi,yj):
                        queue.add(((xi,xj), nb))

        return ac3_changes, True

    def select_cell(self, domain: dict[tuple[int,int], set[int]]) -> tuple[int,int]:
        # MRV + Degree
        def degree(cell:tuple):
            i,j = cell

            count = 0

            for nb in [(i,j-1),(i,j+1),(i-1,j),(i+1,j)]:
                if nb in domain: count += 1
            return -count

        return min(domain.keys(), key=lambda c: (len(domain[c]), degree(c)))
    
    def solve(self, board: Board) -> bool:
        self.time = 0
        self.memory = 0
        self.expanded_nodes = 0
        
        MAX_NODE = 100000

        tracemalloc.start()
        start_time = time.time()
        

        result = self.run_AC_3(board)

        self.time = time.time() - start_time
        
        _, peak = tracemalloc.get_traced_memory()
    
        self.memory = peak / 1024  # KB
        
        tracemalloc.stop()

        return result

    def run_AC_3(self, board: Board) -> bool:
        domain = self.init_domain(board)
        if domain is None:
            return False
        return self.search(board, domain)

    def search(self, board: Board, domain: dict[tuple[int,int], set[int]]) -> bool:
        if not domain:
            return True

        i, j = self.select_cell(domain)
        self.expanded_nodes += 1

        for v in list(domain[(i,j)]):
            # 1. GÁN TRẠNG THÁI TRƯỚC TIÊN
            board.assignment[(i,j)] = v
            board.context.row_used[i].add(v)
            board.context.col_used[j].add(v)
            
            # 2. PROPAGATE
            changes, success = self.propagate(domain, i, j, v, board.context)
            if not success:
                self.undo_propagate(domain, changes)
                continue
            
            # 3. AC-3 (Giờ nó đã có thể truy cập board.assignment mới nhất)
            ac3_changes, ac3_success = self.ac3(domain, board.context, board.assignment)
            if not ac3_success:
                self.undo_propagate(domain, ac3_changes)  # undo ac3 trước
                self.undo_propagate(domain, changes)       # undo propagate sau
                # Rollback state
                del board.assignment[(i,j)]
                board.context.row_used[i].remove(v)
                board.context.col_used[j].remove(v)
                continue

            board.assignment[(i,j)] = v
            board.context.row_used[i].add(v)
            board.context.col_used[j].add(v)

            # 4. TÌM KIẾM SÂU HƠN
            if self.search(board, domain):
                return True

            # 5. BACKTRACK
            del board.assignment[(i,j)]
            board.context.row_used[i].remove(v)
            board.context.col_used[j].remove(v)
            self.undo_propagate(domain, ac3_changes)  # undo ac3 trước
            self.undo_propagate(domain, changes)       # undo propagate sau

        return False
    

def main():
    input = r"Inputs\test.txt"
    
    N, given, less_h, greater_h, less_v, greater_v = parse_input(input)
    print(given)
    
    context = PuzzleContext(N, given, less_h, greater_h, less_v, greater_v)
    board = Board(given, context)
    

    solver = AC_3()
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