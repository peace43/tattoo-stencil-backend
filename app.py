from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import cv2
import numpy as np

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.route("/")
def home():
    return {"message": "Tattoo stencil backend is running"}


@app.route("/health")
def health():
    return {"status": "running"}


@app.route("/outputs/<path:filename>")
def outputs(filename):
    return send_from_directory(OUTPUT_DIR, filename)


def apply_contrast(gray, contrast_value):
    img = gray.astype(np.float32)
    img = img * contrast_value
    img = np.clip(img, 0, 255)
    return img.astype(np.uint8)


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    uid = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_DIR, uid + ".png")
    output_name = uid + "_dark.png"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    file.save(input_path)

    img = cv2.imread(input_path)
    if img is None:
        return jsonify({"error": "Invalid image"}), 400

    mode = request.form.get("mode", "full")
    threshold_value = int(request.form.get("threshold", 140))
    contrast_value = float(request.form.get("contrast", 1.4))
    size_cm = request.form.get("size_cm", "10")
    is_lineart = request.form.get("lineart", "0") == "1"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = apply_contrast(gray, contrast_value)

    # Small quality improvement
    gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    scale_map = {
        "8": 0.85,
        "10": 1.0,
        "12": 1.15,
    }
    scale = scale_map.get(size_cm, 1.0)
    if scale != 1.0:
        gray = cv2.resize(
            gray,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC,
        )

    if is_lineart:
        gray = cv2.bilateralFilter(gray, 9, 75, 75)
    else:
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

    if mode == "outline":
        edges = cv2.Canny(gray, 50, 150)
        stencil = cv2.bitwise_not(edges)

    elif mode == "shading":
        _, stencil = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

    else:  # full
        edges = cv2.Canny(gray, 40, 130)
        _, binary = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        edges_inv = cv2.bitwise_not(edges)
        stencil = cv2.bitwise_and(binary, edges_inv)

    cv2.imwrite(output_path, stencil)

    return jsonify({
        "ok": True,
        "dark": f"/outputs/{output_name}"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
