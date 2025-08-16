from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from twilio.rest import Client
import traceback
import os

# ✅ Get credentials & settings from Railway Variables
register_number = os.getenv("REGISTER_NUMBER")
password = os.getenv("PASSWORD")
url = os.getenv("URL", "http://mitsims.in/home.jsp")

ACCOUNT_SID = os.getenv("ACCOUNT_SID")
AUTH_TOKEN = os.getenv("AUTH_TOKEN")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM")
WHATSAPP_TO = os.getenv("WHATSAPP_TO")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(message):
    try:
        msg = client.messages.create(
            body=message,
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO
        )
        print(f"✅ WhatsApp message sent: SID {msg.sid}")
    except Exception as e:
        print("❌ Failed to send WhatsApp message:", e)
        traceback.print_exc()

print("🚀 Process Started")

# ✅ Chrome options for Railway (headless mode required)
op = Options()
op.add_argument("--no-sandbox")
op.add_argument("--disable-dev-shm-usage")
op.add_argument("--headless=new")  # force headless mode
op.add_argument("--disable-gpu")

s = Service(executable_path="/usr/bin/chromedriver")  # Railway default chrome driver path
with webdriver.Chrome(service=s, options=op) as d:
    wait = WebDriverWait(d, 20)

    d.get(url)

    student_link = wait.until(EC.element_to_be_clickable((By.ID, "studentLink")))
    student_link.click()

    # Step 3: Wait for login form and fill credentials
    wait.until(EC.presence_of_element_located((By.ID, "inputStuId")))
    wait.until(EC.presence_of_element_located((By.NAME, "password")))

    d.execute_script("document.getElementById('inputStuId').value = arguments[0];", register_number)
    d.execute_script("document.getElementsByName('password')[1].value = arguments[0];", password)

    login_btn = wait.until(EC.element_to_be_clickable((By.ID, "studentSubmitButton")))
    d.execute_script("arguments[0].click();", login_btn)

    print("✅ Login attempted. Waiting for dashboard to load...")
    time.sleep(5)

    try:
        elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "x-form-display-field")))
        elements = elements[9:-1]

        no_classes_present = 0
        no_classes_conducted = 0

        for i in range(len(elements)):
            try:
                if i % 5 == 1:
                    no_classes_present += int(elements[i].text.strip())
                elif i % 5 == 2:
                    no_classes_conducted += int(elements[i].text.strip())
            except:
                continue

        if no_classes_conducted == 0:
            message = "⚠️ No classes conducted found. Unable to calculate attendance."
        else:
            percentage = (no_classes_present / no_classes_conducted) * 100
            message = f"📊 Your current attendance is {percentage:.2f}% ({no_classes_present}/{no_classes_conducted})"

        print(f"Attendance result: {message}")

        # ✅ Only Twilio WhatsApp works reliably on Railway
        send_whatsapp_message(message)

    except Exception as e:
        print("❌ Error occurred while fetching attendance:")
        traceback.print_exc()

print("✅ Done")
