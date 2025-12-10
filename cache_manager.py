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
                return json.load(f)
    except Exception as e:
        print(f"Error loading cache: {e}")
    return None

def save_cache(data):
    """Save data to cache file"""
    try:
        with cache_lock:
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ Cache updated at {datetime.now().isoformat()}")
    except Exception as e:
        print(f"Error saving cache: {e}")

def is_cache_valid(cache_data):
    """Check if cache is less than 1 hour old"""
    if not cache_data or 'timestamp' not in cache_data:
        return False
    
    try:
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        age = datetime.now() - cache_time
        return age < timedelta(hours=1)
    except:
        return False

def update_gold_data():
    """Fetch all gold analysis data and cache it"""
    print("\n" + "="*60)
    print(f"🔄 UPDATING GOLD DATA CACHE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        # Run all analyses
        print("\n1️⃣ Fetching Trend Analysis...")
        trend_result = run_trend_analysis()
        
        print("\n2️⃣ Fetching Lower Limit...")
        lower_result = run_lower_limit_analysis()
        
        print("\n3️⃣ Fetching Upper Limit...")
        upper_result = run_upper_limit_analysis()
        
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
        
        # Create cache data
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "trend": trend,
            "lower_limit": lower_limit,
            "upper_limit": upper_limit,
            "raw_responses": {
                "trend": trend_result,
                "lower_limit": lower_result,
                "upper_limit": upper_result
            }
        }
        
        # Save to cache
        save_cache(cache_data)
        
        print("\n" + "="*60)
        print("✅ CACHE UPDATE COMPLETE")
        print(f"   Trend: {trend}")
        print(f"   Lower Limit: {lower_limit}")
        print(f"   Upper Limit: {upper_limit}")
        print("="*60 + "\n")
        
        return cache_data
        
    except Exception as e:
        print(f"❌ Error updating cache: {e}")
        return None

def get_gold_data_cached():
    """Get gold data from cache or update if expired"""
    cache_data = load_cache()
    
    if is_cache_valid(cache_data):
        print(f"✓ Using cached data from {cache_data['timestamp']}")
        return cache_data
    
    print("⚠️ Cache expired or missing, updating...")
    return update_gold_data()

def hourly_cache_updater():
    """Background thread to update cache every hour"""
    print("🕐 Hourly cache updater started")
    
    while True:
        try:
            # Wait 1 hour first
            
            # Then check if update is needed
            cache_data = load_cache()
            if not is_cache_valid(cache_data):
                print("⏰ Hourly update: Cache expired, updating...")
                update_gold_data()
            else:
                print("⏰ Hourly check: Cache still valid, skipping update")
            time.sleep(3600)  # 3600 seconds = 1 hour

        except Exception as e:
            print(f"Error in hourly updater: {e}")
            time.sleep(60)  # Wait 1 minute before retry

def start_cache_updater():
    """Start the background cache updater thread"""
    updater_thread = Thread(target=hourly_cache_updater, daemon=True)
    updater_thread.start()
    
    # Do initial update if cache doesn't exist or is expired
    cache_data = load_cache()
    if not is_cache_valid(cache_data):
        print("📊 Performing initial cache update...")
        update_gold_data()
