FROM sanicframework/sanic:LTS

RUN mkdir /srv
COPY . /srv

WORKDIR /srv

CMD ["sanic", "simple_server.app"]
