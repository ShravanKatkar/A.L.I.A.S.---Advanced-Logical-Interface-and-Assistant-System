"""
Friday AI Assistant - Flask API Wrapper
This file implements a lightweight REST API using Flask.
It allows external systems or web interfaces to request image generation,
query metadata history, and serve the generated images statically.
"""

import os
from flask import Flask, request, jsonify, send_from_directory
import image_generator

app = Flask(__name__)

# Ensure output directories are created on startup
image_generator.ensure_directories()


@app.route("/", methods=["GET"])
def index():
    """
    Root endpoint detailing API usage instructions.
    """
    return jsonify({
        "name": "Friday AI - Image Generation API (Flask)",
        "endpoints": {
            "/generate": "Generate a new image. Methods: GET, POST. Params: prompt, width, height, model, seed, raw",
            "/history": "List image generation history. Methods: GET",
            "/images/<filename>": "Serve a generated image file. Methods: GET"
        },
        "examples": [
            f"http://{request.host}/generate?prompt=cyberpunk+cat&model=flux",
            f"http://{request.host}/generate?prompt=startup+logo&width=512&height=512&raw=true"
        ]
    })


@app.route("/images/<filename>", methods=["GET"])
def serve_image(filename):
    """
    Serves a generated image directly from the images folder.
    
    Args:
        filename (str): Name of the image file (e.g. generated_20260608_123456.jpg).
    """
    # Send file from the registered IMAGE_FOLDER
    if not os.path.exists(os.path.join(image_generator.IMAGE_FOLDER, filename)):
        return jsonify({"error": "Image file not found."}), 404
        
    return send_from_directory(image_generator.IMAGE_FOLDER, filename)


@app.route("/history", methods=["GET"])
def get_history():
    """
    Retrieves the historical records of image generation runs.
    """
    history = image_generator.load_history()
    return jsonify({
        "count": len(history),
        "history": history
    })


@app.route("/generate", methods=["GET", "POST"])
def generate():
    """
    Endpoint that handles image generation.
    Supports GET (query arguments) and POST (JSON body) requests.
    
    Query/Body Parameters:
        prompt (str): Text describing the image (Required)
        width (int): Custom width, default 1024
        height (int): Custom height, default 1024
        model (str): 'flux' or 'default', default 'flux'
        seed (int): Custom seed number (Optional)
        raw (bool/str): If 'true', sends the image binary directly rather than JSON
    """
    # Extract data depending on method
    if request.method == "POST":
        # Handle JSON data or fallback to form parameters
        data = request.get_json() or {}
        if not data:
            data = request.form
    else:
        data = request.args

    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Missing required parameter: 'prompt'"}), 400

    # Retrieve and validate parameters
    try:
        width = int(data.get("width", 1024))
        height = int(data.get("height", 1024))
    except ValueError:
        return jsonify({"error": "Width and Height must be valid integers."}), 400

    model = data.get("model", "flux")
    
    # Handle optional seed
    seed = None
    seed_val = data.get("seed")
    if seed_val is not None and str(seed_val).strip() != "":
        try:
            seed = int(seed_val)
        except ValueError:
            return jsonify({"error": "Seed must be an integer."}), 400

    # Execute generation (this downloads the image and saves it)
    saved_path = image_generator.generate_custom_image(
        prompt=prompt,
        width=width,
        height=height,
        seed=seed,
        model=model
    )

    if saved_path and os.path.exists(saved_path):
        filename = os.path.basename(saved_path)
        
        # Check if the user wants the raw image binary returned directly
        raw_requested = str(data.get("raw", "")).lower() in ("true", "1", "yes")
        if raw_requested:
            return send_from_directory(image_generator.IMAGE_FOLDER, filename)
            
        # Otherwise, construct the static URL for the image and return metadata
        host_url = request.host_url
        image_url = f"{host_url}images/{filename}"
        
        return jsonify({
            "status": "success",
            "message": "Image generated successfully.",
            "prompt": prompt,
            "filename": filename,
            "image_url": image_url,
            "local_path": saved_path,
            "width": width,
            "height": height,
            "model": model,
            "seed": seed if seed is not None else "random"
        })
    else:
        return jsonify({
            "status": "failed",
            "error": "Failed to generate or save image. Please verify inputs or API availability."
        }), 500


if __name__ == "__main__":
    print("[+] Starting Friday Image Gen Flask API on port 5000...")
    # Run server on port 5000 (localhost by default)
    app.run(host="127.0.0.1", port=5000, debug=True)
