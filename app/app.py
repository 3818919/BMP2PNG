import os
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image
import threading
import subprocess


class Settings:
    # User can modify this hex color value to specify which color to make transparent
    # Format: '#RRGGBB' (e.g., '#FF0000' for red)
    COLOR_TO_REMOVE = '#000000'  # Default: black
    
    # Output folder name
    OUTPUT_FOLDER = "PNG_exports"
    WINDOW_TITLE = "BMP to PNG Converter"
    WINDOW_ICON = "app/icon.ico"
    
    # GUI Colors and Fonts
    BG_COLOR = "#1E1E1E"
    TEXT_COLOR = "#FFFFFF"
    BUTTON_BG = "#0078D4"
    BUTTON_FG = "#FFFFFF"
    PROGRESS_BG = "#333333"
    PROGRESS_FG = "#0078D4"

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, width=80, height=30, corner_radius=10, bg=Settings.BUTTON_BG, fg=Settings.BUTTON_FG, **kwargs):
        super().__init__(parent, width=width, height=height, bg=Settings.BG_COLOR, highlightthickness=0, **kwargs)

        self.command = command
        self.create_rounded_rect(0, 0, width, height, corner_radius, fill=bg)
        self.create_text(width/2, height/2, text=text, fill=fg, font=('Arial', 9))
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', lambda e: self.config(cursor='hand2'))
    
    def create_rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def _on_click(self, event):
        if self.command:
            self.command()

class BmpToPngConverter:
    def __init__(self, root):        
        self.root = root
        self.root.title(Settings.WINDOW_TITLE)

        try:
            if os.path.exists(Settings.WINDOW_ICON):
                self.root.iconbitmap(Settings.WINDOW_ICON)
        except:
            pass 
            
        self.root.geometry("300x180")
        self.root.resizable(False, False)
        self.root.configure(bg=Settings.BG_COLOR)
        self.setup_ui()
        self.selected_directory = ""
        self.is_processing = False
        self.total_files = 0
        self.processed_files = 0
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=Settings.BG_COLOR)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        dir_frame = tk.Frame(main_frame, bg=Settings.BG_COLOR)
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        self.dir_label = tk.Label(dir_frame, text="No directory selected", 
                                fg=Settings.TEXT_COLOR, bg=Settings.BG_COLOR,
                                width=20, anchor="w")
        self.dir_label.pack(side=tk.LEFT, padx=(0, 5))
        select_btn = RoundedButton(dir_frame, text="Select Folder", command=self.select_directory)
        select_btn.pack(side=tk.RIGHT)
        self.status_label = tk.Label(main_frame, text="Processing Message",
                                   fg=Settings.TEXT_COLOR, bg=Settings.BG_COLOR)
        self.status_label.pack(anchor="w", pady=(0, 5))
        style = ttk.Style()
        style.theme_use('default')
        style.layout('Rounded.Horizontal.TProgressbar', 
                    [('Horizontal.Progressbar.trough',
                      {'sticky': 'nswe',
                       'children': [('Horizontal.Progressbar.pbar',
                                   {'side': 'left', 'sticky': 'ns'})]})])
        style.configure('Rounded.Horizontal.TProgressbar',
                       troughcolor=Settings.PROGRESS_BG,
                       background=Settings.PROGRESS_FG,
                       thickness=15,
                       borderwidth=0)
        progress_frame = tk.Frame(main_frame, bg=Settings.BG_COLOR, padx=2, pady=2)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_frame,
                                          style='Rounded.Horizontal.TProgressbar',
                                          orient="horizontal",
                                          length=280,
                                          mode="determinate")
        self.progress_bar.pack(fill=tk.X)
        bottom_frame = tk.Frame(main_frame, bg=Settings.BG_COLOR)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.convert_btn = RoundedButton(bottom_frame, text="Convert", command=self.start_conversion)
        self.convert_btn.pack(side=tk.RIGHT)
        credits_label = tk.Label(bottom_frame, text="Created by Vexx",
                               fg=Settings.TEXT_COLOR, bg=Settings.BG_COLOR)
        credits_label.pack(side=tk.LEFT)
        self.file_counter_label = tk.Label(main_frame, text="",
                                         fg=Settings.TEXT_COLOR, bg=Settings.BG_COLOR)
        self.file_counter_label.pack(anchor="w")
    
    def select_directory(self):
        directory = filedialog.askdirectory(title="Select Directory with BMP Files")

        if directory:
            self.selected_directory = directory
            folder_name = os.path.basename(directory)
            self.dir_label.config(text=folder_name)
            self.count_bmp_files()
    
    def count_bmp_files(self):
        if not self.selected_directory:
            return
        
        bmp_files = [f for f in os.listdir(self.selected_directory) 
                    if f.lower().endswith('.bmp')]
        self.total_files = len(bmp_files)
        
        if self.total_files > 0:
            self.file_counter_label.config(text=f"Found {self.total_files} BMP files")
            self.convert_btn.config(state=tk.NORMAL)
        else:
            self.file_counter_label.config(text="No BMP files found in the selected directory")
            self.convert_btn.config(state=tk.DISABLED)
    
    def start_conversion(self):

        if self.is_processing or not self.selected_directory:
            return

        output_dir = os.path.join(self.selected_directory, Settings.OUTPUT_FOLDER)
        os.makedirs(output_dir, exist_ok=True)
        self.processed_files = 0
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = self.total_files
        self.convert_btn.config(state=tk.DISABLED)
        self.is_processing = True
        self.status_label.config(text="Converting...")
        threading.Thread(target=self.convert_files, daemon=True).start()
    
    def convert_files(self):
        try:
            bmp_files = [f for f in os.listdir(self.selected_directory) 
                        if f.lower().endswith('.bmp')]
            output_dir = os.path.join(self.selected_directory, Settings.OUTPUT_FOLDER)

            for bmp_file in bmp_files:
                color_hex = Settings.COLOR_TO_REMOVE.lstrip('#')
                color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
                input_path = os.path.join(self.selected_directory, bmp_file)
                output_path = os.path.join(output_dir, os.path.splitext(bmp_file)[0] + '.png')
                img = Image.open(input_path)
                img = img.convert("RGBA")
                data = img.getdata()
                new_data = []
                for item in data:
                    if item[0] == color_rgb[0] and item[1] == color_rgb[1] and item[2] == color_rgb[2]:
                        new_data.append((255, 255, 255, 0))
                    else:
                        new_data.append(item)
                img.putdata(new_data)
                img.save(output_path, "PNG")
                self.processed_files += 1
                self.root.after(0, self.update_progress)

            self.root.after(0, self.conversion_completed)

        except Exception as e:
            self.root.after(0, lambda: self.show_error(str(e)))
    
    def update_progress(self):
        self.progress_bar["value"] = self.processed_files
        self.file_counter_label.config(text=f"Processed {self.processed_files} of {self.total_files} files")
    
    def conversion_completed(self):
        self.is_processing = False
        self.convert_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Conversion completed!")
        output_dir = os.path.join(self.selected_directory, Settings.OUTPUT_FOLDER)
        folder_name = os.path.basename(output_dir)
        self.dir_label.config(text=folder_name)
        self.file_counter_label.config(text=f"Converted to {folder_name}")
        os.startfile(output_dir)
    
    def show_error(self, error_message):
        self.is_processing = False
        self.convert_btn.config(state=tk.NORMAL)
        self.status_label.config(text=f"Error: {error_message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BmpToPngConverter(root)
    root.mainloop()