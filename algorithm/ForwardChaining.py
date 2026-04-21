# algorithm/ForwardChaining.py
import sys
import os
import time
import tracemalloc

# Đảm bảo import được helperFunction và fol
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from helperFunction.GenerateKB import generate_KB 
from helperFunction.ParseInput import parse_input

class ForwardChaining:
    def __init__(self, inputFile):
        self.kb = generate_KB(inputFile)
        self.N, _, _, _, _, _ = parse_input(inputFile)
        
        # Các biến đo lường hiệu năng
        self.run_time = 0
        self.memory_usage = 0

        self.domains = { (i, j): list(range(1, self.N + 1)) 
                         for i in range(1, self.N + 1) for j in range(1, self.N + 1) }
        
        for lit in self.kb.facts:
            pred = lit.predicate
            p_name = pred.__class__.__name__ 
            
            if p_name in ["Val", "Given"]:
                r, c, v = pred.args
                self.domains[(r, c)] = [v]

    def solve(self):
        # Bắt đầu đo bộ nhớ và thời gian
        tracemalloc.start()
        start_time = time.time()
        
        success = self._run_inference()
        
        # Kết thúc đo
        self.run_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        self.memory_usage = peak / 1024  # Chuyển sang KB
        tracemalloc.stop()
        
        return success

    def _run_inference(self):
        changed = True
        while changed:
            changed = False
            
            # Suy diễn từ Definite Clauses
            for clause in self.kb.definite_clauses:
                if self.apply_definite_clause(clause):
                    changed = True

            # Ràng buộc Unique (Hàng/Cột)
            for i in range(1, self.N + 1):
                for j in range(1, self.N + 1):
                    if len(self.domains[(i, j)]) == 1:
                        if self.prune_row_col(i, j, self.domains[(i, j)][0]):
                            changed = True

            if self.is_failed(): return False
        return True

    def apply_definite_clause(self, clause):
        res = False
        concl = clause.conclusion
        concl_name = concl.predicate.__class__.__name__
        
        if concl_name == "Less":
            for cond in clause.conditions:
                p_obj = cond.predicate
                p_name = p_obj.__class__.__name__
                
                if p_name in ["LessH", "GreaterH", "LessV", "GreaterV"]:
                    r, c = p_obj.args
                    
                    # Sửa lỗi: Truyền đúng 2 đối số (Small, Big) cho constrain_pair
                    if p_name == "LessH":      # Ô (r,c) < Ô (r,c+1)
                        res |= self.constrain_pair((r, c), (r, c + 1))
                    elif p_name == "GreaterH": # Ô (r,c) > Ô (r,c+1) -> (r,c+1) nhỏ hơn
                        res |= self.constrain_pair((r, c + 1), (r, c))
                    elif p_name == "LessV":    # Ô (r,c) < Ô (r+1,c)
                        res |= self.constrain_pair((r, c), (r + 1, c))
                    elif p_name == "GreaterV": # Ô (r,c) > Ô (r+1,c) -> (r+1,c) nhỏ hơn
                        res |= self.constrain_pair((r + 1, c), (r, c))
                    break 
        return res
    
    def constrain_pair(self, S, B):
        res = False
        
        # 1. Kiểm tra an toàn domain
        if S not in self.domains or B not in self.domains: return False
        if not self.domains[S] or not self.domains[B]: return False
        
        # 2. Cắt tỉa ô nhỏ (S): giá trị phải < Max của ô lớn (B)
        max_B = max(self.domains[B])
        new_S = [v for v in self.domains[S] if v < max_B]
        if len(new_S) < len(self.domains[S]):
            self.domains[S] = new_S
            res = True
            if not self.domains[S]: return res

        # 3. Cắt tỉa ô lớn (B): giá trị phải > Min của ô nhỏ (S)
        min_S = min(self.domains[S])
        new_B = [v for v in self.domains[B] if v > min_S]
        if len(new_B) < len(self.domains[B]):
            self.domains[B] = new_B
            res = True
            
        return res

    def prune_row_col(self, r, c, val):
        res = False
        for k in range(1, self.N + 1):
            if k != c and val in self.domains[(r, k)]:
                self.domains[(r, k)].remove(val); res = True
            if k != r and val in self.domains[(k, c)]:
                self.domains[(k, c)].remove(val); res = True
        return res

    def get_grid(self):
        grid = [[0]*self.N for _ in range(self.N)]
        for (i, j), dom in self.domains.items():
            grid[i-1][j-1] = dom[0] if len(dom) == 1 else 0
        return grid

    def print_pretty_grid(self, inputFile):
        N, _, less_h, greater_h, less_v, greater_v = parse_input(inputFile)
        grid_data = self.get_grid()
        
        # Độ rộng cố định cho mỗi số để dễ căn lề (ví dụ: 3 ký tự)
        cell_w = 3 
        
        print(f"\n--- Futoshiki {N}x{N} Result ---")
        for i in range(1, N + 1):
            # 1. In hàng số và dấu ngang
            row_str = ""
            for j in range(1, N + 1):
                val = grid_data[i-1][j-1]
                num = str(val) if val != 0 else "."
                row_str += num.center(cell_w) # Căn giữa con số
                
                if j < N:
                    if (i, j) in less_h: row_str += "<"
                    elif (i, j) in greater_h: row_str += ">"
                    else: row_str += " " # Khoảng trống giữa các số
            print(row_str)

            # 2. In hàng dấu dọc (^, v)
            if i < N:
                sep_str = ""
                for j in range(1, N + 1):
                    # Căn lề dấu dọc đúng vị trí cột của số bên trên
                    char = " "
                    if (i, j) in less_v: char = "^"
                    elif (i, j) in greater_v: char = "v"
                    
                    sep_str += char.center(cell_w)
                    
                    if j < N:
                        sep_str += " " # Khoảng trống bù cho vị trí dấu ngang
                print(sep_str)

    def is_solved(self):
        return all(len(v) == 1 for v in self.domains.values())

    def is_failed(self):
        for pos, v in self.domains.items():
            if len(v) == 0:
                print(f"DEBUG: Ô {pos} bị rỗng domain!") # Dòng này sẽ cứu bạn
                return True
        return False

# --- MAIN CHẠY TERMINAL ---
if __name__ == "__main__":
    path = "Inputs/input4.txt" 
    if os.path.exists(path):
        solver = ForwardChaining(path)
        print(f"--- Running Forward Chaining Inference ---")
        
        result = solver.solve()
        
        if result:
            # Gọi hàm in đẹp thay vì in thô
            solver.print_pretty_grid(path)
        else:
            print("No solution found.")
            
        print("-" * 30)
        print(f"Time:    {solver.run_time:.4f}s")
        print(f"Memory:  {solver.memory_usage:.2f}KB")