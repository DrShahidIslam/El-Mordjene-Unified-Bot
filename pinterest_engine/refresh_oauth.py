import os
import sys
import json
import base64
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from dotenv import load_dotenv, set_key

ROOT_DIR = Path(__file__).parent.parent
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

CLIENT_ID = os.getenv("PINTEREST_APP_ID", "1562363").strip()
CLIENT_SECRET = os.getenv("PINTEREST_APP_SECRET", "4a99a5b5175e38ba0aa1436602d334fa680d4180").strip()
REDIRECT_URI = "http://localhost:5000/admin/success.html"
SCOPES = "boards:read,boards:write,pins:read,pins:write,user_accounts:read"

AUTH_URL = (
    f"https://www.pinterest.com/oauth/?"
    f"client_id={CLIENT_ID}&"
    f"redirect_uri={REDIRECT_URI}&"
    f"response_type=code&"
    f"scope={SCOPES}"
)

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/admin/success.html":
            qs = parse_qs(parsed.query)
            code = qs.get("code", [None])[0]
            if code:
                print(f"\n[+] Authorization code received: {code[:10]}...")
                # Exchange code for tokens
                auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
                try:
                    res = requests.post(
                        "https://api.pinterest.com/v5/oauth/token",
                        headers={
                            "Authorization": f"Basic {auth_header}",
                            "Content-Type": "application/x-www-form-urlencoded"
                        },
                        data={
                            "grant_type": "authorization_code",
                            "code": code.strip(),
                            "redirect_uri": REDIRECT_URI
                        },
                        timeout=30
                    )
                    
                    if res.status_code == 200:
                        data = res.json()
                        access_token = data.get("access_token")
                        refresh_token = data.get("refresh_token")
                        
                        # Save to pinterest_auth.json
                        with open(ROOT_DIR / "pinterest_auth.json", "w") as f:
                            json.dump(data, f, indent=2)
                            
                        # Save to pinterest_token.json (for dashboard compatibility)
                        with open(ROOT_DIR / "pinterest_token.json", "w") as f:
                            json.dump(data, f, indent=2)

                        # Update .env
                        if ENV_PATH.exists():
                            set_key(str(ENV_PATH), "PINTEREST_ACCESS_TOKEN", access_token)
                            if refresh_token:
                                set_key(str(ENV_PATH), "PINTEREST_REFRESH_TOKEN", refresh_token)

                        self.send_response(200)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        html_response = f"""
                        <!DOCTYPE html>
                        <html>
                        <head><title>Pinterest Authentication Successful</title></head>
                        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #0f172a; color: #f8fafc;">
                            <h1 style="color: #22c55e;">Authentication Successful!</h1>
                            <p style="font-size: 1.1rem;">Tokens have been generated and saved locally to <code>pinterest_auth.json</code> and <code>.env</code>.</p>
                            <p>You can close this window and return to your terminal.</p>
                        </body>
                        </html>
                        """
                        self.wfile.write(html_response.encode())
                        
                        print("\n" + "="*70)
                        print("SUCCESS! PINTEREST TOKENS REFRESHED")
                        print("="*70)
                        print(f"\n[1] PINTEREST_ACCESS_TOKEN:\n{access_token}\n")
                        print(f"[2] PINTEREST_REFRESH_TOKEN:\n{refresh_token}\n")
                        print("="*70)
                        print("Saved to pinterest_auth.json and .env successfully.")
                        print("="*70)
                        
                        # Exit server after successful exchange
                        def shutdown_server():
                            import threading, time
                            time.sleep(1)
                            os._exit(0)
                        import threading
                        threading.Thread(target=shutdown_server).start()
                        return
                    else:
                        print(f"[-] Token exchange failed: {res.status_code} - {res.text}")
                        self.send_response(400)
                        self.send_header("Content-type", "text/html")
                        self.end_headers()
                        self.wfile.write(f"<h1>Token Exchange Failed</h1><p>{res.status_code}: {res.text}</p>".encode())
                except Exception as e:
                    print(f"[-] Error exchanging code: {e}")
            else:
                error = qs.get("error", ["Unknown error"])[0]
                error_desc = qs.get("error_description", [""])[0]
                print(f"[-] OAuth Error: {error} - {error_desc}")
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>OAuth Error</h1><p>{error}: {error_desc}</p>".encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server_address = ('', 5000)
    httpd = HTTPServer(server_address, OAuthCallbackHandler)
    print("="*70)
    print("PINTEREST OAUTH RE-AUTHENTICATION SERVER")
    print("="*70)
    print(f"Listening on: http://localhost:5000")
    print(f"\nPlease open this link in your browser to authorize Pinterest:\n")
    print(AUTH_URL)
    print("\n" + "="*70)
    print("Waiting for authorization callback...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
