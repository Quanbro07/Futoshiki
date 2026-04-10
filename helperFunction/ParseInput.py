def parse_input(inputFile):
    with open(inputFile, 'r') as f:
        lines = [line.strip() for line in f if not line.startswith('#') and line.strip()]
    
    idx = 0
    N = int(lines[idx])
    idx += 1


    # Given
    given: dict[tuple[int,int]: int] = dict()

    for i in range(N):
        row = lines[idx].split(", ")
        idx += 1
        for j in range(len(row)):
            if row[j] != '0':
                given[(i + 1,j + 1)] = int(row[j])

    
    # Horizontal - Ngang
    less_h: set[tuple[int,int]] = set()    
    greater_h: set[tuple[int,int]] = set()

    for i in range(1, N+1):
        row = lines[idx].split(", ")
        idx += 1
        for j in range(len(row)):
            if(row[j] == '1'):
                less_h.add((i,j+1))
            if(row[j] == '-1'):
                greater_h.add((i,j+1))
    


    # Vertical - Dọc
    less_v: set[tuple[int,int]] = set()    
    greater_v: set[tuple[int,int]] = set()

    for i in range(1, N):
        row = lines[idx].split(", ")
        print(row)
        idx += 1
        for j in range(len(row)):
            if(row[j] == '1'):
                less_v.add((i,j + 1))
            if(row[j] == '-1'):
                greater_v.add((i,j + 1))
    
    return N, given, less_h, greater_h, less_v, greater_v




def main():
    input = r"D:\US\Nam_2_HK_2\Co So Tri Tue Nhan Tao\Project\Project_2\test.txt"
    parse_input(input)



if __name__ == "__main__":
    main()