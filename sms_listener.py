import json
import subprocess
import requests
import time

TELEGRAM_BOT_TOKEN = "8619498927:AAExQnFSEdYw7-q3hLxtWGa-FF1zV36S-jA"
TELEGRAM_CHAT_ID = "7792153788"

# স্টেট ট্র্যাক করার জন্য ভেরিয়েবল
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
        f"⚙️ *স্ট্যাটাস:* `ONLINE (Interactive Click Mode)`\n\n"
        f"👇 নিচের যেকোনো একটি বাটন ব্যবহার করুন:"
    )
    reply_markup = {
        "keyboard": [
            [{"text": "🟢 BOT STATUS CHECK"}],
            [{"text": "📥 MESSAGE LIST"}]
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
    print("Clickable SMS Bot Started. Waiting for commands...")
    send_control_panel()
    
    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            response = requests.get(url, timeout=35).json()
            
            if "result" in response:
                for update in response["result"]:
                    offset = update["update_id"] + 1
                    
                    # ১. ইনলাইন বাটন ক্লিক হ্যান্ডেল করার অংশ (যখন ইউজার বাটনে ক্লিক করবে)
                    if "callback_query" in update:
                        callback = update["callback_query"]
                        callback_id = callback["id"]
                        chat_id = str(callback["message"]["chat"]["id"])
                        data = callback["data"]
                        
                        # কলব্যাক একনলেজ করা যাতে লোডিং অ্যানিমেশন বন্ধ হয়
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
                                
                    # ২. সাধারণ টেক্সট মেসেজ বা মেইন মেনু বাটন হ্যান্ডেল করার অংশ
                    elif "message" in update and "text" in update["message"]:
                        chat_id = str(update["message"]["chat"]["id"])
                        text = update["message"]["text"].strip()
                        
                        if text == "🟢 BOT STATUS CHECK":
                            waiting_for_limit = False
                            send_message(chat_id, "🟢 *বট বর্তমানে অনলাইন (ONLINE) রয়েছে!*")
                            
                        elif text == "📥 MESSAGE LIST":
                            waiting_for_limit = True
                            send_message(chat_id, "🔢 *সাম্প্রতিক কয়টি মেসেজ দেখতে চান?*\n\nদয়া করে একটি সংখ্যা লিখে পাঠান (যেমন: `5`, `10` বা `15`)।")
                            
                        elif waiting_for_limit:
                            if text.isdigit():
                                limit_num = int(text)
                                if limit_num > 20:
                                    limit_num = 20  # বেশি বড় লিস্ট এড়াতে সর্বোচ্চ লিমিট কুড়িটি রাখা হলো
                                    
                                sms_records = get_all_sms(limit_num)
                                if sms_records:
                                    # ইউনিক সেন্ডার ফিল্টার করা যাতে একই নাম্বারের একাধিক এন্ট্রি না আসে
                                    unique_senders = []
                                    list_text = f"📋 *সাম্প্রতিক প্রেরকগণের তালিকা (সর্বশেষ {len(sms_records)}টি থেকে):*\n\n"
                                    inline_keyboard = []
                                    
                                    for sms in sms_records:
                                        sender = sms.get('number', 'Unknown')
                                        date = sms.get('received', 'N/A')
                                        
                                        if sender not in unique_senders:
                                            unique_senders.append(sender)
                                            list_text += f"👤 *নাম্বার/নাম:* `{sender}`\n📅 *সময়:* `{date}`\n-------------------\n"
                                            # প্রতিটি নাম্বারের জন্য একটি করে ক্লিকযোগ্য বাটন তৈরি করা
                                            inline_keyboard.append([{"text": f"📩 দেখুন: {sender}", "callback_data": f"read_{sender}"}])
                                    
                                    reply_markup = {"inline_keyboard": inline_keyboard}
                                    list_text += "\n👇 *নিচের বাটনগুলোতে ক্লিক করলেই সেই নাম্বারের সম্পূর্ণ মেসেজ চলে আসবে:*"
                                    
                                    send_message(chat_id, list_text, reply_markup=reply_markup)
                                    waiting_for_limit = False
                                else:
                                    send_message(chat_id, "⚠️ ফোনে কোনো এসএমএস পাওয়া যায়নি!")
                                    waiting_for_limit = False
                            else:
                                send_message(chat_id, "❌ দয়া করে সঠিক একটি সংখ্যা লিখুন (যেমন: 5 বা 10)।")
                        else:
                            send_message(chat_id, "দয়া করে নিচের বাটনগুলো ব্যবহার করুন অথবা 'MESSAGE LIST' এ চাপ দিন।")
                            
        except Exception as e:
            print(f"Polling Error: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()
