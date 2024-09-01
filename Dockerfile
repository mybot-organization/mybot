# syntax=docker/dockerfile-upstream:master-labs

FROM python:3.12.0-alpine as build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
WORKDIR /app
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"
COPY ./resources ./
RUN --mount=type=cache,target=/var/cache/apk/ \
    --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=./bin/msgfmt.py,target=./msgfmt.py \
    : \
    && apk add gcc musl-dev linux-headers \
    && uv sync --no-dev --frozen \
    && python ./msgfmt.py ./locale/**/LC_MESSAGES/*.po \
    && :

FROM python:3.12.0-alpine as base
# https://docs.docker.com/reference/dockerfile/#copy---parents
COPY --parents --from=build /app/.venv /app/locale/**/LC_MESSAGES/*.mo /
WORKDIR /app
COPY ./src ./
COPY --parents ./alembic.ini ./alembic ./
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=0


FROM base as production
CMD ["/bin/sh", "-c", "alembic upgrade head && python ./main.py run --sync -c ./config.toml"]


FROM base as debug
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
ENV DEBUG=1
ENV LOG_LEVEL=DEBUG
RUN uv pip install debugpy
CMD ["/bin/sh", "-c", "alembic upgrade head && python -Xfrozen_modules=off -m debugpy --wait-for-client --listen 0.0.0.0:5678 ./main.py run -c ./config.toml"]
