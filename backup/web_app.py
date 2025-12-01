import os
import io
import random
import base64
import threading
from flask import Flask, render_template, request, jsonify
from PIL import Image
import requests

# Import existing logic
from gd2 import get_product_descriptions
from flux_image_gen import generate_product_image

app = Flask(__name__)

# Global model cache
V_PROCESSOR = None
V_CLIP = None
V_CLASSIFIER = None
MODEL_LOCK = threading.Lock()

def load_verification_models():
    global V_PROCESSOR, V_CLIP, V_CLASSIFIER
    with MODEL_LOCK:
        if V_PROCESSOR is None:
            try:
                print("Loading verification models...")
                from verify_image import load_models
                V_PROCESSOR, V_CLIP, V_CLASSIFIER = load_models()
                print("Verification models loaded.")
            except Exception as e:
                print(f"Failed to load verification models: {e}")

# Load models in background on startup
threading.Thread(target=load_verification_models, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    product_name = data.get('product')
    variant_idx = data.get('variant', 1)
    do_verify = data.get('verify', True)

    if not product_name:
        return jsonify({"error": "Product name required"}), 400

    # 1. Get Description
    visual_desc = ""
    features = "Features unavailable (AI Quota Limit)"
    
    try:
        visual_desc, feats = get_product_descriptions(f"{product_name} variation {variant_idx}")
        # Format features
        if isinstance(feats, (list, tuple)):
            features = "• " + "\n• ".join([str(x).strip() for x in feats if str(x).strip()])
        else:
            features = str(feats)
    except Exception:
        print(f"[{product_name}] Description AI busy. Using raw prompt.")
        visual_desc = "high quality, detailed, 8k, photorealistic"

    # 2. Generate Image
    full_prompt = f"{product_name}, {visual_desc}"
    image_url = ""
    image_b64 = ""
    
    try:
        urls = generate_product_image(full_prompt)
        if urls:
            image_url = urls[0]
            # Download and convert to base64 for easier frontend display/saving
            img_data = requests.get(image_url).content
            image_b64 = base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        return jsonify({"error": f"Image generation failed: {str(e)}"}), 500

    # 3. Verify (if requested and image exists)
    is_match = False
    score = 0.0
    verification_status = "skipped"

    if do_verify and image_b64 and V_PROCESSOR:
        try:
            import torch
            img_bytes = base64.b64decode(image_b64)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            
            inputs = V_PROCESSOR(text=[product_name], images=img, return_tensors="pt", padding="max_length", max_length=77, truncation=True)
            device = "cuda" if torch.cuda.is_available() else "cpu"
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = V_CLIP(**inputs)
                score = V_CLASSIFIER(outputs.image_embeds, outputs.text_embeds).item()
                is_match = score > 0.5
                verification_status = "success"
        except Exception as e:
            print(f"Verification failed: {e}")
            verification_status = "error"

    return jsonify({
        "product": product_name,
        "variant": variant_idx,
        "features": features,
        "image_b64": image_b64,
        "verification": {
            "status": verification_status,
            "is_match": is_match,
            "score": score
        }
    })

@app.route('/api/save', methods=['POST'])
def save_image():
    data = request.json
    product_name = data.get('product')
    variant_idx = data.get('variant')
    image_b64 = data.get('image_b64')
    features = data.get('features')

    if not all([product_name, variant_idx, image_b64]):
        return jsonify({"error": "Missing data"}), 400

    try:
        os.makedirs("generated_images", exist_ok=True)
        base_name = f"{product_name.replace(' ', '_')}_{variant_idx}"
        img_path = f"generated_images/{base_name}.png"
        txt_path = f"generated_images/{base_name}.txt"
        
        with open(img_path, "wb") as f:
            f.write(base64.b64decode(image_b64))
        
        with open(txt_path, "w") as f:
            f.write(features)
            
        _rebuild_gallery_html()
        return jsonify({"status": "success", "path": img_path})
    except Exception as e:
        print(f"Failed to save image: {e}")
        return jsonify({"error": str(e)}), 500

def _rebuild_gallery_html():
    gallery_path = "generated_images/gallery.html"
    images_dir = "generated_images"
    
    if not os.path.exists(images_dir):
        return

    # Scan for images
    images = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    images.sort(key=lambda x: os.path.getmtime(os.path.join(images_dir, x)), reverse=True)
    
    html_content = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEO-GENESIS Archive</title>
    <style>
        body { background-color: #020617; color: #f8fafc; font-family: 'Segoe UI', sans-serif; padding: 40px; }
        h1 { text-align: center; margin-bottom: 40px; font-size: 2.5em; color: #8b5cf6; }
        .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 30px; }
        .card { background: #0f172a; border: 1px solid #1e293b; border-radius: 15px; overflow: hidden; transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); border-color: #8b5cf6; }
        img { width: 100%; height: 400px; object-fit: cover; }
        .info { padding: 20px; }
        h3 { margin: 0 0 10px 0; color: #fff; }
        p { color: #94a3b8; font-size: 0.9em; white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>ARCHIVED GENERATIONS</h1>
    <div class="grid" id="grid">
'''
    
    for img_file in images:
        name = os.path.splitext(img_file)[0].replace('_', ' ').title()
        txt_file = os.path.splitext(img_file)[0] + ".txt"
        features = "No features available."
        
        if os.path.exists(os.path.join(images_dir, txt_file)):
            with open(os.path.join(images_dir, txt_file), "r") as f:
                features = f.read()
        
        # Use the /generated_images/ route for src
        html_content += f'''
    <div class="card">
        <img src="/generated_images/{img_file}" alt="{name}">
        <div class="info">
            <h3>{name}</h3>
            <p>{features}</p>
        </div>
    </div>
        '''
        
    html_content += '''
    </div>
</body>
</html>
'''
    with open(gallery_path, "w") as f:
        f.write(html_content)

@app.route('/gallery')
def gallery():
    _rebuild_gallery_html()
    if os.path.exists("generated_images/gallery.html"):
        with open("generated_images/gallery.html", "r") as f:
            return f.read()
    return "Gallery is empty."

@app.route('/generated_images/<path:filename>')
def serve_image(filename):
    from flask import send_from_directory
    return send_from_directory('generated_images', filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
