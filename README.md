
# run

docker-compose up --build

to generate database:
    alembic upgrade head
    docker-compose exec api python -m  scripts.seed_data (generates data in the script. Doesnt work yet)

to generate test database:
    source .env
    DATABASE_URL=$TEST_DATABASE_URL alembic upgrade head


# SQL database

You can connect to database using : postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}

to generate new alembic version : alembic revision --autogenerate -m "commit-name"
to upgrade to newest alembic version: alembic upgrade head
to add test data into database: docker-compose exec api python -m  scripts.seed_data
 
