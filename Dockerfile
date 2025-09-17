FROM python:3.11-slim

WORKDIR /app


ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh


RUN apt-get update && apt-get install -y curl wget gnupg unzip && apt-get clean
COPY wait-for-it.sh .
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN python -m playwright install --with-deps

COPY . .

CMD ["python", "scrape_otodom.py"]
