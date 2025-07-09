# 🚀 BTC Historical Chart Setup Guide

## ✅ Problem Solved

Your repository has been configured to **maintain continuous historical data** across all JSON file generations. Charts will no longer reset every 8 hours!

## 🔧 What Was Changed

### 1. Enhanced Data Processing (`process_data.py`)
- **Before:** Only processed today's CSV data
- **After:** Processes ALL historical CSV files for complete dataset
- **New Files Generated:**
  - `historical.json` - Complete continuous dataset
  - `metadata.json` - Dataset information and quality metrics
  - `index.json` - File index and navigation
  - Individual daily JSONs (still generated for compatibility)

### 2. Improved Flask API (`logger.py`)
- **New Endpoints:**
  - `/historical.json` - **Primary endpoint for charts**
  - `/metadata.json` - Dataset metadata
  - `/index.json` - File index
  - `/chart-data?limit=1000` - Filtered data for performance

### 3. Moving Average Improvements
- **Historical Context:** MAs calculated with complete historical data
- **Quality Indicators:** `ma_50_valid`, `ma_100_valid`, `ma_200_valid` fields
- **No Gaps:** Continuous calculation across all time periods

## 🎯 Chart Integration

### Recommended Chart Configuration

**Primary Endpoint:** Use `/historical.json` for your charts

```javascript
// Example fetch for continuous data
const response = await fetch('http://your-server:10000/historical.json');
const historicalData = await response.json();

// Data structure:
// [{
//   "time": "2025-07-06T00:00:00.000",
//   "price": 60002,
//   "spread_avg_L20_pct": 0.0004666667,
//   "ma_50": 0.0004666667,
//   "ma_100": 0.0004666667,
//   "ma_200": 0.0004666667,
//   "ma_50_valid": false,    // true when 50+ data points
//   "ma_100_valid": false,   // true when 100+ data points
//   "ma_200_valid": false    // true when 200+ data points
// }]
```

### Alternative Endpoints for Performance

```javascript
// Last 1000 data points (faster loading)
fetch('/chart-data?limit=1000')

// Data from specific date
fetch('/chart-data?start_date=2025-01-01')

// Combined filters
fetch('/chart-data?limit=500&start_date=2025-01-01&end_date=2025-01-10')
```

## 🏃‍♂️ How to Run

### 1. Start the Logger
```bash
cd render_app
python3 logger.py
```

### 2. Test the API
```bash
# Check status
curl http://localhost:10000/

# Get historical data
curl http://localhost:10000/historical.json

# Get metadata
curl http://localhost:10000/metadata.json
```

### 3. Use the Example Chart
Open `chart_config_example.html` in a browser and update the API_BASE URL to your server.

## 📊 Data Flow

```
CSV Files (every 8 hours)
    ↓
process_csv_to_json() [called automatically]
    ↓
Load ALL historical CSVs
    ↓
Resample to 1-minute intervals
    ↓
Calculate MAs with full historical context
    ↓
Generate:
├── historical.json (continuous dataset)
├── output_YYYY-MM-DD.json (daily files)
├── metadata.json (dataset info)
└── index.json (file index)
```

## 🔄 Continuous Updates

### Automatic Processing
- Every time new data is logged (every second)
- `process_csv_to_json()` rebuilds the complete historical dataset
- Charts get updated data without losing historical context

### Data Persistence
- Historical data persists across CSV file rotations
- MAs maintain proper historical calculation context
- No chart resets or data gaps

## 📈 Chart Benefits

### ✅ Before vs After

| Before | After |
|--------|-------|
| ❌ Chart resets every 8 hours | ✅ Continuous historical data |
| ❌ MAs calculated on partial data | ✅ MAs with full historical context |
| ❌ Lost data between rotations | ✅ Complete data preservation |
| ❌ Inconsistent MA values | ✅ Reliable MA calculations |

### 🎯 MA Quality Indicators

Use the `ma_*_valid` fields to show data quality:

```javascript
// Example: Only show MA when sufficient data
if (dataPoint.ma_200_valid) {
    // Show 200-period MA (reliable)
} else {
    // Show warning or hide MA (insufficient data)
}
```

## 🛠️ Customization Options

### Performance Tuning
For large datasets, consider:

```javascript
// Option 1: Limit data points
fetch('/chart-data?limit=2000')

// Option 2: Date range filtering
fetch('/chart-data?start_date=2025-01-01')

// Option 3: Client-side sampling (every 5th point)
const sampledData = data.filter((_, i) => i % 5 === 0);
```

### Additional Metrics
Extend `process_data.py` to add more indicators:

```python
# Example: Add volatility calculation
df_1min["volatility"] = df_1min["spread_avg_L20_pct"].rolling(window=20).std()

# Example: Add volume-weighted averages
df_1min["vwma_50"] = (df_1min["spread_avg_L20_pct"] * df_1min["volume"]).rolling(50).sum() / df_1min["volume"].rolling(50).sum()
```

## 🔍 Troubleshooting

### Issue: Empty historical.json
**Solution:** Ensure CSV files exist in `render_app/data/`

### Issue: MAs all the same value
**Solution:** This is normal with insufficient data. MAs become meaningful after 50+ data points.

### Issue: Chart not updating
**Solution:** Check the API endpoint URLs and ensure the Flask server is running.

### Issue: Large file sizes
**Solution:** Use filtered endpoints (`/chart-data?limit=1000`) or implement client-side sampling.

## 🎉 Next Steps

1. **Accumulate Data:** Let the system run to build meaningful historical data
2. **Test Charts:** Use the example HTML file to verify continuous updates
3. **Monitor Performance:** Watch file sizes and consider filtering for large datasets
4. **Customize:** Add additional metrics or chart features as needed

Your charts will now maintain continuous historical context across all CSV rotations! 🚀