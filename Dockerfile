FROM python:3.11.0 as base
WORKDIR /app
ENV PYTHONUNBUFFERED=0
COPY bin/wait-for-it.sh requirements.txt config.toml* ./
RUN chmod +x ./wait-for-it.sh && pip install -r requirements.txt
ENTRYPOINT ["./wait-for-it.sh", "database:5432", "--"]

FROM base as prod
COPY ./src ./
CMD ["python", "./main.py", "bot", "--sync"]

FROM base as debug
ENV DEBUG=1
ENV LOG_LEVEL=DEBUG
RUN pip install debugpy
CMD ["python", "-m", "debugpy", "--wait-for-client", "--listen", "0.0.0.0:5678", "./src/main.py", "bot", "-c", "./config.toml"]
