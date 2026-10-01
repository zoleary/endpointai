FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
EXPOSE 8000
# Pass credentials at runtime: docker run --env-file .env -p 8000:8000 zsai-demo
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
