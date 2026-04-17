import pygame
import sys
import os
import random
from pathlib import Path

def show_size_menu(screen):
    font_title = pygame.font.SysFont("Arial", 45, bold=True)
    font_btn = pygame.font.SysFont("Arial", 30, bold=True)
    
    sizes = [4, 5, 6, 7, 8, 9]
    buttons = []
    
    # Bố cục 2 cột, 3 hàng
    btn_w, btn_h = 180, 70
    spacing_x, spacing_y = 50, 30
    start_x = (1000 - (2 * btn_w + spacing_x)) // 2
    start_y = 250

    for i, n in enumerate(sizes):
        col = i // 3
        row = i % 3
        rect = pygame.Rect(start_x + col * (btn_w + spacing_x), 
                           start_y + row * (btn_h + spacing_y), btn_w, btn_h)
        buttons.append((n, rect))

    while True:
        screen.fill((240, 240, 240))
        title = font_title.render("CHOOSE GRID SIZE", True, (50, 50, 50))
        screen.blit(title, title.get_rect(center=(500, 150)))

        m_pos = pygame.mouse.get_pos()
        for n, rect in buttons:
            hover = rect.collidepoint(m_pos)
            pygame.draw.rect(screen, (100, 200, 255) if hover else (200, 200, 200), rect, 0, 10)
            pygame.draw.rect(screen, (0, 0, 0), rect, 2, 10)
            txt = font_btn.render(f"{n} x {n}", True, (0, 0, 0))
            screen.blit(txt, txt.get_rect(center=rect.center))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for n, rect in buttons:
                    if rect.collidepoint(event.pos):
                        return n
        pygame.display.flip()

def generate_puzzle(N):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Nhảy ra ngoài 1 cấp để về thư mục gốc (Futoshiki)
    project_root = os.path.dirname(current_dir)
    
    # Bây giờ mới nối với thư mục Inputs
    input_path = os.path.join(project_root, 'Inputs', f'input{N}.txt')
    
    print(f"[DEBUG] Looking for file at: {input_path}")

    if os.path.exists(input_path):
        # Lưu ý: Vì welcome.py nằm trong GUI/, 
        # bạn cần đảm bảo helperFunction có thể import được (thường qua thư mục gốc)
        from helperFunction.ParseInput import parse_input
        return parse_input(input_path)
    else:
        print(f"!!! ERROR: File {input_path} does not exist.")
        return None