from helperFunction.ValidateBoard import is_valid
from state.PuzzleContext import PuzzleContext

class Board:
    N: int
    assignment: dict[tuple[int,int]: int]
    context: PuzzleContext

    def __init__(self, assignment: dict[tuple[int,int]: int], context: PuzzleContext):
        self.assignment = assignment
        self.N = context.N
        self.context = context

    def is_complete(self)->bool:
        return len(self.assignment) == self.N * self.N
    
    def assign_value(self, i, j, v):
        self.assignment[(i,j)] = v
        self.context.row_used[i].add(v)
        self.context.col_used[j].add(v)
    
    def unassign_value(self, i, j):
        v = self.assignment.pop((i,j))
        self.context.row_used[i].remove(v)
        self.context.col_used[j].remove(v)
        return v

    def get_empty_cells(self) -> list[tuple[int,int]]:
        return [
            (i, j)
            for i in range(1, self.N + 1)
            for j in range(1, self.N + 1)
            if (i, j) not in self.assignment
        ]

    def get_valid_values(self,i , j)->list[int]:
        ctx = self.context
        return [
            v for v in range(1, self.N + 1) 
            if is_valid(self.assignment, i, j, v, 
                        ctx.row_used, ctx.col_used, 
                        ctx.less_h, ctx.greater_h,
                        ctx.less_v, ctx.greater_v)
        ]
    
    def to_grid(self) -> list[list[int]]:
        grid = []
        for i in range(self.N):
            row = []
            for j in range(self.N):
                v = self.assignment[(i + 1,j + 1)]
                if v is not None:
                    row.append(v)
                else:
                    row.append(0)
            grid.append(row)
        
        return grid
    
