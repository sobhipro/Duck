import os
import time
import requests
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# بيانات البوت (يجب تخزينها في متغيرات بيئية)
bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

# بيانات تسجيل الدخول (يجب تخزينها في متغيرات بيئية)
login_url = 'https://sawa9ly.app/login'
email = os.getenv('LOGIN_EMAIL')
password = os.getenv('LOGIN_PASSWORD')

# قائمة الروابط
product_links = []

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    payload = {'chat_id': chat_id, 'text': message}
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print('تم إرسال الرسالة بنجاح!')
    except requests.exceptions.RequestException as e:
        print(f'فشل إرسال الرسالة: {e}')

def login():
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.get(login_url)
        
        driver.find_element(By.NAME, 'email').send_keys(email)
        driver.find_element(By.NAME, 'password').send_keys(password)
        driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        
        time.sleep(5)
        
        if 'dashboard' in driver.current_url:
            print('تم تسجيل الدخول بنجاح!')
            cookies = driver.get_cookies()
            driver.quit()
            return cookies
        else:
            print('فشل تسجيل الدخول: تحقق من بيانات الاعتماد')
            driver.quit()
            return None
    except Exception as e:
        print(f'خطأ أثناء تسجيل الدخول: {e}')
        return None

def check_product_availability(product_url, cookies):
    try:
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        response = session.get(product_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        availability_div = soup.find('div', class_='text-center text-xl grow bg-red-600 text-white p-3')
        
        if availability_div and 'غير متوفر' in availability_div.text.strip():
            return False
        return True
    except requests.exceptions.RequestException as e:
        print(f'خطأ أثناء فحص المنتج: {e}')
        return None

def monitor_products(cookies):
    print('بدء مراقبة المنتجات...')
    threads = []
    for link in product_links:
        thread = threading.Thread(target=check_and_notify, args=(link, cookies))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    print('انتهت مراقبة المنتجات.')

def check_and_notify(link, cookies):
    is_available = check_product_availability(link, cookies)
    if is_available is False:
        send_telegram_message(f'🔴 المنتج غير متوفر: {link}')
        product_links.remove(link)
        save_links()

def save_links():
    with open('product_links.txt', 'w') as file:
        file.write('\n'.join(product_links))
    print('تم حفظ الروابط.')

def load_links():
    try:
        with open('product_links.txt', 'r') as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

def handle_updates(cookies):
    try:
        url = f'https://api.telegram.org/bot{bot_token}/getUpdates'
        response = requests.get(url).json()
        
        if not response.get('ok'):
            return
        
        for update in response.get('result', []):
            message = update.get('message', {}).get('text', '').strip()
            if message.startswith('http') and message not in product_links:
                product_links.append(message)
                send_telegram_message(f'✅ تمت إضافة الرابط: {message}')
                save_links()
            elif message == '/check':
                send_telegram_message('🔍 جارٍ الفحص...')
                monitor_products(cookies)
                send_telegram_message('✅ تم الفحص.')
            elif message == '/list':
                send_telegram_message('\n'.join(product_links) if product_links else '🚫 لا توجد روابط.')
            elif message == '/clear':
                product_links.clear()
                save_links()
                send_telegram_message('🗑️ تم مسح الروابط.')
            elif message == '/help':
                send_telegram_message('/check - فحص المنتجات\n/list - عرض الروابط\n/clear - مسح جميع الروابط')
        
        if response.get('result'):
            last_update_id = response['result'][-1]['update_id']
            requests.get(f'{url}?offset={last_update_id + 1}')
    except Exception as e:
        print(f'خطأ في معالجة التحديثات: {e}')

if __name__ == "__main__":
    cookies = login()
    if cookies:
        product_links = load_links()
        while True:
            handle_updates(cookies)
            time.sleep(10)
    else:
        print('🔴 فشل تسجيل الدخول.')

