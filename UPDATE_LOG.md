# BTC Data Pipeline Updates

## 2025-07-10 - Timestamp Fix and Enhanced Debugging

### Changes Made:
1. **Fixed Historical Data Update Issue** - `process_data.py`
   - Enhanced timestamp checking with detailed logging
   - Added error handling for file timestamp operations
   - Historical data should now update properly after 1+ hours

2. **Enhanced CSV File Discovery** - `process_data.py`
   - Added comprehensive debugging for CSV file loading
   - Shows file sizes and date ranges for each loaded file
   - Better error messages when files can't be loaded

3. **New Debug Endpoint** - `logger.py`
   - Added `/debug-status` endpoint for system diagnostics
   - Shows file timestamps, ages, and sizes
   - Helps troubleshoot data update issues

### Issue Being Fixed:
- Historical.json was not updating despite being 11+ hours old
- Timestamp checking logic was incorrectly reporting "updated within last hour"
- Missing visibility into which CSV files were being found/loaded

### Expected Results:
- Historical.json should update immediately (it's overdue)
- Better logging in Render console showing exact file ages
- Debug endpoint available for troubleshooting

### Test URLs After Deploy:
- `/debug-status` - Shows current system status
- `/historical.json` - Should have fresh timestamp
- `/metadata.json` - Should show updated generation time