"""
Check if .env is loading correctly from the right directory
python debug_env.py
"""
import os
import sys
from dotenv import load_dotenv

print(f"Running from: {os.getcwd()}")
print(f"Python: {sys.executable}")
print()

# Try loading .env
result = load_dotenv(verbose=True)
print(f"dotenv loaded: {result}")
print()

key = os.getenv("ELEVENLABS_API_KEY", "")
print(f"ELEVENLABS_API_KEY: '{key[:8]}...{key[-4:]}' (length: {len(key)})")

# Check for hidden characters
if key:
    print(f"First char code: {ord(key[0])}")  # should be normal letter/number
    print(f"Has spaces: {' ' in key}")
    print(f"Has quotes: {chr(34) in key or chr(39) in key}")
    print(f"Has newline: {chr(10) in key or chr(13) in key}")
