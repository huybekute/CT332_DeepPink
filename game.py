import pygame
import sys
import math

# --- THAY ĐỔI 1: Import toàn bộ module 'game_rules' và AI ---
import game_rules 
from game_rules import get_valid_moves, move_piece, get_piece_at
from ai_player import get_ai_move, load_ai_model

# --- THAY ĐỔI 2: Import cả 3 module đồ họa với tên khác nhau ---
# (Giả sử theme "Basic" là file gốc của bạn)
import game_screen as screen_basic
# (Giả sử "Water" là game_screen1.py)
import game_screen1 as screen_water
# (Giả sử "Event" là game_screen2.py)
import game_screen2 as screen_event
try:
    background_raw = pygame.image.load("background/background.jpg")
except pygame.error:
    background_raw = None
background= None
# Khởi tạo Pygame
pygame.init()

# Tải model AI
ai_model = load_ai_model()

# Lấy độ phân giải màn hình
screen_info = pygame.display.Info()
width, height = screen_info.current_w, screen_info.current_h

# Tạo cửa sổ game
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption('Chess Game')

# Màu sắc
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
PURPLE = (128, 0, 128)
HIGHLIGHT_COLOR = (100, 255, 100, 150)

font = pygame.font.SysFont("Arial", 36)

# --- THAY ĐỔI 3: Quản lý trạng thái game và module đồ họa ---
game_state = "MAIN_MENU" # Các trạng thái: "MAIN_MENU", "CHOOSE_THEME", "IN_GAME"
current_screen_module = None # <<< Biến mới để giữ module đồ họa đang dùng

selected_piece = None
valid_moves = []
button_width = width // 4
button_height = height // 7
button_x = (width - button_width) // 2
try:
    # Tải hình gốc
    start_img_raw = pygame.image.load("button/start_button.png").convert_alpha()
    quit_img_raw = pygame.image.load("button/quit_button.png").convert_alpha()
    basic_img_raw = pygame.image.load("button/basic_button.png").convert_alpha()
    water_img_raw = pygame.image.load("button/ocean_button.png").convert_alpha()
    event_img_raw = pygame.image.load("button/event_button.png").convert_alpha()

    # Scale hình ảnh về đúng kích thước nút
    start_img = pygame.transform.scale(start_img_raw, (button_width, button_height))
    quit_img = pygame.transform.scale(quit_img_raw, (button_width, button_height))
    basic_img = pygame.transform.scale(basic_img_raw, (button_width, button_height))
    water_img = pygame.transform.scale(water_img_raw, (button_width, button_height))
    event_img = pygame.transform.scale(event_img_raw, (button_width, button_height))

except pygame.error as e:
    print(f"LỖI: Không thể tải hình ảnh nút! {e}")
    pygame.quit()
    sys.exit()

def is_point_in_polygon(point, polygon_vertices):
    x, y = point
    n = len(polygon_vertices)
    inside = False
    p1x, p1y = polygon_vertices[0]
    for i in range(n + 1):
        p2x, p2y = polygon_vertices[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def get_cell_from_mouse(pos):
    # <<< THAY ĐỔI 4: Dùng module đồ họa hiện tại
    if not current_screen_module: return None
    
    for r in range(7, -1, -1):
        for c in range(8):
            corners = current_screen_module.get_cell_corners(r, c)
            if is_point_in_polygon(pos, corners):
                return (r, c)
    return None

def draw_valid_moves(surface, moves):
    # <<< THAY ĐỔI 5: Dùng module đồ họa hiện tại
    if not current_screen_module: return
    if current_screen_module == screen_basic:
        HIGHLIGHT_COLOR = (100, 255, 100, 150)
    elif current_screen_module == screen_water:
        HIGHLIGHT_COLOR = (255, 100, 100, 150)
    else: 
        HIGHLIGHT_COLOR = (100, 255, 100, 150)
    for move in moves:
        r, c = move
        x, y = current_screen_module.cells[r][c]
        s = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(s, HIGHLIGHT_COLOR, (15, 15), 15)
        surface.blit(s, (x - 15, y - 15))

# Hàm chính của game
def game_loop():
    global game_state, selected_piece, valid_moves, current_screen_module    
    # Nút màn hình chính
    start_button_y = height // 2 - button_height // 2
    quit_button_y = height // 2 + button_height // 2 + 20
    
    # Nút chọn theme
    theme_button_y_start = height // 2 - (button_height * 3 + 40) // 2
    basic_button_y = theme_button_y_start
    water_button_y = theme_button_y_start + button_height + 20
    event_button_y = theme_button_y_start + (button_height + 20) * 2

    while True:
        
        # Vẽ nền xám mặc định cho menu
        if game_state == "MAIN_MENU" or game_state == "CHOOSE_THEME":
            if background_raw:
                background = background_raw.convert()
            if background:
                bg_scaled = pygame.transform.scale(background, (width, height))
                screen.blit(bg_scaled, (0, 0))
            else:
                screen.fill((50, 50, 50))
        elif game_state == "IN_GAME":
            # Chỉ vẽ bàn cờ khi đã vào game
            current_screen_module.draw_game_screen(screen, width, height)
        # --- THAY ĐỔI 6: Vòng lặp game dựa trên STATE ---
        
        if game_state == "MAIN_MENU":
            screen.blit(start_img, (button_x, start_button_y))
            screen.blit(quit_img, (button_x, quit_button_y))
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    if button_x <= mouse_x <= button_x + button_width and start_button_y <= mouse_y <= start_button_y + button_height:
                        game_state = "CHOOSE_THEME"
                    if button_x <= mouse_x <= button_x + button_width and quit_button_y <= mouse_y <= quit_button_y + button_height:
                        pygame.quit()
                        sys.exit()
        
        elif game_state == "CHOOSE_THEME":
            screen.blit(basic_img, (button_x, basic_button_y))
            screen.blit(water_img, (button_x, water_button_y))
            screen.blit(event_img, (button_x, event_button_y))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    chosen_module = None
                    if button_x <= mouse_x <= button_x + button_width and basic_button_y <= mouse_y <= basic_button_y + button_height:
                        chosen_module = screen_basic
                    if button_x <= mouse_x <= button_x + button_width and water_button_y <= mouse_y <= water_button_y + button_height:
                        chosen_module = screen_water
                    if button_x <= mouse_x <= button_x + button_width and event_button_y <= mouse_y <= event_button_y + button_height:
                        chosen_module = screen_event
                    
                    if chosen_module:
                        current_screen_module = chosen_module # <<< ĐẶT MODULE ĐỒ HỌA
                        game_rules.current_turn = "white"
                        game_state = "IN_GAME"
                        
        elif game_state == "IN_GAME":
            # --- Đây là logic game cũ của bạn ---
            
            # 1. Vẽ bàn cờ (dùng module đã chọn)
            current_screen_module.draw_game_screen(screen, width, height) 

            # 2. Xử lý logic game
            if game_rules.current_turn == 'white' and not game_rules.promotion_pending:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_cell = get_cell_from_mouse(mouse_pos)
                        if clicked_cell:
                            r, c = clicked_cell
                            if selected_piece:
                                if (r, c) in valid_moves:
                                    move_piece(selected_piece, (r, c))
                                    selected_piece = None
                                    valid_moves = []
                                else:
                                    selected_piece = None
                                    valid_moves = []
                                    piece, color = get_piece_at(r, c)
                                    if piece and color == game_rules.current_turn:
                                        selected_piece = (r, c)
                                        valid_moves = get_valid_moves(r, c)
                            else:
                                piece, color = get_piece_at(r, c)
                                if piece and color == game_rules.current_turn:
                                    selected_piece = (r, c)
                                    valid_moves = get_valid_moves(r, c)
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

            if game_rules.current_turn == 'black' and not game_rules.promotion_pending:
                ai_move = get_ai_move(ai_model) 
                if ai_move:
                    start_pos, end_pos = ai_move
                    move_piece(start_pos, end_pos)
                else:
                    print("AI không thể di chuyển! Trò chơi kết thúc.")
                    game_state = "MAIN_MENU"

            # 3. Vẽ highlight
            if game_rules.current_turn == 'white':
                draw_valid_moves(screen, valid_moves)
        
        pygame.display.flip()

# Chạy game
game_loop()