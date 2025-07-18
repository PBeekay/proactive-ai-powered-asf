# worker.py (Final Combined Version with Proxy)

# --- 1. Import libraries ---
import pika
import time
import json
import requests
import redis
from pika.exceptions import AMQPConnectionError
from redis.exceptions import ConnectionError
from typing import Dict, Optional # Import typing for clarity

# --- 2. Setup Redis Connection ---
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
    print("[+] Connected to Redis successfully!")
except ConnectionError as e:
    print(f"[!] Could not connect to Redis. Please ensure it's running. Error: {e}")
    exit()

# This is the key our threat intel worker uses to store the blocklist.
BLOCKLIST_KEY = "spam_keywords" 

# --- 3. Create the function to call the Gemini API ---
def analyze_with_llm(content_to_analyze: str):
    """Analyzes content using the Gemini API for deep contextual understanding."""
    print("     [LLM] Calling Gemini API for analysis...")
    
    apiKey = "" # Your API Key

    if not apiKey:
        print("     [!] FATAL: Gemini API key is missing.")
        return {"verdict": "ham", "reason": "API key not configured."}

    prompt = f"""
    Analyze the following text and determine if it is 'spam' or 'ham' (legitimate).
    Your response must be a JSON object with two keys: "verdict" and "reason".

    Text to analyze: "{content_to_analyze}"

    JSON Response:
    """
    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    # --- FIX: Type-Safe Proxy Configuration ---
    # Define proxy URLs as string or None. This makes configuration clear.
    http_proxy: Optional[str] = None  # Example: 'http://127.0.0.1:8080'
    https_proxy: Optional[str] = None # Example: 'https://user:pass@127.0.0.1:8080'

    # Build the proxies dictionary dynamically, ensuring it only contains strings.
    # This resolves the static type error.
    proxies: Dict[str, str] = {}
    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy

    try:
        # The 'proxies' parameter is added to the requests call.
        # We pass the dictionary only if it's not empty.
        response = requests.post(apiUrl, json=payload, timeout=20, proxies=proxies if proxies else None)
        response.raise_for_status()
        result = response.json()
        content_part = result['candidates'][0]['content']['parts'][0]['text']
        cleaned_json_str = content_part.strip().replace('```json', '').replace('```', '')
        return json.loads(cleaned_json_str)
    except Exception as e:
        print(f"     [!] Error during LLM call: {e}")
        return {"verdict": "ham", "reason": "API call failed."}

# --- 4. Define the main callback function ---
def callback(ch, method, properties, body):
    """Processes a message using both Redis and the Gemini API."""
    print("\n [x] Received message from queue...")
    
    message_data = json.loads(body.decode())
    content = message_data.get("content", "").lower()
    
    print(f"     Content: '{content}'")
    
    # --- Step 1: Check against the live Redis blocklist ---
    is_blocklisted = False
    # We check if any word from the content is in our Redis set.
    # This is a simple but effective check against known bad keywords/domains.
    for word in content.split():
        if redis_client.sismember(BLOCKLIST_KEY, word):
            print(f"     [!] Reputation Check: SPAM (Found blocked keyword: '{word}')")
            is_blocklisted = True
            break
    
    # --- Step 2: Get a deep analysis from the Cloud AI ---
    llm_analysis = analyze_with_llm(content)
    llm_verdict_is_spam = llm_analysis.get("verdict", "ham").lower() == "spam"
    
    # --- Step 3: Combine the evidence for a final decision ---
    # If it's on our live blocklist OR the powerful AI says it's spam, we block it.
    if is_blocklisted or llm_verdict_is_spam:
        print(f"     [!] FINAL VERDICT: SPAM")
        if is_blocklisted:
             print("         Reason: Matched live threat intelligence database (Redis).")
        if llm_verdict_is_spam:
             print(f"         Reason: Deep content analysis by AI. (AI Reason: {llm_analysis.get('reason')})")
    else:
        print("     [✓] FINAL VERDICT: Not Spam (Ham)")
        
    print(" [x] Done processing.")
    ch.basic_ack(delivery_tag=method.delivery_tag)


# --- 5. Main function to start the worker ---
def main():
    """Main loop to connect and consume messages."""
    connection = None
    while True:
        try:
            print("[*] Attempting to connect to RabbitMQ...")
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue='task_queue', durable=True)
            print(' [*] Combined Intelligence Worker is waiting for messages. To exit press CTRL+C')
            channel.basic_consume(queue='task_queue', on_message_callback=callback)
            channel.start_consuming()

        except AMQPConnectionError as e:
            print(f" [!] Connection failed: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n[*] Shutting down...")
            if connection and connection.is_open:
                connection.close()
            break


# --- 6. Run the worker ---
if __name__ == '__main__':
    main()
