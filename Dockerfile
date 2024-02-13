FROM python:3.10-alpine

RUN apk add --no-cache gcc musl-dev libffi-dev

WORKDIR /usr/src/app

ENV PYTHONPATH="src:${PYTHONPATH}"

COPY requirements.txt ./requirements.txt

RUN pip3 install --upgrade pip --default-timeout=100 && \
    pip3 install --no-cache-dir -r requirements.txt --default-timeout=100

COPY . .
