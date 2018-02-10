FROM alpine:3.7

RUN apk add --no-cache --update \
        curl \
        bash \
        build-base \
        ca-certificates \
        git \
        bzip2-dev \
        linux-headers \
        ncurses-dev \
        openssl \
        openssl-dev \
        readline-dev \
        sqlite-dev

RUN update-ca-certificates
RUN rm -rf /var/cache/apk/*

ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"

ADD . /app
WORKDIR /app

RUN /app/docker/bin/install_python.sh 3.5.4 3.6.4

ENTRYPOINT ["./docker/bin/entrypoint.sh"]
