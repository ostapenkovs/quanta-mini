FROM python:3.10-slim-bullseye

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get -qq update && apt-get -y -qq upgrade

COPY . ./
RUN pip install -r requirements.txt

ENTRYPOINT ["sh", "entrypoint.sh"]
