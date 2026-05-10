import os
import sys
from dotenv import load_dotenv

# Path to the config.py directory
sys.path.append(os.path.abspath("alerts_engine"))
import config

load_dotenv()
os_username = os.getenv("WP_USERNAME")
os_password = os.getenv("WP_APP_PASSWORD")

print(f"OS Username: '{os_username}'")
print(f"Config Username: '{config.WP_USERNAME}'")
print(f"OS Password match Config: {os_password == config.WP_APP_PASSWORD}")

if os_password != config.WP_APP_PASSWORD:
    print(f"OS Password length: {len(os_password) if os_password else 0}")
    print(f"Config Password length: {len(config.WP_APP_PASSWORD) if config.WP_APP_PASSWORD else 0}")
