import os
import requests
from dotenv import load_dotenv
import json

load_dotenv()

def test_siliconflow():
    api_key = os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        print("Missing SILICONFLOW_API_KEY")
        return

    url = "https://api.siliconflow.cn/v1/user/info"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    print(f"Testing SiliconFlow connection to {url}...")
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            user_data = res.json().get('data', {})
            # Avoid printing non-ascii names
            print(f"SUCCESS: Connected! User ID: {user_data.get('id')}")
            
            # Check credits
            res_bal = requests.get("https://api.siliconflow.cn/v1/user/balance", headers=headers, timeout=15)
            if res_bal.status_code == 200:
                bal_data = res_bal.json()
                print(f"Balance Info: {json.dumps(bal_data)}")
        else:
            print(f"FAIL: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    test_siliconflow()
