# catalog_neon_full_with_classifier.py
import customtkinter as ctk
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk, ImageDraw
import threading, requests, io, os, random, math, webbrowser, pickle, sys, traceback

from gd2 import get_product_descriptions
from flux_image_gen import generate_product_image
from verify_image import verify

# ========= BACKGROUND GENERATORS =========
def generate_neon_swirl(width, height):
    """Deep-space neon aurora swirl: purple / cyan / magenta + stars."""
    img = Image.new("RGB", (width, height), (3, 0, 20))
    draw = ImageDraw.Draw(img)

    # Base vertical gradient
    for y in range(height):
        t = y / max(1, height)
        r = int(20 + 40 * t)
        g = int(0 + 25 * t)
        b = int(40 + 80 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    swirl_colors = [
        (168, 85, 247),   # neon purple
        (56, 189, 248),   # electric cyan
        (244, 63, 191),   # magenta
    ]

    # Aurora ribbons
    for color in swirl_colors:
        for _ in range(70):
            cx, cy = random.randint(-200, width + 200), random.randint(0, height)
            strength = random.randint(180, 260)
            for i in range(420):
                angle = i * 0.04
                radius = strength * math.sin(i * 0.012)
                x = int(cx + math.cos(angle) * radius)
                y = int(cy + math.sin(angle) * radius)
                if 0 <= x < width and 0 <= y < height:
                    draw.point((x, y), fill=color)

    # Stars
    for _ in range(420):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        if random.random() < 0.2:
            col = (248, 250, 252)
        else:
            col = random.choice([
                (192, 132, 252),
                (56, 189, 248),
                (244, 114, 182),
            ])
        draw.point((x, y), fill=col)

    return img


def generate_glass_swirl(width, height):
    """Bluish frosted swirl with soft glassy glow."""
    img = Image.new("RGB", (width, height), (4, 6, 26))
    draw = ImageDraw.Draw(img)

    # subtle gradient
    for y in range(height):
        t = y / max(1, height)
        r = int(10 + 10 * t)
        g = int(20 + 30 * t)
        b = int(40 + 70 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    blue_shade = (56, 189, 248)
    for _ in range(80):
        cx, cy = random.randint(-100, width + 100), random.randint(0, height)
        for i in range(380):
            angle = i * 0.11
            radius = 200 * math.sin(i * 0.014)
            x = int(cx + math.cos(angle) * radius)
            y = int(cy + math.sin(angle) * radius)
            if 0 <= x < width and 0 <= y < height:
                draw.point((x, y), fill=blue_shade)

    # sparkle
    for _ in range(260):
        draw.point(
            (random.randint(0, width - 1), random.randint(0, height - 1)),
            fill=(226, 232, 240),
        )

    return img


def generate_gradient_bg(width, height):
    """Premium purple/blue gradient with noise + soft halo."""
    base = Image.new("RGB", (width, height), "#020617")
    draw = ImageDraw.Draw(base)

    for y in range(height):
        t = y / max(1, height)
        r = int(80 + (70 * t))
        g = int(30 + (20 * t))
        b = int(120 + (90 * t))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # halo blobs
    for _ in range(6):
        cx, cy = random.randint(0, width), random.randint(0, height)
        radius = random.randint(160, 260)
        color = random.choice([
            (129, 140, 248),
            (244, 114, 182),
            (45, 212, 191),
        ])
        for r in range(radius, 0, -1):
            col = tuple(int(c * 0.7) for c in color)
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col)

    # light noise stars
    for _ in range(260):
        x, y = random.randint(0, width - 1), random.randint(0, height - 1)
        draw.point((x, y), fill=(248, 250, 252))

    return base


# ========= THEMES =========
THEMES = {
    "Neon": {
        "bg_func": generate_neon_swirl,
        "card_bg": "#12011F",
        "card_glow": "#3b0764",
        "entry_bg": "#1b0730",
        "button_fg": "#7c3aed",
        "button_hover": "#a855f7",
        "header_title": "#e9d5ff",
        "subtext": "#e879f9",
        "card_title": "#f9a8ff",
        "card_text": "#f4e4ff",
        "noimage_text": "#e879f9",
    },
    "Glass": {
        "bg_func": generate_glass_swirl,
        "card_bg": "#020617",
        "card_glow": "#0b1120",
        "entry_bg": "#020617",
        "button_fg": "#2563eb",
        "button_hover": "#1d4ed8",
        "header_title": "#e5e7eb",
        "subtext": "#9ca3af",
        "card_title": "#e5e7eb",
        "card_text": "#d1d5db",
        "noimage_text": "#9ca3af",
    },
    "Gradient": {
        "bg_func": generate_gradient_bg,
        "card_bg": "#1d1040",
        "card_glow": "#312e81",
        "entry_bg": "#1f2937",
        "button_fg": "#4f46e5",
        "button_hover": "#6366f1",
        "header_title": "#e0e7ff",
        "subtext": "#c7d2fe",
        "card_title": "#e0e7ff",
        "card_text": "#e0e7ff",
        "noimage_text": "#c7d2fe",
    },
}


# ========= Tooltip =========
class NeonTooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _=None):
        if self.tip:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
        self.tip = Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.geometry(f"+{x}+{y}")
        self.tip.config(bg="#0b0118")

        ctk.CTkLabel(
            self.tip,
            text=self.text,
            font=("Inter", 12),
            text_color="#e9d5ff",
            fg_color="#3b0764",
        ).pack(ipadx=8, ipady=4)

    def hide(self, _=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


# ========= Hover Glow Button =========
class NeonButton(ctk.CTkButton):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.default_w = kwargs.get("width", 220)
        self.default_h = kwargs.get("height", 48)
        self.default_fg = kwargs.get("fg_color", "#581c87")
        self.hover_fg = kwargs.get("hover_color", "#7e22ce")
        self.bind("<Enter>", self.enlarge)
        self.bind("<Leave>", self.restore)

    def enlarge(self, _):
        self.configure(
            width=int(self.default_w * 1.06),
            height=int(self.default_h * 1.06),
            fg_color=self.hover_fg,
        )

    def restore(self, _):
        self.configure(
            width=self.default_w,
            height=self.default_h,
            fg_color=self.default_fg,
        )


# ========= Main App Class =========
class ProductGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌌 AI Product Catalog – Neo-Cyber Aurora")
        
        # Load verification model once at startup
        try:
            from verify_image import load_models
            self.v_processor, self.v_clip, self.v_classifier = load_models()
            self.verification_ready = True
            print("Verification model loaded.")
        except Exception as e:
            print(f"Verification model load failed: {e}")
            self.verification_ready = False

        # Root full screen + black background to avoid side bars
        self.fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#000000")
        self.root.bind("<Escape>", lambda e: self.set_fullscreen(False))
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())

        ctk.set_appearance_mode("dark")

        self.root.update_idletasks()
        self.w, self.h = root.winfo_screenwidth(), root.winfo_screenheight()

        os.makedirs("generated_images", exist_ok=True)

        # Background / parallax state
        self.theme = "Neon"
        self.colors = THEMES[self.theme]
        self.bg_labels = []
        self.mouse_x = self.w // 2
        self.mouse_y = self.h // 2
        self.dust_particles = []

        # generate base background + image
        self.bg_base_img = self.colors["bg_func"](self.w, self.h)
        self.bg_image = ImageTk.PhotoImage(self.bg_base_img)
        self._init_dust_particles()

        # Pages
        self.page_home = self._make_page()
        self.page_loading = self._make_page()
        self.page_catalog = self._make_page()
        self.page_home.pack(fill="both", expand=True)

        self.build_home()
        self.build_loading()
        self.build_catalog()

        # Animations
        self.root.bind("<Motion>", self._on_mouse_move)
        self.root.bind("<Configure>", self._on_resize)
        self._animate_base_background()
        self._animate_dust()

    # ----- Dust / Parallax helpers -----
    def _init_dust_particles(self):
        self.dust_particles = []
        for _ in range(70):
            self.dust_particles.append({
                "x": random.uniform(0, self.w),
                "y": random.uniform(0, self.h),
                "vx": random.uniform(-0.15, 0.15),
                "vy": random.uniform(-0.05, 0.05),
                "size": random.uniform(1.8, 3.5),
                "depth": random.uniform(0.4, 1.4),
            })

    def _on_mouse_move(self, event):
        self.mouse_x = event.x
        self.mouse_y = event.y

    def _on_resize(self, event):
        # when root resized regenerate background and particles
        if event.widget is self.root:
            if event.width != self.w or event.height != self.h:
                self.w, self.h = event.width, event.height
                self.bg_base_img = self.colors["bg_func"](self.w, self.h)
                self._init_dust_particles()
                self._update_background_frame()

    def _animate_base_background(self):
        # slowly regenerate base background to create subtle motion
        try:
            self.bg_base_img = self.colors["bg_func"](self.w, self.h)
        except Exception:
            pass
        self.root.after(7000, self._animate_base_background)

    def _animate_dust(self):
        for p in self.dust_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            # wrap-around
            if p["x"] < -10:
                p["x"] = self.w + 10
            elif p["x"] > self.w + 10:
                p["x"] = -10
            if p["y"] < -10:
                p["y"] = self.h + 10
            elif p["y"] > self.h + 10:
                p["y"] = -10

        self._update_background_frame()
        # ~16 FPS
        self.root.after(60, self._animate_dust)

    def _update_background_frame(self):
        """Composite base background + parallax dust and push to all pages."""
        try:
            frame = self.bg_base_img.copy().convert("RGBA")
        except Exception:
            # catastrophic failure generating background — skip update
            return

        draw = ImageDraw.Draw(frame, "RGBA")

        # parallax offset from mouse
        cx, cy = self.w / 2, self.h / 2
        strength = 20
        base_off_x = (self.mouse_x - cx) / max(1, self.w) * strength
        base_off_y = (self.mouse_y - cy) / max(1, self.h) * strength

        for p in self.dust_particles:
            depth = p["depth"]
            px = p["x"] + base_off_x * depth
            py = p["y"] + base_off_y * depth
            r = p["size"]
            alpha = int(90 * depth)
            color = (241, 245, 249, max(40, min(140, alpha)))
            draw.ellipse((px - r, py - r, px + r, py + r), fill=color)

        try:
            self.bg_image = ImageTk.PhotoImage(frame)
        except Exception:
            return

        # update all background labels safely
        for lbl in list(self.bg_labels):
            try:
                if getattr(lbl, "winfo_exists", None) and lbl.winfo_exists():
                    lbl.configure(image=self.bg_image)
            except Exception:
                # ignore destroyed widgets
                pass

    # ----- Fullscreen helpers -----
    def set_fullscreen(self, value: bool):
        self.fullscreen = value
        self.root.attributes("-fullscreen", value)

    def toggle_fullscreen(self):
        self.set_fullscreen(not getattr(self, "fullscreen", False))

    # ----- Page / background handling -----
    def _make_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bg_label = ctk.CTkLabel(frame, image=self.bg_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        frame.pack_propagate(False)
        self.bg_labels.append(bg_label)
        return frame

    def _refresh_background_theme(self):
        # regenerate base and re-init dust
        try:
            self.bg_base_img = self.colors["bg_func"](self.w, self.h)
        except Exception:
            pass
        self._init_dust_particles()
        self._update_background_frame()

    # ========= TEXT CLASSIFIER LOADER =========
    def _load_text_classifier(self):
        """Attempt to load text_classifier.pkl which should contain (model, vectorizer)."""
        try:
            path = os.path.join(os.getcwd(), "text_classifier.pkl")
            if os.path.exists(path):
                with open(path, "rb") as f:
                    loaded = pickle.load(f)
                    # expected either (model, vectorizer) or {'model':..., 'vectorizer':...}
                    if isinstance(loaded, tuple) and len(loaded) == 2:
                        self.model, self.vectorizer = loaded
                    elif isinstance(loaded, dict) and "model" in loaded and "vectorizer" in loaded:
                        self.model = loaded["model"]
                        self.vectorizer = loaded["vectorizer"]
                    else:
                        # attempt best-effort unpack
                        try:
                            self.model, self.vectorizer = loaded
                        except Exception:
                            raise ValueError("Unrecognized text_classifier.pkl format")
                self.classifier_ready = True
                print("[Classifier] Loaded text_classifier.pkl")
            else:
                self.classifier_ready = False
                print("[Classifier] text_classifier.pkl not found. Place it in the project folder.")
        except Exception as e:
            self.classifier_ready = False
            print("[Classifier] Load error:", e)
            traceback.print_exc(file=sys.stdout)

    def classify_text(self, text):
        """Return (label, probability) or ('(model missing)', 0.0)"""
        if not getattr(self, "classifier_ready", False) or self.model is None or self.vectorizer is None:
            return ("(model missing)", 0.0)
        try:
            X = self.vectorizer.transform([text])
            probs = self.model.predict_proba(X)[0]
            idx = int(probs.argmax())
            label = str(self.model.classes_[idx])
            return (label, float(probs[idx]))
        except Exception as e:
            print("Classification error:", e)
            return ("(error)", 0.0)

    # ----- Navigation helpers -----
    def _sw(self, page):
        for p in (self.page_home, self.page_loading, self.page_catalog, getattr(self, "page_classifier", None)):
            if p:
                p.pack_forget()
        page.pack(fill="both", expand=True)

    def show_home(self):
        self._sw(self.page_home)

    def show_loading(self):
        self._sw(self.page_loading)

    def show_catalog(self):
        self._sw(self.page_catalog)

    def show_classifier(self):
        if getattr(self, "page_classifier", None):
            self._sw(self.page_classifier)

    # ========= HOME PAGE =========
    def build_home(self):
        c = self.colors
        self.home_card = ctk.CTkFrame(self.page_home, fg_color=c["card_bg"], corner_radius=26)
        self.home_card.place(relx=0.5, rely=0.33, anchor="center")

        # Theme switcher
        self.theme_var = ctk.StringVar(value=self.theme)
        theme_menu = ctk.CTkOptionMenu(
            self.home_card,
            variable=self.theme_var,
            values=list(THEMES.keys()),
            command=self.change_theme,
            width=140,
            fg_color="#020617",
            button_color="#020617",
            button_hover_color="#111827",
            font=("Inter", 12),
        )
        theme_menu.place(relx=0.98, rely=0.08, anchor="ne")

        self.home_title = ctk.CTkLabel(
            self.home_card,
            text="🚀 Neo-Cyber Product Catalog Generator",
            font=("Inter", 36, "bold"),
            text_color=c["header_title"],
        )
        self.home_title.pack(pady=(26, 4))

        self.home_sub = ctk.CTkLabel(
            self.home_card,
            text="Describe your lineup – AI will craft a luminous product gallery.",
            font=("Inter", 15),
            text_color=c["subtext"],
        )
        self.home_sub.pack()

        self.entry = ctk.CTkEntry(
            self.home_card,
            width=740,
            font=("Inter", 18),
            placeholder_text="Example: gaming mouse, VR headset, neon keyboard",
            fg_color=c["entry_bg"],
        )
        self.entry.pack(pady=20, padx=40)

        self.home_button = NeonButton(
            self.home_card,
            text="⚡ Generate Catalog",
            width=350,
            height=64,
            fg_color=c["button_fg"],
            hover_color=c["button_hover"],
            font=("Inter", 19, "bold"),
            command=self.start_generation,
        )
        self.home_button.pack(pady=(18, 16))

        self.gallery_button = NeonButton(
            self.home_card,
            text="📁 Open Saved Gallery",
            width=250,
            height=52,
            fg_color=c["button_fg"],
            hover_color=c["button_hover"],
            font=("Inter", 16, "bold"),
            command=self.open_gallery,
        )
        self.gallery_button.pack(pady=(0, 12))

        self.classifier_button = NeonButton(
            self.home_card,
            text="🤖 Classify Description",
            width=250,
            height=52,
            fg_color=c["button_fg"],
            hover_color=c["button_hover"],
            font=("Inter", 16, "bold"),
            command=self.build_classifier_page,
        )
        self.classifier_button.pack(pady=(0, 12))

        NeonTooltip(self.home_button, "Generate AI product catalog")
        NeonTooltip(self.gallery_button, "Open your saved neon product gallery")
        NeonTooltip(self.classifier_button, "Open the text classifier page")

    # ========= LOADING PAGE =========
    def build_loading(self):
        c = self.colors
        self.loading_card = ctk.CTkFrame(self.page_loading, fg_color=c["card_bg"], corner_radius=26)
        self.loading_card.place(relx=0.5, rely=0.40, anchor="center")

        self.loading_title = ctk.CTkLabel(
            self.loading_card,
            text="⏳ Spinning up your AI catalog...",
            font=("Inter", 30, "bold"),
            text_color=c["header_title"],
        )
        self.loading_title.pack(pady=(26, 6))

        self.loading_sub = ctk.CTkLabel(
            self.loading_card,
            text="Neon engines drafting descriptions and renders...",
            font=("Inter", 15),
            text_color=c["subtext"],
        )
        self.loading_sub.pack()

        self.progress = ctk.CTkProgressBar(
            self.loading_card,
            width=650,
            mode="indeterminate",
            progress_color="#a855f7",
        )
        self.progress.pack(pady=(20, 26))

    # ========= CATALOG PAGE =========
    def build_catalog(self):
        c = self.colors
        self.catalog_header = ctk.CTkFrame(self.page_catalog, fg_color="transparent")
        self.catalog_header.pack(fill="x")

        self.catalog_title = ctk.CTkLabel(
            self.catalog_header,
            text="🌌 Aurora Product Catalog",
            font=("Inter", 30, "bold"),
            text_color=c["header_title"],
        )
        self.catalog_title.pack(side="left", padx=30, pady=12)

        self.catalog_back = NeonButton(
            self.catalog_header,
            text="← Back",
            width=150,
            height=44,
            fg_color=c["button_fg"],
            hover_color=c["button_hover"],
            font=("Inter", 14),
            command=self.show_home,
        )
        self.catalog_back.pack(side="right", padx=30)
        NeonTooltip(self.catalog_back, "Return to home page")

        self.catalog = ctk.CTkScrollableFrame(
            self.page_catalog,
            fg_color="transparent",
            width=self.w - 120,
        )
        self.catalog.pack(padx=30, pady=18, fill="both", expand=True)

    # ========= THEME SWITCH =========
    def change_theme(self, new_theme):
        if new_theme not in THEMES:
            return
        self.theme = new_theme
        self.colors = THEMES[self.theme]
        c = self.colors

        self.home_card.configure(fg_color=c["card_bg"])
        self.home_title.configure(text_color=c["header_title"])
        self.home_sub.configure(text_color=c["subtext"])
        self.entry.configure(fg_color=c["entry_bg"])

        self.home_button.default_fg = c["button_fg"]
        self.home_button.hover_fg = c["button_hover"]
        self.home_button.configure(fg_color=c["button_fg"])

        self.loading_card.configure(fg_color=c["card_bg"])
        self.loading_title.configure(text_color=c["header_title"])
        self.loading_sub.configure(text_color=c["subtext"])

        self.catalog_title.configure(text_color=c["header_title"])
        self.catalog_back.default_fg = c["button_fg"]
        self.catalog_back.hover_fg = c["button_hover"]
        self.catalog_back.configure(fg_color=c["button_fg"])

        # refresh background & dust to match new theme
        self._refresh_background_theme()

    # ========= GALLERY OPEN =========
    def open_gallery(self):
        gallery_dir = "generated_images"
        gallery_file = os.path.join(gallery_dir, "gallery.html")
        if not os.path.exists(gallery_file):
            return messagebox.showinfo("Gallery", "No gallery yet. Save an image first.")
        gallery_path = os.path.abspath(gallery_file).replace("\\", "/")
        webbrowser.open(f"file:///{gallery_path}")

    # ========= Feature formatter =========
    def _format_features_bullets(self, feats):
        if isinstance(feats, (list, tuple)):
            cleaned = []
            for x in feats:
                x = str(x).replace(" ,", ",").replace(", ,", ",").strip(" ,.")
                if x:
                    cleaned.append(x)
            if cleaned:
                return "Features:\n• " + "\n• ".join(cleaned)
            else:
                return "Features: (no details)"
        else:
            f = str(feats).replace(" ,", ",").replace(", ,", ",").strip(" ,.")
            if not f:
                f = "(no details)"
            return "Features:\n• " + f

    # ========= Begin Generation =========
    def start_generation(self):
        txt = self.entry.get().strip()
        if not txt:
            return messagebox.showerror("Error", "Enter at least one product.")
        self.products = [p.strip() for p in txt.split(",") if p.strip()]
        self.show_loading()
        self.progress.start()
        threading.Thread(target=self._generate_worker, daemon=True).start()
    def _generate_worker(self):
        cards = []
        for p in self.products:
            for i in range(1, 6):
                try:
                    # ask GD2 for product features
                    _, feats = get_product_descriptions(f"{p} variation {i}")

                    # format as bullet list
                    features = self._format_features_bullets(feats)

                    # generate product image via Replicate/Flux
                    urls = generate_product_image(
                        f"{p}, neon-lit premium product render style {i}"
                    )
                    data = requests.get(urls[0]).content if urls else None
                    
                    # Verify Image
                    is_match = False
                    score = 0.0
                    if data and getattr(self, "verification_ready", False):
                        try:
                            # Save temp for verification
                            temp_path = "temp_verify.png"
                            with open(temp_path, "wb") as f:
                                f.write(data)
                            
                            # Run verification
                            from PIL import Image
                            import torch
                            
                            img = Image.open(temp_path).convert("RGB")
                            inputs = self.v_processor(text=[p], images=img, return_tensors="pt", padding=True)
                            device = "cuda" if torch.cuda.is_available() else "cpu"
                            inputs = {k: v.to(device) for k, v in inputs.items()}
                            
                            with torch.no_grad():
                                outputs = self.v_clip(**inputs)
                                score = self.v_classifier(outputs.image_embeds, outputs.text_embeds).item()
                                is_match = score > 0.5
                                
                        except Exception as ve:
                            print(f"Verification error: {ve}")

                    cards.append((p, i, features, data, is_match, score))
                except Exception as e:
                    print("Error:", e)

        # update UI safely on main thread
        self.root.after(0, lambda: self._generate_complete(cards))

    def _generate_complete(self, cards):
        # clear old cards
        for w in self.catalog.winfo_children():
            w.destroy()

        # build each product card
        for (name, idx, features, data, is_match, score) in cards:
            self.make_card(name, idx, features, data, is_match, score)

    # ========= PRODUCT CARD =========
    def make_card(self, name, idx, features, data, is_match, score):
        c = self.colors

        # glow border
        glow = ctk.CTkFrame(self.catalog, fg_color=c["card_glow"], corner_radius=28)
        glow.pack(fill="x", pady=18, padx=30)

        # actual card
        card = ctk.CTkFrame(glow, fg_color=c["card_bg"], corner_radius=22)
        card.pack(fill="both", expand=True, padx=4, pady=4)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=24, pady=22)

        # LEFT SIDE (text)
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left,
            text=f"{name.capitalize()} — Model {idx}",
            font=("Inter", 20, "bold"),
            text_color=c["card_title"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text=features,
            wraplength=760,
            font=("Segoe UI", 15),
            text_color=c["card_text"],
            justify="left",
        ).pack(anchor="w", pady=(10, 4))
        
        # Verification Badge
        if data:
            v_color = "#22c55e" if is_match else "#ef4444"
            v_text = f"✅ Verified Match ({score:.2f})" if is_match else f"❌ Potential Mismatch ({score:.2f})"
            ctk.CTkLabel(
                left,
                text=v_text,
                font=("Inter", 14, "bold"),
                text_color=v_color,
            ).pack(anchor="w", pady=(5, 0))

        # classification result label
        if getattr(self, "classifier_ready", False):
            pred_lbl = ctk.CTkLabel(
                left,
                text="Predicting...",
                font=("Inter", 12),
                text_color=c["card_text"],
            )
            pred_lbl.pack(anchor="w", pady=(6, 6))

            # run classifier thread
            def do_pred():
                text_for_pred = features
                label, prob = self.classify_text(text_for_pred)
                pred_lbl.configure(
                    text=f"AI Category: {label} ({prob*100:.1f}%)"
                )

            threading.Thread(target=do_pred, daemon=True).start()

        # RIGHT SIDE (image)
        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right", padx=(12, 0))

        halo = ctk.CTkFrame(right, fg_color="#020617", corner_radius=999)
        halo.pack(padx=4, pady=4)

        if data:
            try:
                img = Image.open(io.BytesIO(data)).resize((260, 260))
                tk_img = ImageTk.PhotoImage(img)

                lbl = ctk.CTkLabel(halo, image=tk_img, text="")
                lbl.image = tk_img
                lbl.pack()

                # click = open lightbox
                lbl.bind(
                    "<Button-1>",
                    lambda e, im=img, n=name, m=idx, feat=features: self.lightbox(
                        im, n, m, feat
                    ),
                )
                return
            except Exception:
                pass

        # fallback
        ctk.CTkLabel(
            right,
            text="No Image",
            font=("Inter", 13, "italic"),
            text_color=c["noimage_text"],
        ).pack()

    # ========= LIGHTBOX POPUP =========
    def lightbox(self, image, name, idx, features):
        top = Toplevel(self.root)
        top.title("🔍 Product Image Viewer")
        top.configure(bg="#020617")

        # resize for popup
        w, h = image.size
        scale = min(900 / w, 900 / h)
        img = image.resize((int(w * scale), int(h * scale)))
        tk_img = ImageTk.PhotoImage(img)

        lbl = ctk.CTkLabel(top, image=tk_img, text="")
        lbl.image = tk_img
        lbl.pack(padx=20, pady=20)

        # classifier in popup
        if getattr(self, "classifier_ready", False):
            pred_lbl = ctk.CTkLabel(
                top,
                text="Analyzing...",
                font=("Inter", 13),
                text_color=self.colors["card_text"],
            )
            pred_lbl.pack(pady=(6, 0))

            def do_pred_lightbox():
                label, prob = self.classify_text(features)
                pred_lbl.configure(
                    text=f"AI Prediction: {label} ({prob*100:.1f}%)"
                )

            threading.Thread(target=do_pred_lightbox, daemon=True).start()

        # SAVE BUTTON
        def save():
            os.makedirs("generated_images", exist_ok=True)

            safe = "".join(
                c if c.isalnum() or c in "-_" else "_" for c in name.lower()
            )
            base = f"{safe}_model{idx}"
            path = os.path.join("generated_images", base + ".png")
            img.save(path)

            # save features for gallery
            meta_path = os.path.join("generated_images", base + ".txt")
            with open(meta_path, "w", encoding="utf-8") as f:
                f.write(features)

            self.update_gallery_html()
            messagebox.showinfo("Saved", "Image saved & gallery updated!")

        NeonButton(
            top,
            text="💾 Save Image",
            width=180,
            height=42,
            fg_color=self.colors["button_fg"],
            hover_color=self.colors["button_hover"],
            font=("Inter", 14),
            command=save,
        ).pack(pady=6)

        NeonButton(
            top,
            text="❌ Close",
            width=150,
            height=38,
            fg_color="#3b0764",
            hover_color="#4c0a7a",
            font=("Inter", 14),
            command=top.destroy,
        ).pack(pady=10)
    # ========= CLASSIFIER PAGE (UI) =========
    def build_classifier_page(self):
        c = self.colors

        if not hasattr(self, "page_classifier") or self.page_classifier is None:
            self.page_classifier = self._make_page()

        # clear old widgets
        for w in self.page_classifier.winfo_children():
            w.destroy()

        card = ctk.CTkFrame(self.page_classifier, fg_color=c["card_bg"], corner_radius=20)
        card.place(relx=0.5, rely=0.24, anchor="center")

        ctk.CTkLabel(
            card,
            text="🤖 Description Classifier",
            font=("Inter", 26, "bold"),
            text_color=c["header_title"],
        ).pack(pady=(18, 8))

        # TEXT INPUT
        self.classifier_text = ctk.CTkTextbox(
            card, width=820, height=180, fg_color=c["entry_bg"]
        )
        self.classifier_text.pack(padx=20, pady=8)

        # RESULT LABEL
        result_frame = ctk.CTkFrame(card, fg_color="transparent")
        result_frame.pack(pady=(6, 12))

        self.classifier_result_lbl = ctk.CTkLabel(
            result_frame,
            text="Model not loaded" if not self.classifier_ready else "",
            font=("Inter", 16, "bold"),
            text_color=c["card_title"],
        )
        self.classifier_result_lbl.pack()

        # BUTTON
        def on_classify():
            text = self.classifier_text.get("0.0", "end").strip()
            if not text:
                return messagebox.showerror("Error", "Enter description to classify.")

            label, prob = self.classify_text(text)
            self.classifier_result_lbl.configure(
                text=f"Prediction: {label} ({prob*100:.1f}%)"
            )

        ctk.CTkButton(card, text="Classify", width=160, command=on_classify).pack(
            pady=(6, 18)
        )

        ctk.CTkButton(self.page_classifier, text="← Back", command=self.show_home).place(
            x=20, y=20
        )

    # ========= UPDATE HTML GALLERY =========
    def update_gallery_html(self):
        gallery_dir = "generated_images"
        os.makedirs(gallery_dir, exist_ok=True)
        gallery_file = os.path.join(gallery_dir, "gallery.html")

        files = [
            f for f in os.listdir(gallery_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        ]

        html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Saved Product Images Gallery</title>
<style>
    body {
        background: radial-gradient(circle at top, #1e1b4b, #020617);
        color: #e5e5ff;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        text-align: center;
        padding: 20px;
        margin: 0;
    }
    h1 {
        color: #c4b5fd;
        margin-bottom: 6px;
    }
    p.subtitle {
        color: #a5b4fc;
        margin-top: 0;
        opacity: 0.9;
    }
    .grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 18px;
        margin-top: 25px;
    }
    .card {
        background: rgba(15,23,42,0.92);
        border-radius: 18px;
        padding: 12px;
        width: 260px;
        box-shadow: 0 18px 40px rgba(15,23,42,0.8);
        border: 1px solid rgba(129,140,248,0.4);
        backdrop-filter: blur(14px);
        text-align: left;
    }
    .card img {
        width: 240px;
        height: auto;
        border-radius: 12px;
        cursor: pointer;
        transition: transform 0.18s ease, box-shadow 0.18s ease;
        display: block;
        margin: 0 auto;
    }
    .card img:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 16px 30px rgba(0,0,0,0.55);
    }
    .card ul {
        margin: 8px 0 0 18px;
        padding: 0;
        color: #c7d2fe;
        font-size: 13px;
    }
    .card li { margin-bottom: 3px; }
    .card .title {
        font-size: 13px;
        color: #e5e7ff;
        margin-top: 8px;
        margin-bottom: 2px;
        font-weight: 600;
    }
    .lightbox {
        display: none;
        position: fixed;
        inset: 0;
        background: rgba(3, 7, 18, 0.92);
        justify-content: center;
        align-items: center;
        z-index: 9999;
    }
    .lightbox img {
        max-width: 90vw;
        max-height: 90vh;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.8);
    }
    .lightbox-close-hint {
        position: fixed;
        bottom: 20px;
        width: 100%;
        text-align: center;
        color: #9ca3af;
        font-size: 13px;
        pointer-events: none;
    }
</style>
</head>
<body>
<h1>🌌 Saved Aurora Product Images</h1>
<p class="subtitle">Click any image to zoom. Click background to close.</p>
<div class="grid">
"""

        # LOOP THROUGH IMAGES
        for f in files:
            img_abs = os.path.abspath(os.path.join(gallery_dir, f)).replace("\\", "/")
            img_url = "file:///" + img_abs
            base = os.path.splitext(f)[0]
            meta_file = os.path.join(gallery_dir, base + ".txt")

            caption_html = f"<div class='title'>{base}</div>"
            if os.path.exists(meta_file):
                try:
                    with open(meta_file, "r", encoding="utf-8") as mf:
                        lines = [ln.strip() for ln in mf.readlines() if ln.strip()]

                    if lines:
                        caption_html += "<ul>"
                        for ln in lines:
                            ln = ln.replace("•", "")
                            caption_html += f"<li>{ln}</li>"
                        caption_html += "</ul>"
                except:
                    pass

            html += f"""
    <div class="card">
        <img src="{img_url}" onclick="openLightbox('{img_url}')">
        {caption_html}
    </div>
"""

        # FOOTER + LIGHTBOX
        html += """
</div>
<div id="lightbox" class="lightbox" onclick="closeLightbox(event)">
    <img id="lightbox-img">
    <div class="lightbox-close-hint">Click outside the image to close</div>
</div>

<script>
function openLightbox(src){
    var lb=document.getElementById('lightbox');
    var img=document.getElementById('lightbox-img');
    img.src=src;
    lb.style.display='flex';
}
function closeLightbox(e){
    if(e.target.id==='lightbox'){ 
        document.getElementById('lightbox').style.display='none';
    }
}
</script>

</body>
</html>
"""

        with open(gallery_file, "w", encoding="utf-8") as g:
            g.write(html)
    # ========= LIGHTBOX VIEWER =========
    def lightbox(self, image, name, idx, features):
        """Popup window for zoomed image + Save button."""
        top = Toplevel(self.root)
        top.title("🔍 Product Image Viewer")
        top.configure(bg="#020617")

        # scale image
        w, h = image.size
        scale = min(900 / w, 900 / h)
        img = image.resize((int(w * scale), int(h * scale)))
        tk_img = ImageTk.PhotoImage(img)

        lbl = ctk.CTkLabel(top, image=tk_img, text="")
        lbl.image = tk_img
        lbl.pack(padx=20, pady=20)

        # SAVE BUTTON
        def save():
            os.makedirs("generated_images", exist_ok=True)

            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
            base = f"{safe}_model{idx}"

            img_path = os.path.join("generated_images", base + ".png")
            img.save(img_path)

            # SAVE METADATA (FEATURES)
            meta_path = os.path.join("generated_images", base + ".txt")
            try:
                with open(meta_path, "w", encoding="utf-8") as f:
                    f.write(features)
            except Exception as e:
                print("Meta write error:", e)

            self.update_gallery_html()
            messagebox.showinfo("Saved", f"Saved!\n\n{img_path}")

        NeonButton(
            top,
            text="💾 Save Image",
            width=180,
            height=42,
            fg_color=self.colors["button_fg"],
            hover_color=self.colors["button_hover"],
            font=("Inter", 14),
            command=save,
        ).pack(pady=6)

        # CLOSE
        NeonButton(
            top,
            text="❌ Close",
            width=150,
            height=38,
            fg_color="#3b0764",
            hover_color="#4c0a7a",
            font=("Inter", 14),
            command=top.destroy,
        ).pack(pady=10)

    # ========= MAIN EXECUTION =========
if __name__ == "__main__":
    root = ctk.CTk()
    app = ProductGeneratorApp(root)
    root.mainloop()
