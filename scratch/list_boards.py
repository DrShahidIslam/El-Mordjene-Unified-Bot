import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("PINTEREST_ACCESS_TOKEN")
url = "https://api.pinterest.com/v5/boards"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    boards = response.json().get("items", [])
    print("--- YOUR PINTEREST BOARDS ---")
    for b in boards:
        print(f"ID: {b['id']} | Name: {b['name']}")
else:
    print(f"Error fetching boards: {response.status_code}")
    print(response.text)
