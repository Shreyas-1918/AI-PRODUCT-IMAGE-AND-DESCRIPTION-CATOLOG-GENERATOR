import os
import csv
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from PIL import Image, ImageDraw, ImageFont
from transformers import CLIPProcessor, CLIPModel
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np


# Configuration
DATASET_DIR = "dataset"
MANIFEST_FILE = os.path.join(DATASET_DIR, "manifest.csv")
MODEL_SAVE_PATH = "verification_model.pth"
BATCH_SIZE = 4
EPOCHS = 15
LEARNING_RATE = 1e-4
TEST_SIZE = 0.2  # 20% for testing

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Load CLIP
print("Loading CLIP model...")
model_id = "openai/clip-vit-base-patch32"
processor = CLIPProcessor.from_pretrained(model_id)
clip_model = CLIPModel.from_pretrained(model_id).to(device)
clip_model.eval()



class VerificationDataset(Dataset):
    def __init__(self, data_list):
        self.data = data_list

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        image_path = item["image_path"]
        text = item["text"]
        label = float(item["label"])
        
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = processor(text=[text], images=image, return_tensors="pt", padding="max_length", max_length=77, truncation=True)
            return inputs, torch.tensor(label, dtype=torch.float32)
        except Exception as e:
            print(f"Error loading {image_path}: {e}")
            return None, None

def load_data(manifest_path):
    data = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def collate_fn(batch):
    batch = [b for b in batch if b[0] is not None]
    if not batch:
        return None, None
        
    inputs_list = [b[0] for b in batch]
    labels = torch.stack([b[1] for b in batch])
    
    pixel_values = torch.cat([i["pixel_values"] for i in inputs_list], dim=0)
    input_ids = torch.cat([i["input_ids"] for i in inputs_list], dim=0)
    attention_mask = torch.cat([i["attention_mask"] for i in inputs_list], dim=0)
    
    return {"pixel_values": pixel_values, "input_ids": input_ids, "attention_mask": attention_mask}, labels

class VerificationClassifier(nn.Module):
    def __init__(self, input_dim=512):
        super(VerificationClassifier, self).__init__()
        # Enhanced Architecture
        self.fc1 = nn.Linear(input_dim * 2, 512)
        self.bn1 = nn.BatchNorm1d(512)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(0.3)
        
        self.fc2 = nn.Linear(512, 256)
        self.bn2 = nn.BatchNorm1d(256)
        
        self.fc3 = nn.Linear(256, 128)
        self.fc4 = nn.Linear(128, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, img_emb, text_emb):
        x = torch.cat((img_emb, text_emb), dim=1)
        
        x = self.fc1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.dropout(x)
        
        x = self.fc2(x)
        x = self.bn2(x)
        x = self.relu(x)
        x = self.dropout(x)
        
        x = self.fc3(x)
        x = self.relu(x)
        
        x = self.fc4(x)
        return self.sigmoid(x)

def save_classification_report_image(report_dict):
    df = pd.DataFrame(report_dict).transpose()
    
    # Create a figure to plot the table
    fig, ax = plt.subplots(figsize=(10, 6)) 
    ax.axis('off')
    
    # Create the table
    table = ax.table(cellText=df.values.round(2), colLabels=df.columns, rowLabels=df.index, loc='center', cellLoc='center')
    
    # Style the table
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)
    
    plt.title("Classification Report", fontsize=16, weight='bold')
    plt.tight_layout()
    plt.savefig("classification_report.png", dpi=300, bbox_inches='tight')
    plt.close()
    print("Classification report image saved as classification_report.png")



def train():

    
    # Load and Split Data
    all_data = load_data(MANIFEST_FILE)
    train_data, test_data = train_test_split(all_data, test_size=TEST_SIZE, random_state=42)
    
    print(f"Total samples: {len(all_data)}")
    print(f"Training samples: {len(train_data)}")
    print(f"Testing samples: {len(test_data)}")

    train_dataset = VerificationDataset(train_data)
    test_dataset = VerificationDataset(test_data)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, collate_fn=collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False, collate_fn=collate_fn)
    
    classifier = VerificationClassifier().to(device)
    optimizer = optim.Adam(classifier.parameters(), lr=LEARNING_RATE)
    criterion = nn.BCELoss()
    
    print("Starting training...")
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    for epoch in range(EPOCHS):
        # Training Phase
        classifier.train()
        total_loss = 0
        all_preds = []
        all_labels = []
        
        for batch_idx, (inputs, labels) in enumerate(train_loader):
            if inputs is None: continue
            
            inputs = {k: v.to(device) for k, v in inputs.items()}
            labels = labels.to(device).unsqueeze(1)
            
            with torch.no_grad():
                outputs = clip_model(**inputs)
                img_emb = outputs.image_embeds
                text_emb = outputs.text_embeds
                
            optimizer.zero_grad()
            preds = classifier(img_emb, text_emb)
            loss = criterion(preds, labels)
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            all_preds.extend((preds > 0.5).cpu().numpy().flatten())
            all_labels.extend(labels.cpu().numpy().flatten())
            

        
        avg_train_loss = total_loss / len(train_loader) if len(train_loader) > 0 else 0
        train_acc = accuracy_score(all_labels, all_preds)
        
        # Validation Phase
        classifier.eval()
        val_loss = 0
        val_preds = []
        val_labels = []
        
        with torch.no_grad():
            for inputs, labels in test_loader:
                if inputs is None: continue
                inputs = {k: v.to(device) for k, v in inputs.items()}
                labels = labels.to(device).unsqueeze(1)
                
                outputs = clip_model(**inputs)
                preds = classifier(outputs.image_embeds, outputs.text_embeds)
                loss = criterion(preds, labels)
                
                val_loss += loss.item()
                val_preds.extend((preds > 0.5).cpu().numpy().flatten())
                val_labels.extend(labels.cpu().numpy().flatten())
        
        avg_val_loss = val_loss / len(test_loader) if len(test_loader) > 0 else 0
        val_acc = accuracy_score(val_labels, val_preds) if val_labels else 0
        
        history['train_loss'].append(avg_train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(avg_val_loss)
        history['val_acc'].append(val_acc)
        
        print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {avg_train_loss:.4f} Acc: {train_acc:.4f} | Val Loss: {avg_val_loss:.4f} Acc: {val_acc:.4f}")

    # Save model
    torch.save(classifier.state_dict(), MODEL_SAVE_PATH)
    print(f"Model saved to {MODEL_SAVE_PATH}")
    
    # Final Evaluation on Test Set
    print("Generating final reports...")
    classifier.eval()
    eval_preds = []
    eval_labels = []
    
    with torch.no_grad():
        for inputs, labels in test_loader:
            if inputs is None: continue
            inputs = {k: v.to(device) for k, v in inputs.items()}
            labels = labels.to(device).unsqueeze(1)
            
            outputs = clip_model(**inputs)
            preds = classifier(outputs.image_embeds, outputs.text_embeds)
            
            eval_preds.extend((preds > 0.5).cpu().numpy().flatten())
            eval_labels.extend(labels.cpu().numpy().flatten())
            
    # Classification Report
    if eval_labels:
        report_dict = classification_report(eval_labels, eval_preds, target_names=["Mismatch", "Match"], output_dict=True)
        report_text = classification_report(eval_labels, eval_preds, target_names=["Mismatch", "Match"])
        
        print("\nClassification Report (Test Set):")
        print(report_text)
        
        with open("classification_report.txt", "w") as f:
            f.write(report_text)
            
        save_classification_report_image(report_dict)
        
        # Confusion Matrix
        cm = confusion_matrix(eval_labels, eval_preds)
        plt.figure(figsize=(6, 5))
        sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=["Mismatch", "Match"], yticklabels=["Mismatch", "Match"])
        plt.title("Confusion Matrix (Test Set)")
        plt.ylabel("True Label")
        plt.xlabel("Predicted Label")
        plt.tight_layout()
        plt.savefig("confusion_matrix.png")
        plt.close()
    else:
        print("Not enough data for classification report.")
    
    # Training vs Testing Graphs
    plt.figure(figsize=(12, 5))
    
    # Loss Plot
    plt.subplot(1, 2, 1)
    plt.plot(range(1, EPOCHS+1), history['train_loss'], marker='o', color='red', label='Training Loss')
    plt.plot(range(1, EPOCHS+1), history['val_loss'], marker='o', color='blue', linestyle='--', label='Testing Loss')
    plt.title("Training vs Testing Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.grid(True)
    plt.legend()
    
    # Accuracy Plot
    plt.subplot(1, 2, 2)
    plt.plot(range(1, EPOCHS+1), history['train_acc'], marker='o', color='green', label='Training Accuracy')
    plt.plot(range(1, EPOCHS+1), history['val_acc'], marker='o', color='orange', linestyle='--', label='Testing Accuracy')
    plt.title("Training vs Testing Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")
    plt.grid(True)
    plt.legend()
    
    plt.savefig("training_loss.png") 
    plt.savefig("accuracy_graph.png")
    plt.close()
    
    print("All reports and graphs generated successfully.")

if __name__ == "__main__":
    train()
