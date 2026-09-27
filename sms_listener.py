import json
import subprocess
import time
import requests
import threading

# আপনার টেলিগ্রাম বটের টোকেন এবং চ্যাট আইডি
TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
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

def check_telegram_commands():
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url).json()
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"]
                        
                        if text == "/status":
                            reply_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                            requests.post(reply_url, json={
                                "chat_id": chat_id,
                                "text": "🟢 *বট বর্তমানে সচল এবং লাইভ আছে!* SMS মনিটরিং চলছে...",
                                "parse_mode": "Markdown"
                            })
        except Exception as e:
            print(f"Command Check Error: {e}")
        time.sleep(2)

def main():
    print("SMS to Telegram Bot listener started...")
    
    send_to_telegram("🚀 *বট সফলভাবে রান হয়েছে!*\n\nবট এখন সম্পূর্ণ সচল আছে এবং এসএমএস ট্র্যাক করছে। বটের অবস্থা জানতে `/status` লিখে পাঠান।")
    
    # এখানে .start() ঠিক করা হয়েছে (ছোট হাতের s দিয়ে)
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

                if any(x in sender for x in ["bKash", "Nagad", "16216", "BKASH", "NAGAD"]):
                    date = sms.get('received', '')
                    msg_text = (
                        f"📩 *নতুন পেমেন্ট এসএমএস এসেছে!*\n\n"
                        f"👤 *প্রেরক:* `{sender}`\n"
                        f"📅 *সময়:* `{date}`\n"
                        f"💬 *মেসেজ:* \n{body}"
                    )
                    send_to_telegram(msg_text)
                    print(f"Sent SMS from {sender} to Telegram.")

        time.sleep(3)

if __name__ == "__main__":
    main()
