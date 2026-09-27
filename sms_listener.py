import json
import subprocess
import time
import requests

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Send Error: {e}")

def send_control_panel(chat_id=TELEGRAM_CHAT_ID):
    text = (
        f"🚀 *SMS Manager Bot সচল আছে!*\n\n"
        f"✨ *CONTROL PANEL* ✨\n"
        f"⚙️ *স্ট্যাটাস:* `ONLINE (Manual Backup Mode)`\n\n"
        f"👇 Nicher button byabohar korun:"
    )
    reply_markup = {
        "keyboard": [
            [{"text": "⚡ BOT STATUS CHECK 📊"}],
            [{"text": "📂 BACKUP (সবশেষ এসএমএস)"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }
    send_message(chat_id, text, reply_markup)

def get_multiple_sms(limit=5):
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
                return sms_list
    except Exception as e:
        print(f"SMS Read Error: {e}")
    return []

def main():
    print("Manual Backup SMS Bot Running...")
    send_control_panel()
    
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=2"
            response = requests.get(url, timeout=5).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"]
                        
                        if "BOT STATUS CHECK" in text:
                            send_message(chat_id, "🟢 *Bot active ache ebong shudhu command-er opor vitti kore kaj korche!*")
                        elif "BACKUP" in text:
                            send_message(chat_id, "📂 *Shesh asha SMS-gula ana hocche...*")
                            sms_records = get_multiple_sms(5)
                            if sms_records:
                                for sms in sms_records:
                                    sender = sms.get('number', 'Unknown')
                                    body = sms.get('body', '')
                                    date = sms.get('received', '')
                                    
                                    backup_text = (
                                        f"📦 *[SMS UPDATE]*\n\n"
                                        f"👤 *Prerok:* `{sender}`\n"
                                        f"📅 *Somoy:* `{date}`\n"
                                        f"💬 *Message:* \n{body}"
                                    )
                                    send_message(chat_id, backup_text)
                            else:
                                send_message(chat_id, "⚠️ Kono SMS paowa jayni!")
        except Exception as e:
            pass
        
        time.sleep(1)

if __name__ == "__main__":
    main()
