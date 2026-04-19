import os

def read_input_file(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    size = int(lines[0])

    board = []
    for i in range(1, size + 1):
        row = [int(x.strip()) for x in lines[i].split(',')]
        board.append(row)

    # N lines horizontal constraints, each has N-1 values
    h_cons = []
    start_h = 1 + size
    for i in range(start_h, start_h + size):
        row = [int(x.strip()) for x in lines[i].split(',')]
        h_cons.append(row)

    # N-1 lines vertical constraints, each has N values
    v_cons = []
    start_v = start_h + size
    for i in range(start_v, start_v + size - 1):
        row = [int(x.strip()) for x in lines[i].split(',')]
        v_cons.append(row)

    return size, board, h_cons, v_cons


def format_futoshiki_board(size, board, h_cons, v_cons, title=None):
    lines = []

    if title:
        lines.append(f'=== {title} ===')

    for i in range(size):
        row_parts = []
        for j in range(size):
            cell = '.' if board[i][j] == 0 else str(board[i][j])
            row_parts.append(cell)

            if j < size - 1:
                # 1 means less, -1 means greater
                sign = ' '
                if h_cons[i][j] == 1:
                    sign = '<'
                elif h_cons[i][j] == -1:
                    sign = '>'
                row_parts.append(sign)

        lines.append(' '.join(row_parts))

        if i < size - 1:
            v_parts = []
            for j in range(size):
                # 1 means less, -1 means greater
                sign = ' '
                if v_cons[i][j] == 1:
                    sign = '^'
                elif v_cons[i][j] == -1:
                    sign = 'v'
                v_parts.append(sign)

                if j < size - 1:
                    v_parts.append(' ')

            lines.append(' '.join(v_parts))

    return '\n'.join(lines)

def main():
    input_folder = os.path.join(os.path.dirname(__file__), '../Inputs')
    output_folder = os.path.join(os.path.dirname(__file__), '../testing')
    os.makedirs(output_folder, exist_ok=True)

    output_txt = os.path.join(output_folder, 'boards_from_inputs.txt')
    input_files = sorted([f for f in os.listdir(input_folder) if f.endswith('.txt')])

    all_boards_text = []
    for file in input_files:
        file_path = os.path.join(input_folder, file)
        size, board, h_cons, v_cons = read_input_file(file_path)
        board_text = format_futoshiki_board(size, board, h_cons, v_cons, title=file)
        all_boards_text.append(board_text)

    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(all_boards_text))

    print(f'Saved all boards to: {output_txt}')

if __name__ == '__main__':
    main()
