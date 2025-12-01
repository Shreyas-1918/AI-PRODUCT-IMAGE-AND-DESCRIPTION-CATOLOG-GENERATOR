import os
import csv
import random
import requests
import time
from flux_image_gen import generate_product_image

# Configuration
DATASET_DIR = "dataset"
IMAGES_DIR = os.path.join(DATASET_DIR, "images")
MANIFEST_FILE = os.path.join(DATASET_DIR, "manifest.csv")
NUM_SAMPLES_PER_PRODUCT = 1  # Keep low to save credits for now

# List of products to generate
PRODUCTS = [
    "red gaming mouse",
    "blue mechanical keyboard",
    "green vr headset",
    "yellow smart watch",
    "purple drone",
    "orange bluetooth speaker",
    "black noise cancelling headphones",
    "white wireless earbuds",
    "silver laptop stand",
    "gold smartphone case"
]

def setup_directories():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    if not os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "text", "label"]) # label: 1 for match, 0 for mismatch

def download_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(response.content)
            return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return False

def generate_data():
    setup_directories()
    
    existing_images = os.listdir(IMAGES_DIR)
    start_idx = len(existing_images)
    
    new_entries = []

    print(f"Starting generation for {len(PRODUCTS)} products...")

    for i, product in enumerate(PRODUCTS):
        print(f"[{i+1}/{len(PRODUCTS)}] Generating: {product}")
        
        # Generate Image
        try:
            image_urls = generate_product_image(f"product photo of a {product}, high quality, studio lighting")
            if not image_urls:
                print("No image URL returned, skipping.")
                continue
                
            image_url = image_urls[0]
            image_filename = f"img_{start_idx + i}.png"
            image_path = os.path.join(IMAGES_DIR, image_filename)
            
            if download_image(image_url, image_path):
                # Positive Sample (Match)
                new_entries.append([image_path, product, 1])
                
                # Negative Sample (Mismatch) - pick a random other product
                other_products = [p for p in PRODUCTS if p != product]
                if other_products:
                    negative_text = random.choice(other_products)
                    new_entries.append([image_path, negative_text, 0])
                    
                print(f"  Saved {image_filename}")
            else:
                print("  Failed to save image.")
                
        except Exception as e:
            print(f"  Error generating {product}: {e}")
            
        # Sleep briefly to avoid rate limits if any
        time.sleep(1)

    # Append to manifest
    with open(MANIFEST_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(new_entries)
        
    print(f"Generation complete. Added {len(new_entries)} entries to manifest.")

if __name__ == "__main__":
    generate_data()
