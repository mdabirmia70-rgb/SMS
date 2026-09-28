import json
import subprocess
import requests
import time
from datetime import datetime

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

current_state = None
selected_sender = None

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
        f"🚀 *এসএমএস ম্যানেজার বট সচল আছে!*\n\n"
        f"✨ *কন্ট্রোল প্যানেল* ✨\n"
        f"⚙️ *স্ট্যাটাস:* `অনলাইন (এক্সাক্ট ম্যাচ মোড)`\n\n"
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

def get_all_sms(limit=200):
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
                try:
                    sms_list.sort(key=lambda x: x.get('received', ''), reverse=True)
                except:
                    pass
                return sms_list
    except Exception as e:
        print(f"SMS Read Error: {e}")
    return []

def main():
    global current_state, selected_sender
    print("Exact Match SMS Bot Started...")
    
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
                    
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        callback_id = callback["id"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        data = callback["data"]
                        
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})
                        
                        if data.startswith("select_"):
                            selected_sender = data.replace("select_", "")
                            current_state = "WAITING_FOR_COUNT"
                            send_message(chat_id, f"📱 *নির্বাচিত প্রেরক:* `{selected_sender}`\n\n🔢 *এই নির্দিষ্ট প্রেরকের কয়টি মেসেজ দেখতে চান?*\n(দয়া করে একটি সংখ্যা লিখে পাঠান, যেমন: `1`, `2`, `5`)")
                            
                    elif "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"].strip()
                        clean_text = text.replace("🟢", "").replace("📥", "").strip()
                        
                        if clean_text == "BOT STATUS CHECK":
                            current_state = None
                            send_message(chat_id, "🟢 *বট বর্তমানে অনলাইন (ONLINE) রয়েছে!*")
                            
                        elif clean_text == "MESSAGE LIST":
                            current_state = "WAITING_FOR_LIMIT"
                            send_message(chat_id, "🔢 *সাম্প্রতিক কয়টি মেসেজ লিস্ট দেখতে চান?*\n\nদয়া করে একটি সংখ্যা লিখে পাঠান (যেমন: `10`, `20` বা `30`).")
                            
                        elif current_state == "WAITING_FOR_LIMIT":
                            if text.isdigit():
                                limit_num = int(text)
                                if limit_num > 50:
                                    limit_num = 50
                                    
                                sms_records = get_all_sms(limit_num)
                                if sms_records:
                                    unique_senders = []
                                    list_text = f"📋 *সর্বশেষ {len(sms_records)}টি মেসেজ থেকে প্রাপ্ত প্রেরকগণ:*\n\n"
                                    inline_keyboard = []
                                    
                                    for sms in sms_records:
                                        sender = sms.get('number', 'Unknown')
                                        date = sms.get('received', 'N/A')
                                        
                                        if sender not in unique_senders:
                                            unique_senders.append(sender)
                                            list_text += f"👤 *নাম্বার/প্রেরক:* `{sender}`\n📅 *সময়:* `{date}`\n-------------------\n"
                                            inline_keyboard.append([{"text": f"👉 {sender}", "callback_data": f"select_{sender}"}])
                                    
                                    reply_markup = {"inline_keyboard": inline_keyboard}
                                    list_text += "\n👇 *যেকোনো প্রেরকের ওপর ক্লিক করুন:*"
                                    
                                    send_message(chat_id, list_text, reply_markup=reply_markup)
                                    current_state = None
                                else:
                                    send_message(chat_id, "⚠️ ফোনে কোনো এসএমএস পাওয়া যায়নি!")
                                    current_state = None
                            else:
                                send_message(chat_id, "❌ ভুল ইনপুট! দয়া করে শুধু একটি সংখ্যা লিখে পাঠান (যেমন: 10 বা 20)।")
                                
                        elif current_state == "WAITING_FOR_COUNT":
                            if text.isdigit():
                                count_num = int(text)
                                # পর্যাপ্ত মেসেজ (২০০টি) ফেচ করে একদম নিখুঁতভাবে (Exact Match) ফিল্টার করা হচ্ছে
                                sms_records = get_all_sms(200)
                                
                                matched_sms = []
                                for s in sms_records:
                                    s_num = str(s.get('number', '')).strip()
                                    # এখানে হুবহু (Exact) মেলানো হচ্ছে যাতে অন্য কোনো নাম বা অফার মিক্স না হয়
                                    if s_num == selected_sender:
                                        matched_sms.append(s)
                                        
                                if matched_sms:
                                    limited_sms = matched_sms[:count_num]
                                    result_msg = f"🔍 *`{selected_sender}` থেকে প্রাপ্ত নির্দিষ্ট {len(limited_sms)}টি মেসেজ:*\n\n"
                                    
                                    for sms in limited_sms:
                                        body = sms.get('body', '')
                                        date = sms.get('received', '')
                                        result_msg += f"📅 *সময়:* `{date}`\n💬 *মেসেজ:* \n{body}\n\n===================\n\n"
                                        
                                    send_message(chat_id, result_msg)
                                else:
                                    send_message(chat_id, f"❌ `{selected_sender}` এর কোনো মেসেজ পাওয়া যায়নি।")
                                    
                                current_state = None
                                selected_sender = None
                            else:
                                send_message(chat_id, "❌ দয়া করে সঠিক একটি সংখ্যা লিখে পাঠান (যেমন: 1, 2 বা 5)।")
                        else:
                            send_message(chat_id, "দয়া করে নিচের মূল বাটনগুলো ব্যবহার করুন অথবা 'MESSAGE LIST' এ চাপ দিন।")
                            
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
