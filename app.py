from flask import Flask, request, jsonify, send_from_directory
import os
import uuid
import cv2

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

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    _, stencil = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)

    cv2.imwrite(output_path, stencil)

    return jsonify({
        "ok": True,
        "dark": f"/outputs/{output_name}"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
