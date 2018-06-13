FROM python:3.6-alpine

ENV FLASK_APP app
ENV FLASK_CONFIG production

COPY . /srv/sentinel
WORKDIR /srv/sentinel

RUN apk update && apk add \
    gcc \
    libffi-dev \
    linux-headers \
    musl-dev \
    openssl-dev

RUN pip install pipenv
RUN pipenv install --deploy --system

CMD ["flask", "run", "--host=0.0.0.0"]

# gunicorn -b :5000 --access-logfile - --error-logfile - sentinel:app
