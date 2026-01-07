#!/usr/bin/env sh
set -e

if [ "${RUN_MIGRATE:-1}" = "1" ]; then
	python manage.py migrate --noinput
fi

exec "$@"
