def get_row_col_used(N: int, given: dict[tuple[int,int] : int]):
    row_used = {i: set() for i in range(1, N + 1)}
    col_used = {j: set() for j in range(1, N + 1)}

    for (i,j), v in given.items():
        row_used[i].add(v)
        col_used[j].add(v)

    return row_used, col_used
