import pygame
import copy
from .constants import *
from state.Board import Board
from state.PuzzleContext import PuzzleContext
from algorithm.AC_3 import AC_3

class FutoshikiGUI:
    def __init__(self, N, given, less_h, greater_h, less_v, greater_v):
        self.N = N
        self.given_clues = given
        self.less_h = less_h
        self.greater_h = greater_h
        self.less_v = less_v
        self.greater_v = greater_v
        
        self.grid = [[0]*N for _ in range(N)]
        for (r, c), val in given.items():
            self.grid[r-1][c-1] = val

        self.context = PuzzleContext(N, given, less_h, greater_h, less_v, greater_v)
        self.board_obj = Board(given, self.context)
        self.solver = AC_3()

        if self.solver.solve(self.board_obj):
            self.solved_solution = self.board_obj.to_grid() # Lưu kết quả vào biến riêng
        else:
            self.solved_solution = None

        # --- LAYOUT CALCULATIONS ---
        self.gap = 30
        self.cell_size = (GRID_SIZE - (self.N - 1) * self.gap) // self.N
        self.total_grid_w = self.N * self.cell_size + (self.N - 1) * self.gap
        self.offset_x = (1000 - self.total_grid_w) // 2
        self.offset_y = 100 

        
            
        self.selected = None
        self.history = []

        # --- BUTTONS SETUP ---
        self.labels = ["Restart", "Undo", "Solve", "New Game"]
        self.btn_rects = []
        self.init_button_rects()
    
    def init_button_rects(self):
        btn_w, btn_h = 120, 45
        spacing = 20
        total_btns_w = len(self.labels) * btn_w + (len(self.labels) - 1) * spacing
        start_btn_x = (1000 - total_btns_w) // 2
        # Đặt nút dưới lưới
        start_btn_y = self.offset_y + self.total_grid_w + (2 * self.gap)
        
        self.btn_rects = []
        for i, label in enumerate(self.labels):
            rect = pygame.Rect(start_btn_x + i * (btn_w + spacing), start_btn_y, btn_w, btn_h)
            self.btn_rects.append((label, rect))

    def draw(self, screen):
        screen.fill(WHITE)
        font = pygame.font.SysFont("Arial", 30)
        font_sign = pygame.font.SysFont("Arial", 25, bold=True)
        mouse_pos = pygame.mouse.get_pos()
        dups = self.get_duplicates()

        # 1. Vẽ các ô số
        for r in range(self.N):
            for c in range(self.N):
                rect_x = self.offset_x + c * (self.cell_size + self.gap)
                rect_y = self.offset_y + r * (self.cell_size + self.gap)
                rect = pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size)

                # Vẽ viền ô: Xanh Cyan nếu chọn, Đen nếu bình thường
                if self.selected == (r, c):
                    pygame.draw.rect(screen, (0, 180, 255), rect, 4)
                else:
                    pygame.draw.rect(screen, BLACK, rect, 2)

                val = self.grid[r][c]
                if val != 0:
                    # LOGIC MÀU SẮC ƯU TIÊN:
                    if (r, c) in dups:
                        color = RED               # 1. Sai luật trùng hàng/cột -> Đỏ
                    elif (r + 1, c + 1) in self.given_clues:
                        color = BLACK             # 2. Số đề bài cho -> Đen
                    else:
                        color = (0, 0, 255)       # 3. Số mình điền HOẶC Auto Solve -> Xanh biển

                    text_surf = font.render(str(val), True, color)
                    screen.blit(text_surf, text_surf.get_rect(center=rect.center))
        for (r, c) in self.less_h:
            cx = self.offset_x + c * self.cell_size + c * self.gap - (self.gap // 2)
            cy = self.offset_y + (r-1) * (self.cell_size + self.gap) + self.cell_size // 2
            screen.blit(font_sign.render("<", True, BLACK), font_sign.render("<", True, BLACK).get_rect(center=(cx, cy)))

        for (r, c) in self.greater_h:
            cx = self.offset_x + c * self.cell_size + c * self.gap - (self.gap // 2)
            cy = self.offset_y + (r-1) * (self.cell_size + self.gap) + self.cell_size // 2
            screen.blit(font_sign.render(">", True, BLACK), font_sign.render(">", True, BLACK).get_rect(center=(cx, cy)))

        for (r, c) in self.less_v:
            cx = self.offset_x + (c-1) * (self.cell_size + self.gap) + self.cell_size // 2
            cy = self.offset_y + r * self.cell_size + r * self.gap - (self.gap // 2)
            screen.blit(font_sign.render("^", True, BLACK), font_sign.render("^", True, BLACK).get_rect(center=(cx, cy)))

        for (r, c) in self.greater_v:
            cx = self.offset_x + (c-1) * (self.cell_size + self.gap) + self.cell_size // 2
            cy = self.offset_y + r * self.cell_size + r * self.gap - (self.gap // 2)
            screen.blit(font_sign.render("v", True, BLACK), font_sign.render("v", True, BLACK).get_rect(center=(cx, cy)))

        # 3. Vẽ nút bấm (Đã tích hợp hover và xóa hàm lỗi draw_buttons)
        for label, rect in self.btn_rects:
            is_hovered = rect.collidepoint(mouse_pos)
            bg_color = (200, 200, 200) if is_hovered else GRAY
            
            pygame.draw.rect(screen, bg_color, rect, 0, 5)
            pygame.draw.rect(screen, BLACK, rect, 2, 5)
            
            text_color = BLUE if is_hovered else BLACK
            text = pygame.font.SysFont("Arial", 18, bold=True).render(label, True, text_color)
            screen.blit(text, text.get_rect(center=rect.center))

    def handle_click(self, pos):
        for label, rect in self.btn_rects:
            if rect.collidepoint(pos):
                if label == "Solve": 
                    if self.solved_solution:
                        self.grid = [row[:] for row in self.solved_solution]
                elif label == "Undo":
                    self.undo()
                return label 
        
        for r in range(self.N):
            for c in range(self.N):
                rect_x = self.offset_x + c * (self.cell_size + self.gap)
                rect_y = self.offset_y + r * (self.cell_size + self.gap)
                rect = pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size)
                if rect.collidepoint(pos):
                    self.selected = (r, c)
                    return None
        self.selected = None
        return None

    def get_duplicates(self):
        dups = set()
        for r in range(self.N):
            row = [self.grid[r][c] for c in range(self.N) if self.grid[r][c] != 0]
            for c in range(self.N):
                if self.grid[r][c] != 0 and row.count(self.grid[r][c]) > 1: dups.add((r, c))
        for c in range(self.N):
            col = [self.grid[r][c] for r in range(self.N) if self.grid[r][c] != 0]
            for r in range(self.N):
                if self.grid[r][c] != 0 and col.count(self.grid[r][c]) > 1: dups.add((r, c))
        return dups

    def undo(self):
        if self.history: self.grid = self.history.pop()

    def handle_input(self, key):
        if self.selected:
            r, c = self.selected
            # Kiểm tra xem ô này có phải là số đề bài không (tọa độ từ 1)
            if (r + 1, c + 1) in self.given_clues:
                return # Không cho phép điền vào ô đề bài

            val = 0
            # Nhận diện phím số hàng ngang (1-9)
            if pygame.K_1 <= key <= pygame.K_9:
                val = key - pygame.K_1 + 1
            # Nhận diện phím số bên bàn phím Numpad (1-9)
            elif pygame.K_KP1 <= key <= pygame.K_KP9:
                val = key - pygame.K_KP1 + 1
            # Nhận diện phím xóa
            elif key == pygame.K_BACKSPACE or key == pygame.K_DELETE:
                val = 0
            else:
                return # Phím không hợp lệ thì thoát

            # Chỉ cho phép điền nếu số <= kích thước lưới N
            if val <= self.N:
                self.history.append(copy.deepcopy(self.grid))
                self.grid[r][c] = val