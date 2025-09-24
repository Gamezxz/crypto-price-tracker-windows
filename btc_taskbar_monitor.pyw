import asyncio
import json
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
import websockets
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BTCTaskbarMonitor:
    def __init__(self):
        # Available currencies (TOP 4 + ASTER)
        self.available_currencies = {
            'BTC': {'symbol': 'btcusdt', 'name': 'Bitcoin', 'icon': '₿'},
            'ETH': {'symbol': 'ethusdt', 'name': 'Ethereum', 'icon': 'Ξ'},
            'BNB': {'symbol': 'bnbusdt', 'name': 'BNB', 'icon': '●'},
            'TRX': {'symbol': 'trxusdt', 'name': 'TRON', 'icon': '◊'},
            'ASTER': {'symbol': 'asterusdt', 'name': 'Asterdex', 'icon': '✦'}
        }

        # Settings file path
        self.settings_file = Path.home() / 'crypto_monitor_settings.json'

        # Load settings or use defaults
        self.load_settings()

        # Price data for each currency
        self.currency_data = {}
        for currency in self.available_currencies:
            self.currency_data[currency] = {
                'price': "Loading...",
                'price_change': 0.0,
                'change_24h': 0.0
            }

        self.running = True
        self.websockets = {}
        self.reconnect_attempts = {}
        self.max_reconnect_attempts = 5
        
        # Create main window
        self.root = tk.Tk()
        self.setup_window()

    def load_settings(self):
        """Load settings from file"""
        try:
            logger.info(f"Loading settings from: {self.settings_file}")
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                logger.info(f"Raw settings loaded: {settings}")

                # Load selected currencies (validate they exist in available currencies)
                saved_currencies = settings.get('selected_currencies', ['BTC'])
                logger.info(f"Saved currencies: {saved_currencies}")
                valid_currencies = [c for c in saved_currencies if c in self.available_currencies]
                logger.info(f"Valid currencies: {valid_currencies}")

                # Ensure at least one currency and max 3
                if not valid_currencies:
                    valid_currencies = ['BTC']
                    logger.warning("No valid currencies found, using BTC")
                elif len(valid_currencies) > 3:
                    valid_currencies = valid_currencies[:3]
                    logger.warning(f"Too many currencies, limiting to first 3: {valid_currencies}")

                self.selected_currencies = valid_currencies
                logger.info(f"✅ Settings loaded: {', '.join(self.selected_currencies)}")
            else:
                # Default settings
                self.selected_currencies = ['BTC']
                logger.info("Settings file not found, using default: BTC")

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.selected_currencies = ['BTC']

    def save_settings(self):
        """Save current settings to file"""
        try:
            settings = {
                'selected_currencies': self.selected_currencies,
                'version': '3.0'
            }

            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Settings saved: {', '.join(self.selected_currencies)}")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
        
    def setup_window(self):
        """Setup the taskbar window"""
        self.root.title("Crypto Monitor")
        # Dynamic height based on selected currencies
        height = 30 + (len(self.selected_currencies) * 25)
        self.root.geometry(f"300x{height}")
        self.root.resizable(False, False)
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Position window at top-right corner
        screen_width = self.root.winfo_screenwidth()
        height = 30 + (len(self.selected_currencies) * 25)
        self.root.geometry(f"300x{height}+{screen_width-320}+10")
        
        # Remove window decorations for cleaner look
        self.root.overrideredirect(True)
        
        # Make window background transparent
        self.root.attributes('-alpha', 0.95)
        self.root.configure(bg='#000001')  # Nearly black for transparency
        self.root.wm_attributes('-transparentcolor', '#000001')
        
        # Create main frame for price labels
        self.main_frame = tk.Frame(
            self.root,
            bg='#000001'
        )
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=2)

        # Create price labels for selected currencies
        self.price_labels = {}
        self.update_price_labels()
        
        # Create context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Select Currencies", command=self.show_currency_selector)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Reconnect", command=self.reconnect)
        self.context_menu.add_command(label="Toggle Stay on Top", command=self.toggle_topmost)
        self.context_menu.add_command(label="About", command=self.show_about)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Quit", command=self.quit_application)
        
        # Bind events to main frame for interaction
        self.main_frame.bind("<Button-3>", self.show_context_menu)
        self.main_frame.bind("<Button-1>", self.start_drag)
        self.main_frame.bind("<B1-Motion>", self.on_drag)
        self.main_frame.bind("<Enter>", self.on_hover_enter)
        self.main_frame.bind("<Leave>", self.on_hover_leave)
        
        # Variables for dragging
        self.drag_start_x = 0
        self.drag_start_y = 0
        
        # Hover effect variables
        self.is_hovered = False
        
    def start_drag(self, event):
        """Start dragging the window"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_drag(self, event):
        """Handle window dragging"""
        x = self.root.winfo_x() + event.x - self.drag_start_x
        y = self.root.winfo_y() + event.y - self.drag_start_y
        self.root.geometry(f"+{x}+{y}")
    
    def on_hover_enter(self, event):
        """Handle mouse hover enter"""
        self.is_hovered = True
        self.root.attributes('-alpha', 1.0)
        
    def on_hover_leave(self, event):
        """Handle mouse hover leave"""
        self.is_hovered = False
        self.root.attributes('-alpha', 0.95)
    
    def show_context_menu(self, event):
        """Show context menu on right-click"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def toggle_topmost(self):
        """Toggle stay on top setting"""
        current = self.root.attributes('-topmost')
        self.root.attributes('-topmost', not current)

    def update_price_labels(self):
        """Update price labels for selected currencies"""
        logger.info(f"Updating price labels for: {', '.join(self.selected_currencies)}")

        # Clear existing labels
        for label in self.price_labels.values():
            label.destroy()
        self.price_labels.clear()

        # Create labels for selected currencies
        for i, currency in enumerate(self.selected_currencies):
            logger.info(f"Creating label for {currency}")
            label = tk.Label(
                self.main_frame,
                text=f"{self.available_currencies[currency]['icon']} {currency}: Loading...",
                font=("Segoe UI", 11, "bold"),
                bg='#000001',
                fg="#ffffff",
                anchor='w'
            )
            label.pack(fill="x", pady=1)
            self.price_labels[currency] = label

            # Bind events to each label
            label.bind("<Button-3>", self.show_context_menu)
            label.bind("<Button-1>", self.start_drag)
            label.bind("<B1-Motion>", self.on_drag)
            label.bind("<Enter>", self.on_hover_enter)
            label.bind("<Leave>", self.on_hover_leave)

        # Update window size
        height = 30 + (len(self.selected_currencies) * 25)
        screen_width = self.root.winfo_screenwidth()
        self.root.geometry(f"300x{height}+{screen_width-320}+10")
        logger.info(f"Window resized to: 300x{height}, labels created: {list(self.price_labels.keys())}")

    def show_currency_selector(self):
        """Show currency selection dialog"""
        selector_window = tk.Toplevel(self.root)
        selector_window.title("Select Currencies (1-3)")
        selector_window.geometry("400x400")
        selector_window.resizable(False, False)
        selector_window.attributes('-topmost', True)
        selector_window.configure(bg="#1a1a1a")

        # Center the window
        selector_window.update_idletasks()
        x = (selector_window.winfo_screenwidth() // 2) - (400 // 2)
        y = (selector_window.winfo_screenheight() // 2) - (400 // 2)
        selector_window.geometry(f"400x400+{x}+{y}")

        # Main frame
        main_frame = tk.Frame(selector_window, bg="#1a1a1a", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="Select Currencies to Display",
            font=("Segoe UI", 14, "bold"),
            fg="#f59e0b",
            bg="#1a1a1a"
        )
        title_label.pack(pady=(0, 10))

        # Instruction
        info_label = tk.Label(
            main_frame,
            text="Choose 1 to 3 currencies to display (TOP 4 + ASTER available)",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg="#1a1a1a"
        )
        info_label.pack(pady=(0, 15))

        # Currency checkboxes frame (no scrollable since only 5 currencies)
        currencies_frame = tk.Frame(main_frame, bg="#1a1a1a")
        currencies_frame.pack(fill="x", pady=(0, 15))

        # Currency checkboxes
        self.currency_vars = {}
        for currency, details in self.available_currencies.items():
            var = tk.BooleanVar(value=currency in self.selected_currencies)
            self.currency_vars[currency] = var

            frame = tk.Frame(currencies_frame, bg="#2d3748", relief="solid", bd=1)
            frame.pack(fill="x", padx=5, pady=2)

            checkbox = tk.Checkbutton(
                frame,
                text=f"{details['icon']} {currency} - {details['name']}",
                variable=var,
                font=("Segoe UI", 10),
                fg="#ffffff",
                bg="#2d3748",
                selectcolor="#374151",
                activebackground="#4b5563",
                activeforeground="#ffffff",
                command=lambda: self.validate_selection()
            )
            checkbox.pack(anchor='w', padx=10, pady=5)

        # Buttons frame
        button_frame = tk.Frame(main_frame, bg="#1a1a1a")
        button_frame.pack(fill="x", pady=(20, 0))

        # Cancel button
        cancel_button = tk.Button(
            button_frame,
            text="Cancel",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#6b7280",
            activeforeground="#ffffff",
            activebackground="#9ca3af",
            relief="flat",
            padx=20,
            pady=5,
            command=selector_window.destroy
        )
        cancel_button.pack(side="right", padx=(10, 0))

        # Apply button
        apply_button = tk.Button(
            button_frame,
            text="Apply",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#10b981",
            activeforeground="#ffffff",
            activebackground="#059669",
            relief="flat",
            padx=20,
            pady=5,
            command=lambda: self.apply_currency_selection(selector_window)
        )
        apply_button.pack(side="right")

        self.apply_button = apply_button
        self.validate_selection()

    def validate_selection(self):
        """Validate currency selection (1-3 currencies)"""
        selected_count = sum(var.get() for var in self.currency_vars.values())
        self.apply_button.config(state='normal' if 1 <= selected_count <= 3 else 'disabled')

    def apply_currency_selection(self, window):
        """Apply selected currencies"""
        new_selection = [currency for currency, var in self.currency_vars.items() if var.get()]

        if 1 <= len(new_selection) <= 3:
            # Stop existing WebSocket connections for unselected currencies
            for currency in self.selected_currencies:
                if currency not in new_selection and currency in self.websockets:
                    try:
                        asyncio.create_task(self.websockets[currency].close())
                    except:
                        pass

            self.selected_currencies = new_selection
            self.update_price_labels()

            # Save settings
            self.save_settings()

            # Start WebSocket connections for newly selected currencies
            self.start_websocket_connections()

            window.destroy()
            logger.info(f"Selected currencies updated: {', '.join(new_selection)}")

    def start_websocket_connections(self):
        """Start WebSocket connections for selected currencies"""
        logger.info(f"Starting WebSocket connections for: {', '.join(self.selected_currencies)}")
        for currency in self.selected_currencies:
            websocket_exists = currency in self.websockets and self.websockets.get(currency) is not None

            try:
                websocket_closed = websocket_exists and self.websockets[currency].closed
            except:
                websocket_closed = True

            if not websocket_exists or websocket_closed:
                self.reconnect_attempts[currency] = 0
                logger.info(f"Starting WebSocket for {currency}")
                self.start_websocket_thread(currency)
            else:
                logger.info(f"WebSocket for {currency} already running")
    
    def update_price_display(self, currency):
        """Update the price display for a specific currency"""
        if currency not in self.price_labels:
            logger.warning(f"Price label for {currency} not found in price_labels")
            return

        data = self.currency_data[currency]
        logger.debug(f"Updating display for {currency}: {data['price']}")

        if data['price_change'] >= 0:
            color = "#10b981"  # Green for price up
            arrow = "▲"
        else:
            color = "#ef4444"  # Red for price down
            arrow = "▼"

        icon = self.available_currencies[currency]['icon']
        self.price_labels[currency].config(
            text=f"{icon} {currency}: ${data['price']} {arrow} {data['change_24h']:+.2f}%",
            fg=color
        )
        
    async def connect_binance_websocket(self, currency):
        """Connect to Binance WebSocket for specific currency price updates"""
        symbol = self.available_currencies[currency]['symbol']
        uri = f"wss://fstream.binance.com/ws/{symbol}@ticker"

        try:
            logger.info(f"Connecting to Binance WebSocket for {currency} at {uri}")
            async with websockets.connect(uri) as websocket:
                self.websockets[currency] = websocket
                self.reconnect_attempts[currency] = 0
                logger.info(f"✅ Connected to Binance WebSocket for {currency}")

                message_count = 0
                async for message in websocket:
                    if not self.running or currency not in self.selected_currencies:
                        logger.info(f"Stopping WebSocket for {currency}: running={self.running}, in_selected={currency in self.selected_currencies}")
                        break

                    try:
                        data = json.loads(message)
                        new_price = float(data['c'])
                        price_change = float(data['P'])
                        change_24h = float(data['P'])

                        # Format price with appropriate decimal places
                        if new_price < 10:
                            formatted_price = f"{new_price:,.4f}"  # 4 decimal places for < 10
                        elif new_price < 100:
                            formatted_price = f"{new_price:,.3f}"  # 3 decimal places for 10-99
                        elif new_price < 10000:
                            formatted_price = f"{new_price:,.2f}"  # 2 decimal places for 100-9999
                        else:
                            formatted_price = f"{new_price:,.1f}"  # 1 decimal place for >= 10000

                        self.currency_data[currency]['price'] = formatted_price
                        self.currency_data[currency]['price_change'] = price_change
                        self.currency_data[currency]['change_24h'] = change_24h

                        # Schedule GUI update in main thread
                        self.root.after(0, lambda c=currency: self.update_price_display(c))

                        message_count += 1
                        if message_count % 5 == 1:  # Log every 5th message to reduce spam
                            logger.info(f"{currency} price updated: ${self.currency_data[currency]['price']} ({price_change:+.2f}%)")

                    except (KeyError, ValueError, json.JSONDecodeError) as e:
                        logger.error(f"Error parsing WebSocket data for {currency}: {e}")
                        logger.error(f"Raw message: {message}")

        except Exception as e:
            logger.error(f"WebSocket connection error for {currency}: {e}")
            if (self.running and currency in self.selected_currencies and
                self.reconnect_attempts.get(currency, 0) < self.max_reconnect_attempts):
                self.reconnect_attempts[currency] = self.reconnect_attempts.get(currency, 0) + 1
                logger.info(f"Reconnection attempt {self.reconnect_attempts[currency]}/{self.max_reconnect_attempts} for {currency}")
                await asyncio.sleep(5)
                await self.connect_binance_websocket(currency)
            else:
                self.currency_data[currency]['price'] = "Error"
                self.root.after(0, lambda c=currency: self.update_price_display(c))
    
    def start_websocket_thread(self, currency):
        """Start WebSocket connection in separate thread for specific currency"""
        def run_websocket():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect_binance_websocket(currency))
            loop.close()

        thread = threading.Thread(target=run_websocket, daemon=True, name=f"WebSocket-{currency}")
        thread.start()
    
    def reconnect(self):
        """Reconnect to Binance WebSocket for all selected currencies"""
        logger.info("Manual reconnection requested")
        for currency in self.selected_currencies:
            self.reconnect_attempts[currency] = 0
            self.start_websocket_thread(currency)
    
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About BTC Monitor")
        about_window.geometry("350x200")
        about_window.resizable(False, False)
        about_window.attributes('-topmost', True)
        about_window.configure(bg="#1a1a1a")
        
        # Main frame
        main_frame = tk.Frame(about_window, bg="#1a1a1a", padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = tk.Label(
            main_frame,
            text="🚀 Multi-Crypto Taskbar Monitor",
            font=("Segoe UI", 14, "bold"),
            fg="#f59e0b",
            bg="#1a1a1a"
        )
        title_label.pack(pady=(0, 15))

        # Info text
        selected_currencies_text = ", ".join(self.selected_currencies)
        info_text = f"""Version: 3.0 Multi-Currency Edition
Data Source: Binance WebSocket API
Currently Displaying: {selected_currencies_text}
Supported: TOP 4 + ASTER (5 total)

Right-click for options
Left-click and drag to move
Hover for enhanced visibility"""
        
        info_label = tk.Label(
            main_frame, 
            text=info_text, 
            justify="left",
            font=("Segoe UI", 9),
            fg="#ffffff",
            bg="#1a1a1a"
        )
        info_label.pack(pady=(0, 20))
        
        # Modern OK button
        ok_button = tk.Button(
            main_frame, 
            text="OK",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#374151",
            activeforeground="#ffffff",
            activebackground="#4b5563",
            relief="flat",
            padx=20,
            pady=5,
            command=about_window.destroy
        )
        ok_button.pack()
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Quitting application")
        self.running = False
        # Close all WebSocket connections
        for currency, websocket in self.websockets.items():
            if websocket:
                try:
                    asyncio.create_task(websocket.close())
                except:
                    pass
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Start the Multi-Currency taskbar monitor"""
        logger.info("Starting Multi-Currency Taskbar Monitor")

        # Start WebSocket connections for selected currencies
        self.start_websocket_connections()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.quit_application)

        # Start GUI main loop
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Application interrupted")
            self.quit_application()

if __name__ == "__main__":
    try:
        monitor = BTCTaskbarMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        messagebox.showerror("Error", f"Application failed to start: {e}")