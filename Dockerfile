FROM python:3.8-slim

WORKDIR /app

ENV PYTHONUNBUFERRED=1

COPY requirements/prod.txt /app/requirements.txt

RUN pip install --trusted-host pypi.org \
                --trusted-host pypi.python.org \
                --trusted-host files.pythonhosted.org \
                --no-cache-dir \
                -r requirements.txt

COPY src /app

CMD uvicorn main:app --host=0.0.0.0