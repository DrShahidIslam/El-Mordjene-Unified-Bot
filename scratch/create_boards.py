import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("PINTEREST_ACCESS_TOKEN")
url = "https://api.pinterest.com/v5/boards"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

boards_to_create = [
    {"name": "Viral Recipes & Food Trends", "description": "The most trending food concepts and viral recipes from TikTok and Instagram."},
    {"name": "Healthy Salad & Bowl Ideas", "description": "Fresh, nutritious, and easy salad recipes for a healthy lifestyle."},
    {"name": "Quick Weeknight Dinner Recipes", "description": "Fast and delicious dinner ideas for busy families."},
    {"name": "Decadent Desserts & Sweets", "description": "The ultimate collection of cakes, cookies, and chocolate treats."}
]

print("--- CREATING SPECIALIZED BOARDS ---")
for board in boards_to_create:
    response = requests.post(url, headers=headers, json=board)
    if response.status_code in (200, 201):
        data = response.json()
        print(f"CREATED: {data['name']} | ID: {data['id']}")
    else:
        print(f"FAILED to create {board['name']}: {response.status_code} | {response.text}")
