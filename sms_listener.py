import json
import os
import subprocess
import sys
import time


# প্রয়োজনীয় প্যাকেজ অটো-ইনস্টল করার ফাংশন
def auto_install_packages():
  # Python-এর requests লাইব্রেরি চেক ও ইনস্টল
  try:
    import requests
  except ImportError:
    print("[SYSTEM] 'requests' module not found. Installing...")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "requests"]
    )
    import requests

  # Termux API প্যাকেজ (কমান্ডলাইন) চেক ও ইনস্টল
  if subprocess.call(["which", "termux-sms-list"], stdout=subprocess.DEVNULL) != 0:
    print("[SYSTEM] 'termux-api' package not found. Installing...")
    os.system("pkg install termux-api -y")

  return requests


# প্যাকেজ অটো-ইনস্টল সম্পন্ন করে requests ইমপোর্ট করা
requests = auto_install_packages()

# আপনার বটের ব্যাকএন্ড API এন্ডপয়েন্ট URL
SERVER_URL = "https://your-bot-server.com/api/verify-payment"


def get_latest_sms():
  try:
    output = subprocess.check_output(
        ["termux-sms-list", "-l", "1"], stderr=subprocess.DEVNULL
    )
    sms_data = json.loads(output.decode("utf-8"))
    if sms_data:
      return sms_data[0]
  except Exception as e:
    print(f"Error reading SMS: {e}")
  return None


def send_to_backend(sender, full_message):
  payload = {
      "sender": sender,
      "message": full_message,
  }

  while True:
    try:
      response = requests.post(SERVER_URL, json=payload, timeout=10)
      if response.status_code == 200:
        print(f"[SUCCESS] Sent Full SMS from {sender}")
        break
      else:
        print(f"[SERVER ERROR] Status {response.status_code}, retrying...")
    except requests.exceptions.RequestException:
      print("[NETWORK ERROR] Retrying in 10 seconds...")
      time.sleep(10)


def main():
  print("SMS Listener Running...")
  last_processed_sms_id = None

  while True:
    sms = get_latest_sms()
    if sms:
      sms_id = sms.get("_id")
      sender = sms.get("number", "")
      body = sms.get("body", "")

      if sms_id != last_processed_sms_id:
        if (
            "bKash" in sender
            or "Nagad" in sender
            or "16216" in sender
            or "BKASH" in sender
            or "NAGAD" in sender
        ):
          print(f"\n[NEW SMS RECEIVED]\nFrom: {sender}\nMessage: {body}")
          send_to_backend(sender, body)

        last_processed_sms_id = sms_id

    time.sleep(3)


if __name__ == "__main__":
  main()



