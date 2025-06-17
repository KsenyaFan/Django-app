FROM python:3.11

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --upgrade pip "poetry==2.1.3"
RUN poetry config virtualenvs.create false --local
COPY pyproject.toml poetry.lock ./
COPY mysite .

RUN poetry install

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000"]
# CMD ["python", "manage.py", "runserver"]