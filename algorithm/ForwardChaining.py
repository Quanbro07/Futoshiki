# algorithm/ForwardChaining.py

class ForwardChaining:
    def __init__(self, N, given, less_h, greater_h, less_v, greater_v):
        self.N = N
        self.less_h = less_h
        self.greater_h = greater_h
        self.less_v = less_v
        self.greater_v = greater_v
        self.domains = { (i, j): list(range(1, N + 1)) 
                         for i in range(1, N + 1) for j in range(1, N + 1) }
        for (i, j), val in given.items():
            self.domains[(i, j)] = [val]

    def solve(self):
        changed = True
        while changed:
            changed = False
            for i in range(1, self.N + 1):
                for j in range(1, self.N + 1):
                    # 1. Luật A3: Loại bỏ giá trị đã chốt khỏi hàng/cột
                    if len(self.domains[(i, j)]) == 1:
                        val = self.domains[(i, j)][0]
                        if self.prune_row_col(i, j, val):
                            changed = True
                    if self.apply_inequalities(i, j):
                        changed = True            
            # Kiểm tra trạng thái sau mỗi vòng quét
            if not changed: 
                if self.fill_hidden_singles():
                    changed = True
            if self.is_failed(): 
                return False
            
        return self.is_solved()

    def apply_inequalities(self, i, j):
        """Hàm duy nhất xử lý so sánh, đảm bảo không bị ghi đè"""
        res = False
        # Ràng buộc Ngang
        if j < self.N:
            if (i, j) in self.less_h:
                res |= self.constrain_pair((i, j), (i, j + 1), "less")
            if (i, j) in self.greater_h:
                res |= self.constrain_pair((i, j), (i, j + 1), "greater")

        # Ràng buộc Dọc
        if i < self.N:
            if (i, j) in self.less_v:
                res |= self.constrain_pair((i, j), (i + 1, j), "less")
            if (i, j) in self.greater_v:
                res |= self.constrain_pair((i, j), (i + 1, j), "greater")
        return res

    def fill_hidden_singles(self):
        res = False
        for r in range(1, self.N + 1):
            for val in range(1, self.N + 1):
                # Tìm xem số 'val' có thể nằm ở những đâu trong hàng 'r'
                possible_cols = [c for c in range(1, self.N + 1) if val in self.domains[(r, c)]]
                if len(possible_cols) == 1:
                    target_c = possible_cols[0]
                    if len(self.domains[(r, target_c)]) > 1:
                        self.domains[(r, target_c)] = [val]
                        res = True
        for c in range(1, self.N + 1):
            for val in range(1, self.N + 1):
                possible_rows = [r for r in range(1, self.N + 1) if val in self.domains[(r, c)]]
                if len(possible_rows) == 1:
                    target_r = possible_rows[0]
                    if len(self.domains[(target_r, c)]) > 1:
                        self.domains[(target_r, c)] = [val]
                        res = True
        return res

    def constrain_pair(self, pos1, pos2, type):
        """Siết chặt 2 chiều và ngăn lỗi max() rỗng"""
        res = False
        # Quan trọng: Nếu một trong hai ô đã rỗng, không làm gì cả để tránh lỗi max/min
        if not self.domains[pos1] or not self.domains[pos2]:
            return False

        if type == "less": # pos1 < pos2
            # Tỉa ô nhỏ
            max_v2 = max(self.domains[pos2])
            new_dom1 = [v for v in self.domains[pos1] if v < max_v2]
            if len(new_dom1) < len(self.domains[pos1]):
                self.domains[pos1] = new_dom1; res = True
            
            # Tỉa ô lớn
            if not self.domains[pos1]: return res
            min_v1 = min(self.domains[pos1])
            new_dom2 = [v for v in self.domains[pos2] if v > min_v1]
            if len(new_dom2) < len(self.domains[pos2]):
                self.domains[pos2] = new_dom2; res = True

        elif type == "greater": # pos1 > pos2
            # Tỉa ô lớn
            min_v2 = min(self.domains[pos2])
            new_dom1 = [v for v in self.domains[pos1] if v > min_v2]
            if len(new_dom1) < len(self.domains[pos1]):
                self.domains[pos1] = new_dom1; res = True
            
            # Tỉa ô nhỏ
            if not self.domains[pos1]: return res
            max_v1 = max(self.domains[pos1])
            new_dom2 = [v for v in self.domains[pos2] if v < max_v1]
            if len(new_dom2) < len(self.domains[pos2]):
                self.domains[pos2] = new_dom2; res = True
        return res

    def prune_row_col(self, r, c, val):
        res = False
        for k in range(1, self.N + 1):
            # Xử lý hàng
            if k != c and val in self.domains[(r, k)]:
                self.domains[(r, k)].remove(val)
                res = True
                if not self.domains[(r, k)]: return True # Trả về True để solve() gọi is_failed()
            # Xử lý cột
            if k != r and val in self.domains[(k, c)]:
                self.domains[(k, c)].remove(val)
                res = True
                if not self.domains[(k, c)]: return True
        return res

    def get_grid(self):
        grid = [[0]*self.N for _ in range(self.N)]
        for (i, j), dom in self.domains.items():
            if len(dom) == 1:
                grid[i-1][j-1] = dom[0]
            else:
                grid[i-1][j-1] = 0
        return grid

    def is_solved(self):
        return all(len(v) == 1 for v in self.domains.values())

    def is_failed(self):
        return any(len(v) == 0 for v in self.domains.values())