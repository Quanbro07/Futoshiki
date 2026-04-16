from state.PuzzleContext import PuzzleContext

def write_output(outputFile, output):
    with open(outputFile, "w") as f:
        f.write(output) 
    
def parse_output(grid:list[list[int]], context: PuzzleContext):
    N = context.N
    
    output = ""
    W = 4   # độ rộng mỗi ô
    
    for i in range(N):

        # dòng số + ngang
        for j in range(N):
            output += f"{grid[i][j]:^{W-1}}"

            if j < N - 1:
                if (i+1, j+1) in context.less_h:
                    output += "<"
                elif (i+1, j+1) in context.greater_h:
                    output += ">"
                else:
                    output += " "

        output += "\n"

        if i == N - 1:
            break

        # dòng dọc
        for j in range(N):
            if (i+1, j+1) in context.less_v:
                output += f"{'^':^{W}}"
            elif (i+1, j+1) in context.greater_v:
                output += f"{'V':^{W}}"
            else:
                output += " " * W

        output += "\n"

    return output
                  
def parse_write_ouput(outputFile,grid: list[list[int]], context: PuzzleContext):
    
    output = parse_output(grid, context)
    write_output(outputFile, output)
