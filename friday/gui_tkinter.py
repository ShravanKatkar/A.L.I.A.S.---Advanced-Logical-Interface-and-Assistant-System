"""
Friday AI Assistant - Tkinter Image Generation GUI
A desktop graphical user interface for Friday's Image Generation module.
Features a premium dark theme, background threads to prevent UI lockup,
aspect ratio selections, model switching, history viewing, and image preview.
"""

import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk

# Import core image generator functions and configurations
import image_generator

# Global constants for styling
COLOR_BG = "#121214"          # Dark main background
COLOR_CARD = "#1a1a1e"        # Slightly lighter card background
COLOR_TEXT_MAIN = "#FFFFFF"   # White text
COLOR_TEXT_MUTED = "#8E9297"  # Muted grey text
COLOR_ACCENT = "#00ADB5"      # Cyan accent
COLOR_ACCENT_HOVER = "#00FFF5"# Bright cyan for hover
COLOR_BORDER = "#2B2D31"      # Border colors
COLOR_ERROR = "#FF5555"       # Error red
COLOR_SUCCESS = "#50FA7B"     # Success green

# Prompt examples list
EXAMPLES = {
    "Cyberpunk": "Cyberpunk street scene at night with vibrant neon signs, rain reflections, flying vehicles, retro-futurism, 8k resolution",
    "Realistic Portrait": "A photorealistic portrait of an old sailor, weathered face, cinematic lighting, shot on 85mm lens, highly detailed",
    "Anime Wallpaper": "Anime style illustration of a magical girl standing on a skyscraper rooftop at twilight, starry night sky, colorful, highly detailed",
    "Minimal Logo": "A minimalist geometric logo for a tech startup, clean lines, white background, vector style, modern color palette",
    "Fantasy Landscape": "Breathtaking landscape of a glowing fantasy forest with a giant moon, pastel colors, desktop wallpaper"
}


class FridayImageApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("FRIDAY AI - Image Studio")
        self.geometry("960x580")
        self.configure(bg=COLOR_BG)
        
        # Set window icon if available or set windows styling
        self.option_add("*font", ("Segoe UI", 9))
        
        # State variables
        self.generation_active = False
        self.current_preview_path = None
        
        # Create UI Layout
        self.setup_styles()
        self.create_widgets()
        
        # Initialize directories
        image_generator.ensure_directories()
        
    def setup_styles(self):
        """
        Configure custom TTK styles for a modern dark-mode aesthetic.
        """
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Frame styles
        self.style.configure("TFrame", background=COLOR_BG)
        self.style.configure("Card.TFrame", background=COLOR_CARD, borderwidth=1, relief="solid")
        
        # Label styles
        self.style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT_MAIN)
        self.style.configure("Card.TLabel", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN)
        self.style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_ACCENT, font=("Segoe UI", 14, "bold"))
        self.style.configure("Section.TLabel", background=COLOR_CARD, foreground=COLOR_ACCENT, font=("Segoe UI", 10, "bold"))
        
        # Slider (Scale) styles
        self.style.configure("Horizontal.TScale", background=COLOR_CARD, troughcolor=COLOR_BG)
        
        # Combobox styles
        self.style.configure("TCombobox", fieldbackground=COLOR_BG, background=COLOR_BORDER, foreground=COLOR_TEXT_MAIN)
        
        # Radiobutton styles
        self.style.configure("TRadiobutton", background=COLOR_CARD, foreground=COLOR_TEXT_MAIN, focuscolor=COLOR_CARD)
        
    def create_widgets(self):
        """
        Creates and arranges the Tkinter elements in a responsive grid.
        """
        # --- Root Grid Config ---
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)
        
        # --- Header Section ---
        header_frame = ttk.Frame(self, style="TFrame")
        header_frame.grid(row=0, column=0, columnspan=2, fill="x", padx=15, pady=(10, 5))
        
        title_label = ttk.Label(header_frame, text="FRIDAY AI  //  IMAGE STUDIO", style="Title.TLabel")
        title_label.pack(side="left")
        
        subtitle_label = ttk.Label(header_frame, text="Pollinations AI Engine", style="TLabel", foreground=COLOR_TEXT_MUTED)
        subtitle_label.pack(side="left", padx=10, pady=3)
        
        # --- Left Panel (Inputs & Controls) ---
        left_panel = ttk.Frame(self, style="Card.TFrame")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(15, 8), pady=(0, 15))
        left_panel.columnconfigure(0, weight=1)
        
        # Padding variables for compact layout
        pad_x, pad_y = 12, 6
        
        # 1. Prompt Input
        prompt_title = ttk.Label(left_panel, text="IMAGE PROMPT", style="Section.TLabel")
        prompt_title.grid(row=0, column=0, sticky="w", padx=pad_x, pady=(pad_y, 1))
        
        self.prompt_text = scrolledtext.ScrolledText(
            left_panel, height=2, bg=COLOR_BG, fg=COLOR_TEXT_MAIN, 
            insertbackground=COLOR_TEXT_MAIN, bd=1, relief="solid", 
            highlightcolor=COLOR_ACCENT, highlightbackground=COLOR_BORDER,
            wrap="word", font=("Segoe UI", 9)
        )
        self.prompt_text.grid(row=1, column=0, sticky="ew", padx=pad_x, pady=3)
        self.prompt_text.insert(tk.END, "A futuristic sci-fi city with flying cars at night")
        
        # 2. Dimensions Slider
        dim_frame = ttk.Frame(left_panel, style="Card.TFrame")
        dim_frame.grid(row=2, column=0, sticky="ew", padx=pad_x, pady=3)
        dim_frame.columnconfigure(0, weight=1)
        dim_frame.columnconfigure(1, weight=1)
        
        # Width Slider
        width_label_frame = ttk.Frame(dim_frame, style="Card.TFrame")
        width_label_frame.grid(row=0, column=0, sticky="ew", padx=3, pady=3)
        
        self.width_var = tk.IntVar(value=1024)
        self.width_label = ttk.Label(width_label_frame, text="Width: 1024px", style="Card.TLabel")
        self.width_label.pack(anchor="w")
        
        self.width_scale = ttk.Scale(
            width_label_frame, from_=256, to=2048, variable=self.width_var,
            orient="horizontal", style="Horizontal.TScale", command=self.update_dimension_labels
        )
        self.width_scale.pack(fill="x", pady=1)
        
        # Height Slider
        height_label_frame = ttk.Frame(dim_frame, style="Card.TFrame")
        height_label_frame.grid(row=0, column=1, sticky="ew", padx=3, pady=3)
        
        self.height_var = tk.IntVar(value=1024)
        self.height_label = ttk.Label(height_label_frame, text="Height: 1024px", style="Card.TLabel")
        self.height_label.pack(anchor="w")
        
        self.height_scale = ttk.Scale(
            height_label_frame, from_=256, to=2048, variable=self.height_var,
            orient="horizontal", style="Horizontal.TScale", command=self.update_dimension_labels
        )
        self.height_scale.pack(fill="x", pady=1)
        
        # 3. Model & Seed Settings
        settings_frame = ttk.Frame(left_panel, style="Card.TFrame")
        settings_frame.grid(row=3, column=0, sticky="ew", padx=pad_x, pady=3)
        settings_frame.columnconfigure(0, weight=1)
        settings_frame.columnconfigure(1, weight=1)
        
        # Model Selection
        model_container = ttk.Frame(settings_frame, style="Card.TFrame")
        model_container.grid(row=0, column=0, sticky="nw", padx=3, pady=3)
        
        ttk.Label(model_container, text="Generation Model", style="Card.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
        self.model_var = tk.StringVar(value="flux")
        
        rb_flux = ttk.Radiobutton(model_container, text="FLUX (Premium)", variable=self.model_var, value="flux", style="TRadiobutton")
        rb_flux.pack(anchor="w")
        
        rb_default = ttk.Radiobutton(model_container, text="Default Model", variable=self.model_var, value="default", style="TRadiobutton")
        rb_default.pack(anchor="w")
        
        # Seed Option
        seed_container = ttk.Frame(settings_frame, style="Card.TFrame")
        seed_container.grid(row=0, column=1, sticky="nw", padx=3, pady=3)
        
        ttk.Label(seed_container, text="Seed (Optional)", style="Card.TLabel", font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 2))
        
        self.seed_var = tk.StringVar(value="")
        self.seed_entry = tk.Entry(
            seed_container, textvariable=self.seed_var, bg=COLOR_BG, fg=COLOR_TEXT_MAIN,
            insertbackground=COLOR_TEXT_MAIN, bd=1, relief="solid", highlightthickness=1,
            highlightcolor=COLOR_ACCENT, highlightbackground=COLOR_BORDER, width=12
        )
        self.seed_entry.pack(anchor="w", ipady=1)
        
        ttk.Label(seed_container, text="Leave blank for random", style="Card.TLabel", foreground=COLOR_TEXT_MUTED, font=("Segoe UI", 7)).pack(anchor="w", pady=1)
        
        # 4. Template Prompts
        template_title = ttk.Label(left_panel, text="QUICK DESIGN TEMPLATES", style="Section.TLabel")
        template_title.grid(row=4, column=0, sticky="w", padx=pad_x, pady=(8, 1))
        
        templates_frame = ttk.Frame(left_panel, style="Card.TFrame")
        templates_frame.grid(row=5, column=0, sticky="ew", padx=pad_x, pady=3)
        
        # Create grid of template buttons
        row, col = 0, 0
        for name, prompt_text in EXAMPLES.items():
            btn = tk.Button(
                templates_frame, text=name, bg=COLOR_BG, fg=COLOR_TEXT_MAIN,
                activebackground=COLOR_BORDER, activeforeground=COLOR_ACCENT,
                bd=1, relief="solid", highlightthickness=0, font=("Segoe UI", 7),
                command=lambda p=prompt_text: self.load_template(p)
            )
            btn.grid(row=row, column=col, padx=3, pady=3, sticky="ew")
            # Bind hover effect
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=COLOR_BORDER, fg=COLOR_ACCENT))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=COLOR_BG, fg=COLOR_TEXT_MAIN))
            
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        # 5. Generate Button
        self.btn_generate = tk.Button(
            left_panel, text="GENERATE IMAGE", bg=COLOR_ACCENT, fg=COLOR_BG,
            activebackground=COLOR_ACCENT_HOVER, activeforeground=COLOR_BG,
            font=("Segoe UI", 11, "bold"), bd=0, cursor="hand2", command=self.start_generation
        )
        self.btn_generate.grid(row=6, column=0, sticky="ew", padx=pad_x, pady=(10, pad_y), ipady=6)
        self.btn_generate.bind("<Enter>", lambda e: self.btn_generate.config(bg=COLOR_ACCENT_HOVER))
        self.btn_generate.bind("<Leave>", lambda e: self.btn_generate.config(bg=COLOR_ACCENT))
        
        # --- Right Panel (Visual Preview) ---
        right_panel = ttk.Frame(self, style="Card.TFrame")
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(8, 15), pady=(0, 15))
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=1)
        
        # Preview Container
        self.preview_canvas = tk.Canvas(
            right_panel, bg=COLOR_BG, bd=1, relief="solid",
            highlightthickness=0
        )
        self.preview_canvas.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        
        # Bind canvas resize to update display
        self.preview_canvas.bind("<Configure>", self.on_canvas_resize)
        
        # Setup Initial Canvas Message
        self.draw_placeholder_text("No Image Generated Yet\n\nEnter a prompt and click Generate")
        
        # --- Status Bar ---
        self.status_bar = tk.Label(
            self, text="Ready", bg=COLOR_BG, fg=COLOR_TEXT_MUTED,
            anchor="w", font=("Segoe UI", 9)
        )
        self.status_bar.grid(row=2, column=0, columnspan=2, fill="x", padx=20, pady=(0, 5))
        
    def update_dimension_labels(self, *args):
        """
        Updates the UI labels when scale values change.
        """
        # Snap sliders to multiples of 64 for cleaner neural net aspect ratios
        w = int(round(self.width_var.get() / 64) * 64)
        h = int(round(self.height_var.get() / 64) * 64)
        
        # Clamp bounds
        w = max(256, min(w, 2048))
        h = max(256, min(h, 2048))
        
        self.width_var.set(w)
        self.height_var.set(h)
        
        self.width_label.config(text=f"Width: {w}px")
        self.height_label.config(text=f"Height: {h}px")
        
    def load_template(self, prompt_text: str):
        """
        Loads a preset template prompt into the prompt box.
        """
        self.prompt_text.delete("1.0", tk.END)
        self.prompt_text.insert(tk.END, prompt_text)
        self.set_status("Loaded template prompt.", COLOR_TEXT_MAIN)
        
    def set_status(self, message: str, color=COLOR_TEXT_MUTED):
        """
        Sets the status bar text and color.
        """
        self.status_bar.config(text=f"Status: {message}", fg=color)
        
    def draw_placeholder_text(self, text: str):
        """
        Draws placeholder text on the preview canvas.
        """
        self.preview_canvas.delete("all")
        width = self.preview_canvas.winfo_width()
        height = self.preview_canvas.winfo_height()
        # Fallback default size if config hasn't run yet
        if width <= 1:
            width, height = 450, 450
            
        self.preview_canvas.create_rectangle(
            5, 5, width-5, height-5, outline=COLOR_BORDER, width=1, dash=(5, 5)
        )
        self.preview_canvas.create_text(
            width/2, height/2, text=text, fill=COLOR_TEXT_MUTED,
            justify="center", font=("Segoe UI", 11)
        )
        
    def start_generation(self):
        """
        Triggers the image generation in a secondary background thread.
        """
        if self.generation_active:
            return
            
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("Empty Prompt", "Please enter an image prompt first.")
            return
            
        width = self.width_var.get()
        height = self.height_var.get()
        model = self.model_var.get()
        
        # Check seed
        seed_str = self.seed_var.get().strip()
        seed = None
        if seed_str:
            try:
                seed = int(seed_str)
            except ValueError:
                messagebox.showerror("Invalid Seed", "Seed must be an integer or left blank.")
                return
                
        # Lock UI
        self.generation_active = True
        self.btn_generate.config(state="disabled", text="GENERATING...", bg=COLOR_BORDER, fg=COLOR_TEXT_MUTED)
        self.set_status("Friday is calling Pollinations AI...", COLOR_ACCENT)
        self.draw_placeholder_text("GENERATING IMAGE...\n\nSending request to Pollinations AI API")
        
        # Spin up generation thread
        t = threading.Thread(
            target=self.run_generation_thread, 
            args=(prompt, width, height, seed, model),
            daemon=True
        )
        t.start()
        
    def run_generation_thread(self, prompt: str, width: int, height: int, seed: int, model: str):
        """
        Internal worker run in background to fetch the image.
        """
        try:
            # Call custom generator directly
            saved_path = image_generator.generate_custom_image(
                prompt=prompt, width=width, height=height, seed=seed, model=model
            )
            
            if saved_path and os.path.exists(saved_path):
                # Update UI on success
                self.after(0, lambda: self.generation_success(saved_path))
            else:
                self.after(0, lambda: self.generation_failed("Image downloader failed to save file."))
        except Exception as e:
            self.after(0, lambda e=e: self.generation_failed(str(e)))
            
    def generation_success(self, filepath: str):
        """
        Handles post-generation updates (re-enabling buttons, updating canvas).
        """
        self.generation_active = False
        self.btn_generate.config(state="normal", text="GENERATE IMAGE", bg=COLOR_ACCENT, fg=COLOR_BG)
        self.set_status("Success! Image generated and saved.", COLOR_SUCCESS)
        
        # Load and render image on canvas
        self.current_preview_path = filepath
        self.render_image_on_canvas()
        
    def generation_failed(self, error_message: str):
        """
        Handles API request failures.
        """
        self.generation_active = False
        self.btn_generate.config(state="normal", text="GENERATE IMAGE", bg=COLOR_ACCENT, fg=COLOR_BG)
        self.set_status(f"Error: {error_message}", COLOR_ERROR)
        self.draw_placeholder_text(f"Generation Failed!\n\n{error_message}\n\nPlease check your network or try again.")
        messagebox.showerror("Generation Error", f"Failed to generate image:\n{error_message}")
        
    def render_image_on_canvas(self):
        """
        Loads the current generated image, scales it proportionally to fit the canvas,
        and renders it.
        """
        if not self.current_preview_path or not os.path.exists(self.current_preview_path):
            return
            
        try:
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            # Safe boundary check
            if canvas_width <= 10 or canvas_height <= 10:
                return
                
            img = Image.open(self.current_preview_path)
            
            # Calculate aspect ratio scaling
            img_w, img_h = img.size
            ratio_w = canvas_width / img_w
            ratio_h = canvas_height / img_h
            scale_ratio = min(ratio_w, ratio_h) * 0.95 # Leave a small margin
            
            new_w = int(img_w * scale_ratio)
            new_h = int(img_h * scale_ratio)
            
            # Resize image with high-quality filter
            resized_img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage and draw
            self.tk_image = ImageTk.PhotoImage(resized_img)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(
                canvas_width/2, canvas_height/2, image=self.tk_image, anchor="center"
            )
        except Exception as e:
            self.set_status(f"Preview Render Error: {e}", COLOR_ERROR)
            
    def on_canvas_resize(self, event):
        """
        Triggered when canvas dimensions change. Redraws image or placeholder.
        """
        if self.generation_active:
            self.draw_placeholder_text("GENERATING IMAGE...\n\nSending request to Pollinations AI API")
        elif self.current_preview_path:
            self.render_image_on_canvas()
        else:
            self.draw_placeholder_text("No Image Generated Yet\n\nEnter a prompt and click Generate")


if __name__ == "__main__":
    # Create the application
    app = FridayImageApp()
    # Start the Tkinter main loop
    app.mainloop()
