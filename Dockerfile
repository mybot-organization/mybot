# syntax=docker/dockerfile-upstream:master-labs

FROM python:3.12.0-alpine as build
WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY ./resources ./
RUN --mount=type=cache,target=/var/cache/apk/ \
    --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    --mount=type=bind,source=./bin/msgfmt.py,target=./msgfmt.py \
    : \
    && apk add gcc musl-dev linux-headers \
    && pip install -U pip \
    && pip install -U -r requirements.txt \
    && python ./msgfmt.py ./locale/**/LC_MESSAGES/*.po \
    && :

FROM python:3.12.0-alpine as base
# https://docs.docker.com/reference/dockerfile/#copy---parents
COPY --parents --from=build /opt/venv /app/locale/**/LC_MESSAGES/*.mo /
WORKDIR /app
COPY ./src ./
COPY --parents ./alembic.ini ./alembic ./
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=0


FROM base as production
CMD ["/bin/sh", "-c", "alembic upgrade head && python ./main.py run --sync -c ./config.toml"]


FROM base as debug
ENV DEBUG=1
ENV LOG_LEVEL=DEBUG
RUN pip install debugpy
CMD ["/bin/sh", "-c", "alembic upgrade head && python -m debugpy --wait-for-client --listen 0.0.0.0:5678 ./main.py run -c ./config.toml"]
