#!/bin/sh

echo "starting alembic upgrade"

alembic -c /app/alembic.ini upgrade head
DATABASE_URL=$TEST_DATABASE_URL alembic -c /app/alembic.ini upgrade head

echo "alembic upgrade finished"


echo "starting FastAPI"
exec "$@"
