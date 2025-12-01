import customtkinter as ctk
from tkinter import messagebox, Toplevel
import tkinter as tk
from PIL import Image, ImageDraw
import threading, requests, io, os, random, math, webbrowser

from gd2 import get_product_descriptions
from flux_image_gen import generate_product_image


# ========= Aurora Gradient + Swirl Background =========
def generate_aurora_bg(width, height):
    """Luxury purple/blue aurora-style background."""
    img = Image.new("RGB", (width, height), "#050816")
    draw = ImageDraw.Draw(img)

    # Vertical gradient base (deep purple -> navy)
    for y in range(height):
        t = y / height
        r = int(30 + 50 * t)
        g = int(6 + 40 * t)
        b = int(60 + 100 * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Soft aurora ribbon bands
    bands = [
        ((140, 92, 255), 0.25, 220),
        ((236, 72, 153), 0.55, 260),
        ((56, 189, 248), 0.8, 200),
    ]
    for color, center_y_ratio, strength in bands:
        cy = int(height * center_y_ratio)
        for _ in range(70):
            cx = random.randint(-200, width + 200)
            for i in range(360):
                angle = i * 0.05
                radius = strength * math.sin(i * 0.01)
                x = int(cx + math.cos(angle) * radius)
                y = int(cy + math.sin(angle) * radius)
                if 0 <= x < width and 0 <= y < height:
                    draw.point((x, y), fill=color)

    # star sparkles
    for _ in range(350):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        col = (248, 250, 252) if random.random() < 0.3 else (168, 85, 247)
        draw.point((x, y), fill=col)

    return img


# ========= Liquid Hover Button =========
class LiquidButton(ctk.CTkButton):
    """Button with soft pulsing 'liquid' hover effect."""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.base_w = kwargs.get("width", 220)
        self.base_h = kwargs.get("height", 48)
        self.base_color = kwargs.get("fg_color", "#7c3aed")
        self.hover_color = kwargs.get("hover_color", "#a855f7")
        self._hovering = False
        self._animating = False
        self._pulse_step = 0

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _=None):
        self._hovering = True
        if not self._animating:
            self._animating = True
            self._animate()

    def _on_leave(self, _=None):
        self._hovering = False

    def _animate(self):
        if not self._hovering:
            self.configure(width=self.base_w, height=self.base_h, fg_color=self.base_color)
            self._animating = False
            return

        phase = math.sin(self._pulse_step / 4)
        scale = 1 + 0.04 * phase
        self.configure(
            width=int(self.base_w * scale),
            height=int(self.base_h * (1 + 0.02 * phase)),
            fg_color=self.hover_color if phase > 0 else self.base_color,
        )
        self._pulse_step += 1
        self.after(40, self._animate)


# ========= Main App =========
class ProductGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🟣 AI Product Catalog – Aurora Edition")

        ctk.set_appearance_mode("dark")

        # Fullscreen + ESC and F11
        self.fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.bind("<Escape>", lambda e: self.set_fullscreen(False))
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())

        self.root.update_idletasks()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Larger background for parallax
        self.w, self.h = screen_w, screen_h
        self.bg_w, self.bg_h = screen_w + 80, screen_h + 80

        # Background image as CTkImage
        pil_bg = generate_aurora_bg(self.bg_w, self.bg_h)
        self.bg_image = ctk.CTkImage(light_image=pil_bg, size=(self.bg_w, self.bg_h))
        self.bg_labels = []

        os.makedirs("generated_images", exist_ok=True)
        self.image_refs = []

        # Pages
        self.page_home = self.make_page()
        self.page_loading = self.make_page()
        self.page_catalog = self.make_page()
        self.page_home.pack(fill="both", expand=True)

        # Build Screens
        self.build_home()
        self.build_loading()
        self.build_catalog()

        # Parallax movement
        self.root.bind("<Motion>", self.on_mouse_move)

        # Orb animation
        self.orb_phase = 0
        self.animate_orb()

    # ----- Fullscreen -----
    def set_fullscreen(self, v: bool):
        self.fullscreen = v
        self.root.attributes("-fullscreen", v)

    def toggle_fullscreen(self):
        self.set_fullscreen(not self.fullscreen)

    # ----- UI Pages with background -----
    def make_page(self):
        frame = ctk.CTkFrame(self.root, fg_color="transparent")
        bg_lbl = ctk.CTkLabel(
            frame,
            image=self.bg_image,
            text="",
            width=self.bg_w,
            height=self.bg_h
        )
        bg_lbl.place(x=-40, y=-40)
        self.bg_labels.append(bg_lbl)
        return frame

    def on_mouse_move(self, event):
        if not self.bg_labels:
            return
        rel_x = (event.x / max(1, self.w)) - 0.5
        rel_y = (event.y / max(1, self.h)) - 0.5
        shift = 18
        x = int(-40 - rel_x * shift)
        y = int(-40 - rel_y * shift)
        for lbl in self.bg_labels:
            lbl.place_configure(x=x, y=y)

    # ---------- HOME ----------
    def build_home(self):
        self.home_card = ctk.CTkFrame(self.page_home, fg_color="#14002b", corner_radius=26)
        self.home_card.place(relx=0.5, rely=0.28, anchor="center")

        ctk.CTkLabel(
            self.home_card,
            text="🚀 AI Product Catalog Generator",
            font=("Inter", 38, "bold"),
            text_color="#f5f3ff",
        ).pack(pady=(26, 8), padx=50)

        ctk.CTkLabel(
            self.home_card,
            text="Enter product names (comma separated)",
            font=("Inter", 15),
            text_color="#e0b3ff",
        ).pack()

        self.entry = ctk.CTkEntry(
            self.home_card,
            width=760,
            font=("Inter", 18),
            placeholder_text="Example: gaming mouse, VR headset, aurora keyboard",
            fg_color="#31004d",
        )
        self.entry.pack(pady=22, padx=50)

        LiquidButton(
            self.home_card,
            text="✨ Generate Catalog",
            width=340,
            height=60,
            fg_color="#7c3aed",
            hover_color="#a855f7",
            font=("Inter", 19, "bold"),
            command=self.start_generation,
        ).pack(pady=(10, 26))

    # ---------- LOADING ----------
    def build_loading(self):
        self.loading_card = ctk.CTkFrame(self.page_loading, fg_color="#14002b", corner_radius=26)
        self.loading_card.place(relx=0.5, rely=0.22, anchor="n")

        ctk.CTkLabel(
            self.loading_card,
            text="⏳ Generating your catalog...",
            font=("Inter", 30, "bold"),
            text_color="#f5f3ff",
        ).pack(pady=(20, 6), padx=40)

        ctk.CTkLabel(
            self.loading_card,
            text="Our AI is crafting descriptions and aurora-lit product renders.",
            font=("Inter", 15),
            text_color="#e0b3ff",
        ).pack()

        self.orb_canvas = tk.Canvas(
            self.loading_card, width=110, height=110,
            bg="#14002b", highlightthickness=0
        )
        self.orb_canvas.pack(pady=(10, 8))

        self.progress = ctk.CTkProgressBar(
            self.loading_card, width=650, mode="indeterminate",
            progress_color="#a855f7"
        )
        self.progress.pack(pady=(10, 24))

    # ---------- CATALOG ----------
    def build_catalog(self):
        header = ctk.CTkFrame(self.page_catalog, fg_color="transparent")
        header.pack(fill="x")

        ctk.CTkLabel(
            header, text="🟣 Aurora Product Catalog",
            font=("Inter", 30, "bold"), text_color="#f5f3ff"
        ).pack(side="left", padx=30, pady=10)

        LiquidButton(
            header, text="← Back", width=150, height=44,
            fg_color="#312e81", hover_color="#4338ca",
            font=("Inter", 14), command=self.show_home
        ).pack(side="right", padx=30, pady=8)

        self.catalog = ctk.CTkScrollableFrame(
            self.page_catalog, fg_color="transparent",
            width=self.w - 100
        )
        self.catalog.pack(padx=30, pady=18, fill="both", expand=True)

    # -------- Navigation --------
    def show_home(self): self._sw(self.page_home)
    def show_loading(self): self._sw(self.page_loading)
    def show_catalog(self): self._sw(self.page_catalog)

    def _sw(self, page):
        for p in (self.page_home, self.page_loading, self.page_catalog):
            p.pack_forget()
        page.pack(fill="both", expand=True)

    # -------- Start Generation --------
    def start_generation(self):
        text = self.entry.get().strip()
        if not text:
            return messagebox.showerror("Error", "Enter at least one product name.")
        self.products = [p.strip() for p in text.split(",") if p.strip()]

        self.show_loading()
        self.progress.start()
        threading.Thread(target=self.generate_catalog, daemon=True).start()

    # ---------- Orb animation (FIXED VERSION) ----------
    def animate_orb(self):
        if not hasattr(self, "orb_canvas"):
            self.root.after(80, self.animate_orb)
            return

        self.orb_canvas.delete("all")
        cx, cy = 55, 55
        phase = self.orb_phase
        pulse = 5 * math.sin(phase / 6)
        r = 22 + pulse

        # glow aura
        self.orb_canvas.create_oval(cx-r-10, cy-r-10, cx+r+10, cy+r+10,
                                   outline="#22d3ee", width=2)
        self.orb_canvas.create_oval(cx-r-4, cy-r-4, cx+r+4, cy+r+4,
                                   outline="#a855f7", width=3)
        self.orb_canvas.create_oval(cx-r, cy-r, cx+r, cy+r,
                                   fill="#f472b6", outline="")

        self.orb_phase += 1
        self.root.after(80, self.animate_orb)

    # -------- Catalog generator --------
    def generate_catalog(self):
        for w in self.catalog.winfo_children():
            w.destroy()
        self.image_refs.clear()

        for product in self.products:
            for i in range(1, 6):
                try:
                    _, feats = get_product_descriptions(f"{product} variation {i}")
                    feats = "Features: " + ", ".join(feats) + "."
                    urls = generate_product_image(
                        f"{product}, aurora lighting, premium product, style {i}"
                    )
                    data = requests.get(urls[0], timeout=20).content if urls else None
                    self.make_card(product, i, feats, data)
                except Exception as e:
                    print("Error:", e)

        self.progress.stop()
        self.root.after(350, self.show_catalog)

    # -------- Product Card --------
    def make_card(self, name, idx, features, data):
        glow = ctk.CTkFrame(self.catalog, fg_color="#1e1035", corner_radius=26)
        glow.pack(fill="x", pady=14, padx=26)

        card = ctk.CTkFrame(glow, fg_color="#150022", corner_radius=22)
        card.pack(fill="both", expand=True, padx=3, pady=3)

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=22, pady=20)

        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(
            left, text=f"{name.capitalize()} — Model {idx}",
            font=("Inter", 20, "bold"), text_color="#f9fafb"
        ).pack(anchor="w")

        ctk.CTkLabel(
            left, text=features, wraplength=700,
            font=("Inter", 15), text_color="#e5e7eb"
        ).pack(anchor="w", pady=(6, 2))

        right = ctk.CTkFrame(row, fg_color="transparent")
        right.pack(side="right")

        if data:
            try:
                img = Image.open(io.BytesIO(data)).resize((260, 260))
                tk_img = ctk.CTkImage(light_image=img, size=(260, 260))
                self.image_refs.append(tk_img)
                lbl = ctk.CTkLabel(right, image=tk_img, text="")
                lbl.pack()
                lbl.bind(
                    "<Button-1>",
                    lambda e, im=img, n=name, m=idx: self.lightbox(im, n, m)
                )
                return
            except Exception:
                pass

        ctk.CTkLabel(
            right, text="No Image",
            font=("Inter", 13, "italic"), text_color="#e0b3ff"
        ).pack()

    # -------- Lightbox --------
    def lightbox(self, image, name, idx):
        top = Toplevel(self.root)
        top.title("🔍 Product Image")
        top.configure(bg="#020617")

        w, h = image.size
        scale = min(900 / w, 900 / h)
        img = image.resize((int(w * scale), int(h * scale)))
        tk_img = ctk.CTkImage(light_image=img, size=(int(w * scale), int(h * scale)))

        lbl = ctk.CTkLabel(top, image=tk_img, text="")
        lbl.image = tk_img
        lbl.pack(padx=20, pady=20)

        def save():
            fp = f"generated_images/{name}_model{idx}.png"
            img.save(fp)

            gallery_file = "generated_images/gallery.html"
            files = [f for f in os.listdir("generated_images")
                     if f.lower().endswith((".png", ".jpg", ".jpeg"))]

            html = """
            <html>
            <head>
                <title>Saved Product Images Gallery</title>
                <style>
                    body {
                        background: #0a0018;
                        color: #e5e5ff;
                        font-family: Arial, sans-serif;
                        text-align: center;
                        padding: 20px;
                    }
                    h1 { color: #b388ff; }
                    .grid {
                        display: flex;
                        flex-wrap: wrap;
                        justify-content: center;
                        gap: 18px;
                        margin-top: 25px;
                    }
                    .card {
                        background: #1b0030;
                        border-radius: 14px;
                        padding: 12px;
                        width: 260px;
                    }
                    img {
                        width: 240px;
                        height: auto;
                        border-radius: 10px;
                    }
                    p { font-size: 14px; color: #cbaaff; }
                </style>
            </head>
            <body>
                <h1>🟣 Saved Aurora Product Images</h1>
                <div class="grid">
            """

            for f in files:
                html += f"""
                  <div class='card'>
                    <img src='{f}'/>
                    <p>{f}</p>
                  </div>
                """

            html += """
                </div>
            </body>
            </html>
            """

            with open(gallery_file, "w", encoding="utf-8") as g:
                g.write(html)

            webbrowser.open(f"file://{os.path.abspath(gallery_file)}")
            messagebox.showinfo("Saved", f"Image saved and gallery updated!\n\nFile: {fp}")

        LiquidButton(
            top, text="💾 Save Image", width=180, height=42,
            fg_color="#7c3aed", hover_color="#a855f7",
            font=("Inter", 14), command=save
        ).pack(pady=6)

        LiquidButton(
            top, text="❌ Close", width=150, height=38,
            fg_color="#312e81", hover_color="#4338ca",
            font=("Inter", 14), command=top.destroy
        ).pack(pady=10)


# ========= Run App =========
if __name__ == "__main__":
    root = ctk.CTk()
    app = ProductGeneratorApp(root)
    root.mainloop()
