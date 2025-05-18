import os
import uuid
import json
import cv2
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, url_for
from flask_cors import CORS
from inference_sdk import InferenceHTTPClient

app = Flask(__name__)
CORS(app)

# ============================================
# Roboflow Client Initialization
# ============================================
ROBOFLOW_API_KEY = os.getenv("ROBOFLOW_API_KEY")

if not ROBOFLOW_API_KEY:
    print("ПОМИЛКА: Змінна середовища ROBOFLOW_API_KEY не встановлена. Застосунок не може працювати без ключа.")
    raise ValueError("ROBOFLOW_API_KEY environment variable is not set.")

ROBOFLOW_MODEL_ID = "military_objects/1"

if not ROBOFLOW_API_KEY:
    print("ПОПЕРЕДЖЕННЯ: Змінна середовища ROBOFLOW_API_KEY не встановлена. Використовується ключ з коду.")

ROBOFLOW_CLIENT = InferenceHTTPClient(
    api_url="https://detect.roboflow.com",
    api_key=ROBOFLOW_API_KEY
)
print(f"Roboflow Client ініціалізовано для моделі: {ROBOFLOW_MODEL_ID}")


# ============================================
# 1. Roboflow detection
# ============================================

def roboflow_inference(image_path, confidence_threshold=0.5):
    """
    Runs Roboflow inference on the image at `image_path` and returns:
     - annotated_image (cv2 image with detections drawn)
     - list of detected objects
    """
    try:
        print(f"Надсилання запиту до Roboflow для: {image_path} з моделлю {ROBOFLOW_MODEL_ID}")
        result = ROBOFLOW_CLIENT.infer(image_path, model_id=ROBOFLOW_MODEL_ID)
        print("Відповідь від Roboflow отримана.")
    except Exception as e:
        print(f"Помилка під час Roboflow inference: {e}")
        raise

    image_to_annotate = cv2.imread(image_path)
    if image_to_annotate is None:
        raise FileNotFoundError(f"Не вдалося завантажити зображення для анотації: {image_path}")

    annotated_image = image_to_annotate.copy()
    objects = []

    if 'predictions' in result:
        for idx, pred in enumerate(result['predictions']):
            if pred['confidence'] < confidence_threshold:
                continue

            center_x, center_y = pred['x'], pred['y']
            width, height = pred['width'], pred['height']
            label = pred['class']
            conf = pred['confidence']

            x1 = int(center_x - width / 2)
            y1 = int(center_y - height / 2)
            x2 = int(center_x + width / 2)
            y2 = int(center_y + height / 2)

            cv2.rectangle(annotated_image, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                annotated_image,
                f"{label} {conf:.2f}",
                (x1, y1 - 10 if y1 - 10 > 10 else y1 + 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2
            )

            objects.append({
                'id': idx,
                'type': label,
                'confidence': float(conf),
                'coordinates': {'x': x1, 'y': y1, 'width': int(width), 'height': int(height)}  # Зберігаємо x1, y1, w, h
            })
    else:
        print("Відповідь Roboflow не містить ключа 'predictions'")

    return annotated_image, objects


# ============================================
# 2. Flask endpoints
# ============================================

@app.route('/process_image', methods=['POST'])
def process_image_endpoint():
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    uid = uuid.uuid4().hex[:6]

    base_results_dir = "results"
    os.makedirs(base_results_dir, exist_ok=True)
    out_dir_name = f"run_{ts}_{uid}"
    out_dir_path = os.path.join(base_results_dir, out_dir_name)
    os.makedirs(out_dir_path, exist_ok=True)

    original_filename = file.filename
    _, file_extension = os.path.splitext(original_filename)

    saved_path = os.path.join(out_dir_path, f'uploaded_temp{file_extension}')
    try:
        file.save(saved_path)
        print(f"Завантажене зображення тимчасово збережено як: {saved_path}")
    except Exception as e:
         if os.path.exists(out_dir_path):
             os.rmdir(out_dir_path)
         app.logger.error(f"Помилка при збереженні завантаженого файлу: {e}")
         return jsonify({'error': f'Failed to save uploaded file: {e}'}), 500


    try:
        print("Виклик roboflow_inference...")
        rf_annotated_img, rf_info = roboflow_inference(saved_path, confidence_threshold=0.5)
        print("roboflow_inference завершено.")

        annotated_image_filename = 'yolo.jpg'
        json_info_filename = 'object_info.json'

        annotated_image_path = os.path.join(out_dir_path, annotated_image_filename)
        cv2.imwrite(annotated_image_path, rf_annotated_img)
        print(f"Анотоване зображення збережено як: {annotated_image_path}")

        json_info_path = os.path.join(out_dir_path, json_info_filename)
        with open(json_info_path, 'w', encoding='utf-8') as jf:
            json.dump(rf_info, jf, indent=4, ensure_ascii=False)
        print(f"JSON інформація збережена як: {json_info_path}")

        try:
            os.remove(saved_path)
            print(f"Тимчасовий файл видалено: {saved_path}")
        except Exception as e:
            print(f"ПОПЕРЕДЖЕННЯ: Не вдалося видалити тимчасовий файл {saved_path}: {e}")

        relative_annotated_image_path = os.path.join(out_dir_name, annotated_image_filename)
        relative_json_info_path = os.path.join(out_dir_name, json_info_filename)

        return jsonify({
            'message': 'Image processed successfully with Roboflow.',
            'results_folder': out_dir_name,
            'annotated_image_url': url_for('get_result_file', path_to_file=relative_annotated_image_path,
                                           _external=True),
            'object_info_url': url_for('get_result_file', path_to_file=relative_json_info_path, _external=True),
            'object_info': rf_info 
        }), 200

    except FileNotFoundError as e:
        app.logger.error(f"Файл не знайдено: {e}")
        if os.path.exists(out_dir_path):
             print(f"Папка результатів {out_dir_path} залишилась після помилки.")
        if os.path.exists(saved_path):
             os.remove(saved_path)
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        app.logger.error(f"Помилка обробки зображення: {e}")
        if os.path.exists(out_dir_path):
             print(f"Папка результатів {out_dir_path} залишилась після помилки.")
        if os.path.exists(saved_path):
             os.remove(saved_path)

        if "Roboflow" in str(e):
            return jsonify({'error': f'Roboflow processing failed: {str(e)}'}), 502  # Bad Gateway or similar
        return jsonify({'error': f'An error occurred during processing: {str(e)}'}), 500


@app.route('/results/<path:path_to_file>', methods=['GET'])
def get_result_file(path_to_file):
    print(f"Запит файлу: {path_to_file} з директорії {os.path.join(os.getcwd(), 'results')}")
    return send_from_directory(os.path.join(os.getcwd(), "results"), path_to_file,
                               as_attachment=False)


if __name__ == '__main__':
    if not os.path.exists("results"):
        os.makedirs("results")
    app.run(debug=True, host='0.0.0.0', port=5000) 