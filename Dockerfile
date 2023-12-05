FROM python:3.11.2 as base
WORKDIR /app
ENV PYTHONUNBUFFERED=0
COPY requirements.txt alembic.ini ./
RUN pip install -U -r requirements.txt

FROM base as prod
COPY ./src ./
CMD ["/bin/bash", "-c", "alembic upgrade head && python ./main.py bot --sync -c ./config.toml"]

FROM base as debug
ENV DEBUG=1
ENV LOG_LEVEL=DEBUG
RUN pip install debugpy
CMD ["/bin/bash", "-c", "alembic upgrade head && python -m debugpy --wait-for-client --listen 0.0.0.0:5678 ./src/main.py bot -c ./config.toml"]
