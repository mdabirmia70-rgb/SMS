import json
import subprocess
import time
import requests

# Apnar bot-er backend API URL
SERVER_URL = "https://your-bot-server.com/api/verify-payment"


def get_latest_sms():
  try:
    # Termux API diye shobshesh 1-ti SMS pora
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
      "message": full_message,  # Pura message body pathano hochhe
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

      # Nothun SMS ashle ebong bKash/Nagad theke hole
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

    # Proti 3 second por por SMS check korbe
    time.sleep(3)


if __name__ == "__main__":
  main()
