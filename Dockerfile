# Základní image
FROM python:3.12-slim-bullseye

# Nastavení pracovního adresáře
WORKDIR /app

# Instalace systémových závislostí
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# vytvoření přesného seznamu instalovaných balíčků
# pip freeze > requirements.docker.txt
# namisto requirements.txt zkopírujeme soubor requirements.docker.txt
# Kopírování pouze requirements souboru pro lepší využití cache
COPY requirements.docker.txt .

# Instalace Python závislostí
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.docker.txt

COPY . .

# Spuštění aplikace
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]