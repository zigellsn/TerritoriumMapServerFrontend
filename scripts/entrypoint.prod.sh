#!/usr/bin/env sh

if [ -e ".env" ]; then
    ENV_SQL_ENGINE="$(grep SQL_ENGINE .env | cut -d '=' -f2)"
    SQL_ENGINE="${ENV_SQL_ENGINE:-django.db.backends.sqlite}"
    if [ "${SQL_ENGINE}" = "django.db.backends.postgresql" ]; then
      ENV_SQL_HOST="$(grep SQL_HOST .env | cut -d '=' -f2)"
      SQL_HOST="${ENV_SQL_HOST:-localhost}"
      ENV_SQL_PORT="$(grep SQL_PORT .env | cut -d '=' -f2)"
      SQL_PORT="${ENV_SQL_PORT:-5432}"
    fi
    ENV_RABBITMQ_HOST="$(grep RABBITMQ_HOST .env | cut -d '=' -f2)"
    RABBITMQ_HOST="${ENV_RABBITMQ_HOST:-mq}"
fi

if [ "${SQL_ENGINE}" = "django.db.backends.postgresql" ]; then
    echo "Waiting for postgres..."

    while ! nc -z "${SQL_HOST}" "${SQL_PORT}"; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

echo "Waiting for RabbitMQ..."

while ! nc -z "${RABBITMQ_HOST}" 5672; do
  sleep 0.1
done

echo "RabbitMQ started"

python manage.py migrate --no-input
python manage.py compilemessages --ignore venv
python manage.py collectstatic --no-input --clear
python manage.py runworker mq &

exec "$@"
