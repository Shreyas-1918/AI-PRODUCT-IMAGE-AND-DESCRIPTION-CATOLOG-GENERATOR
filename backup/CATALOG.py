import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import io

from generate_description import get_product_descriptions
from flux_image_gen import generate_product_image

class ProductGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Product Catalog Generator")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f8f9fa")

        # Title
        title = tk.Label(root, text="AI Product Catalog Generator", font=("Arial", 20, "bold"), bg="#f8f9fa", fg="#333")
        title.pack(pady=10)

        # Input frame
        input_frame = tk.Frame(root, bg="#f8f9fa")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Enter Product Name:", font=("Arial", 12), bg="#f8f9fa").pack(side=tk.LEFT, padx=5)
        self.product_entry = tk.Entry(input_frame, font=("Arial", 12), width=40)
        self.product_entry.pack(side=tk.LEFT, padx=5)

        generate_btn = tk.Button(input_frame, text="Generate Catalog", command=self.generate_catalog, 
                                 bg="#007BFF", fg="white", font=("Arial", 12, "bold"))
        generate_btn.pack(side=tk.LEFT, padx=5)

        # Results frame (scrollable)
        self.result_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.RIDGE)
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.result_frame, bg="#ffffff")
        self.scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ffffff")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def generate_catalog(self):
        product_name = self.product_entry.get().strip()
        if not product_name:
            messagebox.showwarning("Input Error", "Please enter a product name.")
            return

        try:
            # Clear old results
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Generate 3 variations
            for i in range(1, 4):
                desc_long, desc_features = get_product_descriptions(f"{product_name} variation {i}")
                image_urls = generate_product_image(f"{product_name}, style {i}")

                # Catalog Card
                card = tk.Frame(self.scrollable_frame, bg="#f8f9fa", bd=2, relief=tk.GROOVE)
                card.pack(fill="x", padx=10, pady=10)

                # Title
                tk.Label(card, text=f"{product_name.capitalize()} - Model {i}", 
                         font=("Arial", 16, "bold"), bg="#f8f9fa").pack(anchor="w", pady=5)

                # # Description
                # tk.Label(card, text=desc_long, wraplength=900, justify="left", 
                #          font=("Arial", 12), bg="#f8f9fa").pack(anchor="w", pady=5)


               # Features
                tk.Label(self.scrollable_frame, text="Features:", 
                     font=("Arial", 14, "bold"), bg="#ffffff", fg="#155724").pack(anchor="w", pady=5)

            # for feature in desc_features:
                tk.Label(self.scrollable_frame, text=f"✅ {desc_features}", 
                        font=("Arial", 12), bg="#e9f7ef", fg="#155724", anchor="w", padx=10).pack(fill="x", pady=2)
                

                # Image (take first one only for catalog)
                if image_urls:
                    try:
                        response = requests.get(image_urls[0])
                        img_data = response.content
                        img = Image.open(io.BytesIO(img_data))
                        img.thumbnail((300, 300))
                        photo = ImageTk.PhotoImage(img)

                        img_label = tk.Label(card, image=photo, bg="#f8f9fa")
                        img_label.image = photo
                        img_label.pack(pady=10)
                    except Exception as e:
                        tk.Label(card, text=f"[Could not load image: {image_urls[0]}]", 
                                 font=("Arial", 10), bg="#f8f9fa", fg="red").pack(anchor="w")

        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductGeneratorGUI(root)
    root.mainloop()