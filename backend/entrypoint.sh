#!/bin/sh
# entrypoint.sh - jalankan pembuatan tabel (retry) lalu start Uvicorn

set -eu

echo "===> Menunggu database dan mencoba membuat tabel (max 10 percobaan)..."

attempt=0
max_attempts=10
while [ $attempt -lt $max_attempts ]; do
  attempt=$((attempt+1))
  echo "Percobaan $attempt/$max_attempts: menjalankan create_tables..."
  # jalankan modul create_tables sebagai package sehingga import relatif bekerja
  if python -m app.create_tables; then
    echo "create_tables berhasil (atau sudah ada)."
    break
  else
    echo "create_tables gagal, menunggu 3 detik sebelum coba lagi..."
    sleep 3
  fi
done

if [ $attempt -ge $max_attempts ]; then
  echo "Peringatan: create_tables gagal setelah $max_attempts percobaan. Melanjutkan startup."
fi

echo "===> Menjalankan Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
