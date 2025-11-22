# Dockerfile para Django
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Coleta arquivos estáticos
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "contas_a_pagar.wsgi:application", "--bind", "0.0.0.0:8000"] 