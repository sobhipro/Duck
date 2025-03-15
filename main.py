from flask import Flask, request
import threading
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

app = Flask(__name__)

# بيانات البوت
bot_token = '8063259306:AAEQ_EFy4zrUXjRa_oGB9T_UoNxaR6l-MW4'  # Token البوت
chat_id = '5176782297'  # استبدل ب chat_id الخاص بك

# بيانات تسجيل الدخول
login_url = 'https://sawa9ly.app/login'
email = 'sobhi.chebaiki.me@gmail.com'  # استبدل ببريدك الإلكتروني
password = '000###sabrina###000'  # استبدل بكلمة المرور

# قائمة لتخزين الروابط
product_links = []

# دالة لإرسال رسالة عبر Telegram
def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print('تم إرسال الرسالة بنجاح!')
    else:
        print('فشل إرسال الرسالة:', response.text)

# دالة لفحص حالة المنتج باستخدام cookies
def check_product_availability(product_url, cookies):
    try:
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        response = session.get(product_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        availability_div = soup.find('div', class_='text-center text-xl grow bg-red-600 text-white p-3')
        if availability_div:
            availability_text = availability_div.text.strip()
            if 'غير متوفر' in availability_text:
                return False, availability_text
        return True, None
    except Exception as e:
        print('حدث خطأ أثناء فحص المنتج:', e)
        return None, None

# إعداد Webhook في Replit
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' in data:
        text = data['message'].get('text')
        if text and text.startswith('http'):
            product_links.append(text)
            send_telegram_message(f'تمت إضافة الرابط: {text}')
    return "OK", 200

# دالة لمراقبة الروابط
def monitor_products(cookies):
    print('بدء مراقبة المنتجات...')
    threads = []
    for link in product_links:
        thread = threading.Thread(target=check_and_notify, args=(link, cookies))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    print('تم الانتهاء من مراقبة المنتجات.')

def check_and_notify(link, cookies):
    is_available, status = check_product_availability(link, cookies)
    if is_available is False:
        message = f'تنبيه: المنتج غير متوفر.\nالرابط: {link}'
        send_telegram_message(message)
        product_links.remove(link)

# دالة لتحميل الروابط من ملف نصي
def load_links():
    try:
        with open('product_links.txt', 'r') as file:
            links = file.read().splitlines()
            return links
    except FileNotFoundError:
        return []

# دالة لاستقبال الروابط من المستخدم
def handle_updates():
    while True:
        time.sleep(10)
        cookies = login()
        if cookies:
            monitor_products(cookies)

def login():
    # إنشاء متصفح باستخدام Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(login_url)

    # إدخال بيانات تسجيل الدخول
    email_field = driver.find_element(By.ID, 'email')
    email_field.send_keys(email)
    password_field = driver.find_element(By.ID, 'password')
    password_field.send_keys(password)

    # النقر على زر تسجيل الدخول
    login_button = driver.find_element(By.ID, 'login_button')
    login_button.click()

    # انتظار التحميل
    time.sleep(5)

    # استخراج الـ cookies بعد تسجيل الدخول
    cookies = driver.get_cookies()
    driver.quit()

    return cookies

# تفعيل الـ Webhook للبوت
def set_webhook():
    webhook_url = 'https://duck.replit.app/webhook'  # الرابط الخاص بك في Replit
    url = f'https://api.telegram.org/bot{bot_token}/setWebhook?url={webhook_url}'
    response = requests.get(url)
    if response.status_code == 200:
        print('تم تفعيل الـ Webhook بنجاح!')
    else:
        print('فشل تفعيل الـ Webhook:', response.text)

if __name__ == '__main__':
    # تحميل الروابط المحفوظة
    product_links = load_links()
    
    # تفعيل الـ Webhook للبوت
    set_webhook()

    # بدء خادم Flask في Replit
    threading.Thread(target=handle_updates).start()
    app.run(host='0.0.0.0', port=80)
