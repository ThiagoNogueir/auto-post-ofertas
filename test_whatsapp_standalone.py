import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv('EVOLUTION_API_URL', 'http://localhost:8080')
API_KEY = os.getenv('EVOLUTION_API_KEY')
INSTANCE = os.getenv('EVOLUTION_INSTANCE_NAME')
GROUP_ID = "120363422429816674@g.us" # ID do seu log

print(f"Testing Evolution API:")
print(f"URL: {BASE_URL}")
print(f"Instance: {INSTANCE}")
print(f"API Key: {API_KEY[:5]}..." if API_KEY else "None")
print(f"Group ID: {GROUP_ID}")

# 1. Check Instance Status
try:
    url = f"{BASE_URL}/instance/connectionState/{INSTANCE}"
    print(f"\nChecking connection state: {url}")
    headers = {'apikey': API_KEY}
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error checking instance: {e}")

# 2. Send Text Message
try:
    url = f"{BASE_URL}/message/sendText/{INSTANCE}"
    print(f"\nSending text message: {url}")
    payload = {
        "number": GROUP_ID,
        "text": "🤖 Teste de Debug PromoBot"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error sending message: {e}")

# 3. Send Image Message
try:
    url = f"{BASE_URL}/message/sendMedia/{INSTANCE}"
    print(f"\nSending IMAGE message: {url}")
    payload = {
        "number": GROUP_ID,
        "mediatype": "image",
        "media": "https://http2.mlstatic.com/D_NQ_NP_606997-MLA47665096338_092021-O.webp",
        "caption": "🤖 Teste de Imagem PromoBot"
    }
    response = requests.post(url, json=payload, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error sending image: {e}")
