# game_rules.py


# --- Quản lý lượt đi ---
current_turn = "white"

# --- TÍNH NĂNG MỚI: Quản lý trạng thái phong cấp ---
# Biến này sẽ lưu vị trí của quân Tốt đang chờ phong cấp
# Sẽ là None nếu không có Tốt nào đang chờ.
promotion_pending = None
white_board = [
    [None]*8, [None]*8, [None]*8, [None]*8, [None]*8, [None]*8,
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
]
black_board = [
    ["R", "N", "B", "Q", "K", "B", "N", "R"],
    ["P", "P", "P", "P", "P", "P", "P", "P"],
    [None]*8, [None]*8, [None]*8, [None]*8, [None]*8, [None]*8,
]
def switch_turn():
    global current_turn
    current_turn = "black" if current_turn == "white" else "white"

# --- Quản lý quyền nhập thành ---
castling_rights = {
    "white": {"king_side": True, "queen_side": True},
    "black": {"king_side": True, "queen_side": True}
}

# --- Các hàm kiểm tra cơ bản ---

def is_within_bounds(row, col):
    return 0 <= row < 8 and 0 <= col < 8

def get_piece_at(row, col):
    if not is_within_bounds(row, col):
        return None, None
    if white_board[row][col] is not None:
        return white_board[row][col], "white"
    if black_board[row][col] is not None:
        return black_board[row][col], "black"
    return None, None

def get_valid_moves(row, col):
    # (Hàm này đã được SỬA ĐỔI RẤT NHIỀU để kiểm tra chiếu)
    
    piece, color = get_piece_at(row, col)
    if not piece or color != current_turn:
        return []

    # Danh sách này sẽ chứa các nước đi "có thể" (pseudo-legal)
    # Chúng ta sẽ lọc lại chúng ở cuối hàm
    pseudo_moves = []
    directions = []

    if piece == 'P': # Tốt (Pawn)
        direction = -1 if color == 'white' else 1
        start_row = 6 if color == 'white' else 1
        
        # Di chuyển 1 ô
        if is_within_bounds(row + direction, col) and not get_piece_at(row + direction, col)[0]:
            pseudo_moves.append((row + direction, col))
        # Di chuyển 2 ô từ vị trí ban đầu
        if row == start_row and not get_piece_at(row + direction, col)[0] and not get_piece_at(row + 2 * direction, col)[0]:
            pseudo_moves.append((row + 2 * direction, col))
        # Ăn chéo
        for d_col in [-1, 1]:
            if is_within_bounds(row + direction, col + d_col):
                target_piece, target_color = get_piece_at(row + direction, col + d_col)
                if target_piece and target_color != color:
                    pseudo_moves.append((row + direction, col + d_col))
    
    # Các quân cờ khác (Vua, Hậu, Xe, Tượng, Mã)
    elif piece == 'R': # Xe (Rook)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    elif piece == 'B': # Tượng (Bishop)
        directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    elif piece == 'Q': # Hậu (Queen)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    elif piece == 'N': # Mã (Knight)
        for move in [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]:
            new_row, new_col = row + move[0], col + move[1]
            if is_within_bounds(new_row, new_col):
                target_piece, target_color = get_piece_at(new_row, new_col)
                if not target_piece or target_color != color:
                    pseudo_moves.append((new_row, new_col))
    elif piece == 'K': # Vua (King)
        for move in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
            new_row, new_col = row + move[0], col + move[1]
            if is_within_bounds(new_row, new_col):
                target_piece, target_color = get_piece_at(new_row, new_col)
                if not target_piece or target_color != color:
                    pseudo_moves.append((new_row, new_col))
        
        # --- SỬA ĐỔI LOGIC NHẬP THÀNH ---
        attacker_color = 'black' if color == 'white' else 'white'
        # Chỉ được nhập thành NẾU Vua không đang bị chiếu
        if not is_square_attacked(row, col, attacker_color):
            if castling_rights[color]['king_side']:
                # Kiểm tra ô trống VÀ các ô đi qua không bị chiếu
                if (not get_piece_at(row, col + 1)[0] and
                    not get_piece_at(row, col + 2)[0] and
                    not is_square_attacked(row, col + 1, attacker_color) and
                    not is_square_attacked(row, col + 2, attacker_color)):
                    pseudo_moves.append((row, col + 2))
            if castling_rights[color]['queen_side']:
                # Kiểm tra ô trống VÀ các ô đi qua không bị chiếu
                if (not get_piece_at(row, col - 1)[0] and
                    not get_piece_at(row, col - 2)[0] and
                    not get_piece_at(row, col - 3)[0] and
                    not is_square_attacked(row, col - 1, attacker_color) and
                    not is_square_attacked(row, col - 2, attacker_color)):
                    pseudo_moves.append((row, col - 2))

    for d_row, d_col in directions:
        for i in range(1, 8):
            new_row, new_col = row + i * d_row, col + i * d_col
            if not is_within_bounds(new_row, new_col):
                break
            target_piece, target_color = get_piece_at(new_row, new_col)
            if target_piece:
                if target_color != color:
                    pseudo_moves.append((new_row, new_col))
                break
            pseudo_moves.append((new_row, new_col))
    
    # --- PHẦN QUAN TRỌNG NHẤT: Lọc các nước đi hợp lệ ---
    # Lặp qua tất cả các nước đi "có thể" và kiểm tra xem
    # sau khi thực hiện, Vua của mình có bị chiếu không.
    
    legal_moves = []
    start_row, start_col = row, col
    
    for move in pseudo_moves:
        end_row, end_col = move
        
        # --- Bắt đầu mô phỏng nước đi ---
        # 1. Lưu lại trạng thái các ô
        piece_at_start = piece
        board_at_start = white_board if color == 'white' else black_board
        
        piece_at_end, color_at_end = get_piece_at(end_row, end_col)
        board_at_end = None
        if piece_at_end:
            board_at_end = white_board if color_at_end == 'white' else black_board

        # 2. Thực hiện di chuyển mô phỏng
        board_at_start[end_row][end_col] = piece_at_start
        board_at_start[start_row][start_col] = None
        if board_at_end:
            board_at_end[end_row][end_col] = None # Ăn quân
        
        # --- 3. Kiểm tra Vua có bị chiếu sau nước đi này không ---
        if not is_king_in_check(color):
            legal_moves.append(move)
        
        # --- 4. Hoàn tác di chuyển (cực kỳ quan trọng) ---
        board_at_start[start_row][start_col] = piece_at_start
        board_at_start[end_row][end_col] = None # Xóa quân vừa di chuyển
        if board_at_end:
            # Trả lại quân cờ đã bị ăn
            board_at_end[end_row][end_col] = piece_at_end 
    
    return legal_moves


def move_piece(start_pos, end_pos):
    global promotion_pending
    start_row, start_col = start_pos
    end_row, end_col = end_pos

    piece, color = get_piece_at(start_row, start_col)
    if not piece:
        return

    # Xác định đúng bàn cờ để thao tác
    source_board = white_board if color == 'white' else black_board
    target_board_white = white_board
    target_board_black = black_board
    
    # Ăn quân
    if target_board_white[end_row][end_col]: target_board_white[end_row][end_col] = None
    if target_board_black[end_row][end_col]: target_board_black[end_row][end_col] = None

    # Di chuyển
    source_board[end_row][end_col] = piece
    source_board[start_row][start_col] = None
    
    # Cập nhật quyền nhập thành
    if piece == 'K':
        castling_rights[color]['king_side'] = False
        castling_rights[color]['queen_side'] = False
    if piece == 'R':
        if start_col == 0: castling_rights[color]['queen_side'] = False
        if start_col == 7: castling_rights[color]['king_side'] = False
    
    # Xử lý di chuyển Xe khi nhập thành
    if piece == 'K' and abs(start_col - end_col) == 2:
        # Nhập thành
        if end_col > start_col: # Cánh Vua (King side)
            rook_start_col, rook_end_col = 7, 5
        else: # Cánh Hậu (Queen side)
            rook_start_col, rook_end_col = 0, 3
        
        # Lấy quân Xe (phải cùng màu)
        rook, r_color = get_piece_at(start_row, rook_start_col)
        board = white_board if r_color == 'white' else black_board
        
        board[start_row][rook_end_col] = rook
        board[start_row][rook_start_col] = None
    
    # --- TÍNH NĂNG MỚI: Kiểm tra và kích hoạt trạng thái phong cấp ---
    if piece == 'P' and color == 'white' and end_row == 0:
        # Tạm dừng việc đổi lượt, báo cho game.py biết cần hiển thị lựa chọn
        promotion_pending = {'pos': (end_row, end_col), 'color': color}
    elif piece == 'P' and color == 'black' and end_row == 7: # <<< THÊM: Phong cấp cho quân Đen
        promotion_pending = {'pos': (end_row, end_col), 'color': color}
    else:
        # Nếu không phải là trường hợp phong cấp, đổi lượt như bình thường
        switch_turn()

# --- TÍNH NĂNG MỚI: Hàm để thực hiện việc phong cấp ---
def promote_pawn(new_piece):
    """Thay thế quân Tốt bằng quân cờ mới và đổi lượt."""
    global promotion_pending
    if promotion_pending:
        pos = promotion_pending['pos']
        color = promotion_pending['color']
        
        board = white_board if color == 'white' else black_board
        board[pos[0]][pos[1]] = new_piece
        
        # Hoàn thành phong cấp, reset trạng thái và đổi lượt
        promotion_pending = None
        switch_turn()

# ===================================================================
# --- CÁC HÀM KIỂM TRA CHIẾU (CHECK) MỚI ĐƯỢC THÊM VÀO ---
# ===================================================================

def find_king(color):
    """Tìm vị trí (row, col) của Vua màu 'color'."""
    board = white_board if color == 'white' else black_board
    for r in range(8):
        for c in range(8):
            if board[r][c] == 'K':
                return (r, c)
    return None # Không tìm thấy vua (không bao giờ xảy ra nếu bàn cờ hợp lệ)

def is_square_attacked(row, col, attacker_color):
    """
    Kiểm tra xem ô (row, col) có bị tấn công bởi bất kỳ quân nào
    của 'attacker_color' hay không.
    """
    
    # 1. Kiểm tra Tốt (Pawn)
    # Hướng Tốt 'attacker' di chuyển để *ăn* tới ô (row, col)
    direction = 1 if attacker_color == 'white' else -1
    pawn_row = row + direction # Hàng mà Tốt phải đứng
    for d_col in [-1, 1]:
        pawn_col = col + d_col
        if is_within_bounds(pawn_row, pawn_col):
            piece, color = get_piece_at(pawn_row, pawn_col)
            if piece == 'P' and color == attacker_color:
                return True
                
    # 2. Kiểm tra Mã (Knight)
    for move in [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]:
        n_row, n_col = row + move[0], col + move[1]
        if is_within_bounds(n_row, n_col):
            piece, color = get_piece_at(n_row, n_col)
            if piece == 'N' and color == attacker_color:
                return True
                
    # 3. Kiểm tra Vua (King) - để ngăn 2 vua đứng cạnh nhau
    for move in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
        k_row, k_col = row + move[0], col + move[1]
        if is_within_bounds(k_row, k_col):
            piece, color = get_piece_at(k_row, k_col)
            if piece == 'K' and color == attacker_color:
                return True

    # 4. Kiểm tra Xe/Hậu (Rook/Queen) - (ngang/dọc)
    for d_row, d_col in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
        for i in range(1, 8):
            s_row, s_col = row + i * d_row, col + i * d_col
            if not is_within_bounds(s_row, s_col):
                break
            piece, color = get_piece_at(s_row, s_col)
            if piece:
                if color == attacker_color and (piece == 'R' or piece == 'Q'):
                    return True
                break # Bị chặn bởi quân khác (dù là bạn hay thù)
                
    # 5. Kiểm tra Tượng/Hậu (Bishop/Queen) - (chéo)
    for d_row, d_col in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
        for i in range(1, 8):
            s_row, s_col = row + i * d_row, col + i * d_col
            if not is_within_bounds(s_row, s_col):
                break
            piece, color = get_piece_at(s_row, s_col)
            if piece:
                if color == attacker_color and (piece == 'B' or piece == 'Q'):
                    return True
                break # Bị chặn bởi quân khác
                
    return False

def is_king_in_check(color):
    """Kiểm tra xem Vua của màu 'color' có đang bị chiếu hay không."""
    king_pos = find_king(color)
    if not king_pos:
        return False # Không tìm thấy vua
    
    attacker_color = "black" if color == "white" else "white"
    return is_square_attacked(king_pos[0], king_pos[1], attacker_color)