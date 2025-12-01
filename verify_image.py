import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
import sys
import os
from train_verifier import VerificationClassifier

# Configuration
# Configuration
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_model.pth")
device = "cuda" if torch.cuda.is_available() else "cpu"

def load_models():
    print("Loading models...")
    model_id = "openai/clip-vit-base-patch32"
    processor = CLIPProcessor.from_pretrained(model_id)
    clip_model = CLIPModel.from_pretrained(model_id).to(device)
    clip_model.eval()
    
    classifier = VerificationClassifier().to(device)
    if os.path.exists(MODEL_PATH):
        classifier.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        classifier.eval()
    else:
        print("Warning: Trained model not found. Using random weights.")
        
    return processor, clip_model, classifier

def verify(image_path, product_name):
    processor, clip_model, classifier = load_models()
    
    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        print(f"Error opening image: {e}")
        return False, 0.0

    inputs = processor(text=[product_name], images=image, return_tensors="pt", padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = clip_model(**inputs)
        img_emb = outputs.image_embeds
        text_emb = outputs.text_embeds
        
        score = classifier(img_emb, text_emb).item()
        
    is_match = score > 0.5
    return is_match, score

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_image.py <image_path> <product_name>")
    else:
        img_path = sys.argv[1]
        prod_name = " ".join(sys.argv[2:])
        match, score = verify(img_path, prod_name)
        print(f"Match: {match}")
        print(f"Score: {score:.4f}")
