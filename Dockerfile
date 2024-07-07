# menggunakan base python versi 3.12
FROM python:3.12

# atur direktori
WORKDIR /app

# mengkopi yang dibutuhkan ke dalam docker
COPY requirements.txt .

# menjalan package yang dbutuhkan
RUN pip install --no-cache-dir -r requirements.txt

# menyalin seluruh file atau folder
COPY . .

# menjalankan command
CMD ["uvicorn", "main:app", "--port", "8000", "--reload"]