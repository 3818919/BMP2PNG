import tkinter as tk
from tkinter import ttk, colorchooser, NORMAL, DISABLED
import json
import os

class Config:
    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        with open(config_path, 'r') as f:
            self.config = json.load(f)
    
    def get(self, *keys, default=None):
        value = self.config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value
    
    def get_template(self, component_type):
        return self.get('components', component_type, 'template', default={})

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, **kwargs):
        self.settings = Config()
        
        # Get button template
        template = self.settings.get_template('button')
        width = kwargs.get('width', template.get('width', 80))
        height = kwargs.get('height', template.get('height', 30))
        corner_radius = kwargs.get('corner_radius', template.get('corner_radius', 10))
        
        # Initialize canvas with parent's background color
        super().__init__(
            parent,
            highlightthickness=0,
            bg=self.settings.get('colors', 'background'),
            width=width,
            height=height,
            **kwargs
        )
        
        # Get colors from config
        self.bg_color = self.settings.get('colors', 'button', 'background')
        self.fg_color = self.settings.get('colors', 'button', 'foreground')
        self.hover_color = self.settings.get('colors', 'button', 'hover')
        self.disabled_color = self.settings.get('colors', 'button', 'disabled', default='#666666')
        self.disabled_fg = self.settings.get('colors', 'button', 'disabled_text', default='#999999')
        
        self.command = command
        self.state = 'normal'
        self.text = text
        self._create_button()
        
        self.bind('<Button-1>', self._on_click)
        self.bind('<Enter>', self._on_enter)
        self.bind('<Leave>', self._on_leave)
        self.bind('<Motion>', lambda e: self.configure(cursor='hand2' if self.state == 'normal' else ''))
    
    def _create_button(self):
        # Clear any existing items
        self.delete('all')
        
        # Get dimensions
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        corner_radius = self.settings.get_template('button').get('corner_radius', 10)
        
        # Create the button shape
        self.create_rounded_rect(0, 0, width, height, corner_radius,
                               fill=self.disabled_color if self.state == 'disabled' else self.bg_color)
        
        # Create the text
        self.create_text(width/2, height/2, text=self.text,
                        fill=self.disabled_fg if self.state == 'disabled' else self.fg_color,
                        font=(self.settings.get_template('button').get('font', 'Arial'),
                              self.settings.get_template('button').get('font_size', 9)))
    
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
        if self.state == 'normal' and self.command:
            self.command()
    
    def _on_enter(self, event):
        if self.state == 'normal':
            self.itemconfig(1, fill=self.hover_color)
    
    def _on_leave(self, event):
        if self.state == 'normal':
            self.itemconfig(1, fill=self.bg_color)
    
    def configure(self, **kwargs):
        if 'state' in kwargs:
            # Convert tk.NORMAL/tk.DISABLED to 'normal'/'disabled'
            state = kwargs['state']
            if state in (NORMAL, 'normal'):
                state = 'normal'
            elif state in (DISABLED, 'disabled'):
                state = 'disabled'
            self.state = state
            self._create_button()
            kwargs.pop('state')
        super().configure(**kwargs)
    
    config = configure

class StyledLabel(tk.Label):
    def __init__(self, parent, text="", **kwargs):
        config = Config()
        template = config.get_template('label')
        
        super().__init__(
            parent,
            text=text,
            fg=config.get('colors', 'text'),
            bg=config.get('colors', 'background'),
            font=(template.get('font', 'Arial'), template.get('font_size', 9)),
            **kwargs
        )

class StyledProgressBar(ttk.Progressbar):
    def __init__(self, parent, **kwargs):
        config = Config()
        template = config.get_template('progress_bar')
        
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure(
            'Rounded.Horizontal.TProgressbar',
            troughcolor=config.get('colors', 'progress', 'background'),
            background=config.get('colors', 'progress', 'foreground'),
            thickness=template.get('thickness', 15),
            borderwidth=0
        )
        
        super().__init__(
            parent,
            style='Rounded.Horizontal.TProgressbar',
            orient="horizontal",
            length=template.get('length', 280),
            mode="determinate",
            **kwargs
        )

class StyledEntry(tk.Entry):
    def __init__(self, parent, **kwargs):
        config = Config()
        template = config.get_template('entry')
        
        super().__init__(
            parent,
            bg=config.get('colors', 'input', 'background'),
            fg=config.get('colors', 'input', 'foreground'),
            insertbackground=config.get('colors', 'input', 'foreground'),
            relief="flat",
            highlightthickness=1,
            highlightbackground=config.get('colors', 'input', 'border'),
            highlightcolor=config.get('colors', 'input', 'focus_border'),
            **kwargs
        )
        
        self.bind('<FocusIn>', lambda e: self.config(highlightbackground=config.get('colors', 'input', 'focus_border')))
        self.bind('<FocusOut>', lambda e: self.config(highlightbackground=config.get('colors', 'input', 'border')))

class StyledCombobox(ttk.Combobox):
    def __init__(self, parent, values, **kwargs):
        config = Config()
        template = config.get_template('dropdown')
        
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure(
            'Styled.TCombobox',
            background=config.get('colors', 'dropdown', 'background'),
            foreground=config.get('colors', 'dropdown', 'foreground'),
            fieldbackground=config.get('colors', 'dropdown', 'background'),
            selectbackground=config.get('colors', 'dropdown', 'selected_background'),
            selectforeground=config.get('colors', 'dropdown', 'selected_foreground'),
            arrowcolor=config.get('colors', 'dropdown', 'button_foreground')
        )
        
        super().__init__(
            parent,
            values=values,
            style='Styled.TCombobox',
            state='readonly',
            width=template.get('width', 15),
            **kwargs
        )

class ColorSelector(tk.Frame):
    def __init__(self, parent, initial_color='#000000', on_color_change=None, **kwargs):
        config = Config()
        template = config.get_template('color_selector')
        
        super().__init__(parent, bg=config.get('colors', 'background'), **kwargs)
        
        self.on_color_change = on_color_change
        self.color = initial_color
        
        self.color_button = tk.Canvas(
            self,
            width=template.get('button_size', 30),
            height=template.get('button_size', 30),
            bg=self.color,
            highlightthickness=0
        )
        self.color_button.pack(side=tk.LEFT, padx=template.get('padding', 2))
        
        picker_btn = RoundedButton(
            self,
            "Pick Color",
            self.pick_color
        )
        picker_btn.pack(side=tk.LEFT, padx=template.get('padding', 2))
        
        self.color_entry = StyledEntry(
            self,
            width=8,
            justify='center'
        )
        self.color_entry.pack(side=tk.LEFT, padx=template.get('padding', 2))
        self.color_entry.insert(0, self.color)
        self.color_entry.bind('<Return>', self.update_color_from_entry)
    
    def pick_color(self):
        color = colorchooser.askcolor(
            color=self.color,
            title="Choose Color"
        )[1]
        if color:
            self.set_color(color)
    
    def set_color(self, color):
        self.color = color
        self.color_button.configure(bg=color)
        self.color_entry.delete(0, tk.END)
        self.color_entry.insert(0, color)
        if self.on_color_change:
            self.on_color_change(color)
    
    def update_color_from_entry(self, event):
        color = self.color_entry.get()
        if color.startswith('#'):
            self.set_color(color)
    
    def get_color(self):
        return self.color 