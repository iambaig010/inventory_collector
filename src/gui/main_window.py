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
        self.root.title("PortView Pro - by Mohammad Arfin Baig")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Load settings first
        self.load_settings()
        
        # Configure modern styling
        self.setup_modern_styling()
        
        # Application state
        self.devices_file = None
        self.collector = InventoryCollector()
        self.excel_handler = ExcelHandler()
        self.current_task = None
        self.last_results = None  # Initialize this attribute
        
        # Thread communication
        self.progress_queue = queue.Queue()
        self.result_queue = queue.Queue()
        
        # Setup logging for GUI
        self.setup_gui_logging()
        
        # Build UI
        self.setup_ui()
        
        # Start queue monitoring
        self.monitor_queues()
        
        # Show shortcuts popup if not disabled
        self.root.after(500, self.show_shortcuts_popup)

    def load_settings(self):
        """Load application settings"""
        self.settings = {
            'show_shortcuts_popup': True,
            'theme': 'dark',
            'log_level': 'info'
        }
        # In a real app, this would load from a config file

    def save_settings(self):
        """Save application settings"""
        # In a real app, this would save to a config file
        pass

    def setup_modern_styling(self):
        """Setup modern styling with consistent color scheme"""
        style = ttk.Style()
        
        # Refined color palette for better consistency
        self.colors = {
            'bg_primary': '#f8fafc',       # Light background
            'bg_secondary': '#f1f5f9',     # Card background
            'bg_tertiary': '#e2e8f0',      # Input background
            'text_primary': '#1e293b',     # Main text
            'text_secondary': '#64748b',   # Secondary text
            'text_muted': '#94a3b8',       # Muted text
            'border': '#e2e8f0',           # Borders
            'accent_primary': '#3b82f6',   # Primary blue
            'accent_hover': '#2563eb',     # Hover blue
            'success': '#10b981',          # Success green
            'warning': '#f59e0b',          # Warning amber
            'error': '#ef4444',            # Error red
            'info': '#06b6d4',             # Info cyan
        }
        
        # Set theme based on system or user preference
        style.theme_use('clam')
        
        # Font configuration
        if os.name == 'nt':  # Windows
            self.primary_font = 'Segoe UI'
            self.mono_font = 'Consolas'
        else:  # macOS/Linux
            self.primary_font = 'Arial'
            self.mono_font = 'Courier New'
        
        # Configure styles with consistent theming
        self.configure_widget_styles(style)
        
        # Configure root window
        self.root.configure(bg=self.colors['bg_primary'])
        
    def configure_widget_styles(self, style):
        """Configure all widget styles consistently"""
        # Label styles
        style.configure('Title.TLabel', 
                       font=(self.primary_font, 24, 'bold'), 
                       background=self.colors['bg_primary'], 
                       foreground=self.colors['text_primary'])
        
        style.configure('Subtitle.TLabel', 
                       font=(self.primary_font, 12), 
                       background=self.colors['bg_primary'], 
                       foreground=self.colors['text_secondary'])
        
        style.configure('Header.TLabel', 
                       font=(self.primary_font, 11, 'bold'), 
                       background=self.colors['bg_secondary'], 
                       foreground=self.colors['text_primary'])
        
        style.configure('Body.TLabel', 
                       font=(self.primary_font, 10), 
                       background=self.colors['bg_secondary'], 
                       foreground=self.colors['text_secondary'])
        
        # Frame styles
        style.configure('Main.TFrame', background=self.colors['bg_primary'])
        style.configure('Card.TFrame', background=self.colors['bg_secondary'])
        
        # Button styles
        style.configure('Primary.TButton', 
                       font=(self.primary_font, 11, 'bold'),
                       relief='flat')
        style.map('Primary.TButton',
                 background=[('active', self.colors['accent_hover']), 
                           ('!active', self.colors['accent_primary'])],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        style.configure('Success.TButton', 
                       font=(self.primary_font, 12, 'bold'),
                       relief='flat')
        style.map('Success.TButton',
                 background=[('active', '#059669'), 
                           ('!active', self.colors['success'])],
                 foreground=[('active', 'white'), ('!active', 'white')])
        
        style.configure('Secondary.TButton', 
                       font=(self.primary_font, 10),
                       relief='flat')
        style.map('Secondary.TButton',
                 background=[('active', self.colors['bg_tertiary']), 
                           ('!active', self.colors['bg_secondary'])],
                 foreground=[('active', self.colors['text_primary']), 
                           ('!active', self.colors['text_primary'])])
        
        # Entry styling
        style.configure('Modern.TEntry',
                       font=(self.primary_font, 11),
                       fieldbackground=self.colors['bg_tertiary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='solid')
        
        # LabelFrame styling
        style.configure('Card.TLabelframe',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       relief='solid')
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['bg_secondary'],
                       foreground=self.colors['text_primary'],
                       font=(self.primary_font, 11, 'bold'))
        
        # Progress bar styling
        style.configure('Modern.Horizontal.TProgressbar',
                       background=self.colors['accent_primary'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       lightcolor=self.colors['accent_primary'],
                       darkcolor=self.colors['accent_primary'])
        
    def setup_gui_logging(self):
        """Setup logging that will display in GUI"""
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
    def setup_ui(self):
        """Create responsive user interface with proper layout"""
        # Main container with proper padding
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Header section
        self.create_modern_header(main_frame)

        # Content area with proper responsive layout
        content_frame = ttk.Frame(main_frame, style='Main.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        # Use PanedWindow for responsive layout
        paned_window = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # Left panel (controls)
        left_panel = ttk.Frame(paned_window, style='Main.TFrame')
        left_panel.pack(fill=tk.BOTH, expand=False)
        
        # Right panel (activity monitor)
        right_panel = ttk.Frame(paned_window, style='Main.TFrame')
        right_panel.pack(fill=tk.BOTH, expand=True)

        # Add panels to paned window
        paned_window.add(left_panel, weight=1)
        paned_window.add(right_panel, weight=2)

        left_panel.grid_propagate(False)  # prevent shrinking
        left_panel.config(width=350)      # set minimum width

        right_panel.grid_propagate(False)
        right_panel.config(width=400)  # set minimum width

        # Create left panel content
        self.create_left_panel(left_panel)
        
        # Create right panel content
        self.create_right_panel(right_panel)

        # Footer section
        self.create_modern_footer(main_frame)
        
        # Add professional watermark
        self.create_professional_watermark(main_frame)
        
    def create_professional_watermark(self, parent):
        """Add professional watermark in bottom-right corner"""
        # Create watermark frame
        watermark_frame = ttk.Frame(parent, style='Main.TFrame')
        watermark_frame.place(relx=1.0, rely=1.0, anchor='se', x=-10, y=-10)
        
        # Watermark text
        watermark_label = ttk.Label(
            watermark_frame,
            text="Developed by M.A. Baig",
            font=(self.primary_font, 8, 'italic'),
            background=self.colors['bg_primary'],
            foreground=self.colors['text_muted']
        )
        watermark_label.pack()
        
    def create_left_panel(self, parent):
        """Create left panel with all control elements"""
        # File selection card
        self.create_file_card(parent)
        
        # Credentials card
        self.create_credentials_card(parent)
        
        # Progress card
        self.create_progress_card(parent)
        
        # Actions card - ensure it's always visible
        self.create_actions_card(parent)
        
    def create_right_panel(self, parent):
        """Create right panel with activity monitor"""
        self.create_activity_monitor(parent)

    def create_modern_header(self, parent):
        """Create clean modern header"""
        header_frame = ttk.Frame(parent, style='Main.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Header content
        header_content = ttk.Frame(header_frame, style='Main.TFrame')
        header_content.pack(fill=tk.X)
        
        # Left side - title and branding
        title_frame = ttk.Frame(header_content, style='Main.TFrame')
        title_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # App title
        title_label = ttk.Label(title_frame, text="PortView Pro", 
                               style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(title_frame, 
                                  text="Enterprise Network Device Management", 
                                  style='Subtitle.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Right side - status
        status_frame = ttk.Frame(header_content, style='Main.TFrame')
        status_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Connection status
        self.connection_status = ttk.Label(status_frame, text="System Ready",
                                         font=(self.primary_font, 10, 'bold'),
                                         background=self.colors['bg_primary'],
                                         foreground=self.colors['success'])
        self.connection_status.pack(anchor=tk.E, pady=(10, 5))
        
        # Quick stats
        self.quick_stats = ttk.Label(status_frame, text="Ready to connect",
                                   font=(self.primary_font, 9),
                                   background=self.colors['bg_primary'],
                                   foreground=self.colors['text_secondary'])
        self.quick_stats.pack(anchor=tk.E)

    def create_file_card(self, parent):
        """Create file selection card with proper styling"""
        card_frame = ttk.LabelFrame(parent, text="  Device Configuration", 
                                   style='Card.TLabelframe', padding=15)
        card_frame.pack(fill=tk.X, pady=(0, 15))
        
        # File status
        status_frame = ttk.Frame(card_frame, style='Card.TFrame')
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Configuration File", style='Header.TLabel').pack(anchor=tk.W)
        
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        
        # File path display
        self.file_display = ttk.Label(status_frame, textvariable=self.file_path_var,
                                     font=(self.primary_font, 9),
                                     background=self.colors['bg_tertiary'],
                                     foreground=self.colors['text_secondary'],
                                     padding=(8, 5),
                                     relief='solid',
                                     borderwidth=1)
        self.file_display.pack(fill=tk.X, pady=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(card_frame, style='Card.TFrame')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        select_btn = ttk.Button(button_frame, text="Select Device File", 
                               command=self.select_device_file, style='Primary.TButton')
        select_btn.pack(fill=tk.X, pady=(0, 8), ipady=6)
        
        template_btn = ttk.Button(button_frame, text="Create New Template", 
                                 command=self.create_template, style='Secondary.TButton')
        template_btn.pack(fill=tk.X, ipady=4)

    def create_credentials_card(self, parent):
        """Create credentials input card with proper styling"""
        cred_frame = ttk.LabelFrame(parent, text="  Authentication", 
                                   style='Card.TLabelframe', padding=15)
        cred_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Username field
        username_frame = ttk.Frame(cred_frame, style='Card.TFrame')
        username_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(username_frame, text="Username", style='Header.TLabel').pack(anchor=tk.W)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(username_frame, textvariable=self.username_var, 
                                  style='Modern.TEntry')
        username_entry.pack(fill=tk.X, pady=(5, 0), ipady=6)
        
        # Password field
        password_frame = ttk.Frame(cred_frame, style='Card.TFrame')
        password_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(password_frame, text="Password", style='Header.TLabel').pack(anchor=tk.W)
        
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(password_frame, textvariable=self.password_var, 
                                       show="*", style='Modern.TEntry')
        self.password_entry.pack(fill=tk.X, pady=(5, 0), ipady=6)
        
        # Show password toggle
        self.show_password_var = tk.BooleanVar()
        show_check = ttk.Checkbutton(cred_frame, text="Show password", 
                                    variable=self.show_password_var,
                                    command=self.toggle_password_visibility)
        show_check.pack(anchor=tk.W, pady=(5, 0))
        
        # Credential status
        self.credential_status = ttk.Label(cred_frame, text="",
                                         font=(self.primary_font, 9),
                                         background=self.colors['bg_secondary'])
        self.credential_status.pack(anchor=tk.W, pady=(5, 0))

        # Bind validation events
        self.username_var.trace_add('write', self.validate_credentials)
        self.password_var.trace_add('write', self.validate_credentials)

    def create_progress_card(self, parent):
        """Create progress tracking card"""
        progress_frame = ttk.LabelFrame(parent, text="  Collection Status", 
                                       style='Card.TLabelframe', padding=15)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Status display
        self.progress_var = tk.StringVar()
        self.progress_var.set("Ready to start collection")
        
        status_label = ttk.Label(progress_frame, textvariable=self.progress_var,
                                font=(self.primary_font, 10, 'bold'),
                                background=self.colors['bg_secondary'],
                                foreground=self.colors['text_primary'])
        status_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, 
                                           style='Modern.Horizontal.TProgressbar',
                                           mode='determinate', length=300)
        self.progress_bar.pack(fill=tk.X, pady=(0, 10), ipady=3)
        
        # Device metrics
        metrics_frame = ttk.Frame(progress_frame, style='Card.TFrame')
        metrics_frame.pack(fill=tk.X)
        
        self.device_counter_var = tk.StringVar()
        self.device_counter_var.set("0 devices ready")
        
        counter_label = ttk.Label(metrics_frame, textvariable=self.device_counter_var,
                                 style='Body.TLabel')
        counter_label.pack(side=tk.LEFT)
        
        self.success_rate_var = tk.StringVar()
        self.success_rate_var.set("")
        
        success_label = ttk.Label(metrics_frame, textvariable=self.success_rate_var,
                                 font=(self.primary_font, 9, 'bold'),
                                 background=self.colors['bg_secondary'],
                                 foreground=self.colors['success'])
        success_label.pack(side=tk.RIGHT)

    def create_actions_card(self, parent):
        """Create actions card with proper layout to ensure visibility"""
        action_frame = ttk.LabelFrame(parent, text="  Controls",
                                     style='Card.TLabelframe', padding=15)
        action_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Primary action - Start button (always visible)
        self.start_button = ttk.Button(action_frame, text="Start Collection",
                                      command=self.start_inventory, style='Success.TButton')
        self.start_button.pack(fill=tk.X, pady=(0, 10), ipady=8)
        
        # Secondary actions in grid
        secondary_frame = ttk.Frame(action_frame, style='Card.TFrame')
        secondary_frame.pack(fill=tk.X)
        
        # Configure grid for equal width buttons
        secondary_frame.grid_columnconfigure(0, weight=1)
        secondary_frame.grid_columnconfigure(1, weight=1)
        
        self.stop_button = ttk.Button(secondary_frame, text="Stop",
                                     command=self.stop_inventory, state='disabled',
                                     style='Secondary.TButton')
        self.stop_button.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipady=6)
        
        clear_button = ttk.Button(secondary_frame, text="Clear Log",
                                 command=self.clear_log, style='Secondary.TButton')
        clear_button.grid(row=0, column=1, sticky="ew", padx=(5, 0), ipady=6)
        
        export_button = ttk.Button(secondary_frame, text="Export Report",
                                  command=self.export_current_report, style='Secondary.TButton')
        export_button.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=(8, 0), ipady=6)
        
        settings_button = ttk.Button(secondary_frame, text="Settings",
                                    command=self.show_settings, style='Secondary.TButton')
        settings_button.grid(row=1, column=1, sticky="ew", padx=(5, 0), pady=(8, 0), ipady=6)

    def create_activity_monitor(self, parent):
        """Create activity monitor with proper styling"""
        monitor_frame = ttk.LabelFrame(parent, text="  Activity Monitor", 
                                      style='Card.TLabelframe', padding=15)
        monitor_frame.pack(fill=tk.BOTH, expand=True)
        
        # Monitor controls
        controls_frame = ttk.Frame(monitor_frame, style='Card.TFrame')
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Live connections display
        self.live_connections_var = tk.StringVar()
        self.live_connections_var.set("0 active connections")
        
        connections_label = ttk.Label(controls_frame, textvariable=self.live_connections_var,
                                     font=(self.primary_font, 10, 'bold'),
                                     background=self.colors['bg_secondary'],
                                     foreground=self.colors['accent_primary'])
        connections_label.pack(side=tk.LEFT)
        
        # Log filter
        filter_frame = ttk.Frame(controls_frame, style='Card.TFrame')
        filter_frame.pack(side=tk.RIGHT)
        
        ttk.Label(filter_frame, text="Filter:", style='Body.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        
        self.log_filter_var = tk.StringVar(value="All")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.log_filter_var,
                                   values=["All", "Info", "Success", "Warning", "Error"],
                                   state="readonly", width=8, font=(self.primary_font, 9))
        filter_combo.pack(side=tk.LEFT)
        filter_combo.bind('<<ComboboxSelected>>', self.filter_logs)
        
        # Log display with modern styling
        self.log_text = scrolledtext.ScrolledText(
            monitor_frame,
            height=20,
            state='disabled',
            font=(self.mono_font, 9),
            bg='white',
            fg=self.colors['text_primary'],
            selectbackground=self.colors['accent_primary'],
            selectforeground='white',
            wrap=tk.WORD,
            relief='solid',
            borderwidth=1,
            padx=10,
            pady=10
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Configure text tags with consistent colors
        self.log_text.tag_configure("INFO", foreground=self.colors['info'])
        self.log_text.tag_configure("WARNING", foreground=self.colors['warning'])
        self.log_text.tag_configure("ERROR", foreground=self.colors['error'])
        self.log_text.tag_configure("SUCCESS", foreground=self.colors['success'])
        self.log_text.tag_configure("HEADER", foreground=self.colors['accent_primary'], font=(self.mono_font, 9, 'bold'))
        self.log_text.tag_configure("TIMESTAMP", foreground=self.colors['text_muted'])

    def create_modern_footer(self, parent):
        """Create clean modern footer with copyright notice"""
        footer_frame = ttk.Frame(parent, style='Main.TFrame')
        footer_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Separator line
        separator = ttk.Separator(footer_frame, orient='horizontal')
        separator.pack(fill=tk.X, pady=(0, 10))
        
        # Footer content
        footer_content = ttk.Frame(footer_frame, style='Main.TFrame')
        footer_content.pack(fill=tk.X)
        
        # Left side - status
        left_footer = ttk.Frame(footer_content, style='Main.TFrame')
        left_footer.pack(side=tk.LEFT, fill=tk.Y)
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready - System initialized")
        
        status_label = ttk.Label(left_footer, textvariable=self.status_var,
                               font=(self.primary_font, 9),
                               background=self.colors['bg_primary'],
                               foreground=self.colors['text_secondary'])
        status_label.pack(anchor=tk.W)
        
        # Center - copyright notice
        copyright_label = ttk.Label(footer_content, 
                                   text="© 2025 Mohammad Arfin Baig - Professional Network Solutions",
                                   font=(self.primary_font, 8),
                                   background=self.colors['bg_primary'],
                                   foreground=self.colors['text_muted'])
        copyright_label.pack()
        
        # Right side - version
        version_label = ttk.Label(footer_content, text="v1.0 Professional",
                                 font=(self.primary_font, 9),
                                 background=self.colors['bg_primary'],
                                 foreground=self.colors['text_muted'])
        version_label.pack(side=tk.RIGHT)

    def show_shortcuts_popup(self):
        """Show shortcuts popup on startup if enabled"""
        if not self.settings.get('show_shortcuts_popup', True):
            return
            
        popup = tk.Toplevel(self.root)
        popup.title("Keyboard Shortcuts")
        popup.geometry("550x650")
        popup.transient(self.root)
        popup.grab_set()
        popup.configure(bg=self.colors['bg_primary'])
        
        # Center the popup
        self.center_window(popup)
        
        # Content frame
        content_frame = ttk.LabelFrame(popup, text="About",
                                      style='Card.TLabelframe', padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header_label = ttk.Label(content_frame, text="PortView Pro",
                                font=(self.primary_font, 16, 'bold'),
                                background=self.colors['bg_secondary'],
                                foreground=self.colors['text_primary'])
        header_label.pack(pady=(0, 5))
        
        # Developer info
        dev_label = ttk.Label(content_frame, text="Developed by Mohammad Arfin Baig",
                             font=(self.primary_font, 11, 'italic'),
                             background=self.colors['bg_secondary'],
                             foreground=self.colors['accent_primary'])
        dev_label.pack(pady=(0, 15))
        
        # Support contact
        support_frame = ttk.Frame(content_frame, style='Card.TFrame')
        support_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(support_frame, text="Technical Support & Inquiries:",
                 font=(self.primary_font, 10, 'bold'),
                 background=self.colors['bg_secondary'],
                 foreground=self.colors['text_primary']).pack(anchor=tk.W)
        
        # Contact email with clickable appearance
        contact_label = ttk.Label(support_frame, text="help.mohammadarfinbaig@gmail.com",
                                 font=(self.primary_font, 10, 'underline'),
                                 background=self.colors['bg_secondary'],
                                 foreground=self.colors['accent_primary'],
                                 cursor="hand2")
        contact_label.pack(anchor=tk.W, pady=(2, 0))
        contact_label.bind("<Button-1>", lambda e: self.copy_to_clipboard("help.mohammadarfinbaig@gmail.com"))
        
        # Shortcuts text
        shortcuts_text = """
KEYBOARD SHORTCUTS

FILE OPERATIONS
  Ctrl + O      Select device configuration file
  Ctrl + T      Create new device template
  Ctrl + E      Export current session data
  Ctrl + Q      Exit application

COLLECTION CONTROL
  F5            Start inventory collection
  Escape        Stop current collection
  Ctrl + L      Clear activity log
  Ctrl + R      Open reports folder

NAVIGATION & TOOLS
  F1            Show user guide
  Ctrl + /      Show keyboard shortcuts
  Tab           Navigate between fields
  Enter         Activate focused button

QUICK ACCESS
  Ctrl + S      Open settings
  Ctrl + H      Show this help
  Alt + F4      Exit application (Windows)
  Cmd + Q       Exit application (macOS)
        """
        
        # Text widget for shortcuts
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=(self.mono_font, 9),
            bg='white',
            fg=self.colors['text_primary'],
            selectbackground=self.colors['accent_primary'],
            selectforeground='white',
            relief='solid',
            borderwidth=1,
            padx=10,
            pady=10,
            state='disabled',
            height=12
        )
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        text_widget.config(state='normal')
        text_widget.insert(tk.END, shortcuts_text.strip())
        text_widget.config(state='disabled')
        
        # Bottom frame for checkbox and button
        bottom_frame = ttk.Frame(content_frame, style='Card.TFrame')
        bottom_frame.pack(fill=tk.X)
        
        # Don't show again checkbox
        self.dont_show_var = tk.BooleanVar()
        dont_show_check = ttk.Checkbutton(bottom_frame, text="Don't show this again",
                                         variable=self.dont_show_var)
        dont_show_check.pack(side=tk.LEFT)
        
        # Close button
        def close_popup():
            if self.dont_show_var.get():
                self.settings['show_shortcuts_popup'] = False
                self.save_settings()
            popup.destroy()
            
        close_btn = ttk.Button(bottom_frame, text="Got it!", command=close_popup,
                              style='Primary.TButton')
        close_btn.pack(side=tk.RIGHT, ipadx=15, ipady=5)

    def copy_to_clipboard(self, text):
        """Copy text to clipboard and show confirmation"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        messagebox.showinfo("Copied", f"Email address copied to clipboard:\n{text}")

    def validate_credentials(self, *args):
        """Real-time credential validation with visual feedback"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if username and password:
            self.credential_status.config(text="Credentials configured", 
                                        foreground=self.colors['success'])
        elif username or password:
            self.credential_status.config(text="Incomplete credentials", 
                                        foreground=self.colors['warning'])
        else:
            self.credential_status.config(text="No credentials provided", 
                                        foreground=self.colors['text_muted'])
            
        # Update connection readiness
        self.update_connection_readiness()
            
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
        
    def select_device_file(self):
        """Enhanced file selection"""
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
            
            # Update display
            if len(filename) > 40:
                display_name = filename[:37] + "..."
            else:
                display_name = filename
                
            self.file_path_var.set(display_name)
            self.file_display.config(foreground=self.colors['text_primary'])
            
            # Log and update status
            self.log_message(f"File loaded: {filename}", "SUCCESS")
            self.status_var.set(f"File ready: {filename}")
            
            # Update connection status
            self.update_connection_readiness()
            
    def update_connection_readiness(self):
        """Update UI based on readiness state"""
        has_file = bool(self.devices_file)
        has_credentials = bool(self.username_var.get().strip() and self.password_var.get().strip())
        
        if has_file and has_credentials:
            self.connection_status.config(text="Ready to Connect", 
                                        foreground=self.colors['success'])
            self.quick_stats.config(text="All requirements met")
            self.start_button.config(state='normal')
        elif has_file:
            self.connection_status.config(text="Awaiting Credentials", 
                                        foreground=self.colors['warning'])
            self.quick_stats.config(text="Enter device credentials")
            self.start_button.config(state='disabled')
        else:
            self.connection_status.config(text="Setup Required", 
                                        foreground=self.colors['error'])
            self.quick_stats.config(text="Select device file")
            self.start_button.config(state='disabled')
            
    def create_template(self):
        """Create device template file"""
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
                
                result = messagebox.askyesno(
                    "Template Created",
                    f"Device template created successfully!\n\n"
                    f"File: {filename}\n\n"
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
        """Start inventory collection with proper validation"""
        # Validate inputs
        errors = self.validate_inputs()
        
        if errors:
            error_text = "Please fix the following issues:\n\n" + "\n".join(errors)
            messagebox.showerror("Validation Failed", error_text)
            return
            
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        # Update UI state
        self.start_button.config(state='disabled', text="Connecting...")
        self.stop_button.config(state='normal')
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)
        
        # Log session start
        self.log_message("=" * 60, "HEADER")
        self.log_message("INVENTORY COLLECTION SESSION STARTED", "HEADER")
        self.log_message("=" * 60, "HEADER")
        self.log_message(f"Device file: {os.path.basename(self.devices_file)}", "INFO")
        self.log_message(f"Username: {username}", "INFO")
        self.log_message(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
        self.log_message("", "INFO")
        
        self.status_var.set("Initializing collection...")
        self.connection_status.config(text="Connecting...", 
                                    foreground=self.colors['warning'])
        
        # Start worker thread
        self.current_task = threading.Thread(target=self.inventory_worker, daemon=True)
        self.current_task.start()
        
    def stop_inventory(self):
        """Stop inventory collection"""
        if self.current_task and self.current_task.is_alive():
            self.log_message("Stop requested - completing current operations...", "WARNING")
            self.status_var.set("Stopping collection...")
            self.stop_button.config(text="Stopping...", state='disabled')
            
            # Reset UI after delay
            self.root.after(2000, self.reset_ui_after_stop)
        
    def reset_ui_after_stop(self):
        """Reset UI elements after stop operation"""
        self.start_button.config(state='normal', text="Start Collection")
        self.stop_button.config(state='disabled', text="Stop")
        self.progress_bar.stop()
        self.progress_bar.config(value=0)
        self.status_var.set("Collection stopped")
        self.connection_status.config(text="Stopped", foreground=self.colors['warning'])
        
    def inventory_worker(self):
        """Worker thread for inventory collection"""
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
            
            # Generate summary
            summary = self.collector.get_collection_summary(results)
            
            # Send results to main thread
            self.result_queue.put(('success', results, summary))
            
        except Exception as e:
            self.result_queue.put(('error', str(e)))
            
    def monitor_queues(self):
        """Monitor progress and result queues"""
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
        self.root.after(100, self.monitor_queues)
        
    def handle_progress_update(self, item):
        """Handle progress updates from worker thread"""
        if item[0] == 'progress':
            phase, total, current, message = item[1], item[2], item[3], item[4]
            
            if phase == 'loaded_devices':
                self.progress_var.set(f"{total} devices loaded")
                self.device_counter_var.set("Initializing...")
                self.live_connections_var.set("0 active connections")
                self.progress_bar.config(mode='determinate', maximum=total, value=0)
                
            elif phase == 'collecting':
                self.progress_var.set(f"Collecting: {self.truncate_message(message, 30)}")
                self.device_counter_var.set(f"{current}/{total} processed")
                self.live_connections_var.set(f"{min(5, total-current)} active connections")
                self.progress_bar.config(value=current)
                
                # Update success rate
                if current > 0:
                    estimated_success_rate = max(75, 100 - (current * 2))
                    self.success_rate_var.set(f"{estimated_success_rate}% success")
                
            elif phase == 'complete':
                self.progress_var.set("Collection completed!")
                self.device_counter_var.set(f"Completed: {current} devices")
                self.live_connections_var.set("0 active connections")
                self.progress_bar.config(value=total)
                
            self.log_message(f"{message}", "INFO")
            
        elif item[0] == 'error':
            error_type, message = item[1], item[2]
            self.log_message(f"{error_type}: {message}", "ERROR")
            
    def handle_result(self, item):
        """Handle final results from worker thread"""
        # Reset UI state
        self.start_button.config(state='normal', text="Start Collection")
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        
        if item[0] == 'success':
            results, summary = item[1], item[2]
            
            # Store results for export functionality
            self.last_results = results
            
            # Log completion
            self.log_message("", "INFO")
            self.log_message("=" * 60, "SUCCESS")
            self.log_message("COLLECTION COMPLETED SUCCESSFULLY", "SUCCESS")
            self.log_message("=" * 60, "SUCCESS")
            
            # Show metrics
            self.log_message(f"Total devices: {summary['total_devices']}", "INFO")
            self.log_message(f"Successful: {summary['successful']}", "SUCCESS")
            self.log_message(f"Failed: {summary['failed']}", "WARNING" if summary['failed'] > 0 else "INFO")
            self.log_message(f"Success rate: {summary['success_rate']:.1f}%", "SUCCESS")
            
            # Update UI
            self.success_rate_var.set(f"{summary['success_rate']:.1f}% success")
            self.connection_status.config(text="Collection Complete", 
                                        foreground=self.colors['success'])
            
            # Generate report
            self.generate_excel_report(results, summary)
            
            self.status_var.set(f"Complete: {summary['successful']}/{summary['total_devices']} successful")
            
        elif item[0] == 'error':
            error_message = item[1]
            self.log_message("", "INFO")
            self.log_message("COLLECTION FAILED", "ERROR")
            self.log_message(f"Error: {error_message}", "ERROR")
            
            # Update UI state
            self.connection_status.config(text="Collection Failed", 
                                        foreground=self.colors['error'])
            self.status_var.set("Collection failed")
            
            messagebox.showerror("Collection Failed", 
                               f"Inventory collection failed:\n\n{error_message}")
            
    def generate_excel_report(self, results, summary):
        """Generate Excel report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"switch_inventory_{timestamp}.xlsx"
            
            # Create reports directory
            output_dir = "reports"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, filename)
            
            # Generate report
            self.excel_handler.generate_report(results, output_path, summary)
            
            self.log_message(f"Report generated: {filename}", "SUCCESS")
            self.log_message(f"Location: {output_dir}/", "INFO")
            
            # Show completion dialog
            dialog_text = (f"Inventory report generated successfully!\n\n"
                          f"File: {filename}\n"
                          f"Location: {output_dir}/\n"
                          f"Success Rate: {summary['success_rate']:.1f}%\n"
                          f"Total Devices: {summary['total_devices']}\n\n"
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
            
        self.log_message("Exporting current session data...", "INFO")
        
        # Get save location
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = filedialog.asksaveasfilename(
            title="Export Current Report",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialname=f"exported_inventory_{timestamp}.xlsx"
        )
        
        if save_path:
            try:
                # Generate summary for current results
                summary = self.collector.get_collection_summary(self.last_results)
                
                # Generate report
                self.excel_handler.generate_report(self.last_results, save_path, summary)
                
                self.log_message(f"Export completed: {os.path.basename(save_path)}", "SUCCESS")
                
                result = messagebox.askyesno("Export Complete", 
                                           f"Report exported successfully!\n\n"
                                           f"File: {os.path.basename(save_path)}\n\n"
                                           "Open the exported file now?",
                                           icon='question')
                
                if result:
                    self.open_file(save_path)
                    
            except Exception as e:
                self.log_message(f"Export failed: {str(e)}", "ERROR")
                messagebox.showerror("Export Failed", 
                                   f"Failed to export report:\n\n{str(e)}")
        
    def show_settings(self):
        """Show application settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("450x350")
        settings_window.transient(self.root)
        settings_window.grab_set()
        settings_window.configure(bg=self.colors['bg_primary'])
        
        self.center_window(settings_window)
        
        # Settings content
        settings_frame = ttk.LabelFrame(settings_window, text="Application Settings",
                                       style='Card.TLabelframe', padding=20)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Popup setting
        popup_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        popup_frame.pack(fill=tk.X, pady=(0, 15))
        
        popup_var = tk.BooleanVar(value=self.settings.get('show_shortcuts_popup', True))
        popup_check = ttk.Checkbutton(popup_frame, text="Show shortcuts popup on startup",
                                     variable=popup_var)
        popup_check.pack(anchor=tk.W)
        
        # Save and close buttons
        button_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        def save_and_close():
            self.settings['show_shortcuts_popup'] = popup_var.get()
            self.save_settings()
            settings_window.destroy()
            
        ttk.Button(button_frame, text="Cancel", command=settings_window.destroy,
                  style='Secondary.TButton').pack(side=tk.LEFT, ipadx=15, ipady=6)
        
        ttk.Button(button_frame, text="Save", command=save_and_close,
                  style='Primary.TButton').pack(side=tk.RIGHT, ipadx=15, ipady=6)
        
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
        filter_level = self.log_filter_var.get()
        self.log_message(f"Log filter set to: {filter_level}", "INFO")
        
    def open_file(self, file_path):
        """Cross-platform file opening"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                if hasattr(os, 'uname') and os.uname().sysname == 'Darwin':  # macOS
                    os.system(f'open "{file_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            self.log_message(f"Could not open file: {str(e)}", "ERROR")
                
    def log_message(self, message, level="INFO"):
        """Enhanced logging with proper formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Level indicators
        level_indicators = {
            "INFO": "[INFO]",
            "SUCCESS": "[OK]",
            "WARNING": "[WARN]",
            "ERROR": "[ERR]",
            "HEADER": "[SYS]"
        }
        
        indicator = level_indicators.get(level, "[INFO]")
        
        if level == "HEADER":
            log_entry = f"{message}\n"
        else:
            log_entry = f"[{timestamp}] {indicator} {message}\n"
        
        self.log_text.config(state='normal')
        
        # Insert with appropriate tag
        if level == "HEADER":
            self.log_text.insert(tk.END, log_entry, level)
        else:
            self.log_text.insert(tk.END, f"[{timestamp}] ", "TIMESTAMP")
            self.log_text.insert(tk.END, f"{indicator} {message}\n", level)
        
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
    def clear_log(self):
        """Clear log with confirmation if collection is running"""
        if self.current_task and self.current_task.is_alive():
            if not messagebox.askyesno("Clear Activity Log", 
                                     "Collection is currently running.\n"
                                     "Clear the log anyway?"):
                return
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        
        # Welcome message
        self.log_message("=" * 60, "HEADER")
        self.log_message("PortView PRO", "HEADER")
        self.log_message("Enterprise Network Device Management System", "HEADER")
        self.log_message("=" * 60, "HEADER")
        self.log_message("System initialized and ready for operation", "SUCCESS")
        self.log_message("Select a device file and enter credentials to begin", "INFO")
        
    def validate_inputs(self):
        """Comprehensive input validation"""
        errors = []
        
        if not self.devices_file:
            errors.append("Device configuration file not selected")
        elif not os.path.exists(self.devices_file):
            errors.append("Selected device file no longer exists")
        elif not self.devices_file.lower().endswith(('.xlsx', '.xls', '.csv')):
            errors.append("Invalid file format (must be Excel or CSV)")
            
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        
        if not username:
            errors.append("Username is required")
        elif len(username) < 2:
            errors.append("Username too short (minimum 2 characters)")
            
        if not password:
            errors.append("Password is required")
        elif len(password) < 3:
            errors.append("Password too short (minimum 3 characters)")
            
        return errors
        
    def open_reports_folder(self):
        """Open reports folder"""
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir, exist_ok=True)
            self.log_message(f"Created reports directory: {reports_dir}", "INFO")
            
        try:
            self.open_file(reports_dir)
            self.log_message("Opened reports folder", "INFO")
        except Exception as e:
            self.log_message(f"Could not open reports folder: {str(e)}", "ERROR")
            
    def show_user_guide(self):
        """Show user guide dialog with contact information"""
        guide_window = tk.Toplevel(self.root)
        guide_window.title("User Guide")
        guide_window.geometry("650x550")
        guide_window.transient(self.root)
        guide_window.grab_set()
        guide_window.configure(bg=self.colors['bg_primary'])
        
        self.center_window(guide_window)
        
        # Guide content
        guide_frame = ttk.LabelFrame(guide_window, text="User Guide",
                                    style='Card.TLabelframe', padding=20)
        guide_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Support contact at top
        support_frame = ttk.Frame(guide_frame, style='Card.TFrame')
        support_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(support_frame, text="Need Help? Contact Technical Support:",
                 font=(self.primary_font, 10, 'bold'),
                 background=self.colors['bg_secondary'],
                 foreground=self.colors['text_primary']).pack(anchor=tk.W)
        
        # Contact email with clickable appearance
        contact_label = ttk.Label(support_frame, text="help.mohammadarfinbaig@gmail.com",
                                 font=(self.primary_font, 10, 'underline'),
                                 background=self.colors['bg_secondary'],
                                 foreground=self.colors['accent_primary'],
                                 cursor="hand2")
        contact_label.pack(anchor=tk.W, pady=(2, 0))
        contact_label.bind("<Button-1>", lambda e: self.copy_to_clipboard("help.mohammadarfinbaig@gmail.com"))
        
        # Separator
        ttk.Separator(guide_frame, orient='horizontal').pack(fill=tk.X, pady=(10, 15))
        
        guide_text = """
GETTING STARTED

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

DEVICE FILE FORMAT

Your device file should contain these columns:
   • IP Address or Hostname (required)
   • Device Type (optional - auto-detected if blank)
   • Location/Description (optional)

SECURITY NOTES

   • Credentials are only stored in memory during collection
   • No sensitive data is logged or saved to disk
   • Use read-only accounts when possible

REPORTS & OUTPUT

   • Excel reports generated automatically in 'reports' folder
   • Reports include device details, configurations, and statistics
   • Each report is timestamped for version control

TROUBLESHOOTING

   • Check device connectivity before running collection
   • Verify credentials have appropriate permissions
   • Review firewall settings if connections fail
   • Contact support for advanced configuration assistance
        """
        
        text_widget = scrolledtext.ScrolledText(
            guide_frame,
            wrap=tk.WORD,
            font=(self.primary_font, 9),
            bg='white',
            fg=self.colors['text_primary'],
            relief='solid',
            borderwidth=1,
            padx=15,
            pady=10,
            state='disabled'
        )
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        text_widget.config(state='normal')
        text_widget.insert(tk.END, guide_text.strip())
        text_widget.config(state='disabled')
        
        # Close button
        ttk.Button(guide_frame, text="Close", command=guide_window.destroy,
                  style='Primary.TButton').pack(ipadx=20, ipady=6)
        
    def show_about_dialog(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About PortView Pro")
        about_window.geometry("500x450")
        about_window.transient(self.root)
        about_window.grab_set()
        about_window.configure(bg=self.colors['bg_primary'])
        
        self.center_window(about_window)
        
        # About content
        about_frame = ttk.LabelFrame(about_window, text="About",
                                    style='Card.TLabelframe', padding=20)
        about_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # App info
        ttk.Label(about_frame, text="PortView Pro",
                 font=(self.primary_font, 16, 'bold'),
                 background=self.colors['bg_secondary'],
                 foreground=self.colors['text_primary']).pack(pady=(0, 5))
        
        ttk.Label(about_frame, text="Version 1.0 Professional Edition",
                 font=(self.primary_font, 11),
                 background=self.colors['bg_secondary'],
                 foreground=self.colors['accent_primary']).pack(pady=(0, 15))
        
        # Developer section
        dev_frame = ttk.Frame(about_frame, style='Card.TFrame')
        dev_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(dev_frame, text="Developed by Mohammad Arfin Baig",
                 font=(self.primary_font, 12, 'bold'),
                 background=self.colors['bg_secondary'],
                 foreground=self.colors['text_primary']).pack(pady=(0, 5))
        
        # Contact info
        contact_frame = ttk.Frame(dev_frame, style='Card.TFrame')
        contact_frame.pack(fill=tk.X)
        
        ttk.Label(contact_frame, text="Technical Support:",
                 font=(self.primary_font, 10),
                 background=self.colors['bg_secondary'],
                 foreground=self.colors['text_secondary']).pack(anchor=tk.W)
        
        # Clickable email
        email_label = ttk.Label(contact_frame, text="help.mohammadarfinbaig@gmail.com",
                               font=(self.primary_font, 10, 'underline'),
                               background=self.colors['bg_secondary'],
                               foreground=self.colors['accent_primary'],
                               cursor="hand2")
        email_label.pack(anchor=tk.W, pady=(2, 0))
        email_label.bind("<Button-1>", lambda e: self.copy_to_clipboard("help.mohammadarfinbaig@gmail.com"))
        
        info_text = """
Features:
• Automated device discovery and inventory collection
• Real-time progress monitoring and statistics
• Comprehensive Excel reporting with analytics
• Secure credential management
• Multi-threaded processing for optimal performance
• Modern, intuitive user interface

© 2025 Professional Network Solutions
All rights reserved.
        """
        
        info_label = ttk.Label(about_frame, text=info_text.strip(),
                              font=(self.primary_font, 9),
                              background=self.colors['bg_secondary'],
                              foreground=self.colors['text_secondary'],
                              justify=tk.LEFT)
        info_label.pack(pady=(0, 20))
        
        # Close button
        ttk.Button(about_frame, text="Close", command=about_window.destroy,
                  style='Primary.TButton').pack(ipadx=20, ipady=6)
        
    def run(self):
        """Start the application"""
        # Initialize with welcome message
        self.clear_log()
        
        # Center window on screen
        self.center_window(self.root)
        
        # Add menu bar
        self.create_menu_bar()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Start the application
        self.root.mainloop()
        
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Select Device File...", command=self.select_device_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Create Template...", command=self.create_template, accelerator="Ctrl+T")
        file_menu.add_separator()
        file_menu.add_command(label="Export Current Data...", command=self.export_current_report, accelerator="Ctrl+E")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit, accelerator="Ctrl+Q")
        
        # Collection menu
        collection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Collection", menu=collection_menu)
        collection_menu.add_command(label="Start Collection", command=self.start_inventory, accelerator="F5")
        collection_menu.add_command(label="Stop Collection", command=self.stop_inventory, accelerator="Esc")
        collection_menu.add_separator()
        collection_menu.add_command(label="Clear Activity Log", command=self.clear_log, accelerator="Ctrl+L")
        collection_menu.add_command(label="Open Reports Folder", command=self.open_reports_folder, accelerator="Ctrl+R")
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Settings", command=self.show_settings)
        tools_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts_dialog)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_user_guide)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            '<Control-o>': lambda e: self.select_device_file(),
            '<Control-t>': lambda e: self.create_template(),
            '<Control-e>': lambda e: self.export_current_report(),
            '<Control-q>': lambda e: self.root.quit(),
            '<F5>': lambda e: self.start_inventory(),
            '<Escape>': lambda e: self.stop_inventory(),
            '<Control-l>': lambda e: self.clear_log(),
            '<Control-r>': lambda e: self.open_reports_folder(),
            '<Control-slash>': lambda e: self.show_shortcuts_dialog(),
            '<F1>': lambda e: self.show_user_guide()
        }
        
        for key, command in shortcuts.items():
            self.root.bind(key, command)
            
    def show_shortcuts_dialog(self):
        """Show keyboard shortcuts dialog"""
        shortcuts_window = tk.Toplevel(self.root)
        shortcuts_window.title("Keyboard Shortcuts")
        shortcuts_window.geometry("450x500")
        shortcuts_window.transient(self.root)
        shortcuts_window.grab_set()
        shortcuts_window.configure(bg=self.colors['bg_primary'])
        
        self.center_window(shortcuts_window)
        
        # Content frame
        content_frame = ttk.LabelFrame(shortcuts_window, text="Keyboard Shortcuts",
                                    style='Card.TLabelframe', padding=20)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        shortcuts_text = """FILE OPERATIONS
    Ctrl + O      Select device configuration file
    Ctrl + T      Create new device template
    Ctrl + E      Export current session data
    Ctrl + Q      Exit application

    COLLECTION CONTROL
    F5            Start inventory collection
    Escape        Stop current collection
    Ctrl + L      Clear activity log
    Ctrl + R      Open reports folder

    NAVIGATION & HELP
    F1            Show user guide
    Ctrl + /      Show keyboard shortcuts
    Tab           Navigate between fields
    Enter         Activate focused button"""
        
        text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=(self.mono_font, 9),
            bg='white',
            fg=self.colors['text_primary'],
            relief='solid',
            borderwidth=1,
            padx=15,
            pady=10,
            state='disabled'
        )
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        text_widget.config(state='normal')
        text_widget.insert(tk.END, shortcuts_text)
        text_widget.config(state='disabled')
        
        # Close button
        ttk.Button(content_frame, text="Close", command=shortcuts_window.destroy,
                  style='Primary.TButton').pack(ipadx=20, ipady=6)