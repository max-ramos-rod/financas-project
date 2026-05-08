FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# VITE_API_URL resolvido em build time
ARG VITE_API_URL=https://financas.igrejabatistafe.com.br/api/v1
ENV VITE_API_URL=$VITE_API_URL

CMD ["gunicorn", "app.main:app", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-w", "2", \
     "-b", "0.0.0.0:8000"]