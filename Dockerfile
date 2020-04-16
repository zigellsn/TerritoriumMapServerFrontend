FROM node:10-slim AS build

COPY . .

RUN npm install && \
    npm run build

FROM tms/python-base:slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE=TerritoriumMapServerFrontend.settings.dev

ENV DEPENDENCIES="gcc \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    libc-dev"

COPY requirements/common.txt .
COPY requirements/dev.txt .

RUN apt-get update && apt-get install -y --no-install-recommends gettext libpq5 $DEPENDENCIES && \
    pip install --no-cache-dir -r ./dev.txt && \
    apt-get autoremove -y --purge $DEPENDENCIES && \
    rm -rf /var/lib/apt/lists/* && \
    rm -f ./common.txt && \
    rm -f ./dev.txt

USER pyuser

COPY --from=build --chown=pyuser:users /TerritoriumMapServerFrontend/static ./TerritoriumMapServerFrontend/static
COPY scripts/entrypoint.sh $HOME/

ENTRYPOINT ["/home/pyuser/entrypoint.sh"]
