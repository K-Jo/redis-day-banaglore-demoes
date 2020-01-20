FROM python:3.7.3

WORKDIR /app
ADD . /app

RUN set -ex; \
    pip install -r redisgraph-bulk-loader/requirements.txt;

ENTRYPOINT [ "python3" ]
