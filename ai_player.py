# ai_player.py (PHIÊN BẢN TỐI ƯU HÓA VỚI TFLITE)

import numpy as np
# --- THAY ĐỔI: Import TFLite Interpreter ---
try:
    # Thử import bản runtime (nhẹ) trước
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    # Nếu thất bại, import từ bản tensorflow đầy đủ
    print("Không tìm thấy tflite_runtime, đang tải từ tensorflow...")
    from tensorflow.lite.python.interpreter import Interpreter

import game_rules
from game_rules import get_piece_at, move_piece, get_valid_moves

# --- Import thêm các thư viện cần thiết cho MCTS ---
import math
import time
import random
import copy 

# --- THAY ĐỔI: Trỏ đến file TFLITE mới ---
MODEL_FILENAME = 'model.tflite' # <<< ĐÃ THAY ĐỔI
EXPLORATION_CONSTANT = 1.41

# ===================================================================
# CÁC HÀM TIỆN ÍCH QUẢN LÝ TRẠNG THÁI GAME (Giữ nguyên)
# ===================================================================
def coords_to_notation(move):
    """
    Chuyển đổi tọa độ ((r1, c1), (r2, c2)) sang dạng ký hiệu 'a1b2'.
    Hệ tọa độ của chúng ta:
    - Cột (col): 0 -> 'a', 1 -> 'b', ..., 7 -> 'h'
    - Hàng (row): 0 -> '8', 1 -> '7', ..., 7 -> '1'
    """
    (start_row, start_col), (end_row, end_col) = move
    
    # Ánh xạ Cột (File)
    files = "abcdefgh"
    start_file = files[start_col]
    end_file = files[end_col]
    
    # Ánh xạ Hàng (Rank)
    ranks = "87654321" 
    start_rank = ranks[start_row]
    end_rank = ranks[end_row]
    
    return f"{start_file}{start_rank}{end_file}{end_rank}"
def save_state():
    return {
        'white_board': [r[:] for r in game_rules.white_board],
        'black_board': [r[:] for r in game_rules.black_board],
        'current_turn': game_rules.current_turn,
        'castling_rights': copy.deepcopy(game_rules.castling_rights)
    }

def restore_state(state):
    for r in range(8):
        game_rules.white_board[r][:] = state['white_board'][r]
        game_rules.black_board[r][:] = state['black_board'][r]
    
    game_rules.current_turn = state['current_turn']
    game_rules.castling_rights = copy.deepcopy(state['castling_rights'])

def get_all_legal_moves():
    moves = []
    board_to_check = game_rules.white_board if game_rules.current_turn == "white" else game_rules.black_board
    
    for r in range(8):
        for c in range(8):
            if board_to_check[r][c] is not None:
                valid_moves_for_piece = get_valid_moves(r, c)
                for move in valid_moves_for_piece:
                    moves.append(((r, c), move))
    return moves

# ===================================================================
# LỚP MCTS NODE (Giữ nguyên)
# ===================================================================
# (Lớp MCTSNode không thay đổi, tôi rút gọn ở đây cho dễ đọc)
class MCTSNode:
    def __init__(self, move=None, parent=None):
        self.move = move; self.parent = parent; self.children = {}
        self.visits = 0; self.value = 0.0
        self.untried_moves = get_all_legal_moves()
        self.player_turn = game_rules.current_turn 

    def select_child_uct(self):
        best_score = -float('inf'); best_child = None
        log_parent_visits = math.log(self.visits)
        for child in self.children.values():
            if child.visits == 0: return child
            Q = child.value / child.visits
            U = EXPLORATION_CONSTANT * math.sqrt(log_parent_visits / child.visits)
            score = (Q + U) if self.player_turn == 'white' else (-Q + U)
            if score > best_score: best_score = score; best_child = child
        return best_child

    def expand(self):
        move = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
        move_piece(move[0], move[1]); child_node = MCTSNode(move=move, parent=self)
        self.children[move] = child_node; return child_node

    def backpropagate(self, value_from_simulation):
        node = self
        while node is not None:
            node.visits += 1; node.value += value_from_simulation
            node = node.parent
# ===================================================================
# CÁC HÀM AI CHÍNH (THAY ĐỔI ĐỂ DÙNG TFLITE)
# ===================================================================

def load_ai_model():
    """Tải model TFLite và chuẩn bị trình thông dịch."""
    try:
        # Tải TFLite interpreter
        interpreter = Interpreter(model_path=MODEL_FILENAME)
        # Cấp phát bộ nhớ
        interpreter.allocate_tensors()
        
        # Lấy chi tiết input và output
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print(f"Tải mô hình AI (TFLite) từ file '{MODEL_FILENAME}' thành công!")
        
        # Trả về một dict chứa interpreter và chi tiết
        return {
            'interpreter': interpreter,
            'input_details': input_details,
            'output_details': output_details
        }
        
    except Exception as e:
        print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"LỖI: Không thể tải file model TFLite '{MODEL_FILENAME}'.")
        print("Hãy chắc chắn bạn đã chạy script 'convert_to_tflite.py' thành công.")
        print(f"LỖI CHI TIẾT: {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return None

def convert_board_to_input_array():
    """
    Chuyển đổi bàn cờ sang mảng cho AI.
    *** Phải là float32 cho TFLite/ONNX ***
    """
    board_array = np.zeros(64, dtype=np.float32) # <<< Phải là float32
    piece_to_int = {
        'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    }
    for r in range(8):
        for c in range(8):
            idx = r * 8 + c
            piece, color = get_piece_at(r, c)
            if piece:
                value = piece_to_int[piece]
                board_array[idx] = value if color == 'white' else -value
    
    # Reshape để model chấp nhận: (1, 64)
    return np.array([board_array])

# ===================================================================
# HÀM CHÍNH `get_ai_move` (ĐÃ CẬP NHẬT ĐỂ DÙNG TFLITE)
# ===================================================================

def get_ai_move(ai_model, time_limit_sec=0.5):
    """
    Tìm nước đi tốt nhất bằng MCTS + TFLite Interpreter.
    """
    if ai_model is None:
        print("Lỗi: AI model (TFLite) chưa được tải.")
        return None

    # Tách interpreter và chi tiết từ dict
    interpreter = ai_model['interpreter']
    input_details = ai_model['input_details']
    output_details = ai_model['output_details']
    
    # Lấy index (chỉ số) của input và output
    input_index = input_details[0]['index']
    output_index = output_details[0]['index']

    root_state = save_state()
    root = MCTSNode(move=None, parent=None)
    start_time = time.time()
    iterations = 0
    
    while (time.time() - start_time) < time_limit_sec:
        
        restore_state(root_state)
        node = root
        
        # === 1. SELECTION ===
        while not node.untried_moves and node.children:
            node = node.select_child_uct()
            move_piece(node.move[0], node.move[1])
            
        # === 2. EXPANSION ===
        if node.untried_moves:
            node = node.expand()
            
        # === 3. SIMULATION (DÙNG TFLITE SIÊU NHANH) ===
        board_input = convert_board_to_input_array()
        
        # *** THAY ĐỔI CÁCH GỌI PREDICT ***
        # 1. Đặt dữ liệu vào tensor input
        interpreter.set_tensor(input_index, board_input)
        
        # 2. Chạy dự đoán
        interpreter.invoke()
        
        # 3. Lấy kết quả từ tensor output
        value_from_model = interpreter.get_tensor(output_index)[0][0]
        
        # === 4. BACKPROPAGATION ===
        node.backpropagate(value_from_model)
        iterations += 1
        
    print(f"\nAI đã hoàn thành {iterations} vòng MCTS trong {time.time() - start_time:.2f}s.")
    
    # === 4. CHỌN NƯỚC ĐI CUỐI CÙNG ===
    # (Phần này giữ nguyên y hệt phiên bản ONNX)
    restore_state(root_state)
    
    if not root.children:
        print("AI không tìm thấy nước đi nào.")
        return None

    best_move = None
    most_visits = -1
    best_move_avg_value = 0.0
    
    print("\n--- Kết quả phân tích MCTS ---")
    for move, child in root.children.items():
        avg_value = child.value / (child.visits + 1e-6)
        notation = coords_to_notation(move)
        print(f"  - Nước đi {notation} {move}: Thăm {child.visits} lần, Giá trị TB: {avg_value:.3f}")
        
        if child.visits > most_visits:
            most_visits = child.visits
            best_move = move
            best_move_avg_value = avg_value

    print("---------------------------------")
    best_move_notation = coords_to_notation(best_move) if best_move else "None"
    print(f"==> AI chọn: {best_move_notation} (Thăm: {most_visits}, Điểm: {best_move_avg_value:.3f})")
    
    return best_move