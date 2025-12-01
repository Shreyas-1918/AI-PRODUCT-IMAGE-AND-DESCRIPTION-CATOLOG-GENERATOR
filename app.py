# catalog_neon_enhanced.py
import customtkinter as ctk
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
import threading, requests, io, os, random, math, webbrowser
import concurrent.futures
import time

from gd2 import get_product_descriptions
from flux_image_gen import generate_product_image

# ========= ASSET GENERATORS =========
# ========= ASSET GENERATORS =========
def generate_premium_bg(width, height):
    """
    Tries to load a cached premium background. 
    If missing, generates one using Flux AI (Replicate) and saves it.
    Falls back to procedural generation if AI fails.
    """
    cache_path = "assets/background.png"
    os.makedirs("assets", exist_ok=True)

    # 1. Try loading cached image
    if os.path.exists(cache_path):
        try:
            print("DEBUG: Loading cached background...")
            img = Image.open(cache_path).convert("RGB")
            return img.resize((width, height), Image.Resampling.LANCZOS)
        except Exception as e:
            print(f"DEBUG: Cache load failed: {e}")

    # 2. Try generating via Flux AI
    print("DEBUG: Generating new premium background via AI...")
    try:
        # A prompt for a stunning, dark, modern UI background
        prompt = "abstract luxury deep purple neon background, violet and magenta gradients, smooth, 8k, high quality, wallpaper, minimalist, cyber aesthetic"
        urls = generate_product_image(prompt)
        if urls:
            data = requests.get(urls[0]).content
            img = Image.open(io.BytesIO(data)).convert("RGB")
            
            # Save to cache
            img.save(cache_path)
            print("DEBUG: Premium background generated and cached.")
            
            return img.resize((width, height), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"DEBUG: AI Background generation failed: {e}")

    # 3. Fallback: Procedural Aurora
    print("DEBUG: Falling back to procedural background.")
    return generate_aurora_bg(width, height)

def generate_aurora_bg(width, height):
    """Generates a deep, rich aurora background (Fallback)."""
    # Base: Deep Void
    img = Image.new("RGB", (width, height), "#020617")
    draw = ImageDraw.Draw(img)

    # 1. Vertical Gradient (Midnight Blue -> Deep Purple)
    for y in range(height):
        t = y / height
        r = int(2 + 10 * t)
        g = int(6 + 5 * t)
        b = int(23 + 20 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 2. Nebulas (Large soft blobs)
    colors = [
        (88, 28, 135),   # Deep Purple
        (12, 74, 110),   # Deep Blue
        (190, 24, 93),   # Pink
    ]
    
    for _ in range(8):
        cx, cy = random.randint(0, width), random.randint(0, height)
        radius = random.randint(300, 800)
        color = random.choice(colors)
        
        # Radial gradient simulation for blob
        overlay = Image.new("RGBA", (width, height), (0,0,0,0))
        odraw = ImageDraw.Draw(overlay)
        
        # Draw a soft ellipse
        left, top, right, bottom = cx-radius, cy-radius, cx+radius, cy+radius
        odraw.ellipse((left, top, right, bottom), fill=(*color, 40))
        
        # Blur it heavily
        overlay = overlay.filter(ImageFilter.GaussianBlur(radius=100))
        img.paste(overlay, (0,0), overlay)

    # 3. Stars (Tiny bright points)
    for _ in range(400):
        x, y = random.randint(0, width), random.randint(0, height)
        opacity = random.randint(100, 255)
        draw.point((x, y), fill=(255, 255, 255, opacity))

    return img

def generate_glass_texture(width, height, opacity=0.85):
    """Generates a frosted glass texture."""
    # Semi-transparent base
    img = Image.new("RGBA", (width, height), (15, 23, 42, int(255 * opacity)))
    return img

# ========= THEME CONFIG =========
THEME = {
    "bg_color": "#020617",
    "accent_primary": "#8b5cf6",   # Violet
    "accent_secondary": "#06b6d4", # Cyan
    "text_main": "#f8fafc",
    "text_dim": "#94a3b8",
    "success": "#10b981",
    "error": "#ef4444",
    "font_header": ("Segoe UI", 32, "bold"),
    "font_sub": ("Segoe UI", 16),
    "font_body": ("Segoe UI", 14),
}

# ========= CUSTOM WIDGETS =========

class GlassFrame(ctk.CTkFrame):
    """A frame that simulates frosted glass."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#0f172a", bg_color="transparent", corner_radius=20, border_width=1, border_color="#1e293b")
        # Note: True blur isn't possible in Tkinter, so we use a semi-transparent dark color
        # that looks good against the dark background.

class GlowingButton(ctk.CTkButton):
    """Button with a neon glow hover effect."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.default_fg = kwargs.get("fg_color", THEME["accent_primary"])
        self.hover_fg = kwargs.get("hover_color", "#7c3aed")
        self.configure(
            fg_color=self.default_fg, 
            hover_color=self.hover_fg, 
            corner_radius=12, 
            height=45,
            font=("Segoe UI", 14, "bold")
        )
        self.bind("<Enter>", self._glow)
        self.bind("<Leave>", self._unglow)

    def _glow(self, _):
        self.configure(border_width=2, border_color="#c4b5fd")

    def _unglow(self, _):
        self.configure(border_width=0)

class StatusStream(ctk.CTkScrollableFrame):
    """Matrix-style scrolling status log."""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="#020617", corner_radius=10, border_width=1, border_color="#1e293b")
        self.lines = []

    def log(self, text, color=THEME["text_main"]):
        lbl = ctk.CTkLabel(self, text=f"> {text}", font=("Consolas", 12), text_color=color, anchor="w")
        lbl.pack(fill="x", pady=2, padx=5)
        self.lines.append(lbl)
        self.after(10, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self._parent_canvas.yview_moveto(1.0)

# ========= MAIN APP =========
class ProductGeneratorApp:
    def __init__(self, root):
        print("DEBUG: App initializing...")
        self.root = root
        self.root.title("NEO-GENESIS | AI Product Catalog")
        
        # Fullscreen Setup
        self.fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")
        self.root.bind("<Escape>", lambda e: self.toggle_fullscreen())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())

        ctk.set_appearance_mode("dark")
        self.w, self.h = root.winfo_screenwidth(), root.winfo_screenheight()
        print(f"DEBUG: Screen size {self.w}x{self.h}")
        
        # Initialize System
        os.makedirs("generated_images", exist_ok=True)
        self.verification_ready = False
        self._load_models_bg()

        # Background System
        print("DEBUG: Generating background...")
        self.bg_img_raw = generate_premium_bg(self.w, self.h)
        self.bg_photo = ImageTk.PhotoImage(self.bg_img_raw)
        print("DEBUG: Background generated.")
        
        # Navigation Stack
        self.pages = {}
        self.current_page = None
        
        print("DEBUG: Initializing UI...")
        self._init_ui()
        print("DEBUG: UI Initialized.")

    def _load_models_bg(self):
        def _load():
            try:
                print("DEBUG: Loading verification models...")
                from verify_image import load_models
                self.v_processor, self.v_clip, self.v_classifier = load_models()
                self.verification_ready = True
                print("System Online: Verification Module Loaded.")
            except Exception as e:
                print(f"System Warning: Verification Module Failed - {e}")
        threading.Thread(target=_load, daemon=True).start()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.root.attributes("-fullscreen", self.fullscreen)

    def _init_ui(self):
        # Base Container (holds background)
        self.container = ctk.CTkFrame(self.root, fg_color="black")
        self.container.pack(fill="both", expand=True)
        
        # Background Label
        self.bg_label = ctk.CTkLabel(self.container, image=self.bg_photo, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Pages
        print("DEBUG: Building pages...")
        self.pages["home"] = self._build_home()
        self.pages["loading"] = self._build_loading()
        self.pages["catalog"] = self._build_catalog()
        print("DEBUG: Pages built.")

        self.show_page("home")

    def show_page(self, name):
        if self.current_page:
            self.current_page.place_forget()
        
        self.current_page = self.pages[name]
        # Fade in effect (simulated)
        self.current_page.place(relx=0.5, rely=0.5, anchor="center", relwidth=1, relheight=1)

    # ========= HOME PAGE =========
    def _build_home(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        
        # Hero Card
        card = GlassFrame(frame, width=900, height=600)
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        # Content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=60, pady=60)
        
        # Header
        ctk.CTkLabel(content, text="NEO-GENESIS", font=("Segoe UI", 48, "bold"), text_color=THEME["text_main"]).pack(pady=(0, 10))
        ctk.CTkLabel(content, text="Architect the future of product design.", font=THEME["font_sub"], text_color=THEME["text_dim"]).pack(pady=(0, 50))
        
        # Input Area
        input_frame = ctk.CTkFrame(content, fg_color="transparent")
        input_frame.pack(fill="x", pady=20)
        
        self.entry = ctk.CTkEntry(
            input_frame, 
            placeholder_text="Describe your vision (e.g. 'Cyberpunk Sneakers, Neon Drone')...",
            height=60,
            font=("Segoe UI", 18),
            fg_color="#1e293b",
            border_color="#334155",
            text_color="white"
        )
        self.entry.pack(fill="x")
        
        # Controls
        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.pack(fill="x", pady=30)
        
        self.verify_var = ctk.BooleanVar(value=True)
        switch = ctk.CTkSwitch(
            controls, 
            text="AI Verification (High Precision)", 
            variable=self.verify_var,
            font=("Segoe UI", 14),
            progress_color=THEME["accent_primary"],
            fg_color="#334155"
        )
        switch.pack(side="left")
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        
        GlowingButton(btn_frame, text="INITIALIZE GENERATION", command=self.start_generation, height=55, font=("Segoe UI", 16, "bold")).pack(fill="x", pady=(0, 15))
        
        ctk.CTkButton(
            btn_frame, 
            text="Access Archives", 
            fg_color="transparent", 
            border_width=1, 
            border_color="#334155", 
            hover_color="#1e293b",
            command=self.open_gallery
        ).pack(fill="x")

        return frame

    # ========= LOADING PAGE =========
    def _build_loading(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        
        card = GlassFrame(frame, width=800, height=600)
        card.place(relx=0.5, rely=0.5, anchor="center")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=50, pady=50)
        
        ctk.CTkLabel(content, text="SYSTEM PROCESSING", font=("Segoe UI", 24, "bold"), text_color=THEME["accent_secondary"]).pack(pady=(0, 20))
        
        self.loader = ctk.CTkProgressBar(content, width=600, height=4, progress_color=THEME["accent_primary"])
        self.loader.pack(pady=20)
        self.loader.configure(mode="indeterminate")
        self.loader.start()
        
        self.status_log = StatusStream(content, height=300)
        self.status_log.pack(fill="x", pady=20)
        
        return frame

    # ========= CATALOG PAGE =========
    def _build_catalog(self):
        frame = ctk.CTkFrame(self.container, fg_color="transparent")
        
        # Header Bar
        header = ctk.CTkFrame(frame, fg_color="#0f172a", height=80, corner_radius=0)
        header.pack(fill="x")
        
        ctk.CTkLabel(header, text="GENERATION RESULTS", font=("Segoe UI", 20, "bold"), text_color="white").pack(side="left", padx=40, pady=20)
        
        ctk.CTkButton(
            header, 
            text="NEW SESSION", 
            fg_color="#334155", 
            hover_color="#475569", 
            command=lambda: self.show_page("home")
        ).pack(side="right", padx=40)
        
        # Scrollable Grid
        self.catalog_scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.catalog_scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Responsive Grid Binding
        self.catalog_scroll.bind("<Configure>", self._on_catalog_resize)
        self.current_results = []
        self.last_cols = 0
        
        return frame

    # ========= LOGIC =========
    def start_generation(self):
        txt = self.entry.get().strip()
        if not txt:
            return messagebox.showerror("Input Error", "Please define a product vision.")
        
        self.products = [p.strip() for p in txt.split(",") if p.strip()]
        self.show_page("loading")
        
        # Reset Log
        for w in self.status_log.winfo_children(): w.destroy()
        self.status_log.lines = []
        
        threading.Thread(target=self._run_generation, daemon=True).start()

    def _run_generation(self):
        results = []
        do_verify = self.verify_var.get()
        
        self.log(f"Initializing generation sequence for {len(self.products)} targets...")
        
        if do_verify and not self.verification_ready:
            self.log("Verification module offline. Bypassing...", THEME["error"])
            do_verify = False

        # Batch 1: Parallel Execution (Variants 1-3)
        self.log("Batch 1: Processing variants 1-3 in parallel...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            for p in self.products:
                for i in range(1, 4):  # Variants 1, 2, 3
                    futures.append(executor.submit(self._process_variant, p, i, do_verify))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    res = future.result()
                    results.append(res)
                except Exception as e:
                    self.log(f"Process Failure (Batch 1): {e}", THEME["error"])

        # Batch 2: Series Execution (Variants 4-5) with Delay
        self.log("Batch 2: Processing variants 4-5 in series (slow mode)...")
        for p in self.products:
            for i in range(4, 6):  # Variants 4, 5
                try:
                    self.log(f"Waiting 2s before processing variant {i}...", THEME["text_dim"])
                    time.sleep(2)  # Artificial delay
                    res = self._process_variant(p, i, do_verify)
                    results.append(res)
                except Exception as e:
                    self.log(f"Process Failure (Batch 2): {e}", THEME["error"])

        self.log("Sequence Complete. Compiling results...")
        self.root.after(800, lambda: self._show_results(results))

    def _process_variant(self, p, i, do_verify):
        self.log(f"[{p}] Analyzing semantic features for variant {i}...")
        
        visual_desc = ""
        features = "Features unavailable (AI Quota Limit)"
        
        try:
            visual_desc, feats = get_product_descriptions(f"{p} variation {i}")
            features = self._format_features(feats)
        except Exception as e:
            self.log(f"[{p}] Description AI busy/quota. Using raw prompt.", THEME["error"])
            visual_desc = "high quality, detailed, 8k, photorealistic"

        self.log(f"[{p}] Rendering visual asset {i}...")
        full_prompt = f"{p}, {visual_desc}"
        urls = generate_product_image(full_prompt)
        data = requests.get(urls[0]).content if urls else None

        is_match = False
        score = 0.0

        if do_verify and data:
            self.log(f"[{p}] Verifying semantic alignment {i}...")
            try:
                temp_path = f"temp_{random.randint(0,99999)}.png"
                with open(temp_path, "wb") as f: f.write(data)
                
                from PIL import Image
                import torch
                img = Image.open(temp_path).convert("RGB")
                inputs = self.v_processor(text=[p], images=img, return_tensors="pt", padding="max_length", max_length=77, truncation=True)
                device = "cuda" if torch.cuda.is_available() else "cpu"
                inputs = {k: v.to(device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.v_clip(**inputs)
                    score = self.v_classifier(outputs.image_embeds, outputs.text_embeds).item()
                    is_match = score > 0.5
                
                os.remove(temp_path)
                status = "MATCH" if is_match else "MISMATCH"
                color = THEME["success"] if is_match else THEME["error"]
                self.log(f"[{p}] Verification Complete: {status} ({score:.2f})", color)
            except Exception as e:
                self.log(f"Verification Error: {e}", THEME["error"])

        return (p, i, features, data, is_match, score, do_verify)

    def log(self, msg, color=THEME["text_main"]):
        self.root.after(0, lambda: self.status_log.log(msg, color))

    def _show_results(self, results):
        self.current_results = sorted(results, key=lambda x: (x[0], x[1]))
        self._regrid_catalog(4) # Default to 4
        self.show_page("catalog")

    def _on_catalog_resize(self, event):
        if not self.current_results: return
        cols = 4 # Force 4 columns
        if cols != self.last_cols:
            self.last_cols = cols
            self._regrid_catalog(cols)

    def _regrid_catalog(self, cols):
        for w in self.catalog_scroll.winfo_children(): w.grid_forget()
        for i in range(cols): self.catalog_scroll.grid_columnconfigure(i, weight=1)
        
        for i, item in enumerate(self.current_results):
            self._make_card(item, i // cols, i % cols)

    def _make_card(self, item, r, c):
        name, idx, features, data, is_match, score, verified = item
        
        # Card Container
        card = GlassFrame(self.catalog_scroll)
        card.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        
        # Image Area
        if data:
            try:
                img = Image.open(io.BytesIO(data)).resize((300, 400))
                tk_img = ImageTk.PhotoImage(img)
                lbl = ctk.CTkLabel(card, image=tk_img, text="")
                lbl.image = tk_img
                lbl.pack(pady=10, padx=10)
                lbl.bind("<Button-1>", lambda e: self.lightbox(img, name, idx, features))
            except:
                ctk.CTkLabel(card, text="[RENDER ERROR]", text_color=THEME["error"]).pack(pady=40)
        else:
            ctk.CTkLabel(card, text="[NO DATA]", text_color=THEME["text_dim"]).pack(pady=40)

        # Info
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(info, text=f"{name.title()} #{idx}", font=("Segoe UI", 16, "bold"), text_color="white").pack(anchor="w")
        
        if verified:
            color = THEME["success"] if is_match else THEME["error"]
            text = f"VERIFIED {int(score*100)}%" if is_match else f"MISMATCH {int(score*100)}%"
            ctk.CTkLabel(info, text=text, font=("Segoe UI", 11, "bold"), text_color=color).pack(anchor="w", pady=2)

        ctk.CTkLabel(info, text=features, font=("Segoe UI", 12), text_color=THEME["text_dim"], justify="left", wraplength=280).pack(anchor="w", pady=(5,0))

    def _format_features(self, feats):
        if isinstance(feats, (list, tuple)):
            return "• " + "\n• ".join([str(x).strip() for x in feats if str(x).strip()])
        return str(feats)

    def open_gallery(self):
        self._rebuild_gallery_html()
        path = os.path.abspath("generated_images/gallery.html")
        if os.path.exists(path): webbrowser.open(f"file:///{path}")
        else: messagebox.showinfo("Info", "Gallery is empty.")

    def _rebuild_gallery_html(self):
        gallery_path = "generated_images/gallery.html"
        images_dir = "generated_images"
        
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
            
            html_content += f'''
        <div class="card">
            <img src="{img_file}" alt="{name}">
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

    def lightbox(self, image, name, idx, features):
        top = Toplevel(self.root)
        top.title("Viewer")
        top.configure(bg="#020617")
        top.state("zoomed")
        
        w, h = image.size
        scale = min(self.w/w, (self.h-100)/h) * 0.8
        img_resized = image.resize((int(w*scale), int(h*scale)))
        tk_img = ImageTk.PhotoImage(img_resized)
        
        lbl = ctk.CTkLabel(top, image=tk_img, text="")
        lbl.image = tk_img
        lbl.pack(expand=True)
        
        def save():
            base = f"{name.replace(' ', '_')}_{idx}"
            save_path = f"generated_images/{base}.png"
            image.save(save_path)
            with open(f"generated_images/{base}.txt", "w") as f: f.write(features)
            
            self._rebuild_gallery_html()
            messagebox.showinfo("Saved", f"Saved to Archive.\n{save_path}")
            
        GlowingButton(top, text="SAVE TO ARCHIVE", command=save, width=200).pack(pady=20)

if __name__ == "__main__":
    root = ctk.CTk()
    app = ProductGeneratorApp(root)
    root.mainloop()
