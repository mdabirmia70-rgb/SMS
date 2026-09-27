import json
import subprocess
import requests
import time

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

# স্টেট ট্র্যাক করার ভেরিয়েবল
waiting_for_limit = False

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
        response = requests.post(url, json=payload, timeout=5)
        return response.json()
    except Exception as e:
        print(f"Send Error: {e}")
    return None

def send_control_panel(chat_id=TELEGRAM_CHAT_ID):
    text = (
        f"🚀 *SMS Manager Bot সচল আছে!*\n\n"
        f"✨ *CONTROL PANEL* ✨\n"
        f"⚙️ *স্ট্যাটাস:* `ONLINE (Flow Fixed)`\n\n"
        f"👇 নিচের যেকোনো একটি বাটন ব্যবহার করুন:"
    )
    reply_markup = {
        "keyboard": [
            [{"text": "BOT STATUS CHECK"}],
            [{"text": "MESSAGE LIST"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }
    send_message(chat_id, text, reply_markup)

def get_all_sms(limit=30):
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
    global waiting_for_limit
    print("Flow Fixed SMS Bot Started...")
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset=-1"
        res = requests.get(url, timeout=5).json()
        if "result" in res and res["result"]:
            offset = res["result"][-1]["update_id"] + 1
        else:
            offset = 0
    except:
        offset = 0

    send_control_panel()
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    
                    # ১. ইনলাইন বাটন ক্লিক (নির্দিষ্ট নাম্বারের মেসেজ দেখার জন্য)
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        callback_id = callback["id"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        data = callback["data"]
                        
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})
                        
                        if data.startswith("read_"):
                            target_sender = data.replace("read_", "")
                            sms_records = get_all_sms(50)
                            matched_sms = [s for s in sms_records if s.get('number', '') == target_sender]
                            
                            if matched_sms:
                                result_msg = f"🔍 *`{target_sender}` থেকে প্রাপ্ত সম্পূর্ণ মেসেজসমূহ:*\n\n"
                                for sms in matched_sms:
                                    body = sms.get('body', '')
                                    date = sms.get('received', '')
                                    result_msg += f"📅 *সময়:* `{date}`\n💬 *মেসেজ:* \n{body}\n\n===================\n\n"
                                send_message(chat_id, result_msg)
                            else:
                                send_message(chat_id, f"❌ `{target_sender}` এর কোনো মেসেজ পাওয়া যায়নি।")
                                
                    # ২. টেক্সট মেসেজ বা বাটন ইনপুট হ্যান্ডেল করা
                    elif "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"].strip()
                        clean_text = text.replace("🟢", "").replace("📥", "").strip()
                        
                        if clean_text == "BOT STATUS CHECK":
                            waiting_for_limit = False
                            send_message(chat_id, "🟢 *বট বর্তমানে অনলাইন (ONLINE) রয়েছে!*")
                            
                        elif clean_text == "MESSAGE LIST":
                            waiting_for_limit = True
                            send_message(chat_id, "🔢 *সাম্প্রতিক কয়টি মেসেজ দেখতে চান?*\n\nদয়া করে একটি সংখ্যা লিখে পাঠান (যেমন: `5`, `10` বা `15`)[span_4](start_span)[span_4](end_span)।")
                            
                        elif waiting_for_limit:
                            # ইউজার যখন সংখ্যা পাঠাবে (যেমন 5 বা 10)
                            if text.isdigit():
                                limit_num = int(text)
                                if limit_num > 25:
                                    limit_num = 25
                                    
                                sms_records = get_all_sms(limit_num)
                                if sms_records:
                                    unique_senders = []
                                    list_text = f"📋 *সর্বশেষ {len(sms_records)}টি মেসেজের প্রেরকগণ:*\n\n"
                                    inline_keyboard = []
                                    
                                    for sms in sms_records:
                                        sender = sms.get('number', 'Unknown')
                                        date = sms.get('received', 'N/A')
                                        
                                        if sender not in unique_senders:
                                            unique_senders.append(sender)
                                            list_text += f"👤 *নাম্বার:* `{sender}`\n📅 *সময়:* `{date}`\n-------------------\n"
                                            inline_keyboard.append([{"text": f"📩 মেসেজ পড়ুন: {sender}", "callback_data": f"read_{sender}"}])
                                    
                                    reply_markup = {"inline_keyboard": inline_keyboard}
                                    list_text += "\n👇 *যেকোনো নাম্বারের সম্পূর্ণ মেসেজ পড়তে নিচে ক্লিক করুন:*"
                                    
                                    send_message(chat_id, list_text, reply_markup=reply_markup)
                                    waiting_for_limit = False  # কাজ শেষ, স্টেট রিসেট
                                else:
                                    send_message(chat_id, "⚠️ ফোনে কোনো এসএমএস পাওয়া যায়নি!")
                                    waiting_for_limit = False
                            else:
                                send_message(chat_id, "❌ ভুল ইনপুট! দয়া করে শুধু একটি সংখ্যা লিখে পাঠান (যেমন: 5 বা 10)।")
                        else:
                            # যদি অন্য কোনো সাধারণ লেখা লেখে
                            send_message(chat_id, "দয়া করে নিচের মূল বাটনগুলো ব্যবহার করুন অথবা 'MESSAGE LIST' এ চাপ দিন[span_5](start_span)[span_5](end_span)।")
                            
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()



