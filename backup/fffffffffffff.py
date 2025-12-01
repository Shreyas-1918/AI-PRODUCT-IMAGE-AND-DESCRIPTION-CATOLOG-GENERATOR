# catalog_neon_enhanced.py
import customtkinter as ctk
from tkinter import messagebox, Toplevel
from PIL import Image, ImageTk, ImageDraw
import threading, requests, io, os, random, math, webbrowser

from gd2 import get_product_descriptions
from flux_image_gen import generate_product_image


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
        if event.widget is self.root:
            if event.width != self.w or event.height != self.h:
                self.w, self.h = event.width, event.height
                # regenerate base and dust for new size
                self.bg_base_img = self.colors["bg_func"](self.w, self.h)
                self._init_dust_particles()
                self._update_background_frame()

    def _animate_base_background(self):
        # slowly regenerate the swirl every few seconds (subtle movement)
        self.bg_base_img = self.colors["bg_func"](self.w, self.h)
        self.root.after(7000, self._animate_base_background)

    def _animate_dust(self):
        # move dust
        for p in self.dust_particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            # wrap around edges
            if p["x"] < -10:
                p["x"] = self.w + 10
            elif p["x"] > self.w + 10:
                p["x"] = -10
            if p["y"] < -10:
                p["y"] = self.h + 10
            elif p["y"] > self.h + 10:
                p["y"] = -10

        self._update_background_frame()
        # ~16 FPS for smooth but not heavy animation
        self.root.after(60, self._animate_dust)

    def _update_background_frame(self):
        """Composite base background + parallax dust and push to all pages."""
        # copy base
        frame = self.bg_base_img.copy().convert("RGBA")
        draw = ImageDraw.Draw(frame, "RGBA")

        # parallax offset from mouse
        cx, cy = self.w / 2, self.h / 2
        strength = 20
        base_off_x = (self.mouse_x - cx) / max(1, self.w) * strength
        base_off_y = (self.mouse_y - cy) / max(1, self.h) * strength

        for p in self.dust_particles:
            # depth-based parallax
            depth = p["depth"]
            px = p["x"] + base_off_x * depth
            py = p["y"] + base_off_y * depth
            r = p["size"]
            alpha = int(90 * depth)
            color = (241, 245, 249, max(40, min(140, alpha)))
            draw.ellipse((px - r, py - r, px + r, py + r), fill=color)

        self.bg_image = ImageTk.PhotoImage(frame)
        for lbl in self.bg_labels:
            lbl.configure(image=self.bg_image)

    # ----- Fullscreen helpers -----
    def set_fullscreen(self, value: bool):
        self.fullscreen = value
        self.root.attributes("-fullscreen", self.fullscreen)

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.fullscreen)

    # ----- Page / background handling -----
    def _make_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bg_label = ctk.CTkLabel(frame, image=self.bg_image, text="")
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        frame.pack_propagate(False)
        self.bg_labels.append(bg_label)
        return frame

    def _refresh_background_theme(self):
        self.bg_base_img = self.colors["bg_func"](self.w, self.h)
        self._init_dust_particles()
        self._update_background_frame()

    # ----- Navigation helpers -----
    def show_home(self):
        self._sw(self.page_home)

    def show_loading(self):
        self._sw(self.page_loading)

    def show_catalog(self):
        self._sw(self.page_catalog)

    def _sw(self, page):
        for p in (self.page_home, self.page_loading, self.page_catalog):
            p.pack_forget()
        page.pack(fill="both", expand=True)

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
        self.gallery_button.pack(pady=(0, 20))

        NeonTooltip(self.home_button, "Generate AI product catalog")
        NeonTooltip(self.gallery_button, "Open your saved neon product gallery")

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
        """Convert raw features from gd2 into a bullet-list string."""
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
                    _, feats = get_product_descriptions(f"{p} variation {i}")
                    features = self._format_features_bullets(feats)
                    urls = generate_product_image(
                        f"{p}, neon-lit premium product render style {i}"
                    )
                    data = requests.get(urls[0]).content if urls else None
                    cards.append((p, i, features, data))
                except Exception as e:
                    print("Error:", e)

        self.root.after(0, lambda: self._generate_complete(cards))

    def _generate_complete(self, cards):
        for w in self.catalog.winfo_children():
            w.destroy()

        for (name, idx, features, data) in cards:
            self.make_card(name, idx, features, data)

        self.progress.stop()
        self.show_catalog()

    # ========= Product Card =========
    def make_card(self, name, idx, features, data):
        c = self.colors

        glow = ctk.CTkFrame(self.catalog, fg_color=c["card_glow"], corner_radius=28)
        glow.pack(fill="x", pady=18, padx=30)

        card = ctk.CTkFrame(glow, fg_color=c["card_bg"], corner_radius=22)
        card.pack(fill="both", expand=True, padx=4, pady=4)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=24, pady=22)

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
                # Pass features into lightbox only for saving metadata (not displayed there)
                lbl.bind(
                    "<Button-1>",
                    lambda e, im=img, n=name, m=idx, feat=features: self.lightbox(
                        im, n, m, feat
                    ),
                )
                return
            except Exception:
                pass

        ctk.CTkLabel(
            right,
            text="No Image",
            font=("Inter", 13, "italic"),
            text_color=c["noimage_text"],
        ).pack()

    # ========= Lightbox Popup (no bullets here) =========
    def lightbox(self, image, name, idx, features):
        top = Toplevel(self.root)
        top.title("🔍 Product Image Viewer")
        top.configure(bg="#020617")

        w, h = image.size
        scale = min(900 / w, 900 / h)
        img = image.resize((int(w * scale), int(h * scale)))
        tk_img = ImageTk.PhotoImage(img)

        lbl = ctk.CTkLabel(top, image=tk_img, text="")
        lbl.image = tk_img
        lbl.pack(padx=20, pady=20)

        def save():
            os.makedirs("generated_images", exist_ok=True)
            safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.lower())
            base = f"{safe}_model{idx}"
            path = os.path.join("generated_images", base + ".png")
            img.save(path)

            # Save bullet-formatted features into sidecar .txt for HTML gallery
            meta_path = os.path.join("generated_images", base + ".txt")
            try:
                with open(meta_path, "w", encoding="utf-8") as f:
                    f.write(features)
            except Exception as e:
                print("Meta save error:", e)

            self.update_gallery_html()
            messagebox.showinfo("Saved", f"Image saved and gallery updated!\n\nFile: {path}")

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

    # ========= HTML Gallery =========
    def update_gallery_html(self):
        gallery_dir = "generated_images"
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
    .card li {
        margin-bottom: 3px;
    }
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

        for f in files:
            img_abs = os.path.abspath(os.path.join(gallery_dir, f)).replace("\\", "/")
            img_url = "file:///" + img_abs
            base_name = os.path.splitext(f)[0]
            meta_path = os.path.join(gallery_dir, base_name + ".txt")

            caption_html = ""
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as mf:
                        txt = mf.read().strip()
                    lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
                    feats = []
                    if lines:
                        # if first line is "Features:" skip it in list
                        if lines[0].lower().startswith("features"):
                            feats = lines[1:] or lines
                        else:
                            feats = lines
                    caption_html += f"<div class='title'>{base_name}</div>"
                    if feats:
                        caption_html += "<ul>"
                        for ln in feats:
                            if ln.startswith("•"):
                                ln = ln[1:].strip()
                            caption_html += f"<li>{ln}</li>"
                        caption_html += "</ul>"
                except Exception as e:
                    print("Meta read error:", e)
                    caption_html = f"<div class='title'>{base_name}</div>"
            else:
                caption_html = f"<div class='title'>{base_name}</div>"

            html += f"""
    <div class="card">
        <img src="{img_url}" alt="{f}" onclick="openLightbox('{img_url}')">
        {caption_html}
    </div>
"""

        html += """
</div>

<div id="lightbox" class="lightbox" onclick="closeLightbox(event)">
    <img id="lightbox-img" src="">
    <div class="lightbox-close-hint">Click outside the image to close</div>
</div>

<script>
function openLightbox(src) {
    var lb = document.getElementById('lightbox');
    var img = document.getElementById('lightbox-img');
    img.src = src;
    lb.style.display = 'flex';
}
function closeLightbox(e) {
    if (e.target.id === 'lightbox') {
        document.getElementById('lightbox').style.display = 'none';
    }
}
</script>

</body>
</html>
"""

        with open(gallery_file, "w", encoding="utf-8") as g:
            g.write(html)


# ========= Run =========
if __name__ == "__main__":
    root = ctk.CTk()
    app = ProductGeneratorApp(root)
    root.mainloop()
