import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {'timeout': 100, 'offset': offset}
    response = requests.get(url, params=params)
    return response.json()

def main():
    print("🤖 Telegram ID Finder Started")
    print("---------------------------------")
    print(f"Bot Token: {TOKEN[:10]}...")
    print("\n👉 INSTRUCTIONS:")
    print("1. Add the bot to your Group or Channel as Administrator.")
    print("2. Send a message in that Group/Channel (e.g., 'Hello Bot').")
    print("3. Wait a few seconds for it to appear below.")
    print("---------------------------------\n")

    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    chat = None
                    if "message" in update:
                        chat = update["message"]["chat"]
                    elif "channel_post" in update:
                        chat = update["channel_post"]["chat"]
                    elif "my_chat_member" in update:
                        chat = update["my_chat_member"]["chat"]
                        print(f"🎉 Bot added to: {chat['title']} (ID: {chat['id']})")
                        continue
                        
                    if chat:
                        chat_type = chat.get("type")
                        title = chat.get("title", "Private Chat")
                        chat_id = chat.get("id")
                        
                        print(f"📩 New Message Detected!")
                        print(f"   Type: {chat_type}")
                        print(f"   Name: {title}")
                        print(f"   ID:   {chat_id}")
                        print("   -------------------")
                        
            time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
