# اختيار صورة الأساس من Ubuntu
FROM ubuntu:20.04

# تثبيت التبعيات
RUN apt-get update && \
    apt-get install -y wget && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt --fix-broken install -y

# تثبيت ChromeDriver
RUN apt-get install -y unzip && \
    wget https://chromedriver.storage.googleapis.com/94.0.4606.61/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/local/bin/chromedriver && \
    chmod +x /usr/local/bin/chromedriver

# تثبيت Python وبعض المكتبات الأخرى التي تحتاجها
RUN apt-get install -y python3 python3-pip

# نسخ الملفات المحلية إلى الحاوية
COPY . /app

# تحديد مجلد العمل
WORKDIR /app

# تثبيت المتطلبات
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# تحديد المنفذ الذي سيتم تشغيله
EXPOSE 8000

# الأمر الذي سيتم تنفيذه عند تشغيل الحاوية
CMD ["python3", "your_script.py"]
