import tensorflow as tf
import numpy as np

MODEL_H5 = 'deeep_pink_model1.h5'
MODEL_TFLITE = 'model.tflite'

print(f"Đang tải model từ '{MODEL_H5}' (dùng TF {tf.__version__})...")

try:
    # Tải model Keras
    model = tf.keras.models.load_model(MODEL_H5)

    # Tạo đối tượng chuyển đổi
    converter = tf.lite.TFLiteConverter.from_keras_model(model)

    # (Tùy chọn) Tối ưu hóa cho tốc độ
    converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # Thực hiện chuyển đổi
    tflite_model = converter.convert()

    # Lưu file .tflite
    with open(MODEL_TFLITE, 'wb') as f:
        f.write(tflite_model)

    print(f"\nCHUYỂN ĐỔI THÀNH CÔNG!")
    print(f"Đã lưu model TFLite vào file: '{MODEL_TFLITE}'")

except Exception as e:
    print(f"\nLỖI TRONG QUÁ TRÌNH CHUYỂN ĐỔI: {e}")
    print("Hãy chắc chắn bạn đang chạy script này trong môi trường có TF 2.19")