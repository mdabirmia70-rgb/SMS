import json
import subprocess
import time
import requests
import threading

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }, timeout=5)
    except Exception as e:
        print(f"Send Error: {e}")

def send_control_panel(chat_id=TELEGRAM_CHAT_ID):
    text = (
        f"🚀 *SMS Forwarder Bot অপ্টিমাইজড মোডে সচল!*\n\n"
        f"✨ *CONTROL PANEL* ✨\n"
        f"⚙️ *স্ট্যাটাস:* `ONLINE (Fast Response)`\n\n"
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
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": reply_markup
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Panel Error: {e}")

def get_sms(limit=1):
    try:
        result = subprocess.run(
            ['termux-sms-list', '-l', str(limit)], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            sms_list = json.loads(result.stdout)
            if sms_list:
                return sms_list if limit > 1 else sms_list[0]
    except Exception as e:
        print(f"SMS Read Error: {e}")
    return [] if limit > 1 else None

def check_telegram_commands():
    offset = 0
    while True:
        try:
            # timeout কমিয়ে শূন্য করে দেওয়া হয়েছে যাতে ইনস্ট্যান্ট কমান্ড ক্যাচ করে
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=0"
            response = requests.get(url, timeout=3).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"]
                        
                        if "BOT STATUS CHECK" in text:
                            send_message(chat_id, "🟢 *বট পুরোপুরি সচল ও দ্রুত কাজ করছে!*")
                        elif "BACKUP" in text:
                            send_message(chat_id, "📂 *সাম্প্রতিক এসএমএস ব্যাকআপ আনা হচ্ছে...*")
                            sms_records = get_sms(5)
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
                                    send_message(chat_id, backup_text)
                            else:
                                send_message(chat_id, "⚠️ কোনো এসএমএস পাওয়া যায়নি!")
        except Exception as e:
            pass
        
        time.sleep(0.5)

def main():
    print("Optimized SMS Listener Running...")
    send_control_panel()
    
    # ব্যাকগ্রাউন্ডে কমান্ড চেকিং থ্রেড চালু করা হলো
    threading.Thread(target=check_telegram_commands, daemon=True).start()

    last_sms_id = None
    initial_sms = get_sms(1)
    if initial_sms:
        last_sms_id = initial_sms.get('_id')

    while True:
        sms = get_sms(1)
        if sms:
            current_id = sms.get('_id')
            if current_id != last_sms_id:
                last_sms_id = current_id
                sender = sms.get('number', 'Unknown')
                body = sms.get('body', '')

                msg_text = (
                    f"📩 *নতুন এসএমএস এসেছে!*\n\n"
                    f"👤 *প্রেরক:* `{sender}`\n"
                    f"💬 *মেসেজ:* \n{body}"
                )
                send_message(TELEGRAM_CHAT_ID, msg_text)
                print(f"Forwarded SMS from {sender}")

        time.sleep(2)

if __name__ == "__main__":
    main()
