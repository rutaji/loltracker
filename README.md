
# run

docker-compose up --build


# SQL database

You can connect to database using : postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}
to generate new alembic version : alembic revision --autogenerate -m "commit-name"
to upgrade to newest alembic version: alembic upgrade head
