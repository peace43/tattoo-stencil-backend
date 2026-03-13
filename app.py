from flask import Flask, jsonify, request, send_from_directory
import os
import uuid

app = Flask(__name__)

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.route("/")
def home():
    return "Tattoo Stencil Backend Running"

@app.route("/health")
def health():
    return jsonify({"status": "ok"})

@app.route("/outputs/<filename>")
def output_file(filename):
    return send_from_directory(OUTPUT_DIR, filename)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"ok": False, "message": "Dosya gelmedi"}), 400

    file = request.files["file"]

    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    uid = str(uuid.uuid4())

    upload_path = os.path.join(UPLOAD_DIR, f"{uid}{ext}")
    output_name = f"{uid}_result{ext}"
    output_path = os.path.join(OUTPUT_DIR, output_name)

    file.save(upload_path)

    with open(upload_path, "rb") as src, open(output_path, "wb") as dst:
        dst.write(src.read())

    base_url = request.host_url.rstrip("/")

    return jsonify({
        "ok": True,
        "result": f"{base_url}/outputs/{output_name}"
    })
