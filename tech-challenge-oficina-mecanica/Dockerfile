# Imagem oficial leve do Python 3.12/3.13 Slim
FROM python:3.12-slim

WORKDIR /app

# Instula dependências do sistema necessárias para compilação se necessário
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia o código fonte do projeto
COPY . .

# Expõe a porta padrão do FastAPI
EXPOSE 8000

# Comando para iniciar o servidor Uvicorn em produção
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]