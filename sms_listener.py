import json
import subprocess
import requests
import time
from datetime import datetime

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

# বর্তমান অবস্থা এবং নির্বাচিত প্রেরক ট্র্যাক করার গ্লোবাল ভেরিয়েবল
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
        f"⚙️ *স্ট্যাটাস:* `অনলাইন (সঠিক সিকোয়েন্স মোড)`\n\n"
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

def get_all_sms(limit=150):
    try:
        # ফোন থেকে নির্দিষ্ট লিমিট অনুযায়ী এসএমএস ফেচ করা
        result = subprocess.run(
            ['termux-sms-list', '-l', str(limit)], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            sms_list = json.loads(result.stdout)
            if sms_list:
                # মেসেজগুলোকে সঠিক সময় বা সিরিয়াল অনুযায়ী সাজানো (যাতে উল্টাপাল্টা না হয়)
                # সাধারণত টার্মাক্স রিসিভড টাইম বা ডেট ফরম্যাটে দেয়, সেটিকে সাজানো হচ্ছে
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
    print("বট সফলভাবে চালু হয়েছে...")
    
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
                    
                    # ১. ইনলাইন বাটন ক্লিক হ্যান্ডেল করা
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        callback_id = callback["id"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        data = callback["data"]
                        
                        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery", json={"callback_query_id": callback_id})
                        
                        if data.startswith("select_"):
                            selected_sender = data.replace("select_", "")
                            current_state = "WAITING_FOR_COUNT"
                            send_message(chat_id, f"📱 *নির্বাচিত প্রেরক:* `{selected_sender}`\n\n🔢 *এই নাম্বারের কয়টি মেসেজ দেখতে চান?*\n(দয়া করে একটি সংখ্যা লিখে পাঠান, যেমন: `1`, `2`, `5` বা `10`)")
                            
                    # ২. টেক্সট মেসেজ ও কিবোর্ড বাটন ইনপুট হ্যান্ডেল করা
                    elif "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"].strip()
                        clean_text = text.replace("🟢", "").replace("📥", "").strip()
                        
                        if clean_text == "BOT STATUS CHECK":
                            current_state = None
                            send_message(chat_id, "🟢 *বট বর্তমানে অনলাইন (ONLINE) রয়েছে!*")
                            
                        elif clean_text == "MESSAGE LIST":
                            current_state = "WAITING_FOR_LIMIT"
                            send_message(chat_id, "🔢 *সাম্প্রতিক কয়টি মেসেজ লিস্ট দেখতে চান?*\n\nদয়া করে একটি সংখ্যা লিখে পাঠান (যেমন: `5`, `10` বা `15`).")
                            
                        elif current_state == "WAITING_FOR_LIMIT":
                            if text.isdigit():
                                limit_num = int(text)
                                if limit_num > 40:
                                    limit_num = 40
                                    
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
                                            list_text += f"👤 *নাম্বার:* `{sender}`\n📅 *সময়:* `{date}`\n-------------------\n"
                                            inline_keyboard.append([{"text": f"👉 নির্বাচন করুন: {sender}", "callback_data": f"select_{sender}"}])
                                    
                                    reply_markup = {"inline_keyboard": inline_keyboard}
                                    list_text += "\n👇 *যেকোনো নাম্বারের মেসেজ দেখতে নিচে ক্লিক করুন:*"
                                    
                                    send_message(chat_id, list_text, reply_markup=reply_markup)
                                    current_state = None
                                else:
                                    send_message(chat_id, "⚠️ ফোনে কোনো এসএমএস পাওয়া যায়নি!")
                                    current_state = None
                            else:
                                send_message(chat_id, "❌ ভুল ইনপুট! দয়া করে শুধু একটি সংখ্যা লিখে পাঠান (যেমন: 5 বা 10)।")
                                
                        elif current_state == "WAITING_FOR_COUNT":
                            if text.isdigit():
                                count_num = int(text)
                                # ১৫০টি মেসেজ লোড করে সঠিক অর্ডারে ফিল্টার করা হচ্ছে
                                sms_records = get_all_sms(150)
                                
                                matched_sms = []
                                for s in sms_records:
                                    s_num = str(s.get('number', '')).strip().lower()
                                    target = str(selected_sender).strip().lower()
                                    if target in s_num or s_num in target:
                                        matched_sms.append(s)
                                        
                                if matched_sms:
                                    # ব্যবহারকারী যতগুলো দেখতে চেয়েছেন ঠিক ততগুলো নেওয়া হচ্ছে
                                    limited_sms = matched_sms[:count_num]
                                    result_msg = f"🔍 *`{selected_sender}` থেকে প্রাপ্ত সর্বশেষ {len(limited_sms)}টি মেসেজ:*\n\n"
                                    
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
