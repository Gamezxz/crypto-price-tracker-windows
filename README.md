# 🚀 Multi-Crypto Taskbar Monitor

A modern, lightweight cryptocurrency price monitor that displays real-time prices directly on your desktop taskbar. Built with Python and Tkinter, featuring WebSocket connections to Binance for live price updates.

## ✨ Features

- **Multi-Currency Support**: Monitor up to 3 cryptocurrencies simultaneously
- **Real-Time Updates**: Live price feeds via Binance WebSocket API
- **Smart Decimal Formatting**: Dynamic decimal places based on price range
- **Customizable Interface**: Draggable, transparent window with hover effects
- **Persistent Settings**: Automatically saves and restores your currency selections
- **Top Cryptocurrencies**: Supports BTC, ETH, BNB, TRX, and ASTER

## 📊 Supported Cryptocurrencies

| Symbol | Name | Icon |
|--------|------|------|
| BTC | Bitcoin | ₿ |
| ETH | Ethereum | Ξ |
| BNB | BNB | ● |
| TRX | TRON | ◊ |
| ASTER | Asterdex | ✦ |

## 💰 Price Display Format

The application uses intelligent decimal formatting based on price ranges:

- **< $10**: 4 decimal places (e.g., `0.0514`)
- **$10 - $99**: 3 decimal places (e.g., `12.345`)
- **$100 - $9,999**: 2 decimal places (e.g., `3,456.78`)
- **≥ $10,000**: 1 decimal place (e.g., `67,890.1`)

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Required packages:
  ```bash
  pip install websockets asyncio
  ```

### Installation

1. Clone or download the repository
2. Navigate to the project directory
3. Run the application:
   ```bash
   python btc_taskbar_monitor.pyw
   ```

### First Run

1. The application will start with Bitcoin (BTC) selected by default
2. Right-click on the price display to open the context menu
3. Select "Select Currencies" to choose your preferred cryptocurrencies (1-3 max)
4. Your selections will be automatically saved for future sessions

## 🎛️ Usage

### Basic Controls

- **Left-click + Drag**: Move the window around your screen
- **Right-click**: Open context menu with options
- **Hover**: Enhanced visibility (opacity increases)

### Context Menu Options

- **Select Currencies**: Choose which cryptocurrencies to display
- **Reconnect**: Manually reconnect WebSocket connections
- **Toggle Stay on Top**: Keep window above other applications
- **About**: View application information
- **Quit**: Exit the application

### Currency Selection

1. Right-click on the price display
2. Select "Select Currencies"
3. Check/uncheck desired currencies (1-3 maximum)
4. Click "Apply" to save changes

## ⚙️ Configuration

### Settings File

Settings are automatically saved to:
```
~/crypto_monitor_settings.json
```

Example settings file:
```json
{
  "selected_currencies": ["BTC", "ETH", "ASTER"],
  "version": "3.0"
}
```

### Window Positioning

The window automatically positions itself at the top-right corner of your screen. You can drag it to any position you prefer.

## 🔧 Technical Details

### Architecture

- **Frontend**: Tkinter (Python's built-in GUI library)
- **Backend**: Asyncio for WebSocket management
- **Data Source**: Binance Futures WebSocket API (`wss://fstream.binance.com/ws/`)
- **Threading**: Separate threads for each WebSocket connection

### WebSocket Endpoints

Each cryptocurrency connects to its dedicated WebSocket stream:
```
wss://fstream.binance.com/ws/{symbol}@ticker
```

Where `{symbol}` is the trading pair (e.g., `btcusdt`, `ethusdt`)

### Error Handling

- **Connection Failures**: Automatic reconnection with exponential backoff
- **Invalid Data**: Error logging with raw message debugging
- **Settings Corruption**: Fallback to default settings (BTC only)

## 🐛 Troubleshooting

### Common Issues

1. **No Price Updates**:
   - Check internet connection
   - Try manual reconnection via context menu
   - Check console logs for WebSocket errors

2. **Window Not Visible**:
   - The window might be positioned off-screen
   - Delete settings file and restart: `~/crypto_monitor_settings.json`

3. **High CPU Usage**:
   - Normal behavior during price updates
   - Consider selecting fewer currencies if performance is an issue

### Debug Mode

The application includes comprehensive logging. Check the console output for detailed information about:
- Settings loading/saving
- WebSocket connections
- Price updates
- Error messages

### Logs Location

All logs are displayed in the console where you run the application. Log levels include:
- **INFO**: General operation information
- **DEBUG**: Detailed debugging information
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors and failures

## 📝 Version History

### Version 3.0 (Current)
- Multi-currency support (up to 3 cryptocurrencies)
- Dynamic decimal formatting
- Persistent settings
- Enhanced error handling and debugging
- Improved UI with currency selection dialog

### Version 2.0
- Single currency (Bitcoin) monitoring
- Basic WebSocket connectivity
- Transparent window design

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📄 License

This project is open source and available under standard terms.

## ⚠️ Disclaimer

This application is for informational purposes only. Cryptocurrency prices are volatile and this tool should not be used as the sole basis for trading decisions. Always verify prices from official sources before making financial decisions.

---

**Data Source**: Binance Futures API
**Update Frequency**: Real-time via WebSocket
**Supported Platforms**: Windows, macOS, Linux (with Python/Tkinter support)# crypto-price-tracker-windows
