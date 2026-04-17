import pygame
import sys
import os
import random
from helperFunction.ParseInput import parse_input
from GUI.welcome import show_size_menu
from GUI.welcome import generate_puzzle
from GUI.board_gui import FutoshikiGUI
from GUI.constants import WIDTH, HEIGHT


def load_new_game(game_id=None):
    """Hàm tải file input và xử lý lỗi đường dẫn"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, 'Inputs')
    
    if not os.path.exists(input_folder):
        print(f"Error: Folder {input_folder} not found!")
        return None

    all_files = [f for f in os.listdir(input_folder) if f.endswith('.txt') and f.startswith('input')]
    if not all_files:
        print("Error: No input files found!")
        return None

    if game_id is not None and f"input{game_id}.txt" in all_files:
        selected_file = f"input{game_id}.txt"
    else:
        selected_file = random.choice(all_files)
        
    input_path = os.path.join(input_folder, selected_file)
    data = parse_input(input_path)
    print(f"Loaded: {selected_file}")
    return data

def run_gui():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    N_selected = show_size_menu(screen)
    
    # BƯỚC 2: Sinh Puzzle từ size đã chọn
    current_data = generate_puzzle(N_selected)
    if current_data is None:
        print("Lỗi: Không thể tìm thấy file input cho kích thước đã chọn.")
        # Bạn có thể quay lại menu hoặc thoát
        pygame.quit()
        return
    N, given, less_h, greater_h, less_v, greater_v = current_data
    
    # BƯỚC 3: Khởi tạo GUI game
    gui = FutoshikiGUI(N, given, less_h, greater_h, less_v, greater_v)
    clock = pygame.time.Clock()


    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEBUTTONDOWN:
                action = gui.handle_click(event.pos)
                
                if action == "Solve":
                    if gui.solved_solution:
                        # Điền đáp án với màu xanh biển (nhờ logic trong draw)
                        gui.grid = [row[:] for row in gui.solved_solution]
                
                elif action == "Restart":
                    # Đưa về trạng thái ban đầu của màn hiện tại (given_clues)
                    gui.reset_to_clues()
                    gui.history = []
                    
                elif action == "Undo":
                    if gui.history:
                        gui.grid = gui.history.pop()
                    
                elif action == "New Game":
                    N_selected = show_size_menu(screen)
                    N, given, less_h, greater_h, less_v, greater_v = generate_puzzle(N_selected)
                    gui = FutoshikiGUI(N, given, less_h, greater_h, less_v, greater_v)
            
            if event.type == pygame.KEYDOWN:
                gui.handle_input(event.key)

        gui.draw(screen)
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    run_gui()