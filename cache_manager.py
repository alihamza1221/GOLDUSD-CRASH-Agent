import json
import os
from datetime import datetime, timedelta
from threading import Thread, Lock
import time
from agent import run_trend_analysis, run_lower_limit_analysis, run_upper_limit_analysis

# Cache file path
CACHE_FILE = "gold_data_cache.json"
cache_lock = Lock()

def load_cache():
    """Load cached data from file"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                # Migrate old format to new format if needed
                if 'symbols' not in data:
                    # Old format detected, migrate to new format
                    old_data = data
                    data = {
                        "last_updated": old_data.get('timestamp', datetime.now().isoformat()),
                        "symbols": {
                            "GOLDUSD": old_data
                        }
                    }
                    save_cache(data)
                return data
    except Exception as e:
        print(f"Error loading cache: {e}")
    return {"last_updated": None, "symbols": {}}

def save_cache(data):
    """Save data to cache file"""
    try:
        with cache_lock:
            data['last_updated'] = datetime.now().isoformat()
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Cache updated at {datetime.now().isoformat()}")
    except Exception as e:
        print(f"Error saving cache: {e}")

def is_symbol_cache_valid(symbol_data):
    """Check if symbol cache is less than 1 hour old"""
    if not symbol_data or 'timestamp' not in symbol_data:
        return False
    
    try:
        cache_time = datetime.fromisoformat(symbol_data['timestamp'])
        age = datetime.now() - cache_time
        return age < timedelta(hours=1)
    except:
        return False

def update_symbol_data(symbol: str):
    """Fetch all analysis data for a symbol and update cache"""
    print("\n" + "="*60)
    print(f"🔄 UPDATING {symbol} DATA - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Run all analyses for the symbol
        print(f"\n1️⃣ Fetching {symbol} Trend Analysis...")
        trend_result = run_trend_analysis(symbol)
        
        print(f"\n2️⃣ Fetching {symbol} Lower Limit...")
        lower_result = run_lower_limit_analysis(symbol)
        
        print(f"\n3️⃣ Fetching {symbol} Upper Limit...")
        upper_result = run_upper_limit_analysis(symbol)
        
        # Extract structured values
        trend = "unknown"
        if "TREND:" in trend_result:
            trend = trend_result.split("TREND:")[1].strip().split()[0].lower()
        
        lower_limit = "N/A"
        if "LIMIT:" in lower_result:
            lower_limit = lower_result.split("LIMIT:")[1].strip().split()[0]
        
        upper_limit = "N/A"
        if "LIMIT:" in upper_result:
            upper_limit = upper_result.split("LIMIT:")[1].strip().split()[0]
        
        # Create symbol data
        symbol_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "trend": trend,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit,
            "raw_responses": {
                "trend": trend_result,
                "lower_limit": lower_result,
                "upper_limit": upper_result
            }
        }
        
        # Load existing cache and update symbol
        cache_data = load_cache()
        cache_data['symbols'][symbol] = symbol_data
        save_cache(cache_data)
        
        print("\n" + "="*60)
        print(f"✅ {symbol} CACHE UPDATE COMPLETE")
        print(f"   Trend: {trend}")
        print(f"   Lower Limit: {lower_limit}")
        print(f"   Upper Limit: {upper_limit}")
        print("="*60 + "\n")
        
        return symbol_data
        
    except Exception as e:
        print(f"❌ Error updating {symbol} cache: {e}")
        return None

def update_all_symbols():
    """Update all symbols in cache"""
    cache_data = load_cache()
    symbols = list(cache_data.get('symbols', {}).keys())
    
    # Ensure GOLDUSD is always tracked
    if 'GOLDUSD' not in symbols:
        symbols.append('GOLDUSD')
    
    print(f"\n📊 Updating {len(symbols)} symbols: {', '.join(symbols)}")
    
    for symbol in symbols:
        update_symbol_data(symbol)

def get_symbol_data_cached(symbol: str = "GOLDUSD"):
    """Get symbol data from cache or update if expired"""
    cache_data = load_cache()
    symbol_data = cache_data.get('symbols', {}).get(symbol)
    
    if is_symbol_cache_valid(symbol_data):
        print(f"✓ Using cached data for {symbol} from {symbol_data['timestamp']}")
        return symbol_data
    
    print(f"⚠️ Cache for {symbol} expired or missing, updating...")
    return update_symbol_data(symbol)

def get_all_cached_symbols():
    """Get all cached symbols data"""
    return load_cache()

def add_symbol_to_cache(symbol: str):
    """Add a new symbol to cache tracking and fetch its data"""
    print(f"📈 Adding new symbol: {symbol}")
    return update_symbol_data(symbol)

# Backward compatibility
def get_gold_data_cached():
    """Backward compatible function - Get gold data from cache"""
    return get_symbol_data_cached("GOLDUSD")

def update_gold_data():
    """Backward compatible function - Update gold data"""
    return update_symbol_data("GOLDUSD")

def hourly_cache_updater():
    """Background thread to update cache every hour"""
    print("🕐 Hourly cache updater started")
    
    while True:
        try:
            # Wait 1 hour first before checking (initial update is done by start_cache_updater)
            time.sleep(3600)  # 3600 seconds = 1 hour
            
            # Then check if update is needed
            cache_data = load_cache()
            symbols = list(cache_data.get('symbols', {}).keys())
            
            # Ensure GOLDUSD is always tracked
            if not symbols:
                symbols = ['GOLDUSD']
            
            needs_update = False
            for symbol in symbols:
                symbol_data = cache_data.get('symbols', {}).get(symbol)
                if not is_symbol_cache_valid(symbol_data):
                    needs_update = True
                    break
            
            if needs_update:
                print("⏰ Hourly update: Some symbols expired, updating all...")
                update_all_symbols()
            else:
                print("⏰ Hourly check: All symbols still valid, skipping update")

        except Exception as e:
            print(f"Error in hourly updater: {e}")
            time.sleep(60)  # Wait 1 minute before retry

def start_cache_updater():
    """Start the background cache updater thread"""
    updater_thread = Thread(target=hourly_cache_updater, daemon=True)
    updater_thread.start()
    
    # Do initial update if cache doesn't exist or is expired
    cache_data = load_cache()
    symbols = list(cache_data.get('symbols', {}).keys())
    
    if not symbols:
        print("📊*** Performing initial cache update for GOLDUSD ***")
        update_symbol_data("GOLDUSD")
    else:
        # Check if any symbol needs update
        for symbol in symbols:
            symbol_data = cache_data.get('symbols', {}).get(symbol)
            if not is_symbol_cache_valid(symbol_data):
                print(f"📊 ******Cache for {symbol} expired, updating...")
                update_symbol_data(symbol)
