# استخدام صورة أساسية من Ubuntu
FROM ubuntu:20.04

# تثبيت التبعيات
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    unzip \
    python3 \
    python3-pip

# تثبيت Google Chrome (إذا كنت بحاجة إلى ذلك)
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    dpkg -i google-chrome-stable_current_amd64.deb && \
    apt --fix-broken install -y

# تثبيت باقي الحزم المطلوبة
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# نسخ المشروع إلى الحاوية
COPY . /app

# تحديد مجلد العمل
WORKDIR /app

# تحديد المنفذ الذي سيتم تشغيله
EXPOSE 8000

# الأمر الذي سيتم تنفيذه عند تشغيل الحاوية
CMD ["python3", "your_script.py"]
