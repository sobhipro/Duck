# استخدام صورة أساسية من Ubuntu
FROM ubuntu:20.04

# تثبيت التبعيات الأساسية
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    unzip \
    python3 \
    python3-pip \
    libx11-dev \
    libgdk-pixbuf2.0-0 \
    libnss3 \
    libxss1 \
    libgconf-2-4 \
    libasound2 \
    libatk1.0-0 \
    libcups2 \
    fonts-liberation \
    libappindicator3-1 \
    libnspr4 \
    libxtst6 \
    xdg-utils \
    ca-certificates \
    curl

# تثبيت Google Chrome (إذا كنت بحاجة إلى ذلك)
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt --fix-broken install -y

# تثبيت باقي الحزم المطلوبة
COPY requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt

# نسخ المشروع إلى الحاوية
COPY . /app

# تحديد مجلد العمل
WORKDIR /app

# تحديد المسار الثابت لـ Chromium في خيارات الـ Selenium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# تحديد المنفذ الذي سيتم تشغيله
EXPOSE 8000

# الأمر الذي سيتم تنفيذه عند تشغيل الحاوية
CMD ["python3", "main.py"]
