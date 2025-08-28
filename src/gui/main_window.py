# src/gui/main_window.py
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
        self.root.title("Switch Inventory Collector v1.0")
        self.root.geometry("800x600")
        
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
        
    def setup_gui_logging(self):
        """Setup logging that will display in GUI"""
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        self.log_handler.setFormatter(formatter)
        
    def setup_ui(self):
        """Create the main user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Network Device Inventory Collector", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection frame
        self.create_file_selection_frame(main_frame)
        
        # Progress frame
        self.create_progress_frame(main_frame)
        
        # Control buttons frame
        self.create_control_frame(main_frame)
        
        # Log/status frame
        self.create_log_frame(main_frame)
        
        # Status bar
        self.create_status_bar()
        
    def create_file_selection_frame(self, parent):
        """Create file selection section"""
        # File selection frame
        file_frame = ttk.LabelFrame(parent, text="Device File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # File path display
        self.file_path_var = tk.StringVar()
        self.file_path_var.set("No file selected")
        file_path_label = ttk.Label(file_frame, textvariable=self.file_path_var)
        file_path_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Buttons
        select_button = ttk.Button(file_frame, text="Select Device File", 
                                  command=self.select_device_file)
        select_button.grid(row=1, column=0, padx=(0, 5))
        
        template_button = ttk.Button(file_frame, text="Create Template", 
                                   command=self.create_template)
        template_button.grid(row=1, column=1, padx=(5, 0))
        
    def create_progress_frame(self, parent):
        """Create progress monitoring section"""
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Overall progress
        self.progress_var = tk.StringVar()
        self.progress_var.set("Ready to start")
        progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        progress_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Device counter
        self.device_counter_var = tk.StringVar()
        self.device_counter_var.set("")
        counter_label = ttk.Label(progress_frame, textvariable=self.device_counter_var)
        counter_label.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
    def create_control_frame(self, parent):
        """Create control buttons section"""
        control_frame = ttk.Frame(parent)
        control_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # Start button
        self.start_button = ttk.Button(control_frame, text="Start Inventory", 
                                      command=self.start_inventory, style='Accent.TButton')
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                     command=self.stop_inventory, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear log button
        clear_button = ttk.Button(control_frame, text="Clear Log", 
                                 command=self.clear_log)
        clear_button.pack(side=tk.LEFT)
        
    def create_log_frame(self, parent):
        """Create logging/status display"""
        log_frame = ttk.LabelFrame(parent, text="Activity Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Scrolled text widget for logs
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for different log levels
        self.log_text.tag_configure("INFO", foreground="blue")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        
    def create_status_bar(self):
        """Create bottom status bar"""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
    def select_device_file(self):
        """Handle device file selection"""
        file_path = filedialog.askopenfilename(
            title="Select Device File",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.devices_file = file_path
            self.file_path_var.set(os.path.basename(file_path))
            self.log_message(f"Selected device file: {os.path.basename(file_path)}", "INFO")
            self.status_var.set(f"File loaded: {os.path.basename(file_path)}")
            
    def create_template(self):
        """Create and save device template file"""
        save_path = filedialog.asksaveasfilename(
            title="Save Template File",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")]
        )
        
        if save_path:
            try:
                self.excel_handler.create_device_template(save_path)
                self.log_message(f"Template created: {os.path.basename(save_path)}", "SUCCESS")
                messagebox.showinfo("Success", f"Device template created successfully!\n\nFile: {save_path}")
            except Exception as e:
                self.log_message(f"Failed to create template: {str(e)}", "ERROR")
                messagebox.showerror("Error", f"Failed to create template:\n{str(e)}")
                
    def start_inventory(self):
        """Start the inventory collection process"""
        if not self.devices_file:
            messagebox.showerror("Error", "Please select a device file first")
            return
            
        if not os.path.exists(self.devices_file):
            messagebox.showerror("Error", "Selected device file does not exist")
            return
            
        # Update UI state
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        
        self.log_message("Starting inventory collection...", "INFO")
        self.status_var.set("Running inventory collection...")
        
        # Start worker thread
        self.current_task = threading.Thread(target=self.inventory_worker, daemon=True)
        self.current_task.start()
        
    def stop_inventory(self):
        """Stop the current inventory collection"""
        if self.current_task and self.current_task.is_alive():
            # Note: In a production app, you'd want proper thread cancellation
            self.log_message("Stop requested (current operations will complete)", "WARNING")
            self.status_var.set("Stopping...")
        
    def inventory_worker(self):
        """Worker thread for inventory collection"""
        try:
            def progress_callback(phase, total, current, message):
                self.progress_queue.put(('progress', phase, total, current, message))
                
            def error_callback(error_type, message):
                self.progress_queue.put(('error', error_type, message))
                
            # Run inventory collection
            results = self.collector.collect_inventory(
                self.devices_file,
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
                self.progress_var.set(f"Loaded {total} devices")
                self.device_counter_var.set("")
                
            elif phase == 'collecting':
                self.progress_var.set(f"Collecting data: {message}")
                self.device_counter_var.set(f"Device {current}/{total}")
                
            elif phase == 'parsing':
                self.progress_var.set(f"Parsing outputs: {message}")
                self.device_counter_var.set(f"Parsed {current}/{total}")
                
            elif phase == 'complete':
                self.progress_var.set("Collection complete!")
                self.device_counter_var.set(f"Processed {current} devices")
                
            self.log_message(message, "INFO")
            
        elif item[0] == 'error':
            error_type, message = item[1], item[2]
            self.log_message(f"Error ({error_type}): {message}", "ERROR")
            
    def handle_result(self, item):
        """Handle final results from worker thread"""
        # Reset UI state
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        
        if item[0] == 'success':
            results, summary = item[1], item[2]
            
            # Log summary
            self.log_message(f"Collection completed successfully!", "SUCCESS")
            self.log_message(f"Total devices: {summary['total_devices']}", "INFO")
            self.log_message(f"Successful: {summary['successful']}", "SUCCESS")
            self.log_message(f"Failed: {summary['failed']}", "WARNING" if summary['failed'] > 0 else "INFO")
            self.log_message(f"Success rate: {summary['success_rate']:.1f}%", "INFO")
            
            # Generate Excel report
            self.generate_excel_report(results, summary)
            
            self.status_var.set("Collection completed successfully")
            
        elif item[0] == 'error':
            error_message = item[1]
            self.log_message(f"Collection failed: {error_message}", "ERROR")
            messagebox.showerror("Collection Failed", f"Inventory collection failed:\n\n{error_message}")
            self.status_var.set("Collection failed")
            
    def generate_excel_report(self, results, summary):
        """Generate and save Excel report"""
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"inventory_report_{timestamp}.xlsx"
            
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, filename)
            
            # Generate report
            self.excel_handler.generate_report(results, output_path, summary)
            
            self.log_message(f"Excel report saved: {filename}", "SUCCESS")
            
            # Ask user if they want to open the file
            if messagebox.askyesno("Report Generated", 
                                  f"Excel report has been generated:\n{filename}\n\nOpen the file now?"):
                try:
                    os.startfile(output_path)  # Windows
                except AttributeError:
                    try:
                        os.system(f'open "{output_path}"')  # macOS
                    except:
                        os.system(f'xdg-open "{output_path}"')  # Linux
                        
        except Exception as e:
            self.log_message(f"Failed to generate Excel report: {str(e)}", "ERROR")
            messagebox.showerror("Report Error", f"Failed to generate Excel report:\n\n{str(e)}")
            
    def log_message(self, message, level="INFO"):
        """Add message to log display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, log_entry, level)
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        
    def clear_log(self):
        """Clear the log display"""
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')
        self.log_message("Log cleared", "INFO")
        
    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.run()