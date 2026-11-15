# Dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# تثبيت حزم النظام ومكتبات الاتصال بـ MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    pkg-config \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# تثبيت مكتبات بايثون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود المشروع بالكامل (الواجهة، القوالب، وقاعدة بيانات الأبحاث)
COPY . .

# إنشاء الفولدرات المطلوبة للتخزين واللوجات
RUN mkdir -p /app/instance /app/logs /app/static/uploads

# تأمين الحاوية بيوزر غير الـ root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# فتح البورت 5000
EXPOSE 4500

# تشغيل التطبيق بواسطة Gunicorn مع مهلة 180 ثانية لتناسب استدعاءات الـ AI
CMD ["gunicorn", "-w", "2", "--threads", "8", "--timeout", "180", "-b", "0.0.0.0:4500", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "app:app"]