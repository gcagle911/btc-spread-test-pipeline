# Moving Average and JSON Analysis

## Overview
Your project has two different approaches for calculating Moving Averages (MAs) and generating JSON outputs from cryptocurrency market data (BTC-USD from Coinbase).

## Moving Average Calculations

### 1. Current Implementation in `process_data.py`
**Location:** Lines 39-42
```python
# Calculate moving averages
df_1min["ma_50"] = df_1min["spread_avg_L20_pct"].rolling(window=50).mean()
df_1min["ma_100"] = df_1min["spread_avg_L20_pct"].rolling(window=100).mean()
df_1min["ma_200"] = df_1min["spread_avg_L20_pct"].rolling(window=200).mean()
```

**Characteristics:**
- **Data Source:** `spread_avg_L20_pct` (percentage spread based on top 20 bid/ask levels)
- **Timeframe:** 1-minute resampled data
- **Window Sizes:** 50, 100, and 200 periods
- **Method:** Simple Moving Average using pandas `.rolling().mean()`
- **Scope:** Processes only today's data (latest CSV file)

### 2. Alternative Implementation in `merge_and_process.py`
**Location:** Lines 45-48
```python
# STEP 4: Add MAs
result["ma50"] = result["spread_avg_L20_pct"].rolling(50).mean()
result["ma100"] = result["spread_avg_L20_pct"].rolling(100).mean()
result["ma200"] = result["spread_avg_L20_pct"].rolling(200).mean()
```

**Characteristics:**
- **Data Source:** Same `spread_avg_L20_pct`
- **Timeframe:** 1-minute resampled data
- **Window Sizes:** Same (50, 100, 200)
- **Method:** Same Simple Moving Average
- **Scope:** Processes ALL historical CSV files grouped by date

## JSON Output Analysis

### 1. JSON Generation in `process_data.py`
**Process:**
1. Resamples tick data to 1-minute intervals
2. Calculates MAs
3. Outputs single JSON file for current date

**Format:**
```python
df_1min.to_json(output_path, orient="records", date_format="iso")
```

**Output Structure:**
- **Filename:** `output_YYYY-MM-DD.json`
- **Format:** Array of records
- **Fields:** `time`, `price`, `spread_avg_L20_pct`, `ma_50`, `ma_100`, `ma_200`

### 2. JSON Generation in `merge_and_process.py`
**Process:**
1. Groups all CSV files by date
2. Merges multiple files per day
3. Creates OHLC data + spread averages
4. Generates JSON for each day + index file

**Additional Features:**
- Creates OHLC (Open, High, Low, Close) data from price
- Generates `index.json` with list of available days
- Processes historical data comprehensively

## Data Flow

### Raw Data (CSV)
**Source:** Coinbase Pro API (`BTC-USD`)
**Fields:** `timestamp`, `price`, `bid`, `ask`, `spread`, `volume`, `spread_avg_L20`, `spread_avg_L20_pct`
**Update Frequency:** Every second
**File Rotation:** Every 8 hours (00:00, 08:00, 16:00 UTC)

### Processed Data (JSON)
**Resampling:** 1-minute intervals
**MA Calculation:** Based on `spread_avg_L20_pct`
**Serving:** Via Flask API endpoints

## Key Observations & Recommendations

### ✅ Strengths
1. **Consistent MA Logic:** Both implementations use the same calculation method
2. **Clean Data Pipeline:** Clear separation between data collection, processing, and serving
3. **Real-time Updates:** `logger.py` automatically generates JSON after each data update
4. **API Access:** Flask endpoints for accessing both raw CSV and processed JSON data

### ⚠️ Potential Issues

1. **Duplicate Processing Logic:** 
   - Two separate files doing similar MA calculations
   - Consider consolidating into one function

2. **MA Data Sufficiency:**
   - 200-period MA needs 200 data points (3+ hours of 1-min data)
   - Early periods will have NaN values
   - Current data shows only 3 rows, insufficient for reliable MAs

3. **Missing Historical Context:**
   - `process_data.py` only uses current day's data
   - MAs are more meaningful with longer historical context
   - `merge_and_process.py` is better for this purpose

4. **Data Validation:**
   - No checks for sufficient data before MA calculation
   - No handling of market gaps/closures

### 🔧 Recommended Improvements

1. **Consolidate MA Logic:**
   ```python
   def calculate_moving_averages(df, column='spread_avg_L20_pct', windows=[50, 100, 200]):
       for window in windows:
           df[f'ma_{window}'] = df[column].rolling(window=window).mean()
       return df
   ```

2. **Add Data Validation:**
   ```python
   def validate_ma_data(df, min_periods=200):
       if len(df) < min_periods:
           print(f"⚠️ Insufficient data: {len(df)} rows, need {min_periods} for reliable MAs")
           return False
       return True
   ```

3. **Enhanced JSON Output:**
   - Include metadata (calculation timestamp, data quality indicators)
   - Add more statistical measures (volatility, volume-weighted averages)
   - Include confidence intervals for MAs

## Current File Structure
```
render_app/
├── logger.py              # Data collection + Flask API
├── process_data.py        # Daily JSON generation (current approach)
├── merge_and_process.py   # Historical data processing
├── requirements.txt       # Dependencies
└── render_app/
    └── data/
        └── 2025-07-06.csv # Sample data (only 3 rows)
```

## Next Steps
1. **Choose Primary Approach:** Decide between daily (`process_data.py`) vs historical (`merge_and_process.py`) processing
2. **Accumulate More Data:** Current sample has insufficient data for meaningful MAs
3. **Test MA Accuracy:** Verify calculations with known test data
4. **Enhance Error Handling:** Add validation for edge cases