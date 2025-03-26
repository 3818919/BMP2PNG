import os
import sys
import tkinter as tk
from tkinter import filedialog, NORMAL, DISABLED
from PIL import Image
import threading
import subprocess

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gui_components import RoundedButton, StyledLabel, StyledProgressBar, Config

class BmpToPngConverter:
    def __init__(self, root):        
        self.root = root
        self.config = Config()
        
        self.root.title(self.config.get('app', 'title'))
        try:
            if os.path.exists(self.config.get('app', 'icon')):
                self.root.iconbitmap(self.config.get('app', 'icon'))
        except:
            pass
            
        self.root.geometry(f"{self.config.get('app', 'width')}x{self.config.get('app', 'height')}")
        self.root.resizable(False, False)
        self.root.configure(bg=self.config.get('colors', 'background'))
        
        self.setup_ui()
        
        self.selected_directory = ""
        self.is_processing = False
        self.total_files = 0
        self.processed_files = 0
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg=self.config.get('colors', 'background'))
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        dir_frame = tk.Frame(main_frame, bg=self.config.get('colors', 'background'))
        dir_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.dir_label = StyledLabel(dir_frame, text="No directory selected", anchor="w")
        self.dir_label.pack(side=tk.LEFT, padx=(0, 5))
        
        select_btn = RoundedButton(dir_frame, "Select Folder", self.select_directory)
        select_btn.pack(side=tk.RIGHT)
        
        self.status_label = StyledLabel(main_frame, text="Processing Message")
        self.status_label.pack(anchor="w", pady=(0, 5))
        
        progress_frame = tk.Frame(main_frame, bg=self.config.get('colors', 'background'), padx=2, pady=2)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_bar = StyledProgressBar(progress_frame)
        self.progress_bar.pack(fill=tk.X)
        
        bottom_frame = tk.Frame(main_frame, bg=self.config.get('colors', 'background'))
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.convert_btn = RoundedButton(bottom_frame, "Convert", self.start_conversion)
        self.convert_btn.pack(side=tk.RIGHT)
        
        credits_label = StyledLabel(bottom_frame, text="Created by Vexx")
        credits_label.pack(side=tk.LEFT)
        
        self.file_counter_label = StyledLabel(main_frame, text="")
        self.file_counter_label.pack(anchor="w")
    
    def select_directory(self):
        directory = filedialog.askdirectory(title="Select Directory with BMP Files")
        if directory:
            if not os.path.exists(directory):
                self.show_error("Selected directory no longer exists")
                return
                
            self.selected_directory = directory
            folder_name = os.path.basename(directory)
            self.dir_label.config(text=folder_name)
            self.count_bmp_files()
    
    def count_bmp_files(self):
        if not self.selected_directory:
            return
            
        try:
            if not os.path.exists(self.selected_directory):
                self.show_error("Selected directory no longer exists")
                self.selected_directory = ""
                self.dir_label.config(text="No directory selected")
                self.convert_btn.config(state=DISABLED)
                return
            
            bmp_files = [f for f in os.listdir(self.selected_directory) 
                        if f.lower().endswith('.bmp')]
            self.total_files = len(bmp_files)
            
            if self.total_files > 0:
                self.file_counter_label.config(text=f"Found {self.total_files} BMP files")
                self.convert_btn.config(state=NORMAL)
            else:
                self.file_counter_label.config(text="No BMP files found in the selected directory")
                self.convert_btn.config(state=DISABLED)
                
        except PermissionError:
            self.show_error("Access denied to selected directory")
            self.selected_directory = ""
            self.dir_label.config(text="No directory selected")
            self.convert_btn.config(state=DISABLED)
        except Exception as e:
            self.show_error(f"Error accessing directory: {str(e)}")
            self.selected_directory = ""
            self.dir_label.config(text="No directory selected")
            self.convert_btn.config(state=DISABLED)
    
    def start_conversion(self):
        if self.is_processing or not self.selected_directory:
            return
        
        output_dir = os.path.join(self.selected_directory, self.config.get('conversion', 'output_folder'))
        os.makedirs(output_dir, exist_ok=True)
        
        self.processed_files = 0
        self.progress_bar["value"] = 0
        self.progress_bar["maximum"] = self.total_files
        
        self.convert_btn.config(state=DISABLED)
        self.is_processing = True
        self.status_label.config(text="Converting...")
        
        threading.Thread(target=self.convert_files, daemon=True).start()
    
    def convert_files(self):
        try:
            bmp_files = [f for f in os.listdir(self.selected_directory) 
                        if f.lower().endswith('.bmp')]
            
            output_dir = os.path.join(self.selected_directory, self.config.get('conversion', 'output_folder'))
            
            for bmp_file in bmp_files:
                try:
                    color_hex = self.config.get('conversion', 'transparent_color').lstrip('#')
                    color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
                    
                    # Normalize paths to use correct system separators
                    input_path = os.path.normpath(os.path.join(self.selected_directory, bmp_file))
                    output_path = os.path.normpath(os.path.join(output_dir, os.path.splitext(bmp_file)[0] + '.png'))
                    
                    # Check if input file exists and is readable
                    if not os.path.exists(input_path):
                        raise FileNotFoundError(f"Input file does not exist: {input_path}")
                    
                    # Check for empty files
                    file_size = os.path.getsize(input_path)
                    if file_size == 0:
                        raise IOError(f"File is empty (0 bytes)")
                    
                    try:
                        # Try to open the file first to verify it's a valid image
                        with open(input_path, 'rb') as test_file:
                            header = test_file.read(2)
                            if not header:
                                raise IOError("File is empty or unreadable")
                            if header != b'BM':  # BMP file header check
                                raise IOError("Not a valid BMP file (incorrect header)")
                    except Exception as e:
                        raise IOError(f"Cannot read file: {str(e)}")
                    
                    # Now try to process the image
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
                    
                except Exception as e:
                    print(f"\nError processing file {bmp_file}:")
                    print(f"Input path: {input_path}")
                    print(f"Error details: {str(e)}")
                    print("File status:")
                    print(f"- File exists: {os.path.exists(input_path)}")
                    try:
                        size = os.path.getsize(input_path)
                        print(f"- File size: {size} bytes")
                        if size == 0:
                            print("  → This file is empty and cannot be processed")
                        elif size < 54:  # Minimum size for a valid BMP header
                            print("  → File is too small to be a valid BMP")
                    except:
                        print("- Could not get file size")
                    print("Continuing with next file...\n")
            
            if self.processed_files < self.total_files:
                failed_files = self.total_files - self.processed_files
                print(f"\nConversion completed with {failed_files} error(s):")
                print(f"Successfully converted {self.processed_files} of {self.total_files} files")
                print("Check the error messages above for details about failed conversions\n")
            
            self.root.after(0, self.conversion_completed)
            
        except Exception as e:
            error_msg = f"Critical error during conversion:\n{str(e)}"
            print(f"\n{error_msg}\n")
            self.root.after(0, lambda: self.show_error(error_msg))
    
    def update_progress(self):
        self.progress_bar["value"] = self.processed_files
        self.file_counter_label.config(text=f"Processed {self.processed_files} of {self.total_files} files")
    
    def conversion_completed(self):
        self.is_processing = False
        self.convert_btn.config(state=NORMAL)
        
        if self.processed_files < self.total_files:
            self.status_label.config(text="Conversion completed with errors")
            print(f"Partially completed: {self.processed_files} of {self.total_files} files converted")
        else:
            self.status_label.config(text="Conversion completed successfully!")
            print("All files converted successfully!")
        
        output_dir = os.path.join(self.selected_directory, self.config.get('conversion', 'output_folder'))
        folder_name = os.path.basename(output_dir)
        self.dir_label.config(text=folder_name)
        self.file_counter_label.config(text=f"Converted {self.processed_files} of {self.total_files} files")
        
        if os.name == 'nt':
            os.startfile(output_dir)
        elif os.name == 'posix':
            subprocess.run(['xdg-open' if os.name == 'linux' else 'open', output_dir])
    
    def show_error(self, error_message):
        self.is_processing = False
        self.convert_btn.config(state=NORMAL)
        
        # Print detailed error to console
        print(f"\nError Details:\n{error_message}\n")
        
        # Show concise message in GUI
        if "Permission denied" in error_message:
            gui_message = "Access denied to directory"
        elif "No such file or directory" in error_message:
            gui_message = "Directory not found"
        elif "cannot find the path specified" in error_message:
            gui_message = "Path not found"
        else:
            gui_message = "Error during conversion"
        
        self.status_label.config(text=f"Error: {gui_message}")

if __name__ == "__main__":
    root = tk.Tk()
    app = BmpToPngConverter(root)
    root.mainloop()