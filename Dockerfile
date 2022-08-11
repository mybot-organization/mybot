FROM python:3.10.5
WORKDIR /app
ENV PYTHONUNBUFFERED=0
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY wait-for-it.sh ./src ./
RUN chmod +x ./wait-for-it.sh
CMD ["python", "./main.py"]
