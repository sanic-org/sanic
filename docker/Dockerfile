ARG BASE_IMAGE_TAG

FROM sanicframework/sanic-build:${BASE_IMAGE_TAG}

RUN apk update
RUN update-ca-certificates

RUN pip install sanic
RUN apk del build-base
