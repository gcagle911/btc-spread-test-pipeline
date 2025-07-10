# 🚀 BTC Real-Time Chart System

A professional-grade Bitcoin charting application with real-time data collection, processing, and visualization.

## 📊 Chart Files Overview

### 1. **improved_btc_chart.html** ⭐ (Recommended)
- **Professional UI** with modern design
- **Dynamic API endpoint selection** (localhost/production)
- **Real-time connection monitoring** with visual indicators
- **Performance metrics** display
- **Enhanced error handling** and user feedback
- **Hybrid loading strategy** for optimal performance

### 2. **tradingview_style_chart.html**
- **TradingView-inspired** interface
- **Hybrid data loading** (recent first, then historical)
- **Auto-refresh capabilities**
- **Performance optimization** for large datasets
- **Dark theme** professional appearance

### 3. **chart_config_example.html**
- **Basic implementation** example
- **Simple configuration**
- **Good for learning** Chart.js basics
- **Lightweight** and fast

## 🚀 Quick Start

### Option 1: Use the Enhanced Startup Script (Recommended)

```bash
cd render_app
python start_server.py
```

This will:
- ✅ Generate sample data if none exists
- ✅ Start the data collection server
- ✅ Process data into optimized JSON formats
- ✅ Display all available API endpoints
- ✅ Run on http://localhost:10000

### Option 2: Manual Start

```bash
cd render_app
python logger.py
```

Then open any HTML file in your browser.

## 🌐 API Endpoints

The system provides multiple data access points:

### Chart Data (Optimized for Performance)
- `/recent.json` - Last 24 hours (fast loading, ~1440 data points)
- `/historical.json` - Complete dataset (all historical data)
- `/metadata.json` - Dataset information and statistics
- `/index.json` - Data source index

### Raw Data Access
- `/data.csv` - Current CSV file being written
- `/csv-list` - List all available CSV files
- `/csv/<filename>` - Download specific CSV file

### Filtered Data
- `/chart-data?limit=1000` - Get last 1000 data points
- `/chart-data?start_date=2025-01-01` - Get data from specific date
- `/chart-data?start_date=2025-01-01&limit=500` - Combined filters

## 📈 Chart Features

### Data Points Displayed
- **BTC Price ($)** - Real-time Bitcoin price from Coinbase
- **MA 50** - 50-period moving average of spread percentage
- **MA 100** - 100-period moving average of spread percentage  
- **MA 200** - 200-period moving average of spread percentage

### Performance Optimizations
- **Hybrid Loading**: Load recent data instantly, then historical data
- **No Chart Resets**: Smooth updates without losing context
- **Efficient Rendering**: Points hidden on large datasets for performance
- **Auto-refresh**: Optional real-time updates every 30 seconds

## 🛠️ Configuration

### API Endpoint Auto-Detection
Charts automatically detect if running locally or in production:

```javascript
const API_BASE = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
    ? 'http://localhost:10000' 
    : 'https://btc-spread-test-pipeline.onrender.com';
```

### Custom API Endpoint
In `improved_btc_chart.html`, you can:
1. Select "Custom URL..." from the dropdown
2. Enter your custom API endpoint
3. The chart will use your custom endpoint

## 📁 Data Structure

### CSV Files (Raw Data)
Files are rotated every 8 hours with format: `YYYY-MM-DD_HH.csv`
- `2025-01-07_00.csv` (00:00-07:59)
- `2025-01-07_08.csv` (08:00-15:59)  
- `2025-01-07_16.csv` (16:00-23:59)

### JSON Files (Processed Data)

#### recent.json
```json
[
  {
    "time": "2025-01-07T10:30:00.000",
    "price": 65432.50,
    "spread_avg_L20_pct": 0.0005,
    "ma_50": 0.0004,
    "ma_100": 0.0004,
    "ma_200": 0.0005,
    "ma_50_valid": true,
    "ma_100_valid": true,
    "ma_200_valid": false
  }
]
```

#### metadata.json
```json
{
  "generated_at": "2025-01-07T10:30:00.000Z",
  "total_records": 2880,
  "date_range": {
    "start": "2025-01-05T10:30:00.000",
    "end": "2025-01-07T10:30:00.000"
  },
  "ma_info": {
    "ma_50_valid_count": 2830,
    "ma_100_valid_count": 2780,
    "ma_200_valid_count": 2680
  },
  "file_size_mb": 1.2
}
```

## 🔧 Development & Testing

### Generate Sample Data
```python
from start_server import generate_sample_data
generate_sample_data(hours=48)  # Generate 48 hours of test data
```

### Test Data Processing
```python
from start_server import test_data_processing
test_data_processing()  # Verify all JSON files are generated correctly
```

### Monitor Performance
The improved chart displays real-time metrics:
- **Data Points**: Number of records loaded
- **Load Time**: API response time in milliseconds
- **Last Price**: Most recent BTC price
- **Updates/min**: Update frequency

## 🎯 Best Practices

### For Production
1. **Use hybrid loading** for best user experience
2. **Enable auto-refresh** for real-time monitoring
3. **Monitor connection status** (green = connected, red = disconnected)
4. **Check performance metrics** to optimize data delivery

### For Development
1. **Start with sample data** using `start_server.py`
2. **Use localhost endpoints** for testing
3. **Monitor console logs** for debugging
4. **Test with different data volumes**

## 🚨 Troubleshooting

### Common Issues

#### "No data available to chart"
- **Cause**: No CSV files or empty dataset
- **Solution**: Run `start_server.py` to generate sample data

#### "Connection failed" error
- **Cause**: Server not running or wrong API endpoint
- **Solution**: 
  1. Ensure server is running on port 10000
  2. Check if API endpoint is correct
  3. Use "Test Connection" button

#### Chart loads slowly
- **Cause**: Large dataset being loaded
- **Solution**: 
  1. Use "Recent (24h)" button for faster loading
  2. Use hybrid loading strategy
  3. Enable data point limits in API calls

#### CORS errors
- **Cause**: Browser blocking cross-origin requests
- **Solution**: 
  1. Run charts from same origin as API
  2. Server has CORS enabled by default

## 📚 Technical Details

### Technologies Used
- **Backend**: Flask (Python) with CORS support
- **Data Processing**: Pandas for CSV/JSON manipulation
- **Frontend**: Chart.js with date-fns adapter
- **Real-time Updates**: JavaScript intervals with fetch API
- **Styling**: Modern CSS with gradients and animations

### Performance Considerations
- **CSV Rotation**: 8-hour blocks prevent files from getting too large
- **JSON Optimization**: Separate recent/historical files for hybrid loading
- **Chart Rendering**: Point hiding and animation control for large datasets
- **Memory Management**: Efficient data structures and cleanup

## 🔮 Future Enhancements

### Planned Features
- **WebSocket support** for true real-time updates
- **Multiple cryptocurrency** support
- **Technical indicators** (RSI, MACD, Bollinger Bands)
- **Data export** functionality
- **Alert system** for price/spread thresholds
- **Mobile-responsive** design improvements

### Customization Options
- **Theme selection** (dark/light modes)
- **Custom time ranges** and intervals
- **Additional chart types** (candlestick, volume)
- **Configurable moving averages** periods

---

## 🎉 Ready to Start?

1. **Run the server**: `python start_server.py`
2. **Open the chart**: Navigate to `improved_btc_chart.html`
3. **Watch the magic**: Real-time BTC data visualization!

For questions or issues, check the console logs or modify the API endpoints as needed.