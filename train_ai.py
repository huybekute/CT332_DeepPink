
print("\n--- Cài đặt Stockfish và python-chess thành công! ---")
# train_ai_colab_v4.py
#
# Đây là code từ lần trước, đã được điều chỉnh để chạy trên Colab.
#
import chess
import chess.pgn
import chess.engine
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os
import random
import math

# ==============================================================================
# --- (CẤU HÌNH CHO COLAB) ---
# ==============================================================================

# 1. ĐÃ TỰ ĐỘNG ĐẶT CHO COLAB (Không cần sửa)
STOCKFISH_PATH = "/usr/games/stockfish"

# 2. (QUAN TRỌNG) Đổi tên này cho khớp với file PGN bạn vừa tải lên
PGN_FILENAME = '/content/project/Cozu/small_120k_games.pgn'

# 3. Tên file model .h5 sẽ được xuất ra
MODEL_FILENAME = 'deeep_pink_model_2D_stockfish.h5'

# 4. Giới hạn số thế cờ (Colab miễn phí có thể chạy 1-2 triệu)
#    (Để chạy thử, bạn có thể đặt 50000)
MAX_POSITIONS_TO_LOAD = 500000

# 5. Thời gian Stockfish phân tích mỗi thế cờ (giây)
ENGINE_TIME_LIMIT = 0.05

# ==============================================================================
# --- INPUT 2D (GIỮ NGUYÊN 100% CỦA BẠN) ---
# ==============================================================================
piece_to_int = {
    'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6,
    'p': -1, 'n': -2, 'b': -3, 'r': -4, 'q': -5, 'k': -6
}

def board_to_array(board):
    board_array = np.zeros(64, dtype=np.int8)
    for i in range(64):
        piece = board.piece_at(i)
        if piece:
            board_array[i] = piece_to_int[piece.symbol()]
    return board_array

# ==============================================================================
# --- MODEL 2D (GIỮ NGUYÊN KIẾN TRÚC CỦA BẠN) ---
# ==============================================================================
def create_model():
    print("\n---> Đang tạo model Dense với input (64,)...")
    ai_model = tf.keras.Sequential([
        layers.Input(shape=(64,)),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(512, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(256, activation='relu'),
        layers.Dropout(0.2),
        layers.Dense(128, activation='relu'),
        layers.Dense(1, activation='tanh')
    ])
    ai_model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.0001),
                     loss='mean_squared_error')
    return ai_model

# ==============================================================================
# --- LABELING BẰNG STOCKFISH ---
# ==============================================================================

def normalize_score(score_cp):
    return math.tanh(score_cp / 300.0)

def train_ai(pgn_path, stockfish_path):
    X_train, y_train = [], []
    positions_loaded = 0
    games_processed = 0

    print(f"\nĐang khởi động Stockfish từ: {stockfish_path}")
    try:
        engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    except Exception as e:
        print(f"LỖI: Không thể khởi động Stockfish: {e}")
        return

    print(f"Bắt đầu đọc dữ liệu từ file PGN: {pgn_path}")
    if not os.path.exists(pgn_path):
        print(f"LỖI: KHÔNG TÌM THẤY FILE PGN '{pgn_path}'.")
        print("Bạn đã tải file PGN lên Colab chưa? Tên file đã khớp 100% chưa?")
        engine.quit()
        return

    limit = chess.engine.Limit(time=ENGINE_TIME_LIMIT)

    with open(pgn_path) as pgn:
        while positions_loaded < MAX_POSITIONS_TO_LOAD:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break

            mainline_moves = list(game.mainline_moves())
            if not mainline_moves:
                continue

            temp_board = game.board()

            sample_indices = random.sample(range(len(mainline_moves)), min(5, len(mainline_moves)))

            for i, move in enumerate(mainline_moves):
                temp_board.push(move)

                if i in sample_indices:
                    try:
                        info = engine.analyse(temp_board, limit)
                        score_cp = info["score"].relative.score(mate_score=10000)
                        if score_cp is None:
                            continue
                        normalized_val = normalize_score(score_cp)
                        X_train.append(board_to_array(temp_board))
                        y_train.append(normalized_val)
                        positions_loaded += 1
                    except Exception as e:
                        pass

            games_processed += 1
            if games_processed % 1000 == 0:
                print(f"Đã xử lý {games_processed} ván cờ, thu thập được {positions_loaded}/{MAX_POSITIONS_TO_LOAD} thế cờ...")

    engine.quit()
    print("Đã đóng Stockfish.")

    if not X_train:
        print("Không tìm thấy dữ liệu huấn luyện.")
        return

    print(f"\nTổng cộng đã thu thập được {len(X_train)} thế cờ CHẤT LƯỢNG CAO.")

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    ai_model = create_model()
    ai_model.summary()

    print("\nBắt đầu quá trình huấn luyện AI (với dữ liệu chuẩn)...")

    ai_model.fit(
        X_train, y_train,
        epochs=15,
        batch_size=1024,
        validation_split=0.1
    )

    ai_model.save(MODEL_FILENAME)
    print("\n=================================================================")
    print(f"--- HOÀN TẤT! ĐÃ LƯU MODEL 2D VÀO {MODEL_FILENAME} ---")
    print(f"File model này đã SẴN SÀNG để bạn tải về.")
    print("=================================================================")

# === PHẦN CHẠY CHÍNH ===
if __name__ == '__main__':
    print(f"Đang sử dụng TensorFlow phiên bản: {tf.__version__}")
    train_ai(PGN_FILENAME, STOCKFISH_PATH)