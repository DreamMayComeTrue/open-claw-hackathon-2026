"""
Find Chinese voices from your Cartesia account
python find_voice.py
"""
import os, requests, json
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("CARTESIA_API_KEY", "")
if not key:
    print("❌ CARTESIA_API_KEY not set in .env")
    exit()

resp = requests.get(
    "https://api.cartesia.ai/voices",
    headers={"X-API-Key": key, "Cartesia-Version": "2025-04-16"},
)

if resp.status_code != 200:
    print(f"❌ Error: {resp.status_code} {resp.text}")
    exit()

data = resp.json()
print(f"Raw response type: {type(data)}")
print(json.dumps(data, indent=2)[:2000])  # print first 2000 chars raw