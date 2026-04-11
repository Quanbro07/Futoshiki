from helperFunction.GenerateRowColUsed import get_row_col_used
class PuzzleContext:
    N: int
    
    row_used: dict[int: set[int]]
    col_used: dict[int: set[int]]
    
    less_h: set[tuple[int,int]]
    greater_h: set[tuple[int,int]]
    less_v: set[tuple[int,int]]
    greater_v: set[tuple[int,int]]

    def __init__(self, N, given, less_h, greater_h, less_v, greater_v):
        self.N = N
        self.less_h = less_h
        self.greater_h = greater_h
        self.less_v = less_v
        self.greater_v = greater_v
        
        self.row_used, self.col_used = get_row_col_used(self.N, given)