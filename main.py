import pygame
import sys
import os
import random
from helperFunction.ParseInput import parse_input
from GUI.board_gui import FutoshikiGUI
from GUI.constants import WIDTH, HEIGHT
from algorithm.ForwardChaining import ForwardChaining

def run_gui():
    pygame.init()
    
    # --- KHẮC PHỤC LỖI FILE NOT FOUND ---
    # Lấy đường dẫn tuyệt đối đến thư mục chứa file main.py
    def load_new_game(game_id=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        input_folder = os.path.join(base_dir, 'Inputs')
        
        # Lấy danh sách tất cả các file .txt trong thư mục Inputs
        all_files = [f for f in os.listdir(input_folder) if f.endswith('.txt') and f.startswith('input')]
        if game_id is not None and f"input{game_id}.txt" in all_files:
            selected_file = f"input{game_id}.txt"
        else:
            selected_file = random.choice(all_files) # Chọn ngẫu nhiên
            
        input_path = os.path.join(input_folder, selected_file)
        data = parse_input(input_path)
        print(f"Loaded: {selected_file}")
        return data
    data = load_new_game() # Mặc định load ngẫu nhiên game khi khởi động
    N, given, less_h, greater_h, less_v, greater_v = data
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    gui = FutoshikiGUI(N, given, less_h, greater_h, less_v, greater_v)
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                action = gui.handle_click(event.pos)
                if action == "Restart":
                    gui.grid = [[0]*N for _ in range(N)]
                    for (r, c), val in given.items(): gui.grid[r-1][c-1] = val
                    gui.history = []
                elif action == "Undo":
                    gui.undo()
                elif action == "New Game":
                    new_data = load_new_game()
                    if new_data:
                        current_data = new_data
                        N, given, less_h, greater_h, less_v, greater_v = current_data
                        gui = FutoshikiGUI(N, given, less_h, greater_h, less_v, greater_v)
            if event.type == pygame.KEYDOWN:
                gui.handle_input(event.key)
        gui.draw(screen)
        pygame.display.flip()
        clock.tick(30)

if __name__ == "__main__":
    run_gui()