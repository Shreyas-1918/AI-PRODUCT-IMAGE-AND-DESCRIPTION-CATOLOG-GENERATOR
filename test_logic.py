import os
import time
from PIL import Image
from gd2 import get_product_descriptions
from flux_image_gen import generate_product_image
from verify_image import load_models
import torch

def test_background_gen():
    print("\n[1/4] Testing Background Generation...")
    try:
        from app import generate_aurora_bg
        img = generate_aurora_bg(800, 600)
        img.save("test_bg.png")
        print("✅ Background generated and saved to test_bg.png")
    except Exception as e:
        print(f"❌ Background generation failed: {e}")

def test_description_gen():
    print("\n[2/4] Testing Description Generation (GD2)...")
    try:
        product = "Cyberpunk Headphones"
        desc, features = get_product_descriptions(product)
        print(f"✅ Description generated for '{product}'")
        print(f"   Desc length: {len(desc)}")
        print(f"   Features length: {len(features)}")
    except Exception as e:
        print(f"❌ Description generation failed: {e}")

def test_image_gen():
    print("\n[3/4] Testing Image Generation (Flux)...")
    try:
        prompt = "Cyberpunk Headphones, neon lights, futuristic design"
        urls = generate_product_image(prompt)
        if urls:
            print(f"✅ Image URL generated: {urls[0]}")
        else:
            print("❌ No URL returned")
    except Exception as e:
        print(f"❌ Image generation failed: {e}")

def test_verification_model():
    print("\n[4/4] Testing Verification Model Loading...")
    try:
        processor, model, classifier = load_models()
        print("✅ Verification models loaded successfully")
        
        # Dummy verification
        print("   Running dummy verification...")
        img = Image.new("RGB", (224, 224), color="red")
        text = "A red image"
        
        inputs = processor(text=[text], images=img, return_tensors="pt", padding="max_length", max_length=77, truncation=True)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            score = classifier(outputs.image_embeds, outputs.text_embeds).item()
        
        print(f"✅ Dummy verification score: {score:.4f}")
        
    except Exception as e:
        print(f"❌ Verification model failed: {e}")

if __name__ == "__main__":
    print("=== STARTING BACKEND LOGIC TESTS ===")
    test_background_gen()
    test_description_gen()
    test_image_gen()
    test_verification_model()
    print("\n=== TESTS COMPLETE ===")
