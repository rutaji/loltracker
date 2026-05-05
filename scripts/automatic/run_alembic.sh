#!/bin/sh

set -eu

echo "starting alembic upgrade for primary database"
alembic -c /app/alembic.ini upgrade head

if [ -n "${TEST_DATABASE_URL:-}" ]; then
    echo "starting alembic upgrade for test database"
    DATABASE_URL="$TEST_DATABASE_URL" alembic -c /app/alembic.ini upgrade head
fi

echo "alembic upgrade finished"
echo "starting app command"
exec "$@"
