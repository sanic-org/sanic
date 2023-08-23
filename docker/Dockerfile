ARG BASE_IMAGE_TAG
ARG SANIC_PYPI_VERSION

FROM sanicframework/sanic-build:${BASE_IMAGE_TAG}

RUN apk update
RUN update-ca-certificates

RUN pip install "sanic==${SANIC_PYPI_VERSION}"
RUN apk del build-base
