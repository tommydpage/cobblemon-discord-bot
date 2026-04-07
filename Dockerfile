FROM python:3.12-slim
WORKDIR /cobblebot
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot/ bot/
CMD ["python", "-m", "bot.main"]