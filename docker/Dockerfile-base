ARG PYTHON_VERSION

FROM python:${PYTHON_VERSION}-alpine
RUN apk update
RUN apk add --no-cache --update build-base \
        ca-certificates \
        openssl
RUN update-ca-certificates
RUN rm -rf /var/cache/apk/*
