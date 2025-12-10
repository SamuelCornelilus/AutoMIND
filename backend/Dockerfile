# backend/Dockerfile - versi sederhana untuk development (dengan entrypoint)
FROM python:3.11-slim

WORKDIR /srv/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# salin requirements dulu supaya cache docker efisien
COPY requirements.txt /srv/app/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /srv/app/requirements.txt

# salin seluruh kode dari konteks build (konteks sudah ./backend)
COPY . /srv/app

# salin entrypoint dan beri izin eksekusi
COPY entrypoint.sh /srv/app/entrypoint.sh
RUN chmod +x /srv/app/entrypoint.sh

EXPOSE 8000

# jalankan entrypoint (entrypoint akan menjalankan create_tables lalu uvicorn)
ENTRYPOINT ["/srv/app/entrypoint.sh"]
