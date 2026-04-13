import pygame
import copy
from .constants import *
from algorithm.ForwardChaining import ForwardChaining

class FutoshikiGUI:
    def __init__(self, N, given, less_h, greater_h, less_v, greater_v):
        self.N = N
        self.given_clues = given
        self.less_h = less_h
        self.greater_h = greater_h
        self.less_v = less_v
        self.greater_v = greater_v
        self.gap = 30
        
        # --- TÍNH TOÁN CĂN GIỮA ---
        # Tổng chiều rộng lưới = (N * cell_size) + (N-1) * gap
        # Tính cell_size dựa trên GRID_SIZE cố định
        self.cell_size = (GRID_SIZE - (self.N - 1) * self.gap) // self.N
        self.total_grid_w = self.N * self.cell_size + (self.N - 1) * self.gap
        self.offset_x = (1000 - self.total_grid_w) // 2
        self.offset_y = 100 # Lề trên

        self.grid = [[0]*N for _ in range(N)]
        for (r, c), val in given.items():
            self.grid[r-1][c-1] = val
            
        self.selected = None
        self.history = []

        # --- PRE-COMPUTING: CHẠY AI TRƯỚC KHI BẮT ĐẦU ---
        solver = ForwardChaining(N, given, less_h, greater_h, less_v, greater_v)
        if solver.solve():
            self.solved_solution = solver.get_grid()
        else:
            self.solved_solution = None
            print("Khong the giai ngay tu dau!")

    def draw(self, screen):
        screen.fill(WHITE)
        font = pygame.font.SysFont("Arial", 30)
        font_sign = pygame.font.SysFont("Arial", 25, bold=True)
        dups = self.get_duplicates()

        for r in range(self.N):
            for c in range(self.N):
                # Tọa độ căn giữa
                rect_x = self.offset_x + c * (self.cell_size + self.gap)
                rect_y = self.offset_y + r * (self.cell_size + self.gap)
                rect = pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size)

                if self.selected == (r, c):
                    pygame.draw.rect(screen, LIGHT_BLUE, rect)
                pygame.draw.rect(screen, BLACK, rect, 2)

                val = self.grid[r][c]
                if val != 0:
                    color = GREEN if (r+1, c+1) in self.given_clues else BLUE
                    if (r, c) in dups: color = RED
                    text = font.render(str(val), True, color)
                    screen.blit(text, text.get_rect(center=rect.center))

        # --- VẼ DẤU SO SÁNH VỚI OFFSET ---
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

        self.draw_buttons(screen)

    def draw_buttons(self, screen):
        labels = ["Restart", "Undo", "Solve", "New Game"]
        self.btn_rects = []
        # Vị trí nút: Dưới lưới 2 khoảng gap
        start_btn_y = self.offset_y + self.total_grid_w + (2 * self.gap)
        
        btn_w, btn_h = 120, 45
        # Căn giữa cụm nút
        total_btns_w = len(labels) * btn_w + (len(labels) - 1) * 20
        start_btn_x = (1000 - total_btns_w) // 2

        for i, label in enumerate(labels):
            rect = pygame.Rect(start_btn_x + i * (btn_w + 20), start_btn_y, btn_w, btn_h)
            pygame.draw.rect(screen, GRAY, rect, 0, 5) # Bo góc nhẹ
            pygame.draw.rect(screen, BLACK, rect, 2, 5)
            text = pygame.font.SysFont("Arial", 18, bold=True).render(label, True, BLACK)
            screen.blit(text, text.get_rect(center=rect.center))
            self.btn_rects.append((label, rect))

    def handle_click(self, pos):
        for label, rect in self.btn_rects:
            if rect.collidepoint(pos):
                if label == "Solve" and self.solved_solution:
                    # Điền kết quả đã tính trước ngay lập tức
                    self.grid = copy.deepcopy(self.solved_solution)
                return label
        
        x, y = pos
        for r in range(self.N):
            for c in range(self.N):
                rect_x = self.offset_x + c * (self.cell_size + self.gap)
                rect_y = self.offset_y + r * (self.cell_size + self.gap)
                rect = pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size)
                if rect.collidepoint(x, y):
                    self.selected = (r, c)
                    return None
        return None

    # --- CÁC HÀM KHÁC GIỮ NGUYÊN ---
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
            if (r+1, c+1) in self.given_clues: return
            if pygame.K_1 <= key <= pygame.K_1 + self.N - 1:
                self.history.append(copy.deepcopy(self.grid))
                self.grid[r][c] = key - pygame.K_0
            elif key == pygame.K_BACKSPACE:
                self.history.append(copy.deepcopy(self.grid))
                self.grid[r][c] = 0