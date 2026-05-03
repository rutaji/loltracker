FROM python:3.11

WORKDIR /app
ENV PYTHONPATH=/app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ./app ./app
COPY ./scripts ./scripts
COPY ./tools ./tools
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini

RUN chmod +x /app/scripts/automatic/run_alembic.sh

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
