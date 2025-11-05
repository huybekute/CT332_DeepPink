import pygame
import os  # <<< THÊM DÒNG NÀY

# --- Định nghĩa thư mục chứa ảnh ---
IMAGE_DIR = "QuanCo1"
# Khởi tạo Pygame
pygame.init()

# Màu sắc và Font
WHITE = (255, 255, 255)
YELLOW = (255, 223, 0)
font = pygame.font.SysFont("Arial", 36)

# --- Giai đoạn 1: Tải tài nguyên THÔ (chưa .convert()) ---
try:
    background_raw = pygame.image.load("background/background1.png")
except pygame.error:
    background_raw = None

chessboard_image_raw = pygame.image.load("background/banco.png")
wood_texture_raw = pygame.image.load("textures/lightblue.jpg")
white_texture_raw = pygame.image.load("textures/deepblue.jpg")

white_pieces = {
    "P": pygame.image.load(os.path.join(IMAGE_DIR, "W-Pawn.png")),
    "R": pygame.image.load(os.path.join(IMAGE_DIR, "W-Rook.png")),
    "N": pygame.image.load(os.path.join(IMAGE_DIR, "W-Horse.png")),
    "B": pygame.image.load(os.path.join(IMAGE_DIR, "W-Bishop.png")),
    "Q": pygame.image.load(os.path.join(IMAGE_DIR, "W-Queen.png")),
    "K": pygame.image.load(os.path.join(IMAGE_DIR, "W-King.png"))
}
black_pieces = {
    "P": pygame.image.load(os.path.join(IMAGE_DIR, "B-Pawn.png")),
    "R": pygame.image.load(os.path.join(IMAGE_DIR, "B-Rook.png")),
    "N": pygame.image.load(os.path.join(IMAGE_DIR, "B-Horse.png")),
    "B": pygame.image.load(os.path.join(IMAGE_DIR, "B-Bishop.png")),
    "Q": pygame.image.load(os.path.join(IMAGE_DIR, "B-Queen.png")),
    "K": pygame.image.load(os.path.join(IMAGE_DIR, "B-King.png"))
}

# --- Biến toàn cục để lưu tài nguyên đã tối ưu hóa ---
background = None
chessboard_image = None
wood_texture = None
white_texture = None
assets_initialized = False
from game_rules import white_board, black_board
# --- Giai đoạn 2: Trạng thái bàn cờ và tính toán hình học ---
top_left = (400, 220); top_right = (1183, 220)
bottom_left = (295, 750); bottom_right = (1268, 750)

def interpolate(p1, p2, t):
    return p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t

def get_cell_corners(row, col):
    t_row_top, t_row_bottom = row / 8, (row + 1) / 8
    t_col_left, t_col_right = col / 8, (col + 1) / 8
    tl = interpolate(interpolate(top_left, bottom_left, t_row_top), interpolate(top_right, bottom_right, t_row_top), t_col_left)
    tr = interpolate(interpolate(top_left, bottom_left, t_row_top), interpolate(top_right, bottom_right, t_row_top), t_col_right)
    bl = interpolate(interpolate(top_left, bottom_left, t_row_bottom), interpolate(top_right, bottom_right, t_row_bottom), t_col_left)
    br = interpolate(interpolate(top_left, bottom_left, t_row_bottom), interpolate(top_right, bottom_right, t_row_bottom), t_col_right)
    return [tl, tr, br, bl]

def generate_cells():
    cells_list = []
    for r in range(8):
        row_cells = [(sum(p[0] for p in get_cell_corners(r, c))/4, sum(p[1] for p in get_cell_corners(r, c))/4) for c in range(8)]
        cells_list.append(row_cells)
    return cells_list
cells = generate_cells()

# --- Giai đoạn 3: Các hàm vẽ ---

def draw_cell_with_texture(surface, corners, texture):
    min_x = int(min(p[0] for p in corners))
    max_x = int(max(p[0] for p in corners))
    min_y = int(min(p[1] for p in corners))
    max_y = int(max(p[1] for p in corners))
    width, height = max_x - min_x, max_y - min_y
    if width <= 0 or height <= 0: return

    texture_scaled = pygame.transform.smoothscale(texture, (width, height))
    mask_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    shifted_corners = [(x - min_x, y - min_y) for (x, y) in corners]
    pygame.draw.polygon(mask_surface, (255, 255, 255), shifted_corners)
    texture_mask = pygame.mask.from_surface(mask_surface)
    mask_surface.fill((0, 0, 0, 0))
    for y in range(height):
        for x in range(width):
            if texture_mask.get_at((x, y)):
                mask_surface.set_at((x, y), texture_scaled.get_at((x, y)))
    surface.blit(mask_surface, (min_x, min_y))

def draw_game_screen(screen, width, height):
    global assets_initialized, background, chessboard_image, wood_texture, white_texture

    if not assets_initialized:
        if background_raw:
            background = background_raw.convert()
        
       
        chessboard_image = chessboard_image_raw.convert_alpha() 
        
        wood_texture = wood_texture_raw.convert()
        white_texture = white_texture_raw.convert()
        for piece in white_pieces:
            white_pieces[piece] = white_pieces[piece].convert_alpha()
        for piece in black_pieces:
            black_pieces[piece] = black_pieces[piece].convert_alpha()
        assets_initialized = True

    if background:
        bg_scaled = pygame.transform.scale(background, (width, height))
        screen.blit(bg_scaled, (0, 0))
    else:
        screen.fill((50, 50, 50))

    board_size = int(min(width, height) * 1.5)
    board_x = (width - board_size) // 2
    board_y = (height - board_size) // 2
    chessboard_scaled = pygame.transform.scale(chessboard_image, (board_size, board_size))
    screen.blit(chessboard_scaled, (board_x, board_y))
    
    for row in range(8):
        for col in range(8):
            corners = get_cell_corners(row, col)
            texture_to_use = white_texture if (row + col) % 2 == 0 else wood_texture
            draw_cell_with_texture(screen, corners, texture_to_use)

    for row in range(8):
        for col in range(8):
            piece, piece_map, color = None, None, None
            if white_board[row][col]:
                piece, piece_map, color = white_board[row][col], white_pieces, "white"
            elif black_board[row][col]:
                piece, piece_map, color = black_board[row][col], black_pieces, "black"

            if piece:
                corners = get_cell_corners(row, col)
                x_center = sum(p[0] for p in corners) / 4
                y_bottom = (corners[2][1] + corners[3][1]) / 2
                bottom_width = abs(corners[2][0] - corners[3][0])
                orig_width, orig_height = piece_map[piece].get_size()
                
                scale_ratio = bottom_width / orig_width
                if color == "white":
                    if piece =="P": scale_ratio *=0.65
                    elif piece =="B": scale_ratio*=0.65
                    else: scale_ratio*=0.8
                else:
                    if piece == "K": scale_ratio *= 1.1
                    elif piece=="P": scale_ratio *=0.9
                    else: scale_ratio *= 0.8 
                
                new_size = (int(orig_width * scale_ratio), int(orig_height * scale_ratio))
                img = pygame.transform.smoothscale(piece_map[piece], new_size)
                img_rect = img.get_rect(midbottom=(int(x_center), int(y_bottom)))
                screen.blit(img, img_rect)