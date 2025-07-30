# threat_intel_worker.py

# --- 1. Import necessary libraries ---
import requests
import redis
import time
# --- FIX: Import the specific exception class directly ---
from redis.exceptions import ConnectionError

# --- 2. Configuration ---

BLOCKLIST_KEY = "spam_keywords" 
THREAT_FEEDS = [
    "https://raw.githubusercontent.com/mitchellkrogza/Phishing.Database/master/phishing-domains-ACTIVE.txt"
]

UPDATE_INTERVAL = 1800

# --- 3. Setup Redis Connection ---
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("[+] Connected to Redis server successfully!")
# --- FIX: Catch the specific ConnectionError exception ---
except ConnectionError as e:
    print(f"[!] FATAL: Could not connect to Redis. Please ensure it's running. Error: {e}")
    exit()

# --- 4. Core Logic ---

def fetch_and_parse_feed(url):
    """Downloads a blocklist feed and parses out domains."""
    print(f"[*] Fetching threat feed from: {url}")
    try:
        # Use a common user-agent to avoid being blocked
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, timeout=20, headers=headers)
        response.raise_for_status()
        
        # The list contains one domain per line. We create a set to hold them.
        entries = set(response.text.splitlines())
        
        print(f"[*] Found {len(entries)} domains in the feed.")
        return entries
        
    except requests.exceptions.RequestException as e:
        print(f"[!] Warning: Could not fetch feed. Error: {e}")
        return set() # Return an empty set on failure

def update_reputation_database():
    """Main function to fetch all feeds and update Redis."""
    print("\n--- Starting Threat Intelligence Update Cycle ---")
    
    all_new_threats = set()
    for feed_url in THREAT_FEEDS:
        threats_from_feed = fetch_and_parse_feed(feed_url)
        all_new_threats.update(threats_from_feed)
    
    if not all_new_threats:
        print("[*] No new threats found in this cycle.")
        return

    pipeline = redis_client.pipeline()
    pipeline.sadd(BLOCKLIST_KEY, *all_new_threats)
    
    # Execute the pipeline
    pipeline.execute()
    
    # Get the total number of items in our blocklist now
    total_threats = redis_client.scard(BLOCKLIST_KEY)
    
    print(f"[+] Successfully added/updated the Redis blocklist.")
    print(f"[+] Total threats in database: {total_threats}")
    print("--- Finished Threat Intelligence Update Cycle ---")


# --- 5. Main Loop ---
if __name__ == "__main__":
    while True:
        update_reputation_database()
        print(f"\n[*] Sleeping for {UPDATE_INTERVAL // 60} minutes...")
        time.sleep(UPDATE_INTERVAL)
