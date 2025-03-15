import os
import requests
from fastapi import FastAPI, Request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
LOGIN_EMAIL = os.getenv("LOGIN_EMAIL")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD")
LOGIN_URL = "https://sawa9ly.app/login"
PRODUCT_LINKS_FILE = "product_links.txt"

product_links = []

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("تم إرسال الرسالة بنجاح!")
    except requests.exceptions.RequestException as e:
        print(f"فشل إرسال الرسالة: {e}")

def login():
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get(LOGIN_URL)
        
        driver.find_element(By.NAME, "email").send_keys(LOGIN_EMAIL)
        driver.find_element(By.NAME, "password").send_keys(LOGIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        # استخدم WebDriverWait بدلاً من implicitly_wait
        WebDriverWait(driver, 10).until(EC.url_contains("dashboard"))

        if "dashboard" in driver.current_url:
            print("تم تسجيل الدخول بنجاح!")
            cookies = driver.get_cookies()
            driver.quit()
            return cookies
        else:
            print("فشل تسجيل الدخول: تحقق من بيانات الاعتماد")
            driver.quit()
            return None
    except Exception as e:
        print(f"خطأ أثناء تسجيل الدخول: {e}")
        return None

def check_product_availability(product_url, cookies):
    try:
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie["name"], cookie["value"])
        
        response = session.get(product_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        availability_div = soup.find("div", class_="text-center text-xl grow bg-red-600 text-white p-3")
        
        if availability_div and "غير متوفر" in availability_div.text.strip():
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f"خطأ أثناء فحص المنتج: {e}")
        return None

def save_links():
    with open(PRODUCT_LINKS_FILE, "w") as file:
        file.write("\n".join(product_links))
    print("تم حفظ الروابط.")

def load_links():
    try:
        with open(PRODUCT_LINKS_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

@app.on_event("startup")
def startup_event():
    global product_links
    product_links = load_links()

@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    message = data.get("message", {}).get("text", "").strip()
    
    if message.startswith("http") and message not in product_links:
        product_links.append(message)
        send_telegram_message(f"✅ تمت إضافة الرابط: {message}")
        save_links()
    elif message == "/check":
        cookies = login()
        if cookies:
            unavailable_products = [link for link in product_links if not check_product_availability(link, cookies)]
            
            if unavailable_products:
                send_telegram_message("🔴 المنتجات غير المتوفرة:")
                for link in unavailable_products:
                    send_telegram_message(link)
            else:
                send_telegram_message("✅ جميع المنتجات متاحة.")
        else:
            send_telegram_message("⚠️ فشل تسجيل الدخول.")
    elif message == "/list":
        send_telegram_message("\n".join(product_links) if product_links else "🚫 لا توجد روابط.")
    elif message == "/clear":
        product_links.clear()
        save_links()
        send_telegram_message("🗑️ تم مسح الروابط.")
    elif message == "/help":
        send_telegram_message("/check - فحص المنتجات\n/list - عرض الروابط\n/clear - مسح جميع الروابط")
    return {"status": "ok"}

@app.get("/")
def home():
    return {"message": "✅ Bot is running!"}

PORT = int(os.getenv("PORT", 8000))
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
