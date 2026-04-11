def is_valid(assignment: dict[tuple[int,int]: int],
                i: int, j: int, v: int, 
                row_used: dict[int: set[int]],
                col_used: dict[int: set[int]],
                less_h: set[tuple[int,int]],
                greater_h: set[tuple[int,int]],
                less_v: set[tuple[int,int]],
                greater_v: set[tuple[int,int]]):
    # Check row unque
    if v in row_used[i]:
        return False
    
    # Check col unque
    if v in col_used[j]:
        return False
    
    # Check Less H: cell(i,j) < cell(i, j+ 1)
    if (i,j) in less_h:
        right = assignment.get((i, j + 1))
        if right is not None and v >= right:
            return False
    # Bên trái
    if(i,j-1) in less_h:
        left = assignment.get((i, j - 1))
        if left is not None and left >= v:
            return False

    
    # Check Greater H: cell(i,j) > cell(i, j+ 1)
    if (i,j) in greater_h:
        right = assignment.get((i, j + 1))
        if right is not None and v <= right:
            return False
    # Bên trái
    if(i,j-1) in greater_h:
        left = assignment.get((i, j - 1))
        if left is not None and left <= v:
            return False
    

    # Check Less V: cell(i,j) < cell(i + 1, j)
    if (i,j) in less_v:
        below = assignment.get((i + 1, j))
        if below is not None and v >= below:
            return False
        
    # Bên Tren
    if(i - 1,j) in less_v:
        above = assignment.get((i - 1, j))
        if above is not None and above >= v:
            return False

    
    # Check Greater H: cell(i,j) > cell(i + 1,)
    if (i,j) in greater_v:
        below = assignment.get((i + 1, j))
        if below is not None and v <= below:
            return False
    # Bên Trên
    if(i - 1,j) in greater_v:
        above = assignment.get((i - 1, j))
        if above is not None and above <= v:
            return False
    
    return True
    