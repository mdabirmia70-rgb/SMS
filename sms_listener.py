import json
import subprocess
import time
import requests
import threading

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

def send_control_panel(chat_id=TELEGRAM_CHAT_ID):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    text = (
        f"🚀 *SMS Forwarder Bot অপ্টিমাইজড মোডে সচল!*\n\n"
        f"✨ *CONTROL PANEL* ✨\n"
        f"⚙️ *স্ট্যাটাস:* `ONLINE (স্মার্ট ও ফাস্ট)`\n\n"
        f"👇 নিচের বাটন ব্যবহার করুন:"
    )
    
    reply_markup = {
        "keyboard": [
            [{"text": "⚡ BOT STATUS CHECK 📊"}],
            [{"text": "📂 BACKUP (সবশেষ এসএমএস)"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }
    
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Error: {e}")

def get_latest_sms():
    try:
        result = subprocess.run(['termux-sms-list', '-l', '1'], capture_output=True, text=True)
        sms_list = json.loads(result.stdout)
        if sms_list:
            return sms_list[0]
    except Exception as e:
        print(f"SMS Read Error: {e}")
    return None

def get_multiple_sms(limit=10):
    try:
        result = subprocess.run(['termux-sms-list', '-l', str(limit)], capture_output=True, text=True)
        sms_list = json.loads(result.stdout)
        if sms_list:
            return sms_list
    except Exception as e:
        print(f"SMS Backup Read Error: {e}")
    return []

def check_telegram_commands():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=5"
            response = requests.get(url).json()
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"]
                        
                        if "BOT STATUS CHECK" in text:
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
                                "chat_id": chat_id,
                                "text": "🟢 *বট সক্রিয় ও লাইভ আছে!*",
                                "parse_mode": "Markdown"
                            })
                        elif "BACKUP" in text:
                            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
                                "chat_id": chat_id,
                                "text": "📂 *ব্যাকআপ পাঠানো হচ্ছে...*",
                                "parse_mode": "Markdown"
                            })
                            
                            sms_records = get_multiple_sms(10)
                            if sms_records:
                                for sms in sms_records:
                                    sender = sms.get('number', 'Unknown')
                                    body = sms.get('body', '')
                                    date = sms.get('received', '')
                                    
                                    backup_text = (
                                        f"📦 *[SMS BACKUP]*\n\n"
                                        f"👤 *প্রেরক:* `{sender}`\n"
                                        f"📅 *সময়:* `{date}`\n"
                                        f"💬 *মেসেজ:* \n{body}"
                                    )
                                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
                                        "chat_id": chat_id,
                                        "text": backup_text,
                                        "parse_mode": "Markdown"
                                    })
                            else:
                                requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json={
                                    "chat_id": chat_id,
                                    "text": "⚠️ কোনো এসএমএস পাওয়া যায়নি!",
                                    "parse_mode": "Markdown"
                                })
        except Exception as e:
            print(f"Command Check Error: {e}")
        time.sleep(1)

def main():
    print("Optimized SMS Listener Running...")
    send_control_panel()
    
    threading.Thread(target=check_telegram_commands, daemon=True).start()

    last_sms_id = None
    initial_sms = get_latest_sms()
    if initial_sms:
        last_sms_id = initial_sms.get('_id')

    while True:
        sms = get_latest_sms()
        if sms:
            current_id = sms.get('_id')
            sender = sms.get('number', 'Unknown')
            body = sms.get('body', '')

            if current_id != last_sms_id:
                last_sms_id = current_id
                
                msg_text = (
                    f"📩 *নতুন এসএমএস এসেছে!*\n\n"
                    f"👤 *প্রেরক:* `{sender}`\n"
                    f"💬 *মেসেজ:* \n{body}"
                )
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                requests.post(url, json={
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": msg_text,
                    "parse_mode": "Markdown"
                })
                print(f"Forwarded SMS from {sender}")

        # আগের সময় ঠিক রাখা হলো যেন ব্যাটারি ও প্রসেসর ওভারলোড না হয়
        time.sleep(3)

if __name__ == "__main__":
    main()
