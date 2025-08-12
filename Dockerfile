FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8008

CMD [ "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8008"]