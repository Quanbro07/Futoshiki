def write_output(outputFile, N:int  , grid: list[list[int]], 
                less_h: set[tuple[int,int]],
                greater_h: set[tuple[int,int]], 
                less_v: set[tuple[int,int]], 
                greater_v: set[tuple[int,int]]
                ):
    output = ""
    for i in range(N):
        for j in range(N):
            isAssign = False
            output += str(grid[i][j]) + " "
            if (i+1,j+1) in less_h:
                output += "< "
                isAssign = True

            if (i+1,j+1) in greater_h:
                output += "> "
                isAssign = True

            if isAssign:
                output += " "
            else: 
                output += " " * 3

        
        output += "\n"

        if i == N - 1:
            break
    
        for j in range(N):
            isAssign = False
            if (i+1,j+1) in less_v:
                if j == 0:
                    output += "^ "
                else:
                    output += "  ^ "
                isAssign = True

            if (i+1,j+1) in greater_v:
                output += "V "
                isAssign = True

            if isAssign:
                output += " " * 3
            else: 
                output += " " * 4
        
        output += "\n"
    
    print(f"{output}")                

def main():
    grid = [
        [2, 3, 4, 1],
        [1, 2, 3, 4],
        [4, 1, 2, 3],
        [3, 4, 1, 2] 
    ]
    N = 4

    less_h:set[tuple[int,int]] = set()

    less_h.add((1,1))
    less_h.add((4,3))

    greater_h:set[tuple[int,int]] = set()

    greater_h.add((2, 2))

    less_v:set[tuple[int,int]] = set()

    less_v.add((2,3))
    less_v.add((3,1))

    greater_v:set[tuple[int,int]] = set()

    greater_v.add((1, 1))

    output = "a"
    write_output(output,N,grid,less_h, greater_h, less_v, greater_v)


if __name__ == "__main__":
    main()