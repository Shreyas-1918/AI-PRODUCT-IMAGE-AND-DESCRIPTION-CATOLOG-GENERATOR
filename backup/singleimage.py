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
        self.root.title("AI Product Generator")
        self.root.geometry("900x600")
        self.root.configure(bg="#f8f9fa")

        # Title
        title = tk.Label(root, text="AI Product Generator", font=("Arial", 20, "bold"), bg="#f8f9fa", fg="#333")
        title.pack(pady=10)

        # Input frame
        input_frame = tk.Frame(root, bg="#f8f9fa")
        input_frame.pack(pady=10)

        tk.Label(input_frame, text="Enter Product Name:", font=("Arial", 12), bg="#f8f9fa").pack(side=tk.LEFT, padx=5)
        self.product_entry = tk.Entry(input_frame, font=("Arial", 12), width=40)
        self.product_entry.pack(side=tk.LEFT, padx=5)

        generate_btn = tk.Button(input_frame, text="Generate", command=self.generate_product, 
                                 bg="#007BFF", fg="white", font=("Arial", 12, "bold"))
        generate_btn.pack(side=tk.LEFT, padx=5)

        # Results frame
        self.result_frame = tk.Frame(root, bg="#ffffff", bd=2, relief=tk.RIDGE)
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollable canvas for results
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

    def generate_product(self):
        product_name = self.product_entry.get().strip()
        if not product_name:
            messagebox.showwarning("Input Error", "Please enter a product name.")
            return

        try:
            # Get AI-generated content
            desc_long, desc_features = get_product_descriptions(product_name)
            image_urls = generate_product_image(desc_long)

            # Clear previous results
            for widget in self.scrollable_frame.winfo_children():
                widget.destroy()

            # Display product name
            tk.Label(self.scrollable_frame, text=f"Product: {product_name}", 
                     font=("Arial", 16, "bold"), bg="#ffffff", fg="#333").pack(anchor="w", pady=5)

            # Features
            tk.Label(self.scrollable_frame, text="Features:", 
                     font=("Arial", 14, "bold"), bg="#ffffff", fg="#155724").pack(anchor="w", pady=5)

            # for feature in desc_features:
            tk.Label(self.scrollable_frame, text=f"✅ {desc_features}", 
                        font=("Arial", 12), bg="#e9f7ef", fg="#155724", anchor="w", padx=10).pack(fill="x", pady=2)

            # Images
            tk.Label(self.scrollable_frame, text="Generated Images:", 
                     font=("Arial", 14, "bold"), bg="#ffffff").pack(anchor="w", pady=10)

            for url in image_urls:
                try:
                    response = requests.get(url)
                    img_data = response.content
                    img = Image.open(io.BytesIO(img_data))
                    img.thumbnail((300, 300))
                    photo = ImageTk.PhotoImage(img)

                    img_label = tk.Label(self.scrollable_frame, image=photo, bg="#ffffff")
                    img_label.image = photo  # prevent garbage collection
                    img_label.pack(side="left", padx=10, pady=10)
                except Exception as e:
                    tk.Label(self.scrollable_frame, text=f"[Could not load image: {url}]",
                             font=("Arial", 10), bg="#ffffff", fg="red").pack(anchor="w")

        except Exception as e:
            messagebox.showerror("Error", f"Something went wrong:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = ProductGeneratorGUI(root)
    root.mainloop()
