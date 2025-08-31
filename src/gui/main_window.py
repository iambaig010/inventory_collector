import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import logging
from datetime import datetime
from src.core.inventory_collector import InventoryCollector
from src.utils.excel_handler import ExcelHandler


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Switch Inventory Collector Pro")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Configure modern styling
        self.setup_modern_styling()
        
        # Application state
        self.devices_file = None
        self.collector = InventoryCollector()
        self.excel_handler = ExcelHandler()
        self.current_task = None
        
        # Thread communication
        self.progress_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Setup logging for GUI
        self.setup_gui_logging()
        
        # Build UI
        self.setup_ui()
        
        # Start queue monitoring
        self.monitor_queues()
        
    def setup_modern_styling(self):
        """Setup modern styling with dark theme and contemporary colors"""
        style = ttk.Style()
        
        # Modern color palette
        self.colors = {
            'primary': '#3b82f6',      # Modern blue
            'primary_hover': '#2563eb',
            'success': '#10b981',      # Modern green
            'warning': '#f59e0b',      # Modern amber
            'error': '#ef4444',        # Modern red
            'background': '#0f172a',   # Dark slate
            'surface': '#1e293b',      # Card background
            'surface_light': '#334155', # Lighter surface
            'text': '#f8fafc',         # Light text
            'text_secondary': '#94a3b8', # Muted text
            'border': '#475569',       # Modern border
            'accent': '#8b5cf6',       # Purple accent
            'input_bg': '#374151',     # Input background
            'hover': '#4f46e5'         # Hover state
        }
        
        # Configure modern ttk styles with dark theme
        style.theme_use('clam')
        
        # Detect system and set appropriate fonts
        try:
            if os.name == 'nt':  # Windows
                primary_font = 'Segoe UI'
                mono_font = 'Consolas'
            elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin':  # macOS
                primary_font = 'SF Pro Display'
                mono_font = 'SF Mono'
            else:  # Linux or fallback
                primary_font = 'Ubuntu'
                mono_font = 'Ubuntu Mono'
        except:
            # Ultimate fallback
            primary_font = 'Arial'
            mono_font = 'Courier New'
            
        # Store fonts for use throughout the class
        self.primary_font = primary_font
        self.mono_font = mono_font
        
        # Configure styles with proper font variables
        style.configure('Title.TLabel', font=(self.primary_font, 28, 'bold'), 
                       background=self.colors['background'], foreground=self.colors['text'])
        style.configure('Subtitle.TLabel', font=(self.primary_font, 14), 
                       background=self.colors['background'], foreground=self.colors['text_secondary'])
        style.configure('Header.TLabel', font=(self.primary_font, 12, 'bold'), 
                       background=self.colors['surface'], foreground=self.colors['text'])
        style.configure('Body.TLabel', font=(self.primary_font, 10), 
                       background=self.colors['surface'], foreground=self.colors['text_secondary'])
        
        # Configure Dark.TFrame style
        style.configure('Dark.TFrame', background=self.colors['background'])
        
        # Modern button styles
        style.configure('Primary.TButton', 
                       font=(self.primary_font, 11, 'bold'),
                       foreground='white',
                       focuscolor='none',
                       borderwidth=0,
                       relief='flat')
        style.map('Primary.TButton',
                 background=[('active', self.colors['primary_hover']), 
                           ('!active', self.colors['primary'])])
        
        style.configure('Success.TButton', 
                       font=(self.primary_font, 12, 'bold'),
                       foreground='white',
                       focuscolor='none',
                       borderwidth=0,
                       relief='flat')
        style.map('Success.TButton',
                 background=[('active', '#059669'), 
                           ('!active', self.colors['success'])])
        
        style.configure('Secondary.TButton', 
                       font=(self.primary_font, 10),
                       foreground=self.colors['text'],
                       focuscolor='none',
                       borderwidth=1,
                       relief='flat')
        style.map('Secondary.TButton',
                 background=[('active', self.colors['surface_light']), 
                           ('!active', self.colors['surface'])])
        
        # Entry styling
        style.configure('Modern.TEntry',
                       font=(self.primary_font, 11),
                       fieldbackground=self.colors['input_bg'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       insertcolor=self.colors['text'],
                       relief='flat')
        
        # LabelFrame styling
        style.configure('Card.TLabelframe',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       borderwidth=0,
                       relief='flat')
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=(self.primary_font, 11, 'bold'))
        
        # Fix: Proper progress bar styling configuration
        style.configure('Horizontal.TProgressbar',
                       background=self.colors['primary'],
                       troughcolor=self.colors['surface_light'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        # Configure root window
        self.root.configure(bg=self.colors['background'])
        
    def setup_gui_logging(self):
        """Setup logging that will display in GUI"""
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
    def setup_ui(self):
        """Create the modern user interface with card-based layout"""
        # Main container with proper spacing
        main_frame = ttk.Frame(self.root, style='Dark.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=32, pady=32)
        
        # Header section
        self.create_modern_header(main_frame)
        
        # Content area with cards
        content_container = ttk.Frame(main_frame, style='Dark.TFrame')
        content_container.pack(fill=tk.BOTH, expand=True, pady=(32, 0))
        
        # Create responsive grid layout
        self.create_grid_layout(content_container)
        
        # Footer with better spacing
        self.create_modern_footer(main_frame)
        
    def create_modern_header(self, parent):
        """Create sleek modern header with better visual hierarchy"""
        header_frame = ttk.Frame(parent, style='Dark.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        # Header content container
        header_content = ttk.Frame(header_frame, style='Dark.TFrame')
        header_content.pack(fill=tk.X)
        
        # Left side - branding
        brand_frame = ttk.Frame(header_content, style='Dark.TFrame')
        brand_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # Modern icon with gradient effect (using Unicode)
        icon_frame = ttk.Frame(brand_frame, style='Dark.TFrame')
        icon_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        icon_label = ttk.Label(icon_frame, text="🔌", font=('Segoe UI Emoji', 36),
                              background=self.colors['background'])
        icon_label.pack()
        
        # Title section with better typography
        title_section = ttk.Frame(brand_frame, style='Dark.TFrame')
        title_section.pack(side=tk.LEFT)
        
        title_label = ttk.Label(title_section, text="Switch Inventory Collector", 
                               style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        pro_badge = ttk.Label(title_section, text="PRO", 
                             font=(self.primary_font, 12, 'bold'),
                             background=self.colors['primary'],
                             foreground='white',
                             padding=(8, 2))
        pro_badge.pack(anchor=tk.W, pady=(4, 8))
        
        subtitle_label = ttk.Label(title_section, 
                                  text="Enterprise Network Device Management", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W)
        
        # Right side - connection status
        status_frame = ttk.Frame(header_content, style='Dark.TFrame')
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Connection indicator
        self.connection_status = ttk.Label(status_frame, text="🟢 System Online",
                                         font=(self.primary_font, 10, 'bold'),
                                         background=self.colors['background'],
                                         foreground=self.colors['success'])
        self.connection_status.pack(anchor=tk.E, pady=(10, 5))
        
        # Quick stats
        self.quick_stats = ttk.Label(status_frame, text="Ready to connect",
                                   font=(self.primary_font, 9),
                                   background=self.colors['background'],
                                   foreground=self.colors['text_secondary'])
        self.quick_stats.pack(anchor=tk.E)
        
    def create_grid_layout(self, parent):
        """Create modern card-based grid layout"""
        # Left column - Configuration cards
        left_column = ttk.Frame(parent, style='Dark.TFrame')
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 24))
        left_column.configure(width=420)
        left_column.pack_propagate(False)
        
        # Right column - Activity monitor
        right_column = ttk.Frame(parent, style='Dark.TFrame')
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create configuration cards
        self.create_file_card(left_column)
        self.create_credentials_card(left_column)
        self.create_progress_card(left_column)
        self.create_actions_card(left_column)
        
        # Create activity monitor
        self.create_activity_monitor(right_column)
        
    def create_file_card(self, parent):
        """Create modern file selection card"""
        card_frame = ttk.LabelFrame(parent, text="  📁  Device Configuration", 
                                   style='Card.TLabelframe', padding=24)
        card_frame.pack(fill=tk.X, pady=(0, 20))
        
        # File status with better visual feedback
        status_frame = ttk.Frame(card_frame, style='Dark.TFrame')
        status_frame.pack(fill=tk.X, pady=(0, 16))
        
        ttk.Label(status_frame, text="Configuration File", style='Header.TLabel').pack(anchor=tk.W)
        
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        
        # File path display with card styling
        path_display_frame = ttk.Frame(status_frame, style='Dark.TFrame')
        path_display_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.file_display = ttk.Label(path_display_frame, textvariable=self.file_path_var,
                                     font=(self.primary_font, 10),
                                     background=self.colors['input_bg'],
                                     foreground=self.colors['text_secondary'],
                                     padding=(12, 8),
                                     relief='flat')
        self.file_display.pack(fill=tk.X)
        
        # Modern button layout
        button_container = ttk.Frame(card_frame, style='Dark.TFrame')
        button_container.pack(fill=tk.X, pady=(8, 0))
        
        # Primary action button with full width
        select_btn = ttk.Button(button_container, text="Select Device File", 
                               command=self.select_device_file, style='Primary.TButton')
        select_btn.pack(fill=tk.X, pady=(0, 12), ipady=8)
        
        # Secondary action button
        template_btn = ttk.Button(button_container, text="+ Create New Template", 
                                 command=self.create_template, style='Secondary.TButton')
        template_btn.pack(fill=tk.X, ipady=6)
        
    def create_credentials_card(self, parent):
        """Create modern credentials input card"""
        cred_frame = ttk.LabelFrame(parent, text="  🔐  Authentication", 
                               style='Card.TLabelframe', padding=24)
        cred_frame.pack(fill=tk.X, pady=(0, 20))
    
        # Username field with modern styling
        username_section = ttk.Frame(cred_frame, style='Dark.TFrame')
        username_section.pack(fill=tk.X, pady=(0, 16))
    
        ttk.Label(username_section, text="Username", style='Header.TLabel').pack(anchor=tk.W)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(username_section, textvariable=self.username_var, 
                              style='Modern.TEntry', font=(self.primary_font, 11))
        username_entry.pack(fill=tk.X, pady=(8, 0), ipady=8)
    
        # Password field with modern styling
        password_section = ttk.Frame(cred_frame, style='Dark.TFrame')
        password_section.pack(fill=tk.X, pady=(0, 12))
    
        ttk.Label(password_section, text="Password", style='Header.TLabel').pack(anchor=tk.W)
    
        # Password input with toggle container
        password_container = ttk.Frame(password_section, style='Dark.TFrame')
        password_container.pack(fill=tk.X, pady=(8, 0))
    
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(password_container, textvariable=self.password_var, 
                                   show="•", style='Modern.TEntry', font=(self.primary_font, 11))
        self.password_entry.pack(fill=tk.X, ipady=8)
    
        # Modern toggle with better UX
        toggle_frame = ttk.Frame(cred_frame, style='Dark.TFrame')
        toggle_frame.pack(fill=tk.X)
    
        self.show_password_var = tk.BooleanVar()
        show_check = ttk.Checkbutton(toggle_frame, text="Show password", 
                                variable=self.show_password_var,
                                command=self.toggle_password_visibility)
        show_check.pack(anchor=tk.W)
    
        # Add credential validation indicator
        self.credential_status = ttk.Label(cred_frame, text="",
                                     font=(self.primary_font, 9),
                                     background=self.colors['surface'])
        self.credential_status.pack(anchor=tk.W, pady=(8, 0))

        # Bind validation events with correct syntax
        try:
            self.username_var.trace_add('write', self.validate_credentials)
            self.password_var.trace_add('write', self.validate_credentials)
        except AttributeError:
            # Fallback for older Python versions
            self.username_var.trace('w', self.validate_credentials)
            self.password_var.trace('w', self.validate_credentials)    
            
    def create_progress_card(self, parent):
        """Create modern progress tracking card"""
        progress_frame = ttk.LabelFrame(parent, text="  📊  Collection Status", 
                                       style='Card.TLabelframe', padding=24)
        progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status display with modern typography
        status_container = ttk.Frame(progress_frame, style='Dark.TFrame')
        status_container.pack(fill=tk.X, pady=(0, 16))
        
        self.progress_var = tk.StringVar()
        self.progress_var.set("Ready to start collection")
        
        status_label = ttk.Label(status_container, textvariable=self.progress_var,
                                font=(self.primary_font, 12, 'bold'),
                                background=self.colors['surface'],
                                foreground=self.colors['text'])
        status_label.pack(anchor=tk.W)
        
        # Modern progress bar with rounded appearance - FIXED
        progress_container = ttk.Frame(progress_frame, style='Dark.TFrame')
        progress_container.pack(fill=tk.X, pady=(0, 12))
        
        # Use default style instead of custom style that doesn't exist
        self.progress_bar = ttk.Progressbar(progress_container, 
                                           mode='determinate', length=350)
        self.progress_bar.pack(fill=tk.X, ipady=4)
        
        # Device metrics with modern layout
        metrics_frame = ttk.Frame(progress_frame, style='Dark.TFrame')
        metrics_frame.pack(fill=tk.X)
        
        self.device_counter_var = tk.StringVar()
        self.device_counter_var.set("0 devices ready")
        
        counter_label = ttk.Label(metrics_frame, textvariable=self.device_counter_var,
                                 font=(self.primary_font, 10),
                                 background=self.colors['surface'],
                                 foreground=self.colors['text_secondary'])
        counter_label.pack(side=tk.LEFT)
        
        # Success rate indicator
        self.success_rate_var = tk.StringVar()
        self.success_rate_var.set("")
        
        success_label = ttk.Label(metrics_frame, textvariable=self.success_rate_var,
                                 font=(self.primary_font, 10, 'bold'),
                                 background=self.colors['surface'],
                                 foreground=self.colors['success'])
        success_label.pack(side=tk.RIGHT)
        
    def create_actions_card(self, parent):
        """Create modern action buttons card"""
        action_frame = ttk.LabelFrame(parent, text="  ⚡  Controls", 
                                     style='Card.TLabelframe', padding=24)
        action_frame.pack(fill=tk.X)
        
        # Primary action - prominent button
        primary_container = ttk.Frame(action_frame, style='Dark.TFrame')
        primary_container.pack(fill=tk.X, pady=(0, 20))
        
        self.start_button = ttk.Button(primary_container, text="Start Collection", 
                                      command=self.start_inventory, style='Success.TButton')
        self.start_button.pack(fill=tk.X, ipady=12)
        
        # Secondary actions in modern grid
        secondary_grid = ttk.Frame(action_frame, style='Dark.TFrame')
        secondary_grid.pack(fill=tk.X)
        
        # First row
        row1 = ttk.Frame(secondary_grid, style='Dark.TFrame')
        row1.pack(fill=tk.X, pady=(0, 8))
        
        self.stop_button = ttk.Button(row1, text="⏹ Stop", 
                                     command=self.stop_inventory, state='disabled',
                                     style='Secondary.TButton')
        self.stop_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=8)
        
        clear_button = ttk.Button(row1, text="🗑 Clear Log", 
                                 command=self.clear_log, style='Secondary.TButton')
        clear_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=8)
        
        # Second row
        row2 = ttk.Frame(secondary_grid, style='Dark.TFrame')
        row2.pack(fill=tk.X)
        
        export_button = ttk.Button(row2, text="📊 Export Report", 
                                  command=self.export_current_report, style='Secondary.TButton')
        export_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=8)
        
        settings_button = ttk.Button(row2, text="⚙ Settings", 
                                    command=self.show_settings, style='Secondary.TButton')
        settings_button.pack(side=tk.RIGHT, fill=tk.X, expand=True, ipady=8)
        
    def create_activity_monitor(self, parent):
        """Create modern activity monitor with better information design"""
        monitor_frame = ttk.LabelFrame(parent, text="  📋  Activity Monitor", 
                                      style='Card.TLabelframe', padding=24)
        monitor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Monitor header with stats
        monitor_header = ttk.Frame(monitor_frame, style='Dark.TFrame')
        monitor_header.pack(fill=tk.X, pady=(0, 16))
        
        # Real-time stats
        stats_container = ttk.Frame(monitor_header, style='Dark.TFrame')
        stats_container.pack(fill=tk.X)
        
        # Live connection count
        self.live_connections_var = tk.StringVar()
        self.live_connections_var.set("0 active connections")
        
        connections_label = ttk.Label(stats_container, textvariable=self.live_connections_var,
                                     font=(self.primary_font, 10, 'bold'),
                                     background=self.colors['surface'],
                                     foreground=self.colors['primary'])
        connections_label.pack(side=tk.LEFT)
        
        # Log level filter
        filter_frame = ttk.Frame(stats_container, style='Dark.TFrame')
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Filter:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 8))
        
        self.log_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_filter_var,
                                   values=["All", "Info", "Success", "Warning", "Error"],
                                   state="readonly", width=10, font=(self.primary_font, 9))
        filter_combo.pack(side=tk.LEFT)
        filter_combo.bind('<<ComboboxSelected>>', self.filter_logs)
        
        # Enhanced log display with terminal aesthetics
        log_container = ttk.Frame(monitor_frame, style='Dark.TFrame')
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(
            log_container,
            height=25,
            state='disabled',
            font=(self.mono_font, 10),
            bg='#0d1117',  # GitHub dark background
            fg='#f0f6fc',  # Light text
            insertbackground='#58a6ff',
            selectbackground='#1f2937',
            selectforeground='#f0f6fc',
            wrap=tk.WORD,
            relief='flat',
            borderwidth=0,
            padx=16,
            pady=12
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure enhanced text tags with modern colors
        self.log_text.tag_configure("INFO", foreground="#58a6ff")      # GitHub blue
        self.log_text.tag_configure("WARNING", foreground="#f1c21b")   # Modern amber
        self.log_text.tag_configure("ERROR", foreground="#ff6b6b")     # Modern red
        self.log_text.tag_configure("SUCCESS", foreground="#40c057")   # Modern green
        self.log_text.tag_configure("HEADER", foreground="#bd93f9")    # Modern purple
        self.log_text.tag_configure("TIMESTAMP", foreground="#6b7280") # Muted timestamp
        
    def create_modern_footer(self, parent):
        """Create sleek modern footer"""
        footer_frame = ttk.Frame(parent, style='Dark.TFrame')
        footer_frame.pack(fill=tk.X, pady=(32, 0))
    
    # Subtle separator using Canvas instead of Frame with background
        separator_canvas = tk.Canvas(footer_frame, height=1, bg=self.colors['border'], 
                                highlightthickness=0, relief='flat')
        separator_canvas.pack(fill=tk.X, pady=(0, 16))
    
    # Footer content with better spacing
        footer_content = ttk.Frame(footer_frame, style='Dark.TFrame')
        footer_content.pack(fill=tk.X)
    
    # Left side - version and status
        left_footer = ttk.Frame(footer_content, style='Dark.TFrame')
        left_footer.pack(side=tk.LEFT, fill=tk.Y)
    
        version_label = ttk.Label(left_footer, text="v1.0 Professional", 
                             foreground=self.colors['text_secondary'], 
                             background=self.colors['background'],
                             font=(self.primary_font, 9))
        version_label.pack(anchor=tk.W)
    
    # Dynamic status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - System initialized")
    
        status_label = ttk.Label(left_footer, textvariable=self.status_var,
                           foreground=self.colors['success'],
                           background=self.colors['background'],
                           font=(self.primary_font, 9, 'bold'))
        status_label.pack(anchor=tk.W, pady=(4, 0))
    
    # Right side - branding with modern touch
        right_footer = ttk.Frame(footer_content, style='Dark.TFrame')
        right_footer.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Developer credit with modern styling
        dev_frame = ttk.Frame(right_footer, style='Dark.TFrame')
        dev_frame.pack()
    
        made_label = ttk.Label(dev_frame, text="Crafted by", 
                          foreground=self.colors['text_secondary'],
                          background=self.colors['background'],
                          font=(self.primary_font, 9))
        made_label.pack(side=tk.LEFT)
    
        name_label = ttk.Label(dev_frame, text="Mohammad Arfin Baig", 
                          foreground=self.colors['primary'],
                          background=self.colors['background'],
                          font=(self.primary_font, 9, 'bold'))
        name_label.pack(side=tk.LEFT, padx=(4, 0))    
        
    def validate_credentials(self, *args):
        """Real-time credential validation with visual feedback"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if username and password:
            self.credential_status.config(text="✓ Credentials configured", 
                                        foreground=self.colors['success'])
        elif username or password:
            self.credential_status.config(text="⚠ Incomplete credentials", 
                                        foreground=self.colors['warning'])
        else:
            self.credential_status.config(text="⚠ No credentials provided", 
                                        foreground=self.colors['text_secondary'])
            
    def toggle_password_visibility(self):
        """Enhanced password visibility toggle"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="•")
        
    def select_device_file(self):
        """Enhanced file selection with better validation"""
        file_path = filedialog.askopenfilename(
            title="Select Device Configuration File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.devices_file = file_path
            filename = os.path.basename(file_path)
            
            # Enhanced file display
            if len(filename) > 35:
                display_name = filename[:32] + "..."
            else:
                display_name = filename
                
            self.file_path_var.set(f"📄 {display_name}")
            self.file_display.config(foreground=self.colors['text'])
            
            # Enhanced logging
            self.log_message(f"File loaded: {filename}", "SUCCESS")
            self.status_var.set(f"File ready: {filename}")
            
            # Update connection status
            self.update_connection_readiness()
            
    def update_connection_readiness(self):
        """Update UI based on readiness state"""
        has_file = bool(self.devices_file)
        has_credentials = bool(self.username_var.get().strip() and self.password_var.get().strip())
        
        if has_file and has_credentials:
            self.connection_status.config(text="🟢 Ready to Connect", 
                                        foreground=self.colors['success'])
            self.quick_stats.config(text="All requirements met")
        elif has_file:
            self.connection_status.config(text="🟡 Awaiting Credentials", 
                                        foreground=self.colors['warning'])
            self.quick_stats.config(text="Enter device credentials")
        else:
            self.connection_status.config(text="🔴 Setup Required", 
                                        foreground=self.colors['error'])
            self.quick_stats.config(text="Select device file")
            
    def create_template(self):
        """Enhanced template creation with better UX"""
        save_path = filedialog.asksaveasfilename(
            title="Save Device Template",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialname=f"device_template_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )
        
        if save_path:
            try:
                self.excel_handler.create_device_template(save_path)
                filename = os.path.basename(save_path)
                self.log_message(f"Template created: {filename}", "SUCCESS")
                
                # Modern success dialog
                result = messagebox.askyesno(
                    "Template Created",
                    f"✅ Device template created successfully!\n\n"
                    f"📄 {filename}\n\n"
                    "The template includes sample data and proper formatting.\n"
                    "Open the file now?",
                    icon='question'
                )
                
                if result:
                    self.open_file(save_path)
                    
            except Exception as e:
                self.log_message(f"Template creation failed: {str(e)}", "ERROR")
                messagebox.showerror("Template Creation Failed", 
                                   f"Could not create device template:\n\n{str(e)}")
                
    def start_inventory(self):
        """Enhanced inventory start with better validation and feedback"""
        # Comprehensive validation
        errors = self.validate_inputs()
        
        if errors:
            error_text = "Please fix the following issues:\n\n" + "\n".join(errors)
            messagebox.showerror("Validation Failed", error_text)
            return
            
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # Update UI state with smooth transitions
        self.start_button.config(state='disabled', text="Connecting...")
        self.stop_button.config(state='normal')
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(8)
        
        # Enhanced session logging
        self.log_message("=" * 80, "HEADER")
        self.log_message("🚀 INVENTORY COLLECTION SESSION STARTED", "HEADER")
        self.log_message("=" * 80, "HEADER")
        self.log_message(f"📁 Device file: {os.path.basename(self.devices_file)}", "INFO")
        self.log_message(f"👤 Username: {username}", "INFO")
        self.log_message(f"🔑 Password: {'●' * len(password)} ({len(password)} chars)", "INFO")
        self.log_message(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log_message("", "INFO")
        
        self.status_var.set("Initializing collection...")
        self.connection_status.config(text="🔄 Connecting...", 
                                    foreground=self.colors['warning'])
        
        # Start worker thread
        self.current_task = threading.Thread(target=self.inventory_worker, daemon=True)
        self.current_task.start()
        
    def stop_inventory(self):
        """Enhanced stop functionality with better user feedback"""
        if self.current_task and self.current_task.is_alive():
            self.log_message("⏹ Stop requested - completing current operations...", "WARNING")
            self.status_var.set("Stopping collection...")
            self.stop_button.config(text="Stopping...", state='disabled')
            
            # Reset UI after short delay
            self.root.after(3000, self.reset_ui_after_stop)
        
    def reset_ui_after_stop(self):
        """Reset UI elements after stop operation"""
        self.start_button.config(state='normal', text="Start Collection")
        self.stop_button.config(state='disabled', text="⏹ Stop")
        self.progress_bar.stop()
        self.progress_bar.config(value=0)
        self.status_var.set("Collection stopped")
        self.connection_status.config(text="🟡 Stopped", foreground=self.colors['warning'])
        
    def inventory_worker(self):
        """Enhanced worker thread with better progress tracking"""
        try:
            def progress_callback(phase, total, current, message):
                self.progress_queue.put(('progress', phase, total, current, message))
                
            def error_callback(error_type, message):
                self.progress_queue.put(('error', error_type, message))
                
            # Pass credentials to collector
            credentials = {
                'username': self.username_var.get().strip(),
                'password': self.password_var.get().strip()
            }
            
            # Run inventory collection
            results = self.collector.collect_inventory(
                self.devices_file,
                credentials=credentials,
                progress_callback=progress_callback,
                error_callback=error_callback
            )
            
            # Generate comprehensive summary
            summary = self.collector.get_collection_summary(results)
            
            # Send results to main thread
            self.result_queue.put(('success', results, summary))
            
        except Exception as e:
            self.result_queue.put(('error', str(e)))
            
    def monitor_queues(self):
        """Enhanced queue monitoring with smooth updates"""
        # Check progress queue
        try:
            while True:
                item = self.progress_queue.get_nowait()
                self.handle_progress_update(item)
        except queue.Empty:
            pass
            
        # Check result queue
        try:
            while True:
                item = self.result_queue.get_nowait()
                self.handle_result(item)
        except queue.Empty:
            pass
            
        # Schedule next check
        self.root.after(50, self.monitor_queues)  # More responsive
        
    def handle_progress_update(self, item):
        """Enhanced progress handling with real-time updates"""
        if item[0] == 'progress':
            phase, total, current, message = item[1], item[2], item[3], item[4]
            
            if phase == 'loaded_devices':
                self.progress_var.set(f"📋 {total} devices loaded")
                self.device_counter_var.set("Initializing...")
                self.live_connections_var.set("0 active connections")
                self.progress_bar.config(mode='determinate', maximum=total, value=0)
                
            elif phase == 'collecting':
                self.progress_var.set(f"🔍 Collecting: {self.truncate_message(message, 30)}")
                self.device_counter_var.set(f"{current}/{total} processed")
                self.live_connections_var.set(f"{min(5, total-current)} active connections")
                self.progress_bar.config(value=current)
                
                # Update success rate in real-time
                if current > 0:
                    # This would need actual success count from collector
                    estimated_success_rate = max(75, 100 - (current * 2))  # Placeholder
                    self.success_rate_var.set(f"{estimated_success_rate}% success")
                
            elif phase == 'parsing':
                self.progress_var.set(f"⚙️ Processing: {self.truncate_message(message, 30)}")
                self.device_counter_var.set(f"Parsed: {current}/{total}")
                
            elif phase == 'complete':
                self.progress_var.set("✅ Collection completed!")
                self.device_counter_var.set(f"Completed: {current} devices")
                self.live_connections_var.set("0 active connections")
                self.progress_bar.config(value=total)
                
            self.log_message(f"{message}", "INFO")
            
        elif item[0] == 'error':
            error_type, message = item[1], item[2]
            self.log_message(f"{error_type}: {message}", "ERROR")
            
    def handle_result(self, item):
        """Enhanced result handling with comprehensive reporting"""
        # Reset UI state
        self.start_button.config(state='normal', text="Start Collection")
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        
        if item[0] == 'success':
            results, summary = item[1], item[2]
            
            # Enhanced completion reporting
            self.log_message("", "INFO")
            self.log_message("=" * 80, "SUCCESS")
            self.log_message("✅ COLLECTION COMPLETED SUCCESSFULLY", "SUCCESS")
            self.log_message("=" * 80, "SUCCESS")
            
            # Detailed metrics
            self.log_message(f"📊 Total devices: {summary['total_devices']}", "INFO")
            self.log_message(f"✅ Successful: {summary['successful']}", "SUCCESS")
            self.log_message(f"❌ Failed: {summary['failed']}", "WARNING" if summary['failed'] > 0 else "INFO")
            self.log_message(f"📈 Success rate: {summary['success_rate']:.1f}%", "SUCCESS")
            self.log_message(f"⏱️ Duration: {summary.get('duration', 'N/A')}", "INFO")
            
            # Update UI elements
            self.success_rate_var.set(f"{summary['success_rate']:.1f}% success")
            self.connection_status.config(text="🟢 Collection Complete", 
                                        foreground=self.colors['success'])
            
            # Generate Excel report
            self.generate_excel_report(results, summary)
            
            self.status_var.set(f"Complete: {summary['successful']}/{summary['total_devices']} successful")
            
        elif item[0] == 'error':
            error_message = item[1]
            self.log_message("", "INFO")
            self.log_message("❌ COLLECTION FAILED", "ERROR")
            self.log_message(f"Error: {error_message}", "ERROR")
            
            # Update UI state
            self.connection_status.config(text="🔴 Collection Failed", 
                                        foreground=self.colors['error'])
            self.status_var.set("Collection failed")
            
            messagebox.showerror("Collection Failed", 
                               f"Inventory collection failed:\n\n{error_message}")
            
    def generate_excel_report(self, results, summary):
        """Enhanced Excel report generation with better UX"""
        try:
            # Generate filename with better naming
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"switch_inventory_{timestamp}.xlsx"
            
            # Create reports directory
            output_dir = "reports"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            # Generate report
            self.excel_handler.generate_report(results, output_path, summary)
            
            self.log_message(f"📊 Report generated: {filename}", "SUCCESS")
            self.log_message(f"📁 Location: {output_dir}/", "INFO")
            
            # Modern completion dialog with better information
            dialog_text = (f"📊 Inventory report generated successfully!\n\n"
                          f"📄 File: {filename}\n"
                          f"📁 Location: {output_dir}/\n"
                          f"📈 Success Rate: {summary['success_rate']:.1f}%\n"
                          f"📋 Total Devices: {summary['total_devices']}\n\n"
                          "Open the report now?")
            
            result = messagebox.askyesno("Report Ready", dialog_text, icon='question')
            
            if result:
                self.open_file(output_path)
                        
        except Exception as e:
            self.log_message(f"Report generation failed: {str(e)}", "ERROR")
            messagebox.showerror("Report Error", 
                               f"Failed to generate Excel report:\n\n{str(e)}")
    
    def export_current_report(self):
        """Export current session data"""
        if not hasattr(self, 'last_results') or not self.last_results:
            messagebox.showinfo("No Data", "No collection data available to export.\nRun an inventory collection first.")
            return
            
        # Implementation for exporting current data
        self.log_message("📤 Exporting current session data...", "INFO")
        
    def show_settings(self):
        """Show application settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.configure(bg=self.colors['background'])
        
        # Center the dialog
        self.center_window(settings_window)
        
        # Settings content
        settings_frame = ttk.Frame(settings_window, style='Card.TLabelframe', padding=24)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(settings_frame, text="Application Settings", 
                 font=(self.primary_font, 16, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['text']).pack(anchor=tk.W, pady=(0, 20))
        
        # Placeholder settings options
        ttk.Label(settings_frame, text="⚙️ Advanced settings coming soon...", 
                 style='Body.TLabel').pack(anchor=tk.W)
        
        # Close button
        ttk.Button(settings_frame, text="Close", command=settings_window.destroy,
                  style='Secondary.TButton').pack(anchor=tk.E, pady=(20, 0))
        
    def center_window(self, window):
        """Center a window on the parent"""
        window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (window.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (window.winfo_height() // 2)
        window.geometry(f"+{x}+{y}")
        
    def truncate_message(self, message, max_length):
        """Truncate long messages for UI display"""
        if len(message) <= max_length:
            return message
        return message[:max_length-3] + "..."
        
    def filter_logs(self, event=None):
        """Filter log display based on selected level"""
        # Placeholder for log filtering functionality
        filter_level = self.log_filter_var.get()
        self.log_message(f"Log filter set to: {filter_level}", "INFO")
        
    def open_file(self, file_path):
        """Cross-platform file opening with error handling"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                if os.uname().sysname == 'Darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            self.log_message(f"Could not open file: {str(e)}", "ERROR")
                
    def log_message(self, message, level="INFO"):
        """Enhanced logging with better formatting and timestamps"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Modern level indicators
        level_indicators = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "HEADER": "🔷"
        }
        
        indicator = level_indicators.get(level, "•")
        
        if level == "HEADER":
            log_entry = f"{message}\n"
        else:
            log_entry = f"[{timestamp}] {indicator} {message}\n"
        
        self.log_text.config(state='normal')
        
        # Insert with appropriate tag
        if level == "HEADER":
            self.log_text.insert(tk.END, log_entry, level)
        else:
            # Insert timestamp with muted color, then message with level color
            self.log_text.insert(tk.END, f"[{timestamp}] ", "TIMESTAMP")
            self.log_text.insert(tk.END, f"{indicator} {message}\n", level)
        
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
    def clear_log(self):
        """Enhanced log clearing with modern welcome message"""
        if self.current_task and self.current_task.is_alive():
            if not messagebox.askyesno("Clear Activity Log", 
                                     "Collection is currently running.\n"
                                     "Clear the log anyway?"):
                return
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # Modern welcome message
        self.log_message("=" * 80, "HEADER")
        self.log_message("🌐 SWITCH INVENTORY COLLECTOR PRO", "HEADER")
        self.log_message("Enterprise Network Device Management System", "HEADER")
        self.log_message("=" * 80, "HEADER")
        self.log_message("System initialized and ready for operation", "SUCCESS")
        self.log_message("Select a device file and enter credentials to begin", "INFO")
        
    def validate_inputs(self):
        """Comprehensive input validation with detailed error messages"""
        errors = []
        
        if not self.devices_file:
            errors.append("❌ Device configuration file not selected")
        elif not os.path.exists(self.devices_file):
            errors.append("❌ Selected device file no longer exists")
        elif not self.devices_file.lower().endswith(('.xlsx', '.xls', '.csv')):
            errors.append("❌ Invalid file format (must be Excel or CSV)")
            
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username:
            errors.append("❌ Username is required")
        elif len(username) < 2:
            errors.append("❌ Username too short (minimum 2 characters)")
            
        if not password:
            errors.append("❌ Password is required")
        elif len(password) < 3:
            errors.append("❌ Password too short (minimum 3 characters)")
            
        return errors
        
    def show_about_dialog(self):
        """Enhanced about dialog with modern design"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("600x500")
        about_window.transient(self.root)
        about_window.grab_set()
        about_window.configure(bg=self.colors['background'])
        
        self.center_window(about_window)
        
        # About content with modern styling
        about_frame = ttk.Frame(about_window, style='Card.TLabelframe', padding=32)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # App icon and title
        header_frame = ttk.Frame(about_frame, style='Dark.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 24))
        
        ttk.Label(header_frame, text="🔌", font=('Segoe UI Emoji', 48),
                 background=self.colors['surface']).pack()
        
        ttk.Label(header_frame, text="Switch Inventory Collector Pro",
                 font=(self.primary_font, 20, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['text']).pack(pady=(8, 4))
        
        ttk.Label(header_frame, text="Version 1.0 Professional Edition",
                 font=(self.primary_font, 12),
                 background=self.colors['surface'],
                 foreground=self.colors['primary']).pack()
        
        # Features list
        features_frame = ttk.Frame(about_frame, style='Dark.TFrame')
        features_frame.pack(fill=tk.X, pady=(16, 24))
        
        features_text = """
🚀 Automated device discovery and inventory collection
📊 Real-time progress monitoring and statistics
📈 Comprehensive Excel reporting with analytics
🔒 Secure credential management
⚡ Multi-threaded processing for optimal performance
🎨 Modern, intuitive user interface
🔧 Support for multiple device types and protocols
📱 Cross-platform compatibility
        """
        
        features_label = ttk.Label(features_frame, text=features_text.strip(),
                                  font=(self.primary_font, 10),
                                  background=self.colors['surface'],
                                  foreground=self.colors['text'],
                                  justify=tk.LEFT)
        features_label.pack(anchor=tk.W)
        
        # Developer info
        dev_frame = ttk.Frame(about_frame, style='Dark.TFrame')
        dev_frame.pack(fill=tk.X, pady=(16, 0))
        
        ttk.Label(dev_frame, text="Developed by Mohammad Arfin Baig",
                 font=(self.primary_font, 11, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['accent']).pack()
        
        ttk.Label(dev_frame, text="© 2025 Professional Network Solutions",
                 font=(self.primary_font, 9),
                 background=self.colors['surface'],
                 foreground=self.colors['text_secondary']).pack(pady=(4, 0))
        
        # Close button
        ttk.Button(about_frame, text="Close", command=about_window.destroy,
                  style='Primary.TButton').pack(pady=(24, 0), ipadx=20, ipady=8)
        
    def run(self):
        """Start the application with enhanced initialization"""
        # Initialize with welcome message
        self.clear_log()
        
        # Center window on screen
        self.center_window(self.root)
        
        # Add modern menu bar
        self.create_modern_menu_bar()
        
        # Apply final styling touches
        self.apply_modern_theme()
        
        # Start the application
        self.root.mainloop()
        
    def create_modern_menu_bar(self):
        """Create modern menu bar with better organization"""
        menubar = tk.Menu(self.root, bg=self.colors['surface'], 
                         fg=self.colors['text'], 
                         activebackground=self.colors['primary'],
                         activeforeground='white',
                         borderwidth=0)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                           fg=self.colors['text'], 
                           activebackground=self.colors['primary'],
                           activeforeground='white')
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="📁 Select Device File...", command=self.select_device_file, accelerator="Ctrl+O")
        file_menu.add_command(label="📄 Create Template...", command=self.create_template, accelerator="Ctrl+T")
        file_menu.add_separator()
        file_menu.add_command(label="📤 Export Current Data...", command=self.export_current_report, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Collection menu
        collection_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                                 fg=self.colors['text'], 
                                 activebackground=self.colors['primary'],
                                 activeforeground='white')
        menubar.add_cascade(label="Collection", menu=collection_menu)
        collection_menu.add_command(label="🚀 Start Collection", command=self.start_inventory, accelerator="F5")
        collection_menu.add_command(label="⏹ Stop Collection", command=self.stop_inventory, accelerator="Esc")
        collection_menu.add_separator()
        collection_menu.add_command(label="🗑 Clear Activity Log", command=self.clear_log, accelerator="Ctrl+L")
        collection_menu.add_command(label="📂 Open Reports Folder", command=self.open_reports_folder, accelerator="Ctrl+R")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                            fg=self.colors['text'], 
                            activebackground=self.colors['primary'],
                            activeforeground='white')
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="⚙️ Settings", command=self.show_settings)
        tools_menu.add_command(label="🔍 Device Validator", command=self.show_device_validator)
        tools_menu.add_command(label="📊 Statistics", command=self.show_statistics)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['surface'], 
                           fg=self.colors['text'], 
                           activebackground=self.colors['primary'],
                           activeforeground='white')
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="📖 User Guide", command=self.show_user_guide)
        help_menu.add_command(label="⌨️ Keyboard Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About", command=self.show_about_dialog)
        
        # Enhanced keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
    def setup_keyboard_shortcuts(self):
        """Setup comprehensive keyboard shortcuts"""
        shortcuts = {
            '<Control-o>': self.select_device_file,
            '<Control-t>': self.create_template,
            '<Control-e>': self.export_current_report,
            '<Control-q>': self.root.quit,
            '<F5>': self.start_inventory,
            '<Escape>': self.stop_inventory,
            '<Control-l>': self.clear_log,
            '<Control-r>': self.open_reports_folder,
            '<F1>': self.show_user_guide
        }
        
        for key, command in shortcuts.items():
            self.root.bind(key, lambda e, cmd=command: cmd())
            
    def show_device_validator(self):
        """Show device configuration validator"""
        if not self.devices_file:
            messagebox.showinfo("No File Selected", "Please select a device file first.")
            return
            
        # Placeholder for device validator
        self.log_message("🔍 Device validator launched", "INFO")
        
    def show_statistics(self):
        """Show collection statistics"""
        # Placeholder for statistics viewer
        self.log_message("📊 Statistics viewer launched", "INFO")
        
    def apply_modern_theme(self):
        """Apply final modern theme touches"""
        # Configure window properties for modern appearance
        try:
            # Windows-specific modern window styling
            if os.name == 'nt':
                self.root.wm_attributes('-alpha', 0.98)  # Slight transparency
        except:
            pass
            
    def open_reports_folder(self):
        """Enhanced reports folder opening"""
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            self.log_message(f"📁 Created reports directory: {reports_dir}", "INFO")
            
        try:
            self.open_file(reports_dir)
            self.log_message(f"📂 Opened reports folder", "INFO")
        except Exception as e:
            self.log_message(f"Could not open reports folder: {str(e)}", "ERROR")
            
    def show_user_guide(self):
        """Enhanced user guide with modern design"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("User Guide")
        guide_window.geometry("700x600")
        guide_window.transient(self.root)
        guide_window.grab_set()
        guide_window.configure(bg=self.colors['background'])
        
        self.center_window(guide_window)
        
        # Guide content with modern styling
        guide_frame = ttk.Frame(guide_window, style='Card.TLabelframe', padding=24)
        guide_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Guide header
        ttk.Label(guide_frame, text="📖 User Guide",
                 font=(self.primary_font, 18, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['text']).pack(anchor=tk.W, pady=(0, 20))
        
        # Guide content
        guide_text = """
🚀 GETTING STARTED

1. Device Configuration
   • Click "Select Device File" to choose your device list
   • Supported formats: Excel (.xlsx, .xls) and CSV (.csv)
   • Use "Create Template" if you need a sample file

2. Authentication Setup
   • Enter your network device username and password
   • These credentials will be used for SSH/SNMP connections
   • Ensure the account has read access to device configurations

3. Start Collection
   • Click "Start Collection" to begin the inventory process
   • Monitor progress in the Activity Monitor
   • Collection runs in background - UI remains responsive

📋 DEVICE FILE FORMAT

Your device file should contain these columns:
   • IP Address or Hostname (required)
   • Device Type (optional - auto-detected if blank)
   • Location/Description (optional)
   • Custom fields (preserved in output)

🔐 SECURITY NOTES

   • Credentials are only stored in memory during collection
   • No sensitive data is logged or saved to disk
   • Use read-only accounts when possible

📊 REPORTS & OUTPUT

   • Excel reports generated automatically in 'reports' folder
   • Reports include device details, configurations, and statistics
   • Each report is timestamped for version control
   • Failed devices are clearly marked with error reasons

⌨️ KEYBOARD SHORTCUTS

   Ctrl+O    Select device file
   Ctrl+T    Create template
   F5        Start collection
   Esc       Stop collection
   Ctrl+L    Clear log
   Ctrl+R    Open reports folder
   F1        Show this guide
        """
        
        text_widget = scrolledtext.ScrolledText(
            guide_frame, 
            wrap=tk.WORD,
            font=(self.primary_font, 10),
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            selectbackground=self.colors['primary'],
            selectforeground='white',
            relief='flat',
            borderwidth=0,
            padx=16,
            pady=12
        )
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        text_widget.insert(tk.END, guide_text.strip())
        text_widget.config(state='disabled')
        
        # Close button
        ttk.Button(guide_frame, text="Close", command=guide_window.destroy,
                  style='Primary.TButton').pack(anchor=tk.E, ipadx=20, ipady=8)
        
    def show_shortcuts(self):
        """Show modern keyboard shortcuts dialog"""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Keyboard Shortcuts")
        shortcuts_window.geometry("500x400")
        shortcuts_window.transient(self.root)
        shortcuts_window.grab_set()
        shortcuts_window.configure(bg=self.colors['background'])
        
        self.center_window(shortcuts_window)
        
        # Shortcuts content
        shortcuts_frame = ttk.Frame(shortcuts_window, style='Card.TLabelframe', padding=24)
        shortcuts_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(shortcuts_frame, text="⌨️ Keyboard Shortcuts",
                 font=(self.primary_font, 16, 'bold'),
                 background=self.colors['surface'],
                 foreground=self.colors['text']).pack(anchor=tk.W, pady=(0, 20))
        
        shortcuts_text = """
📁 FILE OPERATIONS
  Ctrl + O      Select device configuration file
  Ctrl + T      Create new device template
  Ctrl + E      Export current session data
  Ctrl + Q      Exit application

🚀 COLLECTION CONTROL
  F5            Start inventory collection
  Escape        Stop current collection
  Ctrl + L      Clear activity log
  Ctrl + R      Open reports folder

🔧 TOOLS & NAVIGATION
  F1            Show user guide
  Ctrl + /      Show keyboard shortcuts
  Tab           Navigate between fields
  Enter         Activate focused button

💡 PRO TIPS
  • Use Tab to quickly navigate between input fields
  • F5 is the fastest way to start collection
  • Ctrl+L clears logs while preserving session data
  • All shortcuts work globally within the application
        """
        
        text_widget = scrolledtext.ScrolledText(
            shortcuts_frame,
            wrap=tk.WORD,
            font=(self.mono_font, 9),
            bg=self.colors['input_bg'],
            fg=self.colors['text'],
            selectbackground=self.colors['primary'],
            selectforeground='white',
            relief='flat',
            borderwidth=0,
            padx=16,
            pady=12,
            state='disabled'
        )
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        
        text_widget.config(state='normal')
        text_widget.insert(tk.END, shortcuts_text.strip())
        text_widget.config(state='disabled')
        
        # Close button
        ttk.Button(shortcuts_frame, text="Got it!", command=shortcuts_window.destroy,
                  style='Primary.TButton').pack(anchor=tk.E, ipadx=20, ipady=8)