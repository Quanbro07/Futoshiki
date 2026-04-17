import pygame
import copy
from .constants import *
from state.Board import Board
from state.PuzzleContext import PuzzleContext
from algorithm.AC_3 import AC_3

class FutoshikiGUI:
    def __init__(self, N, given, less_h, greater_h, less_v, greater_v):
        self.N = N
        self.given_clues = copy.deepcopy(given)
        print(f"Số lượng clue ban đầu: {len(self.given_clues)}")
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
        self.labels = ["Restart", "Undo", "Solve", "New Game"]
        self.btn_rects = []
        self.init_button_rects()
    
    def is_win(self):
        for row in self.grid:
            if 0 in row:
                return False
                
        if len(self.get_violations()) > 0:
            return False
            
        return True

    def init_button_rects(self):
        btn_w, btn_h = 120, 45
        spacing = 20
        total_btns_w = len(self.labels) * btn_w + (len(self.labels) - 1) * spacing
        start_btn_x = (1000 - total_btns_w) // 2
        start_btn_y = self.offset_y + self.total_grid_w + (2 * self.gap)
        
        self.btn_rects = []
        for i, label in enumerate(self.labels):
            rect = pygame.Rect(start_btn_x + i * (btn_w + spacing), start_btn_y, btn_w, btn_h)
            self.btn_rects.append((label, rect))

    def get_violations(self):
        """Kiểm tra các ô vi phạm luật chơi (trùng hàng/cột hoặc sai dấu)"""
        violations = set()
        for r in range(self.N):
            for c in range(self.N):
                val = self.grid[r][c]
                if val == 0: continue
                
                # Kiểm tra trùng hàng/cột
                for i in range(self.N):
                    if i != c and self.grid[r][i] == val: violations.add((r, c))
                    if i != r and self.grid[i][c] == val: violations.add((r, c))
                
                # Kiểm tra dấu so sánh (Nếu ô bên cạnh cũng đã có số)
                # Dấu ngang (less_h: r, c < r, c+1)
                for (rh, ch) in self.less_h:
                    if self.grid[rh-1][ch-1] != 0 and self.grid[rh-1][ch] != 0:
                        if not (self.grid[rh-1][ch-1] < self.grid[rh-1][ch]):
                            violations.add((rh-1, ch-1)); violations.add((rh-1, ch))
                
                for (rh, ch) in self.greater_h:
                    if self.grid[rh-1][ch-1] != 0 and self.grid[rh-1][ch] != 0:
                        if not (self.grid[rh-1][ch-1] > self.grid[rh-1][ch]):
                            violations.add((rh-1, ch-1)); violations.add((rh-1, ch))
                
                # Dấu dọc
                for (rv, cv) in self.less_v:
                    if self.grid[rv-1][cv-1] != 0 and self.grid[rv][cv-1] != 0:
                        if not (self.grid[rv-1][cv-1] < self.grid[rv][cv-1]):
                            violations.add((rv-1, cv-1)); violations.add((rv, cv-1))

                for (rv, cv) in self.greater_v:
                    if self.grid[rv-1][cv-1] != 0 and self.grid[rv][cv-1] != 0:
                        if not (self.grid[rv-1][cv-1] > self.grid[rv][cv-1]):
                            violations.add((rv-1, cv-1)); violations.add((rv, cv-1))
        return violations

    def draw(self, screen):
        screen.fill(WHITE)
        font = pygame.font.SysFont("Arial", 30)
        font_sign = pygame.font.SysFont("Arial", 25, bold=True)
        mouse_pos = pygame.mouse.get_pos()
        dups = self.get_duplicates()
        violations = self.get_violations()

        # 1. Vẽ các ô số
        for r in range(self.N):
            for c in range(self.N):
                rect_x = self.offset_x + c * (self.cell_size + self.gap)
                rect_y = self.offset_y + r * (self.cell_size + self.gap)
                rect = pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size)

                color_rect = (0, 255, 0) if self.selected == (r, c) else BLACK
                pygame.draw.rect(screen, color_rect, rect, 3 if self.selected == (r, c) else 2)

                val = self.grid[r][c]
                if val != 0:
                    if (r, c) in violations:
                        color_text = RED
                    elif (r + 1, c + 1) in self.given_clues:
                        color_text = BLACK
                    else:
                        color_text = (0, 0, 255) # Xanh biển cho số điền vào
                    
                    text_surf = font.render(str(val), True, color_text)
                    screen.blit(text_surf, text_surf.get_rect(center=rect.center))

        if self.is_win():
            win_font = pygame.font.SysFont("Arial", 50, bold=True)
            # Tạo bóng đổ cho chữ để nổi bật hơn
            shadow_surf = win_font.render("VICTORY!", True, (50, 50, 50))
            text_surf = win_font.render("VICTORY!", True, (255, 215, 0)) 
            
            # Căn giữa màn hình
            rect = text_surf.get_rect(center=(1000 // 2, self.offset_y // 2))
            screen.blit(shadow_surf, rect.move(3, 3)) # Vẽ bóng trước
            screen.blit(text_surf, rect)

        self._draw_signs(screen, font_sign)

        # Vẽ nút bấm
        mouse_pos = pygame.mouse.get_pos()
        for label, rect in self.btn_rects:
            is_hover = rect.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (220, 220, 220) if is_hover else (180, 180, 180), rect, 0, 5)
            pygame.draw.rect(screen, BLACK, rect, 2, 5)
            txt = pygame.font.SysFont("Arial", 18, bold=True).render(label, True, BLACK)
            screen.blit(txt, txt.get_rect(center=rect.center))

    def _draw_signs(self, screen, font):
        # Tái sử dụng logic vẽ dấu của bạn nhưng căn chỉnh chuẩn xác hơn
        for (r, c) in self.less_h:
            cx = self.offset_x + c * self.cell_size + (c-0.5) * self.gap
            cy = self.offset_y + (r-1) * (self.cell_size + self.gap) + self.cell_size // 2
            screen.blit(font.render("<", True, BLACK), font.render("<", True, BLACK).get_rect(center=(cx, cy)))
        for (r, c) in self.greater_h:
            cx = self.offset_x + c * self.cell_size + (c-0.5) * self.gap
            cy = self.offset_y + (r-1) * (self.cell_size + self.gap) + self.cell_size // 2
            screen.blit(font.render(">", True, BLACK), font.render(">", True, BLACK).get_rect(center=(cx, cy)))
        for (r, c) in self.less_v:
            cx = self.offset_x + (c-1) * (self.cell_size + self.gap) + self.cell_size // 2
            cy = self.offset_y + r * self.cell_size + (r-0.5) * self.gap
            screen.blit(font.render("^", True, BLACK), font.render("^", True, BLACK).get_rect(center=(cx, cy)))
        for (r, c) in self.greater_v:
            cx = self.offset_x + (c-1) * (self.cell_size + self.gap) + self.cell_size // 2
            cy = self.offset_y + r * self.cell_size + (r-0.5) * self.gap
            screen.blit(font.render("v", True, BLACK), font.render("v", True, BLACK).get_rect(center=(cx, cy)))

    def handle_click(self, pos):
        for label, rect in self.btn_rects:
            if rect.collidepoint(pos): 
                if self.is_win():
                    if label in ["New Game", "Restart"]:
                        return label
                    else:
                        print(f"[DEBUG] Nút {label} đã bị khóa vì bạn đã thắng!")
                        return None
                return label
        
        
        for r in range(self.N):
            for c in range(self.N):
                rect_x = self.offset_x + c * (self.cell_size + self.gap)
                rect_y = self.offset_y + r * (self.cell_size + self.gap)
                if pygame.Rect(rect_x, rect_y, self.cell_size, self.cell_size).collidepoint(pos):
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

    def reset_to_clues(self):
        self.grid = [[0] * self.N for _ in range(self.N)]
        for (r, c), val in self.given_clues.items():
            self.grid[r-1][c-1] = val
        self.history = []
        self.selected = None
        print("[DEBUG] Game Restarted: Grid reset to initial clues.")

    def handle_input(self, key):
        if self.is_win():
            return
    
        if not self.selected: return
        r, c = self.selected
        target = (r + 1, c + 1)
        if target in self.given_clues:
            print(f"!!! TRÙNG CLUE: Hệ thống chặn không cho nhập vào {target}")
            return

        val = None
        if pygame.K_1 <= key <= pygame.K_9:
            val = key - pygame.K_0
            print(f"[DEBUG] Number key detected. Calculated val: {val}")
        elif pygame.K_KP1 <= key <= pygame.K_KP9:
            val = key - pygame.K_KP0
            print(f"[DEBUG] Numpad key detected. Calculated val: {val}")
        elif key in [pygame.K_BACKSPACE, pygame.K_DELETE, pygame.K_0, pygame.K_KP0]:
            val = 0
            print("[DEBUG] Delete/Zero key detected.")

        if val is not None:
            if val <= self.N:
                print(f"[DEBUG] Success! Updating grid[{r}][{c}] = {val}")
                self.history.append(copy.deepcopy(self.grid))
                self.grid[r][c] = val
            else:
                print(f"[DEBUG] Failure: Value {val} is greater than N ({self.N})")
        else:
            print("[DEBUG] Key is not a valid number or action.")